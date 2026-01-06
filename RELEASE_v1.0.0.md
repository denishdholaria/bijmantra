# BijMantra v1.0.0-beta.1 — Prathama (प्रथम)

**Release Date:** December 30, 2025
**Codename:** Prathama (प्रथम) — "The First"
**Version Type:** Beta (Feature-Complete, Testing Phase)

---

## 🎉 First Public Beta Release

BijMantra v1.0.0-beta.1 marks the completion of the initial development phase. This release is **feature-complete** and enters a **beta testing phase**.

### What "Beta" Means

| Aspect              | Status                                                  |
| ------------------- | ------------------------------------------------------- |
| **Features**  | ✅ Complete — All planned v1.0 features implemented    |
| **Stability** | 🟡 Testing — Not yet validated in production           |
| **API**       | 🟡 Stable Intent — Minor changes possible before 1.0.0 |
| **Bugs**      | 🟡 Expected — Please report issues                     |

### Version Progression

```
1.0.0-beta.1  ← YOU ARE HERE (Feature-complete, testing)
     ↓
1.0.0-beta.2  (Bug fixes from beta testing)
     ↓
1.0.0-rc.1    (Release Candidate, final validation)
     ↓
1.0.0         (Stable Release, production-ready)
```

### Release Policy

| Aspect                  | Policy                                         |
| ----------------------- | ---------------------------------------------- |
| **New Features**  | ❌ Frozen — No new features in public repo    |
| **Bug Fixes**     | ✅ Accepted — Critical and high-priority bugs |
| **Documentation** | ✅ Accepted — Improvements and corrections    |
| **Tests**         | ✅ Priority — Comprehensive test coverage     |
| **Security**      | ✅ Priority — Vulnerability patches           |

---

## 📊 Release Statistics

| Metric              | Value                    |
| ------------------- | ------------------------ |
| Frontend Pages      | 221 (213 functional)     |
| API Endpoints       | 1,370                    |
| BrAPI v2.1 Coverage | 100% (201/201 endpoints) |
| Database Models     | 110                      |
| Database Tables     | 120                      |
| Migrations          | 26                       |
| Modules             | 8                        |
| Workspaces          | 5 + Custom               |
| Build Size          | ~8.0MB PWA               |
| Total Tests         | 315 (51 unit + 18 integration + 229 E2E + 17 a11y) |
| RLS Coverage        | 100% (90 tables)         |

---

## ✅ Completed Features

### Core Platform

- [X] BrAPI v2.1 100% compliance (Core, Germplasm, Phenotyping, Genotyping)
- [X] Multi-tenant architecture with Row-Level Security
- [X] Admin/Demo user separation
- [X] JWT authentication with refresh tokens
- [X] PWA with offline support

### Workspace System

- [X] Gateway-based workspace selection
- [X] 5 predefined workspaces (Plant Breeding, Seed Business, Innovation Lab, Gene Bank, Administration)
- [X] Custom workspace creation
- [X] Workspace-filtered navigation

### Design System

- [X] Prakruti Design System (color palette)
- [X] Dark mode support
- [X] Responsive mobile navigation
- [X] Accessibility (WCAG 2.1 AA)

### AI Integration

- [X] Veena AI Assistant (multi-provider: Ollama, Groq, Google, OpenAI, Anthropic)
- [X] DevGuru PhD Mentor (5 phases complete)
- [X] SATYA anti-sycophancy protocol
- [X] RAG with vector search

### Breeding Tools

- [X] Trial design (RCBD, Alpha-Lattice, Augmented, Split-Plot)
- [X] Selection index calculators
- [X] Genomic selection (GBLUP)
- [X] Cross prediction
- [X] Pedigree analysis
- [X] G×E analysis (AMMI, GGE Biplot)

### Data Management

- [X] Zero in-memory mock data (all database-backed)
- [X] 15 seeders for demo data
- [X] Redis for ephemeral data (jobs, cache)
- [X] Data export (CSV, JSON, Excel)

---

## 🧪 Beta Testing

**Testing Guide:** [docs/BETA_TESTING_v1.0.0.md](docs/BETA_TESTING_v1.0.0.md)

The beta testing guide includes:
- 50 test cases across 10 categories
- API test scripts
- Bug report template
- Sign-off checklist

### Testing Categories

| Category | Tests | Priority |
|----------|-------|----------|
| Authentication | 5 | 🔴 Critical |
| Navigation | 6 | 🔴 Critical |
| BrAPI Core | 7 | 🔴 Critical |
| Germplasm | 5 | 🟡 High |
| Phenotyping | 5 | 🟡 High |
| Genotyping | 5 | 🟡 High |
| Seed Bank | 5 | 🟡 High |
| Environment | 4 | 🟢 Medium |
| AI Features | 4 | 🟢 Medium |
| Offline/PWA | 4 | 🟢 Medium |

---

## 🔮 Future Development & Sustainability

BijMantra v1.0.0 represents 18+ months of solo development. Continued development requires collaboration and resources.

### What's Needed

| Need | Description |
|------|-------------|
| 🧬 **Domain Experts** | Plant breeders, geneticists, agronomists to validate cross-domain logic |
| 📝 **Grant Writers** | Help prepare proposals for CGIAR, USAID, Gates Foundation, etc. |
| 🧪 **Beta Testers** | Institutions willing to field-test with real breeding programs |
| 🤝 **Institutional Partners** | Research centers, universities, seed companies |

### Planned Features (With Support)

- Multi-organization support
- Advanced analytics dashboards
- Custom report builder
- On-premise deployment options
- SSO/SAML integration
- Audit compliance (21 CFR Part 11)

### Open Source Commitment

This public release will continue to receive:

- Security patches
- Critical bug fixes
- Community contributions

**Interested in collaborating?** See [FUNDING.md](FUNDING.md) or contact [DenishDholaria@gmail.com](mailto:DenishDholaria@gmail.com)

---

## 🧪 Testing Checklist (v1.0.0 QA)

### Authentication

- [ ] Login with valid credentials
- [ ] Login with invalid credentials (error handling)
- [ ] Token refresh
- [ ] Logout
- [ ] Demo user access

### Navigation

- [ ] Gateway workspace selection
- [ ] Workspace switching
- [ ] Sidebar filtering by workspace
- [ ] Mobile bottom navigation
- [ ] Breadcrumbs

### BrAPI Core

- [ ] Programs CRUD
- [ ] Trials CRUD
- [ ] Studies CRUD
- [ ] Locations CRUD
- [ ] Seasons CRUD
- [ ] People CRUD
- [ ] Lists CRUD

### Germplasm

- [ ] Germplasm search
- [ ] Germplasm detail view
- [ ] Pedigree display
- [ ] Crosses management
- [ ] Seed lots inventory

### Phenotyping

- [ ] Traits/Variables management
- [ ] Observations recording
- [ ] Observation units
- [ ] Images upload
- [ ] Samples management

### Genotyping

- [ ] Variants display
- [ ] Call sets
- [ ] References
- [ ] Marker positions
- [ ] Allele matrix

### AI Features

- [ ] Veena chat (with Ollama running)
- [ ] DevGuru project creation
- [ ] Voice input (if enabled)

### Offline/PWA

- [ ] App installable
- [ ] Offline indicator
- [ ] Data sync status

---

## 📝 Known Limitations

1. **Weather API** — Requires external API key configuration
2. **AI Features** — Require LLM provider setup (Ollama recommended for local)
3. **Computer Vision** — Models not trained (placeholder UI)
4. **Real-time Collaboration** — Socket.IO mounted but limited testing

---

## 🙏 Acknowledgments

- **Solar Agrotech Private Limited** — Sponsor and resource provider
- **Dr. T. L. Dholaria** — Foundational knowledge in plant breeding
- **Open Source Community** — Tools and libraries that made this possible

---

## 📜 License

BijMantra v1.0.0 is released under dual license:

- **AGPL-3.0** — For open source use
- **Commercial License** — Available for enterprise use

See `LICENSE`, `AGPL-3.0.txt`, and `COMMERCIAL_LICENSE.md` for details.

---

> *"The seed contains the entire tree. The code contains the entire future."*
> — Denish Dholaria

---

**योगः कर्मसु कौशलम्** — Excellence in Action
