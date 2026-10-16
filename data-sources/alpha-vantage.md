# Alpha Vantage

**Covers:** Global stocks, ETFs and mutual funds (daily, weekly, monthly and intraday), forex, crypto, commodities (WTI, Brent, natural gas, metals, agriculture), US economic indicators, 50+ technical indicators, company fundamentals (income statement, balance sheet, cash flow, earnings), news sentiment and US options (historical and real time on premium). Daily stock history goes back 20+ years.

**Provider:** Alpha Vantage Inc. | **Docs:** https://www.alphavantage.co/documentation/

## Access

- **Method:** REST, a single endpoint `https://www.alphavantage.co/query?function=<FUNCTION>&...` plus an official MCP server
- **Auth:** free API key as the `apikey` query parameter. The key `demo` works only on the example URLs in the docs. Env var name: `ALPHA_VANTAGE_API_KEY`
- **Rate limits:** 25 requests per day on the free tier. Premium plans range from 75 to 1,200 requests per minute with no daily cap.
- **Formats:** JSON (the default) or CSV (`datatype=csv`)

## Cost

- **Free tier:** 25 requests per day across most endpoints
- **Paid tiers:** $49.99/mo (75 per minute), $99.99/mo (150), $149.99/mo (300), $199.99/mo (600), $249.99/mo (1,200). Annual billing gets 2 months free. Real-time and 15-minute delayed US data and real-time options need an extra exchange-data entitlement.
- **License or terms:** https://www.alphavantage.co/terms_of_service/. Personal and internal use; no redistribution of the raw data.

## Quality notes

- **Update frequency:** end-of-day for free daily data. Intraday and real-time depend on plan and entitlement. Fundamentals refresh after each earnings filing.
- **Known gaps:** the 25-per-day limit makes the free tier useful only for testing. When you hit the limit the API returns HTTP 200 with a `"Note"` or `"Information"` message instead of data, so check for those keys. Full-history adjusted daily bars (`TIME_SERIES_DAILY_ADJUSTED`) are premium. Fundamentals cover only the last few years.
- **Point-in-time?** no

## Minimal example

```python
import os

import requests

params = {"function": "GLOBAL_QUOTE", "symbol": "IBM", "apikey": os.environ["ALPHA_VANTAGE_API_KEY"]}
data = requests.get("https://www.alphavantage.co/query", params=params, timeout=30).json()
if "Global Quote" not in data:
    raise RuntimeError(data)  # rate-limit messages arrive with HTTP 200
print(data["Global Quote"])
```

## Used by

- `workflows/financial-analysis/` (planned: cross-check against SEC EDGAR)
