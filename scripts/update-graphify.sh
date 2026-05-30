#!/usr/bin/env bash
set -e

echo "🔄 Updating all graphify knowledge graphs..."
echo ""

# Root analysis
echo "📊 [1/3] Updating root analysis..."
uv run python -m graphify update .
echo "✅ Root analysis complete"
echo ""

# Frontend analysis
echo "📊 [2/3] Updating frontend analysis..."
uv run python -m graphify update frontend
echo "✅ Frontend analysis complete"
echo ""

# Backend analysis
echo "📊 [3/3] Updating backend analysis..."
uv run python -m graphify update backend
echo "✅ Backend analysis complete"
echo ""

echo "🎉 All graphify analyses updated successfully!"
echo ""
echo "Updated locations:"
echo "  - graphify-out/GRAPH_REPORT.md"
echo "  - frontend/graphify-out/GRAPH_REPORT.md"
echo "  - backend/graphify-out/GRAPH_REPORT.md"
