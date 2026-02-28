"""
POST /api/v1/optimize
Core optimizer endpoint — the main product.
"""
import logging
import time
from fastapi import APIRouter, HTTPException, Depends

from models.request import OptimizeRequest, OptimizeResponse, RankedStrategyResponse
from data.nse_client import nse_client
from core.optimizer import generate_strategy_universe, rank_strategies
from utils.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=OptimizeResponse)
async def optimize_strategies(req: OptimizeRequest):
    """
    Main optimizer endpoint.

    1. Fetch live option chain from NSE
    2. Generate strategy universe based on market view
    3. Score and rank by EV / |MaxLoss| with risk constraints
    4. Return top N strategies with full analytics

    Returns ranked strategies with:
    - True EV via lognormal numerical integration
    - Exact POP via lognormal CDF
    - Full Greeks (Black-Scholes exact)
    - Payoff curves
    - Margin requirements
    """
    t_start = time.time()

    # ── 1. Fetch option chain ────────────────────────────────────────────────
    try:
        chain_data = await nse_client.fetch_option_chain(
            symbol=req.symbol,
            expiry_filter=req.expiry,
        )
    except Exception as e:
        logger.error(f"Chain fetch failed: {e}")
        raise HTTPException(status_code=503, detail=f"Data fetch failed: {str(e)}")

    chain = chain_data["chain"]
    spot = chain_data["spot"]
    expiry = chain_data["expiries"][0] if chain_data["expiries"] else "N/A"
    is_mock = chain_data.get("is_mock", False)

    if not chain:
        raise HTTPException(status_code=404, detail="No option chain data available.")

    # ── 2. Get ATM IV ────────────────────────────────────────────────────────
    import numpy as np
    strikes = [r["strike"] for r in chain]
    atm_idx = int(np.argmin(np.abs(np.array(strikes) - spot)))
    atm_row = chain[atm_idx]
    atm_iv = (atm_row["call_iv"] + atm_row["put_iv"]) / 2 / 100  # as decimal

    # ── 3. Determine time to expiry ──────────────────────────────────────────
    if req.time_horizon == "weekly":
        T = 1 / 365  # ~1 trading day for weekly
    else:
        T = 29 / 365  # ~1 month

    # Adjust IV based on vol outlook
    if req.volatility_outlook == "rising":
        atm_iv *= 1.05
    elif req.volatility_outlook == "falling":
        atm_iv *= 0.95

    # ── 4. Generate strategy universe ────────────────────────────────────────
    candidates = generate_strategy_universe(
        chain=chain,
        spot=spot,
        market_view=req.market_view,
    )

    if not candidates:
        raise HTTPException(
            status_code=422,
            detail="No valid strategies generated for given parameters."
        )

    # ── 5. Rank strategies ───────────────────────────────────────────────────
    ranked = rank_strategies(
        strategies=candidates,
        spot=spot,
        sigma=atm_iv,
        T=T,
        r=settings.RISK_FREE_RATE,
        capital=req.capital,
        risk_appetite=req.risk_appetite,
        top_n=req.top_n,
    )

    if not ranked:
        raise HTTPException(
            status_code=422,
            detail="No strategies passed risk constraints. Try increasing capital or relaxing risk appetite."
        )

    # ── 6. Format response ───────────────────────────────────────────────────
    ranked_with_rank = []
    for i, strat in enumerate(ranked):
        ranked_with_rank.append(RankedStrategyResponse(
            rank=i + 1,
            **strat
        ))

    t_elapsed = (time.time() - t_start) * 1000

    return OptimizeResponse(
        symbol=req.symbol,
        spot=round(spot, 2),
        iv=round(atm_iv * 100, 2),
        expiry=expiry,
        strategies=ranked_with_rank,
        n_candidates_evaluated=len(candidates),
        optimization_time_ms=round(t_elapsed, 1),
        is_mock_data=is_mock,
    )
