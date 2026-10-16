# Parquet files (local or object storage)

**Best for:** the long-term archive of everything you fetch: daily bars, options chain snapshots, statement facts, yield curves. It suits append-heavy, read-mostly data that grows to tens or hundreds of gigabytes, and data that several tools and languages need to read.

**Pairs with:** DuckDB as the query engine (see [duckdb.md](duckdb.md)). Writers and readers: Python (`pyarrow`, `pandas`, `polars`), R (`arrow`), Rust (`arrow-rs`/`parquet`, `polars`), Julia (`Parquet2.jl`), C++ (Arrow C++), Spark, ClickHouse and most cloud warehouses.

**Cost and hosting:** free, open format (Apache Parquet, Apache 2.0 license). On local disk it costs nothing. On object storage you pay per GB per month; prices vary by provider, region and storage class, so check the current S3, Google Cloud Storage or Cloudflare R2 price pages (R2 has no egress fees). Nothing to run or maintain.

## When to choose it

Parquet is a file format, not a database: there's no server, no locking and no updates in place. In exchange you get compressed columnar files (often 5 to 10 times smaller than CSV) that any modern tool can read, and that DuckDB, Polars or ClickHouse can scan at close to native-database speed. Use it as the archive layer and put a query engine on top. Avoid it for data that changes row by row; rewrite whole partitions instead, or use [ArcticDB](arcticdb.md) or a real database. Keep the lake folder out of git (`*.parquet` is already in `.gitignore`).

## Schema

Hive-style partition folders (`key=value`) let query engines skip files that don't match a filter. The layout and the DuckDB views that expose it as tables:

```sql
-- Folder layout (one dataset per top-level folder):
--   lake/prices_daily/source=<source>/year=<YYYY>/part-*.parquet
--   lake/statement_facts/cik=<10-digit CIK>/facts.parquet
--   lake/option_quotes/underlying=<SYM>/date=<YYYY-MM-DD>/snapshot-<HHMMSS>.parquet
--   lake/yield_curve/year=<YYYY>/part-*.parquet
--   lake/macro_observations/source=<source>/series_id=<ID>/part-*.parquet   (one file per vintage or fetch)
--
-- Columns are the same as the tables in duckdb.md; partition keys come back as columns.
-- Run in DuckDB (in memory or a file) to expose the lake as tables:

CREATE OR REPLACE VIEW prices_daily AS
    SELECT * FROM read_parquet('lake/prices_daily/**/*.parquet', hive_partitioning = true);
CREATE OR REPLACE VIEW statement_facts AS
    SELECT * FROM read_parquet('lake/statement_facts/**/*.parquet', hive_partitioning = true);
CREATE OR REPLACE VIEW option_quotes AS
    SELECT * FROM read_parquet('lake/option_quotes/**/*.parquet', hive_partitioning = true);
CREATE OR REPLACE VIEW yield_curve AS
    SELECT * FROM read_parquet('lake/yield_curve/**/*.parquet', hive_partitioning = true);
CREATE OR REPLACE VIEW macro_observations AS
    SELECT * FROM read_parquet('lake/macro_observations/**/*.parquet', hive_partitioning = true);

-- On object storage, swap the path: 's3://<bucket>/lake/option_quotes/**/*.parquet'
-- after `INSTALL httpfs; LOAD httpfs;` and credentials from the environment
-- (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY, read by `CREATE SECRET (TYPE s3, PROVIDER credential_chain)`).
```

## Queries the workflows rely on

Once the views exist, every query in [duckdb.md](duckdb.md#queries-the-workflows-rely-on) runs unchanged. The two that benefit most from partition pruning:

```sql
-- name: gex_by_strike
-- Source: SqueezeMetrics, "Gamma Exposure (GEX)" white paper: https://squeezemetrics.com/download/white_paper.pdf
-- Reads only the SPY folder and only the latest date folder.
-- Caveat: `gamma` is the gamma the source published. Cboe rounds it to 4 decimals, which for SPX
-- (gammas near 0.001) is enough to flip the sign of the total. Use this query for the strike-level
-- shape; for a precise total, recompute gamma from `iv` as workflows/options/gamma does.
SELECT strike,
       sum(CASE option_type WHEN 'C' THEN 1 ELSE -1 END
           * gamma * open_interest * 100 * underlying_price * underlying_price * 0.01) AS gex_usd
FROM option_quotes
WHERE underlying = $underlying
  AND snapshot_ts = (SELECT max(snapshot_ts) FROM option_quotes WHERE underlying = $underlying)
GROUP BY strike
ORDER BY strike;

-- name: annual_fact_as_of
-- Reads only the one company's folder.
-- arg_max(x, filed) takes x from the latest filing (works in DuckDB 1.4 and 1.5).
SELECT arg_max(period_start, filed) AS period_start, period_end,
       arg_max(value, filed) AS value, max(filed) AS filed, arg_max(form, filed) AS form
FROM statement_facts
WHERE cik = $cik AND tag = $tag AND unit = 'USD' AND filed <= $as_of
  AND date_diff('day', period_start, period_end) BETWEEN 350 AND 380
GROUP BY period_end
ORDER BY period_end;
```

## Loading from data sources

Fetch and shape a DataFrame exactly as in [duckdb.md](duckdb.md#loading-from-data-sources), then write it to its partition folder. Each options snapshot gets its own file, so appends never rewrite old data:

```python
from pathlib import Path

import pandas as pd


def write_option_snapshot(quotes: pd.DataFrame, lake: Path = Path("lake")) -> Path:
    """Write one chain snapshot (columns as in duckdb.md option_quotes) to the lake."""
    ts = pd.Timestamp(quotes["snapshot_ts"].iloc[0])
    folder = lake / "option_quotes" / f"underlying={quotes['underlying'].iloc[0]}" / f"date={ts.date()}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"snapshot-{ts:%H%M%S}.parquet"
    # Partition keys live in the folder names, so drop them from the file.
    quotes.drop(columns=["underlying"]).to_parquet(path, index=False, compression="zstd")
    return path


def write_company_facts(facts: pd.DataFrame, lake: Path = Path("lake")) -> Path:
    """Replace one company's statement facts (columns as in duckdb.md statement_facts)."""
    folder = lake / "statement_facts" / f"cik={facts['cik'].iloc[0]}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "facts.parquet"
    facts.drop(columns=["cik"]).to_parquet(path, index=False, compression="zstd")
    return path
```

Hive partition values come back as strings or inferred types. Keep `cik` as a string by setting `hive_types = {'cik': VARCHAR}` in `read_parquet` if leading zeros matter.
