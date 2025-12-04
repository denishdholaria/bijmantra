# Bijmantra Architecture

## Aerospace-Grade Plant Breeding Platform

This document describes the architectural decisions and technical stack of Bijmantra, designed for aerospace-grade precision and reproducibility in plant breeding computations.

## Vision

> "Build a great future-ready Framework which can house any new development and customisation one can think of"

Bijmantra is designed as a Human-AI Centric (HMI) platform that combines:

- **High-precision numerical computing** using Fortran
- **Memory-safe orchestration** using Rust
- **Modern web interface** with React
- **AI-first interaction** with Veena assistant
- **Voice-enabled operations** for field use

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  React UI   │  │   Veena     │  │   Voice     │  │   Mobile    │        │
│  │  (Web)      │  │  AI 🪷      │  │  Commands   │  │  (Capacitor)│        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                           APPLICATION LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  FastAPI    │  │  WebSocket  │  │  GraphQL    │  │  BrAPI      │        │
│  │  REST API   │  │  Real-time  │  │  (Future)   │  │  Compliance │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                           COMPUTE LAYER                                      │
│  ┌───────────────────────────────────────────────────────────────────┐      │
│  │                    HYBRID COMPUTE ENGINE                           │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │      │
│  │  │ Fortran  │  │   Rust   │  │   WASM   │  │  WebGPU  │          │      │
│  │  │   HPC    │  │   FFI    │  │ Browser  │  │   GPU    │          │      │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │      │
│  │       │              │             │             │                │      │
│  │       └──────────────┴─────────────┴─────────────┘                │      │
│  │                           │                                        │      │
│  │  ┌────────────────────────┴────────────────────────┐              │      │
│  │  │              BLAS / LAPACK / MKL                 │              │      │
│  │  └─────────────────────────────────────────────────┘              │      │
│  └───────────────────────────────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────────────────────────────┤
│                           DATA LAYER                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │   Redis     │  │ Meilisearch │  │  IndexedDB  │        │
│  │ + pgvector  │  │   Cache     │  │   Search    │  │   Offline   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────────────────────┤
│                           AI/ML LAYER                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   ONNX      │  │   WebNN     │  │  TensorFlow │  │   Custom    │        │
│  │  Runtime    │  │  Browser AI │  │   Serving   │  │   Models    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Compute Architecture

### Why Fortran?

| Aspect              | Fortran       | Python/NumPy       | Rust      | JavaScript |
| ------------------- | ------------- | ------------------ | --------- | ---------- |
| Numerical Precision | ⭐⭐⭐⭐⭐    | ⭐⭐⭐             | ⭐⭐⭐⭐  | ⭐⭐       |
| BLAS/LAPACK         | Native        | Wrapper            | FFI       | N/A        |
| Scientific Heritage | 60+ years     | 20 years           | 5 years   | N/A        |
| Reproducibility     | Deterministic | Platform-dependent | Good      | Poor       |
| Performance         | Optimal       | Good               | Excellent | Poor       |

### Hybrid Compute Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPUTE DECISION TREE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Is it a numerical hotspot?                                      │
│       │                                                          │
│       ├── YES → Use Fortran                                      │
│       │         • BLUP/GBLUP solvers                            │
│       │         • REML variance estimation                       │
│       │         • PCA/SVD decomposition                          │
│       │         • Kinship matrix computation                     │
│       │         • LD analysis                                    │
│       │                                                          │
│       └── NO → Is it browser-based?                              │
│                    │                                             │
│                    ├── YES → Use Rust/WASM                       │
│                    │         • Client-side computations          │
│                    │         • Offline calculations              │
│                    │         • Real-time visualizations          │
│                    │                                             │
│                    └── NO → Is it GPU-intensive?                 │
│                                 │                                │
│                                 ├── YES → Use WebGPU             │
│                                 │         • Matrix operations    │
│                                 │         • Parallel processing  │
│                                 │                                │
│                                 └── NO → Use Python/TypeScript   │
│                                           • Business logic       │
│                                           • API orchestration    │
│                                           • ML inference         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Fortran Modules

| Module                   | Purpose                   | Key Algorithms            |
| ------------------------ | ------------------------- | ------------------------- |
| `blup_solver.f90`        | Breeding value estimation | BLUP, GBLUP, MME solver   |
| `reml_engine.f90`        | Variance components       | AI-REML, EM-REML          |
| `kinship.f90`            | Relationship matrices     | VanRaden, Yang, Dominance |
| `pca_svd.f90`            | Dimensionality reduction  | Truncated SVD, PCA        |
| `ld_analysis.f90`        | Linkage disequilibrium    | r², D', LD decay          |
| `gxe_analysis.f90`       | G×E interaction           | AMMI, GGE biplot          |
| `stability_analysis.f90` | Yield stability           | Finlay-Wilkinson, AMMI    |
| `selection_index.f90`    | Multi-trait selection     | Smith-Hazel, BLUP index   |

### Rust FFI Layer

Rust provides memory-safe wrappers around Fortran:

```rust
// Safe wrapper for GBLUP computation
pub fn gblup(
    genotypes: &[f64],
    phenotypes: &[f64],
    heritability: f64,
    n: usize,
    m: usize,
) -> ComputeResult<Vec<f64>> {
    // Validate dimensions
    // Call Fortran via FFI
    // Return safe Result type
}
```

## User Interface

### Design Principles

Key principles:

- **Clean, professional interface**
- **Data-dense panels** for information display
- **Status indicators** for system health
- **Light and Dark themes**
- **Smooth animations** for feedback

### Component System

```
components/
├── ModuleInfoMark.tsx      # i-mark for tech transparency
├── ThemeToggle.tsx         # Light/Dark theme switcher
├── ai/
│   ├── Veena.tsx           # AI assistant (named after musical instrument of Goddess of Knowledge, Saraswati's Veena)
│   ├── VeenaWelcome.tsx    # Cultural introduction screen
│   └── VoiceCommand.tsx    # Voice control
├── collaboration/
│   ├── RealtimePresence.tsx    # Live cursor & user presence
│   └── CollaborativeEditor.tsx # Real-time editing
├── visualizations/
│   ├── GeneticGainChart.tsx    # Genetic gain over time
│   ├── HeritabilityGauge.tsx   # Visual heritability indicators
│   ├── SelectionResponseChart.tsx
│   └── CorrelationHeatmap.tsx  # Trait correlations
└── ...
```

### Module Info Marks (i-marks)

Every page/module displays technical information:

- Description of functionality
- Tech stack used
- Data source
- Compute engine
- API endpoint
- Architecture decision rationale

## AI Integration

### Veena AI Assistant 🪷

Named after the sacred instrument of Goddess Saraswati, symbolizing the harmony of knowledge and creativity.

Human-AI centric interface features:

- Conversational AI for breeding queries
- Voice input/output support (Web Speech API)
- Context-aware suggestions with RAG
- Cultural welcome experience for new users
- Quick action buttons for common tasks
- Predictive analytics and insights

### Voice Commands

Hands-free operation for field use:

- Wake word: "Hey Veena" or "Hey Bijmantra"
- Navigation commands
- Data entry
- Search queries

### Vector Database (pgvector)

Semantic search and RAG for intelligent responses:

- 384-dimensional embeddings (MiniLM model)
- Cosine similarity search
- Germplasm semantic search
- Protocol and document retrieval
- Similar variety discovery

### AI-Powered Insights

Predictive analytics dashboard:

- Yield predictions with confidence intervals
- Crossing recommendations based on genomic data
- Data quality alerts
- Genetic gain opportunities
- Weather impact analysis

## Data Architecture

### Primary Storage (PostgreSQL + pgvector)

- Breeding program data
- Germplasm records
- Trial observations
- User management
- Vector embeddings for semantic search
- PostGIS for spatial data

### Cache Layer (Redis)

- Session management
- Real-time metrics
- Computed aggregations

### Search Engine (Meilisearch)

- Full-text search
- Faceted filtering
- Typo tolerance

### Vector Store (pgvector)

- Semantic search embeddings
- RAG context retrieval
- Similar variety discovery
- Document similarity

### Offline Storage (IndexedDB)

- CRDT-based sync
- Conflict resolution
- Background sync queue
- Vector clock for ordering

## Commercial Module

### Seed Lot Management

For seed companies:

- Lot tracking and traceability
- Quality testing data
- Certification workflow
- Inventory management
- Customizable fields

## Feature Roadmap

### Phase 1: Foundation ✅ Complete

- [x] Modern UI with Light/Dark themes
- [x] Veena AI assistant with cultural welcome
- [x] Voice commands (Hey Veena)
- [x] Fortran HPC compute layer
- [x] Commercial seed lot module
- [x] BrAPI v2.1 compliance

### Phase 2: AI & Analytics ✅ Complete

- [x] Vector database (pgvector) for semantic search
- [x] AI-powered insights dashboard
- [x] Predictive analytics (yield, crossing)
- [x] Real-time collaboration
- [x] Advanced visualization suite
- [x] Enterprise audit trail
- [x] Enhanced offline sync (CRDT)

### Phase 3: Advanced AI 🔄 In Progress

- [ ] AI video processing for phenotyping
- [ ] Drone integration
- [ ] IoT sensor support
- [ ] Computer vision for disease detection

### Phase 4: Enterprise

- [ ] Multi-tenant architecture
- [ ] Custom module builder
- [ ] White-label support
- [ ] Enterprise SSO

## Tech Stack Summary

| Layer      | Technology                    | Purpose                   |
| ---------- | ----------------------------- | ------------------------- |
| Frontend   | React + TypeScript            | UI framework              |
| Styling    | Tailwind CSS                  | Utility-first CSS         |
| State      | Zustand + TanStack Query      | State management          |
| Backend    | FastAPI (Python)              | REST API                  |
| Database   | PostgreSQL + PostGIS          | Primary storage + spatial |
| Vector DB  | pgvector                      | Semantic search & RAG     |
| Cache      | Redis                         | Caching layer             |
| Search     | Meilisearch                   | Full-text search          |
| Compute    | Fortran + Rust + WASM         | Numerical computing       |
| AI         | Veena + sentence-transformers | AI assistant + embeddings |
| Mobile     | Capacitor                     | Native apps               |
| Real-time  | Socket.io                     | WebSocket + collaboration |
| Offline    | CRDT + IndexedDB              | Offline sync              |
| Containers | Podman                        | Rootless containers       |

## Architectural Decisions

### Decision 1: Fortran for Numerical Computing

**Context**: Plant breeding requires precise, reproducible numerical computations.

**Decision**: Use Fortran for compute hotspots (BLUP, REML, kinship).

**Rationale**:

- 60+ years of scientific computing heritage
- Native BLAS/LAPACK integration
- Deterministic floating-point operations
- Aerospace-grade precision

### Decision 2: Rust FFI Layer

**Context**: Need memory safety around Fortran calls.

**Decision**: Wrap Fortran in Rust using C ABI.

**Rationale**:

- Memory safety guarantees
- Modern tooling and ecosystem
- Excellent FFI support
- Can compile to WASM for browser

### Decision 3: Professional UI Design

**Context**: Users need data-dense, professional interface.

**Decision**: Clean design with Light and Dark themes.

**Rationale**:

- Reduces eye strain for long sessions
- Professional appearance
- Clear status indicators
- Information density

### Decision 4: Module Info Marks

**Context**: Transparency about technical implementation.

**Decision**: Every page shows i-mark with tech details.

**Rationale**:

- Builds trust with technical users
- Documents architecture in-app
- Helps debugging and support
- Educational value

---

_Bijmantra - Aerospace-Grade Precision for Plant Breeding_
