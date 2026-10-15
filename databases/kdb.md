# kdb+ / KDB-X and q

**Best for:** tick data at the scale of banks and trading firms: every trade and quote across exchanges, real-time capture with a historical database, and time-series joins (as-of joins of trades to quotes) over billions of rows. It is the long-standing industry standard for market data in front-office quant and trading.

**Pairs with:** q, its own built-in vector language. Python through PyKX (`pip install pykx`, which converts q tables to pandas, Polars and Arrow and back), plus C/C++, Java and C# client APIs, and an R interface (`rkdb`). Tables, queries and schemas are all written in q.

**Cost and hosting:** commercial software from KX, installed on your own machines. KDB-X Community Edition is free for personal and commercial use within limits (KX lists a 16 GB RAM cap, one instance, and at most 4 secondary threads per q process). A kdb+ Personal trial is free for 12 months, non-commercial only. Full commercial licenses are priced on request and are expensive. Terms change, so check https://kx.com before relying on them.

## When to choose it

kdb+ is the fastest option here for time-series work and the most expensive one at scale. Its in-memory and on-disk columnar tables, date partitioning and as-of joins are built for exactly the problems in market microstructure. The costs are the license and q itself: a terse, powerful language with a small hiring pool. Learn it if you're aiming at a front-office quant or trading role, where q is still a sought-after skill. For an open-source alternative at similar scale, use [ClickHouse](clickhouse.md); for research, [DuckDB](duckdb.md).

## Schema

```q
/ Reference schema shared by the workflows, as empty typed q tables.
/ Column names avoid q reserved words: `value` -> val, `last` -> lastpx.
/ `sym` is the q convention for the instrument column.

prices_daily:([] date:`date$(); sym:`symbol$(); open:`float$(); high:`float$(); low:`float$();
  close:`float$(); adj_close:`float$(); volume:`long$(); source:`symbol$())

/ SEC EDGAR XBRL facts as reported; `filed` is the point-in-time key.
statement_facts:([] cik:`symbol$(); taxonomy:`symbol$(); tag:`symbol$(); unit:`symbol$();
  period_start:`date$(); period_end:`date$(); val:`float$(); fiscal_year:`int$();
  fiscal_period:`symbol$(); form:`symbol$(); filed:`date$(); accn:`symbol$())

option_quotes:([] snapshot_ts:`timestamp$(); sym:`symbol$(); expiry:`date$(); option_type:`char$();
  strike:`float$(); bid:`float$(); ask:`float$(); lastpx:`float$(); volume:`long$();
  open_interest:`long$(); iv:`float$(); delta:`float$(); gamma:`float$(); vega:`float$();
  theta:`float$(); underlying_price:`float$(); source:`symbol$())

yield_curve:([] date:`date$(); tenor_months:`float$(); yield_pct:`float$(); source:`symbol$())

/ On disk, save option_quotes as a date-partitioned table (one folder per day) with
/ .Q.dpft[`:hdb; date; `sym; `option_quotes], which also applies the `p# attribute to sym.
```

## Queries the workflows rely on

```q
/ name: annualFactAsOf
/ One value per fiscal year for a tag, using only filings public on asof.
/ `select by` keeps the last row per group, so sort by filed first: latest filing wins.
annualFactAsOf:{[c;t;asof]
  f:select from statement_facts where cik=c, tag=t, unit=`USD, filed<=asof,
    (period_end-period_start) within 350 380;
  `period_end xasc select by period_end from `filed xasc f}

/ name: annualGrowth
annualGrowth:{[c;t;asof] update yoy_growth:(val%prev val)-1 from annualFactAsOf[c;t;asof]}

/ name: dailyReturns
dailyReturns:{[s;src]
  update ret:(adj_close%prev adj_close)-1 from `date xasc select from prices_daily where sym=s, source=src}

/ name: riskFreeRate
/ Yield (decimal) at the tenor nearest dte days, latest curve on or before asof.
riskFreeRate:{[asof;dte]
  d:exec max date from yield_curve where date<=asof;
  c:update dist:abs tenor_months-dte%30.4375 from select from yield_curve where date=d;
  0.01*first exec yield_pct from `dist xasc c}

/ name: gexByStrike
/ Source: SqueezeMetrics, "Gamma Exposure (GEX)" white paper: https://squeezemetrics.com/download/white_paper.pdf
/ Dollar gamma per 1% move by strike, latest snapshot; dealers long calls (+), short puts (-).
gexByStrike:{[u]
  t:select from option_quotes where sym=u;
  t:select from t where snapshot_ts=max snapshot_ts;
  `strike xasc select gex_usd:sum (?[option_type="C";1f;-1f])*gamma*open_interest*100*underlying_price*underlying_price*0.01
    by strike from t}

/ name: putCallByExpiry
putCallByExpiry:{[u]
  t:select from option_quotes where sym=u;
  t:select from t where snapshot_ts=max snapshot_ts;
  `expiry xasc select pc_volume:(sum volume where option_type="P")%sum volume where option_type="C",
    pc_open_interest:(sum open_interest where option_type="P")%sum open_interest where option_type="C"
    by expiry from t}

/ Example: gexByStrike[`SPY]   annualGrowth[`0000320193;`RevenueFromContractWithCustomerExcludingAssessedTax;2026.10.15]
```

## Loading from data sources

Fetch and shape a DataFrame as in [duckdb.md](duckdb.md#loading-from-data-sources), rename columns to the q names above, then hand it to q with PyKX. Match the q column types first (symbols as strings, dates as `datetime64`, `option_type` as single characters), because `upsert` rejects mismatched types.

```python
import pykx as kx

kx.q(open("schema.q").read())  # the Schema block above, saved as schema.q

# `quotes` has the option_quotes columns from duckdb.md.
q_quotes = quotes.rename(columns={"underlying": "sym", "last": "lastpx"})[
    ["snapshot_ts", "sym", "expiry", "option_type", "strike", "bid", "ask", "lastpx", "volume",
     "open_interest", "iv", "delta", "gamma", "vega", "theta", "underlying_price", "source"]
]
kx.q("{`option_quotes upsert x}", kx.toq(q_quotes))
print(kx.q("gexByStrike[`SPY]").pd().tail())
```
