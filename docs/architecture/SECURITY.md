# Security Model

## Audit Logging
- `AuditLog` persists immutable mutation events (`POST/PUT/DELETE`) with organization boundary fields and request metadata.
- Middleware performs asynchronous inserts to keep request latency low.
- PII-like keys (`name`, `email`, `phone`, `contact`, `address`) are masked before persistence.

## RBAC Expansion Plan
New business roles to standardize:
- **Scientist**: read/write scientific engines, create datasets and trials.
- **LabTech**: execute operational workflows (imports, annotations, scans), no policy administration.
- **Reviewer**: read scope + approval/review actions, no destructive rights.

Permission model:
1. `permissions` table stores canonical `permission.code` values.
2. `role_permissions` maps role records to permissions.
3. Compatibility fallback still supports legacy `roles.permissions` JSON during transition.

## Endpoint Enforcement
- `require_permission(permission_code)` dependency enforces per-endpoint permission checks.
- `/api/v2/vision` now requires `read:plant_sciences` minimum access.

## Emergency Lockdown
- `EmergencyLockdown.enabled` toggles global write freeze at middleware level for mutating requests.

## High-Resource Rate Limiting
- Middleware applies stricter in-memory throttling for high-cost science routes (`/compute`, `/gwas`, `/simulation`, etc.).

## Encryption-at-Rest Verification
- `verify_encryption_at_rest` checks PostgreSQL `pg_settings` values (`ssl`, `data_checksums`) to aid compliance reporting.
