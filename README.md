# Bijmantra - BrAPI v2.1 Plant Breeding PWA

A modern Progressive Web Application for plant breeding management, fully compliant with BrAPI v2.1 specification.

## Features

### ✅ Implemented Modules

#### 1. **Programs Management**
- List all breeding programs with pagination
- Create new programs
- View program details
- Edit program information
- Delete programs with confirmation

#### 2. **Trials Management**
- List all trials with pagination
- Create new trials linked to programs
- View trial details
- Edit trial information
- Delete trials with confirmation

#### 3. **Studies Management**
- List all studies with pagination
- Create new studies linked to trials and locations
- View study details
- Edit study information
- Delete studies with confirmation

#### 4. **Locations Management**
- List all locations with pagination
- Create new locations with coordinates
- View location details
- Edit location information
- Delete locations with confirmation

#### 5. **Dashboard**
- Overview statistics for all modules
- Quick access to recent programs
- Quick action buttons for creating new entities

### 🎨 UI Features

- Modern gradient-based design
- Smooth animations and transitions
- Vertical collapsible sidebar navigation
- Responsive layout for all screen sizes
- Glassmorphism effects
- Color-coded modules (Programs: Green, Trials: Purple, Studies: Blue, Locations: Orange)

### 🔐 Authentication

- JWT-based authentication
- Login/Register pages
- Protected routes
- Token persistence

## Tech Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- React Router for navigation
- TanStack Query for data fetching
- React Hook Form for form management

### Backend
- FastAPI (Python)
- PostgreSQL database
- Redis for caching
- MinIO for object storage
- BrAPI v2.1 compliant endpoints

## Getting Started

### Prerequisites
- Docker and Podman
- Node.js 18+
- Python 3.11+

### Installation

1. Start the infrastructure services:
```bash
cd bijmantra
podman compose up -d postgres redis minio
```

2. Start the backend:
```bash
cd backend
./start_dev.sh
```

3. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
bijmantra/
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Page components
│   │   ├── lib/        # Utilities and API client
│   │   └── App.tsx     # Main application component
│   └── package.json
├── backend/            # FastAPI backend application
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── models/     # Database models
│   │   └── core/       # Core functionality
│   └── requirements.txt
└── docker-compose.yml  # Infrastructure services
```

## BrAPI Compliance

This application implements the following BrAPI v2.1 modules:
- Core (Programs, Locations, Trials, Studies)
- Authentication
- Pagination
- Metadata responses

## Development Status

### Completed
- ✅ Authentication system
- ✅ Programs CRUD
- ✅ Trials CRUD
- ✅ Studies CRUD (List & Create)
- ✅ Locations CRUD (List & Create)
- ✅ Dashboard with statistics
- ✅ Modern UI with animations
- ✅ Responsive design

### In Progress
- 🚧 Study detail/edit pages
- 🚧 Location detail/edit pages
- 🚧 Germplasm module
- 🚧 Genotyping module
- 🚧 Phenotyping module

## License

MIT



## Developer: R.E.E.V.A.I. (Rural Empowerment through Emerging Value‑driven Agro‑Intelligence)

