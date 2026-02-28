"""
Mock Data — Development & Testing
===================================
Realistic Bank Nifty option chain mock data.
Used when NSE API is unavailable (dev mode, testing).
"""
import numpy as np
from datetime import datetime, timedelta
from core.black_scholes import bs_price, bs_greeks, implied_volatility
from utils.config import settings


SPOT = 51204.0
BASE_IV = 0.1432   # 14.32%
R = 0.065


def _bs_chain_row(strike: float, spot: float, T: float, iv_skew: float = 0.0) -> dict:
    """Generate a realistic option chain row using Black-Scholes."""
    sigma = max(BASE_IV + iv_skew, 0.05)

    # Smile: OTM options have higher IV
    moneyness = (strike - spot) / spot
    smile_adj = abs(moneyness) * 0.20
    call_iv = sigma + smile_adj * (0.8 if moneyness < 0 else 0.5)
    put_iv = sigma + smile_adj * (1.2 if moneyness < 0 else 0.6)

    call_price = bs_price(spot, strike, T, R, call_iv, "call")
    put_price = bs_price(spot, strike, T, R, put_iv, "put")

    call_g = bs_greeks(spot, strike, T, R, call_iv, "call")
    put_g = bs_greeks(spot, strike, T, R, put_iv, "put")

    spread_pct = 0.005  # 0.5% bid-ask spread
    call_oi_base = max(int(500000 * np.exp(-0.5 * (moneyness / 0.02) ** 2)), 1000)
    put_oi_base  = max(int(600000 * np.exp(-0.5 * (moneyness / 0.02) ** 2)), 1000)

    return {
        "strike": round(strike),
        "expiry": (datetime.now() + timedelta(days=max(1, int(T * 365)))).strftime("%d-%b-%Y"),
        "call_ltp":    round(call_price, 2),
        "call_bid":    round(call_price * (1 - spread_pct), 2),
        "call_ask":    round(call_price * (1 + spread_pct), 2),
        "call_oi":     call_oi_base + np.random.randint(-5000, 5000),
        "call_oi_chg": np.random.randint(-50000, 100000),
        "call_volume": np.random.randint(1000, 50000),
        "call_iv":     round(call_iv * 100, 2),
        "call_delta":  round(call_g["delta"], 4),
        "call_gamma":  round(call_g["gamma"], 6),
        "call_theta":  round(call_g["theta"] * 100, 2),
        "call_vega":   round(call_g["vega"] * 100, 2),
        "put_ltp":     round(put_price, 2),
        "put_bid":     round(put_price * (1 - spread_pct), 2),
        "put_ask":     round(put_price * (1 + spread_pct), 2),
        "put_oi":      put_oi_base + np.random.randint(-5000, 5000),
        "put_oi_chg":  np.random.randint(-100000, 50000),
        "put_volume":  np.random.randint(1000, 50000),
        "put_iv":      round(put_iv * 100, 2),
        "put_delta":   round(put_g["delta"], 4),
        "put_gamma":   round(put_g["gamma"], 6),
        "put_theta":   round(put_g["theta"] * 100, 2),
        "put_vega":    round(put_g["vega"] * 100, 2),
        "pcr":         round(put_oi_base / max(call_oi_base, 1), 2),
    }


def get_mock_chain(symbol: str = "BANKNIFTY") -> dict:
    """
    Generate a realistic mock option chain for Bank Nifty.
    Strikes every 100 points, ATM ± 10 strikes.
    """
    spot = SPOT
    T = 1 / 365  # 1-day expiry (weekly)

    # Generate strikes: ATM ± 10 × 100
    atm_strike = round(spot / 100) * 100
    strikes = [atm_strike + (i - 10) * 100 for i in range(21)]

    chain = [_bs_chain_row(k, spot, T) for k in strikes]

    expiry_dates = [
        (datetime.now() + timedelta(days=d)).strftime("%d-%b-%Y")
        for d in [1, 8, 29, 57]
    ]

    total_call_oi = sum(r["call_oi"] for r in chain)
    total_put_oi = sum(r["put_oi"] for r in chain)

    return {
        "symbol": symbol,
        "spot": spot,
        "expiries": expiry_dates,
        "chain": chain,
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "pcr": round(total_put_oi / max(total_call_oi, 1), 2),
        "is_mock": True,
    }


def get_mock_iv_data(symbol: str = "BANKNIFTY") -> dict:
    """Mock IV surface data for development."""
    # Historical IV data (90 days)
    np.random.seed(42)
    days = 90
    hv_series = 0.118 + 0.03 * np.sin(np.linspace(0, 3*np.pi, days)) + np.random.normal(0, 0.005, days)
    iv_series = 0.143 + 0.04 * np.sin(np.linspace(0, 3*np.pi, days)) + np.random.normal(0, 0.007, days)
    iv_series = np.clip(iv_series, 0.08, 0.40)
    hv_series = np.clip(hv_series, 0.06, 0.35)

    # IV percentile over 52 weeks
    iv_52w_high = 0.42
    iv_52w_low = 0.09
    iv_rank = round((BASE_IV - iv_52w_low) / (iv_52w_high - iv_52w_low) * 100, 1)

    # Simulated 252-day history for percentile
    iv_history_1y = 0.15 + 0.12 * np.random.beta(2, 5, 252)
    iv_percentile = round(float(np.mean(iv_history_1y < BASE_IV)) * 100, 1)

    return {
        "symbol": symbol,
        "current_iv": round(BASE_IV * 100, 2),
        "current_hv_20d": round(float(np.std(np.diff(np.log(SPOT + np.random.normal(0, 50, 21))))) * np.sqrt(252) * 100, 2),
        "current_hv_30d": round(float(np.std(np.diff(np.log(SPOT + np.random.normal(0, 50, 31))))) * np.sqrt(252) * 100, 2),
        "iv_rank": iv_rank,
        "iv_percentile": iv_percentile,
        "iv_52w_high": round(iv_52w_high * 100, 2),
        "iv_52w_low": round(iv_52w_low * 100, 2),
        "term_structure": [
            {"expiry": "1W",  "days": 1,  "iv": round(BASE_IV * 100 + 0.1, 2)},
            {"expiry": "2W",  "days": 7,  "iv": round(BASE_IV * 100 - 0.1, 2)},
            {"expiry": "1M",  "days": 29, "iv": round(BASE_IV * 100 - 0.5, 2)},
            {"expiry": "2M",  "days": 57, "iv": round(BASE_IV * 100 - 0.8, 2)},
            {"expiry": "3M",  "days": 85, "iv": round(BASE_IV * 100 - 1.2, 2)},
        ],
        "iv_history": {
            "dates": [(datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d") for i in range(days)],
            "iv": iv_series.tolist(),
            "hv_20d": hv_series.tolist(),
        },
    }
