# 🌱 Bijmantra - BrAPI v2.1 Plant Breeding Platform

A comprehensive Progressive Web Application for plant breeding management, fully compliant with BrAPI v2.1 specification. Built with modern technologies for efficient breeding program management.

## 🚀 Features

### Core Modules (BrAPI v2.1 Compliant)
- **Programs** - Breeding program management
- **Trials** - Multi-environment trial management
- **Studies** - Study design and execution
- **Locations** - Site management with GPS coordinates
- **Germplasm** - Accession and pedigree management
- **Observations** - Phenotypic data collection
- **Traits** - Observation variable definitions
- **Samples** - Genotyping sample management

### 🧬 Advanced Genomics (16 Tools)
- **Genetic Diversity** - Population diversity metrics (Shannon, Simpson, Fst)
- **Breeding Values** - BLUP/GBLUP estimation
- **QTL Mapping** - Linkage mapping and GWAS
- **Genomic Selection** - GS model training and GEBV prediction
- **Marker-Assisted Selection** - Foreground/background selection
- **Haplotype Analysis** - Block detection and breeding applications
- **Linkage Disequilibrium** - LD decay and pruning
- **Population Genetics** - Structure, PCA, admixture analysis
- **Parentage Analysis** - Pedigree verification
- **Genetic Correlations** - Trait relationship analysis
- **G×E Interaction** - AMMI, GGE biplot analysis
- **Stability Analysis** - Multiple stability parameters

### 🔬 Advanced Breeding Technologies
- **Molecular Breeding** - MABC, MARS, gene pyramiding
- **Phenomic Selection** - HTP, spectral indices, prediction models
- **Speed Breeding** - Accelerated generation advancement
- **Doubled Haploid** - DH production and management

### 🤖 AI Integration & Computer Vision
- **AI Assistant** - Multi-provider support (OpenAI, Anthropic, Google, Mistral)
- **Plant Vision AI** - Disease detection, growth stage, stress analysis
- **Field Scanner** - Real-time field scanning with continuous mode
- **Disease Atlas** - Comprehensive disease reference guide
- **Crop Health Dashboard** - Monitor health across trials
- **Yield Predictor** - AI-powered yield prediction with scenario analysis
- **Chrome AI** - Local Gemini Nano integration
- **Hybrid Mode** - Smart routing between local and cloud AI

### 🛠️ Breeding Tools (25+)
- Trial Design (RCBD, Alpha-lattice, Augmented)
- Selection Index Calculator
- Genetic Gain Predictor
- Pedigree Viewer
- Crossing Planner
- Harvest Planner
- Seed Inventory
- Field Book
- Label Printing
- Weather Integration
- And many more...

## 📊 Statistics

| Metric | Count |
|--------|-------|
| **Total Pages** | 141 |
| **BrAPI Endpoints** | 34/34 (100%) |
| **Breeding Tools** | 25+ |
| **Genomic Tools** | 16 |
| **AI Phenotyping** | 8 |

## 🎨 UI Features

- Modern gradient-based design with glassmorphism
- Responsive layout for desktop and mobile
- Collapsible sidebar navigation
- Dark/Light mode support
- PWA with offline capability
- Keyboard shortcuts

## 🔧 Tech Stack

### Frontend
- React 18 + TypeScript
- Vite build tooling
- TailwindCSS + shadcn/ui
- TanStack Query
- Zustand state management

### Backend
- FastAPI (Python)
- PostgreSQL database
- Redis caching
- MinIO object storage
- BrAPI v2.1 compliant API

## 🚀 Getting Started

### Prerequisites
- Docker/Podman
- Node.js 18+
- Python 3.11+

### Quick Start

```bash
# Clone the repository
git clone https://github.com/denishdholaria/bijmantra.git
cd bijmantra

# Start infrastructure
podman compose up -d postgres redis minio

# Start backend
cd backend && ./start_dev.sh

# Start frontend (new terminal)
cd frontend && npm install && npm run dev
```

### Access Points
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **BrAPI**: http://localhost:8000/brapi/v2

## 📁 Project Structure

```
bijmantra/
├── frontend/           # React PWA
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── pages/      # 136 page components
│   │   ├── lib/        # Utilities, API, AI
│   │   └── store/      # Zustand stores
├── backend/            # FastAPI server
│   ├── app/
│   │   ├── api/        # BrAPI routes
│   │   ├── models/     # SQLAlchemy models
│   │   └── core/       # Auth, config
└── docker-compose.yml
```

## 🌐 BrAPI v2.1 Compliance

Full implementation of BrAPI v2.1 specification:
- ✅ Core Module (Programs, Trials, Studies, Locations)
- ✅ Germplasm Module (Germplasm, Pedigree, Crosses)
- ✅ Phenotyping Module (Observations, Traits, Events)
- ✅ Genotyping Module (Samples, Variants, Calls)

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

## 👨‍💻 Developer

**R.E.E.V.A.i** - Rural Empowerment through Emerging Value-driven Agro-Intelligence

---

*Jay Shree Ganeshay Namo Namah!* 🙏
