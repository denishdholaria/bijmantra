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
