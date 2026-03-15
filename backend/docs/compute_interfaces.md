# Compute Interfaces Documentation

## Overview

This document describes the compute interface wrappers implemented for Task 6.2: Wrap Analytics Compute Operations.

All analytics compute operations are now wrapped in the job queue interface, providing:
- Async execution for operations > 30 seconds
- Timeout handling
- Error recovery
- Progress tracking
- Job status monitoring

## Architecture

### Base Compute Interface

All compute interfaces inherit from `BaseComputeInterface` which provides:

```python
class BaseComputeInterface:
    async def enqueue(compute_name, compute_func, compute_type, priority, **kwargs) -> str
    async def get_status(job_id: str) -> dict
    async def get_result(job_id: str) -> Any
    async def cancel(job_id: str) -> bool
    def get_jobs(compute_type, user_id, limit) -> list
```

### Compute Types

Operations are classified by compute type for worker routing:

- `LIGHT_PYTHON`: Python-only operations < 30 seconds
- `HEAVY_COMPUTE`: Rust/Fortran operations > 30 seconds
- `GPU_COMPUTE`: WebGPU/CUDA operations (specialized hardware)

## Breeding Domain Analytics

### GBLUPAnalyticsCompute

Wraps GBLUP matrix solver operations.

**Location**: `backend/app/modules/breeding/compute/analytics/gblup_analytics_compute.py`

**Methods**:

```python
async def solve_gblup(
    phenotypes: list[float],
    g_matrix: list[list[float]],
    heritability: float,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str
```

**Timeout Configuration**:
- Small matrices (n ≤ 1000): 30 seconds
- Large matrices (n > 1000): 300 seconds (5 minutes)

**Example Usage**:

```python
from app.modules.breeding.compute.analytics import gblup_analytics_compute

# Submit job
job_id = await gblup_analytics_compute.solve_gblup(
    phenotypes=[10.0, 12.0, 11.0],
    g_matrix=[[1.0, 0.5, 0.3], [0.5, 1.0, 0.4], [0.3, 0.4, 1.0]],
    heritability=0.5,
    user_id="user123"
)

# Check status
status = await gblup_analytics_compute.get_status(job_id)
print(f"Progress: {status['progress']}")

# Get result (blocks until complete)
result = await gblup_analytics_compute.get_result(job_id)
print(f"GEBVs: {result['gebv']}")
```

### GxEAnalyticsCompute

Wraps GxE interaction scorer operations.

**Location**: `backend/app/modules/breeding/compute/analytics/gxe_analytics_compute.py`

**Methods**:

```python
async def calculate_all_scores(
    yield_matrix: np.ndarray,
    genotype_names: list[str],
    environment_names: list[str],
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str

async def calculate_interaction_matrix(
    yield_matrix: np.ndarray,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str
```

**Timeout Configuration**:
- Small matrices (≤ 10,000 cells): 30 seconds
- Large matrices (> 10,000 cells): 300 seconds (5 minutes)

**Example Usage**:

```python
from app.modules.breeding.compute.analytics import gxe_analytics_compute
import numpy as np

# Submit job
yield_matrix = np.array([
    [10.0, 12.0, 11.0, 13.0],
    [9.0, 11.0, 10.0, 12.0],
    [11.0, 13.0, 12.0, 14.0],
])

job_id = await gxe_analytics_compute.calculate_all_scores(
    yield_matrix=yield_matrix,
    genotype_names=["G1", "G2", "G3"],
    environment_names=["E1", "E2", "E3", "E4"],
    user_id="user123"
)

# Get result
result = await gxe_analytics_compute.get_result(job_id)
print(f"Wricke's Ecovalence: {result['wricke_ecovalence']}")
print(f"Shukla's Stability: {result['shukla_stability']}")
```

## Genomics Domain Statistics

### KinshipCompute

Wraps kinship matrix calculation operations.

**Location**: `backend/app/modules/genomics/compute/statistics/kinship_compute.py`

**Methods**:

```python
async def calculate_vanraden_kinship(
    genotype_matrix: np.ndarray,
    check_maf: bool = True,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str

async def calculate_inbreeding(
    kinship_matrix: np.ndarray,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str
```

**Timeout Configuration**:
- Small matrices (≤ 100,000 cells): 30 seconds
- Large matrices (> 100,000 cells): 600 seconds (10 minutes)

**Example Usage**:

```python
from app.modules.genomics.compute.statistics import kinship_compute
import numpy as np

# Submit kinship calculation job
genotype_matrix = np.array([
    [0, 1, 2, 0, 2],
    [0, 1, 2, 0, 2],
    [2, 1, 0, 2, 0],
])

job_id = await kinship_compute.calculate_vanraden_kinship(
    genotype_matrix=genotype_matrix,
    user_id="user123"
)

# Get result
result = await kinship_compute.get_result(job_id)
K = np.array(result['K'])
print(f"Kinship matrix shape: {K.shape}")

# Calculate inbreeding from kinship matrix
job_id2 = await kinship_compute.calculate_inbreeding(
    kinship_matrix=K,
    user_id="user123"
)

result2 = await kinship_compute.get_result(job_id2)
print(f"Inbreeding coefficients: {result2['inbreeding_coefficients']}")
```

### GWASPlinkCompute

Wraps PLINK adapter operations.

**Location**: `backend/app/modules/genomics/compute/statistics/gwas_plink_compute.py`

**Methods**:

```python
async def run_association(
    bfile: Path | str,
    output_prefix: Path | str,
    phenotype_file: Path | str | None = None,
    covariates_file: Path | str | None = None,
    method: Literal["linear", "logistic", "assoc"] = "linear",
    adjust: bool = False,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str

async def calculate_pca(
    bfile: Path | str,
    output_prefix: Path | str,
    n_pcs: int = 10,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str

async def ld_pruning(
    bfile: Path | str,
    output_prefix: Path | str,
    window_size: int = 50,
    step_size: int = 5,
    r2_threshold: float = 0.2,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> str
```

**Timeout Configuration**:
- Association analysis: 1800 seconds (30 minutes)
- PCA calculation: 900 seconds (15 minutes)
- LD pruning: 900 seconds (15 minutes)

**Example Usage**:

```python
from app.modules.genomics.compute.statistics import gwas_plink_compute
from pathlib import Path

# Submit PLINK association job
job_id = await gwas_plink_compute.run_association(
    bfile=Path("/data/genotypes"),
    output_prefix=Path("/results/gwas"),
    phenotype_file=Path("/data/phenotypes.txt"),
    method="linear",
    user_id="user123"
)

# Check progress
status = await gwas_plink_compute.get_status(job_id)
print(f"Status: {status['status']}, Progress: {status['progress']}")

# Get result
result = await gwas_plink_compute.get_result(job_id)
print(f"Result file: {result['result_file']}")
print(f"Number of markers: {result['n_markers']}")
```

## Error Handling

All compute interfaces include comprehensive error handling:

### Timeout Errors

When a computation exceeds its timeout, the worker returns an error result:

```python
{
    "error": "Computation timed out after 300s",
    # ... other fields with default/empty values
}
```

### Computation Errors

When a computation fails, the worker catches the exception and returns:

```python
{
    "error": "Computation failed: <error message>",
    # ... other fields with default/empty values
}
```

### Checking for Errors

Always check the result for errors:

```python
result = await compute_interface.get_result(job_id)

if result.get("error"):
    print(f"Computation failed: {result['error']}")
else:
    # Process successful result
    print(f"Result: {result}")
```

## Progress Tracking

All compute operations report progress via the `progress_callback`:

```python
progress_callback(0.1, "Initializing computation")
progress_callback(0.5, "Processing data")
progress_callback(1.0, "Computation complete")
```

Check progress using `get_status`:

```python
status = await compute_interface.get_status(job_id)
print(f"Progress: {status['progress'] * 100}%")
print(f"Message: {status['progress_message']}")
```

## Testing

Tests are located in:
- `backend/tests/modules/breeding/compute/test_analytics_compute.py`
- `backend/tests/modules/genomics/compute/test_statistics_compute.py`

Run tests:

```bash
pytest tests/modules/breeding/compute/test_analytics_compute.py -v
pytest tests/modules/genomics/compute/test_statistics_compute.py -v
```

## Migration Notes

### Before (Direct Service Calls)

```python
from app.services.analytics.gblup_matrix_solver import GBLUPMatrixSolver

solver = GBLUPMatrixSolver()
result = solver.solve(phenotypes, g_matrix, heritability)
```

### After (Compute Interface)

```python
from app.modules.breeding.compute.analytics import gblup_analytics_compute

job_id = await gblup_analytics_compute.solve_gblup(
    phenotypes, g_matrix, heritability
)
result = await gblup_analytics_compute.get_result(job_id)
```

### Benefits

1. **Isolation**: Compute operations run in separate workers
2. **Async**: Long-running operations don't block API workers
3. **Timeout**: Automatic timeout handling prevents hung operations
4. **Progress**: Track progress of long-running computations
5. **Error Recovery**: Graceful error handling and reporting
6. **Scalability**: Workers can be scaled independently

## Performance Considerations

### Compute Type Selection

The compute type is automatically determined based on operation size:

- **LIGHT_PYTHON**: Small operations that complete quickly
- **HEAVY_COMPUTE**: Large operations requiring significant compute time

### Timeout Configuration

Timeouts are configured based on expected operation duration:

- Small operations: 30 seconds
- Medium operations: 5 minutes (300 seconds)
- Large operations: 10-30 minutes (600-1800 seconds)

### Worker Scaling

Configure worker count in `task_queue.py`:

```python
task_queue = TaskQueue(max_concurrent=5)  # Adjust based on available resources
```

## Future Enhancements

1. **Priority Queues**: High-priority jobs processed first
2. **Result Caching**: Cache results for identical computations
3. **Distributed Workers**: Deploy workers across multiple machines
4. **GPU Support**: Add GPU_COMPUTE worker type for CUDA operations
5. **Progress Streaming**: Real-time progress updates via WebSocket
