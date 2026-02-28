#!/bin/bash
# QuantEdge — One-command dev setup
# Usage: chmod +x scripts/setup.sh && ./scripts/setup.sh

set -e
echo "🚀 Setting up QuantEdge development environment..."

# ── Python backend ──────────────────────────────────────────────────────────
echo ""
echo "📦 Installing Python dependencies..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "✅ Python deps installed."

# Create .env if not exists
if [ ! -f ".env" ]; then
  cat > .env << 'ENVEOF'
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/quantedge
JWT_SECRET=dev-secret-change-in-production-use-256-bit-key
RAZORPAY_KEY_ID=
RAZORPAY_SECRET=
UPSTOX_API_KEY=
UPSTOX_SECRET=
ZERODHA_API_KEY=
ZERODHA_SECRET=
TELEGRAM_BOT_TOKEN=
ENVEOF
  echo "✅ Created backend/.env (configure API keys)"
fi

cd ..

# ── Node frontend ────────────────────────────────────────────────────────────
echo ""
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
echo "✅ Node deps installed."

if [ ! -f ".env" ]; then
  cat > .env << 'ENVEOF'
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
ENVEOF
  echo "✅ Created frontend/.env"
fi

cd ..

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo ""
echo "  Terminal 1 (Backend):"
echo "  cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "  Terminal 2 (Frontend):"
echo "  cd frontend && npm run dev"
echo ""
echo "  Or full stack with Docker:"
echo "  docker-compose -f docker/docker-compose.yml up"
echo ""
echo "  API docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:5173"
echo ""
echo "  Run backend tests:"
echo "  cd backend && source venv/bin/activate && pytest tests/backend/ -v"
