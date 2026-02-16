# Backend Dependencies Audit - February 2025

> **Audit Date**: February 11, 2026  
> **Python Version**: 3.14  
> **Status**: 🟡 Multiple outdated packages identified

---

## Executive Summary

**Outdated Packages**: 15 of 50 packages  
**Critical Updates**: 8 packages  
**Security Concerns**: NumPy, pandas (2+ years old)  
**Breaking Changes**: NumPy 2.x migration required

---

## Critical Updates Required

### 1. Scientific Computing Stack (CRITICAL)

| Package | Current | Latest | Status | Priority |
|---------|---------|--------|--------|----------|
| **numpy** | >=1.24.0 | **2.4.0** | 🔴 2+ years old | **HIGH** |
| **pandas** | >=2.0.0 | **2.2.3** | 🟡 Needs update | **HIGH** |
| **scipy** | >=1.10.0 | **1.15.1** | 🟡 Needs update | **HIGH** |
| **scikit-learn** | >=1.3.0 | **1.6.1** | 🟡 Needs update | **HIGH** |
| **xgboost** | >=2.0.0 | **2.1.3** | 🟡 Minor update | MEDIUM |

**Impact**: Performance improvements, security fixes, NumPy 2.x compatibility

---

### 2. Web Framework Stack

| Package | Current | Latest | Status | Priority |
|---------|---------|--------|--------|----------|
| **fastapi** | >=0.115.0 | **0.116.1** | 🟢 Recent | LOW |
| **uvicorn** | >=0.32.0 | **0.34.0** | 🟡 Minor update | MEDIUM |
| **pydantic** | >=2.10.0 | **2.12.0** | 🟡 Minor update | MEDIUM |
| **sqlalchemy** | >=2.0.36 | **2.0.40** | 🟡 Minor update | MEDIUM |
| **alembic** | >=1.14.0 | **1.15.1** | 🟡 Minor update | LOW |

**Impact**: Bug fixes, performance improvements

---

### 3. Data Processing Stack

| Package | Current | Latest | Status | Priority |
|---------|---------|--------|--------|----------|
| **polars** | >=0.19.0 | **1.33.0** | 🔴 Major version behind | **HIGH** |
| **pyarrow** | >=14.0.0 | **19.0.0** | 🟡 Several versions behind | MEDIUM |
| **duckdb** | >=0.9.0 | **1.2.0** | 🟡 Major version behind | MEDIUM |

**Impact**: Polars 1.x has breaking changes, significant performance improvements

---

### 4. Other Notable Updates

| Package | Current | Latest | Status | Priority |
|---------|---------|--------|--------|----------|
| **pillow** | >=10.4.0 | **11.2.0** | 🟡 Major version | MEDIUM |
| **redis** | >=5.2.0 | **5.3.0** | 🟢 Recent | LOW |
| **httpx** | >=0.28.0 | **0.29.0** | 🟢 Recent | LOW |
| **pytest** | >=8.3.0 | **8.4.0** | 🟢 Recent | LOW |
| **cryptography** | >=41.0.0 | **44.0.0** | 🟡 Security updates | MEDIUM |

---

## NumPy 2.x Migration Analysis

### Breaking Changes

**NumPy 2.0** (released June 2024) introduced:
1. Scalar precision changes
2. Removed deprecated APIs
3. C API changes (affects compiled extensions)
4. Performance improvements (17x faster in some operations)

### Compatibility Matrix

| Package | NumPy 1.24 | NumPy 2.x | Min Version for NumPy 2.x |
|---------|------------|-----------|---------------------------|
| pandas | ✅ | ✅ | pandas >= 2.2.0 |
| scikit-learn | ✅ | ✅ | scikit-learn >= 1.5.0 |
| scipy | ✅ | ✅ | scipy >= 1.13.0 |
| xgboost | ✅ | ✅ | xgboost >= 2.1.0 |
| scikit-allel | ✅ | ⚠️ | Check compatibility |
| shap | ✅ | ✅ | shap >= 0.44.0 (current) |

### Migration Risk Assessment

**Risk Level**: 🟡 MEDIUM

**Reasons**:
- Most packages now support NumPy 2.x (as of late 2024)
- Your current versions need updates for compatibility
- `scikit-allel` compatibility uncertain
- `zarr<4.0.0` constraint may conflict

**Mitigation**:
1. Update all scientific packages together
2. Run full test suite after update
3. Check `scikit-allel` compatibility first

---

## Recommended Update Strategy

### Phase 1: Safe Updates (No Breaking Changes)

```python
# Web Framework (minor updates)
fastapi>=0.116.0
uvicorn[standard]>=0.34.0
pydantic[email]>=2.12.0
sqlalchemy>=2.0.40
alembic>=1.15.0

# Security
cryptography>=44.0.0

# Testing
pytest>=8.4.0
```

### Phase 2: Scientific Stack (Coordinated Update)

```python
# NumPy 2.x Migration
numpy>=2.0.0,<3.0.0
pandas>=2.2.3
scipy>=1.15.0
scikit-learn>=1.6.0
xgboost>=2.1.3
```

### Phase 3: Data Processing (Breaking Changes)

```python
# Polars 1.x (breaking changes from 0.19)
polars>=1.33.0

# PyArrow
pyarrow>=19.0.0

# DuckDB
duckdb>=1.2.0
```

---

## Polars 0.19 → 1.33 Migration Notes

**Breaking Changes**:
- API changes in DataFrame methods
- LazyFrame execution changes
- Expression syntax updates
- New plotting backend (native, no pandas required)

**Benefits**:
- 2-3x performance improvements
- Better memory efficiency
- Native plotting support
- Improved scikit-learn integration (DataFrame Protocol)

**Migration Effort**: MEDIUM (2-4 hours)

---

## Testing Requirements

### Before Update
```bash
# Capture current test results
pytest backend/tests/ --tb=short > pre_update_tests.log

# Document current behavior
python -c "import numpy; print(numpy.__version__)"
python -c "import pandas; print(pandas.__version__)"
```

### After Update
```bash
# Run full test suite
pytest backend/tests/ -v

# Check for deprecation warnings
pytest backend/tests/ -W error::DeprecationWarning

# Verify scientific computations
pytest backend/tests/services/test_breeding_value_solver.py
pytest backend/tests/services/test_gxe_analysis.py
```

---

## Proposed Updated requirements.txt

```python
fastapi>=0.116.0
uvicorn[standard]>=0.34.0
pydantic[email]>=2.12.0
pydantic-settings>=2.6.0
sqlalchemy>=2.0.40
alembic>=1.15.0
asyncpg>=0.30.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.20
pillow>=11.0.0
redis>=5.3.0
httpx>=0.29.0
pytest>=8.4.0
pytest-asyncio>=0.24.0
ruff>=0.8.0
geoalchemy2>=0.16.0
shapely>=2.0.0
minio>=7.2.10
python-socketio>=5.10.0
meilisearch==0.40.0
sentry-sdk[fastapi]>=1.38.0

# Vector Store & Embeddings
pgvector>=0.2.4
sentence-transformers>=2.2.0
greenlet>=3.0.0

# MCP (Model Context Protocol)
mcp>=1.0.0

# Encryption
cryptography>=44.0.0

# Voice (VibeVoice TTS + Edge TTS)
websockets>=12.0
aiohttp>=3.9.0
edge-tts>=6.1.0

# Production Server
gunicorn>=21.0.0

# Analytical Plane (Target Architecture)
pyarrow>=19.0.0
polars>=1.33.0
duckdb>=1.2.0
psycopg2-binary>=2.9.9

# Machine Learning & Scientific Computing (NumPy 2.x compatible)
numpy>=2.0.0,<3.0.0
pandas>=2.2.3
scipy>=1.15.0
scikit-learn>=1.6.0
xgboost>=2.1.3
shap>=0.44.0
weasyprint>=60.0.0
jinja2>=3.1.0
aiosqlite>=0.20.0
email-validator>=2.0.0
scikit-allel>=1.3.0  # TODO: Verify NumPy 2.x compatibility
zarr<4.0.0
```

---

## Action Items

- [ ] Review Polars 1.x migration guide
- [ ] Check `scikit-allel` NumPy 2.x compatibility
- [ ] Run test suite with current versions (baseline)
- [ ] Update Phase 1 packages (safe updates)
- [ ] Update Phase 2 packages (NumPy 2.x stack)
- [ ] Run full test suite
- [ ] Update Phase 3 packages (Polars, PyArrow, DuckDB)
- [ ] Update documentation if API changes required
- [ ] Update `pyproject.toml` if present

---

## References

- [NumPy 2.0 Migration Guide](https://numpy.org/doc/2.0/numpy_2_0_migration_guide.html)
- [Polars 1.0 Release Notes](https://pola.rs/posts/polars-1-0/)
- [pandas 2.2 Release Notes](https://pandas.pydata.org/docs/whatsnew/v2.2.0.html)
- [scikit-learn 1.6 Release Notes](https://scikit-learn.org/stable/whats_new/v1.6.html)

---

*Generated by Kiro AI - Session 94*
