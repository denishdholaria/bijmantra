# Rust Roadmap & Deep Dive for Bijmantra

## 1. Deep Dive: Current State

### Context & Findings
The Bijmantra application currently utilizes a hybrid architecture where high-performance computing is required. The primary adoption of Rust is within the `genomics_kernel` crate.

- **Existing Rust Module**: `backend/crates/genomics_kernel`
    - **Purpose**: Calculates the G-Matrix (Genomic Relationship Matrix) using the VanRaden method.
    - **Target**: Compiles to WebAssembly (`wasm32-unknown-unknown`) for frontend usage.
    - **Parallelism**: Uses `rayon` for native targets (potential backend use) but serial execution for WASM.
    - **Current Implementation**: Only contains `calculate_g_matrix`.

- **Frontend Expectations**: `frontend/src/wasm/types.ts`
    - The frontend types (`BijmantraGenomicsWasm`) define a vast interface that is **currently missing** in the Rust implementation.
    - **Missing Features**:
        - LD Analysis (`calculate_ld_pair`, `calculate_ld_matrix`)
        - Population Genetics (`test_hwe`, `calculate_fst`, `calculate_diversity`)
        - Matrix Operations (`calculate_grm`, `calculate_pca`, `calculate_eigenvalues`)
        - Statistical Models (`estimate_blup`, `estimate_gblup`, `calculate_ammi`)

- **Backend Reality**: `backend/app/services`
    - Heavy computational logic is currently implemented in **Python** using `numpy` and `scipy`.
    - **GWASService**: Performs GLM/MLM and LD analysis using Python loops and NumPy broadcasting.
    - **GenomicSelectionService**: Performs GBLUP matrix inversion and solving using SciPy.
    - **Redundancy**: Logic for G-Matrix calculation exists in *both* Rust (for frontend) and Python (for backend).

---

## 2. Recommendations

### A. Module Expansion (The `genomics_kernel`)

**Goal**: Achieve parity between the Frontend Interface and Rust Implementation.

1.  **Linkage Disequilibrium (LD)**
    -   *Function*: `calculate_ld_matrix(genotypes, window_size)`
    -   *Why Rust*: LD calculation involves pairwise comparisons ($O(m^2)$ or $O(m \times w)$). Rust's iterator adapters and SIMD support can significantly outperform Python loops and reduce WASM memory overhead compared to passing large arrays to JS.
2.  **PCA & Eigen Decomposition**
    -   *Function*: `calculate_pca(genotypes, k)`
    -   *Why Rust*: Implement Random SVD or standard SVD using `nalgebra` or `ndarray-linalg` (with LAPACK for native, or pure Rust implementations for WASM like `rulinalg`).
3.  **GWAS Engines**
    -   *Function*: `perform_glm`, `perform_mlm`
    -   *Why Rust*: Moving the regression loop to Rust allows for efficient parallelization (`rayon`) across thousands of markers, avoiding Python's GIL and interpretation overhead.
4.  **Imputation**
    -   *Function*: `impute_missing` (Mean, Mode, KNN)
    -   *Why Rust*: Fast iteration over raw genotype bytes (0/1/2) without decompression overhead.

### B. Backend Integration (PyO3)

**Goal**: Unify logic and boost backend performance.

1.  **Python Bindings**
    -   Use **PyO3** to create Python bindings for `genomics_kernel`.
    -   *Benefit*: `GWASService` and `GenomicSelectionService` in Python can call the *exact same* optimized Rust code used by the frontend.
    -   *Action*: Add `[lib] crate-type = ["cdylib"]` and `pyo3` feature flags to `Cargo.toml`.
2.  **Zero-Copy Data Transfer**
    -   Use `numpy` crate in Rust to accept `PyArray` directly, avoiding memory copying between Python and Rust.

### C. New Domain Modules

**Goal**: Extend Rust's safety and speed to other computation-heavy domains.

#### 1. Earth Systems Kernel (`earth_kernel`)
-   **Domain**: Geospatial Analysis, Satellite Imagery Processing.
-   **Current State**: Python `rasterio`/`scipy` in `backend/app/services/earth_systems`.
-   **Rust Opportunities**:
    -   **Raster Algebra**: NDVI/EVI calculations on large Sentinel-2 arrays.
    -   **Interpolation**: Kriging and IDW (Inverse Distance Weighting) for generating heatmaps from point data.
    -   **Vector Tiling**: Generating MVT (Mapbox Vector Tiles) on the fly for frontend visualization.
-   **Crates**: `gdal`, `georaster`, `geo`.

#### 2. Compliance & Crypto Kernel (`crypto_kernel`)
-   **Domain**: Seed Traceability, Blockchain.
-   **Current State**: `backend/app/services/ledger` (Python).
-   **Rust Opportunities**:
    -   **Merkle Trees**: High-speed generation of Merkle roots for batch transaction verification.
    -   **Signatures**: Ed25519 signing/verification for "Proof of Authority" consensus.
    -   **WASM**: Allow verification of blockchain proofs directly in the browser/client.

#### 3. Graph/Pedigree Kernel (`graph_kernel`)
-   **Domain**: Pedigree Analysis, Ancestry.
-   **Current State**: Recursive Python queries.
-   **Rust Opportunities**:
    -   **A-Matrix Calculation**: Recursive tabular method for pedigree relationships.
    -   **Pathfinding**: Finding shortest paths or common ancestors in deep pedigree trees.
    -   **Crates**: `petgraph`.

---

## 3. Implementation Roadmap

### Phase 1: WASM Parity (Immediate)
-   [ ] Implement `calculate_allele_frequencies`, `test_hwe`, `filter_by_maf` in `genomics_kernel`.
-   [ ] Implement `calculate_ld_pair` and `calculate_ld_matrix`.
-   [ ] Update `frontend/src/wasm/index.ts` to use real WASM calls instead of fallback.

### Phase 2: Statistical Core (Short-term)
-   [ ] Implement Matrix operations (PCA, Inverse) in Rust (using `nalgebra`).
-   [ ] Implement GLM (General Linear Model) regression solver in Rust.
-   [ ] Expose these via WASM for client-side "Quick Analysis".

### Phase 3: Backend Performance (Mid-term)
-   [ ] Configure `genomics_kernel` to build as a Python extension (PyO3).
-   [ ] Refactor `GWASService` (Python) to delegate heavy math to `genomics_kernel`.

### Phase 4: Domain Expansion (Long-term)
-   [ ] Initialize `earth_kernel` crate for raster processing.
-   [ ] Initialize `crypto_kernel` for blockchain operations.
