# FINRA Reg SHO daily short sale volume

**Covers:** Daily short sale volume, short-exempt volume and total volume for every US exchange-listed and OTC equity, for trades reported to FINRA trade reporting facilities (off-exchange trading: dark pools and internalizers). Daily files go back to August 2009. FINRA also publishes twice-monthly short interest data separately.

**Provider:** Financial Industry Regulatory Authority (FINRA) | **Docs:** https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data

## Access

- **Method:** bulk download, one pipe-delimited text file per day at `https://cdn.finra.org/equity/regsho/daily/CNMSshvol<YYYYMMDD>.txt` (consolidated across all FINRA facilities). The FINRA Query API (`https://api.finra.org`) serves the same data and short interest.
- **Auth:** none for the daily files. The Query API needs a free FINRA API client ID and secret for most datasets. Env var name: `FINRA_API_KEY` (only for the Query API).
- **Rate limits:** unknown for the CDN files, none published. The CDN returns 403 to Python's default `urllib` user agent (which `pd.read_csv(url)` uses), so send a browser-style `User-Agent`. The Query API has per-dataset limits listed in its docs.
- **Formats:** pipe-delimited text for the daily files, JSON or CSV from the Query API

## Cost

- **Free tier:** daily files and the public Query API datasets
- **Paid tiers:** none for this data
- **License or terms:** FINRA website terms of use (https://www.finra.org/terms-of-use). Free to use with attribution to FINRA.

## Quality notes

- **Update frequency:** daily, published the evening of each trading day
- **Known gaps:** this is short sale volume, not short interest. Market makers sell short as part of normal liquidity provision, so a high short-volume ratio does not mean bearish positioning. Off-exchange trades only; on-exchange short volume is published by each exchange. No files on market holidays.
- **Point-in-time?** yes. Files are published once and not revised.

## Minimal example

```python
import datetime as dt
import io

import pandas as pd
import requests

day = dt.date.today() - dt.timedelta(days=1)  # files appear the evening of each trading day
while day.weekday() >= 5:  # step back over weekends; market holidays still need a manual step back
    day -= dt.timedelta(days=1)
url = f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{day:%Y%m%d}.txt"
# The CDN rejects pandas' default urllib user agent with a 403, so fetch with requests.
text = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
vol = pd.read_csv(io.StringIO(text), sep="|").dropna(subset=["Symbol"])
vol["short_ratio"] = vol["ShortVolume"] / vol["TotalVolume"]
print(vol[vol["Symbol"].isin(["SPY", "AAPL", "TSLA"])])
```

## Used by

- Alternative data and market structure workflows (planned). Inputs similar to the SqueezeMetrics DIX.
