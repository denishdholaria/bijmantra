# Production Readiness - Sandboxed Demo Architecture

> **Priority**: P0 - CRITICAL  
> **Created**: December 22, 2025  
> **Status**: IN PROGRESS

---

## Architecture: Sandboxed Demo via Organization Isolation

Demo data is completely isolated in a "Demo Organization" - no mixing with production data.

```
┌─────────────────────────────────────────────────────────┐
│                    BIJMANTRA DATABASE                    │
├─────────────────────────────────────────────────────────┤
│  Organization: "Demo Organization" (id=1)               │
│  ├── Demo User: demo@bijmantra.org                      │
│  ├── Demo Germplasm (8 entries)                         │
│  ├── Demo Trials, Studies, etc.                         │
│  └── Completely isolated from production                │
├─────────────────────────────────────────────────────────┤
│  Organization: "IRRI" (id=2)                            │
│  ├── Real users, real data                              │
│  └── Never sees demo data                               │
├─────────────────────────────────────────────────────────┤
│  Organization: "CIMMYT" (id=3)                          │
│  └── ...                                                │
└─────────────────────────────────────────────────────────┘
```

### Benefits

1. **Complete Isolation** - Demo data never mixes with production
2. **AI-Safe** - Filter by `organization_id != demo_org_id` for analytics
3. **Same Codebase** - No special "demo mode" code paths
4. **Real Experience** - Demo users see the real app, not a fake version
5. **Easy Reset** - Can reset demo org without affecting others

---

## Implementation Status

### Completed ✅

| Task | File | Description |
|------|------|-------------|
| Config settings | `backend/app/core/config.py` | DEMO_ORG_NAME, DEMO_USER_*, SEED_DEMO_DATA |
| Seeder framework | `backend/app/db/seeders/` | BaseSeeder, registry, CLI |
| Demo germplasm seeder | `demo_germplasm.py` | 8 rice/wheat/maize entries |
| Demo BrAPI seeder | `demo_brapi.py` | Programs, trials, studies, etc. |
| Seeder CLI | `backend/app/db/seed.py` | `python -m app.db.seed` |
| Germplasm models | `backend/app/models/germplasm.py` | 8 BrAPI models |
| Germplasm migration | `009_germplasm_tables.py` | Database tables |
| Germplasm endpoint | `backend/app/api/brapi/germplasm.py` | Database-only (no fallback) |
| Frontend hook | `frontend/src/hooks/useDemoMode.ts` | Simplified for sandbox approach |
| Makefile commands | `Makefile` | db-seed, db-seed-clear, etc. |
| Env example | `.env.example` | Updated configuration |

### Remaining ⏳

| Task | Priority | Description |
|------|----------|-------------|
| Migrate remaining BrAPI endpoints | P1 | Remove `_store` dicts from 9 files |
| Create demo user seeder | P1 | Seed demo@bijmantra.org user |
| Update docker-compose | P2 | Dev/prod separation |
| Update CI/CD | P2 | Auto-seed demo org in dev |

---

## Usage

### Seed Demo Data

```bash
# Seed demo data into Demo Organization
make db-seed

# Or manually:
cd backend
python -m app.db.seed --env=dev
```

### Demo Login

```
Email: demo@bijmantra.org
Password: demo123
```

Demo users are automatically placed in "Demo Organization" and only see demo data.

### Production Deployment

```bash
# Production: No seeding, empty database
SEED_DEMO_DATA=false
ENVIRONMENT=production

# Run migrations only
make db-migrate
```

---

## Files Requiring Migration

BrAPI endpoints still using in-memory `_store` dicts:

| File | Status | Notes |
|------|--------|-------|
| `germplasm.py` | ✅ Done | Database-only |
| `crosses.py` | ⏳ TODO | Needs Cross model |
| `events.py` | ⏳ TODO | Needs Event model |
| `images.py` | ⏳ TODO | Needs Image model |
| `observations.py` | ⏳ TODO | Needs Observation model |
| `observationunits.py` | ⏳ TODO | Needs ObservationUnit model |
| `samples.py` | ⏳ TODO | Needs Sample model |
| `seedlots.py` | ⏳ TODO | Uses Seedlot model (exists) |
| `traits.py` | ⏳ TODO | Needs Trait model |
| `variables.py` | ⏳ TODO | Needs Variable model |

---

## Analytics Filtering

To exclude demo data from analytics/AI:

```python
# Python
from app.models.core import Organization

demo_org = db.query(Organization).filter(
    Organization.name == "Demo Organization"
).first()

# Exclude demo data
real_data = db.query(Germplasm).filter(
    Germplasm.organization_id != demo_org.id
).all()
```

```sql
-- SQL
SELECT * FROM germplasm 
WHERE organization_id != (
    SELECT id FROM organizations WHERE name = 'Demo Organization'
);
```

---

## References

- [Multi-Tenant Architecture](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [12-Factor App - Config](https://12factor.net/config)
- [Database Seeding Best Practices](https://www.prisma.io/docs/guides/database/seed-database)
