# PostgreSQL and TimescaleDB

**Best for:** a shared database server for a team or an app: daily bars, statement facts, options snapshots, macro series and app data (users, watchlists, alerts) in one place with real concurrency. With the TimescaleDB extension it also handles time series from minute bars to moderate tick volumes.

**Pairs with:** Python (`psycopg` 3, SQLAlchemy, pandas `read_sql`), R (`RPostgres`, `DBI`), Rust (`sqlx`, `tokio-postgres`), C++ (`libpqxx`), Julia (`LibPQ.jl`), Java (JDBC), Go, Node. Every BI tool connects to it (Grafana, Metabase, Superset).

**Cost and hosting:** PostgreSQL is free (PostgreSQL License, permissive). TimescaleDB is a PostgreSQL extension: the core is Apache 2.0, and features such as compression and continuous aggregates are under the Timescale License, which is free to self-host but forbids offering it as a database service to others. Run locally with Docker (`timescale/timescaledb` image), or use a managed service: Tiger Cloud from Tiger Data (formerly Timescale), or managed PostgreSQL from AWS RDS, Supabase or Neon, where the TimescaleDB extension may not be available.

## When to choose it

Choose PostgreSQL when more than one person or process writes at the same time, when an app or dashboard needs a server to connect to, or when you need transactions and constraints across tables. It is row-oriented, so plain PostgreSQL is slower than DuckDB or ClickHouse for big scans. TimescaleDB closes much of that gap: hypertables split tables into time chunks automatically, and compression stores old chunks in a columnar layout. For billions of ticks a day, look at [ClickHouse](clickhouse.md) or [kdb+](kdb.md).

## Schema

```sql
-- Reference schema shared by the workflows. Requires: CREATE EXTENSION IF NOT EXISTS timescaledb;
-- Without TimescaleDB, skip the create_hypertable / compression lines; the rest is plain PostgreSQL.

CREATE TABLE IF NOT EXISTS prices_daily (
    symbol     TEXT             NOT NULL,
    date       DATE             NOT NULL,
    open       DOUBLE PRECISION,
    high       DOUBLE PRECISION,
    low        DOUBLE PRECISION,
    close      DOUBLE PRECISION,
    adj_close  DOUBLE PRECISION,
    volume     BIGINT,
    source     TEXT             NOT NULL,
    PRIMARY KEY (symbol, date, source)
);
SELECT create_hypertable('prices_daily', by_range('date', INTERVAL '1 year'), if_not_exists => TRUE);

-- SEC EDGAR XBRL facts as reported. `filed` is the point-in-time key.
CREATE TABLE IF NOT EXISTS statement_facts (
    cik           TEXT             NOT NULL,
    taxonomy      TEXT             NOT NULL,
    tag           TEXT             NOT NULL,
    unit          TEXT             NOT NULL,
    period_start  DATE,
    period_end    DATE             NOT NULL,
    value         DOUBLE PRECISION NOT NULL,
    fiscal_year   INTEGER,
    fiscal_period TEXT,
    form          TEXT,
    filed         DATE             NOT NULL,
    accn          TEXT             NOT NULL
);
CREATE INDEX IF NOT EXISTS statement_facts_lookup ON statement_facts (cik, tag, filed);

CREATE TABLE IF NOT EXISTS option_quotes (
    snapshot_ts      TIMESTAMPTZ      NOT NULL,
    underlying       TEXT             NOT NULL,
    expiry           DATE             NOT NULL,
    option_type      CHAR(1)          NOT NULL CHECK (option_type IN ('C', 'P')),
    strike           DOUBLE PRECISION NOT NULL,
    bid              DOUBLE PRECISION,
    ask              DOUBLE PRECISION,
    last             DOUBLE PRECISION,
    volume           BIGINT,
    open_interest    BIGINT,
    iv               DOUBLE PRECISION,
    delta            DOUBLE PRECISION,
    gamma            DOUBLE PRECISION,
    vega             DOUBLE PRECISION,
    theta            DOUBLE PRECISION,
    underlying_price DOUBLE PRECISION,
    source           TEXT             NOT NULL,
    PRIMARY KEY (snapshot_ts, underlying, expiry, option_type, strike, source)
);
SELECT create_hypertable('option_quotes', by_range('snapshot_ts', INTERVAL '1 day'), if_not_exists => TRUE);
-- Compress chunks older than 7 days, grouped by underlying (Timescale License feature).
ALTER TABLE option_quotes SET (timescaledb.compress, timescaledb.compress_segmentby = 'underlying');
SELECT add_compression_policy('option_quotes', INTERVAL '7 days', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS yield_curve (
    date         DATE             NOT NULL,
    tenor_months DOUBLE PRECISION NOT NULL,
    yield_pct    DOUBLE PRECISION NOT NULL,
    source       TEXT             NOT NULL,
    PRIMARY KEY (date, tenor_months, source)
);

CREATE TABLE IF NOT EXISTS macro_observations (
    series_id      TEXT             NOT NULL,
    date           DATE             NOT NULL,
    value          DOUBLE PRECISION,
    realtime_start DATE             NOT NULL,
    source         TEXT             NOT NULL,
    PRIMARY KEY (series_id, date, realtime_start, source)
);
```

## Queries the workflows rely on

Parameters use psycopg's `%(name)s` syntax: `cur.execute(sql, {"cik": "0000320193", ...})`.

```sql
-- name: annual_fact_as_of
-- DISTINCT ON keeps the first row per period_end: the latest filing public on as_of.
SELECT DISTINCT ON (period_end) period_start, period_end, value, filed, form
FROM statement_facts
WHERE cik = %(cik)s AND tag = %(tag)s AND unit = 'USD' AND filed <= %(as_of)s
  AND period_end - period_start BETWEEN 350 AND 380
ORDER BY period_end, filed DESC;

-- name: annual_growth
WITH annual AS (
    SELECT DISTINCT ON (period_end) period_end, value
    FROM statement_facts
    WHERE cik = %(cik)s AND tag = %(tag)s AND unit = 'USD' AND filed <= %(as_of)s
      AND period_end - period_start BETWEEN 350 AND 380
    ORDER BY period_end, filed DESC
)
SELECT period_end, value, value / lag(value) OVER (ORDER BY period_end) - 1 AS yoy_growth
FROM annual
ORDER BY period_end;

-- name: daily_returns
SELECT symbol, date,
       adj_close / lag(adj_close) OVER (PARTITION BY symbol ORDER BY date) - 1 AS ret
FROM prices_daily
WHERE symbol = %(symbol)s AND source = %(source)s
ORDER BY date;

-- name: risk_free_rate
SELECT tenor_months, yield_pct / 100 AS rate
FROM yield_curve
WHERE date = (SELECT max(date) FROM yield_curve WHERE date <= %(as_of)s)
ORDER BY abs(tenor_months - %(days_to_expiry)s / 30.4375)
LIMIT 1;

-- name: gex_by_strike
-- Source: SqueezeMetrics, "Gamma Exposure (GEX)" white paper: https://squeezemetrics.com/download/white_paper.pdf
SELECT strike,
       sum(CASE option_type WHEN 'C' THEN 1 ELSE -1 END
           * gamma * open_interest * 100 * underlying_price * underlying_price * 0.01) AS gex_usd
FROM option_quotes
WHERE underlying = %(underlying)s
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = %(underlying)s)
GROUP BY strike
ORDER BY strike;

-- name: put_call_by_expiry
SELECT expiry,
       sum(volume)        FILTER (WHERE option_type = 'P')::float / nullif(sum(volume)        FILTER (WHERE option_type = 'C'), 0) AS pc_volume,
       sum(open_interest) FILTER (WHERE option_type = 'P')::float / nullif(sum(open_interest) FILTER (WHERE option_type = 'C'), 0) AS pc_open_interest
FROM option_quotes
WHERE underlying = %(underlying)s
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = %(underlying)s)
GROUP BY expiry
ORDER BY expiry;

-- name: daily_gex_history (TimescaleDB)
-- Total GEX per underlying per day from the last snapshot of each day.
SELECT time_bucket('1 day', snapshot_ts) AS day, underlying,
       sum(CASE option_type WHEN 'C' THEN 1 ELSE -1 END
           * gamma * open_interest * 100 * underlying_price * underlying_price * 0.01) AS gex_usd
FROM option_quotes
WHERE (underlying, snapshot_ts) IN (
    SELECT underlying, max(snapshot_ts) FROM option_quotes GROUP BY underlying, time_bucket('1 day', snapshot_ts)
)
GROUP BY day, underlying
ORDER BY day, underlying;
```

## Loading from data sources

Fetch and shape a DataFrame as in [duckdb.md](duckdb.md#loading-from-data-sources), then stream it in with `COPY`, which is far faster than row-by-row inserts. The connection string comes from the environment. Env var name: `DATABASE_URL`, for example `postgresql://user@localhost:5432/quant`.

```python
import os

import psycopg

# `edgar` has the statement_facts columns from duckdb.md.
cols = list(edgar.columns)
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM statement_facts WHERE cik = %s", (edgar["cik"].iloc[0],))
        with cur.copy(f"COPY statement_facts ({', '.join(cols)}) FROM STDIN") as copy:
            for row in edgar.astype(object).where(edgar.notna(), None).itertuples(index=False):
                copy.write_row(row)
    # leaving the block commits the transaction
```

For tables with a primary key, `COPY` into a temporary table and then `INSERT ... SELECT ... ON CONFLICT DO UPDATE` to upsert.
