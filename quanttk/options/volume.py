"""Options volume and open interest: put/call ratios, unusual activity, concentration and OI change.

Put/call ratio definitions follow Cboe's published market statistics
(https://www.cboe.com/us/options/market_statistics/): put volume / call volume, and the
same for open interest.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _ratio(num, den):
    return num / den if den else np.nan


def put_call_summary(df: pd.DataFrame) -> pd.Series:
    """Total call/put volume and open interest, and the two put/call ratios."""
    calls, puts = df[df["cp"] == "C"], df[df["cp"] == "P"]
    return pd.Series({
        "call_volume": calls["volume"].sum(), "put_volume": puts["volume"].sum(),
        "call_oi": calls["open_interest"].sum(), "put_oi": puts["open_interest"].sum(),
        "pc_volume": _ratio(puts["volume"].sum(), calls["volume"].sum()),
        "pc_open_interest": _ratio(puts["open_interest"].sum(), calls["open_interest"].sum()),
    })


def put_call_by_expiry(df: pd.DataFrame) -> pd.DataFrame:
    """Put/call volume and open-interest ratios for each expiry."""
    piv = df.pivot_table(index="expiry", columns="cp", values=["volume", "open_interest"], aggfunc="sum", fill_value=0)
    out = pd.DataFrame(index=piv.index)
    for field, name in (("volume", "volume"), ("open_interest", "oi")):
        c = piv.get((field, "C"), pd.Series(0, index=piv.index))
        p = piv.get((field, "P"), pd.Series(0, index=piv.index))
        out[f"call_{name}"], out[f"put_{name}"] = c, p
        out[f"pc_{name}"] = (p / c.replace(0, np.nan))
    return out


def unusual_activity(df: pd.DataFrame, min_volume: int = 1000, min_ratio: float = 1.0, top: int = 15) -> pd.DataFrame:
    """Contracts where today's volume is large and exceeds open interest (volume / OI >= min_ratio).

    Volume above the prior day's open interest means at least some of it is new positioning,
    not just existing holders trading. A screen, not a signal: it can't tell buyers from sellers.
    """
    d = df[(df["volume"] >= min_volume)].copy()
    d["vol_oi_ratio"] = d["volume"] / d["open_interest"].replace(0, np.nan)
    d.loc[d["open_interest"] == 0, "vol_oi_ratio"] = np.inf
    d = d[d["vol_oi_ratio"] >= min_ratio]
    return d.sort_values("volume", ascending=False).head(top)


def oi_concentration(df: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Strikes with the most open interest, summed across expiries, split by calls and puts."""
    piv = df.pivot_table(index="strike", columns="cp", values="open_interest", aggfunc="sum", fill_value=0)
    piv = piv.reindex(columns=["C", "P"], fill_value=0).rename(columns={"C": "call_oi", "P": "put_oi"})
    piv["total_oi"] = piv["call_oi"] + piv["put_oi"]
    piv["share_of_total"] = piv["total_oi"] / piv["total_oi"].sum()
    return piv.sort_values("total_oi", ascending=False).head(top)


def oi_change(today: pd.DataFrame, previous: pd.DataFrame) -> pd.DataFrame:
    """Change in open interest per contract versus an earlier snapshot (matched on the option symbol).

    Contracts new since the earlier snapshot count from zero; contracts that disappeared
    (expired) are left out.
    """
    prev = previous[["option", "open_interest"]].rename(columns={"open_interest": "previous_oi"})
    d = today.merge(prev, on="option", how="left")
    d["previous_oi"] = d["previous_oi"].fillna(0)
    d["oi_change"] = d["open_interest"] - d["previous_oi"]
    return d
