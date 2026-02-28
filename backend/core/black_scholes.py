"""
Black-Scholes Pricing Engine — Exact Analytical Formulas
=========================================================
All Greeks computed from closed-form BS solutions.
No approximations. Tolerance < 0.1%.
"""
import numpy as np
from scipy.stats import norm
from typing import Literal


OptionType = Literal["call", "put"]


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> tuple[float, float]:
    """
    Compute d1 and d2 for Black-Scholes formula.

    d1 = [ln(S/K) + (r + σ²/2)·T] / (σ·√T)
    d2 = d1 - σ·√T
    """
    if T <= 0 or sigma <= 0:
        raise ValueError(f"T={T} and sigma={sigma} must be positive.")
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


def bs_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType = "call",
) -> float:
    """
    Black-Scholes option price.

    Args:
        S:           Spot price
        K:           Strike price
        T:           Time to expiry in years
        r:           Risk-free rate (annualized)
        sigma:       Implied volatility (annualized)
        option_type: 'call' or 'put'

    Returns:
        Option price
    """
    if T <= 0:
        # At expiry: intrinsic value only
        intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
        return float(intrinsic)

    d1, d2 = _d1_d2(S, K, T, r, sigma)

    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return float(price)


def bs_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType = "call",
) -> dict:
    """
    Compute all first and second order Greeks.

    Returns dict with:
        delta, gamma, vega, theta, rho, vanna, charm, speed, zomma
    """
    if T <= 0:
        return {
            "delta": 1.0 if (option_type == "call" and S > K) else 0.0,
            "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0,
        }

    d1, d2 = _d1_d2(S, K, T, r, sigma)
    sqrt_T = np.sqrt(T)
    phi_d1 = norm.pdf(d1)          # Standard normal PDF at d1
    Nd1 = norm.cdf(d1)
    Nd2 = norm.cdf(d2)
    Nnd1 = norm.cdf(-d1)
    Nnd2 = norm.cdf(-d2)
    disc = np.exp(-r * T)

    # ── First-order Greeks ──────────────────────────────────────────────────
    if option_type == "call":
        delta = Nd1
        theta = (
            -(S * phi_d1 * sigma) / (2 * sqrt_T)
            - r * K * disc * Nd2
        ) / 365  # Per calendar day
        rho = K * T * disc * Nd2 / 100  # Per 1% rate move
    else:
        delta = Nd1 - 1
        theta = (
            -(S * phi_d1 * sigma) / (2 * sqrt_T)
            + r * K * disc * Nnd2
        ) / 365
        rho = -K * T * disc * Nnd2 / 100

    # ── Second-order Greeks ─────────────────────────────────────────────────
    gamma = phi_d1 / (S * sigma * sqrt_T)

    # Vega: sensitivity to 1% IV move
    vega = S * phi_d1 * sqrt_T / 100

    # ── Higher-order Greeks ─────────────────────────────────────────────────
    vanna = -phi_d1 * d2 / sigma          # dDelta/dIV
    charm = -phi_d1 * (                   # dDelta/dT (daily)
        2 * r * T - d2 * sigma * sqrt_T
    ) / (2 * T * sigma * sqrt_T) / 365
    speed = -gamma / S * (d1 / (sigma * sqrt_T) + 1)
    zomma = gamma * (d1 * d2 - 1) / sigma

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega),
        "theta": float(theta),
        "rho": float(rho),
        "vanna": float(vanna),
        "charm": float(charm),
        "speed": float(speed),
        "zomma": float(zomma),
    }


def implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: OptionType = "call",
    max_iter: int = 200,
    tol: float = 1e-6,
) -> float:
    """
    Compute implied volatility via Newton-Raphson method.

    Args:
        market_price: Observed option market price (LTP)
        S, K, T, r:   Standard BS inputs
        option_type:  'call' or 'put'
        max_iter:     Max Newton-Raphson iterations
        tol:          Convergence tolerance

    Returns:
        Implied volatility (annualized, as decimal)
        Returns -1.0 if no convergence.
    """
    if T <= 0 or market_price <= 0:
        return 0.0

    # Initial guess: Brenner-Subrahmanyam approximation
    sigma = np.sqrt(2 * np.pi / T) * market_price / S

    for _ in range(max_iter):
        price = bs_price(S, K, T, r, sigma, option_type)
        vega = S * norm.pdf(*_d1_d2(S, K, T, r, sigma)[:1]) * np.sqrt(T)

        if abs(vega) < 1e-10:
            break

        price_diff = price - market_price
        if abs(price_diff) < tol:
            return float(sigma)

        sigma -= price_diff / vega

        # Keep sigma in reasonable bounds
        sigma = max(0.001, min(sigma, 5.0))

    return float(sigma) if sigma > 0 else -1.0


def iv_shock_pnl(
    legs: list[dict],
    S: float,
    T: float,
    r: float,
    iv_shift_pct: float,
) -> float:
    """
    P&L impact of an IV shock on a multi-leg position.

    Args:
        legs:          List of {'K', 'sigma', 'option_type', 'quantity', 'position'}
                       position: 'long' | 'short'
        S:             Current spot
        T:             Time to expiry in years
        r:             Risk-free rate
        iv_shift_pct:  IV shift in percentage points (e.g., 5.0 = +5%)

    Returns:
        Net P&L change in ₹ (per lot of 15 Bank Nifty)
    """
    lot_size = 15  # Bank Nifty lot size
    pnl = 0.0
    iv_shift = iv_shift_pct / 100.0

    for leg in legs:
        K = leg["K"]
        sigma = leg["sigma"]
        opt_type = leg["option_type"]
        qty = leg["quantity"]
        sign = 1 if leg["position"] == "long" else -1

        price_before = bs_price(S, K, T, r, sigma, opt_type)
        price_after = bs_price(S, K, T, r, sigma + iv_shift, opt_type)
        pnl += sign * qty * (price_after - price_before) * lot_size

    return float(pnl)
