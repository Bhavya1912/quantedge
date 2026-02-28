"""
Multi-Leg Payoff Calculator
============================
Computes payoff at expiry for 1–4 leg option strategies.
Supports: calls, puts, long, short positions.
"""
import numpy as np
from typing import List


def option_payoff_at_expiry(
    ST: float,
    K: float,
    option_type: str,
    position: str,
    quantity: int = 1,
) -> float:
    """
    Payoff of a single option leg at expiry.

    Args:
        ST:          Terminal spot price
        K:           Strike price
        option_type: 'call' | 'put'
        position:    'long' | 'short'
        quantity:    Number of lots

    Returns:
        Payoff (₹ per unit, before premium)
    """
    if option_type == "call":
        intrinsic = max(ST - K, 0.0)
    elif option_type == "put":
        intrinsic = max(K - ST, 0.0)
    else:
        raise ValueError(f"Unknown option_type: {option_type}")

    sign = 1 if position == "long" else -1
    return float(sign * intrinsic * quantity)


def compute_multi_leg_payoff(
    legs: list[dict],
    ST: float,
    include_premium: bool = True,
    lot_size: int = 15,
) -> float:
    """
    Net payoff of a multi-leg strategy at expiry.

    Args:
        legs: List of leg dicts:
              {
                'K':           strike price,
                'option_type': 'call' | 'put',
                'position':    'long' | 'short',
                'quantity':    number of lots,
                'premium':     premium paid/received per unit
              }
        ST:             Terminal spot price
        include_premium: Include net premium in P&L
        lot_size:        Units per lot (default 15 for Bank Nifty)

    Returns:
        Net P&L in ₹ for 1 lot
    """
    total_payoff = 0.0
    net_premium = 0.0

    for leg in legs:
        K = leg["K"]
        opt_type = leg["option_type"]
        position = leg["position"]
        qty = leg.get("quantity", 1)
        premium = leg.get("premium", 0.0)

        # Payoff at expiry (per unit, not per lot yet)
        payoff = option_payoff_at_expiry(ST, K, opt_type, position, qty)
        total_payoff += payoff

        # Net premium (long pays, short receives)
        if position == "long":
            net_premium -= premium * qty
        else:
            net_premium += premium * qty

    if include_premium:
        return (total_payoff + net_premium) * lot_size
    else:
        return total_payoff * lot_size


def compute_payoff_curve(
    legs: list[dict],
    S0: float,
    price_range_pct: float = 0.10,
    n_points: int = 200,
    lot_size: int = 15,
) -> dict:
    """
    Compute full payoff curve across a range of terminal prices.

    Returns:
        Dict with 'prices', 'payoffs', 'breakevens', 'max_profit', 'max_loss'
    """
    S_min = S0 * (1 - price_range_pct)
    S_max = S0 * (1 + price_range_pct)
    prices = np.linspace(S_min, S_max, n_points)

    payoffs = np.array([
        compute_multi_leg_payoff(legs, st, include_premium=True, lot_size=lot_size)
        for st in prices
    ])

    # Find breakeven points (sign changes)
    breakevens = []
    for i in range(len(payoffs) - 1):
        if payoffs[i] * payoffs[i + 1] <= 0:
            # Linear interpolation for exact breakeven
            be = prices[i] + (0 - payoffs[i]) * (prices[i + 1] - prices[i]) / (payoffs[i + 1] - payoffs[i])
            breakevens.append(round(be, 2))

    return {
        "prices": prices.tolist(),
        "payoffs": payoffs.tolist(),
        "breakevens": breakevens,
        "max_profit": float(np.max(payoffs)),
        "max_loss": float(np.min(payoffs)),
        "current_price_idx": int(len(prices) // 2),
    }


def net_premium_collected(legs: list[dict]) -> float:
    """Total net premium for the strategy (positive = credit received)."""
    net = 0.0
    for leg in legs:
        premium = leg.get("premium", 0.0)
        qty = leg.get("quantity", 1)
        if leg["position"] == "short":
            net += premium * qty
        else:
            net -= premium * qty
    return net


def margin_required(legs: list[dict], lot_size: int = 15) -> dict:
    """
    Estimate SPAN margin for the strategy.
    Note: For production use, this should call broker's margin API.
    This is an approximation based on max loss.
    """
    # Simple approximation: SPAN ≈ 70% of max loss, Exposure ≈ 30%
    dummy_payoffs = [
        compute_multi_leg_payoff(legs, s, include_premium=True, lot_size=lot_size)
        for s in np.linspace(0.8 * legs[0]["K"], 1.2 * legs[0]["K"], 100)
    ]
    max_loss = abs(min(dummy_payoffs))
    span = round(max_loss * 0.70)
    exposure = round(max_loss * 0.30)
    total = span + exposure
    return {
        "span": span,
        "exposure": exposure,
        "total": total,
    }
