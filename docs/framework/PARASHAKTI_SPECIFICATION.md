# Parashakti Framework — Technical Specification

> **परा-शक्ति** (Parā-Śakti): The supreme energy that powers all divisions
>
> Version: 1.0.0
> Created: 2025-12-05
> Status: Draft

---

## Executive Summary

Parashakti is the foundational framework for Bijmantra — a modular, extensible platform for agricultural science, plant breeding, and future space-based research. This document defines the architecture, principles, and implementation guidelines.

### Design Philosophy

1. **Modular Monolith** — Single deployable unit with clear internal boundaries
2. **Division-Based** — Self-contained feature domains that can evolve independently
3. **Integration-First** — Connect to external systems rather than rebuild them
4. **Multi-Engine Compute** — Right tool for the job (Python, Rust, Fortran)
5. **Offline-Capable** — Field-ready with robust sync
6. **Future-Proof** — Can split into microservices when scale demands

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Layer Definitions](#2-layer-definitions)
3. [Division System](#3-division-system)
4. [Core Services](#4-core-services)
5. [Compute Engines](#5-compute-engines)
6. [Integration Hub](#6-integration-hub)
7. [Data Layer](#7-data-layer)
8. [Offline & Sync](#8-offline--sync)
9. [Security Model](#9-security-model)
10. [Folder Structure](#10-folder-structure)
11. [Migration Path](#11-migration-path)
12. [API Contracts](#12-api-contracts)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PARASHAKTI FRAMEWORK                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      SHELL LAYER                               │ │
│  │   Navigation │ Authentication │ Theme │ Notifications │ Search │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────┼───────────────────────────────┐   │
│  │               DIVISION LAYER (Lazy Loaded)                    │   │
│  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐│   │
│  │  │Plant  │ │Seed   │ │Earth  │ │Sun-   │ │Commer-│ │Know-  ││   │
│  │  │Science│ │Bank   │ │Systems│ │Earth  │ │cial   │ │ledge  ││   │
│  │  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘│   │
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
| Clear Boundaries | Each division has isolated code, routes, and schemas |
| Lazy Loading | Divisions load only when accessed |
| Feature Flags | Divisions can be enabled/disabled per deployment |
| Event-Driven | Divisions communicate via events, not direct calls |
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

### 2.2 Division Layer

Self-contained feature domains loaded on demand.

**Characteristics:**
- Each division is a separate code-split chunk
- Has its own routes, pages, components, hooks
- Registers with the framework via Division Registry
- Can declare dependencies on other divisions
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

## 3. Division System

### 3.1 Division Registry

Central registry that defines all available divisions.

```typescript
// frontend/src/framework/registry/types.ts
export interface Division {
  // Identity
  id: string;                    // Unique identifier: 'plant-sciences'
  name: string;                  // Display name: 'Plant Sciences'
  description: string;           // Short description
  icon: string;                  // Lucide icon name
  
  // Routing
  route: string;                 // Base route: '/plant-sciences'
  loadComponent: () => Promise<{ default: React.ComponentType }>;
  
  // Access Control
  requiredPermissions: string[]; // ['read:breeding', 'write:trials']
  featureFlag?: string;          // Optional feature flag
  
  // Metadata
  status: 'active' | 'beta' | 'planned' | 'visionary';
  version: string;
  dependencies?: string[];       // Other division IDs this depends on
  
  // Subsections (for navigation)
  sections?: DivisionSection[];
}

export interface DivisionSection {
  id: string;
  name: string;
  route: string;
  icon?: string;
}
```

### 3.2 Division Registration

```typescript
// frontend/src/framework/registry/divisions.ts
import { Division } from './types';

export const divisions: Division[] = [
  {
    id: 'plant-sciences',
    name: 'Plant Sciences',
    description: 'Breeding operations, genomics, and crop research',
    icon: 'Seedling',
    route: '/plant-sciences',
    loadComponent: () => import('@/divisions/plant-sciences'),
    requiredPermissions: ['read:plant_sciences'],
    status: 'active',
    version: '1.0.0',
    sections: [
      { id: 'breeding', name: 'Breeding Operations', route: '/breeding', icon: 'FlaskConical' },
      { id: 'genomics', name: 'Genetics & Genomics', route: '/genomics', icon: 'Dna' },
      { id: 'molecular', name: 'Molecular Biology', route: '/molecular', icon: 'Microscope' },
      { id: 'crop-sciences', name: 'Crop Sciences', route: '/crop-sciences', icon: 'Wheat' },
      { id: 'soil', name: 'Soil & Environment', route: '/soil', icon: 'Mountain' },
    ],
  },
  {
    id: 'seed-bank',
    name: 'Seed Bank',
    description: 'Genetic resources and germplasm preservation',
    icon: 'Warehouse',
    route: '/seed-bank',
    loadComponent: () => import('@/divisions/seed-bank'),
    requiredPermissions: ['read:seed_bank'],
    status: 'planned',
    version: '0.1.0',
  },
  {
    id: 'earth-systems',
    name: 'Earth Systems',
    description: 'Climate, weather, and environmental monitoring',
    icon: 'Globe',
    route: '/earth-systems',
    loadComponent: () => import('@/divisions/earth-systems'),
    requiredPermissions: ['read:earth_systems'],
    featureFlag: 'EARTH_SYSTEMS_ENABLED',
    status: 'beta',
    version: '0.5.0',
  },
  // ... more divisions
];
```

### 3.3 Division Structure (Frontend)

Each division follows a consistent internal structure:

```
frontend/src/divisions/plant-sciences/
├── index.ts                 # Division entry point & routes
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
├── components/              # Division-specific components
├── hooks/                   # Division-specific hooks
├── api/                     # API client functions
├── store/                   # Zustand stores (if needed)
└── types/                   # TypeScript types
```

### 3.4 Division Structure (Backend)

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

### 3.5 Division Communication

Divisions communicate via the Event Bus, never by direct imports.

```python
# Division A publishes an event
await event_bus.publish("germplasm.created", {
    "germplasm_id": "G001",
    "species": "Zea mays",
    "organization_id": "org_123"
})

# Division B subscribes and reacts
@event_bus.on("germplasm.created")
async def handle_germplasm_created(payload: dict):
    # Create corresponding seed bank record
    await create_conservation_record(payload["germplasm_id"])
```

---

## 4. Core Services

### 4.1 Event Bus

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

### 4.2 Feature Flags

Control division and feature availability.

```python
# backend/app/core/features/flags.py
from enum import Enum
from typing import Optional

class FeatureFlag(str, Enum):
    EARTH_SYSTEMS_ENABLED = "EARTH_SYSTEMS_ENABLED"
    SUN_EARTH_SYSTEMS_ENABLED = "SUN_EARTH_SYSTEMS_ENABLED"
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

### 4.3 Permission System

Role-based access control with division-level granularity.

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
    
    # Earth Systems
    READ_EARTH_SYSTEMS = "read:earth_systems"
    WRITE_EARTH_SYSTEMS = "write:earth_systems"
    
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
        Permission.READ_EARTH_SYSTEMS,
    ],
    "admin": list(Permission),  # All permissions
}
```

### 4.4 Background Task Queue

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

## 5. Compute Engines

### 5.1 Multi-Engine Architecture

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

### 5.2 Engine Selection Rules

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

### 5.3 Compute Interface

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

### 5.4 WASM for Browser

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

## 6. Integration Hub

### 6.1 Adapter Interface

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

### 6.2 Example Integrations

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

### 6.3 Integration Registry

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

### 6.4 User Configuration UI

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

## 7. Data Layer

### 7.1 Database Architecture

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

### 7.2 Schema Design Principles

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

### 7.3 Core Schema

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

### 7.4 Spatial Data (PostGIS)

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

### 7.5 Vector Embeddings (pgvector)

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

## 8. Offline & Sync

### 8.1 Offline-First Architecture

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

### 8.2 IndexedDB Schema (Dexie.js)

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

### 8.3 Sync Strategy

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

### 8.4 Sync Engine

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

### 8.5 Service Worker Caching

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

## 9. Security Model

### 9.1 Authentication

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

### 9.2 Authorization (RBAC)

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

### 9.3 Multi-Tenancy Isolation

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

### 9.4 API Security

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

### 9.5 Data Protection

| Layer | Protection |
|-------|------------|
| Transport | HTTPS only (Caddy auto-TLS) |
| Storage | Encrypted at rest (PostgreSQL TDE or disk encryption) |
| Passwords | bcrypt hashing |
| Tokens | JWT with short expiry, refresh rotation |
| API Keys | Hashed storage, scoped permissions |
| Audit | All mutations logged with user, timestamp, changes |

---

## 10. Folder Structure

### 10.1 Complete Project Structure

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

## 11. Migration Path

### 11.1 Overview

Migrate incrementally from current structure to Parashakti framework without breaking existing functionality.

```
Current State                    Target State
─────────────                    ────────────
frontend/src/pages/      →       frontend/src/divisions/plant-sciences/pages/
frontend/src/components/ →       frontend/src/shared/components/ + division-specific
backend/app/api/v2/      →       backend/app/modules/plant_sciences/
```

### 11.2 Phase 1: Framework Foundation (Week 1-2)

**Goal:** Create framework structure without moving existing code.

```bash
# Create framework directories
mkdir -p frontend/src/framework/{shell,registry,auth,sync,events,compute,features,hooks}
mkdir -p backend/app/core/{auth,database,events,compute,queue,storage,features}
mkdir -p backend/app/integrations
```

**Tasks:**
- [ ] Create Division Registry types and initial registration
- [ ] Create Shell components (can wrap existing layout initially)
- [ ] Create feature flag system
- [ ] Create event bus (backend)
- [ ] Update main.py to use modular router mounting

### 11.3 Phase 2: Division Structure (Week 3-4)

**Goal:** Create division folders and move Plant Sciences code.

```bash
# Create division structure
mkdir -p frontend/src/divisions/plant-sciences/{pages,components,hooks,api,types}
mkdir -p backend/app/modules/plant_sciences/{breeding,genomics,molecular}
```

**Tasks:**
- [ ] Create plant-sciences division entry point
- [ ] Move existing pages into plant-sciences/pages/
- [ ] Update imports (can use path aliases)
- [ ] Register plant-sciences in Division Registry
- [ ] Update routing to use lazy loading

### 11.4 Phase 3: Core Services (Week 5-6)

**Goal:** Implement shared services.

**Tasks:**
- [ ] Implement event bus with basic events
- [ ] Implement permission checking middleware
- [ ] Implement feature flag checking
- [ ] Create integration adapter base class
- [ ] Set up first integration (e.g., BrAPI export)

### 11.5 Phase 4: Offline Sync (Week 7-8)

**Goal:** Implement offline-first data layer.

**Tasks:**
- [ ] Set up Dexie.js with schema
- [ ] Implement sync engine
- [ ] Add pending operations queue
- [ ] Implement conflict resolution UI
- [ ] Update service worker caching

### 11.6 Phase 5: New Division (Week 9+)

**Goal:** Add first new division using framework.

**Tasks:**
- [ ] Create Seed Bank division structure
- [ ] Implement basic pages
- [ ] Add to Division Registry
- [ ] Test lazy loading
- [ ] Test feature flag toggling

### 11.7 Migration Checklist

```markdown
## Framework Core
- [ ] Division Registry implemented
- [ ] Shell components created
- [ ] Feature flags working
- [ ] Event bus operational
- [ ] Permission system integrated

## Plant Sciences Division
- [ ] Pages moved to division folder
- [ ] Components organized
- [ ] Routes using lazy loading
- [ ] API calls using division-specific client
- [ ] Division registered and accessible

## Backend Modules
- [ ] Module structure created
- [ ] Routers mounted modularly
- [ ] Schemas organized by module
- [ ] Services separated by domain

## Integrations
- [ ] Base adapter interface defined
- [ ] At least one adapter implemented
- [ ] Settings UI for API keys
- [ ] Connection testing working

## Offline/Sync
- [ ] IndexedDB schema defined
- [ ] Sync engine implemented
- [ ] Pending queue working
- [ ] Conflict resolution UI
- [ ] Service worker updated
```

---

## 12. API Contracts

### 12.1 API Versioning

All APIs are versioned to ensure backward compatibility.

```
/api/v1/...    # Current stable API
/api/v2/...    # Future breaking changes
```

### 12.2 Standard Response Format

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

### 12.3 Standard Endpoints per Entity

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

### 12.4 Query Parameters

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

### 12.5 Sync API

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

### 12.6 Event Webhook Format

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

*Document Version: 1.0.0*
*Last Updated: 2025-12-05*
*Author: Bijmantra Development Team*
