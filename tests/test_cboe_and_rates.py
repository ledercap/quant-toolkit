"""Contract parsing, settlement times, rates and put-call-parity forwards."""

import numpy as np
import pandas as pd
import pytest

from quanttk.pricing.black_scholes import black76_price
from quanttk.pricing.forwards import implied_forwards
from quanttk.sources.cboe import parse_contracts
from quanttk.sources.treasury import continuous_rate


def _chain(symbols):
    return pd.DataFrame({"option": symbols, "bid": 1.0, "ask": 1.2})


def test_occ_symbol_parsing():
    df = parse_contracts(_chain(["SPXW261120C07700000", "SPY261016P00550500"]), pd.Timestamp("2026-10-15 20:00", tz="UTC"))
    assert list(df["root"]) == ["SPXW", "SPY"]
    assert list(df["cp"]) == ["C", "P"]
    assert list(df["strike"]) == [7700.0, 550.5]
    assert df["mid"].tolist() == [1.1, 1.1]


def test_am_settled_spx_expires_at_the_open():
    snap = pd.Timestamp("2026-10-15 20:00", tz="UTC")  # 16:00 ET the day before expiry
    df = parse_contracts(_chain(["SPX261016C07700000", "SPXW261016C07700000"]), snap)
    hours = (df["T"] * 365 * 24).round(2).tolist()
    assert hours == [17.5, 24.0]  # 09:30 ET vs 16:00 ET next day


def test_continuous_rate_conversion_and_flat_extrapolation():
    curve = pd.Series([0.04, 0.05], index=[0.5, 2.0])
    r = continuous_rate(curve, np.array([0.1, 1.25, 10.0]))
    assert r[0] == pytest.approx(2 * np.log(1 + 0.04 / 2))
    assert r[1] == pytest.approx(2 * np.log(1 + 0.045 / 2))
    assert r[2] == pytest.approx(2 * np.log(1 + 0.05 / 2))


def test_implied_forward_recovers_true_forward():
    F_true, T, r, sigma = 5000.0, 30 / 365, 0.04, 0.18
    strikes = np.arange(4800, 5201, 25.0)
    rows = []
    for k in strikes:
        for cp, is_call in (("C", True), ("P", False)):
            mid = float(black76_price(F_true, k, T, r, sigma, is_call))
            rows.append({"root": "SPXW", "expiry": "2026-11-14", "strike": k, "cp": cp,
                         "bid": mid - 0.05, "ask": mid + 0.05, "mid": mid, "T": T, "r": r})
    out = implied_forwards(pd.DataFrame(rows))
    assert out["F"].iloc[0] == pytest.approx(F_true, rel=1e-9)
    assert out["K_star"].iloc[0] == 5000.0
