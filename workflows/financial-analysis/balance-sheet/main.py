"""Balance sheet analysis from SEC EDGAR: liquidity, leverage and working capital.

Point-in-time: balances are read on each fiscal year-end date from 10-K filings public on
or before --as-of, with the latest such filing winning (so restatements replace originals).

Usage:
    python main.py --ticker AAPL
    python main.py --ticker JPM --as-of 2024-12-31 --years 6
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

from quanttk.ratios.registry import RATIOS_BY_NAME, div  # noqa: E402
from quanttk.sources.edgar import fetch_facts, ticker_to_cik  # noqa: E402
from quanttk.statements.build import coverage_warnings  # noqa: E402
from quanttk.statements.concepts import BALANCE_SHEET, INCOME_STATEMENT, tags_for  # noqa: E402
from quanttk.statements.derived import annual_statements  # noqa: E402

# Revenue anchors the fiscal year ends and feeds working capital / revenue.
CONCEPTS = {**BALANCE_SHEET, "revenue": INCOME_STATEMENT["revenue"]}
BALANCES = ["cash_and_investments", "receivables", "inventory", "current_assets", "total_assets", "payables",
            "current_liabilities", "total_debt", "total_liabilities", "equity", "working_capital", "net_debt"]
RATIOS = ["current_ratio", "quick_ratio", "cash_ratio", "debt_to_equity", "debt_to_assets",
          "liabilities_to_assets", "equity_multiplier"]


def add_metrics(st: pd.DataFrame) -> pd.DataFrame:
    """Registry ratios plus working capital as a share of revenue (see README for formulas)."""
    m = st.copy()
    for name in RATIOS:
        m[name] = RATIOS_BY_NAME[name].compute(m)
    m["working_capital_to_revenue"] = div(m["working_capital"], m["revenue"])
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
        sys.exit("No matching us-gaap facts found for this company.")

    table = add_metrics(annual_statements(facts, args.as_of, CONCEPTS)).tail(args.years)

    show = pd.DataFrame(index=table.index.date)
    for col in BALANCES:
        show[col] = [f"{v / 1e6:,.0f}" if pd.notna(v) else "" for v in table[col]]
    for col in RATIOS:
        show[col] = [f"{v:.2f}" if pd.notna(v) else "" for v in table[col]]
    show["working_capital_to_revenue_%"] = [f"{v * 100:.1f}" if pd.notna(v) else "" for v in table["working_capital_to_revenue"]]
    print(f"{label}, balances at fiscal year end, as of {args.as_of}. USD millions; ratios in times (x).\n")
    print(show.T.to_string())
    for warning in coverage_warnings(table, list(BALANCE_SHEET)):
        print(f"WARNING: {warning}")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    path = out / f"balance_sheet_{'sample' if args.sample else args.ticker.upper()}.csv"
    table.to_csv(path)
    print(f"\nFull table written to {path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
