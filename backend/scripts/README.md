# Architecture Validation Scripts

This directory contains scripts for validating and enforcing the BijMantra architecture stabilization.

## Architecture Linting Scripts

These scripts enforce domain boundaries, layer contracts, and migration policies as defined in the Architecture Stabilization spec.

### 1. validate_domain_registry.py

Validates that the `domain_registry.yaml` file is properly structured and all services are registered.

**Usage:**
```bash
python scripts/validate_domain_registry.py
```

**Checks:**
- Domain registry structure is valid
- All required domains are present
- Services are properly registered to domains
- Module services match registry

**Requirements:** PyYAML (`pip install PyYAML`)

---

### 2. validate_api_registry.py

Validates that all API endpoints are documented and organized by domain.

**Usage:**
```bash
python scripts/validate_api_registry.py
```

**Checks:**
- All API endpoints are categorized by domain
- Domain routers exist in modules
- Endpoints are properly documented
- No uncategorized endpoints

**Requirements:** None (uses FastAPI introspection)

---

### 3. check_service_migration.py

Checks that no new services are added to the flat `services/` directory and tracks migration progress.

**Usage:**
```bash
python scripts/check_service_migration.py
```

**Checks:**
- No new services in flat `services/` directory
- No new services in unauthorized subdirectories
- Migration progress by domain
- Overall migration percentage

**Requirements:** PyYAML (`pip install PyYAML`)

**Policy:** New services MUST be created in domain modules (`app/modules/{domain}/services/`), not in the flat `services/` directory.

---

### 4. validate_layer_contracts.py

Validates that layer contracts are enforced (UI → API → Service → Compute/DB).

**Usage:**
```bash
python scripts/validate_layer_contracts.py
```

**Checks:**
- API layer cannot import models directly
- API layer cannot import compute layer
- Schema layer cannot import services
- No cross-domain imports that bypass contracts

**Requirements:** None (uses AST parsing)

**Note:** During migration, this script warns about violations but doesn't fail CI. After migration is complete, it will enforce strict compliance.

---

## Running All Validation Scripts

To run all validation scripts at once:

```bash
# Run architecture linting
python scripts/validate_domain_registry.py
python scripts/validate_api_registry.py
python scripts/check_service_migration.py
python scripts/validate_layer_contracts.py
```

Or use the import-linter and deptry tools:

```bash
# Install tools
pip install import-linter deptry

# Run import-linter
import-linter --config .import-linter.ini

# Run deptry
deptry .

# Run ruff with architecture rules
ruff check app
```

---

## CI/CD Integration

These scripts are integrated into the CI/CD pipeline to enforce architecture rules:

```yaml
# .gitlab-ci.yml
architecture-lint:
  stage: test
  script:
    - pip install import-linter deptry PyYAML
    - import-linter --config .import-linter.ini
    - deptry .
    - ruff check app
  
architecture-validation:
  stage: test
  script:
    - pip install PyYAML
    - python scripts/validate_domain_registry.py
    - python scripts/validate_api_registry.py
    - python scripts/check_service_migration.py
    - python scripts/validate_layer_contracts.py
```

---

## Dependencies

**Required for all scripts:**
- Python 3.13+

**Optional dependencies:**
- PyYAML: Required for `validate_domain_registry.py` and `check_service_migration.py`
- import-linter: For import boundary enforcement
- deptry: For dependency checking
- ruff: For code linting (already installed)

**Install all dependencies:**
```bash
pip install PyYAML import-linter deptry
```

---

## Architecture Rules

These scripts enforce the following architecture rules:

### Domain Boundaries
- Each domain is a bounded context
- No direct cross-domain imports
- Cross-domain communication via event_bus or explicit interfaces

### Layer Contracts
- **UI → API → Service → Compute/DB** (allowed flow)
- API layer cannot import models or compute directly
- Schema layer cannot import services or models
- Services can import models and compute

### Migration Policy
- New services MUST be in domain modules
- No new services in flat `services/` directory
- Existing services can remain during migration
- Track migration progress by domain

### Allowed Exceptions
- Core infrastructure services (task_queue, event_bus, compute_engine)
- Test files can import anything
- Migration files have special needs

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'yaml'"**
- Install PyYAML: `pip install PyYAML`

**"Domain registry not found"**
- Ensure `app/domain_registry.yaml` exists
- Run from backend directory

**"Failed to load routes"**
- Ensure FastAPI app can be imported
- Check that all dependencies are installed
- Run from backend directory

**"Architecture policy violations detected"**
- New services must be created in domain modules
- Move service to `app/modules/{domain}/services/`
- Update imports and tests

---

## Related Documentation

- [Architecture Lane README](../../.github/docs/architecture/README.md)
- [Architecture Rules](../../confidential-docs/architecture/core/ARCHITECTURE_RULES.md)
- [Domain Registry](../app/domain_registry.yaml)
- [Service Migration Map](../../confidential-docs/architecture/tracking/service_migration_map.md)

---

## Support

For questions or issues with these scripts, refer to:
- Architecture Stabilization design document
- Architecture rules documentation
- Domain registry YAML file
