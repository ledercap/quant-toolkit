# DuckDB

**Best for:** local research and analytics: daily bars, financial statement facts, options chain snapshots, yield curves, and fast scans over Parquet or CSV files without loading them first. Handles single-machine datasets from megabytes up to a few hundred gigabytes.

**Pairs with:** Python (`duckdb`, which reads and writes pandas, Polars and Arrow without copying), R (`duckdb` with `dplyr`/`dbplyr`), Julia (`DuckDB.jl`), Rust (`duckdb` crate), C/C++, Java (JDBC) and Node. SQL is the interface in every language.

**Cost and hosting:** free. MIT license. Runs in-process as a library, so there's no server to run; one file (`quant.duckdb`) holds the whole database. MotherDuck offers an optional hosted version.

## When to choose it

Start here. DuckDB is columnar like ClickHouse and kdb+, so aggregations over millions of rows take milliseconds, but it installs with `pip` and lives in one file like SQLite. It can query Parquet files in place, so it also works as the query engine for the [Parquet layout](parquet.md). Move off it when several processes need to write at once (DuckDB allows one writer at a time), when you need a shared server for a team (PostgreSQL), or for tick data at billions of rows a day (ClickHouse, kdb+).

## Schema

```sql
-- Reference schema shared by the workflows. Save as schema.sql.

-- Daily OHLCV bars. One row per symbol, date and source.
CREATE TABLE IF NOT EXISTS prices_daily (
    symbol     VARCHAR NOT NULL,
    date       DATE    NOT NULL,
    open       DOUBLE,
    high       DOUBLE,
    low        DOUBLE,
    close      DOUBLE,
    adj_close  DOUBLE,               -- split- and dividend-adjusted close
    volume     BIGINT,
    source     VARCHAR NOT NULL,     -- file name in data-sources/, e.g. 'massive'
    PRIMARY KEY (symbol, date, source)
);

-- XBRL financial statement facts as reported (SEC EDGAR companyfacts).
-- `filed` is the point-in-time key: a fact is only known from that date on.
-- No primary key: one filing can report the same tag and period end with
-- different start dates (quarter vs year-to-date), and amendments re-report.
CREATE TABLE IF NOT EXISTS statement_facts (
    cik           VARCHAR NOT NULL,  -- 10 digits, zero-padded
    taxonomy      VARCHAR NOT NULL,  -- 'us-gaap', 'dei', 'ifrs-full'
    tag           VARCHAR NOT NULL,  -- e.g. 'NetIncomeLoss'
    unit          VARCHAR NOT NULL,  -- 'USD', 'shares', 'USD-per-shares'
    period_start  DATE,              -- NULL for instant facts (balance sheet)
    period_end    DATE    NOT NULL,
    value         DOUBLE  NOT NULL,
    fiscal_year   INTEGER,           -- fiscal year of the filing, not the fact
    fiscal_period VARCHAR,           -- FY, Q1, Q2, Q3 of the filing
    form          VARCHAR,           -- '10-K', '10-Q', '10-K/A', ...
    filed         DATE    NOT NULL,
    accn          VARCHAR NOT NULL   -- accession number of the filing
);
CREATE INDEX IF NOT EXISTS statement_facts_lookup ON statement_facts (cik, tag);

-- Options chain snapshots. One row per contract per snapshot.
CREATE TABLE IF NOT EXISTS option_quotes (
    snapshot_ts      TIMESTAMP NOT NULL,  -- time the quote was valid (exchange time)
    underlying       VARCHAR   NOT NULL,
    expiry           DATE      NOT NULL,
    option_type      VARCHAR   NOT NULL CHECK (option_type IN ('C', 'P')),
    strike           DOUBLE    NOT NULL,
    bid              DOUBLE,
    ask              DOUBLE,
    last             DOUBLE,
    volume           BIGINT,
    open_interest    BIGINT,
    iv               DOUBLE,              -- annualised, decimal (0.20 = 20%)
    delta            DOUBLE,
    gamma            DOUBLE,              -- per 1.00 move in the underlying
    vega             DOUBLE,
    theta            DOUBLE,
    underlying_price DOUBLE,
    source           VARCHAR   NOT NULL,
    PRIMARY KEY (snapshot_ts, underlying, expiry, option_type, strike, source)
);

-- Treasury par yield curve, long format so new tenors need no schema change.
CREATE TABLE IF NOT EXISTS yield_curve (
    date         DATE    NOT NULL,
    tenor_months DOUBLE  NOT NULL,   -- 1, 1.5, 2, 3, 4, 6, 12, 24, ... 360
    yield_pct    DOUBLE  NOT NULL,   -- percent, as published (4.25 = 4.25%)
    source       VARCHAR NOT NULL,
    PRIMARY KEY (date, tenor_months, source)
);

-- Macro series (FRED and others). realtime_start keeps ALFRED vintages;
-- for plain pulls set it to the date you fetched the data.
CREATE TABLE IF NOT EXISTS macro_observations (
    series_id      VARCHAR NOT NULL,
    date           DATE    NOT NULL,
    value          DOUBLE,           -- NULL where the source reports a gap ('.')
    realtime_start DATE    NOT NULL,
    source         VARCHAR NOT NULL,
    PRIMARY KEY (series_id, date, realtime_start, source)
);
```

## Queries the workflows rely on

Parameters use DuckDB's `$name` syntax. From Python: `con.execute(sql, {"cik": "0000320193", ...})`.

```sql
-- name: annual_fact_as_of
-- One value per fiscal year for a tag, using only filings public on $as_of.
-- Annual = a duration fact of 350 to 380 days. Latest filing wins (restatements).
-- arg_max(x, filed) takes x from the latest filing. (A QUALIFY / row_number() version
-- of this query hits an internal error in DuckDB 1.5.x; arg_max works in 1.4 and 1.5.)
SELECT arg_max(period_start, filed) AS period_start,
       period_end,
       arg_max(value, filed)        AS value,
       max(filed)                   AS filed,
       arg_max(form, filed)         AS form
FROM statement_facts
WHERE cik = $cik
  AND tag = $tag
  AND unit = 'USD'
  AND filed <= $as_of
  AND date_diff('day', period_start, period_end) BETWEEN 350 AND 380
GROUP BY period_end
ORDER BY period_end;

-- name: annual_growth
-- Year-over-year growth for a tag, point-in-time as of $as_of.
WITH annual AS (
    SELECT period_end, arg_max(value, filed) AS value
    FROM statement_facts
    WHERE cik = $cik AND tag = $tag AND unit = 'USD' AND filed <= $as_of
      AND date_diff('day', period_start, period_end) BETWEEN 350 AND 380
    GROUP BY period_end
)
SELECT period_end,
       value,
       value / lag(value) OVER (ORDER BY period_end) - 1 AS yoy_growth
FROM annual
ORDER BY period_end;

-- name: daily_returns
-- Simple daily returns from adjusted closes.
SELECT symbol,
       date,
       adj_close / lag(adj_close) OVER (PARTITION BY symbol ORDER BY date) - 1 AS ret
FROM prices_daily
WHERE symbol = $symbol AND source = $source
ORDER BY date;

-- name: risk_free_rate
-- Treasury yield (decimal) for the tenor nearest $days_to_expiry,
-- from the latest curve published on or before $as_of.
SELECT tenor_months, yield_pct / 100 AS rate
FROM yield_curve
WHERE date = (SELECT max(date) FROM yield_curve WHERE date <= $as_of)
ORDER BY abs(tenor_months - $days_to_expiry / 30.4375)
LIMIT 1;

-- name: gex_by_strike
-- Source: SqueezeMetrics, "Gamma Exposure (GEX)" white paper: https://squeezemetrics.com/download/white_paper.pdf
-- Dollar gamma exposure per 1% move, by strike, for the latest snapshot.
-- Convention (SqueezeMetrics): dealers are long calls (+) and short puts (-).
-- 100 = contract multiplier for US equity and index options.
SELECT strike,
       sum(CASE option_type WHEN 'C' THEN 1 ELSE -1 END
           * gamma * open_interest * 100 * underlying_price * underlying_price * 0.01) AS gex_usd
FROM option_quotes
WHERE underlying = $underlying
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = $underlying)
GROUP BY strike
ORDER BY strike;

-- name: put_call_by_expiry
-- Put/call ratios by volume and by open interest for the latest snapshot.
SELECT expiry,
       sum(volume)        FILTER (WHERE option_type = 'P') / nullif(sum(volume)        FILTER (WHERE option_type = 'C'), 0) AS pc_volume,
       sum(open_interest) FILTER (WHERE option_type = 'P') / nullif(sum(open_interest) FILTER (WHERE option_type = 'C'), 0) AS pc_open_interest
FROM option_quotes
WHERE underlying = $underlying
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = $underlying)
GROUP BY expiry
ORDER BY expiry;
```

## Loading from data sources

DuckDB inserts straight from a pandas DataFrame that is in scope (`INSERT INTO t SELECT * FROM df`), so each loader is "fetch, shape into the table's columns, insert". The three loaders below cover [sec-edgar.md](../data-sources/sec-edgar.md), [us-treasury-yield-curve.md](../data-sources/us-treasury-yield-curve.md) and [cboe-delayed-quotes.md](../data-sources/cboe-delayed-quotes.md). `prices_daily` and `macro_observations` load the same way from any price source or FRED.

```python
import os
import re

import duckdb
import pandas as pd
import requests

con = duckdb.connect("quant.duckdb")
con.execute(open("schema.sql").read())

# SEC EDGAR: flatten companyfacts into statement_facts.
cik = "0000320193"
facts = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                     headers={"User-Agent": os.environ["SEC_USER_AGENT"]}, timeout=60).json()["facts"]
edgar = pd.DataFrame(
    [(cik, taxonomy, tag, unit, f.get("start"), f["end"], f["val"], f.get("fy"), f.get("fp"), f.get("form"), f["filed"], f["accn"])
     for taxonomy, tags in facts.items()
     for tag, body in tags.items()
     for unit, items in body["units"].items()
     for f in items],
    columns=["cik", "taxonomy", "tag", "unit", "period_start", "period_end", "value",
             "fiscal_year", "fiscal_period", "form", "filed", "accn"],
)
con.execute("DELETE FROM statement_facts WHERE cik = ?", [cik])  # reload one company at a time
con.execute("INSERT INTO statement_facts SELECT * FROM edgar")

# US Treasury: wide CSV (one column per tenor) to long rows.
year = 2026
curve = pd.read_csv(
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    f"daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
)
curve = curve.melt(id_vars="Date", var_name="tenor", value_name="yield_pct").dropna()
num = curve["tenor"].str.extract(r"([\d.]+)")[0].astype(float)
curve["tenor_months"] = num.where(curve["tenor"].str.contains("Mo"), num * 12)  # 'Mo'/'Month' vs 'Yr'
curve["date"] = pd.to_datetime(curve["Date"]).dt.date
curve["source"] = "us-treasury-yield-curve"
curve = curve[["date", "tenor_months", "yield_pct", "source"]]
con.execute("INSERT OR REPLACE INTO yield_curve SELECT * FROM curve")

# Cboe: one options chain snapshot.
data = requests.get("https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=30).json()
chain = pd.DataFrame(data["data"]["options"])
parts = chain["option"].str.extract(r"^(?P<root>[A-Z.]+)(?P<ymd>\d{6})(?P<cp>[CP])(?P<k>\d{8})$")
quotes = pd.DataFrame({
    "snapshot_ts": pd.Timestamp(data["timestamp"]),
    "underlying": "SPY",
    "expiry": pd.to_datetime(parts["ymd"], format="%y%m%d").dt.date,
    "option_type": parts["cp"],
    "strike": parts["k"].astype(int) / 1000,
    "bid": chain["bid"], "ask": chain["ask"], "last": chain["last_trade_price"],
    "volume": chain["volume"].astype("int64"), "open_interest": chain["open_interest"].astype("int64"),
    "iv": chain["iv"], "delta": chain["delta"], "gamma": chain["gamma"],
    "vega": chain["vega"], "theta": chain["theta"],
    "underlying_price": data["data"]["current_price"],
    "source": "cboe-delayed-quotes",
})
con.execute("INSERT OR REPLACE INTO option_quotes SELECT * FROM quotes")

print(con.execute("SELECT count(*) FROM statement_facts").fetchone(),
      con.execute("SELECT count(*) FROM option_quotes").fetchone())
```
