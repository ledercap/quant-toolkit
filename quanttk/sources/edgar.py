"""SEC EDGAR XBRL company facts. See data-sources/sec-edgar.md."""

from __future__ import annotations

import os
import sys
from typing import Iterable

import pandas as pd

from quanttk.sources.http import get_json

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
FACT_COLUMNS = ["tag", "unit", "start", "end", "value", "form", "filed"]


def sec_headers() -> dict[str, str]:
    """SEC requires a descriptive User-Agent (name and email) on every request."""
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        sys.exit("Set SEC_USER_AGENT, e.g. export SEC_USER_AGENT='Jane Doe jane@example.com'")
    return {"User-Agent": ua}


def ticker_to_cik(ticker: str) -> str:
    """Map a ticker to its 10-digit, zero-padded CIK using the SEC's ticker file.

    Accepts class-share tickers written with a dash or a dot (BRK-B, BRK.B).
    """
    rows = get_json(TICKERS_URL, headers=sec_headers(), timeout=30)
    wanted = {ticker.upper(), ticker.upper().replace(".", "-"), ticker.upper().replace("-", ".")}
    for row in rows.values():
        if row["ticker"].upper() in wanted:
            return f"{row['cik_str']:010d}"
    sys.exit(f"Ticker {ticker} not found in SEC company_tickers.json")


def fetch_facts(cik: str, tags: Iterable[str], taxonomy: str = "us-gaap") -> pd.DataFrame:
    """Every reported fact for the given tags, in every unit, one row per fact.

    Columns: tag, unit, start (NaN for instant facts), end, value, form, filed.
    """
    raw = get_json(COMPANYFACTS_URL.format(cik=cik), headers=sec_headers(), timeout=60)
    gaap = raw["facts"].get(taxonomy, {})
    rows = [
        {"tag": tag, "unit": unit, "start": f.get("start"), "end": f["end"], "value": f["val"],
         "form": f.get("form"), "filed": f["filed"]}
        for tag in set(tags) if tag in gaap
        for unit, items in gaap[tag]["units"].items()
        for f in items
    ]
    return pd.DataFrame(rows, columns=FACT_COLUMNS)
