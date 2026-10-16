# Massive (formerly Polygon.io)

**Covers:** US stocks, options, indexes, forex and crypto, plus futures in newer plans. Trades, quotes, minute, second and daily aggregates, snapshots, options chains with Greeks and IV, reference data, corporate actions and financial statements. Up to 20+ years of stock history depending on plan. Polygon.io rebranded to Massive in 2025; the old `api.polygon.io` host still answers.

**Provider:** Massive | **Docs:** https://massive.com/docs

## Access

- **Method:** REST (`https://api.massive.com`), WebSocket streaming, and S3-compatible flat files (daily bulk CSVs on paid plans)
- **Auth:** API key, either as `apiKey` in the query string or `Authorization: Bearer <key>`. Env var name: `MASSIVE_API_KEY`
- **Rate limits:** 5 calls per minute on free plans. Paid plans have unlimited calls, with fair-use throttling.
- **Formats:** JSON for the REST API, CSV for flat files

## Cost

- **Free tier:** Basic stocks plan and Basic options plan, each free: 5 calls per minute, 2 years of history, end-of-day data only. No options Greeks.
- **Paid tiers:** priced separately for each asset class (individual use).
  - **Stocks:** Starter $29/mo (15-minute delayed, 5 years), Developer $79/mo (adds trades, 10 years), Advanced $199/mo (real time, quotes, financials, 20+ years).
  - **Options:** Starter $29/mo (15-minute delayed, Greeks and IV, 2 years), Developer $79/mo (4 years), Advanced $199/mo (real time, 5+ years).
  - Annual billing is 20% off. Business plans are priced separately.
- **License or terms:** individual plans are for non-professional, non-commercial use. No redistribution (https://massive.com/terms).

## Quality notes

- **Update frequency:** real time or 15-minute delayed depending on plan. End-of-day on free plans.
- **Known gaps:** stock and options subscriptions are separate, so a stocks plan gives no options data. Free plans have no snapshots and no Greeks. Aggregates are adjusted for splits by default (`adjusted=true`); set it to `false` for as-traded prices. Large requests page through `next_url`.
- **Point-in-time?** partly. Trades and quotes are as recorded. Reference data and aggregates reflect later corporate actions unless you request unadjusted values.

## Minimal example

```python
import os

import requests

key = os.environ["MASSIVE_API_KEY"]
url = "https://api.massive.com/v2/aggs/ticker/AAPL/range/1/day/2026-09-01/2026-09-30"
r = requests.get(url, params={"adjusted": "true", "apiKey": key}, timeout=30)
for bar in r.json().get("results", [])[:5]:
    print(bar["t"], bar["o"], bar["h"], bar["l"], bar["c"], bar["v"])  # t is epoch milliseconds
```

## Used by

- Price and options workflows (planned)
