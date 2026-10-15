# ClickHouse

**Best for:** large-scale analytical time series: tick-level trades and quotes, full options chains snapshotted every minute across thousands of underlyings, and billions of rows queried with sub-second aggregations. Also good for dashboards over that data.

**Pairs with:** Python (`clickhouse-connect`, which inserts and returns pandas DataFrames), Rust (`clickhouse` crate), C++ (`clickhouse-cpp`), Go (`clickhouse-go`), Java (JDBC), R (`RClickHouse`). Grafana and Superset connect directly. `chDB` is an embedded version for Python with no server.

**Cost and hosting:** free and open source (Apache 2.0). Self-host with Docker (`clickhouse/clickhouse-server`) or a single binary. ClickHouse Cloud is the managed service (usage-based, with a free trial); prices on https://clickhouse.com/pricing.

## When to choose it

ClickHouse is a columnar server built for append-only analytics at scale, and it is the open-source tool closest to kdb+ for market data. It ingests millions of rows per second and compresses market data heavily. The trade-offs: updates and deletes are asynchronous and expensive (model corrections as new rows, then deduplicate), joins are weaker than in PostgreSQL, and it's a server you have to run. For research on a laptop, [DuckDB](duckdb.md) is simpler; move here when data no longer fits one machine's disk or several people query it at once.

## Schema

```sql
-- Reference schema shared by the workflows.
-- ReplacingMergeTree dedupes rows with the same ORDER BY key during background merges;
-- add FINAL to a query (or GROUP BY the key) when you need exact dedup at read time.

CREATE TABLE IF NOT EXISTS prices_daily
(
    symbol     LowCardinality(String),
    date       Date,
    open       Float64,
    high       Float64,
    low        Float64,
    close      Float64,
    adj_close  Float64,
    volume     UInt64,
    source     LowCardinality(String)
)
ENGINE = ReplacingMergeTree
PARTITION BY toYear(date)
ORDER BY (symbol, source, date);

-- SEC EDGAR XBRL facts as reported. `filed` is the point-in-time key.
CREATE TABLE IF NOT EXISTS statement_facts
(
    cik           LowCardinality(String),
    taxonomy      LowCardinality(String),
    tag           LowCardinality(String),
    unit          LowCardinality(String),
    period_start  Nullable(Date),
    period_end    Date,
    value         Float64,
    fiscal_year   Nullable(UInt16),
    fiscal_period LowCardinality(Nullable(String)),
    form          LowCardinality(Nullable(String)),
    filed         Date,
    accn          String
)
ENGINE = MergeTree
ORDER BY (cik, tag, period_end, filed);

CREATE TABLE IF NOT EXISTS option_quotes
(
    snapshot_ts      DateTime64(3, 'America/New_York'),
    underlying       LowCardinality(String),
    expiry           Date,
    option_type      Enum8('C' = 1, 'P' = 2),
    strike           Float64,
    bid              Float64,
    ask              Float64,
    last             Float64,
    volume           UInt64,
    open_interest    UInt64,
    iv               Float64,
    delta            Float64,
    gamma            Float64,
    vega             Float64,
    theta            Float64,
    underlying_price Float64,
    source           LowCardinality(String)
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(snapshot_ts)
ORDER BY (underlying, snapshot_ts, expiry, option_type, strike, source);

CREATE TABLE IF NOT EXISTS yield_curve
(
    date         Date,
    tenor_months Float64,
    yield_pct    Float64,
    source       LowCardinality(String)
)
ENGINE = ReplacingMergeTree
ORDER BY (date, tenor_months, source);
```

## Queries the workflows rely on

Parameters use ClickHouse's typed `{name:Type}` syntax. From Python: `client.query_df(sql, parameters={"cik": "0000320193", ...})`.

```sql
-- name: annual_fact_as_of
-- argMax(x, filed) keeps the value from the latest filing public on as_of.
SELECT period_end,
       argMax(period_start, filed) AS period_start,
       argMax(value, filed)        AS value,
       max(filed)                  AS filed
FROM statement_facts
WHERE cik = {cik:String} AND tag = {tag:String} AND unit = 'USD' AND filed <= {as_of:Date}
  AND dateDiff('day', period_start, period_end) BETWEEN 350 AND 380
GROUP BY period_end
ORDER BY period_end;

-- name: annual_growth
SELECT period_end, value,
       value / nullIf(lagInFrame(value) OVER (ORDER BY period_end ROWS BETWEEN 1 PRECEDING AND CURRENT ROW), 0) - 1 AS yoy_growth
FROM (
    SELECT period_end, argMax(value, filed) AS value
    FROM statement_facts
    WHERE cik = {cik:String} AND tag = {tag:String} AND unit = 'USD' AND filed <= {as_of:Date}
      AND dateDiff('day', period_start, period_end) BETWEEN 350 AND 380
    GROUP BY period_end
)
ORDER BY period_end;
-- lagInFrame returns 0 (not NULL) on the first row; nullIf turns that into NULL growth.

-- name: daily_returns
SELECT symbol, date,
       adj_close / nullIf(lagInFrame(adj_close) OVER (PARTITION BY symbol ORDER BY date ROWS BETWEEN 1 PRECEDING AND CURRENT ROW), 0) - 1 AS ret
FROM prices_daily FINAL
WHERE symbol = {symbol:String} AND source = {source:String}
ORDER BY date;

-- name: risk_free_rate
SELECT tenor_months, yield_pct / 100 AS rate
FROM yield_curve FINAL
WHERE date = (SELECT max(date) FROM yield_curve WHERE date <= {as_of:Date})
ORDER BY abs(tenor_months - {days_to_expiry:Float64} / 30.4375)
LIMIT 1;

-- name: gex_by_strike
-- Source: SqueezeMetrics, "Gamma Exposure (GEX)" white paper: https://squeezemetrics.com/download/white_paper.pdf
SELECT strike,
       sum(if(option_type = 'C', 1, -1)
           * gamma * open_interest * 100 * underlying_price * underlying_price * 0.01) AS gex_usd
FROM option_quotes FINAL
WHERE underlying = {underlying:String}
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = {underlying:String})
GROUP BY strike
ORDER BY strike;

-- name: put_call_by_expiry
SELECT expiry,
       sumIf(volume, option_type = 'P')        / nullIf(sumIf(volume, option_type = 'C'), 0)        AS pc_volume,
       sumIf(open_interest, option_type = 'P') / nullIf(sumIf(open_interest, option_type = 'C'), 0) AS pc_open_interest
FROM option_quotes FINAL
WHERE underlying = {underlying:String}
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = {underlying:String})
GROUP BY expiry
ORDER BY expiry;
```

## Loading from data sources

Fetch and shape a DataFrame as in [duckdb.md](duckdb.md#loading-from-data-sources), then insert it in one batch. ClickHouse prefers few large inserts (thousands of rows or more) over many small ones. Connection details come from the environment. Env var names: `CLICKHOUSE_HOST`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`.

```python
import os

import clickhouse_connect

client = clickhouse_connect.get_client(
    host=os.environ["CLICKHOUSE_HOST"],
    username=os.environ.get("CLICKHOUSE_USER", "default"),
    password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
)
# `quotes` has the option_quotes columns from duckdb.md, in the same order as the table.
client.insert_df("option_quotes", quotes)
print(client.query("SELECT count() FROM option_quotes").result_rows)
```
