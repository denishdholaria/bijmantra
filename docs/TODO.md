# Bijmantra - Priority TODO

> **Single Source of Truth** for what needs to be built  
> Last updated: December 5, 2025

---

## 🔴 HIGH PRIORITY: AI/ML Backend

The UI is built. These need backend implementation.

### 1. Veena RAG (2-3 days each)
- [ ] **Embedding Service** — Generate real embeddings for germplasm, protocols
  - Use sentence-transformers (MiniLM, 384-dim)
  - Store in pgvector (migration exists)
- [ ] **Vector Search API** — `/api/v2/vector/search`
  - Semantic search across germplasm, documents
- [ ] **Veena Chat Backend** — Connect to vector search
  - RAG pipeline: query → embed → search → context → response

### 2. Genomic Selection (3-5 days each)
- [ ] **GBLUP Backend** — Python with NumPy/SciPy
  - Kinship matrix calculation
  - Mixed model equations solver
- [ ] **Cross Prediction** — Predict progeny performance
  - Parent combination scoring
  - Expected genetic gain
- [ ] **Breeding Values API** — `/api/v2/breeding-values`

### 3. MCP Integration (HIGH IMPACT)
Enable ChatGPT/Claude to query BrAPI data directly.

```python
# backend/app/mcp/server.py
from fastmcp import FastMCP

mcp = FastMCP("BrAPI MCP Server")

@mcp.tool()
def get_trial_info(trial_id: str) -> dict:
    """Retrieve trial from BrAPI."""
    return brapi_client.get_trial(trial_id)

@mcp.tool()
def search_germplasm(query: str) -> list:
    """Semantic search for germplasm."""
    return vector_search(query, doc_type="germplasm")
```

---

## 🟠 MEDIUM PRIORITY: Computer Vision

### Plant Vision Models (1-2 weeks)
- [ ] **Disease Detection** — TensorFlow.js model
  - Rice blast, bacterial blight, rust
  - Train or use pre-trained model
- [ ] **Growth Stage Classifier** — BBCH scale
- [ ] **Model Serving** — `/api/v2/vision/analyze`

### WASM Compilation (1 week)
- [ ] **Compile Rust to WASM** — `rust/` → `frontend/public/wasm/`
  - GRM calculation
  - LD analysis
  - PCA

---

## 🟡 LOW PRIORITY: Advanced Analytics

- [ ] GWAS Pipeline (MLM, FarmCPU)
- [ ] G×E Analysis (AMMI, GGE biplot)
- [ ] Multi-omics support

---

## ✅ COMPLETED

### Dec 5, 2025
- [x] Navigation redesign (Divisions → Modules)
- [x] Plant Sciences with 9 subgroups
- [x] Quick Access removed
- [x] Documentation consolidated
- [x] 0 TypeScript errors
- [x] 48 tests passing

### Previously
- [x] 210+ pages built
- [x] BrAPI v2.1 100% (34/34 endpoints)
- [x] Veena AI UI
- [x] WASM tool UIs
- [x] Plant Vision UI
- [x] pgvector migration
- [x] Offline sync (Dexie.js)
- [x] PWA with Workbox

---

## 🚫 NOT Building (Integrate Instead)

| Don't Build | Integrate With |
|-------------|----------------|
| Full ERP | ERPNext |
| Agrochemical DB | External registries |
| Bioinformatics tools | NCBI, EMBL, Ensembl |
| Weather service | OpenWeather API |

---

## 📚 Documentation Map

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `PROJECT_STATUS.md` | Current status |
| `docs/ARCHITECTURE.md` | **Technical reference + AI/ML roadmap** |
| `docs/Godsend.md` | Feature tracking |
| `docs/TROUBLESHOOTING.md` | Common issues |
| `docs/framework/PARASHAKTI_SPECIFICATION.md` | Framework spec |

> **Note**: AI/ML roadmap is in `docs/ARCHITECTURE.md` — that's the single source of truth for technical decisions.
