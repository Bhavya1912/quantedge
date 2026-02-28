# QuantEdge – Options Strategy Optimizer

**India's first probability-weighted options strategy optimizer for retail traders.**

> Not a signal provider. Not a tip service. Quantitative decision infrastructure.

---

## Architecture Overview

```
quantedge/
├── backend/                    # Python FastAPI — Quant Engine
│   ├── api/                    # Route handlers
│   │   ├── optimizer.py        # POST /optimize — core ranking endpoint
│   │   ├── greeks.py           # POST /greeks — Black-Scholes Greeks
│   │   ├── monte_carlo.py      # POST /simulate — GBM Monte Carlo
│   │   ├── iv_analysis.py      # GET /iv — volatility surface
│   │   ├── chain.py            # GET /chain — live option chain
│   │   └── auth.py             # POST /auth — JWT authentication
│   ├── core/                   # Mathematical engines
│   │   ├── black_scholes.py    # BS pricing + Greeks (exact formulas)
│   │   ├── ev_engine.py        # True EV via numerical integration
│   │   ├── monte_carlo.py      # Vectorized GBM (Box-Muller)
│   │   ├── optimizer.py        # Constrained strategy optimizer
│   │   ├── payoff.py           # Multi-leg payoff calculator
│   │   └── probability.py      # Lognormal POP/POT calculator
│   ├── data/                   # Data ingestion layer
│   │   ├── nse_client.py       # NSE option chain scraper
│   │   ├── upstox_client.py    # Upstox broker API client
│   │   ├── zerodha_client.py   # Kite Connect API client
│   │   ├── cache.py            # Redis caching layer
│   │   └── mock_data.py        # Mock data for development
│   ├── models/                 # Pydantic schemas
│   │   ├── strategy.py         # Strategy data models
│   │   ├── request.py          # API request schemas
│   │   └── response.py         # API response schemas
│   ├── utils/
│   │   ├── logger.py
│   │   └── config.py
│   ├── main.py                 # FastAPI app entry point
│   └── requirements.txt
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Page-level components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── store/              # Zustand state management
│   │   └── utils/              # API client + helpers
│   ├── index.html
│   └── package.json
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── tests/
│   ├── backend/                # pytest test suite
│   └── frontend/               # Vitest tests
└── scripts/
    ├── setup.sh                # One-command dev setup
    └── deploy.sh               # Production deployment
```

---

## Quant Engine — Mathematical Foundation

### 1. True Expected Value (Numerical Integration)

```
EV = ∫₀^∞ Payoff(Sᵀ) · f(Sᵀ) dSᵀ

where:
f(Sᵀ) = lognormal PDF with parameters:
  μ_log = ln(S₀) + (r - σ²/2)T
  σ_log = σ√T
```

Not Monte Carlo approximation — exact numerical integration over 1000 price points.

### 2. Black-Scholes Greeks (Exact)

```
d₁ = [ln(S/K) + (r + σ²/2)T] / (σ√T)
d₂ = d₁ - σ√T

Delta  (Δ) = N(d₁)               [call] / N(d₁)-1    [put]
Gamma  (Γ) = φ(d₁) / (S·σ·√T)
Vega   (ν) = S·φ(d₁)·√T
Theta  (Θ) = -(S·φ(d₁)·σ)/(2√T) - r·K·e^(-rT)·N(d₂)
Rho    (ρ) = K·T·e^(-rT)·N(d₂)
```

### 3. Monte Carlo — Box-Muller Gaussian Sampling

```
U₁, U₂ ~ Uniform(0,1)
Z = √(-2·ln(U₁)) · cos(2π·U₂)    ← proper N(0,1)

Sᵢ₊₁ = Sᵢ · exp((μ - σ²/2)·dt + σ·√dt·Z)
```

### 4. True POP via CDF

```
POP = P(Sᵀ > BE) = 1 - Φ((ln(BE/S₀) - (μ-σ²/2)T) / (σ√T))
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/optimize` | Core optimizer — returns ranked strategies |
| GET | `/api/v1/chain/{symbol}` | Live option chain |
| POST | `/api/v1/greeks` | Black-Scholes Greeks for any option |
| POST | `/api/v1/simulate` | Monte Carlo GBM simulation |
| GET | `/api/v1/iv/{symbol}` | IV rank, percentile, surface |
| POST | `/api/v1/stress` | Scenario stress test |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/login` | JWT auth |

---

## Quick Start

> **Python version requirement:** Use **Python 3.11** (recommended). Python 3.14 currently fails on some pinned dependencies (for example `pydantic-core==2.18.2`) because prebuilt wheels may be unavailable.

```bash
# Clone and setup
git clone https://github.com/yourorg/quantedge
cd quantedge
chmod +x scripts/setup.sh
./scripts/setup.sh

# Backend (separate terminal)
cd backend
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev

# Full stack via Docker
docker-compose -f docker/docker-compose.yml up
```

Visit `http://localhost:5173` for the app.
API docs at `http://localhost:8000/docs`.

### Windows note (PowerShell): `uvicorn` not recognized

If PowerShell says `uvicorn` is not recognized, run backend commands through Python so they use your virtual environment packages. Also make sure you are creating the venv with **Python 3.11** (not 3.14):

```powershell
cd backend
py -0p                        # list installed Python versions
py -3.11 -m venv .venv        # create venv using Python 3.11
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

If `py -3.11` fails, install Python 3.11 from python.org and rerun the steps.

If activation is blocked by execution policy, run once in PowerShell (as your user):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## Environment Variables

```env
# Backend (.env)
NSE_BASE_URL=https://www.nseindia.com
UPSTOX_API_KEY=your_key
UPSTOX_SECRET=your_secret
ZERODHA_API_KEY=your_key
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/quantedge
JWT_SECRET=your_secret_256bit
RAZORPAY_KEY_ID=your_key
RAZORPAY_SECRET=your_secret
ENVIRONMENT=development

# Frontend (.env)
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, uvicorn |
| Math | NumPy, SciPy, pandas |
| Cache | Redis 7 |
| Database | PostgreSQL 15 |
| Frontend | React 18, Vite, Zustand |
| Charts | D3.js, Recharts |
| Auth | JWT (python-jose) |
| Payments | Razorpay |
| Deploy | Docker, AWS ECS / GCP Cloud Run |

---

## Legal

Educational and analytical tool only. Not investment advice.
SEBI compliance required before commercial launch.
