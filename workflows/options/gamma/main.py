"""Dealer gamma exposure (GEX) from a Cboe options chain: by strike, total, walls, flip level and sensitivity range.

Convention (SqueezeMetrics): dealers are long the calls and short the puts that customers
hold, so call gamma counts positive and put gamma negative. GEX is in dollars of delta
change per 1% move in the underlying.

Usage:
    python main.py                    # SPX, with SqueezeMetrics GEX printed as a reference
    python main.py --symbol SPY
    python main.py --sample           # offline, from sample/chain.csv
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).parent
ET = ZoneInfo("America/New_York")
SECONDS_PER_YEAR = 365.0 * 24 * 3600
MULTIPLIER = 100  # shares per contract for US equity and index options
AM_SETTLED_ROOTS = {"SPX"}  # SPX monthlies settle at the open; SPXW and equity options at the close
SQUEEZEMETRICS_CSV = "https://squeezemetrics.com/monitor/static/DIX.csv"


def get_json(url: str, attempts: int = 3) -> dict:
    """GET with retries: Cboe's CDN occasionally drops large downloads."""
    for i in range(attempts):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=90)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if i == attempts - 1:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError("unreachable")


def load_chain(symbol: str) -> tuple[pd.DataFrame, float, pd.Timestamp]:
    """Cboe delayed chain -> (contracts, spot, snapshot time in UTC)."""
    raw = get_json(f"https://cdn.cboe.com/api/global/delayed_quotes/options/{symbol}.json")
    return pd.DataFrame(raw["data"]["options"]), float(raw["data"]["current_price"]), pd.Timestamp(raw["timestamp"], tz="UTC")


def parse_contracts(chain: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """Split OCC symbols, compute time to expiry, and keep unexpired contracts with open interest."""
    parts = chain["option"].str.extract(r"^(?P<root>[A-Z]+)(?P<ymd>\d{6})(?P<cp>[CP])(?P<k>\d{8})$")
    df = chain.join(parts)
    df["strike"] = df["k"].astype(int) / 1000
    expiry_day = pd.to_datetime(df["ymd"], format="%y%m%d")
    settle_hour = np.where(df["root"].isin(AM_SETTLED_ROOTS), 9.5, 16.0)
    expiry_utc = (expiry_day + pd.to_timedelta(settle_hour, unit="h")).dt.tz_localize(ET).dt.tz_convert("UTC")
    df["expiry"] = expiry_day.dt.date
    df["T"] = (expiry_utc - snapshot).dt.total_seconds() / SECONDS_PER_YEAR
    df["sign"] = np.where(df["cp"] == "C", 1.0, -1.0)
    return df[(df["T"] > 0) & (df["open_interest"] > 0)].copy()


def gex_dollars(gamma, open_interest, sign, spot):
    """Dollar delta change per 1% move: sign x gamma x OI x 100 x S x (0.01 x S)."""
    return sign * gamma * open_interest * MULTIPLIER * spot * spot * 0.01


def bs_gamma(S, K, T, sigma):
    """Black-Scholes gamma with r = q (forward = spot), the approximation used for the flip profile."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + 0.5 * sd**2) / sd
    return np.exp(-0.5 * d1**2) / (np.sqrt(2 * np.pi) * S * sd)


def contract_gamma(df: pd.DataFrame, spot: float) -> np.ndarray:
    """Gamma per contract: recomputed from Cboe's IV where it exists, because Cboe rounds gamma
    to 4 decimals (an SPX gamma of 0.000853 is published as 0.0009). Contracts without an IV
    (mostly AM-settled SPX after their last trading day) fall back to Cboe's gamma."""
    has_iv = df["iv"].values > 0
    model = bs_gamma(spot, df["strike"].values, df["T"].values, np.where(has_iv, df["iv"].values, 1.0))
    return np.where(has_iv, model, df["gamma"].values)


def gamma_profile(df: pd.DataFrame, spot: float, lo: float = 0.85, hi: float = 1.15, step: float = 0.0025) -> pd.Series:
    """Total GEX if spot moved to each level on a grid, holding each contract's IV fixed.
    Contracts without an IV can't be repriced, so their GEX is held at its current value."""
    has_iv = df["iv"] > 0
    usable = df[has_iv]
    fixed = df.loc[~has_iv, "gex"].sum()
    K, T, iv, oi, sign = (usable[c].values for c in ("strike", "T", "iv", "open_interest", "sign"))
    levels = spot * np.arange(lo, hi + step / 2, step)
    totals = [gex_dollars(bs_gamma(s, K, T, iv), oi, sign, s).sum() + fixed for s in levels]
    return pd.Series(totals, index=levels)


def zero_crossing(profile: pd.Series, spot: float) -> float | None:
    """Spot level where total GEX changes sign, nearest to the current spot (linear interpolation)."""
    x, y = profile.index.values, profile.values
    crossings = [x[i] - y[i] * (x[i + 1] - x[i]) / (y[i + 1] - y[i]) for i in range(len(y) - 1) if y[i] * y[i + 1] < 0]
    return min(crossings, key=lambda c: abs(c - spot)) if crossings else None


# Each variant is one defensible assumption about which contracts drive dealer hedging.
# Reporting the range and median across them shows how much the headline depends on choices.
SENSITIVITY_VARIANTS = {
    "base (all expiries)": lambda d: pd.Series(True, index=d.index),
    "excl. 0-1 day expiries": lambda d: d["T"] > 1 / 365,         # OI is a day stale for same-day options
    "excl. contracts with no IV": lambda d: d["iv"] > 0,          # only contracts with precise model gamma
    "expiries <= 90 days": lambda d: d["T"] <= 90 / 365,          # near-term hedging only
    "expiries > 7 days": lambda d: d["T"] > 7 / 365,              # ignores the volatile front week
}


def sensitivity(df: pd.DataFrame) -> pd.Series:
    """Total GEX under each variant in SENSITIVITY_VARIANTS."""
    return pd.Series({name: df.loc[keep(df), "gex"].sum() for name, keep in SENSITIVITY_VARIANTS.items()}, name="total_gex")


def squeezemetrics_gex() -> tuple[pd.Timestamp, float]:
    """Latest SqueezeMetrics SPX GEX (dollars per 1% move). An independent method, so it is printed
    next to the sensitivity range as a reference rather than mixed into the median or the verdict."""
    sm = pd.read_csv(SQUEEZEMETRICS_CSV, parse_dates=["date"]).iloc[-1]
    return sm["date"], float(sm["gex"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", default="_SPX", help="Cboe symbol: _SPX, SPY, QQQ, AAPL, ...")
    parser.add_argument("--sample", action="store_true", help="use sample/chain.csv instead of live data")
    args = parser.parse_args()

    if args.sample:
        chain = pd.read_csv(HERE / "sample" / "chain.csv")
        spot, snapshot = float(chain["spot"].iloc[0]), pd.Timestamp(chain["snapshot_utc"].iloc[0], tz="UTC")
        label = "SPX (sample)"
    else:
        chain, spot, snapshot = load_chain(args.symbol)
        label = args.symbol

    df = parse_contracts(chain, snapshot)
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

    sens = sensitivity(df)
    low, high, median = sens.min(), sens.max(), sens.median()
    if low > 0 or high < 0:
        verdict = f"sign is consistent: {'positive' if low > 0 else 'negative'} under every assumption"
    else:
        verdict = "sign is uncertain: the range crosses zero"
    print("Sensitivity of total GEX to assumptions ($ bn per 1% move):")
    print((sens / 1e9).round(2).to_string())
    print(f"Range: ${low / 1e9:,.2f} to ${high / 1e9:,.2f} bn | Median: ${median / 1e9:,.2f} bn | {verdict}")
    if args.symbol == "_SPX" and not args.sample:
        sm_date, sm_gex = squeezemetrics_gex()
        where = "inside" if low <= sm_gex <= high else "outside"
        print(f"Reference: SqueezeMetrics published SPX GEX ({sm_date:%Y-%m-%d}) ${sm_gex / 1e9:,.2f} bn, "
              f"{where} the range above (independent method; not part of the median or verdict)")

    out = HERE / "output"
    out.mkdir(exist_ok=True)
    name = "sample" if args.sample else args.symbol.strip("_")
    by_strike.to_csv(out / f"gex_by_strike_{name}.csv")
    profile.rename("total_gex").rename_axis("spot_level").to_csv(out / f"gex_profile_{name}.csv")
    sens.rename_axis("assumption").to_csv(out / f"gex_sensitivity_{name}.csv")
    print(f"\nWritten: output/gex_by_strike_{name}.csv, output/gex_profile_{name}.csv, output/gex_sensitivity_{name}.csv")


if __name__ == "__main__":
    main()
