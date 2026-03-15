# Bijmantra Fortran Compute Engine

## Aerospace-Grade Numerical Precision for Plant Breeding

This module provides high-performance numerical computations using Fortran, the gold standard for scientific computing. Fortran is chosen for its:

- **Reproducible Results**: Deterministic floating-point operations
- **Aerospace-Grade Precision**: Same numerical libraries used in NASA/ESA missions
- **Raw Performance**: Optimized BLAS/LAPACK implementations
- **Battle-Tested**: 60+ years of scientific computing heritage

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Bijmantra Application                        │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend  │  FastAPI Backend  │  Rust Orchestration      │
├─────────────────────────────────────────────────────────────────┤
│                    Rust FFI Layer (iso_c_binding)               │
├─────────────────────────────────────────────────────────────────┤
│                    Fortran Compute Kernels                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  BLUP    │  │  GBLUP   │  │  REML    │  │  PCA/SVD │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Kinship  │  │    LD    │  │  G×E     │  │ Stability│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
├─────────────────────────────────────────────────────────────────┤
│              BLAS / LAPACK / OpenBLAS / MKL                     │
└─────────────────────────────────────────────────────────────────┘
```

## Modules

### 1. BLUP/GBLUP Solver (`blup_solver.f90`)
Best Linear Unbiased Prediction for breeding value estimation.
- Mixed model equations solver
- Sparse matrix operations
- Iterative and direct methods

### 2. REML Engine (`reml_engine.f90`)
Restricted Maximum Likelihood for variance component estimation.
- AI-REML algorithm
- EM-REML fallback
- Convergence diagnostics

### 3. Kinship Matrix (`kinship.f90`)
Genomic relationship matrix computation.
- VanRaden Method 1 & 2
- Dominance relationship matrix
- Epistatic relationship matrix

### 4. PCA/SVD (`pca_svd.f90`)
Principal Component Analysis and Singular Value Decomposition.
- Truncated SVD for large matrices
- Incremental PCA
- Population structure analysis

### 5. Linkage Disequilibrium (`ld_analysis.f90`)
LD computation and decay analysis.
- r² calculation
- D' statistics
- LD pruning

### 6. G×E Interaction (`gxe_analysis.f90`)
Genotype-by-Environment interaction analysis.
- AMMI model
- GGE biplot
- Finlay-Wilkinson regression

## Building

### Prerequisites
- gfortran 9+ or Intel Fortran
- OpenBLAS or Intel MKL
- CMake 3.15+

### Build Commands
```bash
# Configure
cmake -B build -DCMAKE_BUILD_TYPE=Release

# Build shared library
cmake --build build

# Run tests
ctest --test-dir build
```

## Integration with Rust

The Fortran routines are exposed via `iso_c_binding` and called from Rust:

```rust
// Rust FFI declaration
extern "C" {
    fn compute_gblup(
        genotypes: *const f64,
        phenotypes: *const f64,
        n_individuals: i32,
        n_markers: i32,
        breeding_values: *mut f64
    ) -> i32;
}
```

## Why Fortran?

| Aspect | Fortran | Python/NumPy | Rust |
|--------|---------|--------------|------|
| Numerical Precision | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| BLAS/LAPACK Integration | Native | Wrapper | FFI |
| Scientific Heritage | 60+ years | 20 years | 5 years |
| Reproducibility | Deterministic | Platform-dependent | Good |
| Performance | Optimal | Good (with NumPy) | Excellent |

## Architectural Decision

> "Use Fortran for the compute hotspots — BLUP/GBLUP/REML solvers, PCA/SVD, kinship/LD kernels — expose them with iso_c_binding. Wrap Fortran in Rust: call Fortran shared libs from Rust using the C ABI. That gives you Rust's memory safety around orchestration + the raw speed of Fortran where it matters."

This hybrid approach provides:
1. **Fortran**: Raw numerical performance where it matters
2. **Rust**: Memory safety and modern tooling for orchestration
3. **Python**: ML interoperability and rapid prototyping
4. **TypeScript/WASM**: Browser-based computations for smaller datasets

## License

Composite BSL License - Part of the Bijmantra Plant Breeding Platform
