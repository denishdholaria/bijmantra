#!/bin/bash
# Start Bijmantra Compute Workers
# Usage: ./scripts/start_workers.sh [worker_type]
#
# worker_type: light, heavy, gpu, or all (default: all)

set -e

WORKER_TYPE=${1:-all}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

cd "$BACKEND_DIR"

echo "Starting Bijmantra Compute Workers..."
echo "Worker Type: $WORKER_TYPE"
echo ""

# Function to start a worker
start_worker() {
    local worker_type=$1
    local worker_id=$2
    local max_concurrent=$3
    
    echo "Starting $worker_type worker: $worker_id"
    
    case $worker_type in
        light)
            WORKER_ID=$worker_id MAX_CONCURRENT=$max_concurrent python -m app.workers.light_worker &
            ;;
        heavy)
            WORKER_ID=$worker_id MAX_CONCURRENT=$max_concurrent python -m app.workers.heavy_worker &
            ;;
        gpu)
            WORKER_ID=$worker_id MAX_CONCURRENT=$max_concurrent GPU_ID=0 python -m app.workers.gpu_worker &
            ;;
        *)
            echo "Unknown worker type: $worker_type"
            exit 1
            ;;
    esac
    
    echo "Started $worker_type worker: $worker_id (PID: $!)"
}

# Start workers based on type
case $WORKER_TYPE in
    light)
        start_worker light light-worker-1 10
        start_worker light light-worker-2 10
        ;;
    heavy)
        start_worker heavy heavy-worker-1 2
        ;;
    gpu)
        start_worker gpu gpu-worker-1 1
        ;;
    all)
        echo "Starting all workers..."
        start_worker light light-worker-1 10
        start_worker light light-worker-2 10
        start_worker heavy heavy-worker-1 2
        # Uncomment to start GPU worker
        # start_worker gpu gpu-worker-1 1
        ;;
    *)
        echo "Invalid worker type: $WORKER_TYPE"
        echo "Valid types: light, heavy, gpu, all"
        exit 1
        ;;
esac

echo ""
echo "Workers started successfully!"
echo "Monitor workers at: http://localhost:8000/api/v2/workers/health"
echo ""
echo "To stop workers, run: ./scripts/stop_workers.sh"
