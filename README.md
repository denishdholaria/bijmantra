<div align="center">

<img src="frontend/public/icons/icon-512x512.png" alt="BijMantra Logo" width="180"/>

# BijMantra
## (Under Development)
### Cross-domain agricultural intelligence platform for breeding, seed, research, and institutional workflows

## ⚠️ Important Notice — Official BijMantra Domain

We have recently become aware of a third-party website operating under the domain **bijmantra.com**.

For clarity:

* The **official BijMantra project is only available at:** https://bijmantra.org
* Any other domain is **not operated or maintained by the core project team**

BijMantra is an open-source initiative, and while reuse of the codebase is permitted under its license, **no third party is authorized to represent itself as the official BijMantra platform or use its branding in a misleading manner**.

Users are advised to:

* Verify the domain before interacting with any BijMantra-related service
* Avoid sharing sensitive data or making payments on unofficial platforms

We are currently reviewing the situation and taking appropriate steps.

If you encounter any suspicious activity or have questions, please reach out through our official channels.


> **Status as of <!-- METRIC:LAST_UPDATED -->2026-04-20<!-- /METRIC -->:** 
- BijMantra is currently in preview, with ongoing refactoring across the platform. While the overall system footprint is substantial, the REEVU intelligence layer and broader architecture are still undergoing stabilization and hardening.

- Progress is slow and steady, but intentionally measured. Agricultural decision systems demand rigorous handling of evidence contracts, data provenance, validation pipelines, and cross-domain behavior before they can be considered production-ready.

- Development is also constrained by limited funding and compute resources. Efficient allocation of AI credits requires careful planning and prioritization. Current tooling subscriptions—such as GitHub Copilot Pro, Kiro Pro, and Antigravity/Google AI Pro -- services—provide essential support but are quickly exhausted, necessitating disciplined usage to maintain continuity of development.

- Despite these constraints, foundational progress continues with a focus on long-term robustness and reliability rather than rapid iteration.


🌐 **[bijmantra.org](https://bijmantra.org)**

---

[![Stars](https://img.shields.io/github/stars/denishdholaria/bijmantra?style=for-the-badge&logo=github&color=gold)](https://github.com/denishdholaria/bijmantra)

[**Get Started**](#quick-start) · [**Current Reality**](#current-reality) · [**Contributing**](#contributing) · [**Docs**](#key-documents)

</div>

---

> **A Note on Documentation Accuracy**
> BijMantra is under active development across genomics, agronomy, AI, interoperability, and full-stack engineering. Exact totals move quickly. For implementation counts and the latest repository snapshot, prefer [metrics.json](metrics.json). If you find a discrepancy, please [open an issue](https://github.com/denishdholaria/bijmantra/issues).

## What BijMantra Is

BijMantra is a server-backed agricultural intelligence platform being built for breeding programs, seed organizations, research institutions, and agricultural administrators that need one system to connect workflows usually split across separate tools: plant breeding, germplasm and seed banks, seed operations, environmental context, research knowledge, and institutional administration.

It is not intended to be a generic dashboard layer. The goal is to make agricultural decisions less fragmented by keeping genetic, operational, environmental, and institutional context closer together.

At a larger level, BijMantra is also being shaped as an advanced agricultural extension system: a platform that can help shorten the long distance between scientific discovery, institutional validation, and practical field adoption.

The name is literal:

- Bij = seed
- Mantra = utterance or formulation

## Why Institutions Care

Agricultural organizations rarely make decisions in a single domain. Breeding strategy, trial interpretation, seed operations, environmental constraints, and institutional reporting often live in separate systems, which raises coordination cost and slows the movement of scientific insight into usable field decisions.

BijMantra is being built for organizations that need more than dashboards:

- breeding and genomics programs coordinating selection, trials, and performance evidence
- seed organizations linking germplasm, inventory, operations, and placement decisions
- research institutions trying to connect datasets, workflows, and evidence across departments
- public and institutional teams that need interoperable systems with clearer provenance and less manual reconciliation

The commercial and institutional relevance is not just digitization. It is a platform thesis: decisions improve when genetic, operational, environmental, and institutional context can be handled closer together instead of being reconciled manually across disconnected tools.

## Why This Is Hard

Agricultural software becomes weak when it treats each problem as isolated.

BijMantra is hard to build because it sits at the intersection of several difficult constraints:

- Agricultural workflows cross breeding, seed systems, field operations, environment, and knowledge management.
- In agriculture, there is often a 5-15 year gap between research results and broad farmer adoption, driven by validation cycles, limited extension capacity, and risk-aware decision making in the field.
- Data quality is uneven, historical records are inconsistent, and institutional practices vary widely.
- Scientific outputs need provenance, assumptions, and uncertainty, not just values on a screen.
- Some workflows need better resilience under weak connectivity, but the platform still depends on authenticated server-backed flows.
- Hybrid compute makes sense here, but it raises the bar for contracts, validation, and long-term maintenance.

That means the real challenge is not only building software. It is building a system that can carry research insight across institutional, operational, and field-level boundaries in a form people can trust enough to use.

## Current Scope

BijMantra remains in preview.

The repository already spans breeding, genomics, gene bank, seed operations, environment, knowledge, and administration, but those areas do not yet share the same maturity or verification depth.

That breadth shows platform direction, not complete production readiness. Some surfaces are already functional, some are being hardened, and some UI mock-up or placeholder views remain as deliberate markers for modules, workflows, or screens still being built.

## What Is Still In Progress

Important areas still in progress include:

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

The first startup can take a while because BijMantra may need to install several dependencies and development tools before it can run.

Frontend workflows now use `bun` as the canonical package manager. Do not default to `npm` or `pnpm` for repo setup, installs, or frontend script execution.

1. Install one IDE: Antigravity, VS Code, or Kiro.
2. Sign in to your IDE account.
3. Open the IDE chat panel and give the agent permission to use the terminal, file system, and Git when prompted.
4. Paste this instruction into the chat:

```text
Clone my public repository https://github.com/denishdholaria/bijmantra.git and start BijMantra locally. Install everything required for first-time setup, follow the README, use Podman rather than Docker, and run both the backend and frontend. Expect the first startup to take a while because dependencies and services may need to be installed and initialized.
```

5. After setup finishes, open these local URLs:
   - Frontend: `http://localhost:5173`
   - API docs: `http://localhost:8000/docs`

If the agent asks to install missing tools such as Podman, Python, Bun, Node.js, or Make, approve those steps. Dependency installation, container image pulls, and service initialization can take several minutes on first setup.

```bash
git clone https://github.com/denishdholaria/bijmantra.git bijmantra && cd bijmantra
bash ./start-bijmantra-app.sh

# Or use the split dev flow
make dev            # Start PostgreSQL only
make dev-all        # Optional: start Redis, MinIO, and Meilisearch too
make dev-backend    # → http://localhost:8000
make dev-frontend   # → http://localhost:5173
```

If you are using an AI agent after the first boot, prefer the repo-owned workflow surfaces instead of rewriting instructions:

- Operator routing: `.github/docs/ai/2026-03-30-ai-operator-quickstart.md`
- Local startup diagnosis: `make startup-doctor`
- Alembic and schema diagnosis: `make migration-doctor`
- Baseline review guardrails: `make pr-review-pack`

| Service       | URL                                                    |
| ------------- | ------------------------------------------------------ |
| 🌐 Frontend   | [localhost:5173](http://localhost:5173)                   |
| 📡 API Docs   | [localhost:8000/docs](http://localhost:8000/docs)         |
| 🔌 BrAPI v2.1 | [localhost:8000/brapi/v2](http://localhost:8000/brapi/v2) |

<details>
<summary><b>View Tech Stack Details</b></summary>
<br />

| Layer              | Technology                                                                                                  |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| **Frontend** | React 19 · TypeScript 5 · Vite · Bun · PWA shell                                                        |
| **Backend**  | Python 3.15+ · FastAPI · SQLAlchemy · NumPy · SciPy                                                     |
| **Compute**  | Rust → WebAssembly · Fortran                                                                              |
| **Data**     | PostgreSQL · PostGIS · pgvector · Redis · MinIO                                                         |
| **AI**       | Multi-provider LLM support · RAG · REEVU (REEVU = Reason → Evidence → Evaluation → Validation → Unit) |
| **Interop**  | BrAPI v2.1 compatibility work plus repo-specific API surface                                                |

</details>

## Runtime Boundary

BijMantra can boot from a fresh public clone without live claw runtime folders in the repo root.

- The product repo only keeps public-safe contract material and sanitized bootstrap examples such as `.openclaw.example/` and `.nemoclaw.example/`.
- Live claw runtime state, auth stores, device identity, session history, watchdog output, and cron state must stay outside the repo in an operator-managed runtime home such as `~/.bijmantra/runtime/claw`.
- Operator-only execution surfaces such as the claw compose stack and launcher/watchdog/bridge control scripts are treated as private execution fabric rather than public product contract. In the private repo view, that staged boundary now lives under `ops-private/claw-runtime/`.

---

## Contributing

BijMantra welcomes builders, scientists, and institutions committed to serious agricultural R&D infrastructure. **You do not need to be an agriculture expert to contribute.**

<details>
<summary><b>How to Contribute (Developers & Scientists)</b></summary>
<br />

### Quick Wins (< 30 minutes)

| Action                    | Impact                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------- |
| ⭐**Star the repo** | Signals community interest to funders                                                             |
| 🐛**Report a bug**  | [Open an issue](https://github.com/denishdholaria/bijmantra/issues) — even "this confused me" helps |
| 📝**Fix a typo**    | PRs welcome on docs, comments, UI text                                                            |

### For Developers

Use `bun` for frontend dependency installation and script execution from here onward. Repository examples and local frontend workflows should prefer `bun install` and `bun run ...`, not `npm` or `pnpm`.

| Area                | Good First Issues                                         |
| ------------------- | --------------------------------------------------------- |
| **Frontend**  | Component polish, accessibility improvements, page wiring |
| **Backend**   | API endpoint coverage, test coverage expansion            |
| **Rust/WASM** | Genomic algorithm optimization, new compute modules       |
| **DevOps**    | CI/CD improvements, container optimization                |

```bash
# Fork, clone, and start developing
git clone https://github.com/YOUR_USERNAME/bijmantra.git && cd bijmantra
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

BijMantra is being built as source-available agricultural research infrastructure: interoperable where possible, modular, and intended for serious institutional use.

The most useful relationships at this stage are:

- institutional pilots around breeding, seed, research, or administrative workflows
- interoperability and integration work in BrAPI-aligned or multi-system environments
- research collaborations focused on provenance, validation, and cross-domain decision support
- licensing and deployment discussions for organizations evaluating long-term use

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

**Bij** = Seed · **Mantra** = Sacred Utterance — the primordial sound from which the universes were seeded.

The project exists to reduce fragmentation in agricultural data and decisions, and to help serious agricultural knowledge move more effectively from research and institutions into usable practice. It does not assume software alone solves agriculture.

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
