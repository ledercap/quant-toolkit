"""Income statement analysis from SEC EDGAR: margins, growth and operating leverage.

Point-in-time: only facts from filings public on or before --as-of are used, and the
latest such filing wins for each fiscal year (so restatements replace earlier values).

Usage:
    python main.py --ticker AAPL
    python main.py --ticker MSFT --as-of 2024-12-31 --years 8
    python main.py --sample            # offline, from sample/aapl_facts.csv
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).parent

# Each line item maps to XBRL us-gaap tags in priority order. Companies switch tags
# over time (Apple used `Revenues` until FY2018), so the first tag with a value wins.
CONCEPTS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "cost_of_revenue": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold"],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
}
ANNUAL_FORMS = {"10-K", "10-K/A"}
MIN_GROWTH_FOR_DOL = 0.01


def sec_headers() -> dict[str, str]:
    """SEC requires a descriptive User-Agent (name and email) on every request."""
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        sys.exit("Set SEC_USER_AGENT, e.g. export SEC_USER_AGENT='Jane Doe jane@example.com'")
    return {"User-Agent": ua}


def ticker_to_cik(ticker: str) -> str:
    """Map a ticker to its 10-digit, zero-padded CIK using the SEC's ticker file."""
    rows = requests.get("https://www.sec.gov/files/company_tickers.json", headers=sec_headers(), timeout=30).json()
    for row in rows.values():
        if row["ticker"].upper() == ticker.upper():
            return f"{row['cik_str']:010d}"
    sys.exit(f"Ticker {ticker} not found in SEC company_tickers.json")


def fetch_facts(cik: str) -> pd.DataFrame:
    """All USD us-gaap facts for the tags in CONCEPTS, one row per reported fact."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    gaap = requests.get(url, headers=sec_headers(), timeout=60).json()["facts"].get("us-gaap", {})
    tags = {t for tag_list in CONCEPTS.values() for t in tag_list}
    rows = [
        {"tag": tag, "start": f.get("start"), "end": f["end"], "value": f["val"], "form": f.get("form"), "filed": f["filed"]}
        for tag in tags if tag in gaap
        for f in gaap[tag]["units"].get("USD", [])
    ]
    return pd.DataFrame(rows)


def annual_values(facts: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """One value per fiscal year end per tag: annual duration, 10-K forms, latest filing on or before as_of."""
    f = facts.copy()
    for col in ("start", "end", "filed"):
        f[col] = pd.to_datetime(f[col])
    days = (f["end"] - f["start"]).dt.days
    f = f[days.between(350, 380) & f["form"].isin(ANNUAL_FORMS) & (f["filed"] <= pd.Timestamp(as_of))]
    f = f.sort_values("filed").groupby(["tag", "end"], as_index=False).last()
    return f.pivot(index="end", columns="tag", values="value")


def build_statement(wide: pd.DataFrame) -> pd.DataFrame:
    """Collapse tag columns into line items using the priority order in CONCEPTS."""
    out = pd.DataFrame(index=wide.index)
    for item, tags in CONCEPTS.items():
        series = pd.Series(float("nan"), index=wide.index)
        for tag in tags:  # earlier tags win; later tags only fill years still missing
            if tag in wide:
                series = series.fillna(wide[tag])
        out[item] = series
    # Some filers report revenue and cost of revenue but not gross profit.
    out["gross_profit"] = out["gross_profit"].fillna(out["revenue"] - out["cost_of_revenue"])
    return out.dropna(subset=["revenue"]).sort_index()


def add_metrics(s: pd.DataFrame) -> pd.DataFrame:
    """Margins, year-over-year growth and degree of operating leverage (see README for formulas)."""
    m = s.copy()
    m["gross_margin"] = m["gross_profit"] / m["revenue"]
    m["operating_margin"] = m["operating_income"] / m["revenue"]
    m["net_margin"] = m["net_income"] / m["revenue"]
    # Growth is only meaningful between consecutive fiscal years (about 365 days apart).
    consecutive = m.index.to_series().diff().dt.days.between(350, 380)
    for col in ("revenue", "operating_income", "net_income"):
        m[f"{col}_growth"] = (m[col] / m[col].shift(1) - 1).where(consecutive)
    # DOL divides by revenue growth, so it explodes as growth approaches zero: leave it blank below 1%.
    m["operating_leverage"] = (m["operating_income_growth"] / m["revenue_growth"]).where(m["revenue_growth"].abs() >= MIN_GROWTH_FOR_DOL)
    return m


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(), help="YYYY-MM-DD, point-in-time date")
    parser.add_argument("--years", type=int, default=5, help="fiscal years to show")
    parser.add_argument("--sample", action="store_true", help="use sample/aapl_facts.csv instead of the SEC API")
    args = parser.parse_args()

    if args.sample:
        facts, label = pd.read_csv(HERE / "sample" / "aapl_facts.csv"), "AAPL (sample)"
    else:
        cik = ticker_to_cik(args.ticker)
        facts, label = fetch_facts(cik), f"{args.ticker.upper()} (CIK {cik})"
    if facts.empty:
        sys.exit("No matching us-gaap USD facts found for this company.")

    table = add_metrics(build_statement(annual_values(facts, args.as_of))).tail(args.years)

    usd_m = ["revenue", "gross_profit", "operating_income", "net_income"]
    pct = ["gross_margin", "operating_margin", "net_margin", "revenue_growth", "operating_income_growth", "net_income_growth"]
    show = pd.DataFrame(index=table.index.date)
    for col in usd_m:
        show[col] = [f"{v / 1e6:,.0f}" if pd.notna(v) else "" for v in table[col]]
    for col in pct:
        show[col] = [f"{v * 100:.1f}" if pd.notna(v) else "" for v in table[col]]
    show["operating_leverage"] = [f"{v:.2f}" if pd.notna(v) else "" for v in table["operating_leverage"]]
    print(f"{label}, fiscal years ending, as of {args.as_of}. USD millions; margins and growth in %.\n")
    print(show.T.to_string())

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    path = out / f"income_statement_{'sample' if args.sample else args.ticker.upper()}.csv"
    table.to_csv(path)
    print(f"\nFull table written to {path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
