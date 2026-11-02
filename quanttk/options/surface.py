"""Price a parsed options chain: rates, put-call-parity forwards, implied vol and Greeks per contract.

Shared by the Greeks, volatility and volume workflows.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quanttk.pricing.black_scholes import bsm_greeks, implied_vol
from quanttk.pricing.forwards import implied_forwards
from quanttk.sources.treasury import continuous_rate


def price_chain(df: pd.DataFrame, spot: float, curve: pd.Series) -> pd.DataFrame:
    """Add r, F, q, my_iv and my_<greek> columns to a parsed, filtered chain.

    - r: continuous risk-free rate at each contract's T, from the Treasury par curve
    - F: forward implied by put-call parity per (root, expiry); expiries without a
      two-sided call/put pair are dropped
    - q: carry (dividend) yield implied by the forward, q = r - ln(F/S) / T
    - my_iv: Black-76 implied volatility from the bid/ask mid
    - my_delta ... my_rho: BSM Greeks with that q (see quanttk.pricing.black_scholes)
    """
    df = df.copy()
    df["r"] = continuous_rate(curve, df["T"].values)
    df = df.merge(implied_forwards(df)[["root", "expiry", "F"]], on=["root", "expiry"], how="inner")
    df["q"] = df["r"] - np.log(df["F"] / spot) / df["T"]
    is_call = (df["cp"] == "C").values
    df["my_iv"] = implied_vol(df["mid"].values, *(df[c].values for c in ("F", "strike", "T", "r")), is_call)
    greeks = bsm_greeks(spot, df["strike"].values, df["T"].values, df["r"].values, df["q"].values,
                        df["my_iv"].values, is_call)
    for name, values in greeks.items():
        df[f"my_{name}"] = values
    return df


def tradable(df: pd.DataFrame, max_days: float) -> pd.DataFrame:
    """Unexpired contracts within max_days with a two-sided market (bid > 0, ask > bid)."""
    keep = (df["T"] > 0) & (df["T"] <= max_days / 365) & (df["bid"] > 0) & (df["ask"] > df["bid"])
    return df[keep].copy()
