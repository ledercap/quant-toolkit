# SEC EDGAR

**Covers:** US public company filings (10-K, 10-Q, 8-K, S-1, 13F, Forms 3/4/5 and every other EDGAR form) and the XBRL financial statement facts tagged inside them. All SEC registrants, including foreign filers that file in the US. Full-text filings go back to 1993 (2001 for complete electronic coverage). XBRL facts go back to roughly 2009 for large filers and 2011 for everyone else.

**Provider:** U.S. Securities and Exchange Commission | **Docs:** https://www.sec.gov/search-filings/edgar-application-programming-interfaces

## Access

- **Method:** REST (`https://data.sec.gov`), plus nightly bulk ZIPs (`companyfacts.zip`, `submissions.zip`) for large pulls
- **Endpoints:** `/submissions/CIK##########.json` (filing history), `/api/xbrl/companyfacts/CIK##########.json` (every XBRL fact for one company), `/api/xbrl/companyconcept/CIK##########/us-gaap/<Tag>.json` (one tag for one company), `/api/xbrl/frames/us-gaap/<Tag>/USD/CY2024Q4I.json` (one tag across every company for a period)
- **Auth:** none. Every request must send a descriptive `User-Agent` with a name and email, or it gets a 403. Env var name: `SEC_USER_AGENT`, for example `Jane Doe jane@example.com`.
- **Rate limits:** 10 requests per second per user, across all of your machines. Excessive traffic gets the IP blocked.
- **Formats:** JSON for the APIs. Filings themselves are HTML, XML, XBRL and plain text.

## Cost

- **Free tier:** everything. There is no paid tier.
- **Paid tiers:** none
- **License or terms:** US government work, in the public domain. You must follow the SEC fair-access policy (https://www.sec.gov/about/developer-resources). No CORS, so call it from a server or script, not a browser.

## Quality notes

- **Update frequency:** real-time. Submissions are typically under one second behind a filing, and XBRL APIs under one minute. Bulk ZIPs are rebuilt nightly around 3:00 a.m. ET.
- **Known gaps:** CIKs must be zero-padded to 10 digits (map tickers with `https://www.sec.gov/files/company_tickers.json`). Companies change XBRL tags over time: Apple reports revenue as `Revenues` up to FY2018 and as `RevenueFromContractWithCustomerExcludingAssessedTax` after that, so one tag rarely gives a full history. Custom company-specific tags (outside `us-gaap`) are common. The same period appears in several filings, so de-duplicate on `end` and `filed`. No market prices.
- **Point-in-time?** yes. Every fact carries its `filed` date and accession number (`accn`), so you can rebuild what was known on any date. Restatements show up as new facts with later `filed` dates.

## Minimal example

```python
import os

import requests

HEADERS = {"User-Agent": os.environ["SEC_USER_AGENT"]}
cik = "0000320193"  # Apple, zero-padded to 10 digits
tag = "RevenueFromContractWithCustomerExcludingAssessedTax"

url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
facts = requests.get(url, headers=HEADERS, timeout=30).json()["units"]["USD"]

# Full-year values from 10-Ks; the `frame` field marks the one canonical value per period.
annual = [f for f in facts if f.get("form") == "10-K" and f.get("frame", "").startswith("CY") and "Q" not in f["frame"]]
for f in annual[-3:]:
    print(f["end"], f["val"], "filed", f["filed"])
```

## Used by

- `workflows/financial-analysis/income-statement` (planned)
- `workflows/financial-analysis/balance-sheet` (planned)
- `workflows/financial-analysis/cash-flow` (planned)
