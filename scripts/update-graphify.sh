#!/usr/bin/env bash
set -e

echo "🔄 Updating all graphify knowledge graphs..."
echo ""

# Root analysis
echo "📊 [1/3] Updating root analysis..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '/opt/homebrew/lib/python3.14/site-packages')
import graphify.export
graphify.export.to_html = lambda *args, **kwargs: None  # skip HTML generation
from graphify.watch import _rebuild_code
_rebuild_code(Path('.'))
"
echo "✅ Root analysis complete"
echo ""

# Frontend analysis
echo "📊 [2/3] Updating frontend analysis..."
cd frontend
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '/opt/homebrew/lib/python3.14/site-packages')
import graphify.export
graphify.export.to_html = lambda *args, **kwargs: None  # skip HTML generation
from graphify.watch import _rebuild_code
_rebuild_code(Path('.'))
"
cd ..
echo "✅ Frontend analysis complete"
echo ""

# Backend analysis
echo "📊 [3/3] Updating backend analysis..."
cd backend
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '/opt/homebrew/lib/python3.14/site-packages')
import graphify.export
graphify.export.to_html = lambda *args, **kwargs: None  # skip HTML generation
from graphify.watch import _rebuild_code
_rebuild_code(Path('.'))
"
cd ..
echo "✅ Backend analysis complete"
echo ""

echo "🎉 All graphify analyses updated successfully!"
echo ""
echo "Updated locations:"
echo "  - graphify-out/GRAPH_REPORT.md"
echo "  - frontend/graphify-out/GRAPH_REPORT.md"
echo "  - backend/graphify-out/GRAPH_REPORT.md"
