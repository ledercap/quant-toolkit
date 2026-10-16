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
import time
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
from scipy.special import ndtr  # standard normal CDF

HERE = Path(__file__).parent
ET = ZoneInfo("America/New_York")
SECONDS_PER_YEAR = 365.0 * 24 * 3600
# SPX (not SPXW) options are AM-settled: they stop trading the day before and settle
# at the open of expiry day. Everything else in Cboe's feed is treated as PM-settled.
AM_SETTLED_ROOTS = {"SPX"}
TREASURY_CSV = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
)


# ---------------------------------------------------------------- data loading

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
    chain = pd.DataFrame(raw["data"]["options"])
    return chain, float(raw["data"]["current_price"]), pd.Timestamp(raw["timestamp"], tz="UTC")


def load_yield_curve(on: date) -> pd.Series:
    """Latest published par yield curve on or before `on`, as decimal yields indexed by tenor in years."""
    for year in (on.year, on.year - 1):  # early January may have no rows yet for the new year
        curve = pd.read_csv(TREASURY_CSV.format(year=year), parse_dates=["Date"])
        curve = curve[curve["Date"].dt.date <= on]
        if not curve.empty:
            break
    row = curve.sort_values("Date").iloc[-1].drop("Date").dropna()
    years = [float(c.split()[0]) / (12 if ("Mo" in c or "Month" in c) else 1) for c in row.index]
    return pd.Series(row.values.astype(float) / 100, index=years).sort_index()


def parse_contracts(chain: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """Split OCC symbols (e.g. SPXW261120C07700000) and compute time to expiry in years."""
    parts = chain["option"].str.extract(r"^(?P<root>[A-Z]+)(?P<ymd>\d{6})(?P<cp>[CP])(?P<k>\d{8})$")
    df = chain.join(parts)
    df["strike"] = df["k"].astype(int) / 1000
    expiry_day = pd.to_datetime(df["ymd"], format="%y%m%d")
    settle_hour = np.where(df["root"].isin(AM_SETTLED_ROOTS), 9.5, 16.0)
    expiry_et = expiry_day + pd.to_timedelta(settle_hour, unit="h")
    df["expiry"] = expiry_day.dt.date
    df["expiry_utc"] = expiry_et.dt.tz_localize(ET).dt.tz_convert("UTC")
    df["T"] = (df["expiry_utc"] - snapshot).dt.total_seconds() / SECONDS_PER_YEAR
    df["mid"] = (df["bid"] + df["ask"]) / 2
    return df


# ---------------------------------------------------------------- the model

def continuous_rate(curve: pd.Series, T: np.ndarray) -> np.ndarray:
    """Interpolate par yields linearly in maturity, then convert from semiannual bond-equivalent
    to continuous compounding: r = 2 ln(1 + y/2)."""
    y = np.interp(T, curve.index.values, curve.values)  # flat beyond the shortest and longest tenors
    return 2 * np.log1p(y / 2)


def implied_forwards(df: pd.DataFrame) -> pd.DataFrame:
    """Per (root, expiry): F = K* + e^{rT} (C - P) at the strike K* where |C - P| is smallest."""
    legs = df[(df["bid"] > 0) & (df["ask"] > df["bid"])]
    pairs = legs.pivot_table(index=["root", "expiry", "strike"], columns="cp", values="mid").dropna()
    pairs["diff"] = (pairs["C"] - pairs["P"]).abs()
    best = pairs.loc[pairs.groupby(level=["root", "expiry"])["diff"].idxmin()].reset_index()
    meta = df.groupby(["root", "expiry"])[["T", "r"]].first().reset_index()
    best = best.merge(meta, on=["root", "expiry"])
    best["F"] = best["strike"] + np.exp(best["r"] * best["T"]) * (best["C"] - best["P"])
    return best[["root", "expiry", "F"]]


def black76_price(F, K, T, r, sigma, is_call):
    """Discounted Black (1976) price on the forward; identical to BSM with q implied by F."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sd**2) / sd
    d2 = d1 - sd
    call = np.exp(-r * T) * (F * ndtr(d1) - K * ndtr(d2))
    put = np.exp(-r * T) * (K * ndtr(-d2) - F * ndtr(-d1))
    return np.where(is_call, call, put)


def implied_vol(price, F, K, T, r, is_call, lo=1e-3, hi=5.0, iterations=100):
    """Vectorised bisection: option prices rise monotonically with volatility."""
    disc = np.exp(-r * T)
    intrinsic = disc * np.where(is_call, np.maximum(F - K, 0), np.maximum(K - F, 0))
    upper = disc * np.where(is_call, F, K)
    valid = (price > intrinsic) & (price < upper)
    lo_v, hi_v = np.full_like(price, lo), np.full_like(price, hi)
    for _ in range(iterations):
        mid_v = 0.5 * (lo_v + hi_v)
        too_high = black76_price(F, K, T, r, mid_v, is_call) > price
        hi_v = np.where(too_high, mid_v, hi_v)
        lo_v = np.where(too_high, lo_v, mid_v)
    return np.where(valid, 0.5 * (lo_v + hi_v), np.nan)


def bsm_greeks(S, K, T, r, q, sigma, is_call) -> dict[str, np.ndarray]:
    """BSM Greeks with continuous dividend yield q (Hull, ch. 19). Units:
    delta per $1 of spot, gamma per $1 per $1, vega per 1 vol point, theta per calendar day,
    rho per 1 percentage point of rates. theta_decay is the time-decay term alone (no rate or
    dividend carry), which is what Cboe publishes as theta."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / sd
    d2 = d1 - sd
    pdf = np.exp(-0.5 * d1**2) / np.sqrt(2 * np.pi)
    eq, er = np.exp(-q * T), np.exp(-r * T)
    delta = np.where(is_call, eq * ndtr(d1), eq * (ndtr(d1) - 1))
    gamma = eq * pdf / (S * sd)
    vega = S * eq * pdf * np.sqrt(T) / 100
    decay = -S * eq * pdf * sigma / (2 * np.sqrt(T))
    theta_call = decay - r * K * er * ndtr(d2) + q * S * eq * ndtr(d1)
    theta_put = decay + r * K * er * ndtr(-d2) - q * S * eq * ndtr(-d1)
    theta = np.where(is_call, theta_call, theta_put) / 365
    rho = np.where(is_call, K * T * er * ndtr(d2), -K * T * er * ndtr(-d2)) / 100
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "theta_decay": decay / 365, "rho": rho}


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
        chain = pd.read_csv(HERE / "sample" / "chain.csv")
        spot, snapshot = float(chain["spot"].iloc[0]), pd.Timestamp(chain["snapshot_utc"].iloc[0], tz="UTC")
        curve_df = pd.read_csv(HERE / "sample" / "yield_curve.csv")
        curve = pd.Series(curve_df["yield"].values, index=curve_df["tenor_years"].values)
        label = f"{chain['option'].str.extract(r'^([A-Z]+)')[0].iloc[0]} (sample)"
    else:
        chain, spot, snapshot = load_chain(args.symbol)
        curve = load_yield_curve(snapshot.tz_convert(ET).date())
        label = args.symbol

    df = parse_contracts(chain, snapshot)
    df = df[(df["T"] > 0) & (df["T"] <= args.max_days / 365) & (df["bid"] > 0) & (df["ask"] > df["bid"])].copy()
    df["r"] = continuous_rate(curve, df["T"].values)
    df = df.merge(implied_forwards(df), on=["root", "expiry"], how="inner")
    df["q"] = df["r"] - np.log(df["F"] / spot) / df["T"]  # dividend yield implied by the forward

    is_call = (df["cp"] == "C").values
    args_np = [df[c].values for c in ("F", "strike", "T", "r")]
    df["my_iv"] = implied_vol(df["mid"].values, *args_np, is_call)
    greeks = bsm_greeks(spot, df["strike"].values, df["T"].values, df["r"].values, df["q"].values, df["my_iv"].values, is_call)
    for name, values in greeks.items():
        df[f"my_{name}"] = values

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
