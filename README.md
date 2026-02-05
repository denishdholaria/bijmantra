
<div align="center">

<!-- README intentionally prioritizes clarity over brevity.
     Do not compress sections without preserving narrative order.
     FUTURE: Consider splitting into README.md (front door)
     and README_DEEP_DIVE.md when contributor base grows -->

<img src="frontend/public/icons/icon-512x512.png" alt="BijMantra Logo" width="200"/>

# BijMantra

### _Cross-Domain Agricultural Intelligence Platform_

**Unifying fragmented agricultural knowledge through AI-assisted reasoning**

🌐 **[bijmantra.org](https://bijmantra.org)** — Join the waitlist for early access

---
## 🚨 Funding Required  

This project has been sustained so far through personal funding, but continuing development is no longer sustainable without external support.  
To move forward, BijMantra urgently requires funding. Please consider sponsoring or donating to help ensure its future.  

🌐 [Support BijMantra] (https://github.com/sponsors/denishdholaria)  
📧 Contact: hello@bijmantra.org  

</div>

> ### ⚠️ **Development Notice**
>
> **BijMantra is currently undergoing major architectural refactoring.** The platform is being systematically rebuilt to eliminate demo data dependencies and implement production-grade computational backends. During this transition period:
>
> - Features may be temporarily unavailable or exhibit unexpected behavior
> - Breaking changes are frequent and expected
> - API contracts may change without prior notice
> - Database schemas are subject to revision
>
> **This is intentional and necessary work.** We are converting a proof-of-concept into production-ready software. If you encounter issues, please check our [issue tracker](https://github.com/denishdholaria/bijmantra/issues) or reach out at [hello@bijmantra.org](mailto:hello@bijmantra.org).
>
> **For production use:** Please wait for the `1.0.0` stable release. Current version: `preview-1` (Early Access).

---

<div align="center">

### The Road Ahead

This platform represents 18+ months of solo development — but the vision extends far beyond what one person can build. BijMantra aims to transform how agricultural research is conducted globally, connecting fragmented domains into unified intelligence.

**What's built:** 233 pages, 1,485 endpoints, 8 modules, 100% BrAPI v2.1 compliance.

**What remains:** Converting 37 pages from demo data to real database queries, implementing missing algorithms, and domain expert validation.

We're seeking collaborators who understand that meaningful work takes time, and that the best software emerges from the intersection of technical excellence and domain expertise.

---

<a id="reality-check"></a>

### ⚠️ Reality Check: What Actually Works Today

**This section exists to prevent misunderstanding.** If you are evaluating BijMantra for research, funding, or contribution, read this carefully before proceeding.

**CALF Assessment (January 2026) revealed critical issues:**

| CALF Level                | Count  | %   | Status               |
| ------------------------- | ------ | --- | -------------------- |
| Display Only              | 89     | 40% | ✅ Acceptable        |
| Client-Side Calculation   | 67     | 30% | ⚠️ Needs backend   |
| **Demo Data (Violation)** | **37** | **17%** | **🟡 Improving** |
| Real Computation          | 23     | 10% | 🟢 Improving         |
| WASM High-Performance     | 5      | 2%  | ✅ Excellent         |

**Progress:** Now **28 pages (12%)** are fully functional with real computation. 5 demo violations fixed in Session 85.

📄 **[CALF Assessment](docs/CALF.md)** — Complete 221-page audit with evidence

> 📊 **Live Metrics:** See [`metrics.json`](metrics.json) for current statistics

---

### The Path Ahead

<img src="docs/images/the-path.png" alt="The Path Ahead" width="500"/>

_The path is long, but the direction is clear._

---

**A comprehensive PWA for plant breeding, genomics, and agricultural research**

[![License](https://img.shields.io/badge/License-AGPL--3.0%20%2B%20Commercial-green?style=for-the-badge)](LICENSE)
[![BrAPI](https://img.shields.io/badge/BrAPI-v2.1_100%25-blue?style=for-the-badge)](https://brapi.org)
[![PWA](https://img.shields.io/badge/PWA-Offline_Capable-purple?style=for-the-badge)](https://web.dev/progressive-web-apps/)
[![Website](https://img.shields.io/badge/Website-bijmantra.org-2E8B57?style=for-the-badge)](https://bijmantra.org)

[**🌐 Website**](https://bijmantra.org) · [**🚀 Quick Start**](#-quick-start) · [**📊 Status**](#-project-status) · [**🔌 APIs**](#-api-catalog) · [**🤝 Contributing**](#-contributing)

</div>

---

## 🎯 Why BijMantra Exists

> **"Understanding one domain without seeing its interaction with others produces incomplete, sometimes misleading conclusions."**

Agricultural research is fragmented. Breeders optimize genetics in isolation. Agronomists optimize management without genetic context. Soil scientists study soil without crop feedback.

**Real-world agricultural decisions do not happen in silos — but our tools still do.**

BijMantra exists to solve this: **a platform where AI assists reasoning across multiple scientific domains**, not just within them.

| Traditional Tools        | BijMantra                         |
| ------------------------ | --------------------------------- |
| Data aggregation         | **Knowledge synthesis**     |
| Single-domain dashboards | **Cross-domain reasoning**  |
| AI as chatbot            | **AI as domain integrator** |

---

## 🧠 The BijMantra Mental Model (30 Seconds)

```
Breeding Program → Trial Design → Phenotyping → Genomics → Selection Decisions
```

Most tools support **one box**. BijMantra connects the **entire flow** into a single computational system.

---

## 👥 Who BijMantra Is For (and Who It Is Not)

**BijMantra is for:**

- Plant breeders running real programs (public or private)
- Researchers tired of siloed tools and CSV glue
- Institutions that value correctness over dashboards
- Developers interested in scientific computing + PWA systems

**BijMantra is NOT for:**

- Quick demo seekers
- Pure visualization tools
- "AI chatbot for agriculture" expectations
- Production SaaS users (yet)

---

## 🧭 How to Read This README

- **Breeders / Researchers** → Read _Why BijMantra Exists_, _Mental Model_, _Key Features_
- **Developers** → Jump to _What Makes This Technically Unusual_, _Quick Start_, _Architecture_
- **Funders / Institutions** → Read _Reality Check_, _Governance_, _Path to Production_

---

## 🚫 Explicit Non-Goals (Current Phase)

BijMantra does not currently aim to:

- Be a turnkey SaaS product
- Replace statistical software like ASReml or SAS
- Provide black-box AI recommendations
- Optimize for casual or demo-first usage

---

## ⚡ At a Glance

> 📊 **Source of Truth:** [`metrics.json`](metrics.json) — All statistics below are derived from this file
>
> 📌 All numeric claims in this document must originate from `metrics.json`. If a discrepancy exists, `metrics.json` is authoritative.

| 📊 Scale                 | 🎯 Computational Status       |
| ------------------------ | ----------------------------- |
| **233** Pages            | **28** Truly Functional       |
| **1,485** API Endpoints  | **147** Database Tables       |
| **8** Modules            | **103** RLS-Protected Tables  |
| **201/201** BrAPI v2.1   | **100%** Spec Complete ✅     |

_As detailed in the Reality Check above, 37 pages currently return demo data — actively being reduced._

---

## 🧩 What Makes BijMantra Technically Unusual

- **Fortran-based numerical kernels** in a web-first platform (BLUP, REML, kinship matrices)
- **WASM genomics** running inside the browser (not server-side)
- **Row-Level Security** as a first-class architectural primitive (103 tables)
- **Offline-capable data collection** (field data entry works without connectivity)
- **Governance documents treated as executable constraints** (14-document Platform Law Stack)
- **100% BrAPI v2.1 compliance** (201/201 endpoints)

---

## 🏛️ The Eight Modules

| Module                      | Endpoints | Pages | CALF Status     |
| --------------------------- | --------- | ----- | --------------- |
| 🌾 **Breeding**             | 126       | 35    | 🟢 Improving    |
| 📋 **Phenotyping**          | 88        | 28    | 🟡 Partial      |
| 🧬 **Genomics**             | 110       | 35    | 🟢 Improving    |
| 🏛️ **Seed Bank**           | 59        | 15    | ⚪ Display only |
| 🌍 **Environment**          | 97        | 20    | ⚪ Display only |
| 🏭 **Seed Operations**      | 99        | 25    | 🟡 Partial      |
| 📚 **Knowledge**            | 35        | 5     | ⚪ Display only |
| ⚙️ **Settings & Admin**    | 79        | 35    | ✅ Functional   |

---

## ✨ Key Features

| Feature                         | Description                                                | Status              |
| ------------------------------- | ---------------------------------------------------------- | ------------------- |
| 🪷 **Veena AI**                 | Agro-Intelligence that connects domains                    | ✅ Implemented      |
| 🔗 **Cross-Domain**             | Breeding decisions surface soil, climate, economic factors | 🟡 Partial          |
| 🧬 **Genomic Selection**        | WASM-powered GBLUP, QTL mapping in browser                 | ✅ WASM works       |
| 🌍 **PWA with Offline Support** | Installable app, offline data collection for field work    | ✅ Implemented      |
| 🌱 **BrAPI v2.1**               | 201/201 endpoints (100%)                                   | ✅ Complete         |
| 🚪 **Workspace Gateway**        | 5 role-based workspaces                                    | ✅ Implemented      |
| 🔐 **Row-Level Security**       | 103 tables with RLS policies                               | ✅ Complete         |
| ♿ **Accessibility**            | WCAG 2 AA compliant                                        | ✅ 17 tests passing |

---

## 🚀 Quick Start

> **Docker users**: BijMantra uses [Podman](https://podman.io) (rootless, daemonless). Commands are identical — just use `podman` instead of `docker`.

```bash
git clone https://github.com/denishdholaria/bijmantra.git && cd bijmantra
make dev              # Start infrastructure
make dev-backend      # → http://localhost:8000
make dev-frontend     # → http://localhost:5173
```

| Service     | URL                                                    |
| ----------- | ------------------------------------------------------ |
| 🌐 Frontend | [localhost:5173](http://localhost:5173)                   |
| 📡 API Docs | [localhost:8000/docs](http://localhost:8000/docs)         |
| 🔌 BrAPI    | [localhost:8000/brapi/v2](http://localhost:8000/brapi/v2) |

---

## 📊 Project Status

### Current Version

> 📊 **Authoritative source:** [`metrics.json`](metrics.json)
>
> 🔄 This README is versioned alongside `preview-*` releases. Update only when version changes or CALF status materially shifts.

| Field    | Value                                |
| -------- | ------------------------------------ |
| Version  | `preview-1`                        |
| Codename | Prathama (प्रथम) — "The First" |
| Phase    | Preview (Early Access)               |
| Status   | Demo data cleanup in progress        |

### CALF Assessment Summary

_Full details in the [Reality Check](#️-reality-check-what-actually-works-today) section above._

| Level            | Description         | Count        | Issue                                    |
| ---------------- | ------------------- | ------------ | ---------------------------------------- |
| CALF-0           | Display Only        | 89           | None — acceptable                       |
| CALF-1           | Client-Side Calc    | 67           | No backend validation                    |
| **CALF-2** | **Demo Data** | **37** | **Improving — 5 fixed this week** |
| CALF-3           | Real Computation    | 23           | Improving                                |
| CALF-4           | WASM                | 5            | Excellent                                |

📄 **[Full CALF Assessment](docs/CALF.md)** — 623-line audit with code evidence

### Path to Production

| Priority | Task                         | Status         |
| -------- | ---------------------------- | -------------- |
| 1        | Fix 37 demo data pages       | 🔄 In progress |
| 2        | Implement missing algorithms | 🔄 In progress |
| 3        | Move calculations to backend | ❌ Not started |

> Each roadmap item directly corresponds to a CALF deficiency identified in the [Reality Check](#reality-check) section above.

### Version Progression

```
preview-1       ← CURRENT (Early access)
     ↓
preview-2       (Demo data fixed)
     ↓
preview-3       (Domain expert validated)
     ↓
1.0.0-rc        (Release Candidate)
     ↓
1.0.0           (Stable Release)
```

---

## 🌍 Join the Global Team — 2026 Resolution

<div align="center">

**Climate change doesn't respect borders. Neither should our solutions.**

</div>

BijMantra represents 18+ months of solo development. For 2026, we're building a **global team** to take this platform from experimental to production.

### Who We're Looking For

| Role                           | What You'd Do                               | Ideal Background                     |
| ------------------------------ | ------------------------------------------- | ------------------------------------ |
| 🧬 **Plant Breeders**          | Validate workflows, advise on genetics      | PhD/MSc, breeding program experience |
| 🌱 **Agronomists**             | Field trial design, cross-domain validation | Crop science background              |
| 🧪 **Genomics Experts**        | Guide GWAS, QTL, molecular features         | Bioinformatics experience            |
| 💻 **Full-Stack Developers**   | React/TypeScript, Python/FastAPI            | 3+ years experience                  |
| 📝 **Technical Writers**       | Documentation, tutorials                    | Technical writing experience         |
| 💰 **Grant Writers**           | Funding proposals                           | Agricultural/tech grant experience   |

### How to Get Involved

1. **Star this repo** — Show your interest
2. **Join our Discord** — [discord.gg/ubUHhBHjhG](https://discord.gg/ubUHhBHjhG)
3. **Pick a "good first issue"** — Start contributing
4. **Read [CONTRIBUTING.md](CONTRIBUTING.md)** — Understand our philosophy

📧 **Contact:** [hello@bijmantra.org](mailto:hello@bijmantra.org)

---

## 🧪 Testing Status

> 📊 **Source:** [`metrics.json`](metrics.json) → `tests` section

| Test Type         | Count   | Status                  |
| ----------------- | ------- | ----------------------- |
| Unit Tests        | 88      | ✅ Passing              |
| Integration Tests | 18      | ✅ Passing (BrAPI live) |
| E2E Tests         | 229     | ✅ Passing (3 skipped)  |
| Accessibility     | 17      | ✅ Passing              |
| **Total**         | **352** | ✅ All Passing          |

**Note:** Tests verify UI rendering and API responses, but do not validate computational correctness of demo data pages.

---

## 🔌 API Catalog

> 📊 **Source:** [`metrics.json`](metrics.json) → `api` section

**Total: 1,485 endpoints** · BrAPI v2.1: 201 (100%) · Custom: 1,284

| Category          | Endpoints | Prefix         | Status         |
| ----------------- | --------- | -------------- | -------------- |
| BrAPI Core        | 50        | `/brapi/v2/` | ✅ Real data   |
| BrAPI Germplasm   | 39        | `/brapi/v2/` | ✅ Real data   |
| BrAPI Phenotyping | 51        | `/brapi/v2/` | ✅ Real data   |
| BrAPI Genotyping  | 61        | `/brapi/v2/` | ⚠️ Some demo |
| Custom APIs       | 1,274     | `/api/v2/`   | ⚠️ See CALF  |

---

## 📚 Key Documentation

| Document                                                      | Description                                               |
| ------------------------------------------------------------- | --------------------------------------------------------- |
| [README_DEEP_DIVE.md](README_DEEP_DIVE.md)                       | Technical architecture for senior engineers               |
| [CONTRIBUTOR_ENTRY.md](CONTRIBUTOR_ENTRY.md)                     | Role-based entry points for contributors                  |
| [CALF.md](docs/CALF.md)                                          | Computational Analysis and Functionality Level assessment |
| [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)             | System architecture overview                              |
| [PLATFORM_LAW_INDEX.md](docs/architecture/PLATFORM_LAW_INDEX.md) | Complete governance framework                             |
| [API_REFERENCE.md](docs/api/API_REFERENCE.md)                    | API documentation                                         |
| [CONTRIBUTING.md](CONTRIBUTING.md)                               | Contribution guidelines                                   |
| [FUNDING.md](FUNDING.md)                                         | Funding vision and UN SDG alignment                       |

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

**Dual License: AGPL-3.0 + Commercial** — _Open Source First, Commercial When Needed_

**Last Updated:** January 2025

| ✅ Free (AGPL-3.0)              | 💰 Commercial License Required |
| ------------------------------- | ------------------------------ |
| Personal, Educational, Research | For-profit agro-companies > $1M revenue |
| Non-profit, Government agencies | SaaS without source disclosure |
| Small agricultural businesses   | Proprietary derivatives        |
| Open source compliance          | White-labeling/OEM use         |

**🚫 Prohibited for ALL users:** Terminator seeds, GURTs, seed termination technologies

See [LICENSE](LICENSE) for complete terms · [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for commercial terms · [ETHICAL_USE_POLICY.md](ETHICAL_USE_POLICY.md) for ethical restrictions

---

## 🤝 Contributing

**Every contribution must support cross-domain reasoning.**

> ⚠️ Pull requests that introduce mock data, placeholder algorithms, or unverifiable claims will be rejected by design.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the cross-domain contributor guide.

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org) · 🔗 [LinkedIn](https://www.linkedin.com/in/denishdholaria)

---

## 💰 Support This Project

📄 **[FUNDING.md](FUNDING.md)** — Vision, risk mitigation, and funding tiers for institutions

This project aligns with the **[United Nations Sustainable Development Goals](https://sdgs.un.org/goals)** (SDGs) — the global blueprint for peace and prosperity by 2030.

---

## 🌟 Help This Project Reach More People

<div align="center">

**If BijMantra's mission resonates with you, help us reach those who can make it a reality.**

| Action                             | Impact                                               |
| ---------------------------------- | ---------------------------------------------------- |
| ⭐ **Star this repository**        | Signals community interest to potential funders      |
| 🔀 **Fork the project**            | Shows active developer engagement                    |
| 📢 **Share on LinkedIn/X**         | Reaches agricultural networks                        |
| 📧 **Forward to your institution** | Universities and NGOs often seek projects to support |

[![GitHub Stars](https://img.shields.io/github/stars/denishdholaria/bijmantra?style=social)](https://github.com/denishdholaria/bijmantra)
[![GitHub Forks](https://img.shields.io/github/forks/denishdholaria/bijmantra?style=social)](https://github.com/denishdholaria/bijmantra/fork)

**Know someone at CGIAR, Gates Foundation, USAID, or an agricultural university?**

A warm introduction could change the trajectory of this project.

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org) · 🌐 [bijmantra.org](https://bijmantra.org)

</div>

---

## 🌟 Vision

> **"Agricultural truth emerges at the intersection of disciplines. BijMantra makes that intersection computable."**

**Bij** (बीज) = Seed · **Mantra** (मन्त्र) = Sacred Utterance

---

<div align="center">

**Hare Krishna** — Creator & Lead Developer

🌾 _Thank you to all those who believe that better tools can lead to better agriculture._

</div>
