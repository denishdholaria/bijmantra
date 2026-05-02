# 🌱 Bijmantra Frontend

**Version:** Preview

React Progressive Web Application for plant breeding data management with AI-powered phenotyping.

## 📊 Current Stats

| Metric | Count |
|--------|-------|
| **Total Pages** | 252 |
| **Functional** | 236 |
| **Experimental** | 2 |
| **Modules** | 8 |
| **API Endpoints** | See `/metrics.json` (1,935 current total) |

> **Note:** 2 pages (ApexAnalytics, InsightsDashboard) are classified as Experimental - APIs exist but return demo data, not connected to real database.

## 🚀 Quick Start

```bash
# Install dependencies
bun install

# Start development server
bun run dev

# Build for production
bun run build
```

The frontend now treats Bun as the canonical package manager for local development:

```bash
bun install
bun run dev
bun run build
bun run test:run
bun run e2e:install
BIJMANTRA_FRONTEND_DEV_COMMAND="bun run dev" bun run e2e
```

Frontend TypeScript should now be treated as TS7-targeted for active development. CLI typechecking runs through the native preview compiler:

```bash
bun run typecheck
bun run build:typecheck
```

Author new frontend TypeScript code to satisfy the TS7 `tsgo` path first. If you need the classic compiler for comparison or tool debugging, use `bun run typecheck:tsc`. The repo still keeps the classic `typescript` package installed because some tooling still depends on the legacy compiler API.

If you want VS Code diagnostics to match the CLI path, install the `TypeScriptTeam.native-preview` extension and switch the workspace to that TypeScript service.

## ⚠️ Bun Compatibility Boundary

From a tech-stack perspective, Bun is now the **default frontend package manager**, but Node-oriented deployment and documentation surfaces still exist elsewhere in the repository.

| Area | Current status | What may break or crack |
|------|----------------|-------------------------|
| Frontend local dev/build/test | ✅ Bun-first | Use `bun install` and `bun run ...` from `frontend/` |
| Playwright E2E | ✅ Bun-first | Use `bun run e2e:install` and `BIJMANTRA_FRONTEND_DEV_COMMAND="bun run dev" bun run e2e` |
| Makefile frontend commands | ✅ Bun-first | `make install`, `make dev-frontend`, and frontend quality targets now default to Bun |
| Bootstrap/setup scripts | ⚠️ Mixed | `setup.sh`, `start-bijmantra-app.sh`, and `scripts/start-tunnel.sh` are Bun-first, but other platform bootstrap surfaces may still reference npm |
| Deployment and containers | ⚠️ Mixed | The main frontend Docker path and compose dev command are Bun-first, but other deploy surfaces outside the frontend lane may still assume npm/Node |
| Dependency reproducibility | ⚠️ Transitioning | Bun lockfiles should be the source of truth after install; remove stale npm lockfiles if they still exist in a working tree |

### Practical guidance

- Treat Bun as the **frontend source-of-truth package manager** on this branch.
- Keep **Node installed** for non-frontend tooling and any remaining repo surfaces that still invoke Node directly.
- If a non-frontend setup, deploy, or CI path fails, inspect that specific surface before assuming the frontend Bun migration is at fault.
- Prefer Bun lockfiles over npm lockfiles when reviewing dependency changes on this branch.

## 📁 Project Structure

```
src/
├── components/        # React components
│   ├── ui/           # shadcn/ui components
│   └── Layout.tsx    # Main layout with sidebar
├── lib/              # Utilities & Services
│   ├── api-client.ts # BrAPI client
│   ├── chrome-ai.ts  # Chrome AI integration
│   ├── plant-vision.ts # Computer vision engine
│   └── db.ts         # IndexedDB (Dexie.js)
├── pages/            # 141 page components
│   ├── Dashboard.tsx
│   ├── PlantVision.tsx
│   ├── FieldScanner.tsx
│   └── ...
├── store/            # Zustand state management
├── App.tsx           # Router configuration
└── main.tsx          # Entry point
```

## 🤖 AI Features

### Plant Vision AI
- **Disease Detection** - Identify plant diseases from images
- **Growth Stage** - BBCH scale classification
- **Stress Detection** - Drought, nutrient, heat stress
- **Trait Measurement** - LAI, chlorophyll, canopy coverage
- **Plant Counting** - Stand establishment analysis

### AI Tools
| Tool | Path | Description |
|------|------|-------------|
| AI Assistant | `/ai-assistant` | Multi-provider chat (OpenAI, Anthropic, Google) |
| Plant Vision | `/plant-vision` | Image-based plant analysis |
| Field Scanner | `/field-scanner` | Real-time field scanning |
| Disease Atlas | `/disease-atlas` | Disease reference guide |
| Crop Health | `/crop-health` | Health monitoring dashboard |
| Yield Predictor | `/yield-predictor` | AI yield prediction |
| Chrome AI | `/chrome-ai` | Local Gemini Nano |
| AI Settings | `/ai-settings` | Configure AI providers |

## 🧬 Genomic Analysis Tools

| Tool | Path | Description |
|------|------|-------------|
| Genetic Diversity | `/genetic-diversity` | Population diversity metrics |
| Breeding Values | `/breeding-values` | BLUP/GBLUP estimation |
| QTL Mapping | `/qtl-mapping` | Linkage mapping & GWAS |
| Genomic Selection | `/genomic-selection` | GS model training |
| MAS | `/marker-assisted-selection` | Foreground/background selection |
| Haplotypes | `/haplotype-analysis` | Haplotype block analysis |
| LD Analysis | `/linkage-disequilibrium` | LD decay & pruning |
| Pop Genetics | `/population-genetics` | Structure & admixture |
| Parentage | `/parentage-analysis` | Pedigree verification |
| Correlations | `/genetic-correlation` | Trait correlations |
| G×E | `/gxe-interaction` | AMMI & GGE biplot |
| Stability | `/stability-analysis` | Stability parameters |

## 🔬 Advanced Breeding

| Tool | Path | Description |
|------|------|-------------|
| Molecular Breeding | `/molecular-breeding` | MABC, gene pyramiding |
| Phenomics | `/phenomic-selection` | HTP & spectral indices |
| Speed Breeding | `/speed-breeding` | Accelerated generation |
| Doubled Haploid | `/doubled-haploid` | DH production |

## 🛠️ Tech Stack

- **React 18** + TypeScript
- **Vite** - Build tool
- **Tailwind CSS** + shadcn/ui
- **TanStack Query** - Server state
- **Zustand** - Local state
- **Dexie.js** - IndexedDB
- **React Hook Form** + Zod
- **Recharts** - Visualization

## 📱 PWA Features

- ✅ Offline-capable with service worker
- ✅ Installable on mobile/desktop
- ✅ IndexedDB for offline data
- ✅ Background sync
- ✅ Camera access for scanning

## 🔐 Authentication

Default development credentials:
- Create your first user via `make create-user` or the registration API
- All credentials should be set via environment variables

⚠️ Never commit credentials to version control!

## 🔄 API Integration

```typescript
import { apiClient } from '@/lib/api-client'

// BrAPI v2.1 compliant
const programs = await apiClient.getPrograms()
const germplasm = await apiClient.getGermplasm()
```

## 🎨 UI Components

Using shadcn/ui with Tailwind:
- Cards, Badges, Buttons
- Forms with validation
- Data tables with sorting
- Charts and visualizations
- Responsive sidebar navigation

## 📋 Available Scripts

```bash
bun run dev       # Development server
bun run build     # Production build
bun run preview   # Preview build
bun run lint      # ESLint
bun run format    # Prettier
bun run e2e       # E2E after frontend/e2e dependencies are installed
```

## 🌐 Environment Variables

```env
VITE_API_URL=http://localhost:8000
VITE_OPENAI_API_KEY=your-key
VITE_ANTHROPIC_API_KEY=your-key
```

---

*Built with 💚 for the global plant breeding community*
