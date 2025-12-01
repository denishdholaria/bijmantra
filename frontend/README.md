# Bijmantra Frontend

React Progressive Web Application for plant breeding data management.

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Available Scripts

```bash
npm run dev       # Start development server
npm run build     # Build for production
npm run preview   # Preview production build
npm run lint      # Run ESLint
npm run format    # Format code with Prettier
npm run test      # Run tests
```

## PWA Features

- ✅ Offline-capable
- ✅ Installable on mobile and desktop
- ✅ Service worker for caching
- ✅ IndexedDB for offline data storage
- ✅ Background sync for offline submissions

## Project Structure

```
src/
├── api/                # BrAPI client
│   ├── client.ts      # Base API client
│   ├── core/          # Core module endpoints
│   ├── phenotyping/   # Phenotyping endpoints
│   ├── genotyping/    # Genotyping endpoints
│   └── germplasm/     # Germplasm endpoints
├── components/        # React components
│   ├── ui/           # UI components
│   ├── layout/       # Layout components
│   ├── forms/        # Form components
│   └── tables/       # Table components
├── hooks/            # Custom React hooks
├── lib/              # Utilities
│   └── db.ts         # IndexedDB (Dexie.js)
├── pages/            # Page components
├── store/            # State management (Zustand)
├── types/            # TypeScript types
├── App.tsx           # Main App component
└── main.tsx          # Entry point
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **TanStack Query** - Server state management
- **Zustand** - Local state management
- **Dexie.js** - IndexedDB wrapper
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **Recharts** - Data visualization
- **Leaflet** - Maps

## Building for Production

```bash
npm run build
```

The build output will be in the `dist/` directory.

## PWA Installation

Users can install the app by:
1. Opening the app in a browser
2. Clicking the install prompt
3. Or using the browser's "Install App" option

## Offline Support

The app caches:
- Static assets (JS, CSS, images)
- BrAPI metadata (traits, methods, scales)
- Recent observation data
- Plant images

Data collected offline is automatically synced when the connection is restored.


## 🎯 Current Implementation Status

### ✅ Completed Features

#### Authentication
- Login page with JWT authentication
- Protected routes with auth guard
- Token storage in localStorage
- Auto-redirect on logout

#### Dashboard
- Overview cards for programs, trials, studies, locations
- Recent programs list
- Quick action buttons
- Real-time data from backend

#### Programs Module
- List all programs with pagination
- Create new program form
- View program details
- BrAPI v2.1 compliant responses

#### Infrastructure
- API client with BrAPI support
- Zustand store for authentication
- TanStack Query for data fetching
- Layout component with navigation
- Protected route wrapper
- Path aliases (@/ for src/)

### 🚧 Coming Soon

- Trials management UI
- Studies management UI
- Locations management with maps
- Program edit functionality
- Phenotyping data collection
- Offline sync with IndexedDB
- Image upload
- Data visualization

## 🔐 Default Credentials

For development/testing:
- **Email**: admin@bijmantra.org
- **Password**: admin123

⚠️ Change these in production!

## 🔄 API Integration

The frontend communicates with the FastAPI backend:
- Base URL: `http://localhost:8000`
- Proxy configured in `vite.config.ts`
- All requests include JWT token in Authorization header
- BrAPI v2.1 response format

### Example API Call

```typescript
import { apiClient } from '@/lib/api-client'

// Login
const { access_token } = await apiClient.login(email, password)

// Get programs
const response = await apiClient.getPrograms(page, pageSize)
const programs = response.result.data

// Create program
await apiClient.createProgram({
  programName: "My Program",
  abbreviation: "MP",
  objective: "Improve yield"
})
```

## 📱 PWA Configuration

Configured in `vite.config.ts`:
- Auto-update service worker
- Workbox for caching strategies
- Network-first for API calls
- Cache-first for static assets
- Manifest for installation

## 🎨 Styling Guide

Using Tailwind CSS utility classes:
- Primary color: Green (`green-600`)
- Spacing: Consistent 4px grid
- Responsive: Mobile-first approach
- Components: Clean, minimal design

## 🧪 Testing the Frontend

1. Start backend: `make dev-backend`
2. Start frontend: `npm run dev`
3. Open: `http://localhost:5173`
4. Login with default credentials
5. Explore dashboard and programs

---

**Jay Shree Ganeshay Namo Namah!** 🙏
