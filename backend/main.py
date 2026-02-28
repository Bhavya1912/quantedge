"""
QuantEdge – Options Strategy Optimizer
FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import json

from api.optimizer import router as optimizer_router
from api.greeks import router as greeks_router
from api.monte_carlo import router as mc_router
from api.iv_analysis import router as iv_router
from api.chain import router as chain_router
from api.auth import router as auth_router
from api.stress import router as stress_router
from utils.config import settings
from utils.logger import setup_logging
from data.cache import cache

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("QuantEdge backend starting up...")
    await cache.connect()
    logger.info("Redis cache connected.")
    yield
    logger.info("QuantEdge backend shutting down...")
    await cache.disconnect()


app = FastAPI(
    title="QuantEdge API",
    description="Probability-weighted options strategy optimizer for Indian retail traders.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

def _parse_allowed_origins(val):
    if isinstance(val, list):
        return val
    if not val or not str(val).strip():
        return []
    s = str(val).strip()
    # If user provided a JSON array in the env, try to parse it
    if s.startswith("["):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    # Fallback to comma-separated string
    return [o.strip() for o in s.split(",") if o.strip()]

_allowed_origins = _parse_allowed_origins(settings.ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    # Allow Vercel preview/production URLs without requiring manual env updates each deploy
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router,      prefix="/api/v1/auth",     tags=["Auth"])
app.include_router(chain_router,     prefix="/api/v1/chain",    tags=["Option Chain"])
app.include_router(optimizer_router, prefix="/api/v1/optimize", tags=["Optimizer"])
app.include_router(greeks_router,    prefix="/api/v1/greeks",   tags=["Greeks"])
app.include_router(mc_router,        prefix="/api/v1/simulate", tags=["Monte Carlo"])
app.include_router(iv_router,        prefix="/api/v1/iv",       tags=["IV Analysis"])
app.include_router(stress_router,    prefix="/api/v1/stress",   tags=["Stress Test"])


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancer."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "quantedge-backend",
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "QuantEdge API — India's first probability-weighted options optimizer",
        "docs": "/docs",
        "version": "1.0.0",
    }
