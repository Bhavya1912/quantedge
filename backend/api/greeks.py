"""POST /api/v1/greeks — Black-Scholes Greeks endpoint."""
from fastapi import APIRouter
from models.request import GreeksRequest
from core.black_scholes import bs_greeks, bs_price, implied_volatility
from utils.config import settings

router = APIRouter()


@router.post("")
async def compute_greeks(req: GreeksRequest):
    """
    Compute full Black-Scholes Greeks for a single option.
    All values are exact analytical solutions.
    """
    T = req.expiry_days / 365
    sigma = req.iv / 100
    r = req.risk_free_rate or settings.RISK_FREE_RATE

    greeks = bs_greeks(
        S=req.spot,
        K=req.strike,
        T=T,
        r=r,
        sigma=sigma,
        option_type=req.option_type,
    )

    price = bs_price(req.spot, req.strike, T, r, sigma, req.option_type)

    # IV shocked Greeks
    greeks_iv_up = bs_greeks(req.spot, req.strike, T, r, sigma + 0.05, req.option_type)
    greeks_iv_dn = bs_greeks(req.spot, req.strike, T, r, max(sigma - 0.05, 0.01), req.option_type)

    return {
        "greeks": greeks,
        "price": round(price, 2),
        "iv_shocked": {
            "iv_plus_5pct": {
                "iv": round((sigma + 0.05) * 100, 2),
                "price": round(bs_price(req.spot, req.strike, T, r, sigma + 0.05, req.option_type), 2),
                "delta": round(greeks_iv_up["delta"], 4),
                "vega": round(greeks_iv_up["vega"], 4),
            },
            "iv_minus_5pct": {
                "iv": round(max(sigma - 0.05, 0.01) * 100, 2),
                "price": round(bs_price(req.spot, req.strike, T, r, max(sigma - 0.05, 0.01), req.option_type), 2),
                "delta": round(greeks_iv_dn["delta"], 4),
                "vega": round(greeks_iv_dn["vega"], 4),
            },
        },
        "parameters": {
            "spot": req.spot,
            "strike": req.strike,
            "expiry_days": req.expiry_days,
            "iv_pct": req.iv,
            "option_type": req.option_type,
            "risk_free_rate": r,
        },
    }
