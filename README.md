<div align="center">

<img src="frontend/public/icons/icon-512x512.png" alt="BijMantra Logo" width="180"/>

# BijMantra

## (Under Development)

**Cross-domain agricultural intelligence computational platform.**

🌐 **[bijmantra.org](https://bijmantra.org)**

---

[![PWA](https://img.shields.io/badge/PWA-Offline_Capable-purple?style=for-the-badge)](https://web.dev/progressive-web-apps/)
[![Stars](https://img.shields.io/github/stars/denishdholaria/bijmantraorg?style=for-the-badge&logo=github&color=gold)](https://gitlab.com/denishdholaria/bijmantraorg)

[**🚀 Get Started**](#-quick-start) · [**🧬 Architecture**](#-architecture) · [**🤝 Contribute**](#-contributing) · [**💰 Fund This Work**](#-invest-in-food-security)

</div>

⸻

# Architectural Evolution

BijMantra is not a typical CRUD web application. It is a system that combines:
	•	plant breeding science
	•	high-performance numerical computing
	•	AI-assisted research workflows
	•	offline-first field data collection
	•	large-scale biological datasets

Because of this scope, the platform has undergone multiple architectural refactoring phases during development.

These refactors were driven by real engineering constraints encountered while building the system:
	•	Early components began forming “god files” and “god objects” as scientific features accumulated.
	•	The domain complexity of breeding analytics required stronger module boundaries.
	•	Integration of AI capabilities beyond a simple chat interface required deeper architectural changes.
	•	The platform needed to support hybrid compute engines (Python, Rust/WASM, and Fortran) in a stable way.
	•	Scaling toward a modular, AI-native research platform required rethinking several early design decisions.

Rather than patching over these issues, the architecture has been intentionally redesigned multiple times to maintain long-term integrity.

This approach follows a common pattern in complex software systems:
early versions prioritize capability, later versions prioritize structure, modularity, and longevity.

The current architecture reflects the latest direction toward:
	•	modular domain-driven design
	•	hybrid scientific compute infrastructure
	•	AI-native data workflows
	•	offline-first PWA capabilities
	•	long-term platform stability

Additional architectural refinements are expected as the platform continues to grow.

⸻

Engineering Philosophy

The project prioritizes:
	•	Correctness over convenience
	•	Architecture over short-term hacks
	•	Scientific reproducibility
	•	Long-term maintainability

Refactoring is treated as a necessary part of building a durable research platform, not as a failure of the development process.
---

<details>
<summary><b>The Architect's Ethos</b></summary>
<br />

> **"Speak in Intent. Architect the Reality."**
> 
> *Say Less. Build More. Deliver Greatness.*

BijMantra is not a massive corporate endeavor; it is built by a solo developer orchestrating specialized AI agents. In this paradigm, English is the primary programming language, and intent is the compiler. There are no theoretical debates here—only relentless execution. I orchestrate the architecture in silence, and let the scale of the impact speak for itself.

</details>

---

> [!NOTE]
> **A Note on Documentation Accuracy**
> BijMantra is designed, architected, and maintained entirely by a single developer. While every effort is made to keep this documentation, codebase references, and all associated materials as accurate and current as possible, the sheer breadth of this platform — spanning genomics, agronomy, AI reasoning, full-stack engineering, and interoperability standards — means that occasional inconsistencies or outdated references are inevitable. Your patience and understanding are sincerely appreciated. If you encounter a discrepancy, please feel free to [open an issue](https://gitlab.com/denishdholaria/bijmantraorg/issues) — contributions of any size are always welcome.

## The Problem

> **Agricultural research is structurally fragmented. Our tools perpetuate the problem.**

A breeder selecting drought-tolerant lines has no visibility into soil microbiome data. An agronomist prescribing inputs has no genetic context. Climate models don't reach farm-level adaptation. These decisions are deeply interconnected — but our software treats them as isolated silos.

**The result:** suboptimal breeding decisions, repeated field failures, and billions lost to preventable yield gaps — disproportionately impacting food-insecure regions.

## The Solution

**BijMantra** is the first open-source platform that makes cross-domain agricultural reasoning computable. Instead of aggregating data into dashboards, it synthesizes knowledge across genetics, agronomy, soil science, climate, and economics — assisted by REEVU, our evidence-driven AI reasoning engine.

```
Breeding Program → Trial Design → Phenotyping → Genomics → Selection Decisions
       ↕               ↕              ↕             ↕              ↕
    Soil Data     Climate Risk    Economics    Pest Pressure   Market Demand
```

Most tools support **one box** above. BijMantra connects them all.

---

## 🚀 Quick Start

> **Docker users:** BijMantra uses [Podman](https://podman.io) (rootless, daemonless). Commands are interchangeable.

```bash
git clone https://gitlab.com/denishdholaria/bijmantraorg.git && cd bijmantraorg
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
| **Frontend** | React 19 · TypeScript 5 · Vite · PWA (221 pages)               |
| **Backend**  | Python 3 · FastAPI · SQLAlchemy · NumPy · SciPy               |
| **Genomics** | Rust → WebAssembly (G-Matrix, LD, Population Stats)              |
| **Database** | PostgreSQL 17 · PostGIS · pgvector · Row-Level Security        |
| **AI**       | Multi-provider LLM (Ollama/Groq/Google AI/OpenAI) · RAG · REEVU |
| **Interop**  | BrAPI v2.1 (201/201 endpoints) · 1344 API endpoints              |

</details>

---

## 🤝 Contributing

BijMantra is built by a solo developer and needs your help. **You don't need to be an agriculture expert to contribute.**

<details>
<summary><b>How to Contribute (Developers & Scientists)</b></summary>
<br />

### Quick Wins (< 30 minutes)

| Action                    | Impact                                                                                               |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| ⭐**Star the repo** | Signals community interest to funders                                                                |
| 🐛**Report a bug**  | [Open an issue](https://gitlab.com/denishdholaria/bijmantraorg/issues) — even "this confused me" helps |
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
git clone https://github.com/YOUR_USERNAME/bijmantraorg.git && cd bijmantraorg
make dev && make dev-backend && make dev-frontend
```

📄 [CONTRIBUTING.md](CONTRIBUTING.md) · [CONTRIBUTOR_ENTRY.md](CONTRIBUTOR_ENTRY.md)

### For Domain Scientists

BijMantra's algorithms need validation from people who understand the science. If you work in **plant breeding, genomics, agronomy, soil science, or agricultural economics** — your review of any module is worth more than a thousand lines of code.

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org)

</details>

---

## 💰 Invest in Food Security

<div align="center">

### Why This Matters

</div>

**Climate change is accelerating.** By 2050, global food production must increase 60% to feed 9.7 billion people — while arable land decreases, water scarcity intensifies, and extreme weather events multiply. The tools researchers use today were designed for a stable climate. They weren't built for this.

**BijMantra is infrastructure for the next generation of agricultural science** — open, interoperable, and accessible to every researcher on the planet, not just those at well-funded institutions.

### The Opportunity

| What exists today                | What BijMantra enables                       |
| -------------------------------- | -------------------------------------------- |
| Data aggregation dashboards      | **Knowledge synthesis** across domains |
| Single-domain analytics tools    | **Cross-domain AI reasoning**          |
| Proprietary, expensive platforms | **Open-source, globally accessible**   |
| Server-dependent systems         | **Offline-capable PWA** for field use  |
| Fragmented data standards        | **100% BrAPI v2.1** interoperability   |

<details>
<summary><b>View Funding Tables & Partnership Mechanics</b></summary>
<br />

### What Funding Enables

| Tier                       | Amount    | Impact                                                             |
| -------------------------- | --------- | ------------------------------------------------------------------ |
| 🌱**Infrastructure** | $200/mo   | PostgreSQL, Redis, hosting, SSL, CI/CD                             |
| 🌿**Accelerator**    | $2,000/mo | Full-time development, faster feature delivery                     |
| 🌳**Institutional**  | $10,000+  | Dedicated domain modules, pilot deployments, research partnerships |

### How to Fund

| Channel                            | Link                                                                          |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| 💖**GitHub Sponsors**        | [github.com/sponsors/denishdholaria](https://github.com/sponsors/denishdholaria) |
| 💰**Open Collective**        | [opencollective.com/bijmantra](https://opencollective.com/bijmantra)             |
| 📧**Institutional / Direct** | [hello@bijmantra.org](mailto:hello@bijmantra.org)                                |

> Every contribution is publicly tracked via Open Collective. Full financial transparency.

### Institutional Partners Welcome

We actively seek partnerships with organizations that understand agricultural research infrastructure as a **global public good**:

- **CGIAR Centers** — IRRI, CIMMYT, ICRISAT, ICARDA
- **Foundations** — Gates Foundation, Rockefeller Foundation, McKnight Foundation
- **Government** — USAID, DFID, GIZ, ICAR, EMBRAPA
- **Universities** — Any institution running plant breeding programs
- **Industry** — Seed companies and AgTech firms who benefit from open standards

### 💖 Development Sponsors

Are you a large institution or enterprise? Consider supporting the long-term sustainability of BijMantra through our [Development Sponsorship Program](SPONSORS.md). Sponsors receive exclusive benefits including perpetual free licenses (Institutional or Commercial, based on tier and org type) and prominent brand placement.

<div align="center">

*Be the first to feature your logo here by becoming a Founding Sponsor!*

</div>

</details>

📄 [FUNDING.md](FUNDING.md) — Detailed tiers, use of funds, and UN SDG alignment
📄 [SPONSORS.md](SPONSORS.md) — View our Development Sponsors and learn how to get your logo here

---

**🚫 Prohibited:** Terminator seeds, GURTs, and seed dependency technologies.

📄 [LICENSE](LICENSE) · [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) · [ETHICAL_USE_POLICY.md](ETHICAL_USE_POLICY.md)

---

## 🌟 The Vision

> **"Agricultural truth emerges at the intersection of disciplines. BijMantra makes that intersection computable."**

**Bij** (बीज) = Seed · **Mantra** (मन्त्र) = Sacred Utterance — the primordial sound from which the universes were seeded.

This platform exists because better tools lead to better science, better science leads to better agriculture, and better agriculture feeds the world.

---

<div align="center">

### Take Action

[![Star](https://img.shields.io/badge/⭐_Star_This_Repo-2_seconds-gold?style=for-the-badge)](https://gitlab.com/denishdholaria/bijmantraorg)
[![Sponsor](https://img.shields.io/badge/💖_Sponsor-Any_Amount-EA4AAA?style=for-the-badge)](https://github.com/sponsors/denishdholaria)
[![Issues](https://img.shields.io/badge/🐛_Report_Bug-5_minutes-blue?style=for-the-badge)](https://gitlab.com/denishdholaria/bijmantraorg/issues)

---

**Built for every researcher, in every country, working toward food security.**

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org) · 🔗 [LinkedIn](https://www.linkedin.com/in/denishdholaria) · 🌐 [bijmantra.org](https://bijmantra.org)

**Hare Krishna** — Creator & Lead Developer

</div>
