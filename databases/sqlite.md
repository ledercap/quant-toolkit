# SQLite

**Best for:** small, row-oriented storage: a watchlist, a symbol and CIK map, fetch logs and job state, cached API responses, and modest daily-bar or statement datasets (up to a few million rows). Also the default for anything that has to ship as one portable file.

**Pairs with:** every language. Python (`sqlite3` in the standard library), R (`RSQLite`), C/C++ (the SQLite C library itself), Rust (`rusqlite`), Julia (`SQLite.jl`), Go, Java, Node. Opens in DB Browser for SQLite for quick inspection.

**Cost and hosting:** free. Public domain. Runs in-process with zero setup; the database is one file. Already installed with Python and macOS.

## When to choose it

Pick SQLite when you need reliable transactional storage with no dependencies, or a file you can hand to anyone. It stores rows, not columns, so wide scans and aggregations (a year of option chains, a GEX across every snapshot) are 10 to 100 times slower than [DuckDB](duckdb.md). A common setup is SQLite for app state and metadata and DuckDB or Parquet for the analytical data. It allows one writer at a time; turn on WAL mode (`PRAGMA journal_mode=WAL`) so readers don't block it.

## Schema

```sql
-- Reference schema shared by the workflows. Save as schema.sql.
-- SQLite has no DATE type: dates are ISO-8601 TEXT ('2026-10-14'), which sorts correctly.

PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS prices_daily (
    symbol     TEXT    NOT NULL,
    date       TEXT    NOT NULL,     -- YYYY-MM-DD
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL,
    adj_close  REAL,                 -- split- and dividend-adjusted close
    volume     INTEGER,
    source     TEXT    NOT NULL,     -- file name in data-sources/
    PRIMARY KEY (symbol, date, source)
);

-- SEC EDGAR XBRL facts as reported. `filed` is the point-in-time key.
CREATE TABLE IF NOT EXISTS statement_facts (
    cik           TEXT    NOT NULL,  -- 10 digits, zero-padded
    taxonomy      TEXT    NOT NULL,
    tag           TEXT    NOT NULL,
    unit          TEXT    NOT NULL,
    period_start  TEXT,              -- NULL for instant facts (balance sheet)
    period_end    TEXT    NOT NULL,
    value         REAL    NOT NULL,
    fiscal_year   INTEGER,
    fiscal_period TEXT,
    form          TEXT,
    filed         TEXT    NOT NULL,
    accn          TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS statement_facts_lookup ON statement_facts (cik, tag, filed);

CREATE TABLE IF NOT EXISTS option_quotes (
    snapshot_ts      TEXT    NOT NULL,  -- 'YYYY-MM-DD HH:MM:SS', exchange time
    underlying       TEXT    NOT NULL,
    expiry           TEXT    NOT NULL,
    option_type      TEXT    NOT NULL CHECK (option_type IN ('C', 'P')),
    strike           REAL    NOT NULL,
    bid              REAL,
    ask              REAL,
    last             REAL,
    volume           INTEGER,
    open_interest    INTEGER,
    iv               REAL,              -- decimal (0.20 = 20%)
    delta            REAL,
    gamma            REAL,
    vega             REAL,
    theta            REAL,
    underlying_price REAL,
    source           TEXT    NOT NULL,
    PRIMARY KEY (snapshot_ts, underlying, expiry, option_type, strike, source)
);

CREATE TABLE IF NOT EXISTS yield_curve (
    date         TEXT NOT NULL,
    tenor_months REAL NOT NULL,      -- 1, 1.5, 2, 3, 4, 6, 12, ... 360
    yield_pct    REAL NOT NULL,      -- percent, as published
    source       TEXT NOT NULL,
    PRIMARY KEY (date, tenor_months, source)
);

CREATE TABLE IF NOT EXISTS macro_observations (
    series_id      TEXT NOT NULL,
    date           TEXT NOT NULL,
    value          REAL,             -- NULL where the source reports a gap
    realtime_start TEXT NOT NULL,    -- ALFRED vintage, or the fetch date
    source         TEXT NOT NULL,
    PRIMARY KEY (series_id, date, realtime_start, source)
);
```

## Queries the workflows rely on

Parameters use `:name` syntax. From Python: `con.execute(sql, {"cik": "0000320193", ...})`. Needs SQLite 3.30 or newer for window functions and `FILTER`.

```sql
-- name: annual_fact_as_of
-- One value per fiscal year for a tag, using only filings public on :as_of.
SELECT period_start, period_end, value, filed, form
FROM (
    SELECT *, row_number() OVER (PARTITION BY period_end ORDER BY filed DESC) AS rn
    FROM statement_facts
    WHERE cik = :cik AND tag = :tag AND unit = 'USD' AND filed <= :as_of
      AND julianday(period_end) - julianday(period_start) BETWEEN 350 AND 380
)
WHERE rn = 1
ORDER BY period_end;

-- name: annual_growth
WITH annual AS (
    SELECT period_end, value
    FROM (
        SELECT *, row_number() OVER (PARTITION BY period_end ORDER BY filed DESC) AS rn
        FROM statement_facts
        WHERE cik = :cik AND tag = :tag AND unit = 'USD' AND filed <= :as_of
          AND julianday(period_end) - julianday(period_start) BETWEEN 350 AND 380
    )
    WHERE rn = 1
)
SELECT period_end, value,
       value / lag(value) OVER (ORDER BY period_end) - 1 AS yoy_growth
FROM annual
ORDER BY period_end;

-- name: daily_returns
SELECT symbol, date,
       adj_close / lag(adj_close) OVER (PARTITION BY symbol ORDER BY date) - 1 AS ret
FROM prices_daily
WHERE symbol = :symbol AND source = :source
ORDER BY date;

-- name: risk_free_rate
-- Yield (decimal) at the tenor nearest :days_to_expiry, latest curve on or before :as_of.
SELECT tenor_months, yield_pct / 100.0 AS rate
FROM yield_curve
WHERE date = (SELECT max(date) FROM yield_curve WHERE date <= :as_of)
ORDER BY abs(tenor_months - :days_to_expiry / 30.4375)
LIMIT 1;

-- name: gex_by_strike
-- Source: SqueezeMetrics, "Gamma Exposure (GEX)" white paper: https://squeezemetrics.com/download/white_paper.pdf
-- Dollar gamma per 1% move; dealers long calls (+), short puts (-); 100 = multiplier.
SELECT strike,
       sum(CASE option_type WHEN 'C' THEN 1 ELSE -1 END
           * gamma * open_interest * 100 * underlying_price * underlying_price * 0.01) AS gex_usd
FROM option_quotes
WHERE underlying = :underlying
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = :underlying)
GROUP BY strike
ORDER BY strike;

-- name: put_call_by_expiry
SELECT expiry,
       1.0 * sum(volume)        FILTER (WHERE option_type = 'P') / nullif(sum(volume)        FILTER (WHERE option_type = 'C'), 0) AS pc_volume,
       1.0 * sum(open_interest) FILTER (WHERE option_type = 'P') / nullif(sum(open_interest) FILTER (WHERE option_type = 'C'), 0) AS pc_open_interest
FROM option_quotes
WHERE underlying = :underlying
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = :underlying)
GROUP BY expiry
ORDER BY expiry;
```

## Loading from data sources

Build a pandas DataFrame with the table's columns (the fetch-and-shape code is the same as in [duckdb.md](duckdb.md#loading-from-data-sources)), then append it with `to_sql`. Dates must be ISO strings. Example for [sec-edgar.md](../data-sources/sec-edgar.md):

```python
import os
import sqlite3

import pandas as pd
import requests

con = sqlite3.connect("quant.sqlite")
con.executescript(open("schema.sql").read())

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
with con:  # one transaction: replace this company's facts atomically
    con.execute("DELETE FROM statement_facts WHERE cik = ?", (cik,))
    edgar.to_sql("statement_facts", con, if_exists="append", index=False)

print(con.execute("SELECT count(*) FROM statement_facts").fetchone())
```

For tables with a primary key (`prices_daily`, `option_quotes`, `yield_curve`), use `INSERT OR REPLACE` through `con.executemany(...)` so a re-fetch overwrites rows instead of failing on duplicates.
