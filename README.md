# 🌱 Bijmantra

**BrAPI v2.1 Compliant Plant Breeding Progressive Web Application**

> A modern, offline-capable plant breeding platform built on open standards.

[🚀 Quick Start](#quick-start) | [📖 Documentation](#documentation) | [💬 Community](#community) | [🤝 Contributing](#contributing)

---

## ✨ Features

- 🌾 **BrAPI v2.1 Compliant** - Full implementation of all 4 modules (Core, Phenotyping, Genotyping, Germplasm)
- 📱 **Progressive Web App** - Works offline, installable on any device, mobile-first design
- 🔄 **Federated Architecture** - Each organization owns their data, with optional federation
- 🔐 **Secure** - JWT authentication, HTTPS, data sovereignty, RBAC
- 🚀 **Modern Stack** - React + FastAPI + PostgreSQL + Podman
- 🌍 **Open Source** - MIT License, community-driven

## 🏗️ Architecture

```
Frontend (React PWA)
    ↓ HTTPS
Caddy Reverse Proxy
    ├─→ /brapi/* → FastAPI Backend
    └─→ /* → React Static Files
         ↓
    PostgreSQL + PostGIS
    Redis (Cache)
    MinIO (Images)
```

## 🚀 Quick Start

### Prerequisites

- **Podman** 5+ (or Docker)
- **Python** 3.11+
- **Node.js** 18+

### Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/denishdholaria/bijmantra.git
    cd bijmantra
    ```

2.  **Configure Environment**

    ```bash
    cp .env.example .env
    # Edit .env with your settings
    ```

3.  **Start Infrastructure**

    ```bash
    make dev
    # Or: podman-compose up -d
    ```

4.  **Access Application**
    - Frontend: http://localhost:5173
    - Backend API: http://localhost:8000/docs

## 📖 Documentation

- [Discussion: Architecture & Business Model](docs/discussion/d1.md)
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 💬 Community

- [GitHub Discussions](https://github.com/denishdholaria/bijmantra/discussions)
- [Issues](https://github.com/denishdholaria/bijmantra/issues)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with ❤️ for the plant breeding community.

**Jay Shree Ganeshay Namo Namah!** 🙏
