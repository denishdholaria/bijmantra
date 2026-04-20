# Compute Worker Deployment Guide

## Overview

Bijmantra uses separate compute workers to isolate heavy computational operations from API servers. This prevents compute crashes from affecting API availability and allows independent scaling of compute resources.

## Worker Types

### 1. Light Compute Workers
**Purpose:** Fast Python-only operations (< 30 seconds)

**Characteristics:**
- Python-only (no Rust/Fortran)
- High concurrency (10 concurrent tasks per worker)
- Quick turnaround
- Low resource requirements

**Examples:**
- Data validation
- Simple statistics
- Quick transformations
- API data processing

**Deployment:**
- Deploy 2-4 workers for high availability
- 256-512MB RAM per worker
- 1 CPU core per worker

### 2. Heavy Compute Workers
**Purpose:** Long-running Rust/Fortran operations (> 30 seconds)

**Characteristics:**
- Rust/Fortran compute engines
- Low concurrency (2 concurrent tasks per worker)
- Resource-intensive
- Long-running operations

**Examples:**
- BLUP/GBLUP calculations
- GWAS analysis
- Genomic relationship matrices
- Large matrix operations
- HPC solver calls

**Deployment:**
- Deploy 1-2 workers initially
- 2-4GB RAM per worker
- 2-4 CPU cores per worker
- Scale based on queue depth

### 3. GPU Compute Workers
**Purpose:** GPU-accelerated operations (WebGPU/CUDA)

**Characteristics:**
- GPU-accelerated (CUDA/WebGPU)
- Very low concurrency (1 task per worker)
- Specialized hardware required
- High throughput for parallel operations

**Examples:**
- Deep learning inference
- Large-scale matrix operations
- Image processing
- Genomic sequence alignment
- Neural network training

**Deployment:**
- Deploy 1 worker per GPU
- 4-8GB RAM per worker
- Requires NVIDIA GPU with CUDA support
- Optional (only if GPU available)

## Deployment Methods

### Method 1: Docker Compose (Recommended)

#### Start All Workers
```bash
docker compose -f compose.yaml -f compose.workers.yaml up -d
```

#### Start Specific Worker Types
```bash
# Light workers only
docker compose -f compose.yaml -f compose.workers.yaml up -d light-worker-1 light-worker-2

# Heavy workers only
docker compose -f compose.yaml -f compose.workers.yaml up -d heavy-worker-1

# GPU workers only (if GPU available)
docker compose -f compose.yaml -f compose.workers.yaml up -d gpu-worker-1
```

#### Stop Workers
```bash
docker compose -f compose.workers.yaml down
```

#### View Worker Logs
```bash
# All workers
docker compose -f compose.workers.yaml logs -f

# Specific worker
docker compose -f compose.workers.yaml logs -f light-worker-1
```

### Method 2: Shell Scripts (Development)

#### Start Workers
```bash
# Start all workers
./backend/scripts/start_workers.sh all

# Start specific worker type
./backend/scripts/start_workers.sh light
./backend/scripts/start_workers.sh heavy
./backend/scripts/start_workers.sh gpu
```

#### Stop Workers
```bash
./backend/scripts/stop_workers.sh
```

### Method 3: Python Directly (Testing)

#### Light Worker
```bash
cd backend
python -m app.workers.light_worker
```

#### Heavy Worker
```bash
cd backend
python -m app.workers.heavy_worker
```

#### GPU Worker
```bash
cd backend
CUDA_VISIBLE_DEVICES=0 python -m app.workers.gpu_worker
```

## Monitoring

### Real-time Dashboard
```bash
cd backend
python scripts/monitor_workers.py
```

This displays:
- Active workers by type
- Worker health status
- Queue depth by type
- Processing statistics
- Error rates

### API Endpoints

#### Worker Health
```bash
curl http://localhost:8000/api/v2/workers/health
```

Returns:
- Active workers
- Queue statistics
- Worker health status

#### Worker Statistics
```bash
curl http://localhost:8000/api/v2/workers/stats
```

Returns:
- Worker counts by type
- Queue depth by type
- Processing rates
- Error rates

#### Queue Depth
```bash
curl http://localhost:8000/api/v2/workers/queue/light
curl http://localhost:8000/api/v2/workers/queue/heavy
curl http://localhost:8000/api/v2/workers/queue/gpu
```

#### Worker Details
```bash
curl http://localhost:8000/api/v2/workers/worker/light-worker-1
```

## Configuration

### Environment Variables

#### Light Worker
```bash
WORKER_ID=light-worker-1      # Unique worker identifier
MAX_CONCURRENT=10              # Max concurrent tasks
LOG_LEVEL=INFO                 # Logging level
```

#### Heavy Worker
```bash
WORKER_ID=heavy-worker-1       # Unique worker identifier
MAX_CONCURRENT=2               # Max concurrent tasks
LOG_LEVEL=INFO                 # Logging level
```

#### GPU Worker
```bash
WORKER_ID=gpu-worker-1         # Unique worker identifier
MAX_CONCURRENT=1               # Max concurrent tasks
GPU_ID=0                       # GPU device ID
CUDA_VISIBLE_DEVICES=0         # CUDA device visibility
LOG_LEVEL=INFO                 # Logging level
```

### Docker Compose Configuration

Edit `compose.workers.yaml` to adjust:
- Number of workers
- Resource limits (memory, CPU)
- Environment variables
- GPU configuration

Example:
```yaml
light-worker-1:
  environment:
    - MAX_CONCURRENT=20  # Increase concurrency
  deploy:
    resources:
      limits:
        memory: 1G       # Increase memory
```

## Scaling

### Horizontal Scaling

#### Add More Light Workers
```yaml
# In compose.workers.yaml
light-worker-3:
  # Copy light-worker-1 configuration
  environment:
    - WORKER_ID=light-worker-3
```

#### Add More Heavy Workers
```yaml
# In compose.workers.yaml
heavy-worker-2:
  # Copy heavy-worker-1 configuration
  environment:
    - WORKER_ID=heavy-worker-2
```

### Vertical Scaling

#### Increase Worker Resources
```yaml
# In compose.workers.yaml
heavy-worker-1:
  deploy:
    resources:
      limits:
        memory: 8G      # Increase from 4G
        cpus: '8'       # Increase from 4
```

#### Increase Concurrency
```yaml
# In compose.workers.yaml
light-worker-1:
  environment:
    - MAX_CONCURRENT=20  # Increase from 10
```

## Health Checks

Workers automatically register themselves in Redis with a 60-second TTL. If a worker dies, it will be automatically removed from the registry after 60 seconds.

### Manual Health Check
```bash
# Check if workers are registered
redis-cli KEYS "worker:*"

# Get worker details
redis-cli GET "worker:light:light-worker-1"
```

## Troubleshooting

### Worker Not Starting

1. Check logs:
```bash
docker compose -f compose.workers.yaml logs light-worker-1
```

2. Verify Redis connection:
```bash
docker compose ps redis
```

3. Check environment variables:
```bash
docker compose -f compose.workers.yaml config
```

### High Queue Depth

1. Check queue statistics:
```bash
curl http://localhost:8000/api/v2/workers/stats
```

2. Add more workers:
```bash
# Edit compose.workers.yaml to add more workers
docker compose -f compose.workers.yaml up -d --scale light-worker=4
```

3. Increase worker concurrency:
```yaml
# In compose.workers.yaml
light-worker-1:
  environment:
    - MAX_CONCURRENT=20
```

### Worker Crashes

1. Check worker logs:
```bash
docker compose -f compose.workers.yaml logs --tail=100 heavy-worker-1
```

2. Check resource usage:
```bash
docker stats
```

3. Increase resource limits:
```yaml
# In compose.workers.yaml
heavy-worker-1:
  deploy:
    resources:
      limits:
        memory: 8G
```

### GPU Worker Not Using GPU

1. Verify GPU availability:
```bash
nvidia-smi
```

2. Check CUDA installation:
```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-runtime-ubuntu22.04 nvidia-smi
```

3. Verify GPU configuration in compose file:
```yaml
gpu-worker-1:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## Production Deployment

### Recommended Configuration

#### Small Deployment (< 100 users)
- 2 light workers (10 concurrent each)
- 1 heavy worker (2 concurrent)
- No GPU worker

#### Medium Deployment (100-1000 users)
- 4 light workers (10 concurrent each)
- 2 heavy workers (2 concurrent each)
- 1 GPU worker (optional)

#### Large Deployment (> 1000 users)
- 8+ light workers (10 concurrent each)
- 4+ heavy workers (2 concurrent each)
- 2+ GPU workers (if available)

### Monitoring and Alerting

Set up alerts for:
- Worker health (workers not responding)
- High queue depth (> 100 pending tasks)
- High error rate (> 5% failed tasks)
- Resource exhaustion (memory/CPU limits)

### Backup and Recovery

Workers are stateless and can be restarted at any time. Jobs in progress will be retried automatically.

To gracefully restart workers:
```bash
# Stop workers
docker compose -f compose.workers.yaml stop

# Wait for jobs to complete (check queue depth)
curl http://localhost:8000/api/v2/workers/stats

# Start workers
docker compose -f compose.workers.yaml start
```

## Architecture

```
┌─────────────────┐
│   API Servers   │
│  (FastAPI)      │
└────────┬────────┘
         │
         │ Enqueue Jobs
         ▼
┌─────────────────┐
│   Redis Queue   │
│  (Job Queue)    │
└────────┬────────┘
         │
         │ Workers Poll
         ▼
┌─────────────────────────────────────────┐
│           Compute Workers               │
├─────────────┬─────────────┬─────────────┤
│   Light     │   Heavy     │    GPU      │
│  Workers    │  Workers    │  Workers    │
│             │             │             │
│ Python-only │ Rust/Fortran│ CUDA/WebGPU │
│ < 30s       │ > 30s       │ Specialized │
│ High Conc.  │ Low Conc.   │ Very Low    │
└─────────────┴─────────────┴─────────────┘
```

## Integration with Compute Modules

Workers automatically process jobs from domain compute modules:

- `app/modules/breeding/compute/` → Heavy workers
- `app/modules/genomics/compute/` → Heavy workers
- `app/modules/phenotyping/compute/` → Light/Heavy workers

Jobs are routed to appropriate workers based on `ComputeType`:
- `ComputeType.LIGHT_PYTHON` → Light workers
- `ComputeType.HEAVY_COMPUTE` → Heavy workers
- `ComputeType.GPU_COMPUTE` → GPU workers

## References

- [Task Queue Service](../app/services/task_queue.py)
- [Compute Interface Pattern](./COMPUTE_INTERFACE_PATTERN.md)
- [Compute Interfaces Documentation](./compute_interfaces.md)
- [Architecture Lane README](../../.github/docs/architecture/README.md)
