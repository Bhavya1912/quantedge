"""GET /api/v1/iv/{symbol} — IV rank, percentile, surface."""
from fastapi import APIRouter
from data.mock_data import get_mock_iv_data

router = APIRouter()


@router.get("/{symbol}")
async def get_iv_analysis(symbol: str):
    """
    Return IV rank, percentile, term structure, skew, and 90-day history.
    Phase 2 feature: connects to historical data store in production.
    """
    # In production: query PostgreSQL for historical IV data
    # and compute real rank/percentile
    data = get_mock_iv_data(symbol.upper())
    return data
