# Options volume and open interest: put/call ratios, unusual activity, concentration and OI change

**Computes:** from a Cboe options chain:
- **Put/call ratios:** total call and put volume and open interest (OI), and both put/call ratios, overall and by expiry.
- **OI concentration:** the strikes holding the most open interest across expiries.
- **Unusual activity:** contracts where today's volume is large and exceeds the prior open interest.
- **OI change (with `--save-snapshot`):** the change in open interest per contract since an earlier saved snapshot. Each run can be archived to a local Parquet lake, so history builds up day by day.

**Inputs:** option `volume`, `open_interest`, `last_trade_price`, spot and snapshot time from [`data-sources/cboe-delayed-quotes.md`](../../../data-sources/cboe-delayed-quotes.md). Earlier days come from the snapshot lake (layout as in [`databases/parquet.md`](../../../databases/parquet.md)).

**Output:** printed tables, plus `output/put_call_by_expiry_<SYMBOL>.csv`, `output/oi_concentration_<SYMBOL>.csv`, `output/unusual_activity_<SYMBOL>.csv` and, once history exists, `output/oi_change_<SYMBOL>.csv`.

## Formula

For a set of contracts (all live contracts, or one expiry):

| Measure | Formula |
| --- | --- |
| Put/call volume ratio | Σ put volume / Σ call volume |
| Put/call OI ratio | Σ put open interest / Σ call open interest |
| OI share of a strike | OI(K) / Σ OI, with OI(K) summed across expiries and both sides |
| Volume / OI | Today's volume / open interest, ∞ for a contract with no prior open interest |
| Unusual activity | volume ≥ `--min-volume` (default 1,000) and volume / OI ≥ `--min-ratio` (default 1.0) |
| OI change | OI<sub>today</sub> − OI<sub>earlier snapshot</sub>, matched on the option symbol; contracts new since then start from 0 |

Sources:
- **Put/call ratio definitions:** as published in Cboe's market statistics (https://www.cboe.com/us/options/market_statistics/).
- **Volume relative to open interest as a new-positioning screen:** McMillan, L. G., *Options as a Strategic Investment*, 5th ed. (2012), chapter on volume and open interest as indicators.

A ratio whose denominator is zero (no call volume in an expiry, say) is left blank rather than shown as infinity. Only unexpired contracts are counted.

## Caveats

- **Open interest is as of the previous close.** OCC publishes it once a day, before the open, so volume / OI compares today's trading with yesterday's positions. Same-day (0DTE) contracts often show volume many times their OI for that reason.
- **Volume doesn't say who traded.** The feed has no buyer/seller flag, so a large put print may be a hedge being bought or premium being sold. The unusual-activity screen finds where positioning changed, not its direction.
- **Snapshot dates use the US market date** (America/New_York). An after-the-close run at 8 pm ET is filed under that trading day, and OI change compares with the latest snapshot from an earlier market date. Run once a day after the close (for example with cron or launchd) to build a clean daily series.
- **Lake location:** `$QUANTTK_LAKE`, or `lake/` at the repo root. Parquet files are gitignored, so nothing you collect is committed. The archive needs `pyarrow`.
- **Index vs ETF:** SPX volume is mostly institutional and spread over many expiries. SPY is heavier in short-dated retail flow. Compare like with like.
- **Delay:** the data is 15 minutes delayed. Volume during the session is partial; the after-close snapshot has the full day.

## Run it

```bash
pip install -r requirements.txt
python main.py                              # SPX
python main.py --symbol SPY --save-snapshot # also archive today's chain
python main.py --symbol AAPL --min-volume 500
python main.py --sample                     # offline: 90 SPX contracts from the 2026-12-18 monthly expiry
```

## Files

- `main.py`: entry point. Calculations come from `quanttk.options.volume`; the archive is `quanttk.sources.snapshots`.
- `requirements.txt`: pinned dependencies (pyarrow only for `--save-snapshot`)
- `sample/chain.csv`: 90 SPX contracts (the 45 strikes nearest spot, 2026-12-18 expiry) with volume, open interest, spot and snapshot time
