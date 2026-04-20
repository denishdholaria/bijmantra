#!/bin/bash

# denish.sh - Developer script to start BijMantra app
# Usage: ./denish.sh

set -e

echo "🚀 Starting BijMantra development environment..."

# Check startup prerequisites
echo "🔍 Running startup doctor..."
make startup-doctor

# Start database and optional services (PostgreSQL, Redis, MinIO, Meilisearch)
echo "📊 Starting database and services..."
make dev-all &
DB_PID=$!

# Wait for services to be ready
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
make db-migrate

# Check migration health
echo "🔍 Running migration doctor..."
make migration-doctor

# Run linting and formatting
echo "🧹 Running lint and format..."
make lint && make format

# Start backend development server
echo "🔧 Starting backend server..."
make dev-backend &
BACKEND_PID=$!

# Start frontend development server
echo "🌐 Starting frontend server..."
make dev-frontend &
FRONTEND_PID=$!

echo "✅ BijMantra app started successfully!"
echo "📍 Backend: http://localhost:8000 (FastAPI)"
echo "📍 Frontend: http://localhost:5173 (Vite)"
echo "📍 Admin board: http://localhost:8000/admin/developer/master-board"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo '🛑 Stopping services...'; kill $DB_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait