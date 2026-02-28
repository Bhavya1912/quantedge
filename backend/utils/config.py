"""
Application configuration via environment variables.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORS
    # Store as a comma-separated string in environment variables (Render UI).
    # Example: "http://localhost:5173,http://localhost:3000,https://quantedge.vercel.app"
    ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://localhost:3000,https://quantedge.vercel.app,https://quantedge-theta.vercel.app,https://quantedge.in"
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        """Parse comma-separated string or list. Empty string becomes empty list."""
        if isinstance(value, str):
            if not value.strip():
                return ""
            return ",".join(origin.strip() for origin in value.split(",") if origin.strip())
        if isinstance(value, list):
            return ",".join(origin.strip() for origin in value if str(origin).strip())
        return value

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_CHAIN: int = 60          # Option chain: 60 seconds
    CACHE_TTL_IV: int = 300            # IV data: 5 minutes
    CACHE_TTL_HV: int = 3600           # Historical vol: 1 hour

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/quantedge"

    # JWT
    JWT_SECRET: str = "change-me-in-production-use-openssl-rand-hex-16"  # Override in .env or env vars!
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080    # 7 days

    # NSE
    NSE_BASE_URL: str = "https://www.nseindia.com"
    NSE_OPTION_CHAIN_URL: str = "https://www.nseindia.com/api/option-chain-indices"
    NSE_HEADERS: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
    }

    # Broker APIs
    UPSTOX_API_KEY: str = ""
    UPSTOX_SECRET: str = ""
    UPSTOX_REDIRECT_URI: str = "https://quantedge.in/callback"
    ZERODHA_API_KEY: str = ""
    ZERODHA_SECRET: str = ""

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_SECRET: str = ""
    SUBSCRIPTION_AMOUNT_PAISE: int = 150000  # ₹1500 in paise

    # Quant engine defaults
    RISK_FREE_RATE: float = 0.065       # 6.5% RBI repo rate
    MONTE_CARLO_SIMULATIONS: int = 10000
    PAYOFF_PRICE_STEPS: int = 1000      # Steps for numerical EV integration
    MAX_STRATEGY_LEGS: int = 4
    STRIKE_RANGE_ATM: int = 5           # ±5 strikes from ATM to scan

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""


settings = Settings()
