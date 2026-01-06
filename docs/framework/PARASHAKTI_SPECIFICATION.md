# Parashakti Framework — Technical Specification

> **परा-शक्ति** (Parā-Śakti): The supreme energy that powers all modules
>
> Version: 1.0.0-beta.1 Prathama (प्रथम)
> Created: 2025-12-05
> Last Updated: 2026-01-01
> Status: Production (Beta Testing)

---

## Executive Summary

Parashakti is the foundational framework for Bijmantra — a modular, extensible platform for agricultural science, plant breeding, and future space-based research. This document defines the architecture, principles, and implementation guidelines.

### Current Implementation Status (v1.0.0-beta.1)

| Metric | Value |
|--------|-------|
| Total Pages | 221 (211 functional, 2 experimental) |
| API Endpoints | 1,370 (201 BrAPI + 1,169 custom) |
| BrAPI v2.1 Coverage | 100% (201/201 endpoints) |
| Database Models | 106 |
| Modules | 8 |
| Workspaces | 5 + Custom |

### Design Philosophy

1. **Modular Monolith** — Single deployable unit with clear internal boundaries
2. **Module-Based** — Self-contained feature domains that can evolve independently (8 modules)
3. **Workspace Gateway** — Role-based navigation pathways (5 workspaces)
4. **Integration-First** — Connect to external systems rather than rebuild them
5. **Multi-Engine Compute** — Right tool for the job (Python, Rust, Fortran)
6. **Offline-Capable** — Field-ready with robust sync
7. **Future-Proof** — Can split into microservices when scale demands

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Layer Definitions](#2-layer-definitions)
3. [Module System](#3-module-system)
4. [Workspace Gateway](#4-workspace-gateway)
5. [Core Services](#5-core-services)
6. [Compute Engines](#6-compute-engines)
7. [Integration Hub](#7-integration-hub)
8. [Data Layer](#8-data-layer)
9. [Offline & Sync](#9-offline--sync)
10. [Security Model](#10-security-model)
11. [Folder Structure](#11-folder-structure)
12. [Migration Path](#12-migration-path)
13. [API Contracts](#13-api-contracts)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PARASHAKTI FRAMEWORK v1.0.0-beta.1             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      SHELL LAYER                               │ │
│  │   Navigation │ Authentication │ Theme │ Notifications │ Search │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                 │                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   WORKSPACE GATEWAY                            │ │
│  │   Plant Breeding │ Seed Business │ Innovation │ Gene Bank │ Admin│
│  └────────────────────────────────────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────┼───────────────────────────────┐   │
│  │               MODULE LAYER (8 Modules, Lazy Loaded)           │   │
│  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐│   │
│  │  │Breed- │ │Pheno- │ │Geno-  │ │Seed   │ │Enviro-│ │Seed   ││   │
│  │  │ing    │ │typing │ │mics   │ │Bank   │ │nment  │ │Ops    ││   │
│  │  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘│   │
│  │  ┌───────┐ ┌───────┐                                        │   │
│  │  │Know-  │ │Settings                                        │   │
│  │  │ledge  │ │& Admin│                                        │   │
│  │  └───────┘ └───────┘                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                 │                                    │
│  ┌──────────────────────────────┼───────────────────────────────┐   │
│  │                    CORE SERVICES                              │   │
│  │   Database │ Storage │ Queue │ Cache │ Events │ Sync │ Auth  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                 │                                    │
│  ┌──────────────────────────────┼───────────────────────────────┐   │
│  │                   COMPUTE ENGINES                             │   │
│  │        Python (API/ML) │ Rust/WASM │ Fortran (Stats)         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                 │                                    │
│  ┌──────────────────────────────┼───────────────────────────────┐   │
│  │                  INTEGRATION HUB                              │   │
│  │   NCBI │ EarthEngine │ ERPNext │ BrAPI │ Weather │ AI APIs   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Principles

| Principle | Description |
|-----------|-------------|
| Single Deployment | One backend, one frontend, one database |
| Clear Boundaries | Each module has isolated code, routes, and schemas |
| Workspace Gateway | Role-based navigation pathways for different user types |
| Lazy Loading | Modules load only when accessed |
| Feature Flags | Modules can be enabled/disabled per deployment |
| Event-Driven | Modules communicate via events, not direct calls |
| Plugin Architecture | Integrations implement standard interfaces |

---

## 2. Layer Definitions

### 2.1 Shell Layer

The always-loaded application shell providing consistent UX across all divisions.

**Components:**
- **Navigation** — Auto-generated from Division Registry
- **Authentication** — Login, logout, session management
- **Theme** — Dark/light mode, user preferences
- **Notifications** — System-wide alerts and messages
- **Search** — Global search across all divisions
- **User Menu** — Profile, settings, organization switcher

**Implementation:**
```typescript
// frontend/src/framework/shell/Shell.tsx
export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar divisions={useDivisionRegistry()} />
      <Header>
        <GlobalSearch />
        <NotificationBell />
        <UserMenu />
      </Header>
      <main>{children}</main>
    </div>
  );
}
```

### 2.2 Module Layer

Self-contained feature domains loaded on demand. As of v1.0.0-beta.1, there are **8 modules**:

| # | Module | Pages | Endpoints | Description |
|---|--------|-------|-----------|-------------|
| 1 | Breeding | 35 | 120 | Programs, trials, crossing, selection |
| 2 | Phenotyping | 25 | 85 | Observations, traits, field ops |
| 3 | Genomics | 35 | 107 | Genotyping, analysis, molecular |
| 4 | Seed Bank | 15 | 59 | Vaults, accessions, conservation |
| 5 | Environment | 20 | 97 | Weather, soil, solar, sensors |
| 6 | Seed Operations | 22 | 96 | Quality, processing, DUS |
| 7 | Knowledge | 5 | 35 | Forums, training |
| 8 | Settings & Admin | 35 | 79 | Settings, teams, integrations |

**Characteristics:**
- Each module is a separate code-split chunk
- Has its own routes, pages, components, hooks
- Registers with the framework via Module Registry
- Can declare dependencies on other modules
- Has a defined status: `active`, `beta`, `planned`, `visionary`

### 2.3 Core Services Layer

Shared infrastructure used by all divisions.

| Service | Purpose |
|---------|---------|
| Database | PostgreSQL connection pool, query builder |
| Storage | File uploads, MinIO/S3 integration |
| Queue | Background job processing |
| Cache | Redis for frequently accessed data |
| Events | Pub/sub for inter-division communication |
| Sync | Offline data synchronization |
| Auth | JWT tokens, permissions, RBAC |

### 2.4 Compute Engines Layer

Specialized runtimes for different workloads.

| Engine | Use Case | Location |
|--------|----------|----------|
| Python | API, ML inference, data processing | Server |
| Rust | Genomics, matrix operations | Server + WASM |
| Fortran | Statistical algorithms (BLUP, REML) | Server |

### 2.5 Integration Hub Layer

Standardized adapters for external services.

All integrations implement a common interface, enabling:
- Consistent configuration (API keys in settings)
- Health checks and connection testing
- Unified error handling
- Audit logging

---

## 3. Module System

> **Note:** The original spec used "Division" terminology. As of v1.0.0-beta.1, we use "Module" to better reflect the 8-module architecture implemented Dec 25, 2025.

### 3.1 Module Registry

Central registry that defines all available modules.

**File:** `frontend/src/framework/registry/divisions.ts` (693 lines)

```typescript
// frontend/src/framework/registry/types.ts
export interface Division {
  // Identity
  id: string;                    // Unique identifier: 'plant-sciences'
  name: string;                  // Display name: 'Plant Sciences'
  description: string;           // Short description
  icon: string;                  // Lucide icon name
  
  // Routing
  route: string;                 // Base route: '/programs'
  component: React.LazyExoticComponent<React.ComponentType>;
  
  // Access Control
  requiredPermissions: string[]; // ['read:plant_sciences']
  featureFlag?: string;          // Optional feature flag
  
  // Metadata
  status: 'active' | 'beta' | 'planned' | 'visionary';
  version: string;
  dependencies?: string[];       // Other module IDs this depends on
  
  // Subsections (for navigation)
  sections?: DivisionSection[];
}

export interface DivisionSection {
  id: string;
  name: string;
  route: string;
  icon?: string;
  isAbsolute?: boolean;          // If true, route is absolute path
  items?: DivisionSectionItem[]; // Nested items for subgroups
}
```

### 3.2 Current Module Registration (v1.0.0-beta.1)

**File:** `frontend/src/framework/registry/divisions.ts`

The 8 modules are registered with their sections and subgroups:

```typescript
// frontend/src/framework/registry/divisions.ts
import { lazy } from 'react';
import { Division } from './types';

export const divisions: Division[] = [
  // Module 1: Plant Sciences (Breeding + Phenotyping + Genomics combined)
  {
    id: 'plant-sciences',
    name: 'Plant Sciences',
    description: 'Breeding, genomics, phenotyping, and field operations',
    icon: 'Seedling',
    route: '/programs',
    component: lazy(() => import('@/divisions/plant-sciences')),
    requiredPermissions: ['read:plant_sciences'],
    status: 'active',
    version: '1.0.0',
    sections: [
      // 10 subgroups: Breeding, Crossing, Selection, Phenotyping, 
      // Genotyping, Genomics, Field Ops, Analysis, AI & Compute, Analysis Tools
    ],
  },

  // Module 2: Seed Bank
  {
    id: 'seed-bank',
    name: 'Seed Bank',
    description: 'Genetic resources preservation and germplasm conservation',
    icon: 'Warehouse',
    route: '/seed-bank',
    component: lazy(() => import('@/divisions/seed-bank')),
    requiredPermissions: ['read:seed_bank'],
    status: 'active',
    version: '1.0.0',
  },

  // Module 3: Environment (merged Earth Systems + Sun-Earth Systems)
  {
    id: 'environment',
    name: 'Environment',
    description: 'Weather, climate, soil, solar radiation, and environmental monitoring',
    icon: 'Globe',
    route: '/earth-systems',
    component: lazy(() => import('@/divisions/earth-systems')),
    requiredPermissions: ['read:earth_systems'],
    status: 'active',
    version: '1.0.0',
  },

  // Module 4: Sensor Networks
  {
    id: 'sensor-networks',
    name: 'Sensor Networks',
    description: 'IoT integration and environmental monitoring',
    icon: 'Radio',
    route: '/sensor-networks',
    component: lazy(() => import('@/divisions/sensor-networks')),
    requiredPermissions: ['read:sensor_networks'],
    status: 'active',
    version: '1.0.0',
  },

  // Module 5: Seed Commerce (merged Seed Operations + Commercial)
  {
    id: 'seed-commerce',
    name: 'Seed Commerce',
    description: 'Lab testing, processing, inventory, dispatch, DUS testing & licensing',
    icon: 'Building2',
    route: '/seed-operations',
    component: lazy(() => import('@/divisions/seed-operations')),
    requiredPermissions: ['read:seed_operations'],
    status: 'active',
    version: '1.0.0',
  },

  // Module 6: Space Research
  {
    id: 'space-research',
    name: 'Space Research',
    description: 'Interplanetary agriculture and space agency collaborations',
    icon: 'Rocket',
    route: '/space-research',
    component: lazy(() => import('@/divisions/space-research')),
    requiredPermissions: ['read:space_research'],
    status: 'active',
    version: '1.0.0',
  },

  // Module 7: Knowledge
  {
    id: 'knowledge',
    name: 'Knowledge',
    description: 'Documentation, training, and community resources',
    icon: 'BookOpen',
    route: '/help',
    component: lazy(() => import('@/divisions/knowledge')),
    requiredPermissions: ['read:knowledge'],
    status: 'active',
    version: '0.6.0',
  },

  // Module 8: Settings & Admin
  {
    id: 'settings',
    name: 'Settings',
    description: 'System configuration, integrations, and administration',
    icon: 'Settings',
    route: '/settings',
    component: lazy(() => import('@/divisions/integrations')),
    requiredPermissions: ['manage:settings'],
    status: 'active',
    version: '1.0.0',
  },
];
```

### 3.3 Module Structure (Frontend)

Each module follows a consistent internal structure:

```
frontend/src/divisions/plant-sciences/
├── index.ts                 # Module entry point & routes
├── routes.tsx               # Route definitions
├── pages/                   # Page components
│   ├── Dashboard.tsx
│   ├── breeding/
│   │   ├── Programs.tsx
│   │   ├── Trials.tsx
│   │   └── Studies.tsx
│   ├── genomics/
│   │   ├── Germplasm.tsx
│   │   ├── Genotyping.tsx
│   │   └── GenomicTools.tsx
│   └── ...
├── components/              # Module-specific components
├── hooks/                   # Module-specific hooks
├── api/                     # API client functions
├── store/                   # Zustand stores (if needed)
└── types/                   # TypeScript types
```

### 3.4 Module Structure (Backend)

```
backend/app/modules/plant_sciences/
├── __init__.py              # Module initialization
├── router.py                # FastAPI router (mounts all sub-routers)
├── breeding/
│   ├── routes.py            # API endpoints
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── services.py          # Business logic
│   └── crud.py              # Database operations
├── genomics/
│   ├── routes.py
│   ├── models.py
│   └── ...
└── ...
```

### 3.5 Module Communication

Modules communicate via the Event Bus, never by direct imports.

```python
# Module A publishes an event
await event_bus.publish("germplasm.created", {
    "germplasm_id": "G001",
    "species": "Zea mays",
    "organization_id": "org_123"
})

# Module B subscribes and reacts
@event_bus.on("germplasm.created")
async def handle_germplasm_created(payload: dict):
    # Create corresponding seed bank record
    await create_conservation_record(payload["germplasm_id"])
```

---

## 4. Workspace Gateway

> **New in v1.0.0-beta.1** — Implemented Dec 25-26, 2025

The Workspace Gateway provides role-based navigation pathways, allowing different user types to access relevant modules through personalized workspaces.

### 4.1 Workspace Architecture

**File:** `frontend/src/framework/registry/workspaces.ts` (840 lines)

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKSPACE GATEWAY                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │   PLANT     │  │    SEED     │  │ INNOVATION  │        │
│   │  BREEDING   │  │  BUSINESS   │  │    LAB      │        │
│   │   (83 pg)   │  │   (22 pg)   │  │   (28 pg)   │        │
│   │  BrAPI ✓    │  │             │  │             │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │   GENE      │  │   ADMIN     │  │   CUSTOM    │        │
│   │   BANK      │  │             │  │ WORKSPACES  │        │
│   │   (34 pg)   │  │   (25 pg)   │  │  (user)     │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Workspace Definitions

```typescript
// frontend/src/types/workspace.ts
export type WorkspaceId = 'breeding' | 'seed-ops' | 'research' | 'genebank' | 'admin';

export interface Workspace {
  id: WorkspaceId;
  name: string;
  description: string;
  longDescription: string;
  icon: string;
  color: string;                    // Tailwind gradient classes
  bgColor: string;                  // Background color
  landingRoute: string;             // Dashboard route
  modules: ModuleId[];              // Modules in this workspace
  targetUsers: string[];            // Target user roles
  pageCount: number;
  isBrAPIAligned: boolean;          // BrAPI compliance badge
}
```

### 4.3 Five Core Workspaces

| Workspace | ID | Pages | Modules | Target Users |
|-----------|-----|-------|---------|--------------|
| Plant Breeding | `breeding` | 83 | core, germplasm, phenotyping, genotyping | Breeders, Geneticists |
| Seed Business | `seed-ops` | 22 | lab-testing, processing, inventory, dispatch, DUS | Seed Companies, Labs |
| Innovation Lab | `research` | 28 | space-research, ai-vision, analytics, analysis-tools | Scientists, PhD Students |
| Gene Bank | `genebank` | 34 | seed-bank, environment, sensors | Curators, Conservation Officers |
| Administration | `admin` | 25 | settings, users-teams, integrations, system, tools | IT Admins, Managers |

### 4.4 Custom Workspaces

Users can create personalized workspaces by selecting pages from any module.

**File:** `frontend/src/store/customWorkspaceStore.ts`

```typescript
interface CustomWorkspace {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  pages: string[];              // Page IDs from any module
  createdAt: string;
  updatedAt: string;
}
```

**Features:**
- 10 predefined templates (Field Researcher, Lab Manager, etc.)
- Max 10 custom workspaces per user
- Max 50 pages per workspace
- Stored in browser LocalStorage

### 4.5 Gateway Page

**File:** `frontend/src/pages/WorkspaceGateway.tsx`

The Gateway page is shown after login, allowing users to select their workspace.

**Features:**
- Full-page workspace selector
- 5 workspace cards with icons, descriptions, page counts
- BrAPI badge for compliant workspaces
- "Set as default" checkbox with persistence
- Keyboard navigation (arrow keys, 1-5 number keys, Enter, Escape)
- ARIA labels and screen reader support
- Animated transitions

### 4.6 Workspace Switcher

**File:** `frontend/src/components/navigation/WorkspaceSwitcher.tsx`

Header dropdown for quick workspace switching.

**Features:**
- Current workspace indicator with icon
- Recent workspaces section (last 3)
- All workspaces list with descriptions
- Set as default option (star icon)
- "Open Gateway" link for full selection view

### 4.7 Backend Integration

**File:** `backend/app/api/v2/profile.py`

User workspace preferences are persisted via API:

```python
# Endpoints
GET    /api/v2/profile/workspace           # Get preferences
PATCH  /api/v2/profile/workspace           # Update preferences
PUT    /api/v2/profile/workspace/default   # Set default
DELETE /api/v2/profile/workspace/default   # Clear default
```

**Database:** `user_preferences` table with columns:
- `default_workspace` — User's default workspace ID
- `recent_workspaces` — JSON array of recent workspace IDs
- `show_gateway_on_login` — Boolean flag for gateway display
- `last_workspace` — Last active workspace

---

## 5. Core Services

### 5.1 Event Bus

Decoupled communication between divisions and services.

```python
# backend/app/core/events/bus.py
from typing import Callable, Dict, List
import asyncio

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
    
    async def publish(self, event: str, payload: dict) -> None:
        """Publish an event to all subscribers."""
        await self._queue.put((event, payload))
        # Also log to audit trail
        await self._log_event(event, payload)
    
    def subscribe(self, event: str) -> Callable:
        """Decorator to subscribe to an event."""
        def decorator(handler: Callable):
            if event not in self._subscribers:
                self._subscribers[event] = []
            self._subscribers[event].append(handler)
            return handler
        return decorator
    
    async def _process_events(self):
        """Background task to process events."""
        while True:
            event, payload = await self._queue.get()
            handlers = self._subscribers.get(event, [])
            for handler in handlers:
                try:
                    await handler(payload)
                except Exception as e:
                    logger.error(f"Event handler failed: {event} - {e}")

# Global instance
event_bus = EventBus()
```

**Standard Events:**

| Event Pattern | Example | Description |
|---------------|---------|-------------|
| `{entity}.created` | `germplasm.created` | New record created |
| `{entity}.updated` | `trial.updated` | Record modified |
| `{entity}.deleted` | `observation.deleted` | Record removed |
| `{division}.sync.completed` | `plant_sciences.sync.completed` | Sync finished |
| `integration.{name}.connected` | `integration.ncbi.connected` | External service connected |

### 5.2 Feature Flags

Control division and feature availability.

```python
# backend/app/core/features/flags.py
from enum import Enum
from typing import Optional

class FeatureFlag(str, Enum):
    ENVIRONMENT_ENABLED = "ENVIRONMENT_ENABLED"
    SPACE_RESEARCH_ENABLED = "SPACE_RESEARCH_ENABLED"
    SENSOR_NETWORKS_ENABLED = "SENSOR_NETWORKS_ENABLED"
    AI_FEATURES_ENABLED = "AI_FEATURES_ENABLED"

class FeatureFlagService:
    def __init__(self, config: dict):
        self._flags = config
    
    def is_enabled(self, flag: FeatureFlag, org_id: Optional[str] = None) -> bool:
        """Check if a feature is enabled globally or for an organization."""
        # Check org-specific override first
        if org_id:
            org_flags = self._get_org_flags(org_id)
            if flag.value in org_flags:
                return org_flags[flag.value]
        # Fall back to global setting
        return self._flags.get(flag.value, False)
```

### 5.3 Permission System

Role-based access control with module-level granularity.

```python
# backend/app/core/auth/permissions.py
from enum import Enum

class Permission(str, Enum):
    # Plant Sciences
    READ_PLANT_SCIENCES = "read:plant_sciences"
    WRITE_PLANT_SCIENCES = "write:plant_sciences"
    ADMIN_PLANT_SCIENCES = "admin:plant_sciences"
    
    # Seed Bank
    READ_SEED_BANK = "read:seed_bank"
    WRITE_SEED_BANK = "write:seed_bank"
    
    # Environment
    READ_ENVIRONMENT = "read:environment"
    WRITE_ENVIRONMENT = "write:environment"
    
    # Commercial
    READ_COMMERCIAL = "read:commercial"
    WRITE_COMMERCIAL = "write:commercial"
    ADMIN_COMMERCIAL = "admin:commercial"
    
    # System
    ADMIN_SYSTEM = "admin:system"
    MANAGE_INTEGRATIONS = "manage:integrations"
    MANAGE_USERS = "manage:users"

# Role definitions
ROLES = {
    "viewer": [Permission.READ_PLANT_SCIENCES, Permission.READ_SEED_BANK],
    "breeder": [
        Permission.READ_PLANT_SCIENCES, Permission.WRITE_PLANT_SCIENCES,
        Permission.READ_SEED_BANK,
    ],
    "researcher": [
        Permission.READ_PLANT_SCIENCES, Permission.WRITE_PLANT_SCIENCES,
        Permission.READ_SEED_BANK, Permission.WRITE_SEED_BANK,
        Permission.READ_ENVIRONMENT,
    ],
    "admin": list(Permission),  # All permissions
}
```

### 5.4 Background Task Queue

For long-running operations.

```python
# backend/app/core/queue/tasks.py
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional
import uuid

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    task_type: str
    payload: dict
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskQueue:
    async def submit(
        self,
        task_type: str,
        payload: dict,
        priority: int = 0
    ) -> str:
        """Submit a task and return task ID."""
        task_id = str(uuid.uuid4())
        # Store in database and queue for processing
        return task_id
    
    async def get_status(self, task_id: str) -> Task:
        """Get current task status."""
        pass
    
    async def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        pass
```

---

## 6. Compute Engines

### 6.1 Multi-Engine Architecture

Different computational tasks require different tools.

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPUTE DISPATCHER                        │
│                                                              │
│   Task Request → Engine Selection → Execution → Result      │
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │   PYTHON    │  │    RUST     │  │   FORTRAN   │        │
│   │             │  │             │  │             │        │
│   │ • API Logic │  │ • Genomics  │  │ • BLUP/REML │        │
│   │ • ML/AI     │  │ • Matrices  │  │ • Statistics│        │
│   │ • Data Proc │  │ • WASM      │  │ • Kinship   │        │
│   │ • Glue Code │  │ • LD/PCA    │  │ • GxE       │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Engine Selection Rules

| Task Type | Engine | Reason |
|-----------|--------|--------|
| API request handling | Python | Fast development, async I/O |
| ML model inference | Python | TensorFlow/PyTorch ecosystem |
| Genomic relationship matrix | Rust | O(n²) computation, memory safety |
| LD analysis | Rust | Large marker datasets |
| PCA/SVD | Rust | Matrix operations |
| BLUP/GBLUP | Fortran | Proven algorithms, LAPACK |
| REML estimation | Fortran | Numerical stability |
| Stability analysis | Fortran | Statistical heritage |
| Browser-side genomics | Rust/WASM | Client-side performance |

### 6.3 Compute Interface

```python
# backend/app/core/compute/dispatcher.py
from enum import Enum
from typing import Any, Optional

class ComputeEngine(str, Enum):
    PYTHON = "python"
    RUST = "rust"
    FORTRAN = "fortran"
    WASM = "wasm"  # Client-side only
    AUTO = "auto"  # Let dispatcher decide

class ComputeDispatcher:
    """Routes compute tasks to appropriate engines."""
    
    # Task type to engine mapping
    ENGINE_MAP = {
        "genomics.grm": ComputeEngine.RUST,
        "genomics.ld": ComputeEngine.RUST,
        "genomics.pca": ComputeEngine.RUST,
        "stats.blup": ComputeEngine.FORTRAN,
        "stats.reml": ComputeEngine.FORTRAN,
        "stats.gxe": ComputeEngine.FORTRAN,
        "ml.predict": ComputeEngine.PYTHON,
        "ml.train": ComputeEngine.PYTHON,
    }
    
    async def dispatch(
        self,
        task_type: str,
        payload: dict,
        engine: ComputeEngine = ComputeEngine.AUTO
    ) -> Any:
        """Dispatch task to appropriate engine."""
        if engine == ComputeEngine.AUTO:
            engine = self.ENGINE_MAP.get(task_type, ComputeEngine.PYTHON)
        
        if engine == ComputeEngine.RUST:
            return await self._call_rust(task_type, payload)
        elif engine == ComputeEngine.FORTRAN:
            return await self._call_fortran(task_type, payload)
        else:
            return await self._call_python(task_type, payload)
    
    async def _call_rust(self, task_type: str, payload: dict) -> Any:
        """Call Rust library via PyO3 bindings."""
        from bijmantra_rust import genomics
        # Route to appropriate Rust function
        pass
    
    async def _call_fortran(self, task_type: str, payload: dict) -> Any:
        """Call Fortran library via ctypes/f2py."""
        import bijmantra_fortran
        # Route to appropriate Fortran function
        pass
```

### 6.4 WASM for Browser

Client-side compute for offline capability.

```typescript
// frontend/src/framework/compute/wasm.ts
import init, { calculate_grm, run_pca } from '@/wasm/pkg/bijmantra_genomics';

class WasmCompute {
  private initialized = false;
  
  async init(): Promise<void> {
    if (!this.initialized) {
      await init();
      this.initialized = true;
    }
  }
  
  async calculateGRM(markers: Float64Array, nSamples: number, nMarkers: number): Promise<Float64Array> {
    await this.init();
    return calculate_grm(markers, nSamples, nMarkers);
  }
  
  async runPCA(data: Float64Array, nComponents: number): Promise<PCAResult> {
    await this.init();
    return run_pca(data, nComponents);
  }
}

export const wasmCompute = new WasmCompute();
```

---

## 7. Integration Hub

### 7.1 Adapter Interface

All external integrations implement a standard interface.

```python
# backend/app/integrations/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum

class IntegrationStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"

@dataclass
class IntegrationConfig:
    """Configuration for an integration."""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    extra: Dict[str, Any] = None

@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    records_synced: int
    errors: List[str]
    duration_ms: int

class IntegrationAdapter(ABC):
    """Base class for all external integrations."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this integration."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this integration provides."""
        pass
    
    @property
    @abstractmethod
    def required_config(self) -> List[str]:
        """List of required configuration keys."""
        pass
    
    @property
    def optional_config(self) -> List[str]:
        """List of optional configuration keys."""
        return []
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the integration is properly configured and reachable."""
        pass
    
    @abstractmethod
    async def get_status(self) -> IntegrationStatus:
        """Get current integration status."""
        pass
    
    async def sync(self, direction: str = "pull") -> SyncResult:
        """Sync data with external service. Override if supported."""
        raise NotImplementedError("This integration does not support sync")
```

### 7.2 Example Integrations

```python
# backend/app/integrations/ncbi.py
from .base import IntegrationAdapter, IntegrationStatus, IntegrationConfig
import httpx

class NCBIAdapter(IntegrationAdapter):
    """Integration with NCBI databases (GenBank, etc.)."""
    
    id = "ncbi"
    name = "NCBI"
    description = "Access GenBank, PubMed, and other NCBI databases"
    required_config = ["api_key", "email"]
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self._client = httpx.AsyncClient()
    
    async def test_connection(self) -> bool:
        try:
            response = await self._client.get(
                f"{self.BASE_URL}/einfo.fcgi",
                params={"api_key": self.config.api_key}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_status(self) -> IntegrationStatus:
        if not self.config.api_key:
            return IntegrationStatus.NOT_CONFIGURED
        if await self.test_connection():
            return IntegrationStatus.CONNECTED
        return IntegrationStatus.ERROR
    
    async def fetch_sequence(self, accession: str) -> dict:
        """Fetch sequence data from GenBank."""
        response = await self._client.get(
            f"{self.BASE_URL}/efetch.fcgi",
            params={
                "db": "nucleotide",
                "id": accession,
                "rettype": "gb",
                "retmode": "json",
                "api_key": self.config.api_key,
            }
        )
        return response.json()
    
    async def search(self, query: str, database: str = "nucleotide") -> list:
        """Search NCBI databases."""
        pass
```

```python
# backend/app/integrations/earth_engine.py
class EarthEngineAdapter(IntegrationAdapter):
    """Integration with Google Earth Engine."""
    
    id = "earth_engine"
    name = "Google Earth Engine"
    description = "Satellite imagery and geospatial analysis"
    required_config = ["service_account_key"]
    
    async def get_ndvi(self, geometry: dict, date_range: tuple) -> dict:
        """Get NDVI values for a field geometry."""
        pass
    
    async def get_weather_history(self, location: tuple, days: int) -> list:
        """Get historical weather data for a location."""
        pass
```

```python
# backend/app/integrations/erpnext.py
class ERPNextAdapter(IntegrationAdapter):
    """Integration with ERPNext for business operations."""
    
    id = "erpnext"
    name = "ERPNext"
    description = "ERP integration for inventory, accounting, and HR"
    required_config = ["base_url", "api_key", "api_secret"]
    
    async def sync_seed_lots(self, direction: str = "push") -> SyncResult:
        """Sync seed lot inventory with ERPNext."""
        pass
    
    async def create_sales_order(self, order_data: dict) -> str:
        """Create a sales order in ERPNext."""
        pass
```

### 7.3 Integration Registry

```python
# backend/app/integrations/registry.py
from typing import Dict, Type
from .base import IntegrationAdapter
from .ncbi import NCBIAdapter
from .earth_engine import EarthEngineAdapter
from .erpnext import ERPNextAdapter
from .brapi import BrAPIAdapter

INTEGRATION_REGISTRY: Dict[str, Type[IntegrationAdapter]] = {
    "ncbi": NCBIAdapter,
    "earth_engine": EarthEngineAdapter,
    "erpnext": ERPNextAdapter,
    "brapi": BrAPIAdapter,
}

def get_adapter(integration_id: str, config: dict) -> IntegrationAdapter:
    """Get an integration adapter instance."""
    adapter_class = INTEGRATION_REGISTRY.get(integration_id)
    if not adapter_class:
        raise ValueError(f"Unknown integration: {integration_id}")
    return adapter_class(IntegrationConfig(**config))
```

### 7.4 User Configuration UI

Users manage integrations through a settings page:

```typescript
// frontend/src/divisions/settings/pages/Integrations.tsx
export function IntegrationsPage() {
  const { data: integrations } = useQuery({
    queryKey: ['integrations'],
    queryFn: api.integrations.list,
  });
  
  return (
    <div className="space-y-6">
      <h1>Integrations</h1>
      <p>Connect external services to extend Bijmantra's capabilities.</p>
      
      {integrations?.map(integration => (
        <IntegrationCard
          key={integration.id}
          integration={integration}
          onConfigure={() => openConfigModal(integration)}
          onTest={() => testConnection(integration.id)}
        />
      ))}
    </div>
  );
}
```

---

## 8. Data Layer

### 8.1 Database Architecture

Single PostgreSQL instance with extensions and schema-per-division.

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL 15+                            │
├─────────────────────────────────────────────────────────────┤
│  Extensions:                                                 │
│  ├── PostGIS 3.3+      → Spatial data (locations, fields)   │
│  ├── pgvector          → AI embeddings, semantic search     │
│  ├── pg_trgm           → Fuzzy text search                  │
│  └── pg_cron           → Scheduled jobs (optional)          │
├─────────────────────────────────────────────────────────────┤
│  Schemas:                                                    │
│  ├── core              → Users, orgs, permissions, audit    │
│  ├── plant_sciences    → Programs, trials, germplasm, etc.  │
│  ├── seed_bank         → Vaults, accessions, conservation   │
│  ├── earth_systems     → Locations, climate, GIS layers     │
│  ├── commercial        → Traceability, licenses, seed lots  │
│  ├── integrations      → API keys, sync logs, external refs │
│  └── analytics         → Aggregates, reports, dashboards    │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Schema Design Principles

```sql
-- Every table follows these conventions:

-- 1. UUID primary keys (for distributed sync)
CREATE TABLE plant_sciences.programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 2. Organization scoping (multi-tenancy)
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    
    -- 3. Standard audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES core.users(id),
    updated_by UUID REFERENCES core.users(id),
    
    -- 4. Soft delete support
    deleted_at TIMESTAMPTZ,
    
    -- 5. Sync tracking (for offline)
    sync_version BIGINT NOT NULL DEFAULT 0,
    
    -- Business fields
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- ...
);

-- 3. Row-level security for multi-tenancy
ALTER TABLE plant_sciences.programs ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_isolation ON plant_sciences.programs
    USING (organization_id = current_setting('app.current_org_id')::UUID);
```

### 8.3 Core Schema

```sql
-- core.organizations
CREATE TABLE core.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- core.users
CREATE TABLE core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- core.organization_members (many-to-many with roles)
CREATE TABLE core.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    user_id UUID NOT NULL REFERENCES core.users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    permissions TEXT[] DEFAULT '{}',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- core.audit_log
CREATE TABLE core.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES core.organizations(id),
    user_id UUID REFERENCES core.users(id),
    action VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete'
    entity_type VARCHAR(100) NOT NULL,  -- 'program', 'trial', etc.
    entity_id UUID NOT NULL,
    changes JSONB,  -- What changed
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast audit queries
CREATE INDEX idx_audit_log_entity ON core.audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_org_time ON core.audit_log(organization_id, created_at DESC);
```

### 8.4 Spatial Data (PostGIS)

```sql
-- Locations with geometry
CREATE TABLE earth_systems.locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES core.organizations(id),
    name VARCHAR(255) NOT NULL,
    location_type VARCHAR(50),  -- 'field', 'station', 'office'
    
    -- PostGIS geometry
    coordinates GEOMETRY(POINT, 4326),  -- WGS84
    boundary GEOMETRY(POLYGON, 4326),   -- Field boundary
    
    -- Address
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(100),
    
    -- Metadata
    elevation_m DECIMAL(8,2),
    soil_type VARCHAR(100),
    climate_zone VARCHAR(50),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Spatial index
CREATE INDEX idx_locations_coords ON earth_systems.locations USING GIST(coordinates);
CREATE INDEX idx_locations_boundary ON earth_systems.locations USING GIST(boundary);
```

### 8.5 Vector Embeddings (pgvector)

```sql
-- For AI-powered semantic search
CREATE TABLE core.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    content_hash VARCHAR(64),  -- To detect changes
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(entity_type, entity_id)
);

-- Vector similarity index
CREATE INDEX idx_embeddings_vector ON core.embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Semantic search function
CREATE OR REPLACE FUNCTION search_similar(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE(entity_type VARCHAR, entity_id UUID, similarity FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.entity_type,
        e.entity_id,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM core.embeddings e
    WHERE 1 - (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

---

## 9. Offline & Sync

### 9.1 Offline-First Architecture

Bijmantra is designed for field use where connectivity is unreliable.

```
┌─────────────────────────────────────────────────────────────┐
│                    OFFLINE ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐         ┌─────────────┐                   │
│   │   BROWSER   │         │   SERVER    │                   │
│   │             │         │             │                   │
│   │ IndexedDB   │◄───────►│ PostgreSQL  │                   │
│   │ (Dexie.js)  │  Sync   │             │                   │
│   │             │         │             │                   │
│   │ Service     │         │ Sync API    │                   │
│   │ Worker      │         │             │                   │
│   └─────────────┘         └─────────────┘                   │
│                                                              │
│   Offline Queue → Sync on Reconnect → Conflict Resolution   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 IndexedDB Schema (Dexie.js)

```typescript
// frontend/src/framework/sync/db.ts
import Dexie, { Table } from 'dexie';

interface SyncableEntity {
  id: string;
  _syncVersion: number;
  _syncStatus: 'synced' | 'pending' | 'conflict';
  _localChanges?: object;
  _serverVersion?: number;
}

class BijmantraDB extends Dexie {
  // Cached data from server
  programs!: Table<Program & SyncableEntity>;
  trials!: Table<Trial & SyncableEntity>;
  studies!: Table<Study & SyncableEntity>;
  germplasm!: Table<Germplasm & SyncableEntity>;
  observations!: Table<Observation & SyncableEntity>;
  
  // Pending operations queue
  pendingSync!: Table<PendingSyncOperation>;
  
  // User preferences (never synced)
  userPrefs!: Table<UserPreference>;
  
  constructor() {
    super('bijmantra');
    
    this.version(1).stores({
      programs: 'id, organizationId, _syncStatus, updatedAt',
      trials: 'id, programId, organizationId, _syncStatus, updatedAt',
      studies: 'id, trialId, organizationId, _syncStatus, updatedAt',
      germplasm: 'id, organizationId, _syncStatus, updatedAt',
      observations: 'id, studyId, organizationId, _syncStatus, updatedAt',
      pendingSync: '++id, entityType, entityId, operation, createdAt',
      userPrefs: 'key',
    });
  }
}

export const db = new BijmantraDB();
```

### 9.3 Sync Strategy

```typescript
// frontend/src/framework/sync/strategy.ts
interface SyncConfig {
  // Entities to sync for offline use
  entities: {
    name: string;
    priority: number;  // Lower = sync first
    conflictResolution: 'server-wins' | 'client-wins' | 'manual';
    maxOfflineAge: number;  // Hours before requiring refresh
  }[];
  
  // When to sync
  triggers: ('online' | 'interval' | 'manual' | 'background')[];
  
  // Sync interval in minutes (if interval trigger enabled)
  intervalMinutes: number;
}

const defaultSyncConfig: SyncConfig = {
  entities: [
    { name: 'programs', priority: 1, conflictResolution: 'server-wins', maxOfflineAge: 168 },
    { name: 'trials', priority: 2, conflictResolution: 'server-wins', maxOfflineAge: 24 },
    { name: 'studies', priority: 3, conflictResolution: 'server-wins', maxOfflineAge: 24 },
    { name: 'germplasm', priority: 4, conflictResolution: 'server-wins', maxOfflineAge: 168 },
    { name: 'observations', priority: 5, conflictResolution: 'manual', maxOfflineAge: 1 },
  ],
  triggers: ['online', 'manual'],
  intervalMinutes: 30,
};
```

### 9.4 Sync Engine

```typescript
// frontend/src/framework/sync/engine.ts
class SyncEngine {
  private isOnline = navigator.onLine;
  private isSyncing = false;
  
  constructor(private config: SyncConfig) {
    // Listen for online/offline events
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }
  
  async sync(): Promise<SyncResult> {
    if (this.isSyncing || !this.isOnline) {
      return { success: false, reason: 'Already syncing or offline' };
    }
    
    this.isSyncing = true;
    
    try {
      // 1. Push pending changes to server
      await this.pushPendingChanges();
      
      // 2. Pull updates from server
      await this.pullServerChanges();
      
      // 3. Resolve any conflicts
      await this.resolveConflicts();
      
      return { success: true };
    } finally {
      this.isSyncing = false;
    }
  }
  
  private async pushPendingChanges(): Promise<void> {
    const pending = await db.pendingSync.toArray();
    
    for (const op of pending) {
      try {
        await this.pushOperation(op);
        await db.pendingSync.delete(op.id);
      } catch (error) {
        if (isConflictError(error)) {
          await this.markConflict(op);
        } else {
          throw error;
        }
      }
    }
  }
  
  private async pullServerChanges(): Promise<void> {
    for (const entity of this.config.entities.sort((a, b) => a.priority - b.priority)) {
      const lastSync = await this.getLastSyncTime(entity.name);
      const changes = await api.sync.getChanges(entity.name, lastSync);
      
      for (const change of changes) {
        await this.applyServerChange(entity.name, change);
      }
    }
  }
}

export const syncEngine = new SyncEngine(defaultSyncConfig);
```

### 9.5 Service Worker Caching

```typescript
// frontend/src/sw.ts (Workbox)
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, CacheFirst, NetworkFirst } from 'workbox-strategies';

// Precache app shell
precacheAndRoute(self.__WB_MANIFEST);

// API: Network first, fall back to cache
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    networkTimeoutSeconds: 10,
  })
);

// Static assets: Cache first
registerRoute(
  ({ request }) => request.destination === 'image' || 
                   request.destination === 'font',
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 7 * 24 * 60 * 60 }),
    ],
  })
);

// Division chunks: Stale while revalidate
registerRoute(
  ({ url }) => url.pathname.includes('/divisions/'),
  new StaleWhileRevalidate({
    cacheName: 'division-chunks',
  })
);
```

---

## 10. Security Model

### 10.1 Authentication

JWT-based authentication with refresh tokens.

```python
# backend/app/core/auth/jwt.py
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(hours=24)
        self.refresh_token_expire = timedelta(days=7)
    
    def create_access_token(self, user_id: str, org_id: str, permissions: list) -> str:
        expire = datetime.utcnow() + self.access_token_expire
        payload = {
            "sub": user_id,
            "org": org_id,
            "permissions": permissions,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + self.refresh_token_expire
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
```

### 10.2 Authorization (RBAC)

```python
# backend/app/core/auth/rbac.py
from functools import wraps
from fastapi import HTTPException, Depends
from typing import List

def require_permissions(*required: str):
    """Decorator to check permissions on endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            user_permissions = set(current_user.permissions)
            required_permissions = set(required)
            
            if not required_permissions.issubset(user_permissions):
                missing = required_permissions - user_permissions
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permissions: {missing}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@router.post("/programs")
@require_permissions("write:plant_sciences")
async def create_program(program: ProgramCreate, current_user: User = Depends(get_current_user)):
    pass
```

### 10.3 Multi-Tenancy Isolation

```python
# backend/app/core/database/context.py
from contextvars import ContextVar
from sqlalchemy.ext.asyncio import AsyncSession

# Current organization context
current_org_id: ContextVar[str] = ContextVar('current_org_id')

class TenantMiddleware:
    """Middleware to set organization context from JWT."""
    
    async def __call__(self, request, call_next):
        token = extract_token(request)
        if token:
            payload = decode_token(token)
            current_org_id.set(payload.get('org'))
            
            # Set PostgreSQL session variable for RLS
            async with get_db() as db:
                await db.execute(
                    f"SET app.current_org_id = '{payload.get('org')}'"
                )
        
        return await call_next(request)
```

### 10.4 API Security

```python
# backend/app/core/security/middleware.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

def configure_security(app: FastAPI):
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rate limiting
    app.state.limiter = limiter
    
    # Security headers
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
```

### 10.5 Data Protection

| Layer | Protection |
|-------|------------|
| Transport | HTTPS only (Caddy auto-TLS) |
| Storage | Encrypted at rest (PostgreSQL TDE or disk encryption) |
| Passwords | bcrypt hashing |
| Tokens | JWT with short expiry, refresh rotation |
| API Keys | Hashed storage, scoped permissions |
| Audit | All mutations logged with user, timestamp, changes |

---

## 11. Folder Structure

### 11.1 Complete Project Structure

```
bijmantra/
├── frontend/                          # React PWA
│   ├── public/
│   │   ├── manifest.json              # PWA manifest
│   │   └── icons/                     # App icons
│   ├── src/
│   │   ├── framework/                 # PARASHAKTI CORE
│   │   │   ├── shell/                 # App shell components
│   │   │   │   ├── Shell.tsx          # Main layout
│   │   │   │   ├── Sidebar.tsx        # Navigation sidebar
│   │   │   │   ├── Header.tsx         # Top header
│   │   │   │   └── index.ts
│   │   │   ├── registry/              # Division registry
│   │   │   │   ├── types.ts           # Division interfaces
│   │   │   │   ├── divisions.ts       # Division definitions
│   │   │   │   └── index.ts
│   │   │   ├── auth/                  # Authentication
│   │   │   │   ├── AuthProvider.tsx
│   │   │   │   ├── useAuth.ts
│   │   │   │   └── guards.tsx
│   │   │   ├── sync/                  # Offline sync
│   │   │   │   ├── db.ts              # IndexedDB (Dexie)
│   │   │   │   ├── engine.ts          # Sync engine
│   │   │   │   └── hooks.ts
│   │   │   ├── events/                # Event bus client
│   │   │   │   └── eventBus.ts
│   │   │   ├── compute/               # WASM compute
│   │   │   │   └── wasm.ts
│   │   │   ├── features/              # Feature flags
│   │   │   │   └── flags.ts
│   │   │   └── hooks/                 # Shared hooks
│   │   │       ├── usePermissions.ts
│   │   │       └── useFeatureFlag.ts
│   │   │
│   │   ├── divisions/                 # DIVISION MODULES
│   │   │   ├── plant-sciences/        # Division 1
│   │   │   │   ├── index.ts           # Entry point
│   │   │   │   ├── routes.tsx         # Division routes
│   │   │   │   ├── pages/
│   │   │   │   │   ├── Dashboard.tsx
│   │   │   │   │   ├── breeding/
│   │   │   │   │   ├── genomics/
│   │   │   │   │   ├── molecular/
│   │   │   │   │   ├── crop-sciences/
│   │   │   │   │   └── soil/
│   │   │   │   ├── components/
│   │   │   │   ├── hooks/
│   │   │   │   ├── api/
│   │   │   │   └── types/
│   │   │   │
│   │   │   ├── seed-bank/             # Division 2
│   │   │   │   ├── index.ts
│   │   │   │   ├── routes.tsx
│   │   │   │   └── pages/
│   │   │   │
│   │   │   ├── earth-systems/         # Division 3
│   │   │   ├── sun-earth-systems/     # Division 4
│   │   │   ├── sensor-networks/       # Division 5
│   │   │   ├── commercial/            # Division 6
│   │   │   ├── space-research/        # Division 7
│   │   │   ├── integrations/          # Division 8
│   │   │   └── knowledge/             # Division 9
│   │   │
│   │   ├── shared/                    # SHARED COMPONENTS
│   │   │   ├── components/
│   │   │   │   ├── ui/                # shadcn/ui components
│   │   │   │   ├── data-table/
│   │   │   │   ├── forms/
│   │   │   │   └── charts/
│   │   │   ├── hooks/
│   │   │   └── utils/
│   │   │
│   │   ├── App.tsx                    # Root component
│   │   ├── main.tsx                   # Entry point
│   │   └── sw.ts                      # Service worker
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── backend/                           # FastAPI Server
│   ├── app/
│   │   ├── core/                      # FRAMEWORK CORE
│   │   │   ├── auth/
│   │   │   │   ├── jwt.py
│   │   │   │   ├── rbac.py
│   │   │   │   └── dependencies.py
│   │   │   ├── database/
│   │   │   │   ├── session.py
│   │   │   │   ├── base.py
│   │   │   │   └── context.py
│   │   │   ├── events/
│   │   │   │   └── bus.py
│   │   │   ├── compute/
│   │   │   │   └── dispatcher.py
│   │   │   ├── queue/
│   │   │   │   └── tasks.py
│   │   │   ├── storage/
│   │   │   │   └── minio.py
│   │   │   ├── features/
│   │   │   │   └── flags.py
│   │   │   └── config.py
│   │   │
│   │   ├── modules/                   # DIVISION BACKENDS
│   │   │   ├── plant_sciences/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py          # Mounts all sub-routers
│   │   │   │   ├── breeding/
│   │   │   │   │   ├── routes.py
│   │   │   │   │   ├── models.py
│   │   │   │   │   ├── schemas.py
│   │   │   │   │   ├── services.py
│   │   │   │   │   └── crud.py
│   │   │   │   ├── genomics/
│   │   │   │   ├── molecular/
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── seed_bank/
│   │   │   ├── earth_systems/
│   │   │   ├── commercial/
│   │   │   └── ...
│   │   │
│   │   ├── integrations/              # EXTERNAL ADAPTERS
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── ncbi.py
│   │   │   ├── earth_engine.py
│   │   │   ├── erpnext.py
│   │   │   └── brapi.py
│   │   │
│   │   ├── api/                       # API ROUTES
│   │   │   ├── v1/                    # API version 1
│   │   │   │   └── router.py
│   │   │   └── deps.py                # Shared dependencies
│   │   │
│   │   └── main.py                    # FastAPI app
│   │
│   ├── alembic/                       # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   ├── requirements.txt
│   └── Containerfile
│
├── compute/                           # COMPUTE ENGINES
│   ├── rust/                          # Rust/WASM modules
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── genomics/
│   │   │   │   ├── grm.rs
│   │   │   │   ├── ld.rs
│   │   │   │   └── pca.rs
│   │   │   └── wasm/
│   │   ├── Cargo.toml
│   │   └── README.md
│   │
│   └── fortran/                       # Fortran libraries
│       ├── src/
│       │   ├── blup_solver.f90
│       │   ├── reml_engine.f90
│       │   └── kinship.f90
│       ├── CMakeLists.txt
│       └── README.md
│
├── docs/                              # DOCUMENTATION
│   ├── framework/
│   │   └── PARASHAKTI_SPECIFICATION.md
│   ├── divisions/
│   ├── api/
│   └── deployment/
│
├── docker/                            # Container configs
│   └── postgres/
│       └── init-extensions.sql
│
├── compose.yaml                       # Podman/Docker compose
├── Caddyfile                          # Reverse proxy
├── Makefile                           # Dev commands
└── README.md
```

---

## 12. Migration Path

### 12.1 Overview

Migrate incrementally from current structure to Parashakti framework without breaking existing functionality.

```
Current State                    Target State
─────────────                    ────────────
frontend/src/pages/      →       frontend/src/divisions/plant-sciences/pages/
frontend/src/components/ →       frontend/src/shared/components/ + division-specific
backend/app/api/v2/      →       backend/app/modules/plant_sciences/
```

### 12.2 Phase 1: Framework Foundation ✅ COMPLETE

**Goal:** Create framework structure without moving existing code.

```bash
# Create framework directories
mkdir -p frontend/src/framework/{shell,registry,auth,sync,events,compute,features,hooks}
mkdir -p backend/app/core/{auth,database,events,compute,queue,storage,features}
mkdir -p backend/app/integrations
```

**Tasks:**
- [x] Create Division Registry types and initial registration
- [x] Create Shell components (can wrap existing layout initially)
- [x] Create feature flag system
- [x] Create event bus (backend)
- [x] Update main.py to use modular router mounting

### 12.3 Phase 2: Division Structure ✅ COMPLETE

**Goal:** Create division folders and move Plant Sciences code.

```bash
# Create division structure
mkdir -p frontend/src/divisions/plant-sciences/{pages,components,hooks,api,types}
mkdir -p backend/app/modules/plant_sciences/{breeding,genomics,molecular}
```

**Tasks:**
- [x] Create plant-sciences division entry point
- [x] Move existing pages into plant-sciences/pages/
- [x] Update imports (can use path aliases)
- [x] Register plant-sciences in Division Registry
- [x] Update routing to use lazy loading

### 12.4 Phase 3: Core Services ✅ COMPLETE

**Goal:** Implement shared services.

**Tasks:**
- [x] Implement event bus with basic events
- [x] Implement permission checking middleware
- [x] Implement feature flag checking
- [x] Create integration adapter base class
- [x] Set up first integration (e.g., BrAPI export)

### 12.5 Phase 4: Offline Sync ✅ COMPLETE

**Goal:** Implement offline-first data layer.

**Tasks:**
- [x] Set up Dexie.js with schema
- [x] Implement sync engine
- [x] Add pending operations queue
- [x] Implement conflict resolution UI
- [x] Update service worker caching

### 12.6 Phase 5: New Division ✅ COMPLETE

**Goal:** Add first new division using framework.

**Tasks:**
- [x] Create Seed Bank division structure
- [x] Implement basic pages
- [x] Add to Division Registry
- [x] Test lazy loading
- [x] Test feature flag toggling

### 12.7 Migration Checklist

```markdown
## Framework Core
- [x] Division Registry implemented
- [x] Shell components created
- [x] Feature flags working
- [x] Event bus operational
- [x] Permission system integrated
- [x] Workspace Gateway implemented

## Plant Sciences Division
- [x] Pages moved to division folder
- [x] Components organized
- [x] Routes using lazy loading
- [x] API calls using division-specific client
- [x] Division registered and accessible

## Backend Modules
- [x] Module structure created
- [x] Routers mounted modularly
- [x] Schemas organized by module
- [x] Services separated by domain

## Integrations
- [x] Base adapter interface defined
- [x] Multiple adapters implemented (BrAPI, NCBI, etc.)
- [x] Settings UI for API keys
- [x] Connection testing working

## Offline/Sync
- [x] IndexedDB schema defined
- [x] Sync engine implemented
- [x] Pending queue working
- [x] Conflict resolution UI
- [x] Service worker updated

## Additional Modules (v1.0.0-beta.1)
- [x] Seed Bank module (production ready)
- [x] Environment module (merged Earth + Sun-Earth)
- [x] Seed Operations module (renamed from Commercial)
- [x] Knowledge module (trimmed to 5 pages)
- [x] Settings & Admin module
- [x] BrAPI v2.1 100% coverage (201 endpoints)
```

---

## 13. API Contracts

### 13.1 API Versioning

All APIs are versioned to ensure backward compatibility.

```
/api/v1/...    # Current stable API
/api/v2/...    # Future breaking changes
```

### 13.2 Standard Response Format

All API responses follow a consistent structure.

```typescript
// Success response
interface ApiResponse<T> {
  success: true;
  data: T;
  metadata?: {
    pagination?: {
      page: number;
      pageSize: number;
      totalCount: number;
      totalPages: number;
    };
    timing?: {
      durationMs: number;
    };
  };
}

// Error response
interface ApiError {
  success: false;
  error: {
    code: string;        // Machine-readable: "VALIDATION_ERROR"
    message: string;     // Human-readable: "Invalid email format"
    details?: object;    // Additional context
    field?: string;      // For validation errors
  };
}
```

### 13.3 Standard Endpoints per Entity

Each entity follows RESTful conventions:

```
GET    /api/v1/{division}/{entity}           # List with pagination
GET    /api/v1/{division}/{entity}/{id}      # Get single
POST   /api/v1/{division}/{entity}           # Create
PUT    /api/v1/{division}/{entity}/{id}      # Full update
PATCH  /api/v1/{division}/{entity}/{id}      # Partial update
DELETE /api/v1/{division}/{entity}/{id}      # Soft delete
```

**Example:**
```
GET    /api/v1/plant-sciences/programs
GET    /api/v1/plant-sciences/programs/123
POST   /api/v1/plant-sciences/programs
PUT    /api/v1/plant-sciences/programs/123
DELETE /api/v1/plant-sciences/programs/123
```

### 13.4 Query Parameters

Standard query parameters for list endpoints:

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (0-indexed) |
| `pageSize` | int | Items per page (default: 20, max: 100) |
| `sort` | string | Sort field (prefix with `-` for descending) |
| `search` | string | Full-text search query |
| `filter[field]` | string | Filter by field value |
| `include` | string | Comma-separated related entities to include |

**Example:**
```
GET /api/v1/plant-sciences/trials?page=0&pageSize=20&sort=-createdAt&filter[status]=active&include=studies,location
```

### 13.5 Sync API

Special endpoints for offline sync:

```
# Get changes since timestamp
GET /api/v1/sync/{entity}?since={timestamp}&limit={n}

Response:
{
  "success": true,
  "data": {
    "changes": [
      { "id": "...", "action": "create", "data": {...}, "timestamp": "..." },
      { "id": "...", "action": "update", "data": {...}, "timestamp": "..." },
      { "id": "...", "action": "delete", "timestamp": "..." }
    ],
    "hasMore": false,
    "syncToken": "..."
  }
}

# Push local changes
POST /api/v1/sync/push
Body:
{
  "changes": [
    { "entity": "observations", "action": "create", "data": {...}, "localId": "..." },
    { "entity": "observations", "action": "update", "id": "...", "data": {...} }
  ]
}

Response:
{
  "success": true,
  "data": {
    "results": [
      { "localId": "...", "serverId": "...", "status": "created" },
      { "id": "...", "status": "updated" },
      { "id": "...", "status": "conflict", "serverVersion": {...} }
    ]
  }
}
```

### 13.6 Event Webhook Format

For external integrations subscribing to events:

```typescript
interface WebhookPayload {
  event: string;           // "germplasm.created"
  timestamp: string;       // ISO 8601
  organizationId: string;
  data: {
    entityType: string;
    entityId: string;
    action: 'create' | 'update' | 'delete';
    changes?: object;      // For updates
    entity?: object;       // Full entity for creates
  };
  signature: string;       // HMAC signature for verification
}
```

---

## Appendix A: Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend Framework | React 18 | Ecosystem, hiring, component libraries |
| Build Tool | Vite | Fast HMR, native ESM, good DX |
| Styling | Tailwind + shadcn/ui | Utility-first, accessible components |
| State (Server) | TanStack Query | Caching, sync, offline support |
| State (Client) | Zustand | Simple, lightweight, TypeScript |
| Backend Framework | FastAPI | Async, auto-docs, Pydantic validation |
| Database | PostgreSQL | Reliability, extensions, SQL standard |
| Spatial | PostGIS | Industry standard for GIS |
| Vector Search | pgvector | Native PostgreSQL, no extra service |
| Cache | Redis | Fast, pub/sub for events |
| Object Storage | MinIO | S3-compatible, self-hosted |
| Compute (Fast) | Rust | Memory safety, WASM target |
| Compute (Stats) | Fortran | Proven algorithms, LAPACK |
| Containers | Podman | Rootless, Docker-compatible |
| Reverse Proxy | Caddy | Auto HTTPS, simple config |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| Division | A self-contained feature domain (e.g., Plant Sciences, Seed Bank) |
| Shell | The always-loaded app frame (navigation, header, auth) |
| Adapter | A plugin that connects to an external service |
| Sync Engine | System for offline data synchronization |
| Event Bus | Pub/sub system for inter-division communication |
| Feature Flag | Toggle to enable/disable features per deployment |
| Compute Engine | Specialized runtime for heavy calculations |

---

## Appendix C: References

- [BrAPI Specification](https://brapi.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)
- [PostGIS Documentation](https://postgis.net/documentation)
- [pgvector](https://github.com/pgvector/pgvector)
- [Dexie.js](https://dexie.org)
- [Workbox](https://developer.chrome.com/docs/workbox)

---

*Document Version: 1.0.0-beta.1*
*Last Updated: 2026-01-01*
*Author: Bijmantra Development Team*
