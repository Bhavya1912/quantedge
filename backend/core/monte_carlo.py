"""
Monte Carlo Engine — Vectorized GBM
=====================================
Uses Box-Muller transform for proper N(0,1) Gaussian sampling.
NOT the broken approximation: Math.random() + Math.random() + ...

GBM: dS = μS·dt + σS·dW
Discrete: Sᵢ₊₁ = Sᵢ · exp((μ - σ²/2)·dt + σ·√dt·Z)
          where Z ~ N(0,1) via Box-Muller
"""
import numpy as np
from typing import Optional
from utils.config import settings


def box_muller_normal(n: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate n standard normal samples using Box-Muller transform.

    Algorithm:
        U₁, U₂ ~ Uniform(0, 1)
        Z₁ = √(-2·ln(U₁)) · cos(2π·U₂)   ~ N(0,1)
        Z₂ = √(-2·ln(U₁)) · sin(2π·U₂)   ~ N(0,1)

    This is mathematically exact, unlike CLT approximations.
    """
    rng = np.random.default_rng(seed)
    # Generate pairs (n+1 to handle odd n)
    m = (n + 1) // 2
    U1 = rng.uniform(0, 1, m)
    U2 = rng.uniform(0, 1, m)

    # Avoid log(0)
    U1 = np.maximum(U1, 1e-15)

    mag = np.sqrt(-2.0 * np.log(U1))
    Z1 = mag * np.cos(2 * np.pi * U2)
    Z2 = mag * np.sin(2 * np.pi * U2)

    result = np.concatenate([Z1, Z2])[:n]
    return result


def simulate_gbm_paths(
    S0: float,
    mu: float,
    sigma: float,
    T: float,
    n_simulations: int = None,
    n_steps: int = 1,
    seed: Optional[int] = None,
    antithetic: bool = True,
) -> np.ndarray:
    """
    Simulate GBM paths using vectorized NumPy operations.

    Args:
        S0:            Initial spot price
        mu:            Drift (use risk-free rate for risk-neutral pricing)
        sigma:         Volatility (annualized)
        T:             Time horizon in years
        n_simulations: Number of Monte Carlo paths
        n_steps:       Number of time steps per path (1 = single-step)
        seed:          Random seed for reproducibility
        antithetic:    Use antithetic variates for variance reduction

    Returns:
        Shape (n_simulations, n_steps+1) array of price paths
        or shape (n_simulations,) terminal prices if n_steps=1
    """
    n_simulations = n_simulations or settings.MONTE_CARLO_SIMULATIONS
    dt = T / n_steps
    drift = (mu - 0.5 * sigma ** 2) * dt
    vol_sqrt_dt = sigma * np.sqrt(dt)

    rng = np.random.default_rng(seed)

    if antithetic:
        # Generate half the paths, mirror for variance reduction
        half_n = n_simulations // 2
        Z_half = rng.standard_normal((half_n, n_steps))
        Z = np.concatenate([Z_half, -Z_half], axis=0)
    else:
        Z = rng.standard_normal((n_simulations, n_steps))

    # Compute log returns for each step
    log_returns = drift + vol_sqrt_dt * Z  # Shape: (n_sims, n_steps)

    # Cumulative sum to get log path
    log_paths = np.cumsum(log_returns, axis=1)  # Shape: (n_sims, n_steps)

    # Convert to price paths
    paths = S0 * np.exp(log_paths)  # Shape: (n_sims, n_steps)

    # Add initial price column
    initial = np.full((n_simulations, 1), S0)
    full_paths = np.concatenate([initial, paths], axis=1)  # (n_sims, n_steps+1)

    return full_paths


def run_monte_carlo(
    legs: list[dict],
    S0: float,
    sigma: float,
    T: float,
    r: float = None,
    n_simulations: int = None,
    n_steps: int = 1,
    seed: int = 42,
    lot_size: int = 15,
) -> dict:
    """
    Full Monte Carlo simulation for a multi-leg strategy.

    Args:
        legs:          Strategy legs (see payoff.py)
        S0:            Current spot
        sigma:         Implied volatility
        T:             Time to expiry (years)
        r:             Risk-free rate
        n_simulations: Number of paths
        n_steps:       Time steps (1 for expiry-only, 252+ for path-dependent)
        seed:          Reproducibility seed
        lot_size:      Lot size (15 for Bank Nifty)

    Returns:
        Dict with EV, win_rate, distribution, VaR, CVaR, Sharpe, paths
    """
    from core.payoff import compute_multi_leg_payoff

    r = r or settings.RISK_FREE_RATE
    n_simulations = n_simulations or settings.MONTE_CARLO_SIMULATIONS

    # Simulate terminal prices
    paths = simulate_gbm_paths(
        S0=S0, mu=r, sigma=sigma, T=T,
        n_simulations=n_simulations, n_steps=n_steps,
        seed=seed, antithetic=True,
    )

    terminal_prices = paths[:, -1]

    # Compute payoff for each simulation
    payoffs = np.array([
        compute_multi_leg_payoff(legs, st, include_premium=True, lot_size=lot_size)
        for st in terminal_prices
    ])

    # ── Statistics ──────────────────────────────────────────────────────────
    ev = float(np.mean(payoffs))
    std_dev = float(np.std(payoffs))
    win_rate = float(np.mean(payoffs > 0))

    # Value at Risk (95th percentile loss)
    var_95 = float(np.percentile(payoffs, 5))
    var_99 = float(np.percentile(payoffs, 1))

    # Conditional VaR (Expected Shortfall)
    cvar_95 = float(np.mean(payoffs[payoffs <= var_95]))

    # Sharpe ratio (EV / std)
    sharpe = ev / std_dev if std_dev > 0 else 0.0

    # Downside deviation
    neg_payoffs = payoffs[payoffs < 0]
    downside_dev = float(np.std(neg_payoffs)) if len(neg_payoffs) > 0 else 0.0

    # Sortino ratio
    sortino = ev / downside_dev if downside_dev > 0 else 0.0

    # ── Distribution histogram for frontend ─────────────────────────────────
    n_bins = 50
    min_p, max_p = float(np.min(payoffs)), float(np.max(payoffs))
    hist, bin_edges = np.histogram(payoffs, bins=n_bins)

    histogram = [
        {
            "bin_low": float(bin_edges[i]),
            "bin_high": float(bin_edges[i + 1]),
            "count": int(hist[i]),
            "frequency": float(hist[i] / n_simulations),
            "is_profit": float(bin_edges[i]) >= 0,
        }
        for i in range(n_bins)
    ]

    # ── Sample paths for visualization (50 paths) ───────────────────────────
    n_viz_paths = min(50, n_simulations)
    viz_step = max(1, n_simulations // n_viz_paths)
    sample_paths = paths[::viz_step][:n_viz_paths]

    # ── Percentile bands ────────────────────────────────────────────────────
    p10 = paths[np.argsort(terminal_prices)[int(0.10 * n_simulations)]]
    p25 = paths[np.argsort(terminal_prices)[int(0.25 * n_simulations)]]
    p50 = paths[np.argsort(terminal_prices)[int(0.50 * n_simulations)]]
    p75 = paths[np.argsort(terminal_prices)[int(0.75 * n_simulations)]]
    p90 = paths[np.argsort(terminal_prices)[int(0.90 * n_simulations)]]

    return {
        "n_simulations": n_simulations,
        "ev": round(ev, 2),
        "std_dev": round(std_dev, 2),
        "win_rate": round(win_rate, 4),
        "max_profit": round(float(np.max(payoffs)), 2),
        "max_loss": round(float(np.min(payoffs)), 2),
        "var_95": round(var_95, 2),
        "var_99": round(var_99, 2),
        "cvar_95": round(cvar_95, 2),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "downside_deviation": round(downside_dev, 2),
        "histogram": histogram,
        "sample_paths": {
            "prices": sample_paths.tolist(),
            "p10": p10.tolist(),
            "p25": p25.tolist(),
            "p50": p50.tolist(),
            "p75": p75.tolist(),
            "p90": p90.tolist(),
        },
        "terminal_prices": {
            "p5":  round(float(np.percentile(terminal_prices, 5)), 2),
            "p25": round(float(np.percentile(terminal_prices, 25)), 2),
            "p50": round(float(np.percentile(terminal_prices, 50)), 2),
            "p75": round(float(np.percentile(terminal_prices, 75)), 2),
            "p95": round(float(np.percentile(terminal_prices, 95)), 2),
        },
    }
