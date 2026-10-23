"""Dealer gamma exposure (GEX).

Convention: SqueezeMetrics, "Gamma Exposure (GEX)" white paper,
https://squeezemetrics.com/download/white_paper.pdf. Dealers are assumed long calls and
short puts, so call gamma counts positive and put gamma negative.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from quanttk.pricing.black_scholes import bs_gamma
from quanttk.sources.cboe import parse_contracts

MULTIPLIER = 100  # shares per contract for US equity and index options
SQUEEZEMETRICS_CSV = "https://squeezemetrics.com/monitor/static/DIX.csv"


def gex_contracts(chain: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """Parsed, unexpired contracts with open interest, plus the dealer sign (+1 call, -1 put)."""
    df = parse_contracts(chain, snapshot)
    df["sign"] = np.where(df["cp"] == "C", 1.0, -1.0)
    return df[(df["T"] > 0) & (df["open_interest"] > 0)].copy()


def gex_dollars(gamma, open_interest, sign, spot):
    """Dollar delta change per 1% move: sign x gamma x OI x 100 x S x (0.01 x S)."""
    return sign * gamma * open_interest * MULTIPLIER * spot * spot * 0.01


def contract_gamma(df: pd.DataFrame, spot: float) -> np.ndarray:
    """Gamma per contract: recomputed from Cboe's IV where it exists, because Cboe rounds gamma
    to 4 decimals (an SPX gamma of 0.000853 is published as 0.0009). Contracts without an IV
    (mostly AM-settled SPX after their last trading day) fall back to Cboe's gamma."""
    has_iv = df["iv"].values > 0
    model = bs_gamma(spot, df["strike"].values, df["T"].values, np.where(has_iv, df["iv"].values, 1.0))
    return np.where(has_iv, model, df["gamma"].values)


def gamma_profile(df: pd.DataFrame, spot: float, lo: float = 0.85, hi: float = 1.15, step: float = 0.0025) -> pd.Series:
    """Total GEX if spot moved to each level on a grid, holding each contract's IV fixed.
    Contracts without an IV can't be repriced, so their GEX is held at its current value.
    `df` needs a `gex` column (current GEX per contract)."""
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
SENSITIVITY_VARIANTS: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "base (all expiries)": lambda d: pd.Series(True, index=d.index),
    "excl. 0-1 day expiries": lambda d: d["T"] > 1 / 365,         # OI is a day stale for same-day options
    "excl. contracts with no IV": lambda d: d["iv"] > 0,          # only contracts with precise model gamma
    "expiries <= 90 days": lambda d: d["T"] <= 90 / 365,          # near-term hedging only
    "expiries > 7 days": lambda d: d["T"] > 7 / 365,              # ignores the volatile front week
}


def sensitivity(df: pd.DataFrame, include_squeezemetrics: bool) -> pd.Series:
    """Total GEX under each variant, plus SqueezeMetrics' published SPX GEX when requested."""
    totals = {name: df.loc[keep(df), "gex"].sum() for name, keep in SENSITIVITY_VARIANTS.items()}
    if include_squeezemetrics:
        sm = pd.read_csv(SQUEEZEMETRICS_CSV, parse_dates=["date"]).iloc[-1]
        totals[f"SqueezeMetrics published ({sm['date']:%Y-%m-%d})"] = float(sm["gex"])
    return pd.Series(totals, name="total_gex")


def summarize_range(values: pd.Series) -> dict:
    """Range, median and a sign verdict for a set of estimates."""
    low, high = values.min(), values.max()
    if low > 0 or high < 0:
        verdict = f"sign is consistent: {'positive' if low > 0 else 'negative'} under every assumption"
    else:
        verdict = "sign is uncertain: the range crosses zero"
    return {"low": low, "high": high, "median": values.median(), "verdict": verdict}
