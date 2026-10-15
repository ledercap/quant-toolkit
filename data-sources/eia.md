# EIA Open Data (U.S. Energy Information Administration)

**Covers:** US and international energy data: crude oil and product spot prices (WTI, Brent, gasoline, heating oil, jet fuel), weekly petroleum inventories and refinery runs, production, imports and exports, natural gas storage and prices, electricity, coal and the Short-Term Energy Outlook (STEO) forecasts. Daily spot prices go back to 1986 for WTI and 1987 for Brent.

**Provider:** U.S. Energy Information Administration | **Docs:** https://www.eia.gov/opendata/documentation.php

## Access

- **Method:** REST, API v2 (`https://api.eia.gov/v2/`). Routes form a tree: request a parent such as `/v2/petroleum` to list its children, then add `/data` to a leaf to get values. Spot prices live at `petroleum/pri/spt`.
- **Auth:** free API key, passed as `api_key` in the URL. Register at https://www.eia.gov/opendata/register.php. Env var name: `EIA_API_KEY`. The key `DEMO_KEY` works for a few test calls.
- **Rate limits:** not published as a number. EIA throttles per second and per hour and suspends keys temporarily when you go over.
- **Formats:** JSON (the default, up to 5,000 rows per response) or XML (up to 300 rows). Page with `offset` and `length`.

## Cost

- **Free tier:** everything, with a free key
- **Paid tiers:** none
- **License or terms:** US government work, in the public domain. EIA asks you to cite it as the source.

## Quality notes

- **Update frequency:** spot prices are published weekly (on Wednesdays) with daily values. The Weekly Petroleum Status Report comes out on Wednesdays, natural gas storage on Thursdays, and monthly series about two months after the reference month.
- **Known gaps:** spot prices come from Refinitiv/LSEG and are published with a lag of about a week. Responses over the row cap come back cut short with only a warning, so always check the `total` field. Values are strings, so cast them to float. Monthly and annual series get revised.
- **Point-in-time?** no. Revisions overwrite earlier values.

## Minimal example

```python
import os

import requests

params = {
    "api_key": os.environ["EIA_API_KEY"],
    "frequency": "daily",
    "data[0]": "value",
    "facets[series][]": "RWTC",  # Cushing, OK WTI spot price, $/bbl
    "sort[0][column]": "period",
    "sort[0][direction]": "desc",
    "length": 5,
}
r = requests.get("https://api.eia.gov/v2/petroleum/pri/spt/data/", params=params, timeout=30)
for row in r.json()["response"]["data"]:
    print(row["period"], row["value"], row["units"])
```

## Used by

- `sectors/` commodities and oil coverage (planned)
