# BijMantra Domain Engines

**Status**: Canonical (Architecture Law Layer)

---

## 1. Purpose of This Document

BijMantra is not a single computational system. It is a **federation of domain-specific engines**, each optimized for a distinct class of biological questions, mathematical structures, and computational constraints.

This document formalizes those engines.

It exists to:

- Make implicit compute specialization explicit
- Separate *biological intent* from *implementation language*
- Provide a stable contract for future expansion (new biology, not new tech)
- Enable humans and agents to reason about computation correctly

This is an architectural document, not an algorithm catalog.

---

## 2. Core Principle

> **Biology selects the engine.**
> **The engine selects the math.**
> **The math selects the runtime.**

Languages (Fortran, Rust, Python, WASM, GPU) are **implementation details**, not architectural drivers.

---

## 3. Engine Taxonomy (Canonical)

BijMantra currently recognizes **five primary domain engines**.

Each engine is defined by:

- Biological scope
- Mathematical shape
- Determinism characteristics
- Performance expectations
- Existing code bindings

---

## 4. Quantitative Genetics Engine

### 4.1 Biological Scope

- Breeding values (EBV, GEBV)
- Variance components
- Genetic gain estimation
- Kinship and relationship matrices

This engine answers questions of the form:

> *"What is the genetic value, independent of environment?"*

---

### 4.2 Mathematical Shape

- Linear Mixed Models (LMM)
- Henderson’s MME
- REML (AI-REML, EM-REML)
- Dense numerical linear algebra

---

### 4.3 Determinism

- **Strictly deterministic**
- Numerically reproducible
- Sensitive to floating-point stability

---

### 4.4 Runtime Binding

- **Primary**: Fortran (BLAS / LAPACK)
- **Secondary**: Rust (via FFI, when required)

---

### 4.5 Existing Implementations

- `fortran/src/blup_solver.f90`
- `fortran/src/reml_engine.f90`
- `fortran/src/kinship.f90`
- API bindings under `/api/v2/breeding-value/*`

---

## 5. Genomics & Population Statistics Engine

### 5.1 Biological Scope

- Allele frequencies
- Linkage disequilibrium
- Population structure
- Diversity and differentiation metrics

This engine answers questions of the form:

> *"How is genetic variation structured across individuals or populations?"*

---

### 5.2 Mathematical Shape

- Matrix construction (GRM, IBS, A-matrix)
- Eigen decomposition / SVD
- Summary statistics

---

### 5.3 Determinism

- Deterministic for given inputs
- Tolerant to approximation
- Emphasizes throughput over exact reproducibility

---

### 5.4 Runtime Binding

- **Primary**: Rust
- **Execution**: WebAssembly (browser-native)

---

### 5.5 Existing Implementations

- `rust/src/` (GRM, LD, PCA, IBS, Fst)
- Frontend WASM bindings under `frontend/src/wasm/`

---

## 6. G×E & Trial Interaction Engine

### 6.1 Biological Scope

- Multi-environment trials
- Stability analysis
- Environmental sensitivity

This engine answers questions of the form:

> *"How do genotypes behave across environments?"*

---

### 6.2 Mathematical Shape

- AMMI models
- GGE biplots
- Regression surfaces

---

### 6.3 Determinism

- Deterministic core
- Visualization-dependent interpretation

---

### 6.4 Runtime Binding

- **Primary**: Fortran (numerical core)
- **Secondary**: Python (API orchestration, visualization prep)

---

### 6.5 Existing Implementations

- `fortran/src/gxe_analysis.f90`
- API: `/api/v2/gxe`

---

## 7. Selection & Decision Optimization Engine

### 7.1 Biological Scope

- Selection indices
- Parent choice
- Cross planning

This engine answers questions of the form:

> *"Given constraints, what should I select or cross next?"*

---

### 7.2 Mathematical Shape

- Weighted index models
- Constraint-based optimization
- Scenario evaluation

---

### 7.3 Determinism

- Deterministic scoring
- Scenario-sensitive outcomes

---

### 7.4 Runtime Binding

- **Primary**: Fortran (index computation)
- **Secondary**: Python (decision orchestration)

---

### 7.5 Existing Implementations

- `fortran/src/selection_index.f90`
- API: `/api/v2/selection`, `/api/v2/crosses`

---

## 8. Cognitive & Knowledge Engine (Veena)

### 8.1 Biological Scope

- Explanation
- Retrieval
- Conversational assistance

This engine answers questions of the form:

> *"What does this mean, and where is the evidence?"*

---

### 8.2 Mathematical Shape

- Vector similarity
- Embedding search
- Language modeling

---

### 8.3 Determinism

- **Non-deterministic by nature**
- Probabilistic outputs

---

### 8.4 Runtime Binding

- **Primary**: Python
- **Storage**: PostgreSQL + pgvector

---

### 8.5 Existing Implementations

- `backend/app/services/vector_store.py`
- `/api/v2/chat`
- MCP server (`backend/app/mcp/`)

---

## 9. Engine Boundaries (Non-Negotiable)

- Engines **do not call each other directly**
- Engines expose **well-defined API contracts**
- Cross-engine workflows are orchestrated at the **application layer**
- No engine owns UI concerns
- No engine owns persistence

---

## 10. Future Engines (Reserved)

The following domains are explicitly reserved but **not yet implemented**:

- Epigenetics Engine
- Metabolomics Engine
- Phenomics / Computer Vision Engine

These must follow the same structure and constraints defined in this document.

---

## 11. Architectural Law

> If a new computation cannot be clearly assigned to an existing engine,
> **a new engine must be defined** rather than overloading an existing one.

This preserves clarity, correctness, and long-term evolution.

---

**End of Document**
