"""Dealer gamma exposure (GEX) from a Cboe options chain: by strike, total, walls, flip level and sensitivity range.

Convention (SqueezeMetrics): dealers are long the calls and short the puts that customers
hold, so call gamma counts positive and put gamma negative. GEX is in dollars of delta
change per 1% move in the underlying.

Usage:
    python main.py                    # SPX, with SqueezeMetrics GEX in the sensitivity range
    python main.py --symbol SPY
    python main.py --sample           # offline, from sample/chain.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).parent
try:
    import quanttk  # noqa: F401
except ImportError:  # running from a checkout without `pip install -e .`
    sys.path.insert(0, str(HERE.parents[2]))

from quanttk.options.gex import (  # noqa: E402
    contract_gamma, gamma_profile, gex_contracts, gex_dollars, sensitivity, summarize_range, zero_crossing,
)
from quanttk.sources.cboe import load_chain, load_sample_chain  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", default="_SPX", help="Cboe symbol: _SPX, SPY, QQQ, AAPL, ...")
    parser.add_argument("--sample", action="store_true", help="use sample/chain.csv instead of live data")
    args = parser.parse_args()

    if args.sample:
        chain, spot, snapshot = load_sample_chain(HERE / "sample" / "chain.csv")
        label = "SPX (sample)"
    else:
        chain, spot, snapshot = load_chain(args.symbol)
        label = args.symbol

    df = gex_contracts(chain, snapshot)
    df["gamma_used"] = contract_gamma(df, spot)
    df["gex"] = gex_dollars(df["gamma_used"], df["open_interest"], df["sign"], spot)
    gex_cboe_rounded = gex_dollars(df["gamma"], df["open_interest"], df["sign"], spot).sum()

    by_strike = df.pivot_table(index="strike", columns="cp", values="gex", aggfunc="sum", fill_value=0.0)
    by_strike = by_strike.reindex(columns=["C", "P"], fill_value=0.0).rename(columns={"C": "call_gex", "P": "put_gex"})
    by_strike["net_gex"] = by_strike["call_gex"] + by_strike["put_gex"]

    total = df["gex"].sum()
    call_wall = by_strike["call_gex"].idxmax()
    put_wall = by_strike["put_gex"].idxmin()
    profile = gamma_profile(df, spot)
    flip = zero_crossing(profile, spot)

    print(f"{label}: spot {spot:,.2f}, snapshot {snapshot:%Y-%m-%d %H:%M} UTC, "
          f"{len(df):,} contracts with open interest across {df['expiry'].nunique()} expiries\n")
    print(f"Total GEX:            ${total / 1e9:,.2f} bn per 1% move "
          f"({'positive: dealers dampen moves' if total > 0 else 'negative: dealers amplify moves'})")
    print(f"  of which calls:     ${df.loc[df['sign'] > 0, 'gex'].sum() / 1e9:,.2f} bn, "
          f"puts: ${df.loc[df['sign'] < 0, 'gex'].sum() / 1e9:,.2f} bn")
    print(f"  0-1 day expiries:   ${df.loc[df['T'] <= 1 / 365, 'gex'].sum() / 1e9:,.2f} bn")
    print(f"Call wall:            {call_wall:,.0f} (largest positive call GEX)")
    print(f"Put wall:             {put_wall:,.0f} (largest negative put GEX)")
    print(f"Gamma flip:           {f'{flip:,.0f} ({(flip / spot - 1) * 100:+.1f}% from spot)' if flip else 'no sign change within ±15%'}")
    print(f"For reference:        ${gex_cboe_rounded / 1e9:,.2f} bn using Cboe's published (rounded) gamma; "
          f"{(df['iv'] <= 0).sum():,} contracts had no IV and use Cboe's gamma\n")

    near = by_strike[(by_strike.index > spot * 0.95) & (by_strike.index < spot * 1.05)]
    top = near.reindex(near["net_gex"].abs().sort_values(ascending=False).index[:12]).sort_index()
    print("Largest net GEX strikes within ±5% of spot ($ millions per 1% move):")
    print((top / 1e6).round(1).to_string(), "\n")

    sens = sensitivity(df, include_squeezemetrics=(args.symbol == "_SPX" and not args.sample))
    rng = summarize_range(sens)
    low, high, median, verdict = rng["low"], rng["high"], rng["median"], rng["verdict"]
    print("Sensitivity of total GEX to assumptions ($ bn per 1% move):")
    print((sens / 1e9).round(2).to_string())
    print(f"Range: ${low / 1e9:,.2f} to ${high / 1e9:,.2f} bn | Median: ${median / 1e9:,.2f} bn | {verdict}")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    name = "sample" if args.sample else args.symbol.strip("_")
    by_strike.to_csv(out / f"gex_by_strike_{name}.csv")
    profile.rename("total_gex").rename_axis("spot_level").to_csv(out / f"gex_profile_{name}.csv")
    sens.rename_axis("assumption").to_csv(out / f"gex_sensitivity_{name}.csv")
    print(f"\nWritten: output/gex_by_strike_{name}.csv, output/gex_profile_{name}.csv, output/gex_sensitivity_{name}.csv")


if __name__ == "__main__":
    main()
