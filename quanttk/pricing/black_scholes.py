"""Black-Scholes-Merton and Black (1976) pricing, implied volatility and Greeks.

References:
    Black, F. and Scholes, M. (1973), JPE 81(3), 637-654.
    Merton, R. C. (1973), Bell Journal of Economics and Management Science 4(1), 141-183.
    Black, F. (1976), Journal of Financial Economics 3, 167-179.
    Hull, J. C., Options, Futures, and Other Derivatives, 11th ed. (2021), "The Greek Letters".

All functions are vectorised over NumPy arrays. `is_call` is a boolean array (or scalar).
"""

from __future__ import annotations

import numpy as np
from scipy.special import ndtr  # standard normal CDF


def norm_pdf(x):
    return np.exp(-0.5 * np.asarray(x) ** 2) / np.sqrt(2 * np.pi)


def bsm_price(S, K, T, r, q, sigma, is_call):
    """Black-Scholes-Merton price with continuous dividend yield q."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / sd
    d2 = d1 - sd
    call = S * np.exp(-q * T) * ndtr(d1) - K * np.exp(-r * T) * ndtr(d2)
    put = K * np.exp(-r * T) * ndtr(-d2) - S * np.exp(-q * T) * ndtr(-d1)
    return np.where(is_call, call, put)


def black76_price(F, K, T, r, sigma, is_call):
    """Discounted Black (1976) price on the forward; identical to BSM with q implied by F."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * sd**2) / sd
    d2 = d1 - sd
    call = np.exp(-r * T) * (F * ndtr(d1) - K * ndtr(d2))
    put = np.exp(-r * T) * (K * ndtr(-d2) - F * ndtr(-d1))
    return np.where(is_call, call, put)


def implied_vol(price, F, K, T, r, is_call, lo=1e-3, hi=5.0, iterations=100):
    """Black-76 implied volatility by vectorised bisection (prices rise monotonically in sigma).

    Returns NaN where the price is at or below intrinsic value or at or above the
    no-arbitrage upper bound, since no volatility reproduces it.
    """
    price = np.asarray(price, dtype=float)
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
    """BSM Greeks with continuous dividend yield q (Hull, "The Greek Letters").

    Units: delta per $1 of spot, gamma per $1 per $1, vega per 1 vol point, theta per
    calendar day, rho per 1 percentage point of rates. `theta_decay` is the time-decay
    term alone (no rate or dividend carry), which is what Cboe publishes as theta.
    """
    sd = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / sd
    d2 = d1 - sd
    pdf = norm_pdf(d1)
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


def bs_gamma(S, K, T, sigma):
    """Black-Scholes gamma with r = q = 0 (forward = spot, no discounting), used for gamma-exposure profiles.

    Equals bsm_greeks(...)["gamma"] with r = q = 0. With a dividend yield q the exact BSM gamma
    carries an extra factor e^{-qT} (about 0.1% smaller for SPX at one month), which this
    approximation ignores."""
    sd = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + 0.5 * sd**2) / sd
    return np.exp(-0.5 * d1**2) / (np.sqrt(2 * np.pi) * S * sd)
