# Compute Interface Pattern

## Overview

The Compute Interface Pattern provides a consistent way to queue and manage heavy compute operations across all domains in BijMantra. This pattern isolates compute operations from API workers, preventing compute crashes from affecting API availability.

## Architecture

```
API Request
    ↓
Service Layer
    ↓
Compute Interface (enqueue job)
    ↓
Task Queue (Redis)
    ↓
Compute Worker (picks up job)
    ↓
Compute Engine (Python/Rust/Fortran)
    ↓
Result Storage
    ↓
Service Layer (retrieves result)
```

## Components

### 1. Task Queue Service (`app/services/task_queue.py`)

Core task queue infrastructure with compute-specific extensions:

- **TaskStatus**: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
- **TaskPriority**: LOW, NORMAL, HIGH, CRITICAL
- **ComputeType**: LIGHT_PYTHON, HEAVY_COMPUTE, GPU_COMPUTE

Key methods:
- `enqueue_compute()`: Queue a compute job
- `get_compute_status()`: Get job status and progress
- `get_compute_result()`: Get result (blocks until complete)
- `get_compute_jobs()`: List jobs with filters

### 2. Base Compute Interface (`app/services/compute_interface.py`)

Abstract base class for domain-specific compute interfaces:

```python
class BaseComputeInterface:
    def __init__(self, domain_name: str)
    async def enqueue(compute_name, compute_func, compute_type, **kwargs) -> str
    async def get_status(job_id: str) -> dict
    async def get_result(job_id: str) -> Any
    async def cancel(job_id: str) -> bool
    def get_jobs(compute_type, user_id, limit) -> list
```

### 3. Domain Compute Interfaces

Each domain implements its own compute interface by subclassing `BaseComputeInterface`:

- `modules/genomics/compute/gwas_compute.py` - GWAS analysis
- `modules/breeding/compute/blup_compute.py` - BLUP/GBLUP estimation
- `modules/phenotyping/compute/` - Image analysis, phenotype prediction
- `modules/environment/compute/` - Climate modeling, GDD calculation

## Usage Pattern

### Step 1: Create Domain Compute Interface

```python
# modules/{domain}/compute/{operation}_compute.py
from app.services.compute_interface import BaseComputeInterface, ComputeType

class GWASCompute(BaseComputeInterface):
    def __init__(self):
        super().__init__(domain_name="genomics")
    
    async def run_gwas(self, genotype_data, phenotype_data):
        """Queue GWAS analysis job"""
        return await self.enqueue(
            compute_name="gwas_analysis",
            compute_func=self._gwas_worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            genotype_data=genotype_data,
            phenotype_data=phenotype_data
        )
    
    async def _gwas_worker(self, genotype_data, phenotype_data, progress_callback):
        """Worker function executed by compute workers"""
        from app.services.compute_engine import compute_engine
        
        progress_callback(0.1, "Starting GWAS")
        
        # Heavy compute operations
        result = compute_engine.compute_gwas(genotype_data, phenotype_data)
        
        progress_callback(1.0, "GWAS complete")
        return result
```

### Step 2: Use in Service Layer

```python
# modules/genomics/services/gwas_service.py
from ..compute import GWASCompute

class GWASService:
    def __init__(self):
        self.gwas_compute = GWASCompute()
    
    async def submit_gwas_analysis(self, genotype_data, phenotype_data):
        """Submit GWAS job and return job ID"""
        job_id = await self.gwas_compute.run_gwas(
            genotype_data=genotype_data,
            phenotype_data=phenotype_data
        )
        return {"job_id": job_id, "status": "queued"}
    
    async def get_gwas_status(self, job_id: str):
        """Get GWAS job status"""
        return await self.gwas_compute.get_status(job_id)
    
    async def get_gwas_result(self, job_id: str):
        """Get GWAS result (blocks until complete)"""
        return await self.gwas_compute.get_result(job_id)
```

### Step 3: Expose via API

```python
# modules/genomics/router.py
from fastapi import APIRouter, Depends
from .services.gwas_service import GWASService

router = APIRouter(prefix="/genomics", tags=["genomics"])

@router.post("/gwas/submit")
async def submit_gwas(
    genotype_data: list,
    phenotype_data: list,
    service: GWASService = Depends()
):
    """Submit GWAS analysis job"""
    return await service.submit_gwas_analysis(genotype_data, phenotype_data)

@router.get("/gwas/status/{job_id}")
async def get_gwas_status(
    job_id: str,
    service: GWASService = Depends()
):
    """Get GWAS job status"""
    return await service.get_gwas_status(job_id)

@router.get("/gwas/result/{job_id}")
async def get_gwas_result(
    job_id: str,
    service: GWASService = Depends()
):
    """Get GWAS result (blocks until complete)"""
    return await service.get_gwas_result(job_id)
```

## Compute Types

### LIGHT_PYTHON
- Python-only operations
- Execution time < 30 seconds
- Examples: data validation, simple statistics, formatting

### HEAVY_COMPUTE
- Rust/Fortran operations
- Execution time > 30 seconds
- Examples: BLUP, GWAS, GRM computation, REML

### GPU_COMPUTE
- WebGPU/CUDA operations
- Specialized hardware required
- Examples: deep learning inference, large-scale matrix operations

## Worker Routing

Workers can be configured to handle specific compute types:

```python
# Worker configuration
WORKER_CONFIG = {
    "light_workers": {
        "count": 10,
        "compute_types": [ComputeType.LIGHT_PYTHON]
    },
    "heavy_workers": {
        "count": 5,
        "compute_types": [ComputeType.HEAVY_COMPUTE]
    },
    "gpu_workers": {
        "count": 2,
        "compute_types": [ComputeType.GPU_COMPUTE]
    }
}
```

## Progress Tracking

Workers receive a `progress_callback` function to report progress:

```python
async def _worker_function(self, data, progress_callback):
    progress_callback(0.0, "Starting")
    
    # Step 1
    process_step_1(data)
    progress_callback(0.33, "Step 1 complete")
    
    # Step 2
    process_step_2(data)
    progress_callback(0.66, "Step 2 complete")
    
    # Step 3
    result = process_step_3(data)
    progress_callback(1.0, "Complete")
    
    return result
```

## Error Handling

```python
try:
    result = await gwas_compute.get_result(job_id)
except ValueError:
    # Job not found
    return {"error": "Job not found"}
except TimeoutError:
    # Job timed out
    return {"error": "Job timed out"}
except RuntimeError as e:
    # Job failed or cancelled
    return {"error": str(e)}
```

## Integration with Compute Engine

The compute interface wraps the existing `compute_engine.py`:

```python
async def _blup_worker(self, phenotypes, fixed_effects, progress_callback):
    from app.services.compute_engine import compute_engine
    
    progress_callback(0.1, "Initializing")
    
    # Use compute_engine for Fortran/Rust operations
    result = compute_engine.compute_blup(
        phenotypes=phenotypes,
        fixed_effects=fixed_effects,
        # ... other parameters
    )
    
    progress_callback(1.0, "Complete")
    return result
```

## Best Practices

1. **Always use compute interface for heavy operations** - Don't call compute_engine directly from API/service layers
2. **Set appropriate compute type** - Use HEAVY_COMPUTE for operations > 30s
3. **Report progress regularly** - Call progress_callback at meaningful intervals
4. **Handle errors gracefully** - Catch exceptions in worker functions
5. **Set appropriate priority** - Use HIGH for user-facing operations, NORMAL for batch jobs
6. **Clean up old jobs** - Use `cleanup_old_tasks()` to remove completed jobs

## Migration from Direct Compute Calls

### Before (Direct compute_engine call):
```python
# Service layer calling compute_engine directly
from app.services.compute_engine import compute_engine

async def calculate_breeding_values(self, data):
    result = compute_engine.compute_blup(data)  # Blocks API worker!
    return result
```

### After (Using compute interface):
```python
# Service layer using compute interface
from ..compute import BLUPCompute

async def calculate_breeding_values(self, data):
    blup_compute = BLUPCompute()
    job_id = await blup_compute.run_blup(data)  # Non-blocking
    return {"job_id": job_id, "status": "queued"}

async def get_breeding_values(self, job_id):
    blup_compute = BLUPCompute()
    return await blup_compute.get_result(job_id)  # Blocks until complete
```

## Testing

```python
import pytest
from app.modules.genomics.compute import GWASCompute

@pytest.mark.asyncio
async def test_gwas_compute():
    gwas_compute = GWASCompute()
    
    # Submit job
    job_id = await gwas_compute.run_gwas(
        genotype_data=test_genotypes,
        phenotype_data=test_phenotypes
    )
    
    assert job_id is not None
    
    # Check status
    status = await gwas_compute.get_status(job_id)
    assert status["status"] in ["pending", "running", "completed"]
    
    # Get result
    result = await gwas_compute.get_result(job_id)
    assert "p_values" in result
```

## Monitoring

Track compute job metrics:

- Queue depth by compute type
- Job execution time by domain
- Job success/failure rate
- Worker utilization
- Average wait time

## Future Enhancements

1. **Redis-based queue** - Replace in-memory queue with Redis for persistence
2. **Distributed workers** - Deploy workers on separate machines
3. **Result caching** - Cache compute results for identical inputs
4. **Job dependencies** - Support job chains and dependencies
5. **Scheduled jobs** - Support cron-like scheduled compute jobs
6. **Job prioritization** - Dynamic priority adjustment based on load
