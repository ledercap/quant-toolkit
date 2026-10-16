# CoinGecko

**Covers:** Crypto asset prices, market cap, volume, OHLC, exchange and DEX data, categories and metadata for more than 15,000 coins across 1,000+ exchanges. History goes back to each coin's listing, but the free plan only gives the last 365 days.

**Provider:** CoinGecko | **Docs:** https://docs.coingecko.com

## Access

- **Method:** REST. Free and demo keys use `https://api.coingecko.com/api/v3/`, paid keys use `https://pro-api.coingecko.com/api/v3/`.
- **Auth:** free Demo key in the `x-cg-demo-api-key` header (paid plans use `x-cg-pro-api-key`). Some endpoints answer without a key but at lower and less stable limits. Env var name: `COINGECKO_API_KEY`
- **Rate limits:** Demo plan allows 100 calls per minute and 10,000 calls per month
- **Formats:** JSON

## Cost

- **Free tier:** Demo plan with the limits above and 1 year of daily and hourly history
- **Paid tiers:** Basic $35/mo, Analyst $129/mo, Lite $499/mo, Pro $999/mo (about 20% less billed yearly), Enterprise on request. Paid plans add full history, higher limits and more endpoints.
- **License or terms:** free use requires showing "Data provided by CoinGecko" with a link (https://www.coingecko.com/en/api_terms)

## Quality notes

- **Update frequency:** prices are cached and refresh every 1 to 5 minutes depending on plan and endpoint
- **Known gaps:** prices are volume-weighted aggregates across exchanges, not a single venue's trades. Coin IDs are slugs (`bitcoin`), not tickers, so look them up with `/coins/list`. Data granularity is chosen automatically by date range. Delisted coins drop out, which creates survivorship bias.
- **Point-in-time?** no

## Minimal example

```python
import os

import requests

headers = {"x-cg-demo-api-key": os.environ["COINGECKO_API_KEY"]}
params = {"ids": "bitcoin,ethereum", "vs_currencies": "usd", "include_24hr_vol": "true"}
r = requests.get("https://api.coingecko.com/api/v3/simple/price", headers=headers, params=params, timeout=30)
print(r.json())
```

## Used by

- Crypto workflows (planned)
