"""Financial ratio layer: every registered ratio for a company by year, or side by side for peers.

Ratios come from quanttk.ratios (one definition each, with formula and source), computed on
standardized, point-in-time annual statements built from SEC EDGAR. Valuation ratios need
prices: add --prices to fetch as-traded closes on each 10-K filing date (yfinance; personal use).

Usage:
    python main.py --ticker AAPL                          # all ratios, last 4 fiscal years
    python main.py --ticker AAPL --prices                 # include valuation ratios
    python main.py --tickers AAPL,MSFT,GOOGL --prices     # latest fiscal year, side by side
    python main.py --ticker MSFT --category profitability,dupont
    python main.py --list                                 # the ratio registry
    python main.py --sample                               # offline, from sample/
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
try:
    import quanttk  # noqa: F401
except ImportError:  # running from a checkout without `pip install -e .`
    sys.path.insert(0, str(HERE.parents[2]))

from quanttk.ratios.registry import RATIOS, RATIOS_BY_NAME, add_valuation_inputs, compute_ratios, ratio_table  # noqa: E402
from quanttk.sources.edgar import fetch_facts, ticker_to_cik  # noqa: E402
from quanttk.statements.build import coverage_warnings  # noqa: E402
from quanttk.statements.concepts import ALL_CONCEPTS, tags_for  # noqa: E402
from quanttk.statements.derived import annual_statements  # noqa: E402

CATEGORIES = list(dict.fromkeys(r.category for r in RATIOS))


def statements_for(ticker: str, as_of: date, with_prices: bool) -> pd.DataFrame:
    cik = ticker_to_cik(ticker)
    st = annual_statements(fetch_facts(cik, tags_for(ALL_CONCEPTS)), as_of)
    if with_prices and not st.empty:
        from quanttk.sources.prices import daily_closes

        start = st["first_filed"].min() - timedelta(days=10)
        st = add_valuation_inputs(st, daily_closes(ticker, start.date(), as_of + timedelta(days=1)))
    return st


def fmt(value: float, unit: str) -> str:
    if pd.isna(value):
        return ""
    return {"%": f"{value * 100:.1f}%", "days": f"{value:.0f}"}.get(unit, f"{value:.2f}")


def format_table(ratios: pd.DataFrame) -> pd.DataFrame:
    """Rows = ratios grouped by category, columns = years or tickers, values formatted by unit."""
    rows = {}
    for r in RATIOS:
        if r.name in ratios:
            rows[(r.category, r.name)] = [fmt(v, r.unit) for v in ratios[r.name]]
    out = pd.DataFrame(rows, index=ratios.index).T
    out.index.names = ["category", "ratio"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--tickers", help="comma-separated peers: latest fiscal year side by side")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(), help="YYYY-MM-DD, point-in-time date")
    parser.add_argument("--years", type=int, default=4, help="fiscal years to show (single ticker)")
    parser.add_argument("--category", help=f"comma-separated subset of: {', '.join(CATEGORIES)}")
    parser.add_argument("--prices", action="store_true", help="fetch prices for valuation ratios (yfinance, personal use)")
    parser.add_argument("--list", action="store_true", help="print the ratio registry and exit")
    parser.add_argument("--sample", action="store_true", help="use sample/ instead of live data")
    args = parser.parse_args()

    if args.list:
        print(ratio_table().to_string(index=False))
        return
    categories = args.category.split(",") if args.category else None
    if categories and (bad := set(categories) - set(CATEGORIES)):
        sys.exit(f"Unknown category {sorted(bad)}; choose from {CATEGORIES}")

    if args.tickers and not args.sample:
        latest = {}
        for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
            st = statements_for(t, args.as_of, args.prices)
            r = compute_ratios(st, categories)
            if r.empty:
                print(f"WARNING: no annual statements found for {t}")
                continue
            latest[f"{t} ({r.index[-1].date()})"] = r.iloc[-1]
        table = pd.DataFrame(latest).T
        title = f"Latest fiscal year per company (year end in brackets), as of {args.as_of}."
        name = "peers_" + "_".join(k.split()[0] for k in latest)
    else:
        if args.sample:
            st = annual_statements(pd.read_csv(HERE / "sample" / "aapl_facts.csv"), args.as_of)
            closes = pd.read_csv(HERE / "sample" / "aapl_prices.csv", index_col="date", parse_dates=["date"])["close"]
            st = add_valuation_inputs(st, closes)
            label, name = "AAPL (sample)", "sample"
        else:
            st = statements_for(args.ticker, args.as_of, args.prices)
            label, name = args.ticker.upper(), args.ticker.upper()
        for warning in coverage_warnings(st, list(ALL_CONCEPTS)):
            if pd.Timestamp(warning.split("year ending ")[1].split(" ")[0]) >= st.index[-min(args.years, len(st))]:
                print(f"WARNING: {warning}")
        table = compute_ratios(st, categories).tail(args.years)
        table.index = table.index.date
        title = f"{label}, fiscal years ending, as of {args.as_of}."

    print(f"{title} Ratios on average balances (ROE, ROA, turnover, days) need the prior fiscal year, so they are blank for a company's first reported year.\n")
    print(format_table(table).to_string())
    dupont = ["dupont_net_margin", "dupont_asset_turnover", "dupont_equity_multiplier", "roe"]
    if all(c in table for c in dupont):
        check = (table[dupont[0]] * table[dupont[1]] * table[dupont[2]] - table["roe"]).abs().max()
        print(f"\nDuPont check: net margin x asset turnover x equity multiplier - ROE = {check:.2e} (should be ~0)")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    path = out / f"ratios_{name}.csv"
    table.to_csv(path)
    print(f"Full table written to {path.relative_to(HERE)}")
    sources = sorted({RATIOS_BY_NAME[c].source for c in table.columns if c in RATIOS_BY_NAME})
    print(f"Ratio sources: {', '.join(sources)} (see README)")


if __name__ == "__main__":
    main()
