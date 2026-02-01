# 📈 Scaling Strategy

> **Purpose:** Growth planning and scaling roadmap  
> **Last Updated:** December 26, 2025

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: Single Instance (Current)                     │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                    Caddy                         │   │
│  │              (Reverse Proxy + SSL)               │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│           ┌─────────────┴─────────────┐                │
│           ▼                           ▼                │
│  ┌─────────────────┐       ┌─────────────────┐        │
│  │    Backend      │       │    Frontend     │        │
│  │   (FastAPI)     │       │   (React PWA)   │        │
│  └─────────────────┘       └─────────────────┘        │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │              PostgreSQL + Redis                  │   │
│  │         (Single instance, local disk)            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Capacity: 1-50 orgs, <10K users, <1M records         │
└─────────────────────────────────────────────────────────┘
```

### Current Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| Organizations | ~50 | Before performance degrades |
| Users | ~10,000 | Concurrent sessions |
| Database size | ~100GB | Single disk |
| Requests/sec | ~1,000 | Single backend instance |

---

## Phase 2: Horizontal Scaling

**Trigger:** When approaching Phase 1 limits

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: Horizontal Scaling                            │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Load Balancer (Caddy/Nginx)         │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│         ┌───────────────┼───────────────┐              │
│         ▼               ▼               ▼              │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐        │
│  │ Backend 1 │   │ Backend 2 │   │ Backend 3 │        │
│  └───────────┘   └───────────┘   └───────────┘        │
│         │               │               │              │
│         └───────────────┼───────────────┘              │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │                Redis Cluster                     │   │
│  │           (Session store, cache)                 │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │              PostgreSQL Primary                  │   │
│  │                     │                            │   │
│  │         ┌───────────┴───────────┐               │   │
│  │         ▼                       ▼               │   │
│  │   ┌──────────┐           ┌──────────┐          │   │
│  │   │ Replica 1│           │ Replica 2│          │   │
│  │   │ (reads)  │           │ (reads)  │          │   │
│  │   └──────────┘           └──────────┘          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Capacity: 50-500 orgs, <100K users, <10M records     │
└─────────────────────────────────────────────────────────┘
```

### Phase 2 Changes

| Component | Change | Effort |
|-----------|--------|--------|
| Backend | Multiple instances behind LB | 1 day |
| Redis | Cluster mode for HA | 2 days |
| PostgreSQL | Primary + read replicas | 3 days |
| Sessions | Move to Redis (already done) | ✅ |
| File storage | Move to S3/MinIO cluster | 2 days |

### Phase 2 Capacity

| Resource | Limit | Notes |
|----------|-------|-------|
| Organizations | ~500 | With proper indexing |
| Users | ~100,000 | Distributed sessions |
| Database size | ~1TB | With replicas |
| Requests/sec | ~10,000 | Multiple backends |

---

## Phase 3: Federation (Future)

**Trigger:** Data sovereignty requirements, global deployment

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: Federation                                    │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Federation Registry                 │   │
│  │         (Node discovery, metadata sync)          │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│         ┌───────────────┼───────────────┐              │
│         ▼               ▼               ▼              │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐        │
│  │  Node A   │   │  Node B   │   │  Node C   │        │
│  │  (IRRI)   │   │ (CIMMYT)  │   │ (ICRISAT) │        │
│  │           │   │           │   │           │        │
│  │ ┌───────┐ │   │ ┌───────┐ │   │ ┌───────┐ │        │
│  │ │  DB   │ │   │ │  DB   │ │   │ │  DB   │ │        │
│  │ └───────┘ │   │ └───────┘ │   │ └───────┘ │        │
│  └───────────┘   └───────────┘   └───────────┘        │
│         │               │               │              │
│         └───────────────┼───────────────┘              │
│                         ▼                               │
│              Federated Search / Sync                    │
│                                                         │
│  Capacity: Unlimited orgs, global scale                │
└─────────────────────────────────────────────────────────┘
```

### Federation Requirements

| Requirement | Description | Effort |
|-------------|-------------|--------|
| Node Protocol | Discovery, authentication | 2 months |
| Data Sync | Selective replication | 3 months |
| Conflict Resolution | Merge strategies | 1 month |
| Federated Search | Cross-node queries | 2 months |
| Admin Tools | Node management | 1 month |

**Total Effort:** 6-12 months

### When to Federate

- Large organizations want their own instance
- Data sovereignty requirements (GDPR, etc.)
- Geographic distribution needs
- >500 organizations

---

## Scaling Triggers

### When to Scale

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU usage | >70% sustained | Add backend instances |
| Memory usage | >80% | Increase instance size |
| Database connections | >80% pool | Add read replicas |
| Response time | >500ms p95 | Investigate bottleneck |
| Disk usage | >70% | Expand storage |
| Error rate | >1% | Investigate and fix |

### Monitoring Setup

```yaml
# Prometheus alerts (example)
groups:
  - name: bijmantra
    rules:
      - alert: HighCPU
        expr: cpu_usage > 0.7
        for: 5m
        labels:
          severity: warning
          
      - alert: HighMemory
        expr: memory_usage > 0.8
        for: 5m
        labels:
          severity: warning
          
      - alert: SlowResponses
        expr: http_request_duration_seconds{quantile="0.95"} > 0.5
        for: 5m
        labels:
          severity: warning
```

---

## Cost Estimation

### Phase 1 (Current)

| Resource | Spec | Monthly Cost |
|----------|------|--------------|
| Server | 4 vCPU, 8GB RAM | ~$40-80 |
| Database | Managed PostgreSQL | ~$50-100 |
| Storage | 100GB SSD | ~$10-20 |
| Bandwidth | 1TB | ~$10-20 |
| **Total** | | **~$110-220/month** |

### Phase 2 (Scaled)

| Resource | Spec | Monthly Cost |
|----------|------|--------------|
| Load Balancer | Managed LB | ~$20-40 |
| Backend (x3) | 2 vCPU, 4GB each | ~$60-120 |
| Database Primary | 4 vCPU, 16GB | ~$100-200 |
| Database Replicas (x2) | 2 vCPU, 8GB each | ~$100-200 |
| Redis Cluster | 3 nodes | ~$50-100 |
| Storage | 500GB SSD | ~$50-100 |
| Bandwidth | 5TB | ~$50-100 |
| **Total** | | **~$430-860/month** |

### Phase 3 (Federation)

Costs vary significantly based on:
- Number of nodes
- Geographic distribution
- Data transfer between nodes
- Each node has its own infrastructure costs

---

## Database Scaling Details

### Read Replicas

```sql
-- Check replication lag
SELECT 
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn
FROM pg_stat_replication;
```

### Connection Pooling

```yaml
# PgBouncer config
[databases]
bijmantra = host=localhost dbname=bijmantra_production

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

### Partitioning (Future)

For very large tables:

```sql
-- Partition by organization_id
CREATE TABLE observations (
    id SERIAL,
    organization_id INTEGER,
    ...
) PARTITION BY HASH (organization_id);

CREATE TABLE observations_0 PARTITION OF observations
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
-- etc.
```

---

## Application Scaling

### Stateless Backend

Ensure backend is stateless:

- ✅ Sessions in Redis (not memory)
- ✅ File uploads to MinIO (not local disk)
- ✅ No in-memory caches (use Redis)
- ✅ No sticky sessions required

### Async Processing

For heavy operations:

```python
# Use background tasks
from app.core.tasks import task_queue

@router.post("/heavy-operation")
async def heavy_operation():
    task_id = await task_queue.enqueue(
        "process_heavy_task",
        {"data": "..."}
    )
    return {"task_id": task_id}
```

---

## Recommendations

### Short Term (Now)

1. ✅ Current architecture is sufficient for launch
2. Set up monitoring (Prometheus + Grafana)
3. Configure alerts for scaling triggers
4. Document current resource usage baseline

### Medium Term (3-6 months)

1. Evaluate growth rate
2. Plan Phase 2 if approaching limits
3. Consider managed database (RDS, Cloud SQL)
4. Implement connection pooling

### Long Term (1+ year)

1. Evaluate federation needs
2. Consider multi-region deployment
3. Plan for data sovereignty requirements
4. Build federation protocol if needed

---

*Scale when needed, not before. Premature optimization is the root of all evil.*
