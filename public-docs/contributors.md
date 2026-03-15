# Contribute to BijMantra

Last reviewed: 2026-02-25
Owner: BijMantra Maintainers

## Why Contribute

BijMantra is an open agricultural intelligence platform focused on cross-domain reasoning across breeding, genomics, phenotyping, climate, soil, and economics.

Your contribution helps researchers and practitioners make better decisions with transparent, evidence-aware software.

## Fastest Ways to Help

1. Fix bugs in backend API endpoints (`backend/app/api/v2/**`).
2. Improve UI flows in key pages (`frontend/src/pages/**`).
3. Add or improve tests (`backend/tests/**`, `frontend/e2e/**`).
4. Improve docs for users and developers (`docs/public/**`).
5. Validate workflows with real-world agricultural scenarios.

## Good First Contribution Areas

- API response consistency and validation checks.
- Error handling and safe-failure behavior.
- Frontend usability polish for forms and detail pages.
- Test reliability and CI stability.
- Public documentation quality.

## Contribution Standards

- Keep changes focused and reviewable.
- Include tests for behavior changes.
- Explain assumptions and limitations clearly.
- Prefer additive, backward-compatible changes.

## Setup and Workflow

1. Read `CONTRIBUTING.md`.
2. Set up local environment from `README.md`.
3. Create a branch using `feature/*`, `bugfix/*`, or `docs/*`.
4. Implement and validate your change.
5. Open a pull request with:
   - what changed,
   - why it changed,
   - test evidence,
   - known limitations.

## Validation Commands

Use the relevant commands for your change type:

```bash
make test
make lint
```

Backend-focused changes typically include:

```bash
cd backend && uv run pytest -q
```

Frontend-focused changes typically include:

```bash
cd frontend && npm run build
cd frontend && npm run test:run
```

## Communication

If you are unsure where to start, open an issue and describe:

- your background,
- the domain you want to work on,
- the kind of contribution you prefer (code, tests, docs, UX).

Maintainers can then suggest a scoped first task.

## Related Public Docs

- `README.md`
- `CONTRIBUTING.md`
- `docs/public/sponsors.md`
