# Bijmantra Rust-First Enterprise Re-Architecture

## 1) Executive Architectural Rationale

### Current-State Findings (Repository Analysis Summary)

Bijmantra is already a multi-runtime system with substantial breadth:

- **Backend**: Python/FastAPI monolithic API surface (BrAPI + platform endpoints), SQLAlchemy/Alembic, Redis/Meilisearch integrations, and broad module sprawl under `backend/app/api/v2` and `backend/app/modules`.
- **Frontend**: Large React + TypeScript PWA with extensive division/workspace routing and >200 pages.
- **High-performance compute**: Existing Rust WASM engine under `rust/` and an additional Rust crate embedded in `backend/crates/genomics_kernel`.
- **DevOps**: Docker Compose (dev/prod), Kubernetes manifests + Helm chart, Prometheus/Grafana scaffolding, and GitHub Actions CI/E2E workflows.
- **Data/ops pattern**: PostgreSQL + Redis + MinIO + Meilisearch already standardized.

This provides a strong foundation to move from **polyglot by accumulation** to **polyglot by policy**, with Rust as the primary systems language.

### Why Rust Is Chosen

Rust is selected as primary backend language for enterprise reasons, not trend reasons:

1. **Memory safety without GC pauses**: Critical for high-throughput APIs and long-running scientific workloads.
2. **Predictable latency and lower infra cost**: Suitable for heavy compute (genomics/statistics) and API fan-out.
3. **Type-system guarantees**: Strong compile-time contracts reduce regressions in complex domain logic.
4. **Unified language across domains**: API services, workers, CLIs, data pipelines, and WASM modules can share domain crates.
5. **Security posture**: Eliminates broad classes of memory vulnerabilities; aligns with regulated environments.

### Enterprise Design Principles Applied

- **Domain-driven modularization** around bounded contexts (Breeding, Germplasm, Phenotyping, Genotyping, Ops, Compliance).
- **Hexagonal architecture** with strict inward dependencies.
- **Platform engineering first**: standardized build, test, SBOM, supply-chain controls, and runtime guardrails.
- **Observability-by-default**: trace IDs, RED/USE metrics, structured logs, SLOs.
- **Security-by-default**: identity, mTLS, secrets lifecycle, policy-as-code, tenant isolation.
- **Operational maturity**: blue/green/canary, migrations with rollback, feature flags, progressive delivery.

### Monolith vs Modular Monolith vs Microservices

**Decision: Modular Monolith first, selective microservices later.**

- Start with a **Rust modular monolith** to reduce operational overhead and preserve consistency across fast-moving domain teams.
- Enforce **internal module contracts via crates** so extraction to microservices is a deployment decision, not a rewrite.
- Split into microservices only when measurable triggers occur:
  - independent scaling needs,
  - team autonomy bottlenecks,
  - hard isolation requirements,
  - protocol heterogeneity.

### Deployment Model

**Primary model: Kubernetes (multi-environment), with local Compose for developer ergonomics.**

- Kubernetes for prod/staging with GitOps.
- Managed PostgreSQL/Redis/Object storage where possible.
- Optional hybrid: edge/offline nodes for field operations syncing to central control plane.

### Async Runtime Choice

**Tokio** as the standard runtime:

- Mature ecosystem with Axum/Tonic/Tower.
- Strong support for async IO, timers, channels, cancellation, tracing propagation.
- Compatible with background workers and streaming workloads.

### API Style

- **External/public APIs**: REST (BrAPI compatibility must remain first-class).
- **Internal service-to-service**: gRPC (Tonic/Prost) for strongly typed contracts.
- **Read-heavy aggregator surfaces**: optional GraphQL federation at gateway only if query orchestration complexity warrants it.

### Observability Stack

- `tracing` + `tracing-subscriber` for structured logs.
- OpenTelemetry SDK + OTLP exporters.
- Prometheus for metrics scraping.
- Tempo/Jaeger for traces, Loki/OpenSearch for logs.
- Grafana dashboards + SLO alerting via Alertmanager/PagerDuty.

### Security Model

- OIDC/OAuth2.1 + JWT access tokens (short-lived), refresh tokens with rotation.
- Fine-grained authorization (RBAC + ABAC + domain policies).
- mTLS for internal traffic (service mesh or sidecarless policy).
- Secrets in Vault/KMS, no plaintext secrets in manifests.
- Supply-chain security: pinned dependencies, SBOM, image signing, provenance attestation.

### Multi-Tenancy Strategy

Given existing RLS direction, recommend **PostgreSQL row-level security + tenant context propagation** as default tenancy model:

- Tenant ID mandatory in request context and DB session settings.
- Hard guardrails in data-access layer; deny-by-default.
- Premium/regulated tenants may use **database-per-tenant** profile, supported by same application code.

---

## 2) Enterprise-Grade Folder & File Structure (Production Tree)

```text
bijmantra/
 ├── Cargo.toml
 ├── Cargo.lock
 ├── rust-toolchain.toml
 ├── .cargo/
 │   └── config.toml
 ├── apps/
 │   ├── api-gateway/
 │   │   ├── Cargo.toml
 │   │   └── src/main.rs
 │   ├── identity-service/
 │   ├── domain-api/
 │   ├── ingestion-service/
 │   ├── workflow-service/
 │   ├── search-indexer/
 │   ├── realtime-service/
 │   ├── analytics-worker/
 │   └── migration-runner/
 ├── crates/
 │   ├── domain/
 │   │   ├── breeding/
 │   │   ├── germplasm/
 │   │   ├── phenotyping/
 │   │   ├── genotyping/
 │   │   ├── compliance/
 │   │   └── tenancy/
 │   ├── application/
 │   │   ├── use-cases/
 │   │   ├── commands/
 │   │   ├── queries/
 │   │   ├── dto/
 │   │   └── ports/
 │   ├── infrastructure/
 │   │   ├── persistence-postgres/
 │   │   ├── cache-redis/
 │   │   ├── objectstore-s3/
 │   │   ├── queue-nats/
 │   │   ├── search-meilisearch/
 │   │   ├── auth-oidc/
 │   │   └── telemetry/
 │   ├── interface/
 │   │   ├── http-rest/
 │   │   ├── grpc/
 │   │   ├── events/
 │   │   └── graphql/
 │   ├── shared/
 │   │   ├── error/
 │   │   ├── config/
 │   │   ├── types/
 │   │   ├── observability/
 │   │   ├── security/
 │   │   └── testing/
 │   └── science/
 │       ├── genomics-core/
 │       ├── statistics-core/
 │       ├── simulation-core/
 │       └── wasm-bindings/
 ├── frontend/
 │   ├── web-app/                 # Leptos/Yew SSR+CSR hybrid
 │   ├── admin-console/           # Rust UI for operations/compliance
 │   ├── design-system/           # shared components/tokens
 │   └── edge-field-client/       # offline-first WASM app
 ├── proto/
 │   ├── bijmantra/
 │   └── buf.yaml
 ├── api-contracts/
 │   ├── openapi/
 │   ├── brapi/
 │   └── graphql/
 ├── db/
 │   ├── migrations/
 │   ├── seeds/
 │   ├── policies/
 │   └── views/
 ├── deployments/
 │   ├── helm/
 │   │   ├── bijmantra-platform/
 │   │   └── charts/
 │   ├── kustomize/
 │   │   ├── base/
 │   │   ├── overlays/staging/
 │   │   └── overlays/production/
 │   ├── terraform/
 │   │   ├── modules/
 │   │   └── envs/
 │   └── argocd/
 │       └── applications/
 ├── platform/
 │   ├── policy/
 │   │   ├── opa/
 │   │   └── kyverno/
 │   ├── observability/
 │   │   ├── prometheus/
 │   │   ├── grafana/
 │   │   ├── loki/
 │   │   └── tempo/
 │   ├── security/
 │   │   ├── vault/
 │   │   └── cert-manager/
 │   └── runbooks/
 ├── scripts/
 │   ├── dev/
 │   ├── ci/
 │   ├── release/
 │   └── migrations/
 ├── tests/
 │   ├── contract/
 │   ├── integration/
 │   ├── e2e/
 │   ├── performance/
 │   └── chaos/
 ├── docs/
 │   ├── architecture/
 │   ├── adr/
 │   ├── operations/
 │   ├── security/
 │   └── rustic.md
 └── .github/
     └── workflows/
```

### Major Folder Purpose, Enterprise Rationale, and Boundaries

- **`apps/`**
  - Purpose: Deployable binaries (gateway, services, workers).
  - Why: Separate runtime concerns from reusable logic.
  - Rules: `apps/*` may depend on `crates/*`; never reverse.

- **`crates/domain/`**
  - Purpose: Pure business invariants, entities, value objects, domain events.
  - Why: Highest stability and testability; no framework leakage.
  - Rules: No DB/network imports. Only `shared/types` and sibling domain crates by explicit contract.

- **`crates/application/`**
  - Purpose: Use-cases/orchestration, command/query handlers, port definitions.
  - Why: Encodes business workflows independent of adapters.
  - Rules: Depends on `domain`, declares traits for infrastructure.

- **`crates/infrastructure/`**
  - Purpose: Implement ports for DB/cache/queue/search/auth.
  - Why: Isolates vendor technology and SDK churn.
  - Rules: May depend on `application` port traits and `shared`; never consumed directly by domain.

- **`crates/interface/`**
  - Purpose: Protocol adapters (REST/gRPC/events/graphql).
  - Why: Keeps transport concerns separate from use-case logic.
  - Rules: Calls application handlers only; no raw SQL.

- **`crates/shared/`**
  - Purpose: Cross-cutting primitives (error model, config, observability, security helpers).
  - Why: Prevents duplicated platform glue.
  - Rules: Must remain generic and minimal; no domain-specific business logic.

- **`crates/science/`**
  - Purpose: Performance-critical algorithms reused by backend and WASM frontends.
  - Why: Single-source scientific correctness with deterministic tests.
  - Rules: Pure compute crates; no transport or persistence concerns.

- **`frontend/`**
  - Purpose: Rust-first UI clients + shared design system.
  - Why: Maximize code sharing, type consistency, and WASM performance.
  - Rules: UI layers consume published API contracts; no direct DB coupling.

- **`deployments/` and `platform/`**
  - Purpose: Environment provisioning + cluster policies + observability/security baseline.
  - Why: Infrastructure as product for multiple teams.
  - Rules: Environment overlays only; immutable base manifests and versioned platform modules.

- **`db/`**
  - Purpose: Schema migrations, RLS policies, seed data.
  - Why: Controlled, auditable data evolution.
  - Rules: Backward-compatible migrations; roll-forward preferred.

- **`tests/`**
  - Purpose: System-level quality gates beyond crate unit tests.
  - Why: Enterprise reliability and contract stability.
  - Rules: Contract tests are release-blocking.

---

## 3) Architectural Layering (Clean / Hexagonal)

### Layers

1. **Domain Layer (`crates/domain/*`)**
   - Entities, aggregates, value objects, domain services, domain events.
   - Zero runtime framework dependencies.

2. **Application Layer (`crates/application/*`)**
   - Use-cases (commands/queries), transaction boundaries, authorization intent checks.
   - Defines inbound and outbound ports (traits).

3. **Infrastructure Layer (`crates/infrastructure/*`)**
   - Postgres repositories, Redis caches, queue producers/consumers, object store, search, IAM adapter.
   - Implements application ports.

4. **Interface Layer (`crates/interface/*` + `apps/*`)**
   - HTTP/gRPC/event handlers, request validation, response mapping.
   - Handles authn context, correlation IDs, tenant propagation.

### Dependency Direction

**Allowed direction only:** `interface -> application -> domain` and `infrastructure -> application/domain contracts`.

- Domain cannot depend on application/infrastructure/interface.
- Application depends on domain + trait abstractions.
- Infrastructure depends on trait abstractions and external SDKs.

### Ownership Boundaries

- Each bounded context owns:
  - its domain model,
  - its use-cases,
  - persistence adapters,
  - API contracts.
- Cross-domain interactions via:
  - explicit application service APIs,
  - domain events on message bus,
  - no shared mutable state.

### Shared Crate Strategy

- `shared/types`: IDs, pagination, money/measurement, date wrappers.
- `shared/error`: typed error taxonomy with machine-readable codes.
- `shared/security`: claims parsing, policy interfaces.
- `shared/observability`: tracing setup, metric macros, context propagation.
- Keep shared crates low churn and highly reviewed.

### Compile-Time Safety Maximization

- Newtypes for IDs and tenant-aware keys.
- Exhaustive enums for state machines.
- `serde(deny_unknown_fields)` for strict contract parsing.
- SQL compile-time checks (`sqlx` offline mode).
- Lints: `clippy -D warnings`, `rustfmt`, `cargo deny`, `cargo audit`.

---

## 4) Technology Recommendations (Opinionated)

### Core Backend Stack

- **Web framework:** **Axum**
  - Best fit with Tower middleware ecosystem, Tokio, tracing, and ergonomic extractors.
  - Strong maintainability for large teams.

- **ORM/Data access:** **SQLx + refinery/sea-query hybrid strategy**
  - SQLx for compile-time checked SQL and performance transparency.
  - Prefer explicit SQL in critical scientific/analytical paths.
  - Use SeaQuery for composable dynamic query generation when needed.

- **Async runtime:** **Tokio**

- **Background jobs:** **Apalis** or **custom Tokio worker pool + NATS streams**
  - For deterministic retries, dead-letter queues, and idempotency keys.

- **Message queue:** **NATS JetStream**
  - Lightweight, high-throughput, clear at-least-once semantics, good for event-driven modularity.

- **Caching layer:** **Redis**
  - Read-through cache, token/session cache, distributed locks for job coordination.

### Identity, Security, Secrets

- **AuthN:** OIDC provider (Keycloak/Auth0/Entra) with JWT + PKCE for clients.
- **AuthZ:** OPA/Rego policies for ABAC + service RBAC.
- **Secrets:** HashiCorp Vault or cloud KMS + External Secrets Operator.

### CI/CD Strategy

- Monorepo pipeline with path-aware jobs.
- Required stages:
  1. format/lint/static checks,
  2. unit + integration tests,
  3. contract tests,
  4. SBOM + vulnerability scan,
  5. container signing,
  6. progressive deployment.
- GitOps via Argo CD/Flux; no imperative production kubectl in CI.

### Observability Stack

- `tracing`, `opentelemetry`, `prometheus` exporters.
- Prometheus + Alertmanager (metrics/alerts).
- Grafana (dashboards).
- Tempo/Jaeger (traces).
- Loki/OpenSearch (logs).

### Testing Strategy

- **Unit tests:** every domain and use-case crate.
- **Integration tests:** testcontainers for Postgres/Redis/NATS.
- **Contract tests:** OpenAPI/BrAPI/gRPC compatibility gates.
- **E2E tests:** browser + API journeys for critical breeding workflows.
- **Load tests:** k6/Gatling with SLO thresholds.
- **Chaos tests:** pod/network failure scenarios for resilience validation.

---

## 5) Enterprise Hardening Considerations

- **Zero-downtime deployment**
  - rolling/canary + readiness gates + schema-expand-contract.

- **Horizontal scaling**
  - stateless APIs, externalized sessions, queue-driven workers.

- **Multi-region readiness**
  - active/passive first (DR), optional active/active for read-heavy services.
  - global DNS failover and replication lag monitoring.

- **Feature flags**
  - OpenFeature-compatible provider; kill switches for risky experiments.

- **API versioning**
  - URI and header versioning policy; semantic deprecation windows.
  - BrAPI compatibility matrix published per release.

- **Data migration strategy**
  - forward-only migration files, preflight checks, reversible fallback scripts for critical changes.

- **Backward compatibility**
  - tolerant readers, additive changes first, event versioning with upcasters.

- **Security best practices**
  - mTLS, CSP/HSTS, strict input validation, SSRF egress policies, WAF/rate limits.

- **Rate limiting**
  - global + tenant + token buckets at gateway and service level.

- **Audit logging**
  - immutable append-only audit stream with signed event envelopes.

- **Compliance readiness**
  - controls mapped for SOC 2 / ISO 27001 / GDPR-like data governance.
  - retention policies, data lineage, subject-access workflows.

---

## 6) Migration Strategy (Phased Roadmap)

### Phase 0 — Baseline and Guardrails (0–6 weeks)

- Introduce monorepo Rust workspace and shared platform crates.
- Add Rust CI quality gates (fmt, clippy, tests, audit, deny).
- Freeze net-new Python architectural sprawl; mandate API contract-first changes.

### Phase 1 — Strangler Gateway + Shared Contracts (6–12 weeks)

- Deploy Rust `api-gateway` in front of current FastAPI.
- Move authn/authz enforcement, rate limiting, and observability to gateway.
- Publish canonical OpenAPI/BrAPI schemas; enforce contract tests.

### Phase 2 — Domain-by-Domain Rust Extraction (3–9 months)

Prioritized extraction order:
1. **High-value compute-heavy services** (genotyping/genomics/statistics) leveraging existing Rust assets.
2. **Identity and tenancy context services** (security critical).
3. **Read-heavy aggregates/search/indexing paths**.
4. **Remaining CRUD-heavy domains**.

Each extracted domain follows:
- parity tests against current behavior,
- shadow traffic validation,
- canary rollout,
- measured cutover.

### Phase 3 — Data Plane Hardening (parallel)

- Formalize RLS policies and tenant test matrix.
- Implement outbox/event relay for reliable cross-domain events.
- Introduce CQRS read models for complex dashboard workloads.

### Phase 4 — Frontend Rust Adoption (incremental)

- Keep existing React app operational.
- Introduce Rust WASM modules for performance-sensitive components first.
- Incrementally build new admin/ops surfaces in Leptos/Yew where ROI is clear.
- Maintain shared API contracts to avoid frontend/backend drift.

### Phase 5 — Decommission Legacy and Optimize (6+ months)

- Retire migrated FastAPI modules.
- Enforce Rust-first contribution policy for new backend services.
- Optimize infra costs and SLO posture based on production telemetry.

### Non-Negotiable Migration Controls

- No big-bang rewrite.
- Every phase has measurable exit criteria (latency, error budget, cost, defect rate).
- Rollback path must exist before cutover.
- Security and compliance checks are release blockers.

---

## Closing Position

The recommended target is a **Rust-first modular enterprise platform** that preserves BrAPI commitments, improves reliability and security, and enables multi-team development without operational chaos. The strategy intentionally balances ambition with risk control: strangler migration, contract governance, and platform guardrails first; aggressive domain modernization second.
