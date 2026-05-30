# Compute Workers - Quick Start Guide

## What are Compute Workers?

Compute workers are separate processes that handle heavy computational operations, isolated from API servers to prevent compute crashes from affecting API availability.

## Worker Types

- **Light Workers:** Fast Python operations (< 30s)
- **Heavy Workers:** Long-running Rust/Fortran operations (> 30s)
- **GPU Workers:** GPU-accelerated operations (optional)

## Quick Start

### 1. Start Workers with Docker (Recommended)

```bash
# Start all services including workers
docker compose -f compose.yaml -f compose.workers.yaml up -d

# View worker logs
docker compose -f compose.workers.yaml logs -f

# Stop workers
docker compose -f compose.workers.yaml down
```

### 2. Start Workers with Scripts (Development)

```bash
# Start all workers
./backend/scripts/start_workers.sh all

# Start specific worker type
./backend/scripts/start_workers.sh light
./backend/scripts/start_workers.sh heavy

# Stop all workers
./backend/scripts/stop_workers.sh
```

### 3. Monitor Workers

```bash
# Real-time dashboard
python backend/scripts/monitor_workers.py

# API endpoint
curl http://localhost:8000/api/v2/workers/health

# Worker statistics
curl http://localhost:8000/api/v2/workers/stats
```

## Configuration

### Environment Variables

```bash
# Light Worker
WORKER_ID=light-worker-1
MAX_CONCURRENT=10

# Heavy Worker
WORKER_ID=heavy-worker-1
MAX_CONCURRENT=2

# GPU Worker
WORKER_ID=gpu-worker-1
MAX_CONCURRENT=1
GPU_ID=0
```

### Docker Compose

Edit `compose.workers.yaml` to adjust:
- Number of workers
- Resource limits
- Environment variables

## Scaling

### Add More Workers

```yaml
# In compose.workers.yaml
light-worker-3:
  # Copy light-worker-1 configuration
  environment:
    - WORKER_ID=light-worker-3
```

### Increase Resources

```yaml
# In compose.workers.yaml
heavy-worker-1:
  deploy:
    resources:
      limits:
        memory: 8G
        cpus: '8'
```

## Troubleshooting

### Workers Not Starting

1. Check logs:
```bash
docker compose -f compose.workers.yaml logs light-worker-1
```

2. Verify Redis is running:
```bash
docker compose ps redis
```

### High Queue Depth

1. Check queue statistics:
```bash
curl http://localhost:8000/api/v2/workers/stats
```

2. Add more workers or increase concurrency

### Worker Crashes

1. Check worker logs
2. Check resource usage: `docker stats`
3. Increase resource limits

## Documentation

For detailed documentation, see:
- [Worker Deployment Guide](docs/WORKER_DEPLOYMENT.md)
- [Task 6.3 Summary](TASK_6.3_SUMMARY.md)
- [Compute Interface Pattern](docs/COMPUTE_INTERFACE_PATTERN.md)

## API Endpoints

- `GET /api/v2/workers/health` - Worker health status
- `GET /api/v2/workers/stats` - Worker statistics
- `GET /api/v2/workers/queue/{type}` - Queue depth
- `GET /api/v2/workers/worker/{id}` - Worker details

## Production Recommendations

### Small Deployment (< 100 users)
- 2 light workers
- 1 heavy worker

### Medium Deployment (100-1000 users)
- 4 light workers
- 2 heavy workers
- 1 GPU worker (optional)

### Large Deployment (> 1000 users)
- 8+ light workers
- 4+ heavy workers
- 2+ GPU workers

## Architecture

```
API Servers → Redis Queue → Compute Workers
                              ├─ Light Workers
                              ├─ Heavy Workers
                              └─ GPU Workers
```

## Next Steps

1. Deploy workers in your environment
2. Monitor worker health and queue depth
3. Adjust worker counts based on load
4. Set up alerting for worker issues
