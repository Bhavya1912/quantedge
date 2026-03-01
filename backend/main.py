"""
QuantEdge – Options Strategy Optimizer
FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from api.optimizer import router as optimizer_router
from api.greeks import router as greeks_router
from api.monte_carlo import router as mc_router
from api.iv_analysis import router as iv_router
from api.chain import router as chain_router
from api.auth import router as auth_router
from api.stress import router as stress_router
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)


@app.options("/{full_path:path}")
async def options_preflight(full_path: str):
    """Explicit OPTIONS fallback for platforms/proxies that bypass middleware preflight handling."""
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Authorization,Content-Type,Accept,Origin,X-Requested-With",
        },
    )


# Versioned API routers
app.include_router(auth_router,      prefix="/api/v1/auth",     tags=["Auth"])
app.include_router(chain_router,     prefix="/api/v1/chain",    tags=["Option Chain"])
app.include_router(optimizer_router, prefix="/api/v1/optimize", tags=["Optimizer"])
app.include_router(greeks_router,    prefix="/api/v1/greeks",   tags=["Greeks"])
app.include_router(mc_router,        prefix="/api/v1/simulate", tags=["Monte Carlo"])
app.include_router(iv_router,        prefix="/api/v1/iv",       tags=["IV Analysis"])
app.include_router(stress_router,    prefix="/api/v1/stress",   tags=["Stress Test"])

# Legacy/unversioned compatibility routes (helps if frontend base URL omits /api/v1)
app.include_router(auth_router,      prefix="/auth",     tags=["Auth Legacy"])
app.include_router(chain_router,     prefix="/chain",    tags=["Option Chain Legacy"])
app.include_router(optimizer_router, prefix="/optimize", tags=["Optimizer Legacy"])
app.include_router(greeks_router,    prefix="/greeks",   tags=["Greeks Legacy"])
app.include_router(mc_router,        prefix="/simulate", tags=["Monte Carlo Legacy"])
app.include_router(iv_router,        prefix="/iv",       tags=["IV Analysis Legacy"])
app.include_router(stress_router,    prefix="/stress",   tags=["Stress Test Legacy"])


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancer."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "quantedge-backend",
    }


@app.get("/health", tags=["Health"])
async def health_check_alias():
    """Compatibility health endpoint."""
    return await health_check()


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "QuantEdge API — India's first probability-weighted options optimizer",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Ensure 404 responses include CORS headers for browser diagnostics."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found", "path": str(request.url.path)},
        headers={"Access-Control-Allow-Origin": "*"},
    )
