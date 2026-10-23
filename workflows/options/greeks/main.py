"""Black-Scholes-Merton implied volatility and Greeks for a Cboe options chain.

For each expiry the forward price is implied from put-call parity (Cboe VIX method), the
risk-free rate comes from the US Treasury par yield curve, implied volatility is solved
from each option's bid/ask mid, and delta, gamma, vega, theta and rho follow from BSM.
The results are compared with the Greeks Cboe publishes for the same contracts.

Usage:
    python main.py                    # SPX, expiries up to 60 days
    python main.py --symbol SPY --max-days 30
    python main.py --sample           # offline, from sample/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
try:
    import quanttk  # noqa: F401
except ImportError:  # running from a checkout without `pip install -e .`
    sys.path.insert(0, str(HERE.parents[2]))

from quanttk.options.surface import price_chain, tradable  # noqa: E402
from quanttk.sources.cboe import ET, load_chain, load_sample_chain, parse_contracts  # noqa: E402
from quanttk.sources.treasury import load_sample_curve, load_yield_curve  # noqa: E402


# ---------------------------------------------------------------- report

def compare_with_cboe(df: pd.DataFrame) -> pd.DataFrame:
    """Median absolute differences vs Cboe, on liquid contracts with 0.10 < |delta| < 0.90 and T >= 7 days."""
    ok = df["my_iv"].notna() & (df["iv"] > 0) & df["delta"].abs().between(0.10, 0.90) & (df["T"] >= 7 / 365)
    s = df[ok]
    rows = {
        "IV (vol points)": (s["my_iv"] - s["iv"]).abs() * 100,
        "delta": (s["my_delta"] - s["delta"]).abs(),
        "gamma (% of Cboe)": ((s["my_gamma"] / s["gamma"]) - 1).abs() * 100,
        "vega (% of Cboe)": ((s["my_vega"] / s["vega"]) - 1).abs() * 100,
        "theta decay term (% of Cboe)": ((s["my_theta_decay"] / s["theta"]) - 1).abs() * 100,
    }
    return pd.DataFrame({"median abs diff": {k: v.median() for k, v in rows.items()},
                         "90th pct abs diff": {k: v.quantile(0.9) for k, v in rows.items()},
                         "contracts": {k: v.notna().sum() for k, v in rows.items()}}).round(4)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", default="_SPX", help="Cboe symbol: _SPX, SPY, QQQ, AAPL, ...")
    parser.add_argument("--max-days", type=int, default=60, help="only expiries within this many days")
    parser.add_argument("--sample", action="store_true", help="use sample/ instead of live data")
    args = parser.parse_args()

    if args.sample:
        chain, spot, snapshot = load_sample_chain(HERE / "sample" / "chain.csv")
        curve = load_sample_curve(HERE / "sample" / "yield_curve.csv")
        label = f"{chain['option'].str.extract(r'^([A-Z]+)')[0].iloc[0]} (sample)"
    else:
        chain, spot, snapshot = load_chain(args.symbol)
        curve = load_yield_curve(snapshot.tz_convert(ET).date())
        label = args.symbol

    df = tradable(parse_contracts(chain, snapshot), args.max_days)
    df = price_chain(df, spot, curve)

    print(f"{label}: spot {spot:,.2f}, snapshot {snapshot:%Y-%m-%d %H:%M} UTC, {len(df):,} contracts priced\n")
    per_expiry = df.groupby(["root", "expiry"]).agg(days=("T", lambda t: t.iloc[0] * 365), r=("r", "first"),
                                                     forward=("F", "first"), q=("q", "first"))
    atm = df.loc[(df["strike"] - df["F"]).abs().groupby([df["root"], df["expiry"]]).idxmin()]
    per_expiry["atm_iv"] = atm.set_index(["root", "expiry"])["my_iv"]
    print("Per expiry (r and q continuous, annualised; ATM IV from the strike nearest the forward):")
    print(per_expiry.round({"days": 1, "r": 4, "forward": 2, "q": 4, "atm_iv": 4}).head(15).to_string(), "\n")

    print("Comparison with Cboe's published IV and Greeks:")
    print(compare_with_cboe(df).to_string(), "\n")

    near = per_expiry.index[np.argmin(np.abs(per_expiry["days"].values - 30))]
    sel = df[(df["root"] == near[0]) & (df["expiry"] == near[1])]
    sel = sel.loc[(sel["strike"] - sel["F"]).abs().sort_values().index[:10]].sort_values(["cp", "strike"])
    cols = ["option", "mid", "iv", "my_iv", "delta", "my_delta", "gamma", "my_gamma", "vega", "my_vega",
            "theta", "my_theta_decay", "my_theta"]
    print(f"Near-the-money contracts, {near[0]} {near[1]} (columns without my_ are Cboe's; my_theta is full BSM theta):")
    print(sel[cols].round(4).to_string(index=False))

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    path = out / f"greeks_{'sample' if args.sample else args.symbol.strip('_')}.csv"
    df.drop(columns=["expiry_utc"]).to_csv(path, index=False)
    print(f"\nAll contracts written to {path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
