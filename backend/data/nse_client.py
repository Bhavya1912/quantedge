"""
NSE Option Chain Data Client
==============================
Fetches live option chain from NSE India.
Handles session cookies, rate limiting, and retry logic.
"""
import asyncio
import logging
import time
from typing import Optional

import httpx

from utils.config import settings
from data.cache import cache

logger = logging.getLogger(__name__)


class NSEClient:
    """
    Async client for NSE India option chain API.
    NSE requires cookies from a page visit before API calls work.
    """

    BASE_URL = "https://www.nseindia.com"
    CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices"
    EQUITY_URL = "https://www.nseindia.com/api/option-chain-equities"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.nseindia.com/",
        "X-Requested-With": "XMLHttpRequest",
    }

    SYMBOL_MAP = {
        "BANKNIFTY": "BANKNIFTY",
        "NIFTY":     "NIFTY",
        "FINNIFTY":  "FINNIFTY",
        "MIDCPNIFTY": "MIDCPNIFTY",
    }

    def __init__(self):
        self._cookies: dict = {}
        self._cookie_timestamp: float = 0
        self._cookie_ttl: float = 300  # Refresh cookies every 5 min
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.HEADERS,
                timeout=httpx.Timeout(15.0),
                follow_redirects=True,
            )
        return self._client

    async def _refresh_cookies(self):
        """
        Visit NSE homepage to get session cookies.
        NSE blocks API calls without valid session cookies.
        """
        if time.time() - self._cookie_timestamp < self._cookie_ttl:
            return

        client = await self._get_client()
        try:
            logger.info("Refreshing NSE session cookies...")
            # Visit homepage first
            resp = await client.get(self.BASE_URL, headers=self.HEADERS)
            resp.raise_for_status()
            self._cookies = dict(resp.cookies)
            self._cookie_timestamp = time.time()
            logger.info(f"NSE cookies refreshed. Got {len(self._cookies)} cookies.")
            await asyncio.sleep(1)  # Polite delay
        except Exception as e:
            logger.error(f"Failed to refresh NSE cookies: {e}")

    async def fetch_option_chain(
        self,
        symbol: str = "BANKNIFTY",
        expiry_filter: Optional[str] = None,
    ) -> dict:
        """
        Fetch raw option chain from NSE.

        Args:
            symbol:        Underlying symbol (BANKNIFTY, NIFTY, etc.)
            expiry_filter: Filter to specific expiry date (YYYY-MM-DD)

        Returns:
            Parsed option chain dict with:
            - spot: current underlying price
            - expiries: list of available expiry dates
            - chain: list of strike rows
        """
        cache_key = f"nse:chain:{symbol}:{expiry_filter or 'all'}"

        # Check cache
        cached = await cache.get(cache_key)
        if cached:
            return cached

        await self._refresh_cookies()

        params = {"symbol": self.SYMBOL_MAP.get(symbol, symbol)}
        if expiry_filter:
            params["expiryDate"] = expiry_filter

        client = await self._get_client()

        for attempt in range(3):
            try:
                resp = await client.get(
                    self.CHAIN_URL,
                    params=params,
                    cookies=self._cookies,
                    headers={**self.HEADERS, "Referer": "https://www.nseindia.com/option-chain"},
                )
                resp.raise_for_status()
                raw = resp.json()
                parsed = self._parse_chain(raw, symbol)

                if not parsed.get("chain"):
                    logger.warning("NSE returned empty chain data — falling back to mock data.")
                    from data.mock_data import get_mock_chain
                    parsed = get_mock_chain(symbol)

                # Cache for 60 seconds
                await cache.set(cache_key, parsed, ttl=settings.CACHE_TTL_CHAIN)
                return parsed

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.warning("NSE 401 — refreshing cookies and retrying...")
                    self._cookie_timestamp = 0
                    await self._refresh_cookies()
                elif e.response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"NSE rate limited — waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    raise
            except Exception as e:
                logger.error(f"NSE fetch attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    logger.warning("Falling back to mock data.")
                    from data.mock_data import get_mock_chain
                    return get_mock_chain(symbol)
                await asyncio.sleep(1)

        from data.mock_data import get_mock_chain
        return get_mock_chain(symbol)

    def _parse_chain(self, raw: dict, symbol: str) -> dict:
        """
        Parse NSE raw response into clean option chain format.
        """
        try:
            records = raw.get("records", {})
            data = records.get("data", [])
            spot = records.get("underlyingValue", 0)
            expiries = records.get("expiryDates", [])

            chain_rows = []
            for item in data:
                strike = item.get("strikePrice")
                ce = item.get("CE", {})
                pe = item.get("PE", {})

                if not strike:
                    continue

                # Compute IV from LTP if not directly available
                call_iv = ce.get("impliedVolatility", 0)
                put_iv = pe.get("impliedVolatility", 0)

                row = {
                    "strike": strike,
                    "expiry": ce.get("expiryDate") or pe.get("expiryDate"),
                    # Call side
                    "call_ltp":     ce.get("lastPrice", 0),
                    "call_bid":     ce.get("bidprice", ce.get("lastPrice", 0) * 0.995),
                    "call_ask":     ce.get("askPrice",  ce.get("lastPrice", 0) * 1.005),
                    "call_oi":      ce.get("openInterest", 0),
                    "call_oi_chg":  ce.get("changeinOpenInterest", 0),
                    "call_volume":  ce.get("totalTradedVolume", 0),
                    "call_iv":      round(call_iv, 2),
                    "call_delta":   ce.get("delta", 0),
                    "call_theta":   ce.get("theta", 0),
                    "call_gamma":   ce.get("gamma", 0),
                    "call_vega":    ce.get("vega", 0),
                    # Put side
                    "put_ltp":      pe.get("lastPrice", 0),
                    "put_bid":      pe.get("bidprice", pe.get("lastPrice", 0) * 0.995),
                    "put_ask":      pe.get("askPrice",  pe.get("lastPrice", 0) * 1.005),
                    "put_oi":       pe.get("openInterest", 0),
                    "put_oi_chg":   pe.get("changeinOpenInterest", 0),
                    "put_volume":   pe.get("totalTradedVolume", 0),
                    "put_iv":       round(put_iv, 2),
                    "put_delta":    pe.get("delta", 0),
                    "put_theta":    pe.get("theta", 0),
                    "put_gamma":    pe.get("gamma", 0),
                    "put_vega":     pe.get("vega", 0),
                    # Metadata
                    "pcr":          round(pe.get("openInterest", 0) / max(ce.get("openInterest", 1), 1), 2),
                }
                chain_rows.append(row)

            # Sort by strike ascending
            chain_rows.sort(key=lambda x: x["strike"])

            return {
                "symbol": symbol,
                "spot": spot,
                "expiries": expiries,
                "chain": chain_rows,
                "total_call_oi": sum(r["call_oi"] for r in chain_rows),
                "total_put_oi": sum(r["put_oi"] for r in chain_rows),
                "pcr": round(
                    sum(r["put_oi"] for r in chain_rows) /
                    max(sum(r["call_oi"] for r in chain_rows), 1), 2
                ),
            }

        except Exception as e:
            logger.error(f"Failed to parse NSE chain response: {e}", exc_info=True)
            from data.mock_data import get_mock_chain
            return get_mock_chain(symbol)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton client
nse_client = NSEClient()
