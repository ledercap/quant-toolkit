# Databento

**Covers:** Exchange-direct tick data from the actual exchange feeds, as historical files and live streams. Includes CME Globex MDP 3.0 (futures and options on CME, CBOT, NYMEX and COMEX, 650,000+ symbols), OPRA (all US equity options), Nasdaq TotalView-ITCH and other US equity venues, and ICE Futures. Formats range from trades and top of book to full order book, plus OHLCV bars and statistics such as settlement prices and open interest. 16+ years of history for top-of-book data.

**Provider:** Databento Inc. | **Docs:** https://databento.com/docs

## Access

- **Method:** Python, C++ and Rust client libraries (`pip install databento`), plus REST for historical data and a TCP gateway for live data. Bulk batch downloads.
- **Auth:** API key. Env var name: `DATABENTO_API_KEY`
- **Rate limits:** generous for historical requests. Your budget is the real limit, so estimate with `metadata.get_cost` before downloading.
- **Formats:** DBN (Databento's own binary format), CSV and JSON. The Python client converts to pandas.

## Cost

- **Free tier:** $125 in historical data credits for new accounts, which expire 6 months after sign-up
- **Paid tiers:** pay-as-you-go historical data priced per GB of uncompressed data. Standard plan $199/mo (live data, 16+ years top-of-book history, 1 year order-book history). Plus $1,750/mo and Unlimited $4,500/mo on annual contracts.
- **License or terms:** set by each exchange dataset. Most can be redistributed after 24 hours; check each dataset's license (https://databento.com/terms).

## Quality notes

- **Update frequency:** real time for live data. Historical data is available the next day, with intraday replay.
- **Known gaps:** priced on uncompressed size, so full-depth order books get expensive quickly. Futures symbols need a symbology choice (raw contract `CLZ6`, continuous `CL.c.0`, or parent `CL.FUT`). Some venues have shorter history.
- **Point-in-time?** yes. Raw exchange messages carry exchange and receive timestamps, and contract definitions are recorded as they were on each date.

## Minimal example

```python
import os

import databento as db

client = db.Historical(os.environ["DATABENTO_API_KEY"])
params = dict(dataset="GLBX.MDP3", symbols=["CL.c.0"], stype_in="continuous",
              schema="ohlcv-1d", start="2026-09-01", end="2026-10-01")
print("estimated cost $", client.metadata.get_cost(**params))  # check before spending credits
bars = client.timeseries.get_range(**params).to_df()
print(bars[["open", "high", "low", "close", "volume"]].tail())
```

## Used by

- Futures and options workflows (planned)
