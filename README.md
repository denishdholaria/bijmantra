<div align="center">

# 🌱 BijMantra

### *Cross-Domain Agricultural Intelligence Platform*

**Unifying fragmented agricultural knowledge through AI-assisted reasoning**

🌐 **[bijmantra.org](https://bijmantra.org)** — Join the waitlist for early access

---

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=28&duration=3000&pause=1000&color=2E8B57&center=true&vCenter=true&multiline=true&repeat=true&width=600&height=100&lines=%F0%9F%8E%8A+Happy+New+Year+2026!+%F0%9F%8E%8A;May+your+seeds+grow+strong+%F0%9F%8C%B1" alt="Happy New Year 2026" />

<table>
<tr>
<td align="center">🎆</td>
<td align="center">🌾</td>
<td align="center">✨</td>
<td align="center">🌱</td>
<td align="center">🎇</td>
</tr>
<tr>
<td align="center" colspan="5">

**Wishing all farmers, breeders, and agricultural scientists a prosperous 2026!**

*May this year bring bountiful harvests, breakthrough discoveries, and climate-resilient crops.*

</td>
</tr>
</table>

---

### 🎉 v1.0.0-beta.1 Prathama (प्रथम) Released! 🎉

**December 30, 2025** — First public beta release is now available!

This release is **feature-complete** and enters a **beta testing phase**.

| Status          | Policy       |
| --------------- | ------------ |
| ✅ Features     | Complete     |
| 🟡 Stability    | Beta Testing |
| 🚫 New Features | Frozen       |
| ✅ Bug Fixes    | Accepted     |
| ✅ Security     | All Issues Fixed |
| ✅ RLS Coverage | 100% (90 tables) |

📄 **[Release Notes](RELEASE_v1.0.0.md)** — Full changelog and QA checklist

🌾 201 BrAPI endpoints · 221 pages · 8 modules · 100% open source 🌾

---

</div>

<div align="center">

**A comprehensive PWA for plant breeding, genomics, and agricultural research**

[![License](https://img.shields.io/badge/License-BSAL_v2.0-green?style=for-the-badge)](LICENSE)
[![BrAPI](https://img.shields.io/badge/BrAPI-v2.1_100%25-blue?style=for-the-badge)](https://brapi.org)
[![PWA](https://img.shields.io/badge/PWA-Offline_First-purple?style=for-the-badge)](https://web.dev/progressive-web-apps/)
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

## ⚡ At a Glance

| 📊 Scale                      | 🎯 Progress                     |
| ----------------------------- | ------------------------------- |
| **221** Pages           | **0%** User-Validated     |
| **1,370** API Endpoints | **213** API-Connected     |
| **8** Modules           | **120** Database Tables   |
| **201/201** BrAPI v2.1  | **100%** Spec Complete ✅ |
| **26** Migrations       | **100%** RLS Coverage ✅  |

---

## 🏛️ The Eight Modules

| Module                         | Endpoints | Pages | Focus                                      |
| ------------------------------ | --------- | ----- | ------------------------------------------ |
| 🌾**Breeding**           | 120       | 35    | Programs · Trials · Crosses · Selection |
| 📋**Phenotyping**        | 85        | 25    | Observations · Traits · Field Book       |
| 🧬**Genomics**           | 107       | 35    | Genotyping · GWAS · QTL · Molecular     |
| 🏛️**Seed Bank**        | 59        | 15    | Conservation · Accessions · Viability    |
| 🌍**Environment**        | 97        | 20    | Weather · Soil · Solar · Sensors        |
| 🏭**Seed Operations**    | 96        | 22    | Quality · Processing · Inventory · DUS  |
| 📚**Knowledge**          | 35        | 5     | Forums · Training Hub                     |
| ⚙️**Settings & Admin** | 79        | 35    | Profile · Teams · Security · System     |
| **Total**                | **1,370** (incl. BrAPI) | **221** | **8 Modules** |

---

## ✨ Key Features

| Feature                       | Description                                                |
| ----------------------------- | ---------------------------------------------------------- |
| 🪷**Veena AI**          | Agro-Intelligence that connects domains                    |
| 🔗**Cross-Domain**      | Breeding decisions surface soil, climate, economic factors |
| 🧬**Genomic Selection** | WASM-powered GBLUP, QTL mapping in browser                 |
| 🌍**Offline-First PWA** | Installable, offline data collection                       |
| 🌱**BrAPI v2.1**        | 201/201 endpoints (100%)                                   |
| 🚪**Workspace Gateway** | 5 role-based workspaces                                    |
| 🔐**Row-Level Security**| 100% RLS coverage (90 tables)                              |
| ♿**Accessibility**     | WCAG 2 AA compliant (17/17 tests passing)                  |

---

## 🚀 Quick Start

> **Docker users**: BijMantra uses [Podman](https://podman.io) (rootless, daemonless). Commands are identical — just use `podman` instead of `docker`. See [Architecture](docs/architecture/ARCHITECTURE.md#container-runtime-podman) for details.

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

### v1.0.0-beta.1 — Beta Testing Phase

**BijMantra v1.0.0-beta.1 Prathama** is feature-complete and in beta testing.

| Version Progression | Status            |
| ------------------- | ----------------- |
| `1.0.0-beta.1`    | ← Current        |
| `1.0.0-beta.2`    | Bug fixes         |
| `1.0.0-rc.1`      | Release Candidate |
| `1.0.0`           | Stable Release    |

| What's Accepted     | What's Frozen    |
| ------------------- | ---------------- |
| ✅ Bug fixes        | ❌ New features  |
| ✅ Security patches | ❌ New pages     |
| ✅ Documentation    | ❌ New endpoints |
| ✅ Test coverage    | ❌ UI redesigns  |

### 🌍 Join the Global Team — 2026 Resolution

<div align="center">

**Climate change doesn't respect borders. Neither should our solutions.**

</div>

BijMantra v1.0.0 represents 18+ months of solo development. For 2026, we're building a **global team** to take this platform from beta to production — and we need people like you.

#### Who We're Looking For

| Role                              | What You'd Do                               | Ideal Background                     |
| --------------------------------- | ------------------------------------------- | ------------------------------------ |
| 🧬**Plant Breeders**        | Validate workflows, advise on genetics      | PhD/MSc, breeding program experience |
| 🌱**Agronomists**           | Field trial design, cross-domain validation | Crop science background              |
| 🧪**Genomics Experts**      | Guide GWAS, QTL, molecular features         | Bioinformatics experience            |
| 🌍**Climate Scientists**    | Climate risk modeling, adaptation           | Agro-meteorology background          |
| 💻**Full-Stack Developers** | React/TypeScript, Python/FastAPI            | 3+ years experience                  |
| 🤖**AI/ML Engineers**       | LLM integration, domain agents              | NLP/RAG experience                   |
| 📝**Technical Writers**     | Documentation, tutorials                    | Technical writing experience         |
| 🌐**Translators**           | Spanish, French, Hindi, Swahili, Arabic     | Native speakers                      |
| 💰**Grant Writers**         | Funding proposals                           | Agricultural/tech grant experience   |

#### Why Join?

| What You Get            | Details                                                       |
| ----------------------- | ------------------------------------------------------------- |
| 🌾**Real Impact** | Your code helps breeders develop climate-resilient crops      |
| 🎓**Learning**    | Cross-domain agricultural AI, modern tech stack               |
| 🤝**Community**   | Global network of scientists and developers                   |
| 📜**Recognition** | Co-authorship, conference sponsorship, recommendation letters |
| 🏆**Portfolio**   | Meaningful open source contribution                           |

#### How to Get Involved

1. **Star this repo** — Show your interest
2. **Join our Discord** — [discord.gg/ubUHhBHjhG](https://discord.gg/ubUHhBHjhG) — Introduce yourself
3. **Pick a "good first issue"** — Start contributing
4. **Read [CONTRIBUTING.md](CONTRIBUTING.md)** — Understand our philosophy

📧 **Direct Contact:** [DenishDholaria@gmail.com](mailto:DenishDholaria@gmail.com)

📄 **Full Plan:** [docs/funding/GLOBAL_TEAM_2026.md](docs/funding/GLOBAL_TEAM_2026.md) — Our complete team-building strategy (public)

> *"No single person can solve climate change. No single country can feed the world. No single discipline holds all the answers. But together, we can build the tools that help humanity adapt."*

**Interested?** See [FUNDING.md](FUNDING.md) for institutional partnerships or reach out directly.

### Production Readiness

**213 API-Connected** · **8 UI-Only** · **0 User-Validated**

**Important Distinction:**
- "API-Connected" = Page has backend endpoints, not hardcoded data
- "User-Validated" = Tested by real users in real workflows — **none yet**

**Zero Mock Data Policy:** All pages use real API endpoints. Demo data sandboxed in "Demo Organization."

> ⚠️ **Honest Status:** No page has been comprehensively tested by end users. The developer has not had time for systematic manual testing. Automated E2E tests pass, but real-world validation is pending.

### 📋 Documentation Accuracy Notice

> **Transparency Statement for a Solo-Developed Project**

BijMantra is developed by a single developer managing 1,370 API endpoints, 221 pages, and 8 modules. While every effort is made to keep documentation accurate, discrepancies may exist between documented status and actual implementation.

| What This Means                                                        | Our Commitment                                                                     |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Some pages marked "Functional" may have incomplete backend connections | We correct errors when found                                                       |
| Endpoint counts are best-effort estimates                              | We welcome verification reports                                                    |
| Status claims are based on code inspection at time of audit            | We follow  [GOVERNANCE.md](.kiro/steering/GOVERNANCE.md) for evidence-based reviews |

**If you find a discrepancy:**

1. Open an issue with the file path and observed behavior
2. Reference the documented claim vs. actual behavior
3. We'll investigate and correct within 48 hours

This notice exists because **honesty builds trust**. We'd rather acknowledge limitations than have users discover them unexpectedly.

*Last audit: January 6, 2026 — All 213 functional pages verified. Zero Mock Data Policy enforced (Session 62).*

### 🧪 Testing Status

> **Honest Assessment of Validation State**

| Testing Type                       | Status      | Notes                                                   |
| ---------------------------------- | ----------- | ------------------------------------------------------- |
| **Automated E2E Tests**      | ✅ 315 total (229 E2E + 69 backend + 17 a11y)  | Playwright + pytest, 3 E2E skipped |
| **Developer Manual Testing** | ❌ Not Done | Creator has not had time for systematic testing         |
| **User Acceptance Testing**  | ❌ Not Done | No real users have tested any workflows                 |
| **Domain Expert Validation** | ❌ Not Done | Researchers/scientists have not validated workflows     |
| **Field Testing**            | ❌ Not Done | No real breeding program has used this in production    |

**What this means:**

- The code compiles and automated tests pass
- Individual features work in isolation
- **Real-world scientific workflows have not been validated by domain experts**
- Edge cases, data integrity, and cross-domain logic need expert review

**Why "beta":** The software is feature-complete, but the ultimate examiners — plant breeders, geneticists, and agricultural researchers — have not yet validated that it meets their real-world needs.

**This is why we're seeking collaborators.** See [Seeking Collaborators](#seeking-collaborators) above.

---

## 🔌 API Catalog

**Total: 1,370 endpoints** · BrAPI v2.1: 201 (100%) · Custom: 1,169

| Category          | Endpoints | Prefix         |
| ----------------- | --------- | -------------- |
| BrAPI Core        | 50        | `/brapi/v2/` |
| BrAPI Germplasm   | 39        | `/brapi/v2/` |
| BrAPI Phenotyping | 51        | `/brapi/v2/` |
| BrAPI Genotyping  | 61        | `/brapi/v2/` |
| Custom APIs       | 1,169     | `/api/v2/`   |

---

## 📜 License

**BijMantra Source Available License (BSAL) v2.0** — *Free to Use, Pay to Sell*

| ✅ Free                         | 💰 Commercial    |
| ------------------------------- | ---------------- |
| Personal, Educational, Research | Selling software |
| Non-profit, Self-hosted         | Paid SaaS        |

---

## 🤝 Contributing

**Every contribution must support cross-domain reasoning.**

See [CONTRIBUTING.md](CONTRIBUTING.md) for the cross-domain contributor guide.

📧 [DenishDholaria@gmail.com](mailto:DenishDholaria@gmail.com) · 🔗 [LinkedIn](https://www.linkedin.com/in/denishdholaria)

[![Sponsor](https://img.shields.io/badge/💰_Sponsor-GitHub_Sponsors-ea4aaa?style=for-the-badge)](https://github.com/sponsors/denishdholaria)

---

## 💰 Support This Project

📄 **[FUNDING.md](FUNDING.md)** — Vision, risk mitigation, and funding tiers for institutions

---

## 🌟 Vision

> **"Agricultural truth emerges at the intersection of disciplines. BijMantra makes that intersection computable."**

**Bij** (बीज) = Seed · **Mantra** (मन्त्र) = Sacred Utterance

---

<div align="center">

**Denish Dholaria** — Creator & Lead Developer

🌾 *Thank you to all those who work in acres, not in hours.*

Last updated: January 6, 2026 · Website: [bijmantra.org](https://bijmantra.org)

</div>
