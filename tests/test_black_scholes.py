"""Pricing checks against published textbook values and model identities."""

import numpy as np
import pytest

from quanttk.pricing.black_scholes import black76_price, bs_gamma, bsm_greeks, bsm_price, implied_vol


def test_hull_textbook_example():
    # Hull, Options, Futures, and Other Derivatives: S=42, K=40, r=10%, sigma=20%, T=0.5 -> c=4.76, p=0.81
    c = bsm_price(42.0, 40.0, 0.5, 0.10, 0.0, 0.20, True)
    p = bsm_price(42.0, 40.0, 0.5, 0.10, 0.0, 0.20, False)
    assert round(float(c), 2) == 4.76
    assert round(float(p), 2) == 0.81


def test_put_call_parity():
    S, K, T, r, q, sigma = 100.0, 95.0, 0.75, 0.04, 0.015, 0.3
    c = bsm_price(S, K, T, r, q, sigma, True)
    p = bsm_price(S, K, T, r, q, sigma, False)
    assert c - p == pytest.approx(S * np.exp(-q * T) - K * np.exp(-r * T), rel=1e-12)


def test_black76_equals_bsm_with_forward():
    S, K, T, r, q, sigma = 100.0, 110.0, 0.4, 0.05, 0.02, 0.25
    F = S * np.exp((r - q) * T)
    for is_call in (True, False):
        assert black76_price(F, K, T, r, sigma, is_call) == pytest.approx(bsm_price(S, K, T, r, q, sigma, is_call), rel=1e-12)


def test_implied_vol_round_trip_and_bounds():
    F, T, r = 100.0, 0.25, 0.04
    K = np.array([80.0, 95.0, 100.0, 105.0, 130.0])
    sig = np.array([0.35, 0.22, 0.2, 0.19, 0.3])
    is_call = np.array([False, False, True, True, True])
    prices = black76_price(F, K, T, r, sig, is_call)
    assert implied_vol(prices, F, K, T, r, is_call) == pytest.approx(sig, abs=1e-8)
    # below intrinsic and above the upper bound have no implied vol
    bad = implied_vol(np.array([0.0, 200.0]), F, np.array([90.0, 90.0]), T, r, np.array([True, True]))
    assert np.isnan(bad).all()


@pytest.mark.parametrize("is_call", [True, False])
def test_greeks_match_finite_differences(is_call):
    S, K, T, r, q, sigma = 100.0, 102.0, 0.5, 0.03, 0.01, 0.25
    g = bsm_greeks(S, K, T, r, q, sigma, is_call)
    price = lambda **kw: float(bsm_price(**{**dict(S=S, K=K, T=T, r=r, q=q, sigma=sigma, is_call=is_call), **kw}))  # noqa: E731
    h = 1e-3
    assert g["delta"] == pytest.approx((price(S=S + h) - price(S=S - h)) / (2 * h), rel=1e-5)
    assert g["gamma"] == pytest.approx((price(S=S + h) - 2 * price() + price(S=S - h)) / h**2, rel=1e-3)
    assert g["vega"] == pytest.approx((price(sigma=sigma + 1e-4) - price(sigma=sigma - 1e-4)) / 2e-4 / 100, rel=1e-5)
    assert g["rho"] == pytest.approx((price(r=r + 1e-5) - price(r=r - 1e-5)) / 2e-5 / 100, rel=1e-4)
    dt = 1 / 365
    assert g["theta"] == pytest.approx(price(T=T - dt) - price(), rel=1e-2)  # one calendar day of decay


def test_bs_gamma_is_bsm_gamma_with_zero_rates():
    g0 = bsm_greeks(100.0, 105.0, 0.3, 0.0, 0.0, 0.22, True)["gamma"]
    assert bs_gamma(100.0, 105.0, 0.3, 0.22) == pytest.approx(float(g0), rel=1e-12)
    # with r = q != 0 the exact gamma carries an extra e^{-qT}; the approximation ignores it
    gq = bsm_greeks(100.0, 105.0, 0.3, 0.02, 0.02, 0.22, True)["gamma"]
    assert float(gq) == pytest.approx(float(g0) * np.exp(-0.02 * 0.3), rel=1e-12)
