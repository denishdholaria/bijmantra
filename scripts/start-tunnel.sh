#!/bin/bash
# Start BijMantra with Cloudflare Tunnel
# Usage: ./scripts/start-tunnel.sh

set -e

echo "🚀 Starting BijMantra with Cloudflare Tunnel..."
echo ""

# Check if services are already running
check_port() {
    lsof -i :$1 > /dev/null 2>&1
}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Start Backend
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Backend already running on :8000${NC}"
else
    echo "Starting backend..."
    cd backend
    source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
    cd ..
    sleep 2
    echo -e "${GREEN}✅ Backend started on :8000${NC}"
fi

# Start Frontend
if check_port 5173; then
    echo -e "${YELLOW}⚠️  Frontend already running on :5173${NC}"
else
    echo "Starting frontend..."
    cd frontend
    npm run dev &
    cd ..
    sleep 3
    echo -e "${GREEN}✅ Frontend started on :5173${NC}"
fi

# Start Caddy
if check_port 80; then
    echo -e "${YELLOW}⚠️  Caddy already running on :80${NC}"
else
    echo "Starting Caddy..."
    caddy run --config Caddyfile.tunnel &
    sleep 1
    echo -e "${GREEN}✅ Caddy started on :80${NC}"
fi

# Start Tunnel
echo "Starting Cloudflare Tunnel..."
cloudflared tunnel run bijmantra &
sleep 2
echo -e "${GREEN}✅ Tunnel started${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}🌐 BijMantra is now live at:${NC}"
echo ""
echo "   https://s108.bijmantra.org"
echo "   https://s108.bijmantra.org/api/docs"
echo ""
echo "   (Landing page remains at https://bijmantra.org)"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="

# Wait for interrupt
wait
