"""Gamma exposure, volume, volatility surface and the VIX replication formula."""

import numpy as np
import pandas as pd
import pytest

from quanttk.options import gex, volatility, volume
from quanttk.pricing.black_scholes import black76_price, bsm_greeks


def test_gex_profile_at_spot_equals_total():
    spot = 5000.0
    df = pd.DataFrame({"strike": [4900.0, 5000.0, 5100.0, 5000.0], "T": [0.1, 0.1, 0.2, 0.05],
                       "iv": [0.2, 0.18, 0.17, 0.0], "gamma": [0.0, 0.0, 0.0, 0.001],
                       "open_interest": [1000, 2000, 1500, 500], "sign": [-1.0, 1.0, 1.0, -1.0]})
    df["gex"] = gex.gex_dollars(gex.contract_gamma(df, spot), df["open_interest"], df["sign"], spot)
    profile = gex.gamma_profile(df, spot, lo=0.99, hi=1.01, step=0.01)
    at_spot = np.interp(spot, profile.index.values, profile.values)
    assert at_spot == pytest.approx(df["gex"].sum(), rel=1e-9)


def test_zero_crossing_and_range_summary():
    profile = pd.Series([-2.0, -1.0, 1.0, 2.0], index=[90.0, 95.0, 100.0, 105.0])
    assert gex.zero_crossing(profile, 99.0) == pytest.approx(97.5)
    assert gex.summarize_range(pd.Series([-3.0, -1.0, -2.0]))["verdict"].startswith("sign is consistent: negative")
    assert gex.summarize_range(pd.Series([-3.0, 1.0, -2.0]))["median"] == -2.0


def _chain():
    return pd.DataFrame({
        "option": ["A", "B", "C", "D"], "expiry": ["e1", "e1", "e2", "e2"], "cp": ["C", "P", "C", "P"],
        "strike": [100.0, 100.0, 110.0, 90.0], "volume": [100, 150, 0, 50], "open_interest": [1000, 500, 200, 0],
    })


def test_put_call_ratios():
    s = volume.put_call_summary(_chain())
    assert s["pc_volume"] == pytest.approx(200 / 100)
    assert s["pc_open_interest"] == pytest.approx(500 / 1200)
    by = volume.put_call_by_expiry(_chain())
    assert by.loc["e1", "pc_volume"] == pytest.approx(1.5)
    assert np.isnan(by.loc["e2", "pc_volume"])  # zero call volume -> undefined, not infinity


def test_unusual_activity_and_oi_change():
    hot = volume.unusual_activity(_chain(), min_volume=50, min_ratio=0.2)
    assert set(hot["option"]) == {"B", "D"}     # 150/500 = 0.3; D is new (OI 0) -> infinite ratio
    prev = pd.DataFrame({"option": ["A", "B"], "open_interest": [900, 600]})
    ch = volume.oi_change(_chain(), prev).set_index("option")["oi_change"]
    assert ch.to_dict() == {"A": 100, "B": -100, "C": 200, "D": 0}


def _flat_vol_chain(F=5000.0, sigma=0.2, r=0.04, days=(25, 32)):
    """A synthetic SPX chain priced with one flat volatility, for testing the VIX formula."""
    rows = []
    for d in days:
        T = d / 365
        for k in np.arange(2500, 7501, 5.0):
            for cp, is_call in (("C", True), ("P", False)):
                mid = float(black76_price(F, k, T, r, sigma, is_call))
                bid = max(mid - 0.05, 0.0) if mid > 0.05 else 0.0
                rows.append({"root": "SPXW", "expiry": f"exp{d}", "strike": k, "cp": cp, "T": T,
                             "bid": bid, "ask": mid + 0.05, "mid": mid})
    return pd.DataFrame(rows)


def test_vix_replica_recovers_flat_volatility():
    out = volatility.vix_replica(_flat_vol_chain(), lambda T: 0.04)
    assert out["vix"] == pytest.approx(20.0, abs=0.3)  # strike truncation costs a little variance


def test_term_structure_and_skew_on_flat_surface():
    df = _flat_vol_chain(days=(20, 40))
    df = df[(df["strike"] > 4000) & (df["strike"] < 6000) & (df["bid"] > 0)].copy()
    df["F"], df["r"], df["q"], df["my_iv"] = 5000.0, 0.04, 0.0, 0.2
    is_call = (df["cp"] == "C").values
    df["my_delta"] = bsm_greeks(5000.0 * np.exp(-0.04 * df["T"].values), df["strike"].values, df["T"].values,
                                0.0, 0.0, 0.2, is_call)["delta"]
    ts = volatility.term_structure(df)
    assert ts["atm_iv"].tolist() == pytest.approx([0.2, 0.2])
    assert ts["forward_vol"].iloc[1] == pytest.approx(0.2)
    sk = volatility.skew(df)
    assert sk["risk_reversal"].abs().max() < 1e-12 and sk["butterfly"].abs().max() < 1e-12


def test_realized_vol_of_constant_returns_is_zero_and_scales():
    closes = pd.Series(100 * np.exp(np.cumsum([0.01] * 70)))
    assert volatility.realized_vol(closes)["21d"] == pytest.approx(0.0, abs=1e-12)
    alt = pd.Series(100 * np.exp(np.cumsum([0.01, -0.01] * 35)))
    # last 10 returns are five +1% and five -1%: mean 0, sample stdev 0.01 * sqrt(10 / 9)
    assert volatility.realized_vol(alt)["10d"] == pytest.approx(0.01 * np.sqrt(10 / 9) * np.sqrt(252), rel=1e-9)


def test_snapshot_lake_finds_the_previous_market_day(tmp_path, monkeypatch):
    pytest.importorskip("pyarrow")
    from quanttk.sources import snapshots

    monkeypatch.setenv("QUANTTK_LAKE", str(tmp_path))
    chain = pd.DataFrame({"option": ["SPY261120C00700000"], "open_interest": [100]})
    day1 = pd.Timestamp("2026-10-23 00:05", tz="UTC")   # 20:05 ET on Oct 22, after the close
    day2 = pd.Timestamp("2026-10-23 21:00", tz="UTC")   # 17:00 ET on Oct 23
    path = snapshots.save_snapshot(chain, 700.0, day1, "SPY")
    assert path.parent.name == "date=2026-10-22"         # filed under the market date, not the UTC date
    assert snapshots.latest_snapshot_before("SPY", day1) is None
    found, ts = snapshots.latest_snapshot_before("SPY", day2)
    assert ts == day1 and found["open_interest"].tolist() == [100]
