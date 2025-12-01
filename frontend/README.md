# 🌱 Bijmantra Frontend

React Progressive Web Application for plant breeding data management with AI-powered phenotyping.

## 📊 Current Stats

| Metric | Count |
|--------|-------|
| **Total Pages** | 141 |
| **AI Tools** | 8 |
| **Genomic Tools** | 16 |
| **Breeding Tools** | 25+ |

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

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
- **Email**: admin@bijmantra.org
- **Password**: admin123

⚠️ Change in production!

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
npm run dev       # Development server
npm run build     # Production build
npm run preview   # Preview build
npm run lint      # ESLint
npm run format    # Prettier
```

## 🌐 Environment Variables

```env
VITE_API_URL=http://localhost:8000
VITE_OPENAI_API_KEY=your-key
VITE_ANTHROPIC_API_KEY=your-key
```

---

**Jay Shree Ganeshay Namo Namah!** 🙏
