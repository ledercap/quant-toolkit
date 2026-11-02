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
import sys
from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
try:
    import quanttk  # noqa: F401
except ImportError:  # running from a checkout without `pip install -e .`
    sys.path.insert(0, str(HERE.parents[2]))

from quanttk.sources.edgar import fetch_facts, ticker_to_cik  # noqa: E402
from quanttk.statements.build import apply_concepts, growth  # noqa: E402
from quanttk.statements.concepts import INCOME_STATEMENT, tags_for  # noqa: E402

ITEMS = ["revenue", "cost_of_revenue", "gross_profit", "operating_income", "net_income"]
CONCEPTS = {k: INCOME_STATEMENT[k] for k in ITEMS}
MIN_GROWTH_FOR_DOL = 0.01


def build_statement(facts: pd.DataFrame, as_of: date) -> pd.DataFrame:
    """Annual line items, point-in-time. Some filers report revenue and cost of revenue but not gross profit."""
    out = apply_concepts(facts, CONCEPTS, as_of)
    out["gross_profit"] = out["gross_profit"].fillna(out["revenue"] - out["cost_of_revenue"])
    return out.dropna(subset=["revenue"]).sort_index()


def add_metrics(s: pd.DataFrame) -> pd.DataFrame:
    """Margins, year-over-year growth and degree of operating leverage (see README for formulas)."""
    m = s.copy()
    m["gross_margin"] = m["gross_profit"] / m["revenue"]
    m["operating_margin"] = m["operating_income"] / m["revenue"]
    m["net_margin"] = m["net_income"] / m["revenue"]
    for col in ("revenue", "operating_income", "net_income"):  # consecutive fiscal years only
        m[f"{col}_growth"] = growth(m[col])
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
        facts, label = fetch_facts(cik, tags_for(CONCEPTS)), f"{args.ticker.upper()} (CIK {cik})"
    if facts.empty:
        sys.exit("No matching us-gaap USD facts found for this company.")

    table = add_metrics(build_statement(facts, args.as_of)).tail(args.years)

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
