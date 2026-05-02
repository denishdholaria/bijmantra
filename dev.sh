#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
# dev.sh — Single entry point for BijMantra development
#
# Usage:
#   ./dev.sh                Start PostgreSQL + backend + frontend
#   ./dev.sh --all          Start all infra (Redis, MinIO, Meilisearch too)
#   ./dev.sh --minimal      Start PostgreSQL only (no backend/frontend)
#   ./dev.sh --stop         Stop everything
#   ./dev.sh --setup        First-time setup (build images, migrate, seed)
#   ./dev.sh --status       Show what's running
# ─────────────────────────────────────────────────────────────────────
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# ── Container runtime ────────────────────────────────────────────────
if [ -x "/opt/podman/bin/podman" ]; then
    RUNTIME="/opt/podman/bin/podman"
elif command -v podman &>/dev/null; then
    RUNTIME="podman"
elif command -v docker &>/dev/null; then
    RUNTIME="docker"
else
    echo "❌ Neither Podman nor Docker found."
    exit 1
fi
COMPOSE="$RUNTIME compose"

# ── Colors ───────────────────────────────────────────────────────────
G='\033[0;32m' Y='\033[1;33m' R='\033[0;31m' N='\033[0m'

# ── Parse args ───────────────────────────────────────────────────────
MODE="dev"
for arg in "$@"; do
    case "$arg" in
        --all)      MODE="all" ;;
        --minimal)  MODE="minimal" ;;
        --chloe) MODE="chloe" ;;
        --stop)     MODE="stop" ;;
        --setup)    MODE="setup" ;;
        --status)   MODE="status" ;;
        --help|-h)  MODE="help" ;;
    esac
done

# ── Help ─────────────────────────────────────────────────────────────
if [ "$MODE" = "help" ]; then
    echo "BijMantra Development Script"
    echo ""
    echo "Usage: ./dev.sh [option]"
    echo ""
    echo "Options:"
    echo "  (none)      Start PostgreSQL + backend + frontend"
    echo "  --all       Start all infra (+ Redis, MinIO, Meilisearch, BeingBijmantra)"
    echo "  --chloe  Start all infra + Chloe agent runtime"
    echo "  --minimal   Start PostgreSQL only"
    echo "  --stop      Stop all BijMantra containers"
    echo "  --setup     First-time setup (build, migrate, seed, install)"
    echo "  --status    Show running containers"
    echo ""
    echo "Services:"
    echo "  Frontend    http://localhost:5173"
    echo "  Backend     http://localhost:8000"
    echo "  API Docs    http://localhost:8000/docs"
    echo "  PostgreSQL  localhost:5432"
    echo "  Redis       localhost:6379   (--all)"
    echo "  MinIO       localhost:9001   (--all)"
    echo "  Meilisearch localhost:7700   (--all)"
    exit 0
fi

# ── Stop ─────────────────────────────────────────────────────────────
if [ "$MODE" = "stop" ]; then
    echo "🛑 Stopping BijMantra..."
    $COMPOSE --profile infra --profile tools --profile beingbijmantra --profile chloe down 2>/dev/null || true
    $COMPOSE down 2>/dev/null || true
    echo -e "${G}✓ All BijMantra services stopped${N}"
    exit 0
fi

# ── Status ───────────────────────────────────────────────────────────
if [ "$MODE" = "status" ]; then
    echo "BijMantra containers:"
    $RUNTIME ps --filter "name=bijmantra" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || \
    $RUNTIME ps --filter "name=bijmantra" 2>/dev/null
    exit 0
fi

# ── Setup (first-time) ──────────────────────────────────────────────
if [ "$MODE" = "setup" ]; then
    echo "🌱 BijMantra First-Time Setup"
    echo "=============================="
    echo ""

    # Build PostgreSQL image
    echo "🔨 Building PostgreSQL image (PostGIS + pgvector)..."
    $COMPOSE build postgres

    # Start PostgreSQL
    echo "📦 Starting PostgreSQL..."
    $COMPOSE up -d postgres
    echo "⏳ Waiting for PostgreSQL..."
    for i in {1..30}; do
        $RUNTIME exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db &>/dev/null && break
        sleep 1
    done
    echo -e "${G}✓ PostgreSQL ready${N}"

    # Backend dependencies
    echo ""
    echo "🐍 Installing backend dependencies..."
    cd backend
    uv sync --extra dev --extra analytics --extra geo
    echo -e "${G}✓ Backend dependencies installed${N}"

    # Migrations
    echo "🗄️  Running migrations..."
    uv run alembic upgrade head
    echo -e "${G}✓ Migrations applied${N}"

    # Extension verification
    echo "🔌 Verifying PostgreSQL extensions..."
    REQUIRED_EXTENSIONS="timescaledb vector postgis pg_trgm uuid-ossp pgcrypto pgaudit ltree"
    MISSING=""
    for ext in $REQUIRED_EXTENSIONS; do
        result=$($RUNTIME exec bijmantra-postgres psql -U bijmantra_user -d bijmantra_db -tAc "SELECT extname FROM pg_extension WHERE extname = '$ext';" 2>/dev/null)
        if [ -z "$result" ]; then
            MISSING="$MISSING $ext"
        fi
    done
    if [ -n "$MISSING" ]; then
        echo -e "${Y}⚠️  Missing extensions:$MISSING${N}"
        echo "   Rebuild the postgres image: $COMPOSE build --no-cache postgres"
    else
        echo -e "${G}✓ All 8 extensions loaded: $REQUIRED_EXTENSIONS${N}"
    fi

    # Seed
    echo "🌱 Seeding demo data..."
    uv run python -m app.db.seed --env=dev
    echo -e "${G}✓ Database seeded${N}"
    cd ..

    # Frontend dependencies
    echo ""
    echo "⚛️  Installing frontend dependencies..."
    cd frontend
    bun install
    cd ..
    echo -e "${G}✓ Frontend dependencies installed${N}"

    echo ""
    echo -e "${G}✅ Setup complete! Run ./dev.sh to start developing.${N}"
    exit 0
fi

# ── Start infrastructure ─────────────────────────────────────────────
echo "🌱 Starting BijMantra..."
echo ""

if [ "$MODE" = "all" ]; then
    echo "📦 Starting PostgreSQL + Redis + MinIO + Meilisearch + BeingBijmantra..."
    $COMPOSE --profile infra --profile beingbijmantra up -d 2>&1 | grep -v "^Error:" | grep -v "cannot remove container" | grep -v "network is being used" | grep -v "WARNING: image platform" || true
elif [ "$MODE" = "chloe" ]; then
    echo "📦 Starting all infra + Chloe agent runtime..."
    $COMPOSE --profile infra --profile beingbijmantra --profile chloe up -d 2>&1 | grep -v "^Error:" | grep -v "cannot remove container" | grep -v "network is being used" | grep -v "WARNING: image platform" || true
else
    echo "📦 Starting PostgreSQL..."
    $COMPOSE up -d postgres 2>&1 | grep -v "^Error:" | grep -v "cannot remove container" | grep -v "network is being used" | grep -v "WARNING: image platform" || true
fi

# Wait for PostgreSQL
for i in {1..30}; do
    $RUNTIME exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db &>/dev/null && break
    sleep 1
done
echo -e "${G}✓ PostgreSQL ready${N}"

if [ "$MODE" = "minimal" ]; then
    echo ""
    echo -e "${G}✓ Infrastructure running. Start backend/frontend manually:${N}"
    echo "  cd backend && bash ./start_dev.sh"
    echo "  cd frontend && bun run dev"
    exit 0
fi

# ── Start backend ────────────────────────────────────────────────────
echo ""
echo "🗄️  Running migrations..."
cd backend
uv run alembic upgrade head 2>&1 | tail -3
echo -e "${G}✓ Database up to date${N}"

echo "🚀 Starting backend..."
export POSTGRES_SERVER="${POSTGRES_SERVER:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-bijmantra_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-changeme_in_production}"
export POSTGRES_DB="${POSTGRES_DB:-bijmantra_db}"
export SECRET_KEY=dev_secret_key_for_local_development_only_do_not_use_in_production
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}

echo "   📌 Database: ${POSTGRES_SERVER}:${POSTGRES_PORT}/${POSTGRES_DB}"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# ── Start frontend ───────────────────────────────────────────────────
echo "🎨 Starting frontend..."
cd frontend
bun run dev &
FRONTEND_PID=$!
cd ..

sleep 3

# ── Ready ────────────────────────────────────────────────────────────
echo ""
echo -e "${G}════════════════════════════════════════════${N}"
echo -e "${G}  🌱 BijMantra is running${N}"
echo -e "${G}════════════════════════════════════════════${N}"
echo ""
echo "  Frontend     http://localhost:5173"
echo "  Backend      http://localhost:8000"
echo "  API Docs     http://localhost:8000/docs"
echo "  PostgreSQL   localhost:5432"
if [ "$MODE" = "all" ] || [ "$MODE" = "chloe" ]; then
    echo "  Redis        localhost:6379"
    echo "  MinIO        http://localhost:9001"
    echo "  Meilisearch  http://localhost:7700"
    echo "  SurrealDB    http://localhost:8083  (BeingBijmantra)"
fi
if [ "$MODE" = "chloe" ]; then
    echo "  Chloe GW  http://127.0.0.1:18789"
fi
echo ""
echo "🪷  R.E.E.V.U. AI (Reason · Evidence · Evaluation · Validation · Unit)"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# ── Cleanup on exit ──────────────────────────────────────────────────
cleanup() {
    echo ""
    echo "🛑 Stopping..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${G}✓ Backend and frontend stopped.${N}"
    echo "  Infrastructure containers are still running."
    echo "  Run ./dev.sh --stop to stop everything."
}
trap cleanup SIGINT SIGTERM

wait
