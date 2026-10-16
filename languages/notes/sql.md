# SQL

**When to reach for it:** storing and querying everything the data sources return. Use it for joins, filters, aggregations, window functions (returns, rolling stats, ranking) and point-in-time lookups. It works alongside Python, not instead of it. The dialects used in this repo are in [databases/](../../databases/README.md).

## Scores

| Capability | Score | Why |
| --- | --- | --- |
| Data wrangling and cleaning | 4 | Joins, group-bys, pivots and window functions are concise and run fast in columnar engines (DuckDB, ClickHouse). Loses a point because cleaning messy text and nested JSON is clumsier than in pandas. |
| Financial statement analysis | 4 | Point-in-time fact lookup, ratios and growth are natural set operations; see `annual_fact_as_of` and `annual_growth` in [databases/duckdb.md](../../databases/duckdb.md). Loses a point because fetching and mapping XBRL tags happens outside SQL. |
| Time series and econometrics | 2 | Window functions handle returns, rolling means and lags, and TimescaleDB adds time buckets and gap filling. No modelling: no regressions beyond simple aggregates, no GARCH or ARIMA. |
| Options pricing and Greeks | 1 | Many dialects lack a normal CDF and there's no root-finding, so pricing and implied vol aren't practical. SQL aggregates Greeks that come from elsewhere (see `gex_by_strike`). |
| Backtesting | 2 | Simple vectorised signal backtests are possible with window functions. Anything with position state, costs or event ordering belongs in a real backtester. |
| Low-latency and HFT execution | 1 | A query language, not an execution environment. |
| Numerical computation at scale | 3 | Columnar engines scan and aggregate billions of rows quickly, but only for set-based arithmetic, not general numerics. |
| Machine learning | 2 | Some in-database ML exists (BigQuery ML, PostgresML), but features are built in SQL and models trained in Python. |
| Visualisation and reporting | 2 | No charting of its own; feeds BI tools (Grafana, Metabase, Superset) that turn queries into dashboards. |
| Native fit with data sources | 3 | DuckDB reads CSV and Parquet straight from a URL (the Treasury curve, SqueezeMetrics and ECB files here), but authenticated JSON APIs need another language. |
| Ecosystem and hiring pool | 5 | Expected in almost every data, analyst and quant role. Every database and language supports it. |

## Libraries and engines

- Engines: [DuckDB](https://duckdb.org), [SQLite](https://sqlite.org), [PostgreSQL](https://www.postgresql.org) with [TimescaleDB](https://github.com/timescale/timescaledb), [ClickHouse](https://clickhouse.com)
- Window functions reference: [DuckDB window functions](https://duckdb.org/docs/sql/functions/window_functions), [PostgreSQL window functions](https://www.postgresql.org/docs/current/tutorial-window.html)
- Dashboards: [Grafana](https://grafana.com), [Metabase](https://www.metabase.com), [Apache Superset](https://superset.apache.org)
