"""
Strategy Generator & Risk-Constrained Optimizer
================================================
Programmatically generates strategy combinations
from option chain data and ranks them by EV/Sharpe.

Objective: max(EV / |MaxLoss|) or max(EV / Margin)
Subject to:
  - Max Loss ≤ capital × risk_threshold
  - Margin   ≤ available_capital
"""
import logging
from typing import List, Dict, Any, Optional
from itertools import product as cartesian_product

import numpy as np

from core.ev_engine import compute_true_ev, compute_pop_exact
from core.payoff import compute_payoff_curve, net_premium_collected, margin_required
from core.black_scholes import bs_greeks
from utils.config import settings

logger = logging.getLogger(__name__)


# ── Risk thresholds by risk appetite ────────────────────────────────────────
RISK_THRESHOLDS = {
    "conservative": 0.05,   # Max loss ≤ 5% of capital
    "moderate":     0.10,   # Max loss ≤ 10% of capital
    "aggressive":   0.20,   # Max loss ≤ 20% of capital
}

# ── Strategy definitions (leg templates) ────────────────────────────────────
# Each strategy is a function that takes (chain, atm_idx) and returns leg dicts

def build_bull_call_spread(chain: list, atm_idx: int, width: int = 1) -> Optional[dict]:
    """Buy ATM call, sell OTM call (width strikes away)."""
    if atm_idx + width >= len(chain):
        return None
    long_call = chain[atm_idx]
    short_call = chain[atm_idx + width]
    return {
        "name": f"Bull Call Spread +{width}",
        "type": "bull_call_spread",
        "legs": [
            {"K": long_call["strike"], "option_type": "call", "position": "long",
             "quantity": 1, "premium": long_call["call_ask"], "sigma": long_call["call_iv"] / 100},
            {"K": short_call["strike"], "option_type": "call", "position": "short",
             "quantity": 1, "premium": short_call["call_bid"], "sigma": short_call["call_iv"] / 100},
        ],
    }


def build_bear_put_spread(chain: list, atm_idx: int, width: int = 1) -> Optional[dict]:
    """Buy ATM put, sell OTM put (width strikes away)."""
    if atm_idx - width < 0:
        return None
    long_put = chain[atm_idx]
    short_put = chain[atm_idx - width]
    return {
        "name": f"Bear Put Spread -{width}",
        "type": "bear_put_spread",
        "legs": [
            {"K": long_put["strike"], "option_type": "put", "position": "long",
             "quantity": 1, "premium": long_put["put_ask"], "sigma": long_put["put_iv"] / 100},
            {"K": short_put["strike"], "option_type": "put", "position": "short",
             "quantity": 1, "premium": short_put["put_bid"], "sigma": short_put["put_iv"] / 100},
        ],
    }


def build_short_put(chain: list, atm_idx: int, otm_offset: int = 1) -> Optional[dict]:
    """Sell OTM put."""
    idx = atm_idx - otm_offset
    if idx < 0:
        return None
    put = chain[idx]
    return {
        "name": f"Short Put (OTM-{otm_offset})",
        "type": "short_put",
        "legs": [
            {"K": put["strike"], "option_type": "put", "position": "short",
             "quantity": 1, "premium": put["put_bid"], "sigma": put["put_iv"] / 100},
        ],
    }


def build_short_call_spread(chain: list, atm_idx: int, width: int = 1) -> Optional[dict]:
    """Short bear call spread: sell OTM call, buy further OTM call."""
    if atm_idx + width + 1 >= len(chain):
        return None
    short_call = chain[atm_idx + 1]
    long_call = chain[atm_idx + width + 1]
    return {
        "name": f"Short Call Spread +{width}",
        "type": "short_call_spread",
        "legs": [
            {"K": short_call["strike"], "option_type": "call", "position": "short",
             "quantity": 1, "premium": short_call["call_bid"], "sigma": short_call["call_iv"] / 100},
            {"K": long_call["strike"], "option_type": "call", "position": "long",
             "quantity": 1, "premium": long_call["call_ask"], "sigma": long_call["call_iv"] / 100},
        ],
    }


def build_long_call(chain: list, atm_idx: int, otm_offset: int = 0) -> Optional[dict]:
    """Buy call (ATM or OTM)."""
    idx = atm_idx + otm_offset
    if idx >= len(chain):
        return None
    call = chain[idx]
    return {
        "name": f"Long Call {'ATM' if otm_offset == 0 else f'OTM+{otm_offset}'}",
        "type": "long_call",
        "legs": [
            {"K": call["strike"], "option_type": "call", "position": "long",
             "quantity": 1, "premium": call["call_ask"], "sigma": call["call_iv"] / 100},
        ],
    }


def build_long_put(chain: list, atm_idx: int, otm_offset: int = 0) -> Optional[dict]:
    """Buy put (ATM or OTM)."""
    idx = atm_idx - otm_offset
    if idx < 0:
        return None
    put = chain[idx]
    return {
        "name": f"Long Put {'ATM' if otm_offset == 0 else f'OTM-{otm_offset}'}",
        "type": "long_put",
        "legs": [
            {"K": put["strike"], "option_type": "put", "position": "long",
             "quantity": 1, "premium": put["put_ask"], "sigma": put["put_iv"] / 100},
        ],
    }


def build_iron_condor(chain: list, atm_idx: int, wing: int = 2) -> Optional[dict]:
    """Iron condor: short strangle with protective wings."""
    if atm_idx - wing < 0 or atm_idx + wing + 1 >= len(chain):
        return None
    short_put = chain[atm_idx - 1]
    long_put = chain[atm_idx - wing]
    short_call = chain[atm_idx + 1]
    long_call = chain[atm_idx + wing]
    return {
        "name": f"Iron Condor (±{wing})",
        "type": "iron_condor",
        "legs": [
            {"K": long_put["strike"],  "option_type": "put",  "position": "long",
             "quantity": 1, "premium": long_put["put_ask"],  "sigma": long_put["put_iv"] / 100},
            {"K": short_put["strike"], "option_type": "put",  "position": "short",
             "quantity": 1, "premium": short_put["put_bid"], "sigma": short_put["put_iv"] / 100},
            {"K": short_call["strike"],"option_type": "call", "position": "short",
             "quantity": 1, "premium": short_call["call_bid"],"sigma": short_call["call_iv"] / 100},
            {"K": long_call["strike"], "option_type": "call", "position": "long",
             "quantity": 1, "premium": long_call["call_ask"],"sigma": long_call["call_iv"] / 100},
        ],
    }


def build_short_straddle(chain: list, atm_idx: int) -> Optional[dict]:
    """Sell ATM call and put."""
    atm = chain[atm_idx]
    return {
        "name": "Short Straddle (ATM)",
        "type": "short_straddle",
        "legs": [
            {"K": atm["strike"], "option_type": "call", "position": "short",
             "quantity": 1, "premium": atm["call_bid"], "sigma": atm["call_iv"] / 100},
            {"K": atm["strike"], "option_type": "put",  "position": "short",
             "quantity": 1, "premium": atm["put_bid"],  "sigma": atm["put_iv"] / 100},
        ],
    }


def build_butterfly(chain: list, atm_idx: int, wing: int = 1) -> Optional[dict]:
    """Long butterfly: buy 2 ATM calls, sell 1 OTM and 1 ITM."""
    if atm_idx - wing < 0 or atm_idx + wing >= len(chain):
        return None
    itm = chain[atm_idx - wing]
    atm = chain[atm_idx]
    otm = chain[atm_idx + wing]
    return {
        "name": f"Long Butterfly (±{wing})",
        "type": "butterfly",
        "legs": [
            {"K": itm["strike"], "option_type": "call", "position": "long",
             "quantity": 1, "premium": itm["call_ask"], "sigma": itm["call_iv"] / 100},
            {"K": atm["strike"], "option_type": "call", "position": "short",
             "quantity": 2, "premium": atm["call_bid"], "sigma": atm["call_iv"] / 100},
            {"K": otm["strike"], "option_type": "call", "position": "long",
             "quantity": 1, "premium": otm["call_ask"], "sigma": otm["call_iv"] / 100},
        ],
    }


# ── Strategy universe by market view ────────────────────────────────────────
STRATEGY_BUILDERS = {
    "bullish": [
        (build_bull_call_spread, {"width": 1}),
        (build_bull_call_spread, {"width": 2}),
        (build_bull_call_spread, {"width": 3}),
        (build_short_put, {"otm_offset": 1}),
        (build_short_put, {"otm_offset": 2}),
        (build_long_call, {"otm_offset": 0}),
        (build_long_call, {"otm_offset": 1}),
    ],
    "bearish": [
        (build_bear_put_spread, {"width": 1}),
        (build_bear_put_spread, {"width": 2}),
        (build_short_call_spread, {"width": 1}),
        (build_short_call_spread, {"width": 2}),
        (build_long_put, {"otm_offset": 0}),
        (build_long_put, {"otm_offset": 1}),
    ],
    "neutral": [
        (build_iron_condor, {"wing": 2}),
        (build_iron_condor, {"wing": 3}),
        (build_short_straddle, {}),
        (build_butterfly, {"wing": 1}),
        (build_butterfly, {"wing": 2}),
    ],
}


def generate_strategy_universe(
    chain: list,
    spot: float,
    market_view: str,
) -> list[dict]:
    """
    Generate all candidate strategies for a given market view.

    Args:
        chain:       Option chain rows (sorted by strike)
        spot:        Current spot price
        market_view: 'bullish' | 'bearish' | 'neutral'

    Returns:
        List of strategy dicts with name, type, legs
    """
    # Find ATM index
    strikes = [row["strike"] for row in chain]
    atm_idx = int(np.argmin(np.abs(np.array(strikes) - spot)))

    builders = STRATEGY_BUILDERS.get(market_view.lower(), [])
    strategies = []

    for builder_fn, kwargs in builders:
        try:
            strat = builder_fn(chain, atm_idx, **kwargs)
            if strat is not None:
                strategies.append(strat)
        except Exception as e:
            logger.warning(f"Strategy builder {builder_fn.__name__} failed: {e}")

    logger.info(f"Generated {len(strategies)} candidate strategies for {market_view} view.")
    return strategies


def rank_strategies(
    strategies: list[dict],
    spot: float,
    sigma: float,
    T: float,
    r: float,
    capital: float,
    risk_appetite: str = "moderate",
    lot_size: int = 15,
    top_n: int = 3,
) -> list[dict]:
    """
    Score and rank all strategies by EV / |MaxLoss|,
    filtered by risk constraints.

    Args:
        strategies:    Candidate strategies from generate_strategy_universe
        spot:          Current spot
        sigma:         ATM implied volatility
        T:             Time to expiry (years)
        r:             Risk-free rate
        capital:       User's available capital
        risk_appetite: 'conservative' | 'moderate' | 'aggressive'
        lot_size:      Lot size
        top_n:         Return top N strategies

    Returns:
        Top N ranked strategy dicts with full analytics
    """
    max_loss_pct = RISK_THRESHOLDS.get(risk_appetite, 0.10)
    max_loss_allowed = capital * max_loss_pct

    scored = []

    for strat in strategies:
        try:
            legs = strat["legs"]

            # Compute EV via numerical integration
            ev_result = compute_true_ev(
                legs=legs, S0=spot, sigma=sigma, T=T, r=r
            )

            max_loss = ev_result["max_loss"]
            ev = ev_result["ev"]

            # Risk filter
            if abs(max_loss) > max_loss_allowed:
                logger.debug(
                    f"Filtered {strat['name']}: max_loss={max_loss:.0f} > limit={max_loss_allowed:.0f}"
                )
                continue

            # Margin check
            margin = margin_required(legs, lot_size)
            if margin["total"] > capital:
                logger.debug(f"Filtered {strat['name']}: margin > capital")
                continue

            # Payoff curve
            payoff_curve = compute_payoff_curve(
                legs, spot, price_range_pct=0.08, n_points=100, lot_size=lot_size
            )

            # Greeks at ATM (use first leg's strike and sigma as proxy)
            atm_leg = legs[0]
            atm_greeks = bs_greeks(
                S=spot, K=atm_leg["K"], T=T, r=r,
                sigma=atm_leg.get("sigma", sigma),
                option_type=atm_leg["option_type"],
            )

            # Net premium
            net_prem = net_premium_collected(legs) * lot_size

            # POP from exact lognormal CDF
            be_list = payoff_curve["breakevens"]
            pop = ev_result["pop"]

            scored.append({
                "name": strat["name"],
                "type": strat["type"],
                "legs": legs,
                "ev": round(ev, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(ev_result["max_profit"], 2),
                "pop": round(pop, 4),
                "sharpe": round(ev_result["sharpe"], 4),
                "ev_per_max_loss": round(ev_result["ev_per_max_loss"], 4),
                "std_dev": round(ev_result["std_dev"], 2),
                "downside_deviation": round(ev_result["downside_deviation"], 2),
                "breakevens": be_list,
                "net_premium": round(net_prem, 2),
                "margin": margin,
                "capital_efficiency": round(ev / margin["total"], 4) if margin["total"] > 0 else 0,
                "greeks": atm_greeks,
                "payoff_curve": payoff_curve,
                "roi": round(ev / margin["total"] * 100, 2) if margin["total"] > 0 else 0,
            })

        except Exception as e:
            logger.error(f"Error scoring {strat.get('name', '?')}: {e}", exc_info=True)

    # Sort by EV / |MaxLoss| descending (risk-adjusted EV)
    scored.sort(key=lambda x: x["ev_per_max_loss"], reverse=True)

    logger.info(f"Ranked {len(scored)} valid strategies. Returning top {top_n}.")
    return scored[:top_n]
