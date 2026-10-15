# Databases

How to store and query what the data sources return. One file per database or storage pattern, from `_TEMPLATE.md`.

Each entry answers: which workloads it fits (tick data, daily bars, fundamentals, filings text), which language pairs with it best, and gives the schemas and queries the workflows depend on.

## Index

| Database | Type | Best for | Cost | File |
| --- | --- | --- | --- | --- |
| ArcticDB | Embedded, versioned DataFrame store (Python) | Versioned time series, time travel | Free for personal/academic; business use needs a license | [arcticdb.md](arcticdb.md) |
| ClickHouse | Columnar server | Tick data and analytics at scale | Free (Apache 2.0); managed cloud paid | [clickhouse.md](clickhouse.md) |
| DuckDB | Embedded columnar SQL | Local research and analytics; queries Parquet in place | Free (MIT) | [duckdb.md](duckdb.md) |
| kdb+ / KDB-X and q | Columnar time-series database and language | Bank-scale tick data, as-of joins | Free Community Edition with limits; commercial license expensive | [kdb.md](kdb.md) |
| Parquet files | Open columnar file format | Long-term archive read by every tool | Free; storage cost only | [parquet.md](parquet.md) |
| PostgreSQL and TimescaleDB | Relational server plus time-series extension | Shared team or app database | Free to self-host; managed services paid | [postgresql-timescaledb.md](postgresql-timescaledb.md) |
| SQLite | Embedded row-store SQL | App state, metadata, small datasets, portable files | Free (public domain) | [sqlite.md](sqlite.md) |

Keep this table in alphabetical order and add a row whenever you add a file.

## Which one to use

| Situation | Use |
| --- | --- |
| Research on one machine (the default for this repo) | **DuckDB**, with raw fetches archived as **Parquet** |
| App state, symbol maps, fetch logs | **SQLite** |
| Several people or an app writing at once | **PostgreSQL** (add **TimescaleDB** for time series) |
| Billions of rows of tick or minute data | **ClickHouse** (open source) or **kdb+** (industry standard, licensed) |
| Need to see exactly what a series looked like before a re-fetch | **ArcticDB** (check the license for business use) |

## Shared reference schema

Every entry implements the same five datasets with the same column names (dialects differ), so workflows can move between stores:

| Table | Grain | Fed by |
| --- | --- | --- |
| `prices_daily` | symbol × date × source | Massive, Alpha Vantage, yfinance, Tradier |
| `statement_facts` | one XBRL fact per filing, point-in-time on `filed` | SEC EDGAR |
| `option_quotes` | contract × snapshot | Cboe delayed quotes, Tradier, Massive |
| `yield_curve` | date × tenor (long format) | US Treasury yield curve, FRED |
| `macro_observations` | series × date × vintage | FRED (ALFRED vintages), EIA, ECB |

And the same six queries: `annual_fact_as_of`, `annual_growth`, `daily_returns`, `risk_free_rate`, `gex_by_strike`, `put_call_by_expiry`.

## Review log

**Batch 1, 2026-10-15** (7 entries). Re-run from a fresh clone on Python 3.11. Tested entries had their schema created, real data loaded (Apple's SEC EDGAR facts and an SPY Cboe chain), and every query run. All tested stores returned identical results.

| File | Tested? | Notes for reviewers |
| --- | --- | --- |
| arcticdb.md | Yes (ArcticDB 6.28, LMDB) | Nullable pandas dtypes fail to write; duplicate appends aren't rejected. Both are handled in the loader. |
| clickhouse.md | No | No server available here, and embedded chDB wouldn't load on this macOS. Check syntax before relying on it. |
| duckdb.md | Yes (DuckDB 1.4.5 and 1.5.6) | Reference implementation; loaders for EDGAR, Treasury and Cboe all ran. Point-in-time queries use `arg_max` because the `QUALIFY` form crashes DuckDB 1.5.x. |
| kdb.md | No | Needs a KX license. q code is written by hand; check it in a q session. |
| parquet.md | Yes (pyarrow + DuckDB 1.4.5 and 1.5.6) | |
| postgresql-timescaledb.md | No | No PostgreSQL server available here. Standard SQL plus TimescaleDB calls. |
| sqlite.md | Yes (SQLite 3.54) | |
