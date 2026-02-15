<div align="center">

<img src="frontend/public/icons/icon-512x512.png" alt="BijMantra Logo" width="200"/>

# BijMantra

### _Cross-Domain Agricultural Intelligence Platform_

**Unifying fragmented agricultural knowledge through AI-assisted reasoning**

🌐 **[bijmantra.org](https://bijmantra.org)**

---

[![License](https://img.shields.io/badge/License-AGPL--3.0%20%2B%20Commercial-green?style=for-the-badge)](LICENSE)
[![BrAPI](https://img.shields.io/badge/BrAPI-v2.1_100%25-blue?style=for-the-badge)](https://brapi.org)
[![PWA](https://img.shields.io/badge/PWA-Offline_Capable-purple?style=for-the-badge)](https://web.dev/progressive-web-apps/)
[![Website](https://img.shields.io/badge/Website-bijmantra.org-2E8B57?style=for-the-badge)](https://bijmantra.org)

[**🌐 Website**](https://bijmantra.org) · [**🚀 Quick Start**](#-quick-start) · [**📊 Status**](#-project-status) · [**🔌 APIs**](#-api-catalog) · [**🤝 Contributing**](#-contributing) · [**💰 Fund This Work**](#-this-project-needs-your-support)

</div>

---

> ### 🚀 Development Momentum
>
> **Science Engine**: ✅ 16 engines, 49 tests passing · **Frontend**: 🟢 180+ of 354 pages wired to real APIs · **Bundle**: 📦 14.0 MB
>
> **Current**: Phase 6E — 9 pedigree & domain pages · **Version**: `preview-2 (in progress)`
>
> 📊 [Project Board](https://github.com/users/denishdholaria/projects/3) · 📄 [CALF Assessment](docs/CALF_STATUS.md) · 🐛 [Report Issue](https://github.com/denishdholaria/bijmantra/issues)

---

## 🎯 Why BijMantra Exists

> **"Understanding one domain without seeing its interaction with others produces incomplete, sometimes misleading conclusions."**

Agricultural research is structurally fragmented. Breeders optimize genetics in isolation. Agronomists optimize management without genetic context. Soil scientists study soil without crop feedback. Climate scientists model risk without farm-level adaptation.

**Real-world agricultural decisions do not happen in silos — but our tools still do.**

| Traditional Tools           | BijMantra                   |
| --------------------------- | --------------------------- |
| Data aggregation            | **Knowledge synthesis**     |
| Single-domain dashboards    | **Cross-domain reasoning**  |
| AI as chatbot               | **AI as domain integrator** |
| Tools for rich institutions | **Tools for the world**     |

BijMantra exists to bridge this gap: **a platform where AI assists reasoning across multiple scientific domains** — genetics, agronomy, soil science, climate, and economics — not just within them.

---

## 🙏 An Honest Note from the Creator

This platform represents **19+ months of solo development**. Over 330,000 lines of code. 354 pages. 1,644 API endpoints. 100% BrAPI v2.1 compatible. A dedicated domain at [bijmantra.org](https://bijmantra.org). All built by one person — not backed by any institution, not funded by any grant, and with zero external funding to date. The only material support has come from my employer, who generously allows me to use company hardware to develop this project alongside my day job — a gesture of goodwill that I am deeply grateful for, and without which this work would not have been possible.

**This is plea; it is a necessity for the future generations. I write this because agricultural resilience is the mission of our age, and building this infrastructure is the standard of greatness we must achieve to secure the world's food supply.** BijMantra exists to fix fragmented agricultural research — **not as a product, not as a startup, but as research infrastructure for the world.**

One person cannot build the future of agricultural research alone. This project needs:

- **Your feedback** — even a GitHub issue saying "this page doesn't work" helps
- **Your expertise** — domain scientists who can validate that the algorithms are correct
- **Your code** — developers who can pick up a module and make it better
- **Your funding** — even small contributions keep the infrastructure running
- **Your voice** — sharing this project with someone who might care

If you've cloned this repo, if you've tried the app, if you've read this far — **please consider giving something back**. A star. An issue. A message. Anything.

**Climate change does not care about borders. Neither should our solutions.**

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org) · 💖 [Sponsor on GitHub](https://github.com/sponsors/denishdholaria) · 💰 [Open Collective](https://opencollective.com/bijmantra)

---

## 🧠 The BijMantra Mental Model (30 Seconds)

```
Breeding Program → Trial Design → Phenotyping → Genomics → Selection Decisions
       ↕               ↕              ↕             ↕              ↕
    Soil Data     Climate Risk    Economics    Pest Pressure   Market Demand
```

Most tools support **one box**. BijMantra connects the **entire flow** — and the interactions between them — into a single computational system.

---

## ⚡ At a Glance

| 📊 Scale                          | 🎯 Computational Status           |
| --------------------------------- | --------------------------------- |
| **354** Pages                     | **180+** Using Real API Calls     |
| **1644** API Endpoints            | **278** Database Tables           |
| **8** Modules + **10** Divisions  | **103** RLS-Protected Tables      |
| **201/201** BrAPI v2.1            | **100%** Spec Complete ✅         |
| **106** Real Computation Pages    | **5** WASM High-Performance Pages |
| **16** Science Engines (49 Tests) | **14.0 MB** Full Build Bundle     |
| **1,618** Smoke Tests Passing     | **102** E2E Tests Passing         |
| **0** Backend Demo Data Arrays    | **0** Auth Guard Gaps             |

---

`<a id="reality-check"></a>`

## ⚠️ Reality Check: What Actually Works Today

**This section exists to prevent misunderstanding.** BijMantra believes in radical honesty. If you are evaluating this platform for research, funding, or contribution, read this carefully.

### CALF Assessment (February 2026)

CALF (Computational Analysis & Functionality Level) is our internal audit system. Every page is classified by what it actually does, not what it claims to do.

| CALF Level | Description             | Count | %      | Status                      |
| ---------- | ----------------------- | ----- | ------ | --------------------------- |
| **CALF-0** | Display Only            | 95    | 27%    | ✅ Acceptable               |
| **CALF-1** | Client-Side Calculation | 76    | 21%    | 🟡 Needs backend validation |
| **CALF-2** | Demo Data               | **3** | **1%** | ✅ Nearly eliminated        |
| **CALF-3** | Real Computation        | 69    | 19%    | ✅ Major improvement        |
| **CALF-4** | WASM High-Performance   | 5     | 1%     | ✅ Excellent                |
| —          | Division Pages          | 106   | 30%    | ✅ Integrated               |

**Progress since January 9, 2026:** CALF-2 (demo data) dropped from **42 pages to 3** (Vision module only). 39 pages converted to real database queries. Zero DEMO\_\* arrays remain in the backend. 8 demo service files deleted (−3,961 lines), 7 API files rewritten to real DB queries (+1,429 lines).

📄 **[Full CALF Assessment](docs/CALF_STATUS.md)** — Comprehensive audit with code evidence

> 📊 **Live Metrics:** See [`metrics.json`](metrics.json) for current statistics

---

## 💰 This Project Needs Your Support

<div align="center">

### The Reality of Building for the World — Alone

</div>

BijMantra is built for **every agricultural researcher on the planet** — not just those at well-funded institutions in wealthy countries. A plant breeder in sub-Saharan Africa deserves the same computational tools as one at a European university. An agronomist in rural India should have access to the same cross-domain intelligence as a CGIAR center.

**But building global research infrastructure costs money.** Domain registration, cloud hosting, CI/CD compute, SSL certificates, search infrastructure, database hosting — these are real, recurring costs that one person's savings cannot sustain indefinitely.

### What Funding Enables

| Need                      | Monthly Cost | Impact                                             |
| ------------------------- | ------------ | -------------------------------------------------- |
| **Cloud Infrastructure**  | ~$200        | PostgreSQL, Redis, Meilisearch, object storage     |
| **Domain & SSL**          | ~$15         | [bijmantra.org](https://bijmantra.org) stays alive |
| **CI/CD Minutes**         | ~$20         | Automated testing on every code change             |
| **Full-Time Development** | —            | Creator can focus on this instead of contract work |

### How to Fund

| Channel                      | Link                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------- |
| 💖**GitHub Sponsors**        | [github.com/sponsors/denishdholaria](https://github.com/sponsors/denishdholaria) |
| 💰**Open Collective**        | [opencollective.com/bijmantra](https://opencollective.com/bijmantra)             |
| 📧**Direct / Institutional** | [hello@bijmantra.org](mailto:hello@bijmantra.org)                                |

**Every contribution is publicly tracked.** Open Collective provides full financial transparency — all income and expenses are visible.

### Institutional Partners Welcome

We actively seek partnerships with organizations that understand that **agricultural research infrastructure is a global public good**:

- **CGIAR Centers** — IRRI, CIMMYT, ICRISAT, ICARDA, and others
- **Philanthropic Foundations** — Gates Foundation, Rockefeller Foundation, McKnight Foundation
- **Government Agencies** — USAID, DFID, GIZ, ICAR, EMBRAPA
- **Universities** — Any institution running plant breeding programs
- **Private Sector** — Seed companies and AgTech firms who benefit from open standards

> 📄 **[FUNDING.md](FUNDING.md)** — Detailed funding tiers, use of funds, and UN SDG alignment

---

## 👥 Who BijMantra Is For

**BijMantra is for:**

- Plant breeders running real breeding programs (public or private, any country)
- Researchers tired of siloed tools and CSV glue between systems
- Institutions that value correctness over dashboards
- Developers interested in scientific computing + modern web architecture
- Anyone who believes agricultural tools should be accessible to all

**BijMantra is NOT for:**

- Quick demo seekers expecting a polished SaaS product
- Pure visualization / dashboard-only use cases
- "AI chatbot for agriculture" expectations
- Production deployment (yet — wait for `1.0.0`)

---

## 🧩 What Makes BijMantra Technically Unusual

Most agricultural software does one thing. BijMantra does something different:

- **16 validated science engines** — Genomic prediction, spatial analysis, mixed models, GWAS, and more (49 tests)
- **WASM genomics** running inside the browser — not server-side (Rust → WebAssembly)
- **Row-Level Security** as a first-class architectural primitive (103 tables)
- **Offline-capable data collection** — field data entry works without internet connectivity
- **100% BrAPI v2.1 compatible** — 201/201 endpoints for global interoperability
- **Cross-domain AI reasoning** — breeding decisions surface soil, climate, and economic factors
- **AI governance framework** — Anti-regression rules, failure journal, and structured decision logs for long-term continuity
- **Multi-language compute stack** — Python (NumPy/SciPy), Rust/WASM (genomics matrices), FastAPI (API layer)

---

## 🏛️ Platform Architecture: 8 Modules + 10 Divisions

BijMantra is organized into **core modules** (the scientific backbone) and **divisions** (specialized operational domains). This architecture is designed to grow — new divisions can be added without disrupting existing modules.

### Core Modules — Scientific Foundation

| Module                 | Endpoints | Pages | Status          | Focus                                             |
| ---------------------- | --------- | ----- | --------------- | ------------------------------------------------- |
| 🌾**Breeding**         | 126       | 35    | 🟢 Improving    | Programs, trials, crosses, selection decisions    |
| 📋**Phenotyping**      | 88        | 28    | 🟡 Partial      | Observations, traits, field data collection       |
| 🧬**Genomics**         | 110       | 35    | 🟢 Improving    | Variants, markers, QTL, GWAS, population genetics |
| 🏛️**Seed Bank**        | 59        | 15    | ⚪ Display only | Accessions, conservation, germplasm exchange      |
| 🌍**Environment**      | 117       | 22    | ⚪ Display only | Climate, soil, weather, spatial analysis          |
| 🏭**Seed Operations**  | 99        | 22    | 🟡 Partial      | Processing, quality, dispatch, certification      |
| 📚**Knowledge**        | 35        | 5     | ⚪ Display only | Ontologies, protocols, references                 |
| ⚙️**Settings & Admin** | 79        | 35    | ✅ Functional   | Users, roles, RLS, audit, system health           |

### Divisions — Specialized Operational Domains (106 pages)

Divisions were introduced in February 2026 to accommodate operational areas that span multiple modules or serve specialized workflows.

| Division                | Pages | Status               | Scope                                                           |
| ----------------------- | ----- | -------------------- | --------------------------------------------------------------- |
| 🏦**Seed Bank**         | 17    | 🟢 Mostly functional | Accession management, GRIN search, vault monitoring, MTA        |
| 🏭**Seed Operations**   | 17    | 🟢 Mostly functional | Processing, dispatch, lab testing, quality gates, lineage       |
| 🔮**Future**            | 19    | 🟡 Mixed             | Emerging capabilities — vision, AI training, advanced analytics |
| 📚**Knowledge**         | 10    | 🟡 Display           | Forums, publications, protocols, training hub                   |
| 📡**Sensor Networks**   | 7     | 🟡 Mixed             | IoT devices, live data, alerts, field monitoring                |
| 🌿**Plant Sciences**    | 5     | 🟢 Functional        | Crop physiology, phenomics, abiotic/biotic stress               |
| 💼**Commercial**        | 4     | 🟡 Partial           | Market analysis, stakeholder portal, agreements                 |
| ☀️**Sun-Earth Systems** | 4     | ⚪ Display           | Solar activity, photoperiod, UV index                           |
| 🛰️**Space Research**    | 4     | ⚪ Display           | Remote sensing, satellite imagery                               |
| 🔗**Integrations**      | 1     | ⚪ Display           | External system connectors                                      |

---

## ✨ Key Features

| Feature                        | Description                                                | Status              |
| ------------------------------ | ---------------------------------------------------------- | ------------------- |
| 🪷**Veena AI**                 | Cross-domain agricultural intelligence assistant           | 🟡 Multiple Trials  |
| 🔗**Cross-Domain Reasoning**   | Breeding decisions surface soil, climate, economic factors | 🟡 Partial          |
| 🧬**Genomic Selection**        | WASM-powered GBLUP, QTL mapping in browser                 | ✅ WASM functional  |
| 🌍**PWA with Offline Support** | Installable app, offline data collection for field work    | ✅ Implemented      |
| 🌱**BrAPI v2.1**               | 201/201 endpoints — full international spec compatible     | ✅ Complete         |
| 🚪**Workspace Gateway**        | 5 role-based workspaces                                    | ✅ Implemented      |
| 🔐**Row-Level Security**       | 103 tables with RLS policies — multi-tenant by default     | ✅ Complete         |
| 🖥️**Web-OS Shell**             | Unified desktop shell (SystemBar, Dock, STRATA, Sidebar)   | ✅ Complete         |
| ♿**Accessibility**            | WCAG 2 AA compliant                                        | ✅ 17 tests passing |

---

## 🚀 Quick Start

> **Docker users**: BijMantra uses [Podman](https://podman.io) (rootless, daemonless). Commands are identical — just use `podman` instead of `docker`.

\`\`\`bash
git clone https://github.com/denishdholaria/bijmantra.git && cd bijmantra
make dev # Start PostgreSQL, Redis, MinIO (Podman)
make dev-backend # → http://localhost:8000
make dev-frontend # → http://localhost:5173
\`\`\`

| Service     | URL                                                       |
| ----------- | --------------------------------------------------------- |
| 🌐 Frontend | [localhost:5173](http://localhost:5173)                   |
| 📡 API Docs | [localhost:8000/docs](http://localhost:8000/docs)         |
| 🔌 BrAPI    | [localhost:8000/brapi/v2](http://localhost:8000/brapi/v2) |

> **If you try BijMantra** — even for 5 minutes — please [open an issue](https://github.com/denishdholaria/bijmantra/issues) with your experience. What worked. What didn't. What confused you. This feedback is more valuable than you might think.

---

## 📊 Project Status

### Current Version

> 📊 **Authoritative source:** [`metrics.json`](metrics.json)
> 📊 **Live tracker:** [GitHub Project Board](https://github.com/users/denishdholaria/projects/3)

| Field    | Value                                    |
| -------- | ---------------------------------------- |
| Version  | `preview-2 (in progress)`                |
| Codename | Prathama (प्रथम) — "The First"           |
| Phase    | Science Engine Complete, Frontend Wiring |
| Status   | 180+ pages wired, 9 more in progress     |

### Recent Milestones (February 2026)

| Milestone                                                 | Status         |
| --------------------------------------------------------- | -------------- |
| 🧮 Science Engine — 16 engines, 49 tests (44 Py + 5 Rust) | ✅ Complete    |
| 🧬 Phase 6A — 12 BrAPI genotyping pages wired             | ✅ Complete    |
| 🌱 Phase 6B — 10 breeding domain pages wired              | ✅ Complete    |
| 🧬 Phase 6C — 5 genomics advanced pages (GWAS, QTL, LD)   | ✅ Complete    |
| 📈 Phase 6D — 5 analytics pages + SpATS integration       | ✅ Complete    |
| 🔵 Phase 6E — 9 pedigree & domain pages                   | 🟡 In Progress |
| 👁️ Phase 7 — Vision Module (5 pages)                      | ⬜ Queued      |
| 🤖 Veena Milestone — Cross-domain AI reasoning            | ⬜ Queued      |

### Path to Stable Release

\`\`\`
preview-1 ✅ COMPLETE (Demo data eliminated, base wiring done)
↓
preview-2 ← CURRENT (All pages wired to real APIs, science engines live)
↓
v1.0 Science Engine (Backend validation, CALF >90%)
↓
v1.1 Vision & AI (Vision module, Veena cross-domain reasoning)
↓
1.0.0 Stable Release
\`\`\`

---

## 🧪 Testing Status

> 📊 **Source:** [`metrics.json`](metrics.json)

| Test Type           | Count | Status       |
| ------------------- | ----- | ------------ |
| Smoke Tests         | 1,618 | ✅ Passing   |
| E2E Tests           | 102   | ✅ Passing   |
| Backend Test Files  | 58    | ✅ Active    |
| Total Tests         | 84    | ✅ Active    |
| Auth Guard Coverage | 100%  | ✅ Zero gaps |
| Accessibility       | 17    | ✅ Passing   |

**CI/CD:** 4 active GitHub Actions workflows with path-based filtering. Code changes trigger CI. Documentation changes do not.

---

## 🔌 API Catalog

> 📊 **Source:** [`metrics.json`](metrics.json) → `api` section

**Total: 1644 endpoints** · BrAPI v2.1: 201 (100%) · BijMantra: 1443

| Category          | Endpoints | Prefix       | Status       |
| ----------------- | --------- | ------------ | ------------ |
| BrAPI Core        | 50        | `/brapi/v2/` | ✅ Real data |
| BrAPI Germplasm   | 39        | `/brapi/v2/` | ✅ Real data |
| BrAPI Phenotyping | 51        | `/brapi/v2/` | ✅ Real data |
| BrAPI Genotyping  | 61        | `/brapi/v2/` | ✅ Real data |
| BijMantra APIs    | 1443      | `/api/v2/`   | ⚠️ See CALF  |

---

## 🤝 Contributing

<div align="center">

### Every Contribution Matters — Yes, Even Yours

</div>

You do not need to be an expert to contribute. You do not need to write code. Here is what helps:

| Contribution                  | Effort     | Impact                                 |
| ----------------------------- | ---------- | -------------------------------------- |
| ⭐**Star the repo**           | 2 seconds  | Signals community interest to funders  |
| 🐛**Report a bug**            | 5 minutes  | Helps fix real problems                |
| 💬**Open a discussion**       | 10 minutes | Shapes the project's direction         |
| 📝**Improve documentation**   | 30 minutes | Helps the next person who tries this   |
| 🔧**Fix a small bug**         | 1-2 hours  | Direct improvement to the platform     |
| 🧬**Validate an algorithm**   | Variable   | Domain expertise is irreplaceable      |
| 🌍**Translate the UI**        | Variable   | Makes the platform accessible globally |
| 📢**Share with your network** | 1 minute   | Reaches people who need this           |

### For Developers

**Stack:** React 18 + TypeScript 5 + Vite 7.3 (frontend) · Python 3.14 + FastAPI + NumPy/SciPy (backend) · Rust/WASM (genomics) · PostgreSQL 17 + PostGIS + pgvector

\`\`\`bash

# Get started

git clone https://github.com/denishdholaria/bijmantra.git && cd bijmantra
make dev && make dev-backend && make dev-frontend
\`\`\`

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide · [CONTRIBUTOR_ENTRY.md](CONTRIBUTOR_ENTRY.md) for role-based entry points

### For Domain Scientists

BijMantra's algorithms need validation from people who understand the science. If you work in plant breeding, genomics, agronomy, soil science, or agricultural economics — **your review of any single module is worth more than a thousand lines of code.**

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org)

---

## 🌍 A Note About Global Equity

<div align="center">

**Climate change does not care about borders.**

**Neither does hunger. Neither does soil degradation. Neither should our tools.**

</div>

The most advanced agricultural software in the world sits behind institutional paywalls, requires expensive licenses, or assumes infrastructure that does not exist in most of the world. A researcher in Niger, a breeder in Bangladesh, a seed bank curator in Peru — they face the same scientific challenges as their counterparts at well-funded Western institutions, but with a fraction of the tools.

BijMantra is **open source by conviction, not by convenience**. The AGPL-3.0 license ensures that improvements flow back to the community. The BrAPI v2.1 compatible ensures interoperability with every other breeding database in the world. The PWA architecture ensures it works on the devices people actually have — including offline, because not every field has internet.

This is not charity. This is engineering for reality.

---

## 📚 Key Documentation

| Document                                                                   | Description                                             |
| -------------------------------------------------------------------------- | ------------------------------------------------------- |
| [README_DEEP_DIVE.md](README_DEEP_DIVE.md)                                 | Technical architecture deep dive                        |
| [CALF_STATUS.md](docs/CALF_STATUS.md)                                      | Computational audit — what actually works (354 pages)   |
| [MASTER-TRACKER.md](.agent/MASTER-TRACKER.md)                              | Living task tracker (The River) — current project state |
| [GitHub Project Board](https://github.com/users/denishdholaria/projects/3) | Visual dashboard — Kanban, Roadmap, Sprint views        |
| [CONTRIBUTOR_ENTRY.md](CONTRIBUTOR_ENTRY.md)                               | Role-based entry points for contributors                |
| [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)                       | System architecture overview                            |
| [PLATFORM_LAW_INDEX.md](docs/architecture/PLATFORM_LAW_INDEX.md)           | Governance framework (14 documents)                     |
| [API_REFERENCE.md](docs/api/API_REFERENCE.md)                              | API documentation                                       |
| [CONTRIBUTING.md](CONTRIBUTING.md)                                         | Contribution guidelines                                 |
| [FUNDING.md](FUNDING.md)                                                   | Funding vision, tiers, and UN SDG alignment             |

---

## 🏛️ Governance & Architecture

BijMantra is governed by a formal **Platform Law Stack** — 14 binding documents organized in 7 layers.

See **[PLATFORM_LAW_INDEX.md](docs/architecture/PLATFORM_LAW_INDEX.md)** for the complete framework.

> The README describes _intent and status_. `ARCHITECTURE.md` defines _system truth_. In case of conflict, architecture documents prevail.

| Layer               | Purpose                                                  |
| ------------------- | -------------------------------------------------------- |
| Foundation          | Evidence-based review (GOVERNANCE.md)                    |
| Architecture        | System shape, data truth                                 |
| External Law        | BrAPI, MCPD, interoperability standards                  |
| Internal Law        | Domain boundaries, schema governance, AI constraints     |
| Operations & Change | Module acceptance, operational playbook, release process |
| Resilience & Memory | Risk mitigation, ADR framework                           |
| Culture             | Contributor onboarding, mindset                          |

> **This is not advisory documentation. This is operational law.**

---

## 📜 License

**Dual License: AGPL-3.0 + Commercial (v4.0)** — _Open Source First, Commercial When Needed_

| ✅ Free (AGPL-3.0)                           | 💰 Commercial License Required          |
| -------------------------------------------- | --------------------------------------- |
| Personal, Educational, Research              | For-profit agro-companies > $1M revenue |
| Individual researchers at ANY institution    | SaaS without source disclosure          |
| Non-profit, Government, CGIAR, Farmer co-ops | Proprietary derivatives                 |
| Small agricultural businesses                | White-labeling / OEM use                |
| Low-income countries (free forever)          | Managed services by for-profit entities |

**🌍 Geographic Equity:** 4-tier system — free forever for low-income countries, grace periods for developing nations, scaled fees for wealthy institutions. Individual researchers always free, everywhere.

**🔮 Future Open Source:** Intended conversion to Apache License 2.0 by January 1, 2030.

**🚫 Prohibited for ALL users:** Terminator seeds, GURTs, seed dependency technologies (with research exemptions)

See [LICENSE](LICENSE) for complete terms · [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for commercial terms & geographic tiers · [ETHICAL_USE_POLICY.md](ETHICAL_USE_POLICY.md) for ethical restrictions

---

## 🌟 Help This Project Reach the People Who Need It

<div align="center">

**You cloned this repo. You read this far. That means something.**

If BijMantra's mission resonates with you — even a little — here is what you can do right now:

| Action                            | Time       | Impact                                         |
| --------------------------------- | ---------- | ---------------------------------------------- |
| ⭐**Star this repository**        | 2 seconds  | Shows funders that people care                 |
| 🔀**Fork the project**            | 5 seconds  | Shows active developer interest                |
| 📢**Share on LinkedIn/X**         | 1 minute   | Reaches agricultural networks                  |
| 🐛**Open an issue**               | 5 minutes  | Direct contribution to the project             |
| 📧**Forward to your institution** | 2 minutes  | Universities and NGOs seek projects to support |
| 💖**Sponsor**                     | Any amount | Keeps the infrastructure running               |

[![GitHub Stars](https://img.shields.io/github/stars/denishdholaria/bijmantra?style=social)](https://github.com/denishdholaria/bijmantra)
[![GitHub Forks](https://img.shields.io/github/forks/denishdholaria/bijmantra?style=social)](https://github.com/denishdholaria/bijmantra/fork)

---

**Know someone at CGIAR, Gates Foundation, USAID, ICAR, EMBRAPA, or an agricultural university?**

A warm introduction could change the trajectory of this project — and the tools available to researchers worldwide.

💖 [Sponsor on GitHub](https://github.com/sponsors/denishdholaria) · 💰 [Open Collective](https://opencollective.com/bijmantra) · 📧 [hello@bijmantra.org](mailto:hello@bijmantra.org) · 🌐 [bijmantra.org](https://bijmantra.org)

</div>

---

## 🌟 Vision

> **"Agricultural truth emerges at the intersection of disciplines. BijMantra makes that intersection computable."**

**Bij** (बीज) = Seed · **Mantra** (मन्त्र) = Sacred Utterance ; The primordial sound (The Big Bang) from which the universes were seeded.

This platform exists because better tools lead to better science, better science leads to better agriculture, and better agriculture feeds the world.

---

<div align="center">

**Hare Krishna** — Creator & Lead Developer

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org) · 🔗 [LinkedIn](https://www.linkedin.com/in/denishdholaria) · 🌐 [bijmantra.org](https://bijmantra.org)

🌾 _Built for every researcher, in every country, working toward food security._

</div>
