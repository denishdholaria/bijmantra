use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

use bijmantra_core::WriteAuthorizationPlan;
use serde_json::Value;

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("server crate should live under crates/")
        .to_path_buf()
}

fn read(path: &str) -> String {
    fs::read_to_string(workspace_root().join(path))
        .unwrap_or_else(|error| panic!("{path} should be readable: {error}"))
}

fn read_json(path: &str) -> Value {
    serde_json::from_str(&read(path)).unwrap_or_else(|error| panic!("{path} json: {error}"))
}

fn assert_repo_path(path: &str) {
    assert!(!path.trim().is_empty(), "repo path should not be empty");
    assert!(
        !path.starts_with('/')
            && !path.contains("..")
            && !path.contains("\\")
            && !path.contains("/Users/")
            && !path.contains("/home/"),
        "{path} should be a repo-relative path"
    );
    assert!(
        workspace_root().join(path).exists(),
        "{path} should exist in the repository"
    );
}

fn assert_contains(text: &str, needle: &str, label: &str) {
    assert!(text.contains(needle), "{label} should contain {needle:?}");
}

fn string_array<'a>(value: &'a Value, key: &str) -> Vec<&'a str> {
    value[key]
        .as_array()
        .unwrap_or_else(|| panic!("{key} should be an array"))
        .iter()
        .map(|item| {
            item.as_str()
                .unwrap_or_else(|| panic!("{key} items should be strings"))
        })
        .collect()
}

fn rust_app_router_source(source: &str) -> &str {
    let app_start = source
        .find("pub fn app")
        .expect("app router function should exist");
    let app_tail = &source[app_start..];
    let app_end = app_tail
        .find("\npub async fn serve")
        .expect("serve function should follow app router function");
    &app_tail[..app_end]
}

#[test]
fn rust_330_gate_artifacts_exist_and_are_closed() {
    let artifacts = [
        "contracts/fastapi-parity/rust-live-db-operations-gate.json",
        "contracts/fastapi-parity/rust-cross-os-gate.json",
        "contracts/fastapi-parity/rust-quality-gate.json",
        "contracts/fastapi-parity/rust-write-readiness-gate.json",
        "contracts/fastapi-parity/rust-frontend-beta-smoke.json",
        "contracts/fastapi-parity/rust-packaging-gate.json",
        "contracts/fastapi-parity/rust-api-beta-declaration.json",
    ];

    for path in artifacts {
        assert_repo_path(path);
        let artifact = read_json(path);
        let status = artifact["status"]
            .as_str()
            .unwrap_or_else(|| panic!("{path} should declare status"));
        assert!(
            matches!(status, "closed" | "declared"),
            "{path} should be closed or declared, got {status}"
        );

        for key in ["evidence", "gates"] {
            if let Some(items) = artifact.get(key).and_then(Value::as_array) {
                for item in items {
                    let item = item
                        .as_str()
                        .unwrap_or_else(|| panic!("{path} {key} item should be a string"));
                    assert_repo_path(item);
                }
            }
        }
    }
}

#[test]
fn live_db_operations_are_guarded_and_documented() {
    let script = read("scripts/rust_live_db.sh");
    let docs = read("docs/rust-operations.md");
    let gate = read_json("contracts/fastapi-parity/rust-live-db-operations-gate.json");

    for required in [
        "BIJMANTRA_RUST_LIVE_DB",
        "BIJMANTRA_RUST_SCRATCH_DB",
        "bijmantra_rust_live_test",
        "bijmantra_rust_scratch_upgrade",
        "refusing to operate on protected database name",
        "refusing to operate on DB with unsafe characters",
        "DROP DATABASE IF EXISTS",
        "CREATE DATABASE",
        "scratch-upgrade",
        "BIJMANTRA_LIVE_DATABASE_URL",
    ] {
        assert_contains(&script, required, "live DB helper");
    }

    for required in [
        "scripts/rust_live_db.sh create",
        "scripts/rust_live_db.sh reset",
        "scripts/rust_live_db.sh head",
        "scripts/rust_live_db.sh scratch-upgrade",
        "pg_trgm",
        "postgis",
        "timescaledb",
        "vector",
        "pgaudit",
    ] {
        assert_contains(&docs, required, "Rust operations docs");
    }

    let rows = gate["milestoneRows"].as_array().expect("milestone rows");
    for row in [16, 17, 20, 30, 236, 323] {
        assert!(
            rows.iter().any(|value| value.as_u64() == Some(row)),
            "live DB gate should cover row {row}"
        );
    }
}

#[test]
fn cross_os_quality_and_packaging_are_wired_to_workflow() {
    let workflow = read(".github/workflows/rust-product.yml");
    let container_docs = read("docs/rust-container.md");
    let compose = read("compose.yaml");

    for required in [
        "ubuntu-latest",
        "windows-latest",
        "macos-latest",
        "CARGO_TARGET_DIR: target/rust-product-ci",
        "astral-sh/setup-uv@v5",
        "uv run python -m py_compile",
        "cargo build --release --locked -p bijmantra-cli",
        "bij.exe",
        "oven-sh/setup-bun@v2",
        "bun run rust-beta-smoke",
        "live_postgres",
        "BIJMANTRA_LIVE_DATABASE_URL",
        "podman run --rm -d",
        "http://127.0.0.1:8000/health",
        "bijmantra:bijmantra",
        "300000000",
    ] {
        assert_contains(&workflow, required, "Rust product workflow");
    }

    for required in [
        "profiles: [rust-api]",
        "Dockerfile.rust",
        "BIJMANTRA_DATABASE_URL",
        "condition: service_healthy",
        "\"bij\"",
        "\"status\"",
    ] {
        assert_contains(&compose, required, "compose rust-api service");
    }

    for required in [
        "Runtime environment variables",
        "BIJMANTRA_DATABASE_URL",
        "podman compose --profile rust-api up -d postgres rust-api",
        "Run migrations before starting",
        "bijmantra:bijmantra",
        "300 MB beta baseline",
        "Beta Deploy Checklist",
    ] {
        assert_contains(&container_docs, required, "Rust container docs");
    }
}

#[test]
fn write_readiness_artifact_matches_core_and_server_helpers() {
    let gate = read_json("contracts/fastapi-parity/rust-write-readiness-gate.json");
    let core_source = read("crates/bijmantra-core/src/write_readiness.rs");
    let server_source = read("crates/bijmantra-server/src/db.rs");
    let router_source = read("crates/bijmantra-server/src/lib.rs");
    let cargo = read("Cargo.toml");
    let id_strategy = read("docs/rust-id-strategy.md");

    assert_eq!(gate["firstRustOwnedWrite"], "seedlot-inventory-adjustments");
    assert_eq!(
        gate["writeCandidate"]["contract"],
        "contracts/fastapi-parity/seedlot-inventory-adjustment-write-contract.json"
    );
    assert_eq!(
        gate["writeCandidate"]["capabilityId"],
        "seedops_commercialization.seed_lot_traceability"
    );
    assert_eq!(
        gate["writeCandidate"]["requiredPermission"],
        "seedops.seed_lots.adjust"
    );
    assert_eq!(gate["writeCandidate"]["auditEvent"], "seed_lot.adjusted");
    assert_eq!(gate["writeCandidate"]["publicRouteRegistered"], true);
    assert_eq!(gate["writeCandidate"]["rustRouteRegistered"], true);
    assert_eq!(gate["writeCandidate"]["status"], "guarded-route-live");
    assert_eq!(gate["uuidCrate"]["crate"], "uuid");

    for required in [
        "uuid = { version = \"1\", features = [\"serde\", \"v7\"] }",
        "PublicId",
        "Uuid::now_v7",
        "IdempotencyKey",
        "CreateDto",
        "UpdateDto",
        "DeletePolicy",
        "WriteAuditFields",
        "WriteAuthorizationPlan",
        "PlatformCapabilityAccessContext",
        "WriteAuthorizationDecision",
        "WriteAuthorizationReason",
        "evaluate_platform_context",
        "SeedlotInventoryAdjustmentRequest",
        "SeedlotInventoryAdjustmentResponse",
        "SeedlotInventoryAdjustmentResponseAdjustment",
        "SeedlotInventoryAdjustmentDetailResponse",
        "SeedlotInventoryAdjustmentAudit",
        "SeedlotInventoryAdjustmentLedgerStatus",
    ] {
        let haystack = if required.starts_with("uuid =") {
            &cargo
        } else {
            &core_source
        };
        assert_contains(haystack, required, "write-readiness core");
    }

    for required in [
        "pub async fn begin_write_transaction",
        "pub async fn create_seedlot_inventory_adjustment_internal",
        "pub async fn create_seedlot_inventory_adjustment_authorized_internal",
        "pub async fn build_seedlot_inventory_adjustment_access_context_internal",
        "pub async fn get_seedlot_inventory_adjustment_by_public_id_internal",
        "pub async fn get_seedlot_inventory_adjustment_by_idempotency_key_internal",
        "pub async fn reverse_seedlot_inventory_adjustment_internal",
        "pub async fn reverse_seedlot_inventory_adjustment_authorized_internal",
        "WriteTransactionOptions",
        "WriteAuthorizationPlan::seedlot_inventory_adjustment",
        "SeedlotInventoryAdjustmentWriteError::AuthorizationDenied",
        "pool.begin()",
        "app.current_organization_id",
        "app.current_user_id",
        "app.idempotency_key",
        "app.audit_event",
        "INSERT INTO seedlot_inventory_adjustments",
        "INSERT INTO audit_logs",
        "seedlot_inventory_adjustment",
    ] {
        assert_contains(&server_source, required, "write transaction helper");
    }

    for required in [
        "post(seedlot_inventory_adjustments_create)",
        "/api/v2/seed-inventory/adjustments",
    ] {
        assert_contains(&router_source, required, "write route registration");
    }

    for required in [
        "seedlot-inventory-adjustments",
        "public_id UUID NOT NULL UNIQUE",
        "Backfill UUID7 values",
        "The 330 milestone did not perform this migration",
        "guarded HTTP handler POST /api/v2/seed-inventory/adjustments is now live",
        "guarded HTTP handler GET /api/v2/seed-inventory/adjustments/{publicId} is now",
        "exactly one public Rust write route is exposed",
        "FastAPI remains fallback for all other writes/deferred routes",
        "no destructive inventory mutation",
    ] {
        assert_contains(&id_strategy, required, "Rust ID strategy");
    }
}

#[test]
fn seedlot_inventory_adjustment_write_contract_is_guarded_and_live() {
    let contract =
        read_json("contracts/fastapi-parity/seedlot-inventory-adjustment-write-contract.json");
    let gate = read_json("contracts/fastapi-parity/rust-write-readiness-gate.json");
    let declaration = read_json("contracts/fastapi-parity/rust-api-beta-declaration.json");
    let read_route_inventory = read_json("contracts/fastapi-parity/rust-read-routes.json");
    let write_route_inventory = read_json("contracts/fastapi-parity/rust-write-routes.json");
    let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment();

    assert_eq!(contract["status"], "guarded-route-live");
    assert_eq!(
        contract["routeCandidate"],
        "POST /api/v2/seed-inventory/adjustments"
    );
    assert_eq!(contract["method"], "POST");
    assert_eq!(contract["path"], "/api/v2/seed-inventory/adjustments");
    assert_eq!(contract["publicRouteRegistered"], true);
    assert_eq!(contract["rustRouteRegistered"], true);

    assert_eq!(
        contract["capabilityId"].as_str(),
        Some(plan.capability_id.as_str())
    );
    assert_eq!(
        contract["requiredPermission"].as_str(),
        Some(plan.required_permission.as_str())
    );
    assert_eq!(
        string_array(&contract, "requiredDataScopes"),
        vec!["organization", "lot"]
    );
    assert_eq!(
        plan.required_data_scopes,
        vec!["organization".to_owned(), "lot".to_owned()]
    );
    assert_eq!(
        contract["tenantField"].as_str(),
        Some(plan.tenant_column.as_str())
    );
    assert_eq!(
        contract["auditEvent"].as_str(),
        Some(plan.audit_event.as_str())
    );
    let read_plan = WriteAuthorizationPlan::seedlot_inventory_adjustment_read();
    assert_eq!(contract["readBackRoute"]["method"], "GET");
    assert_eq!(
        contract["readBackRoute"]["path"],
        "/api/v2/seed-inventory/adjustments"
    );
    assert_eq!(contract["readBackRoute"]["publicRouteRegistered"], true);
    assert_eq!(contract["readBackRoute"]["rustRouteRegistered"], true);
    assert_eq!(
        contract["readBackRoute"]["requiredPermission"].as_str(),
        Some(read_plan.required_permission.as_str())
    );
    assert_eq!(
        string_array(&contract["readBackRoute"], "requiredDataScopes"),
        vec!["organization", "lot"]
    );
    assert_eq!(contract["readBackRoute"]["auditEmission"], false);
    assert_eq!(contract["readBackRoute"]["mutation"], false);
    assert_eq!(contract["detailReadRoute"]["method"], "GET");
    assert_eq!(
        contract["detailReadRoute"]["path"],
        "/api/v2/seed-inventory/adjustments/{publicId}"
    );
    assert_eq!(
        contract["detailReadRoute"]["rustPath"],
        "/api/v2/seed-inventory/adjustments/{public_id}"
    );
    assert_eq!(contract["detailReadRoute"]["publicRouteRegistered"], true);
    assert_eq!(contract["detailReadRoute"]["rustRouteRegistered"], true);
    assert_eq!(
        contract["detailReadRoute"]["requiredPermission"].as_str(),
        Some(read_plan.required_permission.as_str())
    );
    assert_eq!(
        string_array(&contract["detailReadRoute"], "requiredDataScopes"),
        vec!["organization", "lot"]
    );
    assert_eq!(contract["detailReadRoute"]["auditEmission"], false);
    assert_eq!(contract["detailReadRoute"]["mutation"], false);
    assert_eq!(contract["implementationStatus"]["routeLive"], true);
    assert_eq!(
        contract["implementationStatus"]["publicRouteRegistered"],
        true
    );
    assert_eq!(
        contract["implementationStatus"]["rustRouteRegistered"],
        true
    );

    assert_eq!(gate["writeCandidate"]["status"], "guarded-route-live");
    assert_eq!(
        gate["writeCandidate"]["routeCandidate"],
        contract["routeCandidate"]
    );
    assert_eq!(gate["writeCandidate"]["publicRouteRegistered"], true);
    assert_eq!(gate["writeCandidate"]["rustRouteRegistered"], true);
    assert_eq!(
        gate["writeCandidate"]["capabilityId"],
        contract["capabilityId"]
    );
    assert_eq!(
        gate["writeCandidate"]["requiredPermission"],
        contract["requiredPermission"]
    );
    assert_eq!(gate["writeCandidate"]["auditEvent"], contract["auditEvent"]);
    assert_eq!(
        string_array(&gate["writeCandidate"], "requiredDataScopes"),
        string_array(&contract, "requiredDataScopes")
    );

    assert_eq!(contract["publicIdStrategy"]["type"], "UUID7");
    assert_eq!(contract["publicIdStrategy"]["internalPrimaryKey"], "BIGINT");
    assert_eq!(contract["publicIdStrategy"]["migrationNow"], true);
    assert_eq!(
        contract["publicIdStrategy"]["migrationScope"],
        "new ledger table only"
    );
    assert_eq!(
        contract["publicIdStrategy"]["existingTablePublicIdMigration"],
        false
    );
    assert_eq!(
        contract["publicIdStrategy"]["bigIntPrimaryKeyMigration"],
        false
    );
    assert_eq!(
        contract["dataModelDesign"]["status"],
        "migration-added-internal-ledger"
    );
    assert_eq!(
        contract["dataModelDesign"]["migration"],
        "backend/alembic/versions/20260630_0100_add_seedlot_inventory_adjustments.py"
    );
    assert_eq!(contract["dataModelDesign"]["appendOnly"], true);
    assert_eq!(contract["implementationStatus"]["migrationAdded"], true);
    assert_eq!(
        contract["implementationStatus"]["internalLedgerImplemented"],
        true
    );
    assert_eq!(
        contract["implementationStatus"]["canonicalAuditLogEmissionImplemented"],
        true
    );
    assert_eq!(
        contract["implementationStatus"]["publicRouteRegistered"],
        true
    );
    assert_eq!(
        contract["implementationStatus"]["rustRouteRegistered"],
        true
    );
    assert_eq!(contract["implementationStatus"]["routeLive"], true);
    assert_eq!(
        contract["implementationStatus"]["existingTablesAltered"],
        false
    );
    assert_eq!(
        contract["implementationStatus"]["existingTableUuid7Migration"],
        false
    );
    assert_eq!(
        contract["implementationStatus"]["destructiveInventoryMutation"],
        false
    );
    assert_eq!(
        contract["rollbackAndReversalPolicy"]["destructiveUpdate"],
        false
    );
    assert_eq!(
        contract["rollbackAndReversalPolicy"]["physicalDelete"],
        false
    );

    let read_routes = read_route_inventory["routes"]
        .as_array()
        .expect("read route inventory routes");
    assert!(
        read_routes.iter().any(|route| route["method"] == "GET"
            && route["path"] == "/api/v2/seed-inventory/adjustments"),
        "read route inventory should include the guarded seedlot adjustment history read route"
    );
    assert!(
        read_routes.iter().any(|route| route["method"] == "GET"
            && route["path"] == "/api/v2/seed-inventory/adjustments/{public_id}"
            && route["normalizedPath"] == "/api/v2/seed-inventory/adjustments/{publicId}"),
        "read route inventory should include the guarded seedlot adjustment detail read route"
    );

    let write_routes = write_route_inventory["routes"]
        .as_array()
        .expect("write route inventory routes");
    assert_eq!(write_routes.len(), 1);
    assert_eq!(
        write_routes[0]["method"], "POST",
        "write route inventory should expose the guarded POST route"
    );
    assert_eq!(
        write_routes[0]["path"], "/api/v2/seed-inventory/adjustments",
        "write route inventory should only expose the seedlot adjustment route"
    );

    assert!(
        write_routes
            .iter()
            .any(|route| route["path"] == "/api/v2/seed-inventory/adjustments"),
        "guarded seedlot adjustment write route must be in Rust write inventory"
    );

    let server_source = read("crates/bijmantra-server/src/lib.rs");
    let app_source = rust_app_router_source(&server_source);
    assert!(
        app_source.contains("/api/v2/seed-inventory/adjustments"),
        "Rust server source must register the guarded seedlot adjustment route"
    );
    assert!(
        app_source.contains("post(seedlot_inventory_adjustments_create)"),
        "Rust server source should register the guarded write route with POST"
    );
    assert!(
        app_source.contains("get(seedlot_inventory_adjustments_list)"),
        "Rust server source should register the guarded history route with GET"
    );
    assert!(
        app_source.contains("get(seedlot_inventory_adjustments_detail)"),
        "Rust server source should register the guarded detail route with GET"
    );

    let accepted_limits = declaration["acceptedLimits"]
        .as_array()
        .expect("accepted limits");
    assert!(
        accepted_limits.iter().any(|limit| limit
            .as_str()
            .is_some_and(|limit| limit.contains("No public Rust write route"))),
        "Rust beta declaration should keep public Rust writes disabled"
    );
    assert!(
        declaration["declarationText"]
            .as_str()
            .is_some_and(|text| text.contains("guarded POST /api/v2/seed-inventory/adjustments")),
        "Rust beta declaration should note the later guarded write slice"
    );
}

#[test]
fn seedlot_inventory_adjustment_migration_matches_internal_ledger_contract() {
    let migration =
        read("backend/alembic/versions/20260630_0100_add_seedlot_inventory_adjustments.py");
    let contract =
        read_json("contracts/fastapi-parity/seedlot-inventory-adjustment-write-contract.json");

    assert_eq!(
        contract["dataModelDesign"]["migration"],
        "backend/alembic/versions/20260630_0100_add_seedlot_inventory_adjustments.py"
    );

    for required in [
        "revision = \"20260630_0100\"",
        "down_revision = \"20260529_0100\"",
        "TABLE_NAME = \"seedlot_inventory_adjustments\"",
        "sa.Column(\"id\", sa.BigInteger(), sa.Identity(), nullable=False)",
        "sa.Column(\"public_id\", postgresql.UUID(as_uuid=True), nullable=False)",
        "sa.Column(\"organization_id\", sa.BigInteger(), nullable=False)",
        "sa.Column(\"seedlot_id\", sa.BigInteger(), nullable=True)",
        "sa.Column(\"seedlot_db_id\", sa.Text(), nullable=False)",
        "sa.Column(\"quantity_delta\", sa.Numeric(20, 6), nullable=False)",
        "\"metadata\",",
        "postgresql.JSONB(astext_type=sa.Text())",
        "server_default=sa.text(\"'{}'::jsonb\")",
        "sa.Column(\"reversal_of_public_id\", postgresql.UUID(as_uuid=True), nullable=True)",
        "sa.Column(\"reversed_at\", sa.DateTime(timezone=True), nullable=True)",
        "sa.ForeignKeyConstraint([\"organization_id\"], [\"organizations.id\"])",
        "sa.ForeignKeyConstraint([\"seedlot_id\"], [\"seedlots.id\"])",
        "sa.ForeignKeyConstraint([\"actor_user_id\"], [\"users.id\"])",
        "sa.UniqueConstraint(\"public_id\", name=\"uq_seedlot_inventory_adjustments_public_id\")",
        "\"organization_id\",",
        "\"actor_user_id\",",
        "\"action\",",
        "\"idempotency_key\",",
        "ck_seedlot_inventory_adjustments_public_id_uuid7",
        "ck_seedlot_inventory_adjustments_quantity_nonzero",
        "ck_seedlot_inventory_adjustments_reason_nonempty",
        "ck_seedlot_inventory_adjustments_audit_event",
        "ALTER TABLE {TABLE_NAME} ENABLE ROW LEVEL SECURITY",
    ] {
        assert_contains(&migration, required, "seedlot adjustment migration");
    }

    for forbidden in [
        "op.add_column(\"seedlots\"",
        "op.add_column('seedlots'",
        "ALTER TABLE seedlots ADD COLUMN",
        "UPDATE seedlots SET",
        "sa.Column(\"deleted_at\"",
        "sa.Column(\"deleted_by_user_id\"",
    ] {
        assert!(
            !migration.contains(forbidden),
            "seedlot adjustment migration must not alter seedlots: {forbidden}"
        );
    }
}

#[test]
fn frontend_smoke_artifact_matches_client_and_vite() {
    let gate = read_json("contracts/fastapi-parity/rust-frontend-beta-smoke.json");
    let package_json = read("frontend/package.json");
    let smoke = read("frontend/scripts/rust-beta-smoke.mjs");
    let vite = read("frontend/vite.config.ts");
    let config = read("frontend/src/config.ts");
    let client = read("frontend/src/lib/api/core/client.ts");
    let germplasm = read("frontend/src/lib/api/brapi/germplasm/germplasm.ts");
    let seedlots = read("frontend/src/lib/api/brapi/germplasm/seed-lots.ts");
    let crosses = read("frontend/src/lib/api/brapi/germplasm/crosses.ts");

    assert_eq!(gate["command"], "cd frontend && bun run rust-beta-smoke");
    assert_contains(
        &package_json,
        "\"rust-beta-smoke\"",
        "frontend package scripts",
    );
    assert_contains(
        &smoke,
        "Rust beta frontend smoke passed",
        "frontend smoke script",
    );
    assert_contains(&vite, "'/brapi'", "Vite config");
    assert_contains(&vite, "http://localhost:8000", "Vite config");
    assert_contains(&config, "VITE_API_URL", "frontend config");
    assert_contains(&config, "VITE_API_BASE_URL", "frontend config");
    assert_contains(&client, "!endpoint.startsWith('/brapi/v2')", "API client");
    assert_contains(&client, "this.setToken(null)", "API client");
    assert_contains(&germplasm, "/brapi/v2/germplasm", "germplasm client");
    assert_contains(&seedlots, "/brapi/v2/seedlots", "seedlot client");
    assert_contains(&crosses, "/brapi/v2/crosses", "cross client");
    assert_contains(
        &crosses,
        "/brapi/v2/plannedcrosses",
        "planned-cross read client",
    );
}

#[test]
fn milestone_tracker_has_no_pending_or_not_started_rows() {
    let milestone = read("docs/rust-major-milestone-330-slices.md");
    assert_contains(
        &milestone,
        "Summary: Completed 330, Pending 0, Not started 0.",
        "milestone summary",
    );

    let mut rows = 0usize;
    let mut non_completed = Vec::new();
    for line in milestone.lines() {
        if !line.starts_with('|') {
            continue;
        }
        let columns: Vec<_> = line.split('|').map(str::trim).collect();
        if columns.len() < 5 || columns[1].parse::<u16>().is_err() {
            continue;
        }
        rows += 1;
        if columns[3] != "Completed" {
            non_completed.push(line.to_owned());
        }
    }

    assert_eq!(rows, 330, "milestone tracker should keep 330 slice rows");
    assert!(
        non_completed.is_empty(),
        "all milestone rows should be Completed: {non_completed:#?}"
    );
}

#[test]
fn rust_api_beta_declaration_links_all_full_330_gates() {
    let declaration = read_json("contracts/fastapi-parity/rust-api-beta-declaration.json");
    let status_doc = read("contracts/fastapi-parity/read-route-status.md");
    let gates = declaration["gates"].as_array().expect("declaration gates");
    let declared_gate_paths: BTreeSet<_> = gates
        .iter()
        .map(|value| value.as_str().expect("gate should be string"))
        .collect();

    assert_eq!(declaration["status"], "declared");
    for required in [
        "contracts/fastapi-parity/rust-live-db-operations-gate.json",
        "contracts/fastapi-parity/rust-cross-os-gate.json",
        "contracts/fastapi-parity/rust-quality-gate.json",
        "contracts/fastapi-parity/rust-write-readiness-gate.json",
        "contracts/fastapi-parity/rust-frontend-beta-smoke.json",
        "contracts/fastapi-parity/rust-packaging-gate.json",
    ] {
        assert!(
            declared_gate_paths.contains(required),
            "declaration should link {required}"
        );
        assert_repo_path(required);
        assert_contains(&status_doc, required, "read route status doc");
    }

    let declaration_text = declaration["declarationText"]
        .as_str()
        .expect("declaration text");
    assert_contains(
        declaration_text,
        "Rust API Beta milestone 330",
        "declaration",
    );
    assert_contains(
        declaration_text,
        "Public write routes remain disabled",
        "declaration",
    );
}
