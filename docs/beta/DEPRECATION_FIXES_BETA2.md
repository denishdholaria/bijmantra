# Deprecation Fixes for v1.0.0-beta.2

**Created:** January 1, 2026  
**Updated:** January 1, 2026  
**Purpose:** Track Pydantic V2 and Python 3.12+ deprecation warnings for systematic fix

---

## Summary

During beta testing (Session 43), pytest revealed ~90 deprecation warnings. All deprecations have been fixed.

## Status: ✅ COMPLETE

### 1. Pydantic `class Config:` → `model_config = ConfigDict(...)` 

**Status:** ✅ COMPLETE (all ~70 classes fixed)

**Pattern applied:**
```python
# OLD (deprecated)
class MyModel(BaseModel):
    class Config:
        from_attributes = True

# NEW (Pydantic V2)
from pydantic import ConfigDict
class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

### 2. `datetime.utcnow()` → `datetime.now(timezone.utc)` 

**Status:** ✅ COMPLETE

#### Runtime Code: ✅ COMPLETE
All runtime code (API endpoints, services, seeders) has been fixed.

**Pattern applied:**
```python
# OLD (deprecated in Python 3.12+)
from datetime import datetime
datetime.utcnow()

# NEW
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

#### SQLAlchemy Model Defaults: ✅ COMPLETE
All model defaults have been fixed using the lambda pattern.

**Pattern applied:**
```python
# OLD (deprecated)
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# NEW
created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

**Files fixed:**
- `backend/app/models/base.py` (2 occurrences)
- `backend/app/models/field_operations.py` (~13 occurrences)
- `backend/app/models/security_audit.py` (~4 occurrences)
- `backend/app/models/stress_resistance.py` (~10 occurrences)
- `backend/app/models/collaboration.py` (~4 occurrences)
- `backend/app/models/data_management.py` (~17 occurrences)

---

## Completed Files (Runtime Code)

### API Endpoints Fixed
| File | Occurrences Fixed |
|------|-------------------|
| `backend/app/api/brapi/vendor.py` | 4 |
| `backend/app/api/brapi/observations.py` | 1 |
| `backend/app/api/v2/reports.py` | 8 |
| `backend/app/api/v2/insights.py` | 3 |
| `backend/app/api/v2/rls.py` | 1 |
| `backend/app/api/v2/climate.py` | 3 |
| `backend/app/api/v2/collaboration.py` | 2 |
| `backend/app/api/v2/data_validation.py` | 1 |
| `backend/app/api/v2/chat.py` | 1 |
| `backend/app/api/v2/field_book.py` | 4 |
| `backend/app/api/v2/backup.py` | 2 |
| `backend/app/api/v2/data_sync.py` | 7 |
| `backend/app/api/v2/crop_health.py` | 5 |
| `backend/app/api/v2/team_management.py` | 5 |
| `backend/app/api/v2/warehouse.py` | 7 |
| `backend/app/api/v2/core/lists.py` | 4 |
| `backend/app/api/v2/audit.py` | 1 |
| `backend/app/api/v2/collaboration_hub.py` | 15 |
| `backend/app/api/v2/security_audit.py` | 1 |
| `backend/app/api/v2/prahari.py` | 3 |
| `backend/app/api/v2/profile.py` | 4 |
| `backend/app/api/v2/germplasm_collection.py` | 2 |
| `backend/app/api/v2/weather.py` | 5 |
| `backend/app/api/v2/activity.py` | 3 |

### Services Fixed
| File | Occurrences Fixed |
|------|-------------------|
| `backend/app/services/prahari/threat_analyzer.py` | 5 |
| `backend/app/services/prahari/responder.py` | 3 |
| `backend/app/services/prahari/observer.py` | 4 |

### Core Modules Fixed
| File | Occurrences Fixed |
|------|-------------------|
| `backend/app/core/events.py` | 1 |
| `backend/app/core/meilisearch.py` | 2 |
| `backend/app/core/security.py` | 2 |
| `backend/app/core/signature.py` | 1 |
| `backend/app/core/socketio.py` | 6 |

### Seeders Fixed
| File | Occurrences Fixed |
|------|-------------------|
| `backend/app/db/seeders/demo_data_management.py` | 2 |
| `backend/app/db/seeders/demo_user_management.py` | 4 |
| `backend/app/db/seeders/demo_collaboration.py` | 15 |
| `backend/app/db/seeders/demo_iot.py` | 1 |
| `backend/app/db/seeders/demo_field_operations.py` | 1 |

### Modules Fixed
| File | Occurrences Fixed |
|------|-------------------|
| `backend/app/modules/seed_bank/router.py` | 1 |

### Model Defaults Fixed
| File | Occurrences Fixed |
|------|-------------------|
| `backend/app/models/base.py` | 2 |
| `backend/app/models/field_operations.py` | 13 |
| `backend/app/models/security_audit.py` | 4 |
| `backend/app/models/stress_resistance.py` | 10 |
| `backend/app/models/collaboration.py` | 4 |
| `backend/app/models/data_management.py` | 17 |
| `backend/app/modules/seed_bank/models.py` | 10 |
| `backend/app/services/vector_store.py` | 2 |
| `backend/app/services/audit_service.py` | 1 |

### Dataclass/Pydantic Defaults Fixed
| File | Occurrences Fixed |
|------|-------------------|
| `backend/app/integrations/base.py` | 1 |
| `backend/app/services/field_environment.py` | 4 |
| `backend/app/services/task_queue.py` | 1 |
| `backend/app/services/llm_service.py` | 1 |
| `backend/app/services/dus_testing.py` | 2 |

---

## Verification

```bash
# Verify Pydantic class Config: patterns (should be 0)
grep -r "class Config:" backend/app --include="*.py" | wc -l
# Expected: 0

# Verify all datetime.utcnow patterns are gone
grep -r "datetime\.utcnow" backend/app --include="*.py" | wc -l
# Expected: 0

# Verify runtime code is clean
grep -r "datetime\.utcnow()" backend/app/api --include="*.py" | wc -l
# Expected: 0

grep -r "datetime\.utcnow()" backend/app/services --include="*.py" | wc -l
# Expected: 0

grep -r "datetime\.utcnow()" backend/app/core --include="*.py" | wc -l
# Expected: 0

grep -r "datetime\.utcnow" backend/app/models --include="*.py" | wc -l
# Expected: 0
```

---

## Session Log

| Date | Session | Action |
|------|---------|--------|
| 2026-01-01 | 43 | Fixed datetime.utcnow() in ~27 service files |
| 2026-01-01 | 43 | Fixed Pydantic class Config: in ~33 files (~97 classes) |
| 2026-01-01 | 44 | Fixed datetime.utcnow() in API endpoints, core modules, seeders |
| 2026-01-01 | 44 | Fixed model defaults in 6 model files (~50 occurrences) |
| 2026-01-01 | 44 | Fixed remaining model/dataclass defaults in 8 additional files (~22 occurrences) |
| 2026-01-01 | 49 | Verified all fixes complete (0 occurrences remaining) |

---

## Notes

- Model defaults use `lambda: datetime.now(timezone.utc)` pattern
- This is Python-side timestamp generation (not database-side)
- No migrations required - the lambda is called at insert time
- All deprecation warnings have been resolved and verified

---

## Verification Results (Session 49)

```
✅ grep -r "class Config:" backend/app → 0 matches
✅ grep -r "datetime\.utcnow" backend/app → 0 matches
```

All deprecation patterns have been eliminated from the codebase.
