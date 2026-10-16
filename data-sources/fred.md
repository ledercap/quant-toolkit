# FRED (Federal Reserve Economic Data)

**Covers:** More than 800,000 US and international macroeconomic time series from about 100 sources: interest rates and Treasury yields, inflation (CPI, PCE), employment, GDP, money supply, credit spreads, FX rates, commodity prices and regional data. History runs back to the 1700s for some series and decades for most. ALFRED keeps every past vintage of revised series.

**Provider:** Federal Reserve Bank of St. Louis | **Docs:** https://fred.stlouisfed.org/docs/api/fred/

## Access

- **Method:** REST (`https://api.stlouisfed.org/fred/`). Version 1 serves series, categories, releases, sources and tags. Version 2 (`fred/v2/release/observations`) pulls every series on a release in bulk.
- **Auth:** free API key (32 characters), passed as the `api_key` query parameter. Register at https://fred.stlouisfed.org/docs/api/api_key.html. Env var name: `FRED_API_KEY`
- **Rate limits:** 120 requests per minute. Going over returns HTTP 429 and can lead to a temporary block.
- **Formats:** JSON (`file_type=json`) or XML (the default)

## Cost

- **Free tier:** everything, with a free key
- **Paid tiers:** none
- **License or terms:** FRED API Terms of Use (https://fred.stlouisfed.org/legal/#api). Many series belong to third parties (for example ICE BofA, S&P, Moody's) that restrict redistribution; check each series' notes and copyright line before republishing values.

## Quality notes

- **Update frequency:** follows each source's release schedule: daily for rates and FX, weekly, monthly or quarterly for most macro data
- **Known gaps:** missing observations come back as the string `"."`, not null. Some third-party series show only recent history because of licensing. Values are revised after release (GDP, payrolls), and plain FRED shows only the latest value.
- **Point-in-time?** yes, through ALFRED. Pass `realtime_start` and `realtime_end` to `fred/series/observations`, or list revision dates with `fred/series/vintagedates`.

## Minimal example

```python
import os

import requests

params = {
    "series_id": "DGS10",  # 10-year Treasury constant-maturity yield, percent
    "api_key": os.environ["FRED_API_KEY"],
    "file_type": "json",
    "sort_order": "desc",
    "limit": 5,
}
r = requests.get("https://api.stlouisfed.org/fred/series/observations", params=params, timeout=30)
for obs in r.json()["observations"]:
    print(obs["date"], obs["value"])
```

## Used by

- `workflows/options/greeks` (planned: risk-free rate input)
