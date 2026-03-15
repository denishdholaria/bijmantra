<div align="center">

<img src="frontend/public/icons/icon-512x512.png" alt="BijMantra Logo" width="180"/>

# BijMantra

## (Under Development)

> # 🚧 Architectural Refactoring In Progress (Date: 2026-03-15)

Cross-domain agricultural intelligence platform

🌐 **[bijmantra.org](https://bijmantra.org)**

---

[![Stars](https://img.shields.io/github/stars/denishdholaria/bijmantra?style=for-the-badge&logo=github&color=gold)](https://github.com/denishdholaria/bijmantra)

[**Get Started**](#quick-start) · [**Current Reality**](#current-reality) · [**Contributing**](#contributing) · [**Docs**](#key-documents)

</div>

---

> **A Note on Documentation Accuracy**
> BijMantra is under active development across genomics, agronomy, AI, interoperability, and full-stack engineering. Exact totals move quickly. For implementation counts and the latest repository snapshot, prefer [metrics.json](metrics.json). If you find a discrepancy, please [open an issue](https://github.com/denishdholaria/bijmantra/issues).

## What BijMantra Is

BijMantra is a server-backed agricultural software platform being built to connect workflows that are usually split across separate systems: plant breeding, germplasm and seed banks, seed operations, environmental context, research knowledge, and institutional administration.

The project is not trying to be a generic dashboard layer. It is trying to make agricultural decisions less fragmented by keeping genetic, operational, environmental, and institutional context closer together.

The name is literal:

- Bij = seed
- Mantra = utterance or formulation

## Current Reality

Snapshot date: 2026-03-08 from [metrics.json](metrics.json).

- 200+ application pages across 5 workspaces
- 1500+ API endpoints, including 200+ BrAPI endpoints
- 8 major domain modules
- React 19 + TypeScript + Vite frontend
- FastAPI + PostgreSQL + PostGIS + pgvector + Redis backend stack
- Rust/WASM and Fortran compute components in the wider architecture
- Limited low-connectivity and buffered workflows exist, but the product is not broadly offline-capable today

The exact counts above will drift. This README keeps rounded values on purpose.

## Why This Is Hard

Agricultural software becomes weak when it treats each problem as isolated.

BijMantra is hard to build because it sits at the intersection of several difficult constraints:

- Agricultural workflows cross breeding, seed systems, field operations, environment, and knowledge management.
- Data quality is uneven, historical records are inconsistent, and institutional practices vary widely.
- Scientific outputs need provenance, assumptions, and uncertainty, not just values on a screen.
- Some workflows need better resilience under weak connectivity, but the platform still depends on authenticated server-backed flows.
- Hybrid compute makes sense here, but it raises the bar for contracts, validation, and long-term maintenance.

## Current Scope

BijMantra remains in preview.

The repository contains broad surface area across breeding, genomics, gene bank, seed operations, environment, knowledge, and administration, but those areas are not all at the same level of maturity or verification.

At a high level, the current repository includes:

- substantial frontend and backend coverage across multiple agricultural domains
- a large API surface, including BrAPI-compatible work
- local development infrastructure around PostgreSQL, Redis, and MinIO
- a public documentation site at [bijmantra.org](https://bijmantra.org)
- ongoing compute architecture involving Rust/WASM and Fortran components

That scope should be read as an indicator of platform breadth, not as a guarantee of completeness, stability, or production readiness. Validation depth varies by module, and preview status remains intentional until further notice.

## What Is Still In Progress

Several important areas still need continued work:

- Deeper validation across modules with uneven operational maturity
- Stronger provenance, contract clarity, and scientific guardrails around intelligence layers
- Better low-connectivity support for selected field workflows without overstating offline capability
- Continued cleanup of broad product surface area into clearer, more stable module boundaries
- Documentation that stays aligned with moving implementation totals

## Architectural Evolution

BijMantra is not a small CRUD application. It combines plant breeding science, large biological data models, AI-assisted workflows, and hybrid compute infrastructure.

Because of that scope, the system has already gone through multiple rounds of architectural refactoring. Those changes were driven by real engineering pressure rather than branding:

- scientific features accumulating faster than early boundaries could hold
- module boundaries needing to become more explicit
- AI integration requiring stronger contracts than a simple chat layer
- hybrid Python, Rust/WASM, and Fortran execution needing cleaner separation

Refactoring is treated here as part of building a durable research platform, not as evidence that the effort is directionless.

---

## Quick Start

> **Docker users:** BijMantra uses [Podman](https://podman.io) (rootless, daemonless). Commands are interchangeable.

### Simple Start for Non-Developers

If you are not a developer, the easiest way to start BijMantra is to use an AI-enabled IDE and let the built-in agent handle setup.

The first startup is not instant. BijMantra may need to install several dependencies and development tools before it can run, so the initial setup can take some time.

1. Install one IDE: Antigravity, VS Code, or Kiro.
2. Sign in to your IDE account.
3. Open the IDE chat panel and give the agent permission to use the terminal, file system, and Git when prompted.
4. Paste this instruction into the chat:

```text
Clone public repository https://github.com/denishdholaria/bijmantra.git and start BijMantra locally. Install everything required for first-time setup, follow the README, use Podman rather than Docker, and run both the backend and frontend. Expect the first startup to take a while because dependencies and services may need to be installed and initialized.
```

5. After setup finishes, open these local URLs:
	- Frontend: `http://localhost:5173`
	- API docs: `http://localhost:8000/docs`

If the agent asks to install missing tools such as Podman, Python, Node.js, or Make, approve those steps. On a first-time setup, dependency installation, container image pulls, and service initialization can take several minutes.

```bash
git clone https://github.com/denishdholaria/bijmantra.git bijmantra && cd bijmantra
make dev            # Start PostgreSQL, Redis, MinIO
make dev-backend    # → http://localhost:8000
make dev-frontend   # → http://localhost:5173
```

| Service       | URL                                                    |
| ------------- | ------------------------------------------------------ |
| 🌐 Frontend   | [localhost:5173](http://localhost:5173)                   |
| 📡 API Docs   | [localhost:8000/docs](http://localhost:8000/docs)         |
| 🔌 BrAPI v2.1 | [localhost:8000/brapi/v2](http://localhost:8000/brapi/v2) |

<details>
<summary><b>View Tech Stack Details</b></summary>
<br />

| Layer              | Technology                                                        |
| ------------------ | ----------------------------------------------------------------- |
| **Frontend** | React 19 · TypeScript 5 · Vite · PWA shell |
| **Backend**  | Python 3.13+ · FastAPI · SQLAlchemy · NumPy · SciPy |
| **Compute**  | Rust → WebAssembly · Fortran |
| **Data**     | PostgreSQL · PostGIS · pgvector · Redis · MinIO |
| **AI**       | Multi-provider LLM support · RAG · REEVU |
| **Interop**  | BrAPI v2.1 compatibility work plus repo-specific API surface |

</details>

---

## Contributing

BijMantra welcomes builders, scientists, and institutions committed to serious agricultural R&D infrastructure. **You do not need to be an agriculture expert to contribute.**

<details>
<summary><b>How to Contribute (Developers & Scientists)</b></summary>
<br />

### Quick Wins (< 30 minutes)

| Action                    | Impact                                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| ⭐**Star the repo** | Signals community interest to funders                                                                |
| 🐛**Report a bug**  | [Open an issue](https://github.com/denishdholaria/bijmantra/issues) — even "this confused me" helps |
| 📝**Fix a typo**    | PRs welcome on docs, comments, UI text                                                               |

### For Developers

| Area                | Good First Issues                                         |
| ------------------- | --------------------------------------------------------- |
| **Frontend**  | Component polish, accessibility improvements, page wiring |
| **Backend**   | API endpoint coverage, test coverage expansion            |
| **Rust/WASM** | Genomic algorithm optimization, new compute modules       |
| **DevOps**    | CI/CD improvements, container optimization                |

```bash
# Fork, clone, and start developing
git clone https://github.com/YOUR_USERNAME/bijmantra.git && cd bijmantraorg
make dev && make dev-backend && make dev-frontend
```

📄 [CONTRIBUTING.md](CONTRIBUTING.md) · [CONTRIBUTOR_ENTRY.md](CONTRIBUTOR_ENTRY.md)

### For Domain Scientists

BijMantra's algorithms need validation from people who understand the science. If you work in **plant breeding, genomics, agronomy, soil science, or agricultural economics** — your review of any module is worth more than a thousand lines of code.

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org)

</details>

---

## Support and Collaboration

**Climate volatility is rewriting agricultural reality.** Food systems are already under pressure to produce more with less land, less water, and higher environmental uncertainty.

BijMantra is being built as open agricultural research infrastructure: interoperable where possible, modular, and intended for serious institutional use.

If you want to support the work, collaborate institutionally, or understand sponsorship mechanics, use the dedicated documents rather than treating this README as a funding prospectus.

- [FUNDING.md](FUNDING.md)
- [SPONSORS.md](SPONSORS.md)
- [hello@bijmantra.org](mailto:hello@bijmantra.org)

---

**🚫 Prohibited:** Terminator seeds, GURTs, and seed dependency technologies.

📄 [LICENSE](LICENSE) · [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) · [ETHICAL_USE_POLICY.md](ETHICAL_USE_POLICY.md)

---

## Working Principle

> **"Agricultural truth emerges at the intersection of disciplines. BijMantra makes that intersection computable."**

**Bij** (बीज) = Seed · **Mantra** (मन्त्र) = Sacred Utterance — the primordial sound from which the universes were seeded.

The project exists to reduce fragmentation in agricultural data and decisions, not to promise that software alone solves agriculture.

---

## Key Documents

- [metrics.json](metrics.json) — moving implementation snapshot
- [CONTRIBUTING.md](CONTRIBUTING.md) — contributor workflow
- [CONTRIBUTOR_ENTRY.md](CONTRIBUTOR_ENTRY.md) — contributor orientation
- [ETHICAL_USE_POLICY.md](ETHICAL_USE_POLICY.md) — prohibited and restricted uses
- [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) — commercial licensing terms
- [FUNDING.md](FUNDING.md) — support and backing details
- [SPONSORS.md](SPONSORS.md) — sponsorship program details

---

<div align="center">

### Contact

[![Star](https://img.shields.io/badge/⭐_Star_This_Repo-2_seconds-gold?style=for-the-badge)](https://github.com/denishdholaria/bijmantra)
[![Partner](https://img.shields.io/badge/💼_Partner_With_BijMantra-strategic-EA4AAA?style=for-the-badge)](https://github.com/sponsors/denishdholaria)
[![Issues](https://img.shields.io/badge/🐛_Report_Bug-5_minutes-blue?style=for-the-badge)](https://github.com/denishdholaria/bijmantra/issues)

---

**Built for researchers and institutions working toward stronger agricultural decisions.**

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org) · 🔗 [LinkedIn](https://www.linkedin.com/in/denishdholaria) · 🌐 [bijmantra.org](https://bijmantra.org)

</div>
