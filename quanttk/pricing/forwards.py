"""Forward prices implied by put-call parity.

Method: Cboe Volatility Index Mathematics Methodology,
https://cdn.cboe.com/api/global/us_indices/governance/Cboe_Volatility_Index_Mathematics_Methodology.pdf
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def implied_forwards(df: pd.DataFrame) -> pd.DataFrame:
    """Per (root, expiry): F = K* + e^{rT} (C - P) at the strike K* where |C - P| is smallest.

    `df` needs root, expiry, strike, cp, bid, ask, mid, T and r. Only two-sided quotes
    (bid > 0, ask > bid) are candidates; ties go to the lowest strike, as in the Cboe method.
    Returns columns root, expiry, F, K_star.
    """
    legs = df[(df["bid"] > 0) & (df["ask"] > df["bid"])]
    pairs = legs.pivot_table(index=["root", "expiry", "strike"], columns="cp", values="mid").dropna()
    pairs["diff"] = (pairs["C"] - pairs["P"]).abs()
    best = pairs.loc[pairs.groupby(level=["root", "expiry"])["diff"].idxmin()].reset_index()
    meta = df.groupby(["root", "expiry"])[["T", "r"]].first().reset_index()
    best = best.merge(meta, on=["root", "expiry"])
    best["F"] = best["strike"] + np.exp(best["r"] * best["T"]) * (best["C"] - best["P"])
    return best.rename(columns={"strike": "K_star"})[["root", "expiry", "F", "K_star"]]
