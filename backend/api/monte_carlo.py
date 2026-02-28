"""POST /api/v1/simulate — Monte Carlo GBM simulation endpoint."""
from fastapi import APIRouter, HTTPException
from models.request import MonteCarloRequest
from core.monte_carlo import run_monte_carlo
from utils.config import settings

router = APIRouter()


@router.post("")
async def run_simulation(req: MonteCarloRequest):
    """
    Run Monte Carlo GBM simulation using Box-Muller Gaussian sampling.
    Returns full P&L distribution, EV, VaR, CVaR, sample paths.
    """
    if not req.legs:
        raise HTTPException(status_code=422, detail="At least one leg required.")

    T = req.expiry_days / 365
    sigma = req.iv / 100

    result = run_monte_carlo(
        legs=req.legs,
        S0=req.spot,
        sigma=sigma,
        T=max(T, 1/365),
        r=settings.RISK_FREE_RATE,
        n_simulations=req.n_simulations,
        n_steps=req.n_steps,
        seed=req.seed,
    )

    return result
