# Financial Modeling Prep (FMP)

**Covers:** Standardized company fundamentals for global stocks: income statements, balance sheets, cash flow statements, ratios and key metrics, DCF valuations, analyst estimates, earnings calendars, earnings call transcripts, insider and institutional (13F) holdings, ETF holdings, daily and intraday prices, plus forex, crypto and commodities. History goes back 30+ years on higher plans.

**Provider:** Financial Modeling Prep | **Docs:** https://site.financialmodelingprep.com/developer/docs

## Access

- **Method:** REST (`https://financialmodelingprep.com/stable/`). The older `/api/v3/` routes are deprecated.
- **Auth:** API key as the `apikey` query parameter. Env var name: `FMP_API_KEY`
- **Rate limits:** 250 calls per day on the free plan. Paid plans run from 300 to 3,000 calls per minute, with monthly bandwidth caps (500 MB free, 20 GB Starter, 50 GB Premium).
- **Formats:** JSON, plus CSV on some endpoints

## Cost

- **Free tier:** Basic, with 250 calls per day, end-of-day data and limited history and symbol coverage. No credit card needed.
- **Paid tiers:** prices when billed annually:
  - Starter $22/mo: US, 5 years, annual fundamentals
  - Premium $59/mo: 30+ years, quarterly fundamentals, intraday, UK and Canada
  - Ultimate $149/mo: global coverage, transcripts, 3,000 calls per minute
  - Business plans are priced separately.
- **License or terms:** individual plans are for personal use. Displaying or redistributing data needs a commercial license (https://site.financialmodelingprep.com/terms-of-service).

## Quality notes

- **Update frequency:** fundamentals within hours to days of a filing. Prices end-of-day or intraday depending on plan.
- **Known gaps:** line items are standardized by FMP and can differ from the company's own presentation, so check important numbers against SEC EDGAR. Free-tier symbol coverage is limited, so test your tickers first. Going over a limit returns HTTP 429.
- **Point-in-time?** no. Statements show the latest restated values. `filingDate` and `acceptedDate` fields help you approximate it.

## Minimal example

```python
import os

import requests

params = {"symbol": "AAPL", "limit": 3, "apikey": os.environ["FMP_API_KEY"]}
r = requests.get("https://financialmodelingprep.com/stable/income-statement", params=params, timeout=30)
for row in r.json():
    print(row["date"], row["revenue"], row["netIncome"], row["filingDate"])
```

## Used by

- `workflows/financial-analysis/` (planned: standardized statements, cross-checked against SEC EDGAR)
