"""GET /api/v1/chain/{symbol} — Live option chain endpoint."""
from fastapi import APIRouter, Query
from typing import Optional
from data.nse_client import nse_client

router = APIRouter()


@router.get("/{symbol}")
async def get_option_chain(
    symbol: str,
    expiry: Optional[str] = Query(default=None, description="DD-MMM-YYYY"),
):
    """Fetch live option chain from NSE India."""
    data = await nse_client.fetch_option_chain(
        symbol=symbol.upper(),
        expiry_filter=expiry,
    )
    return data
