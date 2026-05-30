# Compute Monitoring Dashboard

## Overview

The Compute Monitoring Dashboard provides real-time observability for the compute layer of BijMantra's architecture. It tracks job execution, worker utilization, queue depth, and alerts based on configurable thresholds.

## Features

### Metrics Tracked

**Job Execution Metrics:**
- Total jobs (pending, running, completed, failed)
- Success/failure rate
- Execution time percentiles (P50, P95, P99)
- Job metrics by compute type (light, heavy, GPU)

**Worker Metrics:**
- Total workers by type
- Active workers
- Worker utilization percentage
- Jobs processed per worker
- Failed jobs per worker

**Queue Metrics:**
- Queue depth by compute type
- Pending jobs
- Running jobs
- Average wait time

**Alerting:**
- Compute job failure rate > 5% (CRITICAL)
- Queue depth > 1000 jobs (WARNING)
- Worker utilization < 20% (WARNING - underutilized)
- Worker utilization > 90% (CRITICAL - overloaded)

## Access

### Web Dashboard

Access the web-based dashboard at:
```
http://localhost:8000/api/v2/monitoring/dashboard
```

The dashboard auto-refreshes every 30 seconds.

### API Endpoints

**Get Complete Dashboard:**
```bash
GET /api/v2/monitoring/compute
```

**Get Job Execution Metrics:**
```bash
GET /api/v2/monitoring/compute/jobs?compute_type=heavy_compute&hours=24
```

**Get Worker Utilization:**
```bash
GET /api/v2/monitoring/compute/workers
```

**Get Queue Depth:**
```bash
GET /api/v2/monitoring/compute/queue
```

**Get Active Alerts:**
```bash
GET /api/v2/monitoring/compute/alerts
```

**Trigger Manual Alert Check:**
```bash
POST /api/v2/monitoring/compute/alerts/check
```

**Get Alert History:**
```bash
GET /api/v2/monitoring/compute/alerts/history?hours=24
```

## CLI Monitoring

For terminal-based monitoring, use the existing worker monitoring script:

```bash
python backend/scripts/monitor_workers.py
```

This provides a real-time CLI dashboard that refreshes every 5 seconds.

## Sentry Integration

The monitoring system integrates with Sentry for error tracking and performance monitoring.

### Compute Job Tracking

All compute jobs are automatically tracked in Sentry with:
- Transaction name: `compute.{job_name}`
- Tags: `compute.job_id`, `compute.type`, `domain`
- Measurements: `compute.execution_time`, `compute.progress`

### Critical Alerts

Critical alerts (failure rate > 5%, worker utilization > 90%) are automatically sent to Sentry with:
- Level: `error`
- Message: Alert details
- Extras: Metric values, thresholds

### Usage in Code

```python
from app.middleware.compute_monitoring import compute_monitor

# Track compute job
with compute_monitor.track_compute_job(
    job_id="abc123",
    job_name="gwas_analysis",
    compute_type=ComputeType.HEAVY_COMPUTE,
    domain="genomics"
):
    result = await run_gwas(data)
```

## Alert Configuration

Alert rules are defined in `backend/app/services/compute_alerting.py`.

### Alert Rules

| Rule ID | Metric | Threshold | Severity | Cooldown |
|---------|--------|-----------|----------|----------|
| `compute_failure_rate_high` | Job failure rate | > 5% | CRITICAL | 30 min |
| `queue_depth_high` | Queue depth | > 1000 | WARNING | 15 min |
| `worker_utilization_low` | Worker utilization | < 20% | WARNING | 60 min |
| `worker_utilization_high` | Worker utilization | > 90% | CRITICAL | 15 min |

### Cooldown Period

Alerts have a cooldown period to prevent alert spam. Once an alert is triggered, it won't trigger again until the cooldown period expires.

## Architecture

### Components

**Monitoring API** (`backend/app/api/v2/monitoring.py`):
- REST API endpoints for metrics and alerts
- Serves web dashboard UI

**Compute Monitoring Middleware** (`backend/app/middleware/compute_monitoring.py`):
- Sentry integration for compute jobs
- Automatic transaction tracking
- Error capture with context

**Compute Alerting Service** (`backend/app/services/compute_alerting.py`):
- Alert rule evaluation
- Threshold checking
- Alert history tracking
- Sentry integration for critical alerts

**Task Queue** (`backend/app/services/task_queue.py`):
- Job execution and tracking
- Queue management
- Worker coordination

**Workers**:
- Light Worker (`backend/app/workers/light_worker.py`) - Python-only, < 30s
- Heavy Worker (`backend/app/workers/heavy_worker.py`) - Rust/Fortran, > 30s
- GPU Worker (future) - WebGPU/CUDA operations

### Data Flow

```
Compute Job Submitted
    ↓
Task Queue (Redis)
    ↓
Worker Picks Up Job
    ↓
Compute Monitor Tracks Execution (Sentry)
    ↓
Job Completes/Fails
    ↓
Metrics Updated in Redis
    ↓
Alert Service Checks Thresholds
    ↓
Alerts Triggered (if needed)
    ↓
Dashboard Displays Metrics
```

## Deployment

### Environment Variables

```bash
# Sentry DSN for error tracking
SENTRY_DSN=https://your-sentry-dsn

# Environment (development, staging, production)
ENVIRONMENT=production
```

### Starting Workers

**Light Worker:**
```bash
python -m app.workers.light_worker
```

**Heavy Worker:**
```bash
python -m app.workers.heavy_worker
```

### Background Alert Checking

The alert checking loop runs automatically in the background. To enable it, add to `main.py` lifespan:

```python
from app.services.compute_alerting import run_alert_check_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(run_alert_check_loop())
    
    yield
    
    # Shutdown
    pass
```

## Monitoring Best Practices

1. **Set up Sentry** - Configure `SENTRY_DSN` for production error tracking
2. **Monitor queue depth** - High queue depth indicates worker capacity issues
3. **Track failure rates** - Investigate when failure rate exceeds 5%
4. **Balance worker utilization** - Aim for 50-80% utilization
5. **Review alert history** - Identify patterns in alert triggers
6. **Scale workers** - Add workers when utilization consistently exceeds 80%

## Troubleshooting

### High Failure Rate

1. Check Sentry for error details
2. Review failed job logs
3. Verify compute engine availability (Rust/Fortran)
4. Check resource constraints (memory, CPU)

### High Queue Depth

1. Check worker status (are workers running?)
2. Verify Redis connectivity
3. Scale up workers if needed
4. Review job submission rate

### Low Worker Utilization

1. Check if jobs are being submitted
2. Verify task queue is running
3. Review worker logs for errors
4. Check Redis connectivity

### Workers Not Registering

1. Verify Redis is running and accessible
2. Check worker logs for connection errors
3. Ensure workers are started with correct configuration
4. Verify Redis TTL settings (workers auto-expire after 60s)

## Future Enhancements

- [ ] Alert resolution tracking
- [ ] Historical metrics storage (time-series database)
- [ ] Custom alert rules via API
- [ ] Slack/email alert notifications
- [ ] Grafana dashboard integration
- [ ] OpenTelemetry support
- [ ] Per-domain compute metrics
- [ ] Job execution time predictions
- [ ] Automatic worker scaling recommendations
