# Compute Job Queue Interface

## Overview

This module extends the existing `task_queue.py` service with a consistent interface for queueing compute jobs across all domains. It implements the Compute Interface Pattern as defined in the Architecture Stabilization design.

## Files

- `task_queue.py` - Extended with compute job queueing methods
- `compute_interface.py` - Base class for domain-specific compute interfaces
- `compute_engine.py` - Existing compute orchestrator (unchanged)

## Key Features

### 1. Compute Job Queueing

Queue heavy compute operations without blocking API workers:

```python
from app.services.task_queue import task_queue, ComputeType

job_id = await task_queue.enqueue_compute(
    compute_name="gwas_analysis",
    compute_func=gwas_worker_function,
    compute_type=ComputeType.HEAVY_COMPUTE,
    genotype_data=genotypes,
    phenotype_data=phenotypes
)
```

### 2. Job Status Tracking

Track job progress and status:

```python
status = await task_queue.get_compute_status(job_id)
# Returns:
# {
#     "id": "...",
#     "name": "genomics.gwas_analysis",
#     "status": "running",
#     "progress": 0.5,
#     "progress_message": "Analyzing markers...",
#     "compute_type": "heavy_compute",
#     ...
# }
```

### 3. Result Retrieval

Get compute results (blocks until complete):

```python
result = await task_queue.get_compute_result(job_id)
```

### 4. Job Listing and Filtering

List jobs with filters:

```python
jobs = task_queue.get_compute_jobs(
    compute_type=ComputeType.HEAVY_COMPUTE,
    status=TaskStatus.RUNNING,
    user_id="user_123",
    limit=50
)
```

## Compute Types

### LIGHT_PYTHON
- Python-only operations
- Execution time < 30 seconds
- Examples: data validation, simple statistics

### HEAVY_COMPUTE
- Rust/Fortran operations
- Execution time > 30 seconds
- Examples: BLUP, GWAS, GRM computation

### GPU_COMPUTE
- WebGPU/CUDA operations
- Specialized hardware required
- Examples: deep learning inference

## Domain Compute Interfaces

Each domain implements its own compute interface by subclassing `BaseComputeInterface`:

### Genomics Domain

```python
from app.modules.genomics.compute import GWASCompute

gwas_compute = GWASCompute()
job_id = await gwas_compute.run_gwas(genotype_data, phenotype_data)
result = await gwas_compute.get_result(job_id)
```

### Breeding Domain

```python
from app.modules.breeding.compute import BLUPCompute

blup_compute = BLUPCompute()
job_id = await blup_compute.run_blup(phenotypes, fixed_effects, ...)
result = await blup_compute.get_result(job_id)
```

## Creating New Domain Compute Interfaces

1. Create compute directory: `modules/{domain}/compute/`
2. Create compute interface class:

```python
# modules/{domain}/compute/{operation}_compute.py
from app.services.compute_interface import BaseComputeInterface, ComputeType

class MyCompute(BaseComputeInterface):
    def __init__(self):
        super().__init__(domain_name="my_domain")
    
    async def run_operation(self, data):
        return await self.enqueue(
            compute_name="my_operation",
            compute_func=self._worker,
            compute_type=ComputeType.HEAVY_COMPUTE,
            data=data
        )
    
    async def _worker(self, data, progress_callback):
        # Heavy compute logic
        progress_callback(0.5, "Processing...")
        result = process_data(data)
        progress_callback(1.0, "Complete")
        return result
```

3. Export in `__init__.py`:

```python
# modules/{domain}/compute/__init__.py
from .my_compute import MyCompute

__all__ = ["MyCompute"]
```

## Integration with Compute Engine

The compute interface wraps the existing `compute_engine.py`:

```python
async def _worker(self, data, progress_callback):
    from app.services.compute_engine import compute_engine
    
    progress_callback(0.1, "Initializing")
    
    # Use compute_engine for Fortran/Rust operations
    result = compute_engine.compute_blup(data)
    
    progress_callback(1.0, "Complete")
    return result
```

## API Integration

Expose compute operations via API endpoints:

```python
# modules/{domain}/router.py
@router.post("/compute/submit")
async def submit_compute(data: ComputeRequest):
    compute = MyCompute()
    job_id = await compute.run_operation(data)
    return {"job_id": job_id, "status": "queued"}

@router.get("/compute/status/{job_id}")
async def get_status(job_id: str):
    compute = MyCompute()
    return await compute.get_status(job_id)

@router.get("/compute/result/{job_id}")
async def get_result(job_id: str):
    compute = MyCompute()
    return await compute.get_result(job_id)
```

## Testing

See `tests/test_compute_interface.py` for comprehensive test examples.

Run tests:
```bash
pytest tests/test_compute_interface.py -v
```

## Examples

See `examples/compute_interface_example.py` for usage examples.

Run examples:
```bash
python examples/compute_interface_example.py
```

## Documentation

Full documentation: `docs/COMPUTE_INTERFACE_PATTERN.md`

## Migration Guide

### Before (Direct compute_engine call):
```python
from app.services.compute_engine import compute_engine

async def calculate_values(self, data):
    result = compute_engine.compute_blup(data)  # Blocks API worker!
    return result
```

### After (Using compute interface):
```python
from ..compute import BLUPCompute

async def calculate_values(self, data):
    blup_compute = BLUPCompute()
    job_id = await blup_compute.run_blup(data)  # Non-blocking
    return {"job_id": job_id, "status": "queued"}

async def get_values(self, job_id):
    blup_compute = BLUPCompute()
    return await blup_compute.get_result(job_id)
```

## Architecture Benefits

1. **Isolation** - Compute crashes don't affect API workers
2. **Scalability** - Workers can be deployed separately
3. **Consistency** - Same interface across all domains
4. **Monitoring** - Centralized job tracking and metrics
5. **Flexibility** - Easy to add new compute types and domains

## Future Enhancements

- Redis-based queue for persistence
- Distributed workers on separate machines
- Result caching for identical inputs
- Job dependencies and chains
- Scheduled compute jobs
- Dynamic priority adjustment
