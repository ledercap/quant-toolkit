"""Cash flow analysis from SEC EDGAR: free cash flow, conversion, capex intensity and payouts.

Point-in-time: only facts from filings public on or before --as-of are used, and the
latest such filing wins for each fiscal year (so restatements replace earlier values).

Usage:
    python main.py --ticker AAPL
    python main.py --ticker AMZN --as-of 2024-12-31 --years 6
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

from quanttk.ratios.registry import RATIOS_BY_NAME, col, div  # noqa: E402
from quanttk.sources.edgar import fetch_facts, ticker_to_cik  # noqa: E402
from quanttk.statements.build import coverage_warnings, growth  # noqa: E402
from quanttk.statements.concepts import CASH_FLOW, INCOME_STATEMENT, tags_for  # noqa: E402
from quanttk.statements.derived import annual_statements  # noqa: E402

CONCEPTS = {**CASH_FLOW, **{k: INCOME_STATEMENT[k] for k in ("revenue", "net_income", "operating_income")}}
AMOUNTS = ["operating_cash_flow", "capex", "free_cash_flow", "depreciation_amortization", "stock_based_compensation",
           "fcf_after_sbc", "dividends_paid", "buybacks", "cash_returned"]
RATIOS = ["fcf_margin", "fcf_conversion", "capex_intensity", "capex_to_depreciation", "payout_ratio", "total_payout_ratio"]


def add_metrics(st: pd.DataFrame) -> pd.DataFrame:
    """Registry ratios plus cash-flow specific measures (see README for formulas)."""
    m = st.copy()
    for name in RATIOS:
        m[name] = RATIOS_BY_NAME[name].compute(m)
    m["cfo_to_net_income"] = div(m["operating_cash_flow"], m["net_income"])
    m["sbc_to_revenue"] = div(col(m, "stock_based_compensation"), m["revenue"])
    m["fcf_after_sbc"] = m["free_cash_flow"] - col(m, "stock_based_compensation").fillna(0)
    m["cash_returned"] = col(m, "dividends_paid").fillna(0) + col(m, "buybacks").fillna(0)
    m["cash_returned_to_fcf"] = div(m["cash_returned"], m["free_cash_flow"])
    m["fcf_growth"] = growth(m["free_cash_flow"], positive_base=True)
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

    pct = ["fcf_margin", "capex_intensity", "sbc_to_revenue", "payout_ratio", "total_payout_ratio", "fcf_growth"]
    times = ["fcf_conversion", "cfo_to_net_income", "capex_to_depreciation", "cash_returned_to_fcf"]
    show = pd.DataFrame(index=table.index.date)
    for c in AMOUNTS:
        show[c] = [f"{v / 1e6:,.0f}" if pd.notna(v) else "" for v in table[c]]
    for c in pct:
        show[f"{c}_%"] = [f"{v * 100:.1f}" if pd.notna(v) else "" for v in table[c]]
    for c in times:
        show[c] = [f"{v:.2f}" if pd.notna(v) else "" for v in table[c]]
    print(f"{label}, fiscal years ending, as of {args.as_of}. USD millions; % and times (x) as labelled.\n")
    print(show.T.to_string())
    for warning in coverage_warnings(table, list(CASH_FLOW)):
        print(f"WARNING: {warning}")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    path = out / f"cash_flow_{'sample' if args.sample else args.ticker.upper()}.csv"
    table.to_csv(path)
    print(f"\nFull table written to {path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
