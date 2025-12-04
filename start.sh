#!/bin/bash

# Bijmantra - Single Command Startup Script
# Usage: ./start.sh

set -e

echo "🌱 Starting Bijmantra..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check for podman or docker
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo "❌ Error: Neither podman nor docker found. Please install one."
    exit 1
fi

echo -e "${YELLOW}Using: $CONTAINER_CMD${NC}"
echo ""

# 1. Build PostgreSQL image if needed (includes PostGIS + pgvector)
if ! $CONTAINER_CMD image exists bijmantra-postgres:latest 2>/dev/null; then
    echo "🔨 Building PostgreSQL image with PostGIS + pgvector..."
    $CONTAINER_CMD compose build postgres
fi

# 2. Start Infrastructure Services
echo "📦 Starting PostgreSQL, Redis, and Meilisearch..."
$CONTAINER_CMD compose up -d postgres redis meilisearch
sleep 3

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
for i in {1..30}; do
    if $CONTAINER_CMD exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is ready (with PostGIS + pgvector)${NC}"
        break
    fi
    sleep 1
done

# 3. Run migrations
echo ""
echo "🔄 Running database migrations..."
cd backend
source venv/bin/activate
export POSTGRES_SERVER=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=bijmantra_user
export POSTGRES_PASSWORD=changeme_in_production
export POSTGRES_DB=bijmantra_db

alembic upgrade head 2>/dev/null || alembic stamp head 2>/dev/null || true
PYTHONPATH=. python app/db_seed.py 2>/dev/null || true

# Initialize vector store extension
echo "🧠 Initializing vector store..."
$CONTAINER_CMD exec bijmantra-postgres psql -U bijmantra_user -d bijmantra_db -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

# 4. Start Backend
echo ""
echo "🚀 Starting Backend API..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
sleep 2

# 5. Start Frontend
echo ""
echo "🎨 Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🌱 Bijmantra is running!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo "  Frontend:     http://localhost:5173"
echo "  Backend:      http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Meilisearch:  http://localhost:7700"
echo ""
echo "  🪷 Veena AI:   Click the lotus button in bottom-right"
echo "  🔍 Vector:     /api/v2/vector/search/simple?q=your+query"
echo ""
echo "  Login: admin@bijmantra.org / admin123"
echo ""
echo "  Press ⌘K to open Command Palette"
echo "  Press Ctrl+C to stop all services"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Stopping Bijmantra..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    $CONTAINER_CMD compose down
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait
