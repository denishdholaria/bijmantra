# 🌱 Bijmantra - BrAPI v2.1 Plant Breeding Platform

A comprehensive Progressive Web Application for plant breeding management, fully compliant with BrAPI v2.1 specification. Built with modern technologies for efficient breeding program management.

**170 Pages** | **BrAPI v2.1 Compliant** | **AI-Powered** | **Offline-First**

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

### 🤖 AI Integration & Computer Vision (8 Tools)
- **AI Assistant** - Multi-provider support (OpenAI, Anthropic, Google, Mistral)
- **Plant Vision AI** - Disease detection, growth stage, stress analysis
- **Field Scanner** - Real-time field scanning with continuous mode
- **Disease Atlas** - Comprehensive disease reference guide
- **Crop Health Dashboard** - Monitor health across trials
- **Yield Predictor** - AI-powered yield prediction with scenario analysis
- **Chrome AI** - Local Gemini Nano integration
- **Hybrid Mode** - Smart routing between local and cloud AI

### 🤝 Collaboration & Productivity (8 Tools)
- **Collaboration Hub** - Real-time team chat, shared items, activity feed
- **Team Management** - Members, roles, and permissions
- **Data Sync** - Offline-first data synchronization
- **Advanced Reports** - Custom report builder with scheduling
- **Protocol Library** - SOPs and breeding methods
- **Experiment Designer** - Trial design generator (CRD, RCBD, Alpha)
- **Resource Calendar** - Field ops, lab, equipment scheduling
- **Environment Monitor** - Real-time sensor data dashboard

### 📊 Program Management (9 Tools)
- **Cost Analysis** - Budget tracking and expense analysis
- **Publication Tracker** - Research outputs and citations
- **Training Hub** - Learning courses and certificates
- **Variety Release** - Release pipeline tracking (DUS, VCU)
- **Compliance Tracker** - Regulatory compliance monitoring
- **Gene Bank** - Genetic resources management
- **Breeding Goals** - Objective tracking with milestones
- **Market Analysis** - Market trends and trait demands
- **Stakeholder Portal** - Partner relationship management

### 🛠️ Developer & Analysis Tools (8 Tools)
- **Trial Comparison** - Compare trial performance metrics
- **Data Visualization** - Interactive chart builder gallery
- **API Explorer** - Test and explore BrAPI endpoints
- **Batch Operations** - Bulk data operations management
- **Field Map** - Interactive field and plot visualization
- **Plot History** - Historical data for each plot
- **Germplasm Passport** - Detailed passport data viewer
- **Sample Tracking** - Sample pipeline tracking

### 🌾 Field Operations (4 Tools)
- **Irrigation Planner** - Schedule and monitor irrigation zones
- **Pest Monitor** - Track and manage pest infestations
- **Growth Tracker** - Monitor plant growth and development
- **Harvest Log** - Record and track harvest data

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
| **Total Pages** | 170 |
| **BrAPI Endpoints** | 34/34 (100%) |
| **Breeding Tools** | 25+ |
| **Genomic Tools** | 16 |
| **AI Phenotyping** | 8 |
| **Collaboration Tools** | 8 |
| **Management Tools** | 9 |
| **Developer Tools** | 8 |
| **Field Operations** | 4 |
| **Help & Documentation** | 13 |


## 🎨 UI Features

- Modern gradient-based design with glassmorphism
- Responsive layout for desktop and mobile
- Collapsible sidebar navigation
- Dark/Light mode support
- PWA with offline capability
- Keyboard shortcuts
- Real-time collaboration features

## 🔧 Tech Stack

### Frontend
- React 18 + TypeScript
- Vite build tooling
- TailwindCSS + shadcn/ui
- TanStack Query
- Zustand state management
- TensorFlow.js (AI/ML)
- IndexedDB (offline storage)

### Backend
- FastAPI (Python)
- PostgreSQL database
- Redis caching
- MinIO object storage
- BrAPI v2.1 compliant API

### Infrastructure
- Nginx reverse proxy
- Docker/Podman containerization
- PWA Service Worker

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
├── frontend/           # React PWA (170 pages)
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── pages/      # Page components
│   │   ├── lib/        # Utilities, API, AI
│   │   └── store/      # Zustand stores
├── backend/            # FastAPI server
│   ├── app/
│   │   ├── api/        # BrAPI routes
│   │   ├── models/     # SQLAlchemy models
│   │   └── core/       # Auth, config
├── nginx/              # Production proxy config
├── rust/               # Future WebAssembly modules
└── docker-compose.yml
```

## 🌐 BrAPI v2.1 Compliance

Full implementation of BrAPI v2.1 specification:
- ✅ Core Module (Programs, Trials, Studies, Locations)
- ✅ Germplasm Module (Germplasm, Pedigree, Crosses)
- ✅ Phenotyping Module (Observations, Traits, Events)
- ✅ Genotyping Module (Samples, Variants, Calls)

## 🔮 Roadmap

- [ ] Mobile PWA Optimization
- [ ] Rust/WebAssembly Modules
- [ ] Drone Integration
- [ ] IoT Sensor Support
- [ ] Blockchain Traceability

## 📜 License

**Bijmantra Open Source License with Attribution (BOSLA)**

This software is open source with mandatory attribution requirements. You are free to use, modify, and distribute this software, but you MUST give visible credit to the creator.

**Required Attribution:**
```
Powered by Bijmantra - Created by Denish Dholaria / R.E.E.V.A.i
```

See [LICENSE](LICENSE) for full details.

## 👨‍💻 Developer

**R.E.E.V.A.i** - Rural Empowerment through Emerging Value-driven Agro-Intelligence

---

**ॐ श्री गणेशाय नमः** 🙏

*May Lord Ganesha remove all obstacles in the path of agricultural innovation*

*Jay Shree Ganeshay Namo Namah!*
