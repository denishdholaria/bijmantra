# BijMantra AI Coding Instructions

## Scope

This is the always-on repo contract. Keep it short.

- Put path-scoped detail in `.github/instructions/`.
- Put repeatable specialist workflows in `.github/skills/`.
- Put agent-routing and control-surface guidance in `AGENTS.md` and `.github/agents/`.
- Put architecture decisions and execution trail material in `.ai/`.

## Project Snapshot

- BijMantra is a preview cross-domain agricultural intelligence platform.
- It publishes all 201 official BrAPI v2.1 operations while maintaining a broader local `/brapi/v2` surface tracked in `/metrics.json`.
- Core thesis: no agricultural decision exists in a single domain.
- Metrics source of truth: `/metrics.json`.
- Architecture trail: `.ai/decisions/` + `.ai/tasks/`.
- Current stack: FastAPI and Python, PostgreSQL with PostGIS and pgvector, React 19 with TypeScript and Vite, Rust/WASM, and Fortran.
- Default local tooling: Podman for containers and Bun for frontend package management.

## Non-Negotiable Rules

- No mock data in production paths. Prefer database-backed truth.
- Demo flows must stay isolated in the deterministic Demo Organization dataset. Do not mirror production or staging data into demo seeders.
- Keep scientific provenance visible. Cross-domain and API surfaces should carry context, assumptions, uncertainty, and provenance rather than raw values alone.
- New cross-domain modules must declare domain scope, assumptions, limitations, and uncertainty handling, and expose domain-neutral inputs and outputs.
- Use Podman-oriented workflows, not Docker-first assumptions.
- Update `metrics.json` when implementation counts or project-state metadata change.
- Do not create a second architecture trail. Use `.ai/` for repo-local proposals, reviews, decisions, and tasks. Use `.agent/jobs/` only as a derived overnight queue surface.
- Treat `.github/docs/architecture/2026-03-29-reevu-trusted-surface-map.md` and `.github/instructions/reevu-trusted-surfaces.instructions.md` as the locked first-wave REEVU authority boundary. Default to safe failure rather than broadening authority.
- If pushing is explicitly requested, use `git push bijmantraorg main`. Do not push to other remotes.
- Do not expose filtered or confidential material such as `docs/gupt/`, `.env*`, or credentials.

## Working Defaults

- Start from current repo evidence, not stale docs or assumptions.
- Make the smallest valid change that preserves tenant safety, BrAPI discipline, and cross-domain boundaries.
- Prefer extraction over accretion when a touched file is already large or responsibility-dense. Follow `.github/instructions/anti-devil-file-growth.instructions.md`.
- If a rule is path-specific, follow the matching file under `.github/instructions/` instead of expanding this repo-wide file.
- If a workflow is repeated or specialist, prefer `.github/skills/` or `.github/prompts/` instead of adding more always-on instruction text.
- For multi-agent work, start with `OmShriMaatreNamaha` unless one clear specialist owner is already obvious.

## Key Commands

```bash
make dev              # Start PostgreSQL only
make dev-all          # Start optional Redis, MinIO, and Meilisearch too
make dev-backend      # Backend development server
make dev-frontend     # Frontend development server
make test             # Default backend + frontend correctness checks
make lint && make format
make db-migrate
make startup-doctor
make migration-doctor
make pr-review-pack
```

## Key Paths

- `backend/app/api/v2/` - API endpoints
- `backend/app/models/` - SQLAlchemy models
- `backend/app/schemas/` - Pydantic schemas
- `frontend/src/pages/` - page surfaces
- `frontend/src/components/` - shared UI
- `frontend/src/lib/api-client.ts` - frontend API client
- `.github/instructions/` - path-scoped rules
- `.github/skills/` - repeatable specialist workflows
- `AGENTS.md` - repo workflow and control-surface map
