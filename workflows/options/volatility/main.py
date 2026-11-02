"""Options volatility: term structure, skew, realized vs implied, and a VIX replication check.

Implied volatilities come from each option's bid/ask mid (Black-76 on a put-call-parity
forward, Treasury rates), using the same pricing as the Greeks workflow (quanttk.options.surface).

Usage:
    python main.py                       # SPX: term structure, skew, realized vol and VIX replication
    python main.py --symbol SPY --max-days 90
    python main.py --sample              # offline, from sample/
"""

from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
try:
    import quanttk  # noqa: F401
except ImportError:  # running from a checkout without `pip install -e .`
    sys.path.insert(0, str(HERE.parents[2]))

from quanttk.options.surface import price_chain, tradable  # noqa: E402
from quanttk.options.volatility import realized_vol, skew, term_structure, vix_replica  # noqa: E402
from quanttk.sources.cboe import ET, load_chain, load_quote, load_sample_chain, parse_contracts  # noqa: E402
from quanttk.sources.treasury import continuous_rate, load_sample_curve, load_yield_curve  # noqa: E402


def prefer_pm_series(df: pd.DataFrame) -> pd.DataFrame:
    """When an expiry date lists both AM-settled SPX and PM-settled SPXW, keep SPXW (more liquid,
    one series per date). Other underlyings have one root and pass through unchanged."""
    roots = df.groupby("expiry")["root"].transform(lambda s: "SPXW" if {"SPX", "SPXW"} <= set(s) else None)
    return df[roots.isna() | (df["root"] == roots)]


def iv_at_days(ts: pd.DataFrame, days: float) -> float:
    """ATM implied vol at a constant maturity, interpolating total variance (sigma^2 T) linearly in T."""
    t = days / 365
    if len(ts) < 2 or t < ts["T"].min() or t > ts["T"].max():
        return np.nan
    var = np.interp(t, ts["T"], ts["atm_iv"] ** 2 * ts["T"])
    return float(np.sqrt(var / t))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", default="_SPX", help="Cboe symbol: _SPX, SPY, QQQ, AAPL, ...")
    parser.add_argument("--max-days", type=int, default=120, help="expiries within this many days")
    parser.add_argument("--sample", action="store_true", help="use sample/ instead of live data")
    args = parser.parse_args()

    if args.sample:
        chain, spot, snapshot = load_sample_chain(HERE / "sample" / "chain.csv")
        curve = load_sample_curve(HERE / "sample" / "yield_curve.csv")
        closes = pd.read_csv(HERE / "sample" / "closes.csv", index_col="date", parse_dates=["date"])["close"]
        label = "SPX (sample)"
    else:
        chain, spot, snapshot = load_chain(args.symbol)
        curve = load_yield_curve(snapshot.tz_convert(ET).date())
        label = args.symbol
        try:
            from quanttk.sources.prices import daily_closes

            closes = daily_closes(args.symbol, (snapshot - timedelta(days=150)).date(), (snapshot + timedelta(days=1)).date(),
                                  adjusted=True)
        except Exception as exc:  # realized vol is optional: keep going without prices
            print(f"(realized volatility skipped: {exc})")
            closes = None

    parsed = parse_contracts(chain, snapshot)
    priced = price_chain(prefer_pm_series(tradable(parsed, args.max_days)), spot, curve)
    print(f"{label}: spot {spot:,.2f}, snapshot {snapshot:%Y-%m-%d %H:%M} UTC, {priced['my_iv'].notna().sum():,} contracts with an IV\n")

    ts = term_structure(priced)
    print("Term structure (ATM IV at the forward; forward vol between consecutive expiries):")
    show = ts[["root", "expiry", "days", "forward", "atm_iv", "forward_vol"]].copy()
    print(show.round({"days": 1, "forward": 2, "atm_iv": 4, "forward_vol": 4}).head(20).to_string(index=False), "\n")

    sk = skew(priced)
    print("Skew (25-delta risk reversal and butterfly; negative RR = puts richer than calls):")
    print(sk.round({"days": 1, "atm_iv": 4, "call_25d_iv": 4, "put_25d_iv": 4, "risk_reversal": 4, "butterfly": 4})
          .head(20).to_string(index=False), "\n")

    iv30 = iv_at_days(ts, 30)
    if closes is not None and len(closes) > 25:
        rv = realized_vol(closes)
        print("Realized vs implied:")
        print("  realized vol (close-to-close, annualized): " + ", ".join(f"{k} {v:.2%}" for k, v in rv.items()))
        if not np.isnan(iv30) and "21d" in rv:
            print(f"  30-day ATM implied vol {iv30:.2%} - 21-day realized {rv['21d']:.2%} = "
                  f"volatility risk premium {iv30 - rv['21d']:+.2%}")
        print()

    if args.symbol == "_SPX" and not args.sample:
        replica = vix_replica(parsed[parsed["T"] > 0], lambda T: continuous_rate(curve, np.array([T]))[0])
        vix = load_quote("_VIX")
        near, nxt = replica["near"], replica["next"]
        print("VIX replication (Cboe methodology, from this SPX snapshot):")
        print(f"  near term {near['root']} {near['expiry']} ({near['minutes'] / 1440:.1f} days, {near['strikes_used']} strikes), "
              f"next term {nxt['root']} {nxt['expiry']} ({nxt['minutes'] / 1440:.1f} days, {nxt['strikes_used']} strikes)")
        print(f"  replicated VIX {replica['vix']:.2f} vs Cboe VIX {vix['current_price']:.2f} "
              f"(difference {replica['vix'] - vix['current_price']:+.2f} points)\n")
    elif args.sample:
        print("VIX replication skipped in --sample mode: it needs every out-of-the-money strike for two expiries.\n")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    name = "sample" if args.sample else args.symbol.strip("_")
    ts.to_csv(out / f"term_structure_{name}.csv", index=False)
    sk.to_csv(out / f"skew_{name}.csv", index=False)
    priced.drop(columns=["expiry_utc"]).to_csv(out / f"surface_{name}.csv", index=False)
    print(f"Written: output/term_structure_{name}.csv, output/skew_{name}.csv, output/surface_{name}.csv")


if __name__ == "__main__":
    main()
