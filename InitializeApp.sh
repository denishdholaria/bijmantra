#!/bin/bash

# InitializeApp.sh - One-click setup for Bijmantra
# Prepares the environment so you can just press "Play" in Podman Desktop.

set -e

# Colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🌱 Bijmantra Initialization"
echo "==========================="
echo ""

# 1. Check Prerequisites
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
    # compound command for podman-compose or podman compose
    if command -v podman-compose &> /dev/null; then
        COMPOSE_CMD="podman-compose"
    elif podman compose version &> /dev/null; then
        COMPOSE_CMD="podman compose"
    else
        echo "❌ Podman Compose is missing. Please install it."
        exit 1
    fi
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
    COMPOSE_CMD="docker compose"
else
    echo "❌ Neither Podman nor Docker found. Please install Podman Desktop."
    exit 1
fi

echo -e "✓ Using ${GREEN}$CONTAINER_CMD${NC} and ${GREEN}$COMPOSE_CMD${NC}"

# 2. Prepare Environment
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
else
    echo "✓ .env file exists"
fi

# 3. Build & Pull Images
echo "🔨 Building and pulling containers (this may take a while)..."
$COMPOSE_CMD -f compose.full.yaml build
$COMPOSE_CMD -f compose.full.yaml pull

# 4. Database Setup & Migrations
echo "🐘 Starting database for initialization..."
$COMPOSE_CMD -f compose.full.yaml up -d postgres redis

echo "⏳ Waiting for PostgreSQL to be ready..."
# Simple wait loop
for i in {1..30}; do
    if $CONTAINER_CMD exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db &> /dev/null; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    sleep 2
done

echo "🔄 Running database migrations..."
$COMPOSE_CMD -f compose.full.yaml run --rm backend alembic upgrade head

echo "🌱 Seeding database (if needed)..."
# Optional: Seed data. Failures ignored in case data exists.
$COMPOSE_CMD -f compose.full.yaml run --rm backend python app/db_seed.py || true

# 5. Cleanup
echo "🛑 Stopping initialization services..."
$COMPOSE_CMD -f compose.full.yaml down

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "===================================================="
echo "1. Open Podman Desktop"
echo "2. Find the 'bijmantra' (or 'compose.full') container group"
echo "3. Press the ▶️ (Play) button to start the app"
echo "===================================================="
