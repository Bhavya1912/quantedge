"""POST /api/v1/stress — Scenario stress testing endpoint."""
from fastapi import APIRouter
from models.request import StressRequest
from core.black_scholes import bs_greeks, bs_price
from core.payoff import compute_multi_leg_payoff
from utils.config import settings

router = APIRouter()


@router.post("")
async def stress_test(req: StressRequest):
    """
    Recalculate P&L and Greeks after a hypothetical scenario.
    Handles: spot move, IV change, time decay.
    """
    T_original = req.expiry_days / 365
    sigma_original = req.iv / 100

    # Apply scenario
    new_spot = req.spot * (1 + req.spot_move_pct / 100)
    new_sigma = max(sigma_original + req.iv_move_pct / 100, 0.01)
    new_T = max(T_original - req.days_forward / 365, 1e-6)

    # Current P&L (at-T payoff approximation using BS)
    current_pnl = 0.0
    new_pnl = 0.0

    for leg in req.legs:
        K = leg["K"]
        opt_type = leg["option_type"]
        position = leg["position"]
        qty = leg.get("quantity", 1)
        premium = leg.get("premium", 0.0)
        sigma_leg = leg.get("sigma", sigma_original)
        sign = 1 if position == "long" else -1
        lot_size = 15

        # Current value
        current_val = bs_price(req.spot, K, T_original, settings.RISK_FREE_RATE, sigma_leg, opt_type)
        # New value under scenario
        new_val = bs_price(new_spot, K, new_T, settings.RISK_FREE_RATE, new_sigma, opt_type)

        # P&L vs entry premium
        current_pnl += sign * (current_val - premium) * qty * lot_size
        new_pnl += sign * (new_val - premium) * qty * lot_size

    # New portfolio Greeks
    leg = req.legs[0] if req.legs else {}
    if leg:
        K = leg["K"]
        sigma_leg = leg.get("sigma", sigma_original)
        opt_type = leg.get("option_type", "call")
        new_g = bs_greeks(new_spot, K, new_T, settings.RISK_FREE_RATE, new_sigma, opt_type)
    else:
        new_g = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}

    # Time decay over days_forward
    time_decay = 0.0
    for leg in req.legs:
        K = leg["K"]
        sigma_leg = leg.get("sigma", sigma_original)
        opt_type = leg.get("option_type", "call")
        qty = leg.get("quantity", 1)
        sign = 1 if leg["position"] == "long" else -1
        g = bs_greeks(req.spot, K, T_original, settings.RISK_FREE_RATE, sigma_leg, opt_type)
        time_decay += sign * g["theta"] * req.days_forward * qty * 15

    scenario_desc = (
        f"Spot {'+'if req.spot_move_pct>=0 else ''}{req.spot_move_pct:.1f}%, "
        f"IV {'+'if req.iv_move_pct>=0 else ''}{req.iv_move_pct:.1f}%, "
        f"{req.days_forward}d forward"
    )

    return {
        "current_pnl": round(current_pnl, 2),
        "new_pnl": round(new_pnl, 2),
        "pnl_change": round(new_pnl - current_pnl, 2),
        "new_spot": round(new_spot, 2),
        "new_iv": round(new_sigma * 100, 2),
        "new_delta": round(new_g.get("delta", 0), 4),
        "new_gamma": round(new_g.get("gamma", 0), 6),
        "new_theta": round(new_g.get("theta", 0), 4),
        "new_vega": round(new_g.get("vega", 0), 4),
        "time_decay": round(time_decay, 2),
        "scenario_description": scenario_desc,
    }
