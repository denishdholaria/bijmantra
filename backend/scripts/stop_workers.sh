#!/bin/bash
# Stop Bijmantra Compute Workers
# Usage: ./scripts/stop_workers.sh

set -e

echo "Stopping Bijmantra Compute Workers..."

# Find and kill all worker processes
pkill -f "app.workers.light_worker" || true
pkill -f "app.workers.heavy_worker" || true
pkill -f "app.workers.gpu_worker" || true

echo "All workers stopped successfully!"
