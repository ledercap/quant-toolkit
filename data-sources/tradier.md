# Tradier

**Covers:** US equities, ETFs, indexes and options from a US brokerage. Quotes, time and sales, daily and intraday bars, full options chains with Greeks and implied volatility (supplied by ORATS), expirations and strikes, market calendar and streaming. Daily price history goes back decades. Intraday history is limited to recent days.

**Provider:** Tradier Brokerage | **Docs:** https://docs.tradier.com

## Access

- **Method:** REST (`https://api.tradier.com/v1/`) plus HTTP and WebSocket streaming. Sandbox at `https://sandbox.tradier.com/v1/`. Options chains: `GET /markets/options/chains?symbol=SPY&expiration=YYYY-MM-DD&greeks=true`
- **Auth:** Bearer token in the `Authorization` header, plus `Accept: application/json` (the default response is XML). Env var name: `TRADIER_API_KEY`
- **Rate limits:** market data allows 120 requests per minute in production and 60 in the sandbox. Trading endpoints allow 60.
- **Formats:** JSON or XML

## Cost

- **Free tier:** a developer sandbox account with delayed market data for testing
- **Paid tiers:** real-time production data comes with an open Tradier brokerage account. Plan prices and account requirements are unknown and change, so check https://tradier.com/individuals/pricing.
- **License or terms:** for use under your own account. Exchange data is not for redistribution (Tradier API terms of use).

## Quality notes

- **Update frequency:** real-time in production, delayed in the sandbox. Greeks and IV carry an `updated_at` timestamp and can lag the quote. The refresh rate isn't documented, so compare `updated_at` with the quote time before using them.
- **Known gaps:** no historical options chains (snapshots only). One expiration per chain request, so list expirations first with `/markets/options/expirations`. Responses with a single item come back as an object, not a list.
- **Point-in-time?** no. Current snapshots only.

## Minimal example

```python
import os

import requests

headers = {"Authorization": f"Bearer {os.environ['TRADIER_API_KEY']}", "Accept": "application/json"}
base = "https://sandbox.tradier.com/v1"  # switch to https://api.tradier.com/v1 for production

expirations = requests.get(f"{base}/markets/options/expirations", params={"symbol": "SPY"},
                           headers=headers, timeout=30).json()["expirations"]["date"]
chain = requests.get(f"{base}/markets/options/chains",
                     params={"symbol": "SPY", "expiration": expirations[0], "greeks": "true"},
                     headers=headers, timeout=30).json()["options"]["option"]
for c in chain[:5]:
    print(c["symbol"], c["bid"], c["ask"], (c.get("greeks") or {}).get("mid_iv"))
```

## Used by

- `workflows/options/greeks` (planned)
- `workflows/options/volatility` (planned)
