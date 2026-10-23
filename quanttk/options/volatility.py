"""Implied volatility term structure, smile and skew, realized volatility, and VIX replication.

References:
    Cboe Volatility Index Mathematics Methodology,
    https://cdn.cboe.com/api/global/us_indices/governance/Cboe_Volatility_Index_Mathematics_Methodology.pdf
    Hull, J. C., Options, Futures, and Other Derivatives, 11th ed. (2021), "Volatility Smiles".
    Sinclair, E., Volatility Trading, 2nd ed. (2013), ch. 2 (realized volatility estimators).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MINUTES_PER_YEAR = 525_600
TRADING_DAYS = 252


def otm_smile(df: pd.DataFrame) -> pd.DataFrame:
    """Out-of-the-money options only (puts with K < F, calls with K >= F), with valid IVs.

    OTM quotes are the liquid side of the market; ITM IVs are noisier and carry the same
    information via put-call parity. Adds log-moneyness k = ln(K / F).
    """
    otm = ((df["cp"] == "P") & (df["strike"] < df["F"])) | ((df["cp"] == "C") & (df["strike"] >= df["F"]))
    s = df[otm & df["my_iv"].notna()].copy()
    s["log_moneyness"] = np.log(s["strike"] / s["F"])
    return s.sort_values(["root", "expiry", "strike"])


def _interp(x_target: float, x: np.ndarray, y: np.ndarray) -> float:
    """Linear interpolation inside the data range only (NaN outside, no extrapolation)."""
    order = np.argsort(x)
    x, y = x[order], y[order]
    if len(x) < 2 or x_target < x[0] or x_target > x[-1]:
        return np.nan
    return float(np.interp(x_target, x, y))


def term_structure(df: pd.DataFrame) -> pd.DataFrame:
    """Per expiry: days, forward, ATM IV (interpolated at K = F across OTM strikes),
    and forward volatility between consecutive expiries:
        sigma_fwd^2 = (sigma_2^2 T_2 - sigma_1^2 T_1) / (T_2 - T_1)  (Hull, variance additivity).
    """
    smile = otm_smile(df)
    rows = []
    for (root, expiry), g in smile.groupby(["root", "expiry"]):
        F, T = g["F"].iloc[0], g["T"].iloc[0]
        rows.append({"root": root, "expiry": expiry, "days": T * 365, "T": T, "forward": F,
                     "atm_iv": _interp(F, g["strike"].values, g["my_iv"].values)})
    ts = pd.DataFrame(rows).dropna(subset=["atm_iv"]).sort_values("T").reset_index(drop=True)
    var = ts["atm_iv"] ** 2 * ts["T"]
    fwd_var = (var - var.shift(1)) / (ts["T"] - ts["T"].shift(1))
    ts["forward_vol"] = np.sqrt(fwd_var.where(fwd_var > 0))
    return ts


def skew(df: pd.DataFrame, delta: float = 0.25) -> pd.DataFrame:
    """Per expiry: ATM IV, IV at the +delta call and -delta put, and
        risk reversal RR = IV(call, +delta) - IV(put, -delta)
        butterfly     BF = (IV(call, +delta) + IV(put, -delta)) / 2 - ATM IV
    IVs at a given delta are interpolated linearly in delta across OTM options.
    Negative RR means puts are richer than calls (the usual equity-index skew)."""
    smile = otm_smile(df)
    rows = []
    for (root, expiry), g in smile.groupby(["root", "expiry"]):
        calls, puts = g[g["cp"] == "C"], g[g["cp"] == "P"]
        F = g["F"].iloc[0]
        c = _interp(delta, calls["my_delta"].values, calls["my_iv"].values)
        p = _interp(-delta, puts["my_delta"].values, puts["my_iv"].values)
        atm = _interp(F, g["strike"].values, g["my_iv"].values)
        rows.append({"root": root, "expiry": expiry, "days": g["T"].iloc[0] * 365, "atm_iv": atm,
                     f"call_{int(delta * 100)}d_iv": c, f"put_{int(delta * 100)}d_iv": p,
                     "risk_reversal": c - p, "butterfly": (c + p) / 2 - atm})
    return pd.DataFrame(rows).sort_values("days").reset_index(drop=True)


def realized_vol(closes: pd.Series, windows=(10, 21, 63)) -> pd.Series:
    """Annualized close-to-close realized volatility over the last N trading days:
        sigma = sqrt(252) * stdev(ln(P_t / P_{t-1}))   (sample stdev, ddof = 1)."""
    rets = np.log(closes / closes.shift(1)).dropna()
    return pd.Series({f"{w}d": rets.tail(w).std(ddof=1) * np.sqrt(TRADING_DAYS) for w in windows if len(rets) >= w})


# ---------------------------------------------------------------- VIX replication

def _single_term_variance(g: pd.DataFrame, r: float) -> dict:
    """Cboe single-term variance for one expiry (steps 1-2 of the methodology)."""
    T = g["T"].iloc[0]
    quotes = g.pivot_table(index="strike", columns="cp", values=["bid", "ask", "mid"])
    both = quotes.dropna()
    two_sided = both[(both[("bid", "C")] > 0) & (both[("bid", "P")] > 0)]
    diff = (two_sided[("mid", "C")] - two_sided[("mid", "P")]).abs()
    k_star = diff.idxmin()  # ties resolve to the lowest strike
    F = k_star + np.exp(r * T) * (two_sided.loc[k_star, ("mid", "C")] - two_sided.loc[k_star, ("mid", "P")])
    strikes = quotes.index.values
    k0 = strikes[strikes <= F].max()

    selected = {}  # strike -> Q(K)
    for side, ordered in (("P", sorted(strikes[strikes < k0], reverse=True)), ("C", sorted(strikes[strikes > k0]))):
        zero_run = 0
        for k in ordered:
            bid = quotes.loc[k, ("bid", side)]
            if not bid > 0:  # zero or missing bid
                zero_run += 1
                if zero_run == 2:  # two consecutive zero bids end the strip
                    break
                continue
            zero_run = 0
            selected[k] = quotes.loc[k, ("mid", side)]
    selected[k0] = (quotes.loc[k0, ("mid", "P")] + quotes.loc[k0, ("mid", "C")]) / 2

    ks = np.array(sorted(selected))
    q = np.array([selected[k] for k in ks])
    dk = np.empty_like(ks)
    dk[1:-1] = (ks[2:] - ks[:-2]) / 2
    dk[0], dk[-1] = ks[1] - ks[0], ks[-1] - ks[-2]
    sigma2 = (2 / T) * np.sum(dk / ks**2 * np.exp(r * T) * q) - (1 / T) * (F / k0 - 1) ** 2
    return {"T": T, "minutes": T * MINUTES_PER_YEAR, "F": F, "K0": k0, "strikes_used": len(ks), "sigma2": sigma2}


def vix_replica(df: pd.DataFrame, r_of_T, target_days: int = 30, window=(23, 37)) -> dict:
    """Replicate the VIX from a parsed SPX chain (Cboe methodology).

    Near- and next-term expiries are the two closest expiries that bracket `target_days`
    within `window` days. When both SPX (AM) and SPXW (PM) list the same date, the
    standard SPX series is used. `r_of_T` maps T (years) to a continuous risk-free rate.

        VIX = 100 * sqrt( [T1 s1^2 (N2 - N30)/(N2 - N1) + T2 s2^2 (N30 - N1)/(N2 - N1)] * N365 / N30 )
    """
    days = df["T"] * 365
    cands = df[(days > window[0]) & (days < window[1])]
    per_date = cands.groupby("expiry")["root"].apply(lambda s: "SPX" if "SPX" in set(s) else sorted(set(s))[0])
    terms = []
    for expiry, root in per_date.items():
        g = cands[(cands["expiry"] == expiry) & (cands["root"] == root)]
        terms.append({"expiry": expiry, "root": root, **_single_term_variance(g, float(r_of_T(g["T"].iloc[0])))})
    terms = sorted(terms, key=lambda t: t["T"])
    target = target_days * 1440
    below = [t for t in terms if t["minutes"] <= target]
    above = [t for t in terms if t["minutes"] > target]
    if below and above:
        near, nxt = below[-1], above[0]
    elif len(terms) >= 2:  # both on one side: Cboe extrapolates with the same weights
        near, nxt = terms[0], terms[1]
    else:
        raise ValueError(f"need two expiries between {window[0]} and {window[1]} days; found {len(terms)}")
    n1, n2 = near["minutes"], nxt["minutes"]
    w1, w2 = (n2 - target) / (n2 - n1), (target - n1) / (n2 - n1)
    var30 = (near["T"] * near["sigma2"] * w1 + nxt["T"] * nxt["sigma2"] * w2) * MINUTES_PER_YEAR / target
    return {"vix": 100 * np.sqrt(var30), "near": near, "next": nxt}
