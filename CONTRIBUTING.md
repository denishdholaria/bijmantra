# Contributing to BijMantra

Welcome to **BijMantra** — a cross-domain agricultural research and intelligence platform.

This project exists to solve a hard problem:
**agricultural decisions require simultaneous reasoning across multiple scientific domains.**

If you are here to work in isolation, this may not be the right project.
If you want to build systems that integrate science, data, and AI — you are in the right place.

🌐 **Website:** [bijmantra.org](https://bijmantra.org)

---

## 1. What Makes BijMantra Different

Most agricultural software:
- Works within a single discipline
- Treats integration as reporting
- Leaves synthesis to humans

BijMantra is built differently.

> **Every contribution must support cross-domain reasoning.**

This applies equally to:
- Code
- Data models
- Algorithms
- Documentation
- AI agents
- UX decisions

---

## 2. Core Principles for Contributors

### 2.1 Cross-Domain by Default

No module exists in isolation.

If you contribute to:
- **Breeding** → consider soil, climate, agronomy
- **Agronomy** → consider genetics, economics
- **Soil** → consider crops, water, climate
- **AI** → consider uncertainty and domain boundaries

**If your contribution cannot interact with other domains, it is incomplete.**

### 2.2 Research-Grade Standards

BijMantra is not a dashboard product.

All contributions must:
- Be scientifically interpretable
- Expose assumptions
- Allow traceability
- Support reproducibility

**Black-box logic without explanation will not be merged.**

### 2.3 AI Is an Integrator, Not an Oracle

AI in BijMantra:
- Assists reasoning
- Translates between domains
- Surfaces conflicts
- Expresses uncertainty

AI must **never**:
- Override domain data silently
- Produce untraceable recommendations
- Claim certainty where none exists

---

## 3. Types of Contributions We Welcome

### 3.1 Domain Modules

Examples:
- Soil carbon modeling
- Pest resistance tracking
- Climate risk analytics
- Seed quality systems

Requirements:
- Clear domain definition
- Declared dependencies
- Cross-domain query support

### 3.2 AI Agents & Intelligence Layers

Examples:
- Breeding intelligence agents
- Climate risk agents
- Economics feasibility agents

Requirements:
- Primary domain defined
- Adjacent domain awareness
- Explicit confidence bounds

### 3.3 Data Models & Schemas

Examples:
- Experiment schemas
- Sensor telemetry
- Field trial metadata

Requirements:
- Domain-agnostic where possible
- Extensible
- Versioned
- Documented

### 3.4 Documentation & Research Design

Examples:
- Domain standards
- Integration examples
- Decision flow documentation

Requirements:
- Neutral tone
- Scientific clarity
- Long-term maintainability

---

## 4. Contribution Workflow

### Step 1: Understand the Philosophy

Before coding, read:
- `.kiro/steering/cross-domain-philosophy.md`
- `.kiro/steering/ai-agents.md`
- `.kiro/steering/module-acceptance-criteria.md`

If you disagree with the philosophy, discuss before coding.

### Step 2: Declare Your Domain

Every contribution must declare:
- Primary domain
- Secondary (affected) domains
- Known assumptions
- Known limitations

Example:
```
Primary domain: Agronomy
Secondary domains: Soil, Breeding
Assumptions: Uniform irrigation
Limitations: Does not model pest pressure
```

### Step 3: Design for Integration

Ask yourself:
- Can another domain interrogate this?
- Can AI reason over this output?
- Does this expose uncertainty?

If the answer is "no", redesign.

### Step 4: Submit with Context

Every PR must include:
- What problem it solves
- Which domains it touches
- How it integrates
- What it does NOT handle

---

## 5. Non-Negotiable Rules

❌ No single-metric optimization  
❌ No silent assumptions  
❌ No domain supremacy  
❌ No unexplained AI output  
❌ No hardcoded "best practices"  

If trade-offs exist, they must be explicit.

---

## 6. How Decisions Are Evaluated

Maintainers will evaluate contributions based on:
1. Scientific soundness
2. Cross-domain compatibility
3. Clarity of assumptions
4. Long-term extensibility
5. AI interpretability

A technically correct contribution **may still be rejected** if it breaks cross-domain coherence.

---

## 7. Who This Project Is For

BijMantra is ideal for contributors who are:
- Researchers
- Scientists
- Engineers with scientific curiosity
- Systems thinkers
- Builders who value correctness over speed

This project may frustrate contributors who want:
- Quick demos
- Narrow optimizations
- Domain-isolated work

---

## 8. Development Process

### Getting Started

> **Docker users**: BijMantra uses **Podman** (rootless, daemonless). Commands are identical — use `podman` instead of `docker`. See [Architecture](docs/ARCHITECTURE.md#container-runtime-podman) for the rationale.

1. **Fork the repo** and create your branch from `main`
2. **Read the steering documents** in `.kiro/steering/`
3. **Make your changes** following our coding standards
4. **Add tests** if you've added code that should be tested
5. **Ensure the test suite passes** (`make test`)
6. **Make sure your code lints** (`make lint`)
7. **Commit your changes** using conventional commits
8. **Push to your fork** and submit a pull request

### Branch Naming Convention

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add cross-domain soil-breeding integration
fix: resolve uncertainty propagation in climate agent
docs: update API contracts documentation
test: add integration tests for multi-domain queries
```

---

## 9. Coding Standards

### Backend (Python)

- Follow PEP 8
- Use type hints
- Write docstrings for all functions/classes
- Use `ruff` for linting and formatting
- Maximum line length: 100 characters
- **Async endpoints must use async-compatible libraries only**

### Frontend (TypeScript/React)

- Follow ESLint configuration
- Use TypeScript for type safety
- Write JSDoc comments for complex functions
- Use functional components with hooks
- Maximum line length: 100 characters

### Cross-Domain Requirements

- Expose inputs and outputs in domain-neutral format
- Include uncertainty metadata in all outputs
- Support interrogation by other modules
- Document assumptions explicitly

---

## 10. Testing

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run test`
- All tests: `make test`

**Cross-domain contributions must include integration tests with at least one other domain.**

---

## 11. Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## 💰 Financial Support — Science Can't Wait

> *"Philanthropic support provides the stability needed to train—and retain—top-caliber scientists... and the flexibility to pursue bold, early-stage ideas that often fall outside traditional funding mechanisms."*

**BijMantra is building affordable tools for plant breeders worldwide.** Your financial support directly accelerates the development of climate-resilient crop varieties for 500 million smallholder farmers.

### How to Support

| Platform | Link | Best For |
|----------|------|----------|
| **GitHub Sponsors** | [Sponsor @denishdholaria](https://github.com/sponsors/denishdholaria) | Recurring monthly support |
| **Open Collective** | [opencollective.com/bijmantra](https://opencollective.com/bijmantra) | Transparent, tax-deductible |
| **Direct Contact** | [hello@bijmantra.org](mailto:hello@bijmantra.org) | Institutional partnerships |

### For Institutions & Foundations

We welcome partnerships with:
- **Philanthropic Foundations** (Gates Foundation, Rockefeller, etc.)
- **CGIAR Centers** (IRRI, CIMMYT, ICRISAT, etc.)
- **Government Agencies** (USAID, DFID, GIZ, etc.)
- **Universities** with plant breeding programs

📄 **See [FUNDING.md](FUNDING.md)** for detailed funding tiers and use of funds.

---

## 🌟 The Bigger Picture

BijMantra isn't just software — it's infrastructure for global food security.

> *"Understanding one domain without seeing its interaction with others produces incomplete, sometimes misleading conclusions."* — Denish Dholaria

Every contribution, whether code, documentation, or funding, helps:
- 🌾 **Accelerate** development of improved crop varieties
- 🌍 **Democratize** access to breeding tools
- 🌡️ **Enable** climate adaptation research
- 👨‍🌾 **Empower** 500 million smallholder farmers
- 🔬 **Unify** fragmented agricultural knowledge

---

## 12. Reporting Documentation Discrepancies

BijMantra is a large project (1,370+ endpoints, 221 pages) maintained by a solo developer. Documentation accuracy is a priority, but discrepancies may exist.

### What to Report

| Report This | Don't Report This |
|-------------|-------------------|
| Page marked "Functional" but API returns errors | Typos (fix directly via PR) |
| Endpoint count mismatch | Formatting issues |
| Backend returns hardcoded data but docs say "database-connected" | Style preferences |
| Feature documented but not implemented | Suggestions (use Discussions) |

### How to Report

1. **Open an Issue** with title: `[Doc Discrepancy] <brief description>`
2. **Include:**
   - File path with the incorrect claim
   - What the documentation says
   - What you observed (with evidence)
   - Steps to reproduce
3. **We respond within 48 hours**

### Why This Matters

Per [GOVERNANCE.md](.kiro/steering/GOVERNANCE.md), all claims must be evidence-based. Documentation that overstates readiness undermines trust. We'd rather correct errors publicly than have users discover them unexpectedly.

---

## Final Statement

> **BijMantra exists because agricultural truth emerges at the intersection of disciplines.  
> Your contribution should strengthen that intersection.**

Welcome to the project.

---

**Thank you for contributing to BijMantra!** 🙏

[![Sponsor](https://img.shields.io/badge/💖_Sponsor-GitHub_Sponsors-ea4aaa?style=for-the-badge)](https://github.com/sponsors/denishdholaria)
