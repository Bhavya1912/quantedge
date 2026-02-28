"""
Expected Value Engine — Numerical Integration
==============================================
Computes TRUE EV via lognormal PDF integration,
NOT Monte Carlo approximation.

EV = ∫₀^∞ Payoff(Sᵀ) · f(Sᵀ) dSᵀ

where f(Sᵀ) = lognormal PDF:

f(Sᵀ) = 1/(Sᵀ·σ·√(2πT)) · exp(-(ln(Sᵀ/S₀)-(μ-σ²/2)T)² / (2σ²T))
"""
import numpy as np
from scipy.stats import lognorm
from scipy.integrate import quad
from typing import Callable

from core.payoff import compute_multi_leg_payoff
from utils.config import settings


def lognormal_pdf(
    ST: np.ndarray,
    S0: float,
    mu: float,
    sigma: float,
    T: float,
) -> np.ndarray:
    """
    Lognormal probability density function for terminal price.

    Args:
        ST:    Array of terminal prices
        S0:    Current spot price
        mu:    Expected return (risk-free rate or real-world drift)
        sigma: Volatility (annualized)
        T:     Time to expiry in years

    Returns:
        PDF values at each ST
    """
    # Parameters of the lognormal distribution
    mu_log = np.log(S0) + (mu - 0.5 * sigma ** 2) * T
    sigma_log = sigma * np.sqrt(T)

    # Avoid division by zero
    ST = np.maximum(ST, 1e-10)

    pdf = (1 / (ST * sigma_log * np.sqrt(2 * np.pi))) * np.exp(
        -((np.log(ST) - mu_log) ** 2) / (2 * sigma_log ** 2)
    )
    return pdf


def compute_true_ev(
    legs: list[dict],
    S0: float,
    sigma: float,
    T: float,
    r: float = None,
    n_points: int = None,
) -> dict:
    """
    Compute true Expected Value via lognormal numerical integration.

    Args:
        legs:     Multi-leg strategy definition
                  Each leg: {'K', 'option_type', 'position', 'quantity', 'premium'}
        S0:       Current spot
        sigma:    Implied volatility (annualized)
        T:        Time to expiry in years
        r:        Risk-free rate (defaults to settings)
        n_points: Number of integration points (defaults to settings)

    Returns:
        Dict with EV, variance, downside_deviation, EV_per_max_loss
    """
    r = r or settings.RISK_FREE_RATE
    n_points = n_points or settings.PAYOFF_PRICE_STEPS

    # Integration range: S₀ × [0.5, 1.5] covers 99.9%+ of lognormal mass
    S_min = S0 * 0.40
    S_max = S0 * 1.60

    # Create price grid
    ST_grid = np.linspace(S_min, S_max, n_points)

    # Compute PDF at each price point
    pdf_vals = lognormal_pdf(ST_grid, S0, r, sigma, T)

    # Compute payoff at each price point
    payoffs = np.array([
        compute_multi_leg_payoff(legs, st, include_premium=True)
        for st in ST_grid
    ])

    # Numerical integration: EV = Σ Payoff(Sᵀ) · f(Sᵀ) · ΔS
    dS = ST_grid[1] - ST_grid[0]
    ev = float(np.sum(payoffs * pdf_vals * dS))

    # Variance: E[Payoff²] - E[Payoff]²
    ev_squared = float(np.sum(payoffs ** 2 * pdf_vals * dS))
    variance = ev_squared - ev ** 2
    std_dev = float(np.sqrt(max(variance, 0)))

    # Downside deviation (semi-variance below 0)
    downside_payoffs = np.minimum(payoffs, 0)
    downside_dev = float(np.sqrt(
        max(np.sum(downside_payoffs ** 2 * pdf_vals * dS), 0)
    ))

    # Max loss and max profit from payoff array
    max_loss = float(np.min(payoffs))
    max_profit = float(np.max(payoffs))

    # EV / |Max Loss| — capital efficiency metric
    ev_per_max_loss = ev / abs(max_loss) if max_loss < 0 else float("inf")

    # Probability of profit: mass where payoff > 0
    profit_mask = payoffs > 0
    pop = float(np.sum(pdf_vals[profit_mask] * dS))

    # Sharpe-like: EV / std_dev
    sharpe = ev / std_dev if std_dev > 0 else 0.0

    return {
        "ev": round(ev, 2),
        "std_dev": round(std_dev, 2),
        "variance": round(variance, 2),
        "downside_deviation": round(downside_dev, 2),
        "max_loss": round(max_loss, 2),
        "max_profit": round(max_profit, 2),
        "ev_per_max_loss": round(ev_per_max_loss, 4),
        "pop": round(min(pop, 1.0), 4),      # cap at 1.0 for numerical errors
        "sharpe": round(sharpe, 4),
        "payoff_curve": {
            "prices": ST_grid[::10].tolist(),   # downsample for API response
            "payoffs": payoffs[::10].tolist(),
            "pdf": pdf_vals[::10].tolist(),
        },
    }


def compute_probability_of_touch(
    S0: float,
    barrier: float,
    sigma: float,
    T: float,
    r: float = None,
    n_steps: int = 252,
) -> float:
    """
    Probability that price TOUCHES barrier at any point before expiry.
    Uses reflection principle for continuous barrier.

    P(touch) = N((-ln(H/S₀) + μ·T) / (σ·√T))
             + exp(2μ·ln(H/S₀)/σ²) · N((-ln(H/S₀) - μ·T) / (σ·√T))
    """
    r = r or settings.RISK_FREE_RATE
    mu = r - 0.5 * sigma ** 2
    sqrt_T = np.sqrt(T)
    h = np.log(barrier / S0)

    from scipy.stats import norm
    d_plus = (-h + mu * T) / (sigma * sqrt_T)
    d_minus = (-h - mu * T) / (sigma * sqrt_T)

    pot = norm.cdf(d_plus) + np.exp(2 * mu * h / sigma ** 2) * norm.cdf(d_minus)
    return float(min(pot, 1.0))


def compute_pop_exact(
    S0: float,
    breakeven: float,
    sigma: float,
    T: float,
    r: float = None,
    direction: str = "above",
) -> float:
    """
    Exact POP using lognormal CDF.

    P(Sᵀ > BE) = 1 - Φ((ln(BE/S₀) - (μ - σ²/2)·T) / (σ·√T))

    Args:
        direction: 'above' for calls/bull spreads, 'below' for puts/bear spreads
    """
    r = r or settings.RISK_FREE_RATE
    from scipy.stats import norm

    mu = r - 0.5 * sigma ** 2
    sqrt_T = np.sqrt(T)

    z = (np.log(breakeven / S0) - mu * T) / (sigma * sqrt_T)

    if direction == "above":
        return float(1 - norm.cdf(z))
    else:
        return float(norm.cdf(z))
