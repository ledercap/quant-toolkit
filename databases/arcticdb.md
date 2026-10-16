# ArcticDB

**Best for:** versioned pandas time series: daily and intraday bars, options chain snapshots, factor and signal DataFrames. It suits research teams that need to see exactly what a series looked like at an earlier version (time travel), and DataFrames with thousands of columns.

**Pairs with:** Python only (`pip install arcticdb`). Reads and writes pandas DataFrames directly. No SQL interface.

**Cost and hosting:** runs in-process on top of storage you provide: local disk (LMDB), Amazon S3 or S3-compatible stores, or Azure Blob, so there's no server. License is the Business Source License 1.1: free for non-commercial, personal or academic use; business use (including research and development environments) needs a commercial license from ArcticDB Ltd (info@arcticdb.io). Each release converts to Apache 2.0 two years after it ships, and from then on that version is free for any use. Terms: https://docs.arcticdb.io/latest/licensing/

## When to choose it

ArcticDB came out of Man Group to store DataFrames at hedge-fund scale. Its edge is versioning: every write creates a version, and `read(symbol, as_of=...)` returns the data as it was, which guards against look-ahead bias when you re-fetch and overwrite history. It is fast for "give me this symbol's DataFrame" access. Ad-hoc questions across many symbols are harder than in SQL (DuckDB, PostgreSQL), and it only works from Python. Check the license before using it for work at a company.

## Schema

ArcticDB stores one DataFrame per *symbol* inside a *library*. The schema is the DataFrame's columns and index. A DatetimeIndex is what enables `date_range` reads and appends.

```python
# Libraries and symbols (one library per dataset):
#   prices_daily     symbol = ticker            index = date             columns: open, high, low, close, adj_close, volume
#   option_quotes    symbol = underlying        index = snapshot_ts      columns: expiry, option_type, strike, bid, ask, last,
#                                                                                  volume, open_interest, iv, delta, gamma,
#                                                                                  vega, theta, underlying_price
#   statement_facts  symbol = CIK (10 digits)   index = filed            columns: taxonomy, tag, unit, period_start,
#                                                                                  period_end, value, fiscal_year,
#                                                                                  fiscal_period, form, accn
#   yield_curve      symbol = 'us-treasury'     index = date             columns: one per tenor in months ('1', '1.5', ... '360')
#
# Indexes must be sorted ascending; option_quotes repeats the same snapshot_ts for every
# contract in a snapshot, which ArcticDB allows. Keep column dtypes stable between writes,
# and use NumPy dtypes (float64, int64, object): pandas nullable types such as Int32 fail to write.
# Open one Arctic instance per LMDB path per process.

import arcticdb as adb

ac = adb.Arctic("lmdb://./arctic")  # local; for S3: "s3://s3.<region>.amazonaws.com:<bucket>?aws_auth=true"
for name in ["prices_daily", "option_quotes", "statement_facts", "yield_curve"]:
    ac.get_library(name, create_if_missing=True)
```

## Queries the workflows rely on

```python
import arcticdb as adb
import pandas as pd

ac = adb.Arctic("lmdb://./arctic")


def annual_fact_as_of(cik: str, tag: str, as_of: str) -> pd.DataFrame:
    """One value per fiscal year for a tag, using only filings public on as_of."""
    q = adb.QueryBuilder()
    q = q[(q["tag"] == tag) & (q["unit"] == "USD")]
    facts = ac["statement_facts"].read(cik, date_range=(None, pd.Timestamp(as_of)), query_builder=q).data
    days = (pd.to_datetime(facts["period_end"]) - pd.to_datetime(facts["period_start"])).dt.days
    annual = facts[days.between(350, 380)].reset_index().sort_values("filed")
    return annual.groupby("period_end").last().reset_index()  # latest filing wins


def gex_by_strike(underlying: str) -> pd.Series:
    """Dollar gamma per 1% move by strike for the latest snapshot (dealers long calls, short puts).

    Source: SqueezeMetrics, "Gamma Exposure (GEX)" white paper: https://squeezemetrics.com/download/white_paper.pdf
    """
    chain = ac["option_quotes"].read(underlying).data
    latest = chain.loc[chain.index == chain.index.max()]
    sign = latest["option_type"].map({"C": 1, "P": -1})
    gex = sign * latest["gamma"] * latest["open_interest"] * 100 * latest["underlying_price"] ** 2 * 0.01
    return gex.groupby(latest["strike"]).sum()


def chain_as_it_was(underlying: str, version: int) -> pd.DataFrame:
    """Time travel: the option_quotes symbol exactly as it was at an earlier version."""
    return ac["option_quotes"].read(underlying, as_of=version).data
```

## Loading from data sources

Fetch and shape a DataFrame as in [duckdb.md](duckdb.md#loading-from-data-sources), set the time column as the index, then `write` (replace, new version) or `append` (add newer rows):

```python
import arcticdb as adb

ac = adb.Arctic("lmdb://./arctic")

# Options snapshots grow over time: append each new snapshot.
# `quotes` has the option_quotes columns from duckdb.md.
lib = ac["option_quotes"]
snap = quotes.drop(columns=["underlying", "source"]).set_index("snapshot_ts").sort_index()
if lib.has_symbol("SPY"):
    # Rows must not be older than the last stored snapshot. Appending the same snapshot
    # twice is NOT rejected and duplicates rows, so check the last stored timestamp first.
    if snap.index.min() > lib.tail("SPY", n=1).data.index.max():
        lib.append("SPY", snap)
else:
    lib.write("SPY", snap)

# Statement facts are re-fetched whole: write a new version (old versions stay readable).
# `edgar` has the statement_facts columns from duckdb.md.
# ArcticDB rejects pandas nullable extension dtypes (Int32, boolean, string), so cast them first.
facts = (edgar.assign(filed=pd.to_datetime(edgar["filed"]), fiscal_year=edgar["fiscal_year"].astype("float64"))
              .drop(columns=["cik"]).set_index("filed").sort_index())
ac["statement_facts"].write("0000320193", facts, prune_previous_versions=False)
```
