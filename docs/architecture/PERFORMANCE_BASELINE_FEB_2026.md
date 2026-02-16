# Performance Baseline — February 2026

## Scope

This baseline captures the VAJRA hardening pass focused on API middleware overhead, static BrAPI caching, and build output chunking.

## Baseline Signals

- **Backend middleware path**: security headers middleware switched to function middleware to avoid `BaseHTTPMiddleware` overhead.
- **Static BrAPI cacheability**: `/brapi/v2/serverinfo` now emits `ETag` and `Cache-Control: public, max-age=300` and supports `304 Not Modified`.
- **Frontend build chunking**: Vite build now enforces stronger tree-shaking and additional manual vendor chunk groups (`vendor-charts`, `vendor-math`).

## Measurement Commands

Run these commands in CI and record P50/P95 latency plus bundle breakdown:

```bash
# Backend smoke latency (replace host as needed)
python backend/smoke_test_executor.py

# Frontend bundle output
cd frontend && npm run build
```

## Notes

- Full benchmark automation (`benchmark.py`) is not present in this repository snapshot; use `smoke_test_executor.py` until benchmark harness is added.
