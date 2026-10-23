"""Options volume and open interest: put/call ratios, unusual activity, concentration and OI change.

Cboe's delayed feed only shows today's chain, so --save-snapshot archives each run to a local
Parquet lake (quanttk.sources.snapshots). Once an earlier day is saved, the report adds the
change in open interest since then. Run it once a day after the close to build history.

Usage:
    python main.py                         # SPX
    python main.py --symbol SPY --save-snapshot
    python main.py --symbol AAPL --min-volume 500
    python main.py --sample                # offline, from sample/chain.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
try:
    import quanttk  # noqa: F401
except ImportError:  # running from a checkout without `pip install -e .`
    sys.path.insert(0, str(HERE.parents[2]))

from quanttk.options.volume import oi_change, oi_concentration, put_call_by_expiry, put_call_summary, unusual_activity  # noqa: E402
from quanttk.sources.cboe import load_chain, load_sample_chain, parse_contracts  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", default="_SPX", help="Cboe symbol: _SPX, SPY, QQQ, AAPL, ...")
    parser.add_argument("--min-volume", type=int, default=1000, help="volume threshold for the unusual-activity screen")
    parser.add_argument("--min-ratio", type=float, default=1.0, help="volume / open interest threshold for the screen")
    parser.add_argument("--save-snapshot", action="store_true", help="archive this chain to the Parquet lake (needs pyarrow)")
    parser.add_argument("--sample", action="store_true", help="use sample/chain.csv instead of live data")
    args = parser.parse_args()

    if args.sample:
        chain, spot, snapshot = load_sample_chain(HERE / "sample" / "chain.csv")
        label = "SPX (sample)"
    else:
        chain, spot, snapshot = load_chain(args.symbol)
        label = args.symbol

    df = parse_contracts(chain, snapshot)
    df = df[df["T"] > 0].copy()  # drop contracts already past settlement
    print(f"{label}: spot {spot:,.2f}, snapshot {snapshot:%Y-%m-%d %H:%M} UTC, {len(df):,} live contracts "
          f"across {df['expiry'].nunique()} expiries\n")

    s = put_call_summary(df)
    print(f"Total volume: calls {s['call_volume']:,.0f}, puts {s['put_volume']:,.0f}  ->  put/call volume ratio {s['pc_volume']:.2f}")
    print(f"Open interest: calls {s['call_oi']:,.0f}, puts {s['put_oi']:,.0f}  ->  put/call OI ratio {s['pc_open_interest']:.2f}\n")

    by_exp = put_call_by_expiry(df)
    busiest = by_exp.assign(total=by_exp["call_volume"] + by_exp["put_volume"]).sort_values("total", ascending=False).head(10)
    print("Busiest expiries by volume:")
    print(busiest.drop(columns="total").round({"pc_volume": 2, "pc_oi": 2}).to_string(), "\n")

    conc = oi_concentration(df)
    print("Strikes with the most open interest (all expiries):")
    print(conc.round({"share_of_total": 4}).to_string(), "\n")

    hot = unusual_activity(df, args.min_volume, args.min_ratio)
    print(f"Unusual activity (volume >= {args.min_volume:,} and volume / OI >= {args.min_ratio}):")
    if hot.empty:
        print("  none\n")
    else:
        cols = ["option", "expiry", "cp", "strike", "volume", "open_interest", "vol_oi_ratio", "last_trade_price"]
        print(hot[cols].round({"vol_oi_ratio": 2}).to_string(index=False), "\n")

    name = "sample" if args.sample else args.symbol.strip("_")
    change = None
    if not args.sample:
        try:
            from quanttk.sources.snapshots import latest_snapshot_before, save_snapshot

            previous = latest_snapshot_before(args.symbol, snapshot)
            if previous is not None:
                prev_df, prev_ts = previous
                change = oi_change(df, prev_df)
                top = change.reindex(change["oi_change"].abs().sort_values(ascending=False).index).head(15)
                print(f"Largest open-interest changes since {prev_ts:%Y-%m-%d %H:%M} UTC:")
                print(top[["option", "expiry", "cp", "strike", "previous_oi", "open_interest", "oi_change"]].to_string(index=False), "\n")
            else:
                print("Open-interest change: no earlier snapshot saved yet (run with --save-snapshot daily to build history).\n")
            if args.save_snapshot:
                print(f"Snapshot saved: {save_snapshot(chain, spot, snapshot, args.symbol)}\n")
        except ImportError as exc:
            print(f"Snapshot archive unavailable ({exc}); install pyarrow to enable it.\n")
    else:
        print("Open-interest change skipped in --sample mode: it needs a saved snapshot from an earlier day.\n")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    by_exp.to_csv(out / f"put_call_by_expiry_{name}.csv")
    conc.to_csv(out / f"oi_concentration_{name}.csv")
    hot.drop(columns=["expiry_utc"], errors="ignore").to_csv(out / f"unusual_activity_{name}.csv", index=False)
    written = [f"put_call_by_expiry_{name}.csv", f"oi_concentration_{name}.csv", f"unusual_activity_{name}.csv"]
    if change is not None:
        change.drop(columns=["expiry_utc"], errors="ignore").to_csv(out / f"oi_change_{name}.csv", index=False)
        written.append(f"oi_change_{name}.csv")
    print("Written: " + ", ".join(f"output/{w}" for w in written))


if __name__ == "__main__":
    main()
