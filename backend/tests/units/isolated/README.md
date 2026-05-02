# Isolated Unit Tests

This directory contains unit tests that must run in strict isolation from the global test runner's configuration (e.g., `conftest.py`).

## Purpose

The main project environment often has complex dependencies (FastAPI, SQLAlchemy, Geometry, etc.) that can cause test discovery failures or require extensive mocking in sparse environments.

Isolated tests are designed to verify specific logic (e.g., algorithms, utilities, domain logic) without needing the full application context.

## How to Run

Do **not** use `pytest` directly on this directory if the global `conftest.py` is broken or missing dependencies.

Instead, run these tests directly with `python`:

```bash
# From the repository root
python backend/tests/units/isolated/test_experimental_designs.py
```

## Guidelines for New Tests

1. Use `unittest.TestCase`.
2. Do not rely on `pytest` fixtures from `conftest.py`.
3. Add `sys.path.insert(0, os.path.abspath("backend"))` to import app modules.
4. Keep dependencies minimal.
