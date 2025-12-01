#!/bin/bash

# Bijmantra Setup Script
# Automated setup for development environment

set -e

echo "🌱 Bijmantra Setup Script"
echo "=========================="
echo ""

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Please install Podman first."
    echo "   Visit: https://podman.io/getting-started/installation"
    exit 1
fi

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✓ Prerequisites check passed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo "⚠️  Please review and update .env file with your settings"
    echo ""
fi

# Start infrastructure
echo "🚀 Starting infrastructure (PostgreSQL, Redis, MinIO)..."
podman-compose up -d postgres redis minio

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Backend setup
echo ""
echo "🐍 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "   Running database migrations..."
alembic upgrade head

echo "   Seeding database..."
python -m app.db_seed

cd ..

# Frontend setup
echo ""
echo "⚛️  Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
fi

cd ..

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📚 Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "4. Default credentials:"
echo "   - Email: admin@bijmantra.org"
echo "   - Password: admin123"
echo ""
echo "   ⚠️  CHANGE THESE IN PRODUCTION!"
echo ""
echo "Or use Make commands:"
echo "   make dev-backend    # Start backend"
echo "   make dev-frontend   # Start frontend"
echo ""
