"""
Pydantic Request & Response Models
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


# ── Request Models ──────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    symbol: str = Field(default="BANKNIFTY", description="Underlying symbol")
    capital: float = Field(..., gt=0, description="Available capital in ₹")
    market_view: Literal["bullish", "bearish", "neutral"]
    volatility_outlook: Literal["rising", "falling", "stable"]
    risk_appetite: Literal["conservative", "moderate", "aggressive"]
    time_horizon: Literal["weekly", "monthly"]
    expiry: Optional[str] = None  # DD-MMM-YYYY, uses nearest if None
    top_n: int = Field(default=3, ge=1, le=10)

    @field_validator("capital")
    @classmethod
    def capital_minimum(cls, v):
        if v < 10000:
            raise ValueError("Minimum capital is ₹10,000")
        return v


class GreeksRequest(BaseModel):
    spot: float = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    expiry_days: int = Field(..., ge=0)
    iv: float = Field(..., gt=0, le=500, description="IV in % (e.g., 14.5 for 14.5%)")
    option_type: Literal["call", "put"]
    risk_free_rate: Optional[float] = None


class MonteCarloRequest(BaseModel):
    symbol: str = "BANKNIFTY"
    legs: List[dict]
    spot: float = Field(..., gt=0)
    iv: float = Field(..., gt=0, description="IV in %")
    expiry_days: int = Field(..., ge=0)
    n_simulations: int = Field(default=10000, ge=1000, le=100000)
    n_steps: int = Field(default=1, ge=1, le=252)
    seed: int = 42


class StressRequest(BaseModel):
    legs: List[dict]
    spot: float
    iv: float
    expiry_days: int
    spot_move_pct: float = Field(default=0.0, ge=-20.0, le=20.0)
    iv_move_pct: float = Field(default=0.0, ge=-50.0, le=100.0)
    days_forward: int = Field(default=0, ge=0, le=30)


class IVRequest(BaseModel):
    symbol: str = "BANKNIFTY"
    spot: Optional[float] = None


# ── Response Models ──────────────────────────────────────────────────────────

class GreeksResponse(BaseModel):
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    vanna: Optional[float] = None
    charm: Optional[float] = None


class LegResponse(BaseModel):
    K: float
    option_type: str
    position: str
    quantity: int
    premium: float
    sigma: float


class MarginResponse(BaseModel):
    span: float
    exposure: float
    total: float


class PayoffCurveResponse(BaseModel):
    prices: List[float]
    payoffs: List[float]
    breakevens: List[float]
    max_profit: float
    max_loss: float


class RankedStrategyResponse(BaseModel):
    rank: int
    name: str
    type: str
    legs: List[dict]
    ev: float
    max_loss: float
    max_profit: float
    pop: float
    sharpe: float
    ev_per_max_loss: float
    std_dev: float
    breakevens: List[float]
    net_premium: float
    margin: dict
    capital_efficiency: float
    greeks: dict
    payoff_curve: dict
    roi: float


class OptimizeResponse(BaseModel):
    symbol: str
    spot: float
    iv: float
    expiry: str
    strategies: List[RankedStrategyResponse]
    n_candidates_evaluated: int
    optimization_time_ms: float
    is_mock_data: bool = False


class MonteCarloResponse(BaseModel):
    n_simulations: int
    ev: float
    std_dev: float
    win_rate: float
    max_profit: float
    max_loss: float
    var_95: float
    var_99: float
    cvar_95: float
    sharpe: float
    sortino: float
    histogram: List[dict]
    sample_paths: dict
    terminal_prices: dict


class StressResponse(BaseModel):
    pnl_change: float
    new_pnl: float
    new_delta: float
    new_gamma: float
    new_theta: float
    new_vega: float
    new_iv: float
    time_decay: float
    scenario_description: str
