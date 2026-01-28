# 🚪 Contributor Entry Points

> **Find your path into BijMantra based on your role and expertise.**

This document maps contributor roles to specific files, directories, and expectations. It exists to reduce onboarding friction and ensure contributions align with platform architecture.

---

## 📊 Quick Reference

| Your Role | Start Here | First Task |
|-----------|------------|------------|
| 🧬 Plant Breeder | [Breeding Workflows](#-plant-breeders) | Validate trial design logic |
| 🌱 Agronomist | [Field Operations](#-agronomists) | Review cross-domain factors |
| 🧪 Genomics Expert | [Genomics Module](#-genomics-experts) | Audit GWAS/QTL implementations |
| 💻 Full-Stack Developer | [Architecture](#-full-stack-developers) | Fix a CALF-2 page |
| 🦀 Rust/WASM Developer | [Compute Engines](#-rustwasm-developers) | Optimize genomic kernels |
| 📝 Technical Writer | [Documentation](#-technical-writers) | Improve module docs |
| 🧪 QA Engineer | [Testing](#-qa-engineers) | Add E2E test coverage |

---

## 🧬 Plant Breeders

**Your expertise matters for:** Validating breeding workflows, advising on genetics logic, reviewing selection algorithms.

### Key Directories

```
frontend/src/divisions/breeding/        # Breeding UI pages
backend/app/services/breeding/          # Breeding business logic
backend/app/services/genomic_selection.py
backend/app/services/genetic_gain_service.py
docs/modules/breeding/                  # Breeding documentation
```

### Entry Tasks

1. **Validate Trial Design** — Review `frontend/src/pages/TrialForm.tsx` for workflow correctness
2. **Audit Selection Logic** — Check `backend/app/services/genomic_selection.py` formulas
3. **Review Cross Planning** — Validate `backend/app/services/crossing_planner.py`

### What We Need From You

- Identify scientifically incorrect assumptions
- Suggest missing workflow steps
- Validate trait ontology usage
- Review GEBV calculation approaches

### Governance Reference

📄 [MODULE_ACCEPTANCE_CRITERIA.md](docs/architecture/MODULE_ACCEPTANCE_CRITERIA.md) — All modules must support cross-domain integration

---

## 🌱 Agronomists

**Your expertise matters for:** Field trial design, cross-domain validation, environmental factor integration.

### Key Directories

```
frontend/src/divisions/earth-systems/   # Environment & weather pages
backend/app/services/weather_service.py
backend/app/services/gxe_service.py     # G×E analysis
backend/app/api/v2/future/              # Future agronomy modules
docs/modules/environment/
```

### Entry Tasks

1. **Review G×E Analysis** — Validate `backend/app/services/gxe_service.py` (AMMI/GGE/Finlay-Wilkinson)
2. **Audit Weather Integration** — Check `backend/app/services/weather_service.py` for GDD calculations
3. **Cross-Domain Factors** — Review how breeding decisions surface soil/climate factors

### What We Need From You

- Validate environmental factor calculations
- Identify missing agronomic constraints
- Review soil-crop interaction logic
- Suggest field-level workflow improvements

---

## 🧪 Genomics Experts

**Your expertise matters for:** GWAS, QTL mapping, molecular marker analysis, genomic selection.

### Key Directories

```
frontend/src/divisions/genomics/        # Genomics UI pages
backend/app/services/gwas.py
backend/app/services/qtl_mapping.py
backend/app/services/genetic_diversity_service.py
rust/src/                               # WASM genomic kernels
```

### Entry Tasks

1. **Audit GWAS Implementation** — Review `backend/app/services/gwas.py`
2. **Validate Diversity Metrics** — Check `backend/app/services/genetic_diversity_service.py` (He, Ho, F, allelic richness)
3. **Review WASM Kernels** — Examine `rust/src/` for genomic matrix operations

### What We Need From You

- Validate statistical methods
- Identify bioinformatics best practices violations
- Review marker data handling
- Suggest algorithm improvements

### Critical Files (Formulas Preserved)

These files contain scientific formulas that must not be altered without domain expert review:

```
backend/app/api/v2/phenotype.py         # Heritability, selection response
backend/app/services/genetic_gain_service.py
backend/app/services/genomic_selection.py
backend/app/services/stability_analysis.py
backend/app/services/gwas.py
backend/app/services/qtl_mapping.py
backend/app/services/population_genetics.py
```

---

## 💻 Full-Stack Developers

**Your expertise matters for:** React/TypeScript frontend, Python/FastAPI backend, database operations.

### Key Directories

```
frontend/src/                           # React application
backend/app/                            # FastAPI application
backend/app/api/v2/                     # REST endpoints
backend/app/api/brapi/                  # BrAPI v2.1 endpoints
backend/app/crud/                       # Database operations
backend/app/models/                     # SQLAlchemy models
backend/alembic/versions/               # Database migrations
```

### Entry Tasks (By Priority)

**Priority 1 — Fix CALF-2 Pages (Demo Data Violations)**

These 42 pages return hardcoded demo data instead of database queries:

```
docs/CALF.md                            # Full list with evidence
backend/app/services/                   # Services to convert
```

Pattern to follow:
```python
# ❌ BEFORE (demo data)
DEMO_DATA = [{"id": 1, "name": "Example"}]
def get_items(): return DEMO_DATA

# ✅ AFTER (database query)
async def get_items(db: AsyncSession, organization_id: int):
    result = await db.execute(
        select(Item).where(Item.organization_id == organization_id)
    )
    return result.scalars().all()
```

**Priority 2 — Add Backend Validation**

67 pages perform client-side calculations without backend validation.

**Priority 3 — Improve Test Coverage**

```
backend/tests/                          # Backend tests
frontend/e2e/                           # E2E tests (Playwright)
```

### Architecture Requirements

📄 [GOVERNANCE.md](docs/architecture/GOVERNANCE.md) — Evidence-based reviews, async safety
📄 [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) — System architecture
📄 [API_CONTRACTS.md](docs/architecture/API_CONTRACTS.md) — Cross-domain API requirements

### Code Standards

- **Python**: Ruff linter, type hints required, async for I/O
- **TypeScript**: ESLint + Prettier, strict mode, TanStack Query for server state
- **Database**: All tables must have `organization_id` for RLS

---

## 🦀 Rust/WASM Developers

**Your expertise matters for:** High-performance genomic computations, browser-side WASM, Fortran FFI.

### Key Directories

```
rust/                                   # Rust/WASM crate
rust/src/lib.rs                         # Main entry point
rust/src/python_bindings.rs             # PyO3 bindings
rust/src/wasm_bindings.rs               # WASM exports
fortran/                                # Fortran numerical kernels
fortran/src/                            # BLUP, REML, kinship
```

### Entry Tasks

1. **Optimize GBLUP** — Review `rust/src/` genomic relationship matrix
2. **Fortran Integration** — Examine FFI in `rust/build.rs`
3. **WASM Performance** — Profile browser-side genomic operations

### What We Need From You

- Optimize matrix operations
- Improve WASM bundle size
- Review numerical stability
- Suggest parallelization opportunities

### Build Commands

```bash
cd rust
cargo build --release                   # Native build
cargo build --target wasm32-unknown-unknown  # WASM build
cargo build --features python           # Python bindings
```

---

## 📝 Technical Writers

**Your expertise matters for:** Documentation clarity, tutorials, API reference accuracy.

### Key Directories

```
docs/                                   # All documentation
docs/api/                               # API documentation
docs/architecture/                      # Architecture & governance
docs/modules/                           # Module-specific docs
README.md                               # Main README
CONTRIBUTING.md                         # Contribution guide
```

### Entry Tasks

1. **Improve Module Docs** — Each module in `docs/modules/` needs better examples
2. **API Examples** — Add usage examples to `docs/api/API_REFERENCE.md`
3. **Tutorial Creation** — Create getting-started tutorials

### Documentation Standards

- All numeric claims must reference `metrics.json`
- Scientific formulas must be preserved exactly
- Cross-reference governance documents where applicable

### Files NOT to Modify Without Review

```
docs/architecture/GOVERNANCE.md         # Platform law
docs/architecture/PLATFORM_LAW_INDEX.md # Law index
metrics.json                            # Authoritative metrics
```

---

## 🧪 QA Engineers

**Your expertise matters for:** Test coverage, E2E testing, accessibility compliance.

### Key Directories

```
frontend/e2e/                           # Playwright E2E tests
frontend/e2e/tests/                     # Test suites
backend/tests/                          # Backend tests
backend/tests/units/                    # Unit tests
backend/tests/integration/              # Integration tests
```

### Current Test Status

| Type | Count | Status |
|------|-------|--------|
| Unit | 88 | ✅ Passing |
| Integration | 18 | ✅ Passing |
| E2E | 229 | ✅ Passing (3 skipped) |
| Accessibility | 17 | ✅ Passing |
| **Total** | **352** | ✅ All Passing |

### Entry Tasks

1. **Increase E2E Coverage** — Add tests for untested pages
2. **Accessibility Audit** — Run axe-core on more pages
3. **API Contract Tests** — Validate BrAPI compliance

### Test Commands

```bash
cd frontend
npm run test:e2e                        # Run E2E tests
npm run test:e2e:ui                     # Interactive mode

cd backend
pytest                                  # Run all tests
pytest -m integration                   # Integration only
```

---

## 🔐 Security Considerations

All contributors must be aware of:

1. **Row-Level Security (RLS)** — 103 tables have RLS policies. Never bypass `organization_id` filtering.
2. **Zero Mock Data Policy** — No hardcoded demo data in production code.
3. **Credential Handling** — Never commit credentials. Use environment variables.

📄 [GOVERNANCE.md §4.3](docs/architecture/GOVERNANCE.md) — Security requirements

---

## 📋 Contribution Checklist

Before submitting a PR:

- [ ] Read [CONTRIBUTING.md](CONTRIBUTING.md)
- [ ] Read relevant governance documents
- [ ] Ensure code follows async patterns (no blocking I/O in async functions)
- [ ] Add/update tests for changes
- [ ] Verify `organization_id` filtering for database queries
- [ ] Run `npm run build` (frontend) and `pytest` (backend)
- [ ] Update `metrics.json` if counts changed

---

## 🚫 Contribution Anti-Patterns

PRs will be rejected if they:

- Introduce mock/demo data in services
- Bypass RLS or multi-tenant isolation
- Mix async endpoints with blocking I/O
- Remove or alter scientific formulas without domain expert review
- Make unverifiable claims

---

## 📞 Getting Help

- **Discord**: [discord.gg/ubUHhBHjhG](https://discord.gg/ubUHhBHjhG)
- **Email**: [hello@bijmantra.org](mailto:hello@bijmantra.org)
- **Issues**: Use GitHub Issues for bugs and feature requests

---

*This document is maintained alongside the codebase. Last updated: January 2026.*
