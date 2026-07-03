use std::collections::BTreeSet;
use std::error::Error;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use axum::Router;
use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use bijmantra_core::{
    IdempotencyKey, PlatformCapabilityAccessContext, PublicId, SEEDLOT_INVENTORY_ADJUST_PERMISSION,
    SEEDLOT_INVENTORY_READ_PERMISSION, SEEDLOT_TRACEABILITY_CAPABILITY_ID,
    SeedlotInventoryAdjustmentCreate, SeedlotInventoryAdjustmentType,
    SeedlotInventoryAdjustmentUnit,
};
use bijmantra_server::{AppState, AuthConfig, DataStore, app};
use jsonwebtoken::{Algorithm, EncodingKey, Header, encode};
use serde::Serialize;
use serde_json::{Value, json};
use sqlx::postgres::PgPoolOptions;
use sqlx::types::Json;
use sqlx::{PgPool, Row};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tower::ServiceExt;

type TestError = Box<dyn Error + Send + Sync>;
type TestResult<T = ()> = Result<T, TestError>;

const KEYCLOAK_ISSUER: &str = "http://localhost:8084/realms/bijmantra";
const KEYCLOAK_AUDIENCE: &str = "bijmantra-api";
const KEYCLOAK_SUBJECT: &str = "00000000-0000-4000-8000-000000000042";
const KEYCLOAK_TOKEN: &str = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJpai10ZXN0LWtleSJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTQwMDAtODAwMC0wMDAwMDAwMDAwNDIiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwODQvcmVhbG1zL2Jpam1hbnRyYSIsImF1ZCI6ImJpam1hbnRyYS1hcGkiLCJleHAiOjQxMDI0NDQ4MDB9.AmpxfCs96U6zQkQCF6GMea0QQu-SBpC9AmjA40IlbseNOV27OZaeBkRbYRfXOFsBpL-Tij3dFI4QYf3934vZEBp8KRW0xim5A2NIyhO7YQkA4UjluYHSqfA_QDqDUKIm-RGau6JRC2iKlZa6spJphIeHaD7pIgJdTMjim1nWyMTUse1zUzakZ44CZHgf_LCFoAZlr5AEzIRo8PKy6Sxqn76SwD_XHR3KWMtiwoWTOQR7eI3oK6zoYPxfXo3F8krWH-qWtTZbMdnXu4b80j4jvpqkQ7XY63T_3CGOZnTgH0uExQ_ch6frffIL-4JTU5cesbsizE1r_pcoDx3SepUOWQ";
const PAGINATION_LOAD_EXTRA_ROWS: usize = 37;
const EXPECTED_ALEMBIC_HEAD: &str = "20260630_0100";

#[derive(Debug, Serialize)]
struct TestClaims {
    sub: String,
    organization_id: i64,
    is_superuser: bool,
    exp: i64,
}

#[derive(Debug)]
struct SeededTenant {
    org_id: i64,
    user_id: i64,
    inactive_user_id: i64,
    program_db_id: String,
    secondary_program_db_id: String,
    program_name: String,
    program_abbreviation: String,
    location_db_id: String,
    null_coordinate_location_db_id: String,
    location_type: String,
    trial_db_id: String,
    inactive_trial_db_id: String,
    trial_start_date: String,
    trial_end_date: String,
    study_db_id: String,
    inactive_study_db_id: String,
    null_observation_levels_study_db_id: String,
    study_start_date: String,
    study_end_date: String,
    season_db_id: String,
    previous_season_db_id: String,
    season_year: i32,
    previous_season_year: i32,
    person_db_id: String,
    secondary_person_db_id: String,
    person_first_name: String,
    person_last_name: String,
    secondary_person_first_name: String,
    secondary_person_last_name: String,
    list_db_id: String,
    secondary_list_db_id: String,
    list_name: String,
    secondary_list_name: String,
    list_type: String,
    secondary_list_type: String,
    list_source: String,
    secondary_list_source: String,
    ontology_db_id: String,
    secondary_ontology_db_id: String,
    ontology_name: String,
    secondary_ontology_name: String,
    germplasm_db_id: String,
    secondary_germplasm_db_id: String,
    germplasm_name: String,
    secondary_germplasm_name: String,
    germplasm_common_crop_name: String,
    secondary_germplasm_common_crop_name: String,
    germplasm_genus: String,
    secondary_germplasm_genus: String,
    germplasm_species: String,
    secondary_germplasm_species: String,
    attribute_db_id: String,
    secondary_attribute_db_id: String,
    attribute_name: String,
    secondary_attribute_name: String,
    attribute_category: String,
    secondary_attribute_category: String,
    attribute_value_db_id: String,
    secondary_attribute_value_db_id: String,
    breeding_method_db_id: String,
    secondary_breeding_method_db_id: String,
    breeding_method_name: String,
    secondary_breeding_method_name: String,
    breeding_method_abbreviation: String,
    secondary_breeding_method_abbreviation: String,
    observation_variable_db_id: String,
    secondary_observation_variable_db_id: String,
    observation_variable_name: String,
    observation_unit_db_id: String,
    secondary_observation_unit_db_id: String,
    observation_db_id: String,
    secondary_observation_db_id: String,
    study_id: i64,
    germplasm_id: i64,
    secondary_germplasm_id: i64,
    trait_class: String,
    secondary_trait_class: String,
    trait_common_crop_name: String,
    secondary_trait_common_crop_name: String,
    method_db_id: String,
    secondary_method_db_id: String,
    method_name: String,
    method_class: String,
    secondary_method_class: String,
    scale_db_id: String,
    secondary_scale_db_id: String,
    scale_name: String,
    scale_data_type: String,
    secondary_scale_data_type: String,
    crossing_project_db_id: String,
    cross_db_id: String,
    planned_cross_db_id: String,
    seedlot_db_id: String,
    secondary_seedlot_db_id: String,
    seedlot_name: String,
    secondary_seedlot_name: String,
    transaction_db_id: String,
    secondary_transaction_db_id: String,
    reference_set_db_id: String,
    secondary_reference_set_db_id: String,
    variant_set_db_id: String,
    secondary_variant_set_db_id: String,
    variant_set_name: String,
    secondary_variant_set_name: String,
    call_set_db_id: String,
    secondary_call_set_db_id: String,
    call_set_name: String,
    secondary_call_set_name: String,
    sample_db_id: String,
    secondary_sample_db_id: String,
    map_db_id: String,
    secondary_map_db_id: String,
    map_name: String,
    secondary_map_name: String,
    linkage_group_name: String,
    secondary_linkage_group_name: String,
    marker_position_db_id: String,
    secondary_marker_position_db_id: String,
    marker_variant_db_id: String,
    secondary_marker_variant_db_id: String,
    marker_variant_name: String,
    secondary_marker_variant_name: String,
}

#[derive(Debug)]
struct SeededData {
    tenant_a: SeededTenant,
    tenant_b: SeededTenant,
}

#[test]
fn alembic_version_diagnostics_accept_expected_head() {
    let versions = vec![EXPECTED_ALEMBIC_HEAD.to_string()];

    validate_alembic_versions(&versions).expect("expected current Alembic head to pass");
}

#[test]
fn alembic_version_diagnostics_explain_missing_table_or_rows() {
    let versions: Vec<String> = Vec::new();

    let message = validate_alembic_versions(&versions)
        .unwrap_err()
        .to_string();

    assert!(message.contains("missing alembic_version"));
    assert!(message.contains("run Alembic first"));
}

#[test]
fn alembic_version_diagnostics_explain_empty_versions() {
    let versions = vec!["  ".to_string()];

    let message = validate_alembic_versions(&versions)
        .unwrap_err()
        .to_string();

    assert!(message.contains("empty Alembic version"));
}

#[test]
fn alembic_version_diagnostics_explain_stale_or_wrong_head() {
    let versions = vec!["20260401_0001".to_string()];

    let message = validate_alembic_versions(&versions)
        .unwrap_err()
        .to_string();

    assert!(message.contains("Alembic head mismatch"));
    assert!(message.contains("expected 20260630_0100"));
    assert!(message.contains("got 20260401_0001"));
    assert!(message.contains("BIJMANTRA_LIVE_DATABASE_URL"));
    assert!(message.contains("uv run alembic upgrade head"));
}

#[test]
fn alembic_version_diagnostics_explain_multiple_heads() {
    let versions = vec![
        "20260401_0001".to_string(),
        EXPECTED_ALEMBIC_HEAD.to_string(),
    ];

    let message = validate_alembic_versions(&versions)
        .unwrap_err()
        .to_string();

    assert!(message.contains("Alembic head mismatch"));
    assert!(message.contains("got 20260401_0001, 20260630_0100"));
}

#[test]
fn expected_alembic_head_matches_migration_graph() -> TestResult {
    let heads = alembic_migration_heads()?;

    assert_eq!(
        heads,
        BTreeSet::from([EXPECTED_ALEMBIC_HEAD.to_string()]),
        "Rust live fixture expected head should match backend Alembic graph heads"
    );
    Ok(())
}

#[tokio::test]
async fn live_brapi_reads_seeded_postgres_rows_with_tenant_isolation() -> TestResult {
    let Some(database_url) = live_database_url() else {
        eprintln!("skipping live Postgres BrAPI test; set BIJMANTRA_LIVE_DATABASE_URL");
        return Ok(());
    };

    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await?;
    ensure_migrated_database(&pool).await?;

    let suffix = unique_suffix()?;
    let prefix = format!("codex-live-{suffix}");
    cleanup_seed_data(&pool, &prefix).await?;
    assert_no_seed_residue(&pool, &prefix).await?;
    let seeded = seed_brapi_fixture(&pool, &prefix).await?;

    let secret = format!("live-test-secret-{suffix}");
    let router = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
        .with_auth_config(AuthConfig::local_hs256(&secret))
        .with_data_store(DataStore::from_database_url(&database_url)));
    let token = access_token(&secret, seeded.tenant_a.user_id, seeded.tenant_a.org_id)?;

    let result = async {
        assert_live_auth_route_rejections(&router, &secret, &seeded).await?;
        assert_live_org_zero_superuser_scope(&router, &secret, &seeded).await?;
        assert_live_keycloak_route_mapping(&database_url, &seeded).await?;
        assert_seeded_brapi_reads(&router, &token, &seeded).await?;
        seed_pagination_load_rows(&pool, &prefix, &seeded.tenant_a).await?;
        assert_live_pagination_load_windows(&router, &token, &seeded, &prefix).await
    }
    .await;
    cleanup_seed_data(&pool, &prefix).await?;
    assert_no_seed_residue(&pool, &prefix).await?;
    result
}

#[tokio::test]
async fn live_seedlot_inventory_adjustment_internal_ledger_is_append_only() -> TestResult {
    let Some(database_url) = live_database_url() else {
        eprintln!("skipping live seedlot adjustment ledger test; set BIJMANTRA_LIVE_DATABASE_URL");
        return Ok(());
    };

    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await?;
    ensure_migrated_database(&pool).await?;

    let suffix = unique_suffix()?;
    let prefix = format!("codex-live-ledger-{suffix}");
    cleanup_seed_data(&pool, &prefix).await?;
    assert_no_seed_residue(&pool, &prefix).await?;
    let seeded = seed_brapi_fixture(&pool, &prefix).await?;
    let store = DataStore::from_database_url(&database_url);
    let access_context = PlatformCapabilityAccessContext::new(
        seeded.tenant_a.org_id,
        seeded.tenant_a.user_id,
        &[SEEDLOT_TRACEABILITY_CAPABILITY_ID],
        &[SEEDLOT_INVENTORY_ADJUST_PERMISSION],
        &["organization", "lot"],
    );

    let result = async {
        let before_count = seedlot_count_text(
            &pool,
            seeded.tenant_a.org_id,
            &seeded.tenant_a.seedlot_db_id,
        )
        .await?;
        let public_id = PublicId::new_uuid7();
        let idempotency_key = IdempotencyKey::parse(format!("{prefix}:adjustment:01"))?;
        let command = SeedlotInventoryAdjustmentCreate::new(
            public_id,
            idempotency_key.clone(),
            seeded.tenant_a.org_id,
            &seeded.tenant_a.seedlot_db_id,
            SeedlotInventoryAdjustmentType::Correction,
            "-3",
            SeedlotInventoryAdjustmentUnit::Seeds,
            "live ledger cycle count correction",
            seeded.tenant_a.user_id,
            None,
            Default::default(),
        )?;

        let created = store
            .create_seedlot_inventory_adjustment_authorized_internal(
                &access_context,
                command.clone(),
            )
            .await
            .map_err(debug_error)?;
        assert_eq!(created.public_id, public_id);
        assert_eq!(created.seedlot_db_id, seeded.tenant_a.seedlot_db_id);
        assert_eq!(created.quantity_delta, "-3.000000");
        assert!(created.seedlot_id.is_some());

        let replay = store
            .create_seedlot_inventory_adjustment_authorized_internal(
                &access_context,
                command.clone(),
            )
            .await
            .map_err(debug_error)?;
        assert_eq!(replay.id, created.id);

        let conflicting_command = SeedlotInventoryAdjustmentCreate::new(
            PublicId::new_uuid7(),
            idempotency_key.clone(),
            seeded.tenant_a.org_id,
            &seeded.tenant_a.seedlot_db_id,
            SeedlotInventoryAdjustmentType::Correction,
            "-4",
            SeedlotInventoryAdjustmentUnit::Seeds,
            "live ledger conflicting correction",
            seeded.tenant_a.user_id,
            None,
            Default::default(),
        )?;
        let conflict = store
            .create_seedlot_inventory_adjustment_authorized_internal(
                &access_context,
                conflicting_command,
            )
            .await;
        assert!(matches!(
            conflict,
            Err(bijmantra_server::SeedlotInventoryAdjustmentWriteError::IdempotencyConflict)
        ));

        let by_public_id = store
            .get_seedlot_inventory_adjustment_by_public_id_internal(
                seeded.tenant_a.org_id,
                public_id,
            )
            .await
            .map_err(debug_error)?
            .expect("created adjustment should be found by public id");
        assert_eq!(by_public_id.id, created.id);

        let by_idempotency = store
            .get_seedlot_inventory_adjustment_by_idempotency_key_internal(
                seeded.tenant_a.org_id,
                seeded.tenant_a.user_id,
                &idempotency_key,
            )
            .await
            .map_err(debug_error)?
            .expect("created adjustment should be found by idempotency key");
        assert_eq!(by_idempotency.id, created.id);

        let reversal_public_id = PublicId::new_uuid7();
        let reversal_idempotency_key =
            IdempotencyKey::parse(format!("{prefix}:adjustment:reversal:01"))?;
        let reversal = store
            .reverse_seedlot_inventory_adjustment_authorized_internal(
                &access_context,
                seeded.tenant_a.org_id,
                seeded.tenant_a.user_id,
                created.public_id,
                reversal_public_id,
                reversal_idempotency_key.clone(),
                "live ledger reversal",
            )
            .await
            .map_err(debug_error)?;
        assert_eq!(reversal.reversal_of_public_id, Some(created.public_id));
        assert_eq!(reversal.quantity_delta, "3.000000");

        let reversal_replay = store
            .reverse_seedlot_inventory_adjustment_authorized_internal(
                &access_context,
                seeded.tenant_a.org_id,
                seeded.tenant_a.user_id,
                created.public_id,
                reversal_public_id,
                reversal_idempotency_key,
                "live ledger reversal",
            )
            .await
            .map_err(debug_error)?;
        assert_eq!(reversal_replay.id, reversal.id);

        let original_after_reversal = store
            .get_seedlot_inventory_adjustment_by_public_id_internal(
                seeded.tenant_a.org_id,
                created.public_id,
            )
            .await
            .map_err(debug_error)?
            .expect("original adjustment should remain after reversal");
        assert!(original_after_reversal.reversed_at.is_some());

        let second_reversal = store
            .reverse_seedlot_inventory_adjustment_authorized_internal(
                &access_context,
                seeded.tenant_a.org_id,
                seeded.tenant_a.user_id,
                created.public_id,
                PublicId::new_uuid7(),
                IdempotencyKey::parse(format!("{prefix}:adjustment:reversal:02"))?,
                "second live ledger reversal should be rejected",
            )
            .await;
        assert!(matches!(
            second_reversal,
            Err(bijmantra_server::SeedlotInventoryAdjustmentWriteError::AlreadyReversed)
        ));

        let after_count = seedlot_count_text(
            &pool,
            seeded.tenant_a.org_id,
            &seeded.tenant_a.seedlot_db_id,
        )
        .await?;
        assert_eq!(
            after_count, before_count,
            "internal adjustment ledger must not mutate seedlots.count"
        );
        assert_eq!(
            seedlot_adjustment_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            2,
            "created adjustment plus reversal should both remain append-only"
        );
        assert_eq!(
            seedlot_adjustment_audit_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            2,
            "created adjustment plus reversal should emit canonical audit rows"
        );

        Ok(())
    }
    .await;

    cleanup_seed_data(&pool, &prefix).await?;
    assert_no_seed_residue(&pool, &prefix).await?;
    result
}

#[tokio::test]
async fn live_seedlot_inventory_adjustment_route_is_guarded_and_append_only() -> TestResult {
    let Some(database_url) = live_database_url() else {
        eprintln!("skipping live seedlot adjustment route test; set BIJMANTRA_LIVE_DATABASE_URL");
        return Ok(());
    };

    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await?;
    ensure_migrated_database(&pool).await?;

    let suffix = unique_suffix()?;
    let prefix = format!("codex-live-route-{suffix}");
    cleanup_seed_data(&pool, &prefix).await?;
    assert_no_seed_residue(&pool, &prefix).await?;
    let seeded = seed_brapi_fixture(&pool, &prefix).await?;
    let secret = format!("live-route-secret-{suffix}");
    let router = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
        .with_auth_config(AuthConfig::local_hs256(&secret))
        .with_data_store(DataStore::from_database_url(&database_url)));
    let tenant_a_token = access_token(&secret, seeded.tenant_a.user_id, seeded.tenant_a.org_id)?;
    let tenant_b_token = access_token(&secret, seeded.tenant_b.user_id, seeded.tenant_b.org_id)?;

    let result = async {
        delete_capability_installation(
            &pool,
            seeded.tenant_a.org_id,
            SEEDLOT_TRACEABILITY_CAPABILITY_ID,
        )
        .await?;
        delete_capability_installation(
            &pool,
            seeded.tenant_b.org_id,
            SEEDLOT_TRACEABILITY_CAPABILITY_ID,
        )
        .await?;

        let seedlot_before = seedlot_count_text(
            &pool,
            seeded.tenant_a.org_id,
            &seeded.tenant_a.seedlot_db_id,
        )
        .await?;

        let (status, body) = get_json(
            &router,
            &tenant_b_token,
            "/api/v2/seed-inventory/adjustments",
        )
        .await?;
        require_status(
            status,
            StatusCode::FORBIDDEN,
            "missing capability seedlot adjustment history",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Seed lot traceability capability is not installed for this organization.",
        )?;
        let missing_capability_detail_uri = format!(
            "/api/v2/seed-inventory/adjustments/{}",
            PublicId::new_uuid7()
        );
        let (status, body) =
            get_json(&router, &tenant_b_token, &missing_capability_detail_uri).await?;
        require_status(
            status,
            StatusCode::FORBIDDEN,
            "missing capability seedlot adjustment detail",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Seed lot traceability capability is not installed for this organization.",
        )?;

        let missing_capability_request = json!({
            "publicId": PublicId::new_uuid7().to_string(),
            "idempotencyKey": format!("{prefix}:route:missing-capability"),
            "seedLotDbId": seeded.tenant_a.seedlot_db_id,
            "adjustmentType": "correction",
            "quantityDelta": "-1",
            "unit": "seeds",
            "reason": "missing capability",
            "metadata": {
                "scenario": "missing-capability"
            }
        });
        let (status, body) = post_json(
            &router,
            &tenant_b_token,
            "/api/v2/seed-inventory/adjustments",
            &missing_capability_request,
        )
        .await?;
        require_status(
            status,
            StatusCode::FORBIDDEN,
            "missing capability seedlot adjustment",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Seed lot traceability capability is not installed for this organization.",
        )?;

        upsert_capability_installation(
            &pool,
            seeded.tenant_b.org_id,
            SEEDLOT_TRACEABILITY_CAPABILITY_ID,
            seeded.tenant_b.user_id,
            &[],
            &["organization", "lot"],
        )
        .await?;

        let (status, body) = get_json(
            &router,
            &tenant_b_token,
            "/api/v2/seed-inventory/adjustments",
        )
        .await?;
        require_status(
            status,
            StatusCode::FORBIDDEN,
            "missing read permission seedlot adjustment history",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Missing required permission seedops.seed_lots.read.",
        )?;
        let missing_permission_detail_uri = format!(
            "/api/v2/seed-inventory/adjustments/{}",
            PublicId::new_uuid7()
        );
        let (status, body) =
            get_json(&router, &tenant_b_token, &missing_permission_detail_uri).await?;
        require_status(
            status,
            StatusCode::FORBIDDEN,
            "missing read permission seedlot adjustment detail",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Missing required permission seedops.seed_lots.read.",
        )?;

        let missing_permission_request = json!({
            "publicId": PublicId::new_uuid7().to_string(),
            "idempotencyKey": format!("{prefix}:route:missing-permission"),
            "seedLotDbId": seeded.tenant_a.seedlot_db_id,
            "adjustmentType": "correction",
            "quantityDelta": "-1",
            "unit": "seeds",
            "reason": "missing permission",
            "metadata": {
                "scenario": "missing-permission"
            }
        });
        let (status, body) = post_json(
            &router,
            &tenant_b_token,
            "/api/v2/seed-inventory/adjustments",
            &missing_permission_request,
        )
        .await?;
        require_status(
            status,
            StatusCode::FORBIDDEN,
            "missing permission seedlot adjustment",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Missing required permission seedops.seed_lots.adjust.",
        )?;

        upsert_capability_installation(
            &pool,
            seeded.tenant_b.org_id,
            SEEDLOT_TRACEABILITY_CAPABILITY_ID,
            seeded.tenant_b.user_id,
            &[SEEDLOT_INVENTORY_ADJUST_PERMISSION],
            &["organization", "lot"],
        )
        .await?;

        let tenant_scope_request = json!({
            "publicId": PublicId::new_uuid7().to_string(),
            "idempotencyKey": format!("{prefix}:route:tenant-scope"),
            "seedLotDbId": seeded.tenant_a.seedlot_db_id,
            "adjustmentType": "correction",
            "quantityDelta": "-1",
            "unit": "seeds",
            "reason": "tenant scope",
            "metadata": {
                "scenario": "tenant-scope"
            }
        });
        let (status, body) = post_json(
            &router,
            &tenant_b_token,
            "/api/v2/seed-inventory/adjustments",
            &tenant_scope_request,
        )
        .await?;
        require_status(
            status,
            StatusCode::NOT_FOUND,
            "tenant scope seedlot adjustment",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Seed lot not found inside current organization.",
        )?;

        upsert_capability_installation(
            &pool,
            seeded.tenant_a.org_id,
            SEEDLOT_TRACEABILITY_CAPABILITY_ID,
            seeded.tenant_a.user_id,
            &[SEEDLOT_INVENTORY_ADJUST_PERMISSION],
            &["organization", "lot"],
        )
        .await?;

        let public_id = PublicId::new_uuid7();
        let idempotency_key = format!("{prefix}:route:happy:01");
        let happy_request = json!({
            "publicId": public_id.to_string(),
            "idempotencyKey": idempotency_key,
            "seedLotDbId": seeded.tenant_a.seedlot_db_id,
            "adjustmentType": "correction",
            "quantityDelta": "-3",
            "unit": "seeds",
            "reason": "route happy path",
            "metadata": {
                "scenario": "happy-path"
            }
        });
        let (status, body) = post_json(
            &router,
            &tenant_a_token,
            "/api/v2/seed-inventory/adjustments",
            &happy_request,
        )
        .await?;
        require_status(status, StatusCode::CREATED, "seedlot adjustment create")?;
        require_json_bool(&body, "/success", true)?;
        require_json_string(&body, "/adjustment/publicId", &public_id.to_string())?;
        require_json_string(
            &body,
            "/adjustment/seedLotDbId",
            &seeded.tenant_a.seedlot_db_id,
        )?;
        require_json_string(&body, "/adjustment/resultingLedgerStatus", "recorded")?;
        require_json_string(&body, "/audit/event", "seed_lot.adjusted")?;
        require_json_u64(&body, "/audit/actorUserId", seeded.tenant_a.user_id as u64)?;
        require_json_u64(
            &body,
            "/audit/organizationId",
            seeded.tenant_a.org_id as u64,
        )?;

        assert_eq!(
            seedlot_adjustment_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            1,
            "route happy path should append one ledger row"
        );
        assert_eq!(
            seedlot_adjustment_audit_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            1,
            "route happy path should emit one canonical audit row"
        );

        let (status, replay) = post_json(
            &router,
            &tenant_a_token,
            "/api/v2/seed-inventory/adjustments",
            &happy_request,
        )
        .await?;
        require_status(status, StatusCode::OK, "idempotent replay")?;
        require_json_string(&replay, "/adjustment/publicId", &public_id.to_string())?;

        let conflict_request = json!({
            "publicId": PublicId::new_uuid7().to_string(),
            "idempotencyKey": happy_request["idempotencyKey"].as_str().unwrap(),
            "seedLotDbId": seeded.tenant_a.seedlot_db_id,
            "adjustmentType": "correction",
            "quantityDelta": "-4",
            "unit": "seeds",
            "reason": "route conflicting correction",
            "metadata": {
                "scenario": "conflict"
            }
        });
        let (status, conflict) = post_json(
            &router,
            &tenant_a_token,
            "/api/v2/seed-inventory/adjustments",
            &conflict_request,
        )
        .await?;
        require_status(status, StatusCode::CONFLICT, "idempotency conflict")?;
        require_json_string(&conflict, "/error/code", "idempotency_conflict")?;

        assert_eq!(
            seedlot_adjustment_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            1,
            "replay and conflict should not add extra ledger rows"
        );
        assert_eq!(
            seedlot_adjustment_audit_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            1,
            "replay and conflict should not duplicate audit rows"
        );

        let (status, body) = get_json(
            &router,
            &tenant_a_token,
            "/api/v2/seed-inventory/adjustments",
        )
        .await?;
        require_status(
            status,
            StatusCode::FORBIDDEN,
            "missing read permission after seedlot adjustment create",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Missing required permission seedops.seed_lots.read.",
        )?;

        upsert_capability_installation(
            &pool,
            seeded.tenant_b.org_id,
            SEEDLOT_TRACEABILITY_CAPABILITY_ID,
            seeded.tenant_b.user_id,
            &[SEEDLOT_INVENTORY_READ_PERMISSION],
            &["organization", "lot"],
        )
        .await?;
        let tenant_scope_uri = format!(
            "/api/v2/seed-inventory/adjustments?seedLotDbId={}",
            seeded.tenant_a.seedlot_db_id
        );
        let (status, body) = get_json(&router, &tenant_b_token, &tenant_scope_uri).await?;
        require_status(
            status,
            StatusCode::OK,
            "tenant scoped seedlot adjustment history",
        )?;
        require_json_u64(&body, "/metadata/totalCount", 0)?;
        require_array_len(&body, "/adjustments", 0)?;
        let tenant_scope_detail_uri = format!("/api/v2/seed-inventory/adjustments/{public_id}");
        let (status, body) = get_json(&router, &tenant_b_token, &tenant_scope_detail_uri).await?;
        require_status(
            status,
            StatusCode::NOT_FOUND,
            "tenant scoped seedlot adjustment detail",
        )?;
        require_json_string(
            &body,
            "/error/message",
            "Seed lot inventory adjustment not found inside current organization.",
        )?;

        upsert_capability_installation(
            &pool,
            seeded.tenant_a.org_id,
            SEEDLOT_TRACEABILITY_CAPABILITY_ID,
            seeded.tenant_a.user_id,
            &[
                SEEDLOT_INVENTORY_READ_PERMISSION,
                SEEDLOT_INVENTORY_ADJUST_PERMISSION,
            ],
            &["organization", "lot"],
        )
        .await?;
        let second_public_id = PublicId::new_uuid7();
        let second_request = json!({
            "publicId": second_public_id.to_string(),
            "idempotencyKey": format!("{prefix}:route:happy:02"),
            "seedLotDbId": seeded.tenant_a.seedlot_db_id,
            "adjustmentType": "correction",
            "quantityDelta": "-2",
            "unit": "seeds",
            "reason": "route pagination order",
            "metadata": {
                "scenario": "pagination-order"
            }
        });
        let (status, second_body) = post_json(
            &router,
            &tenant_a_token,
            "/api/v2/seed-inventory/adjustments",
            &second_request,
        )
        .await?;
        require_status(
            status,
            StatusCode::CREATED,
            "second seedlot adjustment create",
        )?;
        require_json_string(
            &second_body,
            "/adjustment/publicId",
            &second_public_id.to_string(),
        )?;
        assert_eq!(
            seedlot_adjustment_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            2,
            "second route happy path should append one more ledger row"
        );
        assert_eq!(
            seedlot_adjustment_audit_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            2,
            "second route happy path should emit one more canonical audit row"
        );

        let history_uri = format!(
            "/api/v2/seed-inventory/adjustments?seedLotDbId={}&pageSize=10",
            seeded.tenant_a.seedlot_db_id
        );
        let (status, history) = get_json(&router, &tenant_a_token, &history_uri).await?;
        require_status(status, StatusCode::OK, "seedlot adjustment history")?;
        require_json_bool(&history, "/success", true)?;
        require_json_u64(&history, "/metadata/totalCount", 2)?;
        require_json_u64(&history, "/metadata/page", 0)?;
        require_json_u64(&history, "/metadata/pageSize", 10)?;
        require_array_len(&history, "/adjustments", 2)?;
        require_json_string(
            &history,
            "/adjustments/0/publicId",
            &second_public_id.to_string(),
        )?;
        require_json_string(
            &history,
            "/adjustments/0/seedLotDbId",
            &seeded.tenant_a.seedlot_db_id,
        )?;
        require_json_string(&history, "/adjustments/0/resultingLedgerStatus", "recorded")?;
        require_json_string(&history, "/adjustments/0/auditEvent", "seed_lot.adjusted")?;
        require_json_u64(
            &history,
            "/adjustments/0/actorUserId",
            seeded.tenant_a.user_id as u64,
        )?;
        require_json_u64(
            &history,
            "/adjustments/0/organizationId",
            seeded.tenant_a.org_id as u64,
        )?;
        let first_page_uri = format!(
            "/api/v2/seed-inventory/adjustments?seedLotDbId={}&pageSize=1",
            seeded.tenant_a.seedlot_db_id
        );
        let (status, first_page) = get_json(&router, &tenant_a_token, &first_page_uri).await?;
        require_status(
            status,
            StatusCode::OK,
            "seedlot adjustment history first page",
        )?;
        require_json_u64(&first_page, "/metadata/totalCount", 2)?;
        require_json_u64(&first_page, "/metadata/page", 0)?;
        require_json_u64(&first_page, "/metadata/pageSize", 1)?;
        require_array_len(&first_page, "/adjustments", 1)?;
        require_json_string(
            &first_page,
            "/adjustments/0/publicId",
            &second_public_id.to_string(),
        )?;
        let second_page_uri = format!(
            "/api/v2/seed-inventory/adjustments?seedLotDbId={}&pageSize=1&page=1",
            seeded.tenant_a.seedlot_db_id
        );
        let (status, second_page) = get_json(&router, &tenant_a_token, &second_page_uri).await?;
        require_status(
            status,
            StatusCode::OK,
            "seedlot adjustment history second page",
        )?;
        require_json_u64(&second_page, "/metadata/totalCount", 2)?;
        require_json_u64(&second_page, "/metadata/page", 1)?;
        require_json_u64(&second_page, "/metadata/pageSize", 1)?;
        require_array_len(&second_page, "/adjustments", 1)?;
        require_json_string(
            &second_page,
            "/adjustments/0/publicId",
            &public_id.to_string(),
        )?;
        let detail_uri = format!("/api/v2/seed-inventory/adjustments/{public_id}");
        let (status, detail) = get_json(&router, &tenant_a_token, &detail_uri).await?;
        require_status(status, StatusCode::OK, "seedlot adjustment detail")?;
        require_json_bool(&detail, "/success", true)?;
        require_json_string(&detail, "/adjustment/publicId", &public_id.to_string())?;
        require_json_string(
            &detail,
            "/adjustment/seedLotDbId",
            &seeded.tenant_a.seedlot_db_id,
        )?;
        require_json_string(&detail, "/adjustment/resultingLedgerStatus", "recorded")?;
        require_json_string(&detail, "/adjustment/auditEvent", "seed_lot.adjusted")?;
        require_json_u64(
            &detail,
            "/adjustment/actorUserId",
            seeded.tenant_a.user_id as u64,
        )?;
        require_json_u64(
            &detail,
            "/adjustment/organizationId",
            seeded.tenant_a.org_id as u64,
        )?;
        assert_eq!(
            seedlot_adjustment_audit_count(
                &pool,
                seeded.tenant_a.org_id,
                &seeded.tenant_a.seedlot_db_id
            )
            .await?,
            2,
            "history/detail reads should not emit extra audit rows"
        );

        let seedlot_after = seedlot_count_text(
            &pool,
            seeded.tenant_a.org_id,
            &seeded.tenant_a.seedlot_db_id,
        )
        .await?;
        assert_eq!(
            seedlot_before, seedlot_after,
            "route should not destructively mutate seedlots"
        );

        Ok(())
    }
    .await;

    delete_capability_installation(
        &pool,
        seeded.tenant_a.org_id,
        SEEDLOT_TRACEABILITY_CAPABILITY_ID,
    )
    .await?;
    delete_capability_installation(
        &pool,
        seeded.tenant_b.org_id,
        SEEDLOT_TRACEABILITY_CAPABILITY_ID,
    )
    .await?;
    cleanup_seed_data(&pool, &prefix).await?;
    assert_no_seed_residue(&pool, &prefix).await?;
    result
}

async fn assert_live_auth_route_rejections(
    router: &Router,
    secret: &str,
    seeded: &SeededData,
) -> TestResult {
    let wrong_org_token = access_token(secret, seeded.tenant_a.user_id, seeded.tenant_b.org_id)?;
    let (status, body) = get_json(router, &wrong_org_token, "/brapi/v2/programs").await?;
    require_status(status, StatusCode::UNAUTHORIZED, "wrong-org JWT")?;
    require_json_string(&body, "/detail", "Could not validate credentials")?;

    let missing_user_token = access_token(secret, -1, seeded.tenant_a.org_id)?;
    let (status, body) = get_json(router, &missing_user_token, "/brapi/v2/programs").await?;
    require_status(status, StatusCode::UNAUTHORIZED, "missing-user JWT")?;
    require_json_string(&body, "/detail", "Could not validate credentials")?;

    let inactive_user_token = access_token(
        secret,
        seeded.tenant_a.inactive_user_id,
        seeded.tenant_a.org_id,
    )?;
    let (status, body) = get_json(router, &inactive_user_token, "/brapi/v2/programs").await?;
    require_status(status, StatusCode::BAD_REQUEST, "inactive-user JWT")?;
    require_json_string(&body, "/detail", "Inactive user")?;

    Ok(())
}

async fn assert_live_org_zero_superuser_scope(
    router: &Router,
    secret: &str,
    seeded: &SeededData,
) -> TestResult {
    let token = access_token_with_superuser(secret, seeded.tenant_a.user_id, 0, true)?;
    let (status, body) = get_json(router, &token, "/brapi/v2/programs?pageSize=50").await?;
    require_status(status, StatusCode::OK, "org-zero superuser program list")?;
    let program_ids = list_field_values(&body, "programDbId")?;
    require_contains(
        &program_ids,
        &seeded.tenant_a.program_db_id,
        "org-zero superuser program list",
    )?;
    require_not_contains(
        &program_ids,
        &seeded.tenant_b.program_db_id,
        "org-zero superuser program list",
    )?;

    let (status, _) = get_json(
        router,
        &token,
        &format!("/brapi/v2/programs/{}", seeded.tenant_b.program_db_id),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "org-zero superuser cross-tenant program detail",
    )?;

    Ok(())
}

async fn assert_live_keycloak_route_mapping(database_url: &str, seeded: &SeededData) -> TestResult {
    let jwks_url = serve_keycloak_jwks_once().await?;
    let router = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
        .with_auth_config(AuthConfig::keycloak_rs256(
            KEYCLOAK_ISSUER,
            KEYCLOAK_AUDIENCE,
            jwks_url,
        ))
        .with_data_store(DataStore::from_database_url(database_url)));

    let (status, body) =
        get_json(&router, KEYCLOAK_TOKEN, "/brapi/v2/programs?pageSize=50").await?;
    require_status(status, StatusCode::OK, "Keycloak mapped program list")?;
    let program_ids = list_field_values(&body, "programDbId")?;
    require_contains(
        &program_ids,
        &seeded.tenant_a.program_db_id,
        "Keycloak mapped program list",
    )?;
    require_not_contains(
        &program_ids,
        &seeded.tenant_b.program_db_id,
        "Keycloak mapped program list",
    )?;

    Ok(())
}

async fn assert_seeded_brapi_reads(
    router: &Router,
    token: &str,
    seeded: &SeededData,
) -> TestResult {
    let (status, body) = get_json(router, token, "/brapi/v2/programs?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/programs")?;
    let program_ids = list_field_values(&body, "programDbId")?;
    require_order_prefix(
        &program_ids,
        &[
            seeded.tenant_a.program_db_id.as_str(),
            seeded.tenant_a.secondary_program_db_id.as_str(),
        ],
        "program list",
    )?;
    require_contains(&program_ids, &seeded.tenant_a.program_db_id, "program list")?;
    require_contains(
        &program_ids,
        &seeded.tenant_a.secondary_program_db_id,
        "program list",
    )?;
    require_not_contains(&program_ids, &seeded.tenant_b.program_db_id, "program list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/programs?programName={}&pageSize=50",
            seeded.tenant_a.program_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "program name filter")?;
    let filtered_program_ids = list_field_values(&body, "programDbId")?;
    require_contains(
        &filtered_program_ids,
        &seeded.tenant_a.program_db_id,
        "program name filter",
    )?;
    require_not_contains(
        &filtered_program_ids,
        &seeded.tenant_a.secondary_program_db_id,
        "program name filter",
    )?;
    require_not_contains(
        &filtered_program_ids,
        &seeded.tenant_b.program_db_id,
        "program name filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/programs?abbreviation={}&pageSize=50",
            seeded.tenant_a.program_abbreviation
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "program abbreviation filter")?;
    let abbreviation_program_ids = list_field_values(&body, "programDbId")?;
    require_contains(
        &abbreviation_program_ids,
        &seeded.tenant_a.program_db_id,
        "program abbreviation filter",
    )?;
    require_not_contains(
        &abbreviation_program_ids,
        &seeded.tenant_a.secondary_program_db_id,
        "program abbreviation filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/programs?pageSize=1").await?;
    require_status(status, StatusCode::OK, "program pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/programs/{}", seeded.tenant_a.program_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant program detail")?;
    require_json_string(&body, "/result/programDbId", &seeded.tenant_a.program_db_id)?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/programs/{}", seeded.tenant_b.program_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant program detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/locations?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/locations")?;
    let location_ids = list_field_values(&body, "locationDbId")?;
    require_order_prefix(
        &location_ids,
        &[
            seeded.tenant_a.location_db_id.as_str(),
            seeded.tenant_a.null_coordinate_location_db_id.as_str(),
        ],
        "location list",
    )?;
    require_contains(
        &location_ids,
        &seeded.tenant_a.location_db_id,
        "location list",
    )?;
    require_contains(
        &location_ids,
        &seeded.tenant_a.null_coordinate_location_db_id,
        "location list",
    )?;
    require_not_contains(
        &location_ids,
        &seeded.tenant_b.location_db_id,
        "location list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/locations?locationType={}&pageSize=50",
            seeded.tenant_a.location_type
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "location type filter")?;
    let filtered_location_ids = list_field_values(&body, "locationDbId")?;
    require_contains(
        &filtered_location_ids,
        &seeded.tenant_a.location_db_id,
        "location type filter",
    )?;
    require_not_contains(
        &filtered_location_ids,
        &seeded.tenant_a.null_coordinate_location_db_id,
        "location type filter",
    )?;
    require_not_contains(
        &filtered_location_ids,
        &seeded.tenant_b.location_db_id,
        "location type filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/locations?locationType={}&pageSize=50",
            seeded.tenant_a.location_type.to_lowercase()
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "location type case-sensitive filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/locations/{}", seeded.tenant_a.location_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant location detail")?;
    require_json_string(
        &body,
        "/result/locationDbId",
        &seeded.tenant_a.location_db_id,
    )?;
    require_json_string(
        &body,
        "/result/locationType",
        &seeded.tenant_a.location_type,
    )?;
    require_json_f64(&body, "/result/coordinates/latitude", 21.1702)?;
    require_json_f64(&body, "/result/coordinates/longitude", 72.8311)?;
    require_json_null(&body, "/result/coordinates/altitude")?;
    require_json_string(&body, "/result/altitude", "12.5 m")?;
    require_json_string(&body, "/result/coordinateUncertainty", "5 m")?;
    require_json_string(
        &body,
        "/result/coordinateDescription",
        "Live test plot center",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/locations/{}",
            seeded.tenant_a.null_coordinate_location_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "tenant null-coordinate location detail",
    )?;
    require_json_string(
        &body,
        "/result/locationDbId",
        &seeded.tenant_a.null_coordinate_location_db_id,
    )?;
    require_json_null(&body, "/result/coordinates")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/locations/{}", seeded.tenant_b.location_db_id),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant location detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/trials?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/trials")?;
    let trial_ids = list_field_values(&body, "trialDbId")?;
    require_contains(&trial_ids, &seeded.tenant_a.trial_db_id, "trial list")?;
    require_contains(
        &trial_ids,
        &seeded.tenant_a.inactive_trial_db_id,
        "trial list",
    )?;
    require_not_contains(&trial_ids, &seeded.tenant_b.trial_db_id, "trial list")?;

    let (status, body) =
        get_json(router, token, "/brapi/v2/trials?active=true&pageSize=50").await?;
    require_status(status, StatusCode::OK, "active trial filter")?;
    let active_trial_ids = list_field_values(&body, "trialDbId")?;
    require_contains(
        &active_trial_ids,
        &seeded.tenant_a.trial_db_id,
        "active trial filter",
    )?;
    require_not_contains(
        &active_trial_ids,
        &seeded.tenant_a.inactive_trial_db_id,
        "active trial filter",
    )?;
    require_not_contains(
        &active_trial_ids,
        &seeded.tenant_b.trial_db_id,
        "active trial filter",
    )?;

    let (status, body) =
        get_json(router, token, "/brapi/v2/trials?active=false&pageSize=50").await?;
    require_status(status, StatusCode::OK, "inactive trial filter")?;
    let inactive_trial_ids = list_field_values(&body, "trialDbId")?;
    require_contains(
        &inactive_trial_ids,
        &seeded.tenant_a.inactive_trial_db_id,
        "inactive trial filter",
    )?;
    require_not_contains(
        &inactive_trial_ids,
        &seeded.tenant_a.trial_db_id,
        "inactive trial filter",
    )?;
    require_not_contains(
        &inactive_trial_ids,
        &seeded.tenant_b.inactive_trial_db_id,
        "inactive trial filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/trials?pageSize=1").await?;
    require_status(status, StatusCode::OK, "trial pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/trials/{}", seeded.tenant_a.trial_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant trial detail")?;
    require_json_string(&body, "/result/trialDbId", &seeded.tenant_a.trial_db_id)?;
    require_json_string(&body, "/result/programDbId", &seeded.tenant_a.program_db_id)?;
    require_json_string(
        &body,
        "/result/startDate",
        &seeded.tenant_a.trial_start_date,
    )?;
    require_json_string(&body, "/result/endDate", &seeded.tenant_a.trial_end_date)?;
    require_json_bool(&body, "/result/active", true)?;
    require_json_string(&body, "/result/commonCropName", "rice")?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/trials/{}", seeded.tenant_a.inactive_trial_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant inactive trial detail")?;
    require_json_string(
        &body,
        "/result/trialDbId",
        &seeded.tenant_a.inactive_trial_db_id,
    )?;
    require_json_bool(&body, "/result/active", false)?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/trials/{}-missing", seeded.tenant_a.trial_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing trial detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/trials/{}", seeded.tenant_b.trial_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant trial detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/studies?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/studies")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 3)?;
    let study_ids = list_field_values(&body, "studyDbId")?;
    require_order_prefix(
        &study_ids,
        &[
            seeded.tenant_a.study_db_id.as_str(),
            seeded.tenant_a.inactive_study_db_id.as_str(),
            seeded.tenant_a.null_observation_levels_study_db_id.as_str(),
        ],
        "study list",
    )?;
    require_contains(&study_ids, &seeded.tenant_a.study_db_id, "study list")?;
    require_contains(
        &study_ids,
        &seeded.tenant_a.inactive_study_db_id,
        "study list",
    )?;
    require_contains(
        &study_ids,
        &seeded.tenant_a.null_observation_levels_study_db_id,
        "study list",
    )?;
    require_not_contains(&study_ids, &seeded.tenant_b.study_db_id, "study list")?;

    let (status, body) =
        get_json(router, token, "/brapi/v2/studies?active=true&pageSize=50").await?;
    require_status(status, StatusCode::OK, "active study filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let active_study_ids = list_field_values(&body, "studyDbId")?;
    require_contains(
        &active_study_ids,
        &seeded.tenant_a.study_db_id,
        "active study filter",
    )?;
    require_contains(
        &active_study_ids,
        &seeded.tenant_a.null_observation_levels_study_db_id,
        "active study filter",
    )?;
    require_not_contains(
        &active_study_ids,
        &seeded.tenant_a.inactive_study_db_id,
        "active study filter",
    )?;
    require_not_contains(
        &active_study_ids,
        &seeded.tenant_b.study_db_id,
        "active study filter",
    )?;

    let (status, body) =
        get_json(router, token, "/brapi/v2/studies?active=false&pageSize=50").await?;
    require_status(status, StatusCode::OK, "inactive study filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let inactive_study_ids = list_field_values(&body, "studyDbId")?;
    require_contains(
        &inactive_study_ids,
        &seeded.tenant_a.inactive_study_db_id,
        "inactive study filter",
    )?;
    require_not_contains(
        &inactive_study_ids,
        &seeded.tenant_a.study_db_id,
        "inactive study filter",
    )?;
    require_not_contains(
        &inactive_study_ids,
        &seeded.tenant_b.inactive_study_db_id,
        "inactive study filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/studies/{}", seeded.tenant_a.study_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant study detail")?;
    require_json_string(&body, "/result/studyDbId", &seeded.tenant_a.study_db_id)?;
    require_json_string(&body, "/result/trialDbId", &seeded.tenant_a.trial_db_id)?;
    require_json_string(
        &body,
        "/result/locationDbId",
        &seeded.tenant_a.location_db_id,
    )?;
    require_json_string(
        &body,
        "/result/startDate",
        &seeded.tenant_a.study_start_date,
    )?;
    require_json_string(&body, "/result/endDate", &seeded.tenant_a.study_end_date)?;
    require_json_bool(&body, "/result/active", true)?;
    require_json_string(&body, "/result/commonCropName", "rice")?;
    require_json_string(
        &body,
        "/result/culturalPractices",
        "standard agronomic practices",
    )?;
    require_array_len(&body, "/result/observationLevels", 2)?;
    require_json_string(&body, "/result/observationLevels/0/levelName", "plot")?;
    require_json_string(&body, "/result/observationLevels/0/levelOrder", "1")?;
    require_json_string(&body, "/result/observationLevels/1/levelName", "plant")?;
    require_json_string(&body, "/result/observationLevels/1/levelOrder", "2")?;
    require_json_string(
        &body,
        "/result/observationUnitsDescription",
        "Single plot observations",
    )?;
    require_json_string(&body, "/result/license", "CC-BY-4.0")?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/studies/{}", seeded.tenant_a.inactive_study_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant inactive study detail")?;
    require_json_string(
        &body,
        "/result/studyDbId",
        &seeded.tenant_a.inactive_study_db_id,
    )?;
    require_json_string(
        &body,
        "/result/trialDbId",
        &seeded.tenant_a.inactive_trial_db_id,
    )?;
    require_json_bool(&body, "/result/active", false)?;
    require_array_len(&body, "/result/observationLevels", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/studies/{}",
            seeded.tenant_a.null_observation_levels_study_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "tenant null-observation-levels study detail",
    )?;
    require_json_string(
        &body,
        "/result/studyDbId",
        &seeded.tenant_a.null_observation_levels_study_db_id,
    )?;
    require_json_null(&body, "/result/observationLevels")?;
    require_json_null(&body, "/result/observationUnitsDescription")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/studies/{}-missing", seeded.tenant_a.study_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing study detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/studies/{}", seeded.tenant_b.study_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant study detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/seasons?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/seasons")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let season_ids = list_field_values(&body, "seasonDbId")?;
    require_order_prefix(
        &season_ids,
        &[
            seeded.tenant_a.season_db_id.as_str(),
            seeded.tenant_a.previous_season_db_id.as_str(),
        ],
        "season list",
    )?;
    require_contains(&season_ids, &seeded.tenant_a.season_db_id, "season list")?;
    require_contains(
        &season_ids,
        &seeded.tenant_a.previous_season_db_id,
        "season list",
    )?;
    require_not_contains(&season_ids, &seeded.tenant_b.season_db_id, "season list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seasons?year={}&pageSize=50",
            seeded.tenant_a.season_year
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "season year filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let year_filtered_season_ids = list_field_values(&body, "seasonDbId")?;
    require_contains(
        &year_filtered_season_ids,
        &seeded.tenant_a.season_db_id,
        "season year filter",
    )?;
    require_not_contains(
        &year_filtered_season_ids,
        &seeded.tenant_a.previous_season_db_id,
        "season year filter",
    )?;
    require_not_contains(
        &year_filtered_season_ids,
        &seeded.tenant_b.season_db_id,
        "season year filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seasons?seasonDbId={}&pageSize=50",
            seeded.tenant_a.previous_season_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seasonDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_u64(
        &body,
        "/result/data/0/year",
        seeded.tenant_a.previous_season_year as u64,
    )?;
    let id_filtered_season_ids = list_field_values(&body, "seasonDbId")?;
    require_contains(
        &id_filtered_season_ids,
        &seeded.tenant_a.previous_season_db_id,
        "seasonDbId filter",
    )?;
    require_not_contains(
        &id_filtered_season_ids,
        &seeded.tenant_a.season_db_id,
        "seasonDbId filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/seasons?year=1900&pageSize=50").await?;
    require_status(status, StatusCode::OK, "empty season year filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 1)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/seasons/{}", seeded.tenant_a.season_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant season detail")?;
    require_json_string(&body, "/result/seasonDbId", &seeded.tenant_a.season_db_id)?;
    require_json_string(&body, "/result/seasonName", "Kharif")?;
    require_json_u64(&body, "/result/year", seeded.tenant_a.season_year as u64)?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/seasons/{}-missing", seeded.tenant_a.season_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing season detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/seasons/{}", seeded.tenant_b.season_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant season detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/people?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/people")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let person_ids = list_field_values(&body, "personDbId")?;
    require_order_prefix(
        &person_ids,
        &[
            seeded.tenant_a.secondary_person_db_id.as_str(),
            seeded.tenant_a.person_db_id.as_str(),
        ],
        "people list",
    )?;
    require_contains(&person_ids, &seeded.tenant_a.person_db_id, "people list")?;
    require_contains(
        &person_ids,
        &seeded.tenant_a.secondary_person_db_id,
        "people list",
    )?;
    require_not_contains(&person_ids, &seeded.tenant_b.person_db_id, "people list")?;

    let first_name_fragment = seeded.tenant_a.person_first_name[1..5].to_lowercase();
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/people?firstName={first_name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "people firstName contains filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let first_name_filtered_ids = list_field_values(&body, "personDbId")?;
    require_contains(
        &first_name_filtered_ids,
        &seeded.tenant_a.person_db_id,
        "people firstName contains filter",
    )?;
    require_not_contains(
        &first_name_filtered_ids,
        &seeded.tenant_a.secondary_person_db_id,
        "people firstName contains filter",
    )?;
    require_not_contains(
        &first_name_filtered_ids,
        &seeded.tenant_b.person_db_id,
        "people firstName contains filter",
    )?;

    let last_name_fragment = seeded.tenant_a.secondary_person_last_name[1..5].to_lowercase();
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/people?lastName={last_name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "people lastName contains filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let last_name_filtered_ids = list_field_values(&body, "personDbId")?;
    require_contains(
        &last_name_filtered_ids,
        &seeded.tenant_a.secondary_person_db_id,
        "people lastName contains filter",
    )?;
    require_not_contains(
        &last_name_filtered_ids,
        &seeded.tenant_a.person_db_id,
        "people lastName contains filter",
    )?;
    require_not_contains(
        &last_name_filtered_ids,
        &seeded.tenant_b.secondary_person_db_id,
        "people lastName contains filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/people?firstName=nomatch&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "empty people firstName filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 1)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/people/{}", seeded.tenant_a.person_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant person detail")?;
    require_json_string(&body, "/result/personDbId", &seeded.tenant_a.person_db_id)?;
    require_json_string(
        &body,
        "/result/firstName",
        &seeded.tenant_a.person_first_name,
    )?;
    require_json_string(&body, "/result/lastName", &seeded.tenant_a.person_last_name)?;
    require_json_string(
        &body,
        "/result/userId",
        &seeded.tenant_a.user_id.to_string(),
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/people/{}",
            seeded.tenant_a.secondary_person_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant secondary person detail")?;
    require_json_string(
        &body,
        "/result/personDbId",
        &seeded.tenant_a.secondary_person_db_id,
    )?;
    require_json_string(
        &body,
        "/result/firstName",
        &seeded.tenant_a.secondary_person_first_name,
    )?;
    require_json_string(
        &body,
        "/result/lastName",
        &seeded.tenant_a.secondary_person_last_name,
    )?;
    require_json_null(&body, "/result/userId")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/people/{}-missing", seeded.tenant_a.person_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing person detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/people/{}", seeded.tenant_b.person_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant person detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/lists?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/lists")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let list_ids = list_field_values(&body, "listDbId")?;
    require_order_prefix(
        &list_ids,
        &[
            seeded.tenant_a.list_db_id.as_str(),
            seeded.tenant_a.secondary_list_db_id.as_str(),
        ],
        "list list",
    )?;
    require_contains(&list_ids, &seeded.tenant_a.list_db_id, "list list")?;
    require_contains(
        &list_ids,
        &seeded.tenant_a.secondary_list_db_id,
        "list list",
    )?;
    require_not_contains(&list_ids, &seeded.tenant_b.list_db_id, "list list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/lists?listType={}&pageSize=50",
            seeded.tenant_a.secondary_list_type
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "list type filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let type_filtered_list_ids = list_field_values(&body, "listDbId")?;
    require_contains(
        &type_filtered_list_ids,
        &seeded.tenant_a.secondary_list_db_id,
        "list type filter",
    )?;
    require_not_contains(
        &type_filtered_list_ids,
        &seeded.tenant_a.list_db_id,
        "list type filter",
    )?;
    require_not_contains(
        &type_filtered_list_ids,
        &seeded.tenant_b.secondary_list_db_id,
        "list type filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/lists?listName={}&pageSize=50",
            seeded.tenant_a.secondary_list_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "list name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_list_ids = list_field_values(&body, "listDbId")?;
    require_contains(
        &name_filtered_list_ids,
        &seeded.tenant_a.secondary_list_db_id,
        "list name filter",
    )?;
    require_not_contains(
        &name_filtered_list_ids,
        &seeded.tenant_a.list_db_id,
        "list name filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/lists?listDbId={}&pageSize=50",
            seeded.tenant_a.list_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "list ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_list_ids = list_field_values(&body, "listDbId")?;
    require_contains(
        &id_filtered_list_ids,
        &seeded.tenant_a.list_db_id,
        "list ID filter",
    )?;
    require_not_contains(
        &id_filtered_list_ids,
        &seeded.tenant_a.secondary_list_db_id,
        "list ID filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/lists?listSource={}&pageSize=50",
            seeded.tenant_a.secondary_list_source
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "list source filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let source_filtered_list_ids = list_field_values(&body, "listDbId")?;
    require_contains(
        &source_filtered_list_ids,
        &seeded.tenant_a.secondary_list_db_id,
        "list source filter",
    )?;
    require_not_contains(
        &source_filtered_list_ids,
        &seeded.tenant_a.list_db_id,
        "list source filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/lists?pageSize=1").await?;
    require_status(status, StatusCode::OK, "list pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/lists/{}", seeded.tenant_a.list_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant list detail")?;
    require_json_string(&body, "/result/listDbId", &seeded.tenant_a.list_db_id)?;
    require_json_string(&body, "/result/listName", &seeded.tenant_a.list_name)?;
    require_json_string(&body, "/result/listType", &seeded.tenant_a.list_type)?;
    require_json_string(&body, "/result/listSource", &seeded.tenant_a.list_source)?;
    require_json_string(
        &body,
        "/result/listOwnerPersonDbId",
        &seeded.tenant_a.person_db_id,
    )?;
    require_json_u64(&body, "/result/listSize", 2)?;
    require_array_len(&body, "/result/data", 2)?;
    require_json_string(&body, "/result/data/0", &seeded.tenant_a.germplasm_db_id)?;
    require_json_string(
        &body,
        "/result/data/1",
        &seeded.tenant_a.secondary_germplasm_db_id,
    )?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/lists/{}", seeded.tenant_b.list_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant list detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/ontologies?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/ontologies")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let ontology_ids = list_field_values(&body, "ontologyDbId")?;
    require_order_prefix(
        &ontology_ids,
        &[
            seeded.tenant_a.ontology_db_id.as_str(),
            seeded.tenant_a.secondary_ontology_db_id.as_str(),
        ],
        "ontology list",
    )?;
    require_contains(
        &ontology_ids,
        &seeded.tenant_a.ontology_db_id,
        "ontology list",
    )?;
    require_contains(
        &ontology_ids,
        &seeded.tenant_a.secondary_ontology_db_id,
        "ontology list",
    )?;
    require_not_contains(
        &ontology_ids,
        &seeded.tenant_b.ontology_db_id,
        "ontology list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/ontologies?ontologyDbId={}&pageSize=50",
            seeded.tenant_a.ontology_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "ontology ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_ontology_ids = list_field_values(&body, "ontologyDbId")?;
    require_contains(
        &id_filtered_ontology_ids,
        &seeded.tenant_a.ontology_db_id,
        "ontology ID filter",
    )?;
    require_not_contains(
        &id_filtered_ontology_ids,
        &seeded.tenant_a.secondary_ontology_db_id,
        "ontology ID filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/ontologies?ontologyName={}&pageSize=50",
            seeded.tenant_a.secondary_ontology_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "ontology name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_ontology_ids = list_field_values(&body, "ontologyDbId")?;
    require_contains(
        &name_filtered_ontology_ids,
        &seeded.tenant_a.secondary_ontology_db_id,
        "ontology name filter",
    )?;
    require_not_contains(
        &name_filtered_ontology_ids,
        &seeded.tenant_a.ontology_db_id,
        "ontology name filter",
    )?;
    require_not_contains(
        &name_filtered_ontology_ids,
        &seeded.tenant_b.secondary_ontology_db_id,
        "ontology name filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/ontologies?pageSize=1").await?;
    require_status(status, StatusCode::OK, "ontology pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/ontologies/{}", seeded.tenant_a.ontology_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant ontology detail")?;
    require_json_string(
        &body,
        "/result/ontologyDbId",
        &seeded.tenant_a.ontology_db_id,
    )?;
    require_json_string(
        &body,
        "/result/ontologyName",
        &seeded.tenant_a.ontology_name,
    )?;
    require_json_string(&body, "/result/version", "1.0")?;
    require_json_string(&body, "/result/licence", "CC-BY-4.0")?;
    require_json_string(
        &body,
        "/result/documentationURL",
        "https://example.test/ontology-primary",
    )?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/ontologies/{}", seeded.tenant_b.ontology_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "cross-tenant ontology detail")?;
    require_json_null(&body, "/result")?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(router, token, "/brapi/v2/methods?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/methods")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let method_ids = list_field_values(&body, "methodDbId")?;
    require_order_prefix(
        &method_ids,
        &[
            seeded.tenant_a.method_db_id.as_str(),
            seeded.tenant_a.secondary_method_db_id.as_str(),
        ],
        "method list",
    )?;
    require_contains(&method_ids, &seeded.tenant_a.method_db_id, "method list")?;
    require_contains(
        &method_ids,
        &seeded.tenant_a.secondary_method_db_id,
        "method list",
    )?;
    require_not_contains(&method_ids, &seeded.tenant_b.method_db_id, "method list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/methods?methodDbId={}&pageSize=50",
            seeded.tenant_a.method_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "methodDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_method_ids = list_field_values(&body, "methodDbId")?;
    require_contains(
        &id_filtered_method_ids,
        &seeded.tenant_a.method_db_id,
        "methodDbId filter",
    )?;
    require_not_contains(
        &id_filtered_method_ids,
        &seeded.tenant_a.secondary_method_db_id,
        "methodDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/methods?methodClass={}&pageSize=50",
            seeded.tenant_a.secondary_method_class
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "method class filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let class_filtered_method_ids = list_field_values(&body, "methodDbId")?;
    require_contains(
        &class_filtered_method_ids,
        &seeded.tenant_a.secondary_method_db_id,
        "method class filter",
    )?;
    require_not_contains(
        &class_filtered_method_ids,
        &seeded.tenant_a.method_db_id,
        "method class filter",
    )?;

    let method_name_fragment = "field-ruler";
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/methods?methodName={method_name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "method name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_method_ids = list_field_values(&body, "methodDbId")?;
    require_contains(
        &name_filtered_method_ids,
        &seeded.tenant_a.method_db_id,
        "method name filter",
    )?;
    require_not_contains(
        &name_filtered_method_ids,
        &seeded.tenant_a.secondary_method_db_id,
        "method name filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/methods?ontologyDbId={}&pageSize=50",
            seeded.tenant_a.secondary_ontology_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "method ontologyDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let ontology_filtered_method_ids = list_field_values(&body, "methodDbId")?;
    require_contains(
        &ontology_filtered_method_ids,
        &seeded.tenant_a.secondary_method_db_id,
        "method ontologyDbId filter",
    )?;
    require_not_contains(
        &ontology_filtered_method_ids,
        &seeded.tenant_a.method_db_id,
        "method ontologyDbId filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/methods?pageSize=1").await?;
    require_status(status, StatusCode::OK, "method pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/methods/{}", seeded.tenant_a.method_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant method detail")?;
    require_json_string(&body, "/result/methodDbId", &seeded.tenant_a.method_db_id)?;
    require_json_string(&body, "/result/methodName", &seeded.tenant_a.method_name)?;
    require_json_string(&body, "/result/methodClass", &seeded.tenant_a.method_class)?;
    let method_pui = format!("https://example.test/{}", seeded.tenant_a.method_db_id);
    require_json_string(&body, "/result/methodPUI", &method_pui)?;
    require_json_string(
        &body,
        "/result/description",
        "Measure plant height in centimeters",
    )?;
    require_json_string(&body, "/result/reference", "Live field SOP")?;
    require_json_string(
        &body,
        "/result/bibliographicalReference",
        "Bijmantra live method reference",
    )?;
    require_json_string(
        &body,
        "/result/ontologyReference/ontologyDbId",
        &seeded.tenant_a.ontology_db_id,
    )?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/methods/{}-missing", seeded.tenant_a.method_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "missing method detail")?;
    require_json_null(&body, "/result")?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/methods/{}", seeded.tenant_b.method_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "cross-tenant method detail")?;
    require_json_null(&body, "/result")?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(router, token, "/brapi/v2/scales?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/scales")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let scale_ids = list_field_values(&body, "scaleDbId")?;
    require_order_prefix(
        &scale_ids,
        &[
            seeded.tenant_a.scale_db_id.as_str(),
            seeded.tenant_a.secondary_scale_db_id.as_str(),
        ],
        "scale list",
    )?;
    require_contains(&scale_ids, &seeded.tenant_a.scale_db_id, "scale list")?;
    require_contains(
        &scale_ids,
        &seeded.tenant_a.secondary_scale_db_id,
        "scale list",
    )?;
    require_not_contains(&scale_ids, &seeded.tenant_b.scale_db_id, "scale list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/scales?scaleDbId={}&pageSize=50",
            seeded.tenant_a.scale_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "scaleDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_scale_ids = list_field_values(&body, "scaleDbId")?;
    require_contains(
        &id_filtered_scale_ids,
        &seeded.tenant_a.scale_db_id,
        "scaleDbId filter",
    )?;
    require_not_contains(
        &id_filtered_scale_ids,
        &seeded.tenant_a.secondary_scale_db_id,
        "scaleDbId filter",
    )?;

    let scale_name_fragment = "centimeter";
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/scales?scaleName={scale_name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "scale name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_scale_ids = list_field_values(&body, "scaleDbId")?;
    require_contains(
        &name_filtered_scale_ids,
        &seeded.tenant_a.scale_db_id,
        "scale name filter",
    )?;
    require_not_contains(
        &name_filtered_scale_ids,
        &seeded.tenant_a.secondary_scale_db_id,
        "scale name filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/scales?dataType={}&pageSize=50",
            seeded.tenant_a.secondary_scale_data_type
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "scale dataType filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let data_type_filtered_scale_ids = list_field_values(&body, "scaleDbId")?;
    require_contains(
        &data_type_filtered_scale_ids,
        &seeded.tenant_a.secondary_scale_db_id,
        "scale dataType filter",
    )?;
    require_not_contains(
        &data_type_filtered_scale_ids,
        &seeded.tenant_a.scale_db_id,
        "scale dataType filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/scales?ontologyDbId={}&pageSize=50",
            seeded.tenant_a.secondary_ontology_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "scale ontologyDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let ontology_filtered_scale_ids = list_field_values(&body, "scaleDbId")?;
    require_contains(
        &ontology_filtered_scale_ids,
        &seeded.tenant_a.secondary_scale_db_id,
        "scale ontologyDbId filter",
    )?;
    require_not_contains(
        &ontology_filtered_scale_ids,
        &seeded.tenant_a.scale_db_id,
        "scale ontologyDbId filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/scales?pageSize=1").await?;
    require_status(status, StatusCode::OK, "scale pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/scales/{}", seeded.tenant_a.scale_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant scale detail")?;
    require_json_string(&body, "/result/scaleDbId", &seeded.tenant_a.scale_db_id)?;
    require_json_string(&body, "/result/scaleName", &seeded.tenant_a.scale_name)?;
    let scale_pui = format!("https://example.test/{}", seeded.tenant_a.scale_db_id);
    require_json_string(&body, "/result/scalePUI", &scale_pui)?;
    require_json_string(&body, "/result/dataType", &seeded.tenant_a.scale_data_type)?;
    require_json_u64(&body, "/result/decimalPlaces", 1)?;
    require_json_u64(&body, "/result/validValues/min", 0)?;
    require_json_u64(&body, "/result/validValues/max", 250)?;
    require_json_string(&body, "/result/validValues/categories/0/label", "short")?;
    require_json_string(&body, "/result/validValues/categories/1/value", "tall")?;
    require_json_string(
        &body,
        "/result/ontologyReference/ontologyDbId",
        &seeded.tenant_a.ontology_db_id,
    )?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/scales/{}-missing", seeded.tenant_a.scale_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "missing scale detail")?;
    require_json_null(&body, "/result")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 0)?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/scales/{}", seeded.tenant_b.scale_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "cross-tenant scale detail")?;
    require_json_null(&body, "/result")?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(router, token, "/brapi/v2/traits?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/traits")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let trait_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &trait_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "trait list",
    )?;
    require_contains(
        &trait_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "trait list",
    )?;
    require_not_contains(
        &trait_ids,
        &seeded.tenant_b.observation_variable_db_id,
        "trait list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/traits?traitClass={}&pageSize=50",
            seeded.tenant_a.secondary_trait_class
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "trait class filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let class_filtered_trait_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &class_filtered_trait_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "trait class filter",
    )?;
    require_not_contains(
        &class_filtered_trait_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "trait class filter",
    )?;
    require_not_contains(
        &class_filtered_trait_ids,
        &seeded.tenant_b.secondary_observation_variable_db_id,
        "trait class filter",
    )?;

    let name_fragment = "plant-height";
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/traits?observationVariableName={name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "trait observationVariableName filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_trait_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &name_filtered_trait_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "trait observationVariableName filter",
    )?;
    require_not_contains(
        &name_filtered_trait_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "trait observationVariableName filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/traits?commonCropName={}&pageSize=50",
            seeded.tenant_a.secondary_trait_common_crop_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "trait commonCropName filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let crop_filtered_trait_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &crop_filtered_trait_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "trait commonCropName filter",
    )?;
    require_not_contains(
        &crop_filtered_trait_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "trait commonCropName filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/traits?pageSize=1").await?;
    require_status(status, StatusCode::OK, "trait pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/traits/{}",
            seeded.tenant_a.observation_variable_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant trait detail")?;
    require_json_string(
        &body,
        "/result/observationVariableDbId",
        &seeded.tenant_a.observation_variable_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationVariableName",
        &seeded.tenant_a.observation_variable_name,
    )?;
    require_json_string(&body, "/result/traitName", "Plant height")?;
    require_json_string(&body, "/result/traitClass", &seeded.tenant_a.trait_class)?;
    require_json_string(&body, "/result/methodName", "Field ruler")?;
    require_json_string(&body, "/result/scaleName", "centimeter")?;
    require_json_string(&body, "/result/scaleDataType", "Numerical")?;
    require_json_f64(&body, "/result/scaleValidValueMin", 0.0)?;
    require_json_f64(&body, "/result/scaleValidValueMax", 250.0)?;
    require_json_string(
        &body,
        "/result/commonCropName",
        &seeded.tenant_a.trait_common_crop_name,
    )?;
    require_json_string(&body, "/result/status", "active")?;
    require_json_string(
        &body,
        "/result/ontologyReference/ontologyDbId",
        &seeded.tenant_a.ontology_db_id,
    )?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/traits/{}-missing",
            seeded.tenant_a.observation_variable_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing trait detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/traits/{}",
            seeded.tenant_b.observation_variable_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant trait detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/variables?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/variables")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_order_prefix(
        &variable_ids,
        &[
            seeded
                .tenant_a
                .secondary_observation_variable_db_id
                .as_str(),
            seeded.tenant_a.observation_variable_db_id.as_str(),
        ],
        "variable list",
    )?;
    require_contains(
        &variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable list",
    )?;
    require_contains(
        &variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable list",
    )?;
    require_not_contains(
        &variable_ids,
        &seeded.tenant_b.observation_variable_db_id,
        "variable list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variables?observationVariableDbId={}&pageSize=50",
            seeded.tenant_a.observation_variable_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "variable ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &id_filtered_variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable ID filter",
    )?;
    require_not_contains(
        &id_filtered_variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable ID filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/variables?observationVariableName={name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "variable observationVariableName filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &name_filtered_variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable observationVariableName filter",
    )?;
    require_not_contains(
        &name_filtered_variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable observationVariableName filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variables?traitClass={}&pageSize=50",
            seeded.tenant_a.secondary_trait_class
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "variable traitClass filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let class_filtered_variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &class_filtered_variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable traitClass filter",
    )?;
    require_not_contains(
        &class_filtered_variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable traitClass filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variables?commonCropName={}&pageSize=50",
            seeded.tenant_a.secondary_trait_common_crop_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "variable commonCropName filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let crop_filtered_variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &crop_filtered_variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable commonCropName filter",
    )?;
    require_not_contains(
        &crop_filtered_variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable commonCropName filter",
    )?;

    let primary_variable_method_db_id =
        format!("{}-method", seeded.tenant_a.observation_variable_db_id);
    let secondary_variable_scale_db_id = format!(
        "{}-scale",
        seeded.tenant_a.secondary_observation_variable_db_id
    );

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/variables?methodDbId={primary_variable_method_db_id}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "variable methodDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let method_filtered_variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &method_filtered_variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable methodDbId filter",
    )?;
    require_not_contains(
        &method_filtered_variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable methodDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/variables?scaleDbId={secondary_variable_scale_db_id}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "variable scaleDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let scale_filtered_variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &scale_filtered_variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable scaleDbId filter",
    )?;
    require_not_contains(
        &scale_filtered_variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable scaleDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variables?ontologyDbId={}&pageSize=50",
            seeded.tenant_a.secondary_ontology_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "variable ontologyDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let ontology_filtered_variable_ids = list_field_values(&body, "observationVariableDbId")?;
    require_contains(
        &ontology_filtered_variable_ids,
        &seeded.tenant_a.secondary_observation_variable_db_id,
        "variable ontologyDbId filter",
    )?;
    require_not_contains(
        &ontology_filtered_variable_ids,
        &seeded.tenant_a.observation_variable_db_id,
        "variable ontologyDbId filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/variables?pageSize=1").await?;
    require_status(status, StatusCode::OK, "variable pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variables/{}",
            seeded.tenant_a.observation_variable_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant variable detail")?;
    require_json_string(
        &body,
        "/result/observationVariableDbId",
        &seeded.tenant_a.observation_variable_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationVariableName",
        &seeded.tenant_a.observation_variable_name,
    )?;
    require_json_string(
        &body,
        "/result/commonCropName",
        &seeded.tenant_a.trait_common_crop_name,
    )?;
    require_json_string(&body, "/result/defaultValue", "0")?;
    require_json_string(&body, "/result/status", "active")?;
    require_json_string(
        &body,
        "/result/trait/traitDbId",
        &format!("{}-trait", seeded.tenant_a.observation_variable_db_id),
    )?;
    require_json_string(&body, "/result/trait/traitName", "Plant height")?;
    require_json_string(
        &body,
        "/result/trait/traitClass",
        &seeded.tenant_a.trait_class,
    )?;
    require_json_string(
        &body,
        "/result/method/methodDbId",
        &primary_variable_method_db_id,
    )?;
    require_json_string(&body, "/result/method/methodName", "Field ruler")?;
    require_json_string(
        &body,
        "/result/method/methodDescription",
        "Measure plant height in centimeters",
    )?;
    require_json_string(
        &body,
        "/result/scale/scaleDbId",
        &format!("{}-scale", seeded.tenant_a.observation_variable_db_id),
    )?;
    require_json_string(&body, "/result/scale/scaleName", "centimeter")?;
    require_json_string(&body, "/result/scale/dataType", "Numerical")?;
    require_json_f64(&body, "/result/scale/validValues/min", 0.0)?;
    require_json_f64(&body, "/result/scale/validValues/max", 250.0)?;
    require_json_string(
        &body,
        "/result/ontologyReference/ontologyDbId",
        &seeded.tenant_a.ontology_db_id,
    )?;
    require_json_string(
        &body,
        "/result/ontologyReference/ontologyTermId",
        &format!("{}:0001", seeded.tenant_a.ontology_db_id),
    )?;
    require_json_string(&body, "/result/additionalInfo/kind", "primary-trait")?;
    require_json_string(
        &body,
        "/result/externalReferences/0/referenceId",
        &seeded.tenant_a.observation_variable_db_id,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variables/{}-missing",
            seeded.tenant_a.observation_variable_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing variable detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variables/{}",
            seeded.tenant_b.observation_variable_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant variable detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/observations?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/observations")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let observation_ids = list_field_values(&body, "observationDbId")?;
    require_contains(
        &observation_ids,
        &seeded.tenant_a.observation_db_id,
        "observation list",
    )?;
    require_contains(
        &observation_ids,
        &seeded.tenant_a.secondary_observation_db_id,
        "observation list",
    )?;
    require_not_contains(
        &observation_ids,
        &seeded.tenant_b.observation_db_id,
        "observation list",
    )?;

    let tenant_study_id = seeded.tenant_a.study_id.to_string();
    let tenant_germplasm_id = seeded.tenant_a.germplasm_id.to_string();
    let secondary_tenant_germplasm_id = seeded.tenant_a.secondary_germplasm_id.to_string();

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/observations?studyDbId={tenant_study_id}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "observation studyDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let study_filtered_observation_ids = list_field_values(&body, "observationDbId")?;
    require_contains(
        &study_filtered_observation_ids,
        &seeded.tenant_a.observation_db_id,
        "observation studyDbId filter",
    )?;
    require_contains(
        &study_filtered_observation_ids,
        &seeded.tenant_a.secondary_observation_db_id,
        "observation studyDbId filter",
    )?;
    require_not_contains(
        &study_filtered_observation_ids,
        &seeded.tenant_b.observation_db_id,
        "observation studyDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observations?germplasmDbId={secondary_tenant_germplasm_id}&pageSize=50"
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "observation germplasmDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let germplasm_filtered_observation_ids = list_field_values(&body, "observationDbId")?;
    require_contains(
        &germplasm_filtered_observation_ids,
        &seeded.tenant_a.secondary_observation_db_id,
        "observation germplasmDbId filter",
    )?;
    require_not_contains(
        &germplasm_filtered_observation_ids,
        &seeded.tenant_a.observation_db_id,
        "observation germplasmDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observations?observationVariableDbId={}&pageSize=50",
            seeded.tenant_a.observation_variable_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "observation observationVariableDbId filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let variable_filtered_observation_ids = list_field_values(&body, "observationDbId")?;
    require_contains(
        &variable_filtered_observation_ids,
        &seeded.tenant_a.observation_db_id,
        "observation observationVariableDbId filter",
    )?;
    require_not_contains(
        &variable_filtered_observation_ids,
        &seeded.tenant_a.secondary_observation_db_id,
        "observation observationVariableDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observations?observationUnitDbId={}&pageSize=50",
            seeded.tenant_a.secondary_observation_unit_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "observation observationUnitDbId filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let unit_filtered_observation_ids = list_field_values(&body, "observationDbId")?;
    require_contains(
        &unit_filtered_observation_ids,
        &seeded.tenant_a.secondary_observation_db_id,
        "observation observationUnitDbId filter",
    )?;
    require_not_contains(
        &unit_filtered_observation_ids,
        &seeded.tenant_a.observation_db_id,
        "observation observationUnitDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/observations?observationVariableDbId=codex-live-no-match&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "observation no-match filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(router, token, "/brapi/v2/observations?pageSize=1").await?;
    require_status(status, StatusCode::OK, "observation pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observations/{}",
            seeded.tenant_a.observation_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant observation detail")?;
    require_json_string(
        &body,
        "/result/observationDbId",
        &seeded.tenant_a.observation_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationUnitDbId",
        &seeded.tenant_a.observation_unit_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationVariableDbId",
        &seeded.tenant_a.observation_variable_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationVariableName",
        &seeded.tenant_a.observation_variable_name,
    )?;
    require_json_string(&body, "/result/value", "123.4")?;
    require_json_string(
        &body,
        "/result/observationTimeStamp",
        "2026-07-01T08:00:00Z",
    )?;
    require_json_string(&body, "/result/collector", "Anika Rao")?;
    require_json_string(&body, "/result/studyDbId", &tenant_study_id)?;
    require_json_string(&body, "/result/germplasmDbId", &tenant_germplasm_id)?;
    require_json_string(&body, "/result/seasonDbId", &seeded.tenant_a.season_db_id)?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;
    require_json_string(
        &body,
        "/result/externalReferences/0/referenceId",
        &seeded.tenant_a.observation_db_id,
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observations/{}",
            seeded.tenant_a.secondary_observation_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "tenant secondary observation detail",
    )?;
    require_json_string(
        &body,
        "/result/observationDbId",
        &seeded.tenant_a.secondary_observation_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationUnitDbId",
        &seeded.tenant_a.secondary_observation_unit_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationVariableDbId",
        &seeded.tenant_a.secondary_observation_variable_db_id,
    )?;
    require_json_string(&body, "/result/value", "excellent")?;
    require_json_string(
        &body,
        "/result/observationTimeStamp",
        "2026-07-02T08:00:00Z",
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observations/{}-missing",
            seeded.tenant_a.observation_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing observation detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observations/{}",
            seeded.tenant_b.observation_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant observation detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/observationunits?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/observationunits")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let observation_unit_ids = list_field_values(&body, "observationUnitDbId")?;
    require_order_prefix(
        &observation_unit_ids,
        &[
            seeded.tenant_a.observation_unit_db_id.as_str(),
            seeded.tenant_a.secondary_observation_unit_db_id.as_str(),
        ],
        "observation unit list",
    )?;
    require_contains(
        &observation_unit_ids,
        &seeded.tenant_a.observation_unit_db_id,
        "observation unit list",
    )?;
    require_contains(
        &observation_unit_ids,
        &seeded.tenant_a.secondary_observation_unit_db_id,
        "observation unit list",
    )?;
    require_not_contains(
        &observation_unit_ids,
        &seeded.tenant_b.observation_unit_db_id,
        "observation unit list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/observationunits?studyDbId={tenant_study_id}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "observation unit studyDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let study_filtered_unit_ids = list_field_values(&body, "observationUnitDbId")?;
    require_contains(
        &study_filtered_unit_ids,
        &seeded.tenant_a.observation_unit_db_id,
        "observation unit studyDbId filter",
    )?;
    require_contains(
        &study_filtered_unit_ids,
        &seeded.tenant_a.secondary_observation_unit_db_id,
        "observation unit studyDbId filter",
    )?;
    require_not_contains(
        &study_filtered_unit_ids,
        &seeded.tenant_b.observation_unit_db_id,
        "observation unit studyDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observationunits?germplasmDbId={secondary_tenant_germplasm_id}&pageSize=50"
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "observation unit germplasmDbId filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let germplasm_filtered_unit_ids = list_field_values(&body, "observationUnitDbId")?;
    require_contains(
        &germplasm_filtered_unit_ids,
        &seeded.tenant_a.secondary_observation_unit_db_id,
        "observation unit germplasmDbId filter",
    )?;
    require_not_contains(
        &germplasm_filtered_unit_ids,
        &seeded.tenant_a.observation_unit_db_id,
        "observation unit germplasmDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/observationunits?observationLevel=plot&pageSize=50",
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "observation unit observationLevel filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let level_filtered_unit_ids = list_field_values(&body, "observationUnitDbId")?;
    require_contains(
        &level_filtered_unit_ids,
        &seeded.tenant_a.observation_unit_db_id,
        "observation unit observationLevel filter",
    )?;
    require_contains(
        &level_filtered_unit_ids,
        &seeded.tenant_a.secondary_observation_unit_db_id,
        "observation unit observationLevel filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observationunits?observationUnitDbId={}&pageSize=50",
            seeded.tenant_a.observation_unit_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "observation unit observationUnitDbId filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_unit_ids = list_field_values(&body, "observationUnitDbId")?;
    require_contains(
        &id_filtered_unit_ids,
        &seeded.tenant_a.observation_unit_db_id,
        "observation unit observationUnitDbId filter",
    )?;
    require_not_contains(
        &id_filtered_unit_ids,
        &seeded.tenant_a.secondary_observation_unit_db_id,
        "observation unit observationUnitDbId filter",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/observationunits?pageSize=1").await?;
    require_status(status, StatusCode::OK, "observation unit pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observationunits/{}",
            seeded.tenant_a.observation_unit_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant observation unit detail")?;
    require_json_string(
        &body,
        "/result/observationUnitDbId",
        &seeded.tenant_a.observation_unit_db_id,
    )?;
    require_json_string(
        &body,
        "/result/observationUnitName",
        "Live Observation Unit a",
    )?;
    require_json_string(
        &body,
        "/result/observationUnitPUI",
        &format!(
            "https://example.test/{}",
            seeded.tenant_a.observation_unit_db_id
        ),
    )?;
    require_json_string(&body, "/result/studyDbId", &tenant_study_id)?;
    require_json_string(&body, "/result/studyName", "Live Active Study a")?;
    require_json_string(&body, "/result/germplasmDbId", &tenant_germplasm_id)?;
    require_json_string(
        &body,
        "/result/germplasmName",
        &seeded.tenant_a.germplasm_name,
    )?;
    require_json_string(&body, "/result/observationLevel", "plot")?;
    require_json_string(&body, "/result/observationLevelCode", "PLOT")?;
    require_json_u64(&body, "/result/observationLevelOrder", 1)?;
    require_json_string(&body, "/result/positionCoordinateX", "101")?;
    require_json_string(&body, "/result/positionCoordinateXType", "GRID_COL")?;
    require_json_string(&body, "/result/positionCoordinateY", "202")?;
    require_json_string(&body, "/result/positionCoordinateYType", "GRID_ROW")?;
    require_json_string(&body, "/result/entryType", "CHECK")?;
    require_json_string(&body, "/result/geoCoordinates/type", "Point")?;
    require_json_string(&body, "/result/treatments/0/factor", "water")?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;
    require_json_string(
        &body,
        "/result/externalReferences/0/referenceId",
        &seeded.tenant_a.observation_unit_db_id,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observationunits/{}-missing",
            seeded.tenant_a.observation_unit_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "missing observation unit detail",
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/observationunits/{}",
            seeded.tenant_b.observation_unit_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant observation unit detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/germplasm?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/germplasm")?;
    let germplasm_ids = list_field_values(&body, "germplasmDbId")?;
    require_order_prefix(
        &germplasm_ids,
        &[
            seeded.tenant_a.germplasm_db_id.as_str(),
            seeded.tenant_a.secondary_germplasm_db_id.as_str(),
        ],
        "germplasm list",
    )?;
    require_contains(
        &germplasm_ids,
        &seeded.tenant_a.germplasm_db_id,
        "germplasm list",
    )?;
    require_contains(
        &germplasm_ids,
        &seeded.tenant_a.secondary_germplasm_db_id,
        "germplasm list",
    )?;
    require_not_contains(
        &germplasm_ids,
        &seeded.tenant_b.germplasm_db_id,
        "germplasm list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/germplasm?germplasmName={}&pageSize=50",
            seeded.tenant_a.germplasm_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "germplasm name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_germplasm_ids = list_field_values(&body, "germplasmDbId")?;
    require_contains(
        &name_filtered_germplasm_ids,
        &seeded.tenant_a.germplasm_db_id,
        "germplasm name filter",
    )?;
    require_not_contains(
        &name_filtered_germplasm_ids,
        &seeded.tenant_a.secondary_germplasm_db_id,
        "germplasm name filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/germplasm?commonCropName={}&pageSize=50",
            seeded.tenant_a.secondary_germplasm_common_crop_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "germplasm common crop filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let crop_filtered_germplasm_ids = list_field_values(&body, "germplasmDbId")?;
    require_contains(
        &crop_filtered_germplasm_ids,
        &seeded.tenant_a.secondary_germplasm_db_id,
        "germplasm common crop filter",
    )?;
    require_not_contains(
        &crop_filtered_germplasm_ids,
        &seeded.tenant_a.germplasm_db_id,
        "germplasm common crop filter",
    )?;
    require_not_contains(
        &crop_filtered_germplasm_ids,
        &seeded.tenant_b.secondary_germplasm_db_id,
        "germplasm common crop filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/germplasm?species={}&pageSize=50",
            seeded.tenant_a.secondary_germplasm_species
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "germplasm species filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let species_filtered_germplasm_ids = list_field_values(&body, "germplasmDbId")?;
    require_contains(
        &species_filtered_germplasm_ids,
        &seeded.tenant_a.secondary_germplasm_db_id,
        "germplasm species filter",
    )?;
    require_not_contains(
        &species_filtered_germplasm_ids,
        &seeded.tenant_a.germplasm_db_id,
        "germplasm species filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/germplasm?genus={}&pageSize=50",
            seeded.tenant_a.germplasm_genus
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "germplasm genus filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let genus_filtered_germplasm_ids = list_field_values(&body, "germplasmDbId")?;
    require_contains(
        &genus_filtered_germplasm_ids,
        &seeded.tenant_a.germplasm_db_id,
        "germplasm genus filter",
    )?;
    require_not_contains(
        &genus_filtered_germplasm_ids,
        &seeded.tenant_a.secondary_germplasm_db_id,
        "germplasm genus filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/germplasm?germplasmName=codex-live-no-match&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "germplasm no-match filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/germplasm/{}", seeded.tenant_a.germplasm_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant germplasm detail")?;
    require_json_string(
        &body,
        "/result/germplasmDbId",
        &seeded.tenant_a.germplasm_db_id,
    )?;
    require_json_string(
        &body,
        "/result/germplasmName",
        &seeded.tenant_a.germplasm_name,
    )?;
    require_json_string(
        &body,
        "/result/commonCropName",
        &seeded.tenant_a.germplasm_common_crop_name,
    )?;
    require_json_string(&body, "/result/genus", &seeded.tenant_a.germplasm_genus)?;
    require_json_string(&body, "/result/species", &seeded.tenant_a.germplasm_species)?;
    require_json_string(&body, "/result/synonyms/0", "live-synonym-a")?;
    require_json_string(
        &body,
        "/result/donors/0/donorAccessionNumber",
        "donor-accession-a",
    )?;
    require_json_string(
        &body,
        "/result/donors/0/donorInstitute",
        "Bijmantra Live Donor Bank",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/germplasm/{}",
            seeded.tenant_a.secondary_germplasm_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant secondary germplasm detail")?;
    require_json_string(
        &body,
        "/result/germplasmDbId",
        &seeded.tenant_a.secondary_germplasm_db_id,
    )?;
    require_json_string(
        &body,
        "/result/germplasmName",
        &seeded.tenant_a.secondary_germplasm_name,
    )?;
    require_json_string(
        &body,
        "/result/genus",
        &seeded.tenant_a.secondary_germplasm_genus,
    )?;
    require_json_string(
        &body,
        "/result/species",
        &seeded.tenant_a.secondary_germplasm_species,
    )?;
    require_json_string(
        &body,
        "/result/commonCropName",
        &seeded.tenant_a.secondary_germplasm_common_crop_name,
    )?;
    require_json_string(&body, "/result/synonyms/0", "live-secondary-synonym-a")?;
    require_array_len(&body, "/result/donors", 0)?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/germplasm/{}", seeded.tenant_b.germplasm_db_id),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant germplasm detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/attributes?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/attributes")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_order_prefix(
        &attribute_ids,
        &[
            seeded.tenant_a.secondary_attribute_db_id.as_str(),
            seeded.tenant_a.attribute_db_id.as_str(),
        ],
        "attribute list",
    )?;
    require_contains(
        &attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attribute list",
    )?;
    require_contains(
        &attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attribute list",
    )?;
    require_not_contains(
        &attribute_ids,
        &seeded.tenant_b.attribute_db_id,
        "attribute list",
    )?;

    let secondary_attribute_category_query = seeded
        .tenant_a
        .secondary_attribute_category
        .replace(' ', "%20");
    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributes?attributeCategory={secondary_attribute_category_query}&pageSize=50"
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "attribute category filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let category_filtered_attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_contains(
        &category_filtered_attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attribute category filter",
    )?;
    require_not_contains(
        &category_filtered_attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attribute category filter",
    )?;
    require_not_contains(
        &category_filtered_attribute_ids,
        &seeded.tenant_b.secondary_attribute_db_id,
        "attribute category filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributes?attributeDbId={}&pageSize=50",
            seeded.tenant_a.attribute_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "attributeDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_contains(
        &id_filtered_attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attributeDbId filter",
    )?;
    require_not_contains(
        &id_filtered_attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attributeDbId filter",
    )?;

    let attribute_name_fragment = "grain-color";
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/attributes?attributeName={attribute_name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "attributeName filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_contains(
        &name_filtered_attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attributeName filter",
    )?;
    require_not_contains(
        &name_filtered_attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attributeName filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributes?commonCropName={}&pageSize=50",
            seeded.tenant_a.secondary_germplasm_common_crop_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "attribute commonCropName filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let crop_filtered_attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_contains(
        &crop_filtered_attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attribute commonCropName filter",
    )?;
    require_not_contains(
        &crop_filtered_attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attribute commonCropName filter",
    )?;

    let primary_attribute_trait_db_id = format!("{}-trait", seeded.tenant_a.attribute_db_id);
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/attributes?traitDbId={primary_attribute_trait_db_id}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "attribute traitDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let trait_filtered_attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_contains(
        &trait_filtered_attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attribute traitDbId filter",
    )?;
    require_not_contains(
        &trait_filtered_attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attribute traitDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributes?methodDbId={}&pageSize=50",
            seeded.tenant_a.secondary_method_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "attribute methodDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let method_filtered_attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_contains(
        &method_filtered_attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attribute methodDbId filter",
    )?;
    require_not_contains(
        &method_filtered_attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attribute methodDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributes?scaleDbId={}&pageSize=50",
            seeded.tenant_a.secondary_scale_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "attribute scaleDbId filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let scale_filtered_attribute_ids = list_field_values(&body, "attributeDbId")?;
    require_contains(
        &scale_filtered_attribute_ids,
        &seeded.tenant_a.secondary_attribute_db_id,
        "attribute scaleDbId filter",
    )?;
    require_not_contains(
        &scale_filtered_attribute_ids,
        &seeded.tenant_a.attribute_db_id,
        "attribute scaleDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/attributes?attributeName=codex-live-no-match&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "attribute no-match filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 1)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(router, token, "/brapi/v2/attributes?pageSize=1").await?;
    require_status(status, StatusCode::OK, "attribute pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/attributes/{}", seeded.tenant_a.attribute_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant attribute detail")?;
    require_json_string(
        &body,
        "/result/attributeDbId",
        &seeded.tenant_a.attribute_db_id,
    )?;
    require_json_string(
        &body,
        "/result/attributeName",
        &seeded.tenant_a.attribute_name,
    )?;
    require_json_string(
        &body,
        "/result/attributePUI",
        &format!("https://example.test/{}", seeded.tenant_a.attribute_db_id),
    )?;
    require_json_string(
        &body,
        "/result/attributeDescription",
        "Grain color scored at harvest",
    )?;
    require_json_string(
        &body,
        "/result/attributeCategory",
        &seeded.tenant_a.attribute_category,
    )?;
    require_json_string(
        &body,
        "/result/commonCropName",
        &seeded.tenant_a.germplasm_common_crop_name,
    )?;
    require_json_string(&body, "/result/contextOfUse/0", "field")?;
    require_json_string(&body, "/result/contextOfUse/1", "harvest")?;
    require_json_string(&body, "/result/defaultValue", "white")?;
    require_json_string(
        &body,
        "/result/documentationURL",
        "https://example.test/attribute-primary",
    )?;
    require_json_string(&body, "/result/growthStage", "maturity")?;
    require_json_string(&body, "/result/institution", "Bijmantra Live Lab")?;
    require_json_string(&body, "/result/language", "en")?;
    require_json_string(&body, "/result/scientist", "Anika Rao")?;
    require_json_string(&body, "/result/status", "active")?;
    require_json_string(&body, "/result/submissionTimestamp", "2026-06-19T00:00:00Z")?;
    require_json_string(&body, "/result/synonyms/0", "kernel color")?;
    require_json_string(&body, "/result/traitDbId", &primary_attribute_trait_db_id)?;
    require_json_string(&body, "/result/traitName", "Grain color")?;
    require_json_string(&body, "/result/traitDescription", "Visual grain color")?;
    require_json_string(&body, "/result/traitClass", "quality")?;
    require_json_string(&body, "/result/methodDbId", &seeded.tenant_a.method_db_id)?;
    require_json_string(&body, "/result/methodName", &seeded.tenant_a.method_name)?;
    require_json_string(
        &body,
        "/result/methodDescription",
        "Visual panel assessment",
    )?;
    require_json_string(&body, "/result/methodClass", &seeded.tenant_a.method_class)?;
    require_json_string(&body, "/result/scaleDbId", &seeded.tenant_a.scale_db_id)?;
    require_json_string(&body, "/result/scaleName", &seeded.tenant_a.scale_name)?;
    require_json_string(&body, "/result/dataType", "Categorical")?;
    require_json_string(&body, "/result/additionalInfo/kind", "primary-attribute")?;
    require_json_string(
        &body,
        "/result/externalReferences/0/referenceId",
        &seeded.tenant_a.attribute_db_id,
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributes/{}",
            seeded.tenant_a.secondary_attribute_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant secondary attribute detail")?;
    require_json_string(
        &body,
        "/result/attributeDbId",
        &seeded.tenant_a.secondary_attribute_db_id,
    )?;
    require_json_string(
        &body,
        "/result/attributeName",
        &seeded.tenant_a.secondary_attribute_name,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributes/{}-missing",
            seeded.tenant_a.attribute_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "missing attribute detail")?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/attributes/{}", seeded.tenant_b.attribute_db_id),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant attribute detail",
    )?;

    let (status, body) =
        get_json(router, token, "/brapi/v2/attributes/categories?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/attributes/categories")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_string(
        &body,
        "/result/data/0",
        &seeded.tenant_a.secondary_attribute_category,
    )?;
    require_json_string(&body, "/result/data/1", &seeded.tenant_a.attribute_category)?;

    let (status, body) = get_json(router, token, "/brapi/v2/attributevalues?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/attributevalues")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let attribute_value_ids = list_field_values(&body, "attributeValueDbId")?;
    require_order_prefix(
        &attribute_value_ids,
        &[
            seeded.tenant_a.secondary_attribute_value_db_id.as_str(),
            seeded.tenant_a.attribute_value_db_id.as_str(),
        ],
        "attribute value list",
    )?;
    require_contains(
        &attribute_value_ids,
        &seeded.tenant_a.attribute_value_db_id,
        "attribute value list",
    )?;
    require_contains(
        &attribute_value_ids,
        &seeded.tenant_a.secondary_attribute_value_db_id,
        "attribute value list",
    )?;
    require_not_contains(
        &attribute_value_ids,
        &seeded.tenant_b.attribute_value_db_id,
        "attribute value list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributevalues?attributeDbId={}&pageSize=50",
            seeded.tenant_a.attribute_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "attribute value attributeDbId filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let attribute_filtered_value_ids = list_field_values(&body, "attributeValueDbId")?;
    require_contains(
        &attribute_filtered_value_ids,
        &seeded.tenant_a.attribute_value_db_id,
        "attribute value attributeDbId filter",
    )?;
    require_not_contains(
        &attribute_filtered_value_ids,
        &seeded.tenant_a.secondary_attribute_value_db_id,
        "attribute value attributeDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/attributevalues?attributeName={attribute_name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "attribute value attributeName filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_value_ids = list_field_values(&body, "attributeValueDbId")?;
    require_contains(
        &name_filtered_value_ids,
        &seeded.tenant_a.attribute_value_db_id,
        "attribute value attributeName filter",
    )?;
    require_not_contains(
        &name_filtered_value_ids,
        &seeded.tenant_a.secondary_attribute_value_db_id,
        "attribute value attributeName filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributevalues?attributeValueDbId={}&pageSize=50",
            seeded.tenant_a.secondary_attribute_value_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "attribute value attributeValueDbId filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_value_ids = list_field_values(&body, "attributeValueDbId")?;
    require_contains(
        &id_filtered_value_ids,
        &seeded.tenant_a.secondary_attribute_value_db_id,
        "attribute value attributeValueDbId filter",
    )?;
    require_not_contains(
        &id_filtered_value_ids,
        &seeded.tenant_a.attribute_value_db_id,
        "attribute value attributeValueDbId filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributevalues?germplasmDbId={}&pageSize=50",
            seeded.tenant_a.secondary_germplasm_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "attribute value germplasmDbId filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let germplasm_filtered_value_ids = list_field_values(&body, "attributeValueDbId")?;
    require_contains(
        &germplasm_filtered_value_ids,
        &seeded.tenant_a.secondary_attribute_value_db_id,
        "attribute value germplasmDbId filter",
    )?;
    require_not_contains(
        &germplasm_filtered_value_ids,
        &seeded.tenant_a.attribute_value_db_id,
        "attribute value germplasmDbId filter",
    )?;

    let germplasm_name_fragment = "secondary";
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/attributevalues?germplasmName={germplasm_name_fragment}&pageSize=50"),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "attribute value germplasmName filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let germplasm_name_filtered_value_ids = list_field_values(&body, "attributeValueDbId")?;
    require_contains(
        &germplasm_name_filtered_value_ids,
        &seeded.tenant_a.secondary_attribute_value_db_id,
        "attribute value germplasmName filter",
    )?;
    require_not_contains(
        &germplasm_name_filtered_value_ids,
        &seeded.tenant_a.attribute_value_db_id,
        "attribute value germplasmName filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/attributevalues?attributeValueDbId=codex-live-no-match&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "attribute value no-match filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 1)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(router, token, "/brapi/v2/attributevalues?pageSize=1").await?;
    require_status(status, StatusCode::OK, "attribute value pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributevalues/{}",
            seeded.tenant_a.attribute_value_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant attribute value detail")?;
    require_json_string(
        &body,
        "/result/attributeValueDbId",
        &seeded.tenant_a.attribute_value_db_id,
    )?;
    require_json_string(
        &body,
        "/result/attributeDbId",
        &seeded.tenant_a.attribute_db_id,
    )?;
    require_json_string(
        &body,
        "/result/attributeName",
        &seeded.tenant_a.attribute_name,
    )?;
    require_json_string(
        &body,
        "/result/germplasmDbId",
        &seeded.tenant_a.germplasm_db_id,
    )?;
    require_json_string(
        &body,
        "/result/germplasmName",
        &seeded.tenant_a.germplasm_name,
    )?;
    require_json_string(&body, "/result/value", "white")?;
    require_json_string(&body, "/result/determinedDate", "2026-07-01")?;
    require_json_string(
        &body,
        "/result/additionalInfo/kind",
        "primary-attribute-value",
    )?;
    require_json_string(
        &body,
        "/result/externalReferences/0/referenceId",
        &seeded.tenant_a.attribute_value_db_id,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributevalues/{}-missing",
            seeded.tenant_a.attribute_value_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "missing attribute value detail",
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/attributevalues/{}",
            seeded.tenant_b.attribute_value_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant attribute value detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/breedingmethods?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/breedingmethods")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let breeding_method_ids = list_field_values(&body, "breedingMethodDbId")?;
    require_order_prefix(
        &breeding_method_ids,
        &[
            seeded.tenant_a.secondary_breeding_method_db_id.as_str(),
            seeded.tenant_a.breeding_method_db_id.as_str(),
        ],
        "breeding method list",
    )?;
    require_contains(
        &breeding_method_ids,
        &seeded.tenant_a.breeding_method_db_id,
        "breeding method list",
    )?;
    require_contains(
        &breeding_method_ids,
        &seeded.tenant_a.secondary_breeding_method_db_id,
        "breeding method list",
    )?;
    require_not_contains(
        &breeding_method_ids,
        &seeded.tenant_b.breeding_method_db_id,
        "breeding method list",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/breedingmethods?pageSize=1").await?;
    require_status(status, StatusCode::OK, "breeding method pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/breedingmethods/{}",
            seeded.tenant_a.breeding_method_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant breeding method detail")?;
    require_json_string(
        &body,
        "/result/breedingMethodDbId",
        &seeded.tenant_a.breeding_method_db_id,
    )?;
    require_json_string(
        &body,
        "/result/breedingMethodName",
        &seeded.tenant_a.breeding_method_name,
    )?;
    require_json_string(
        &body,
        "/result/abbreviation",
        &seeded.tenant_a.breeding_method_abbreviation,
    )?;
    require_json_string(
        &body,
        "/result/description",
        "Advancing generations by selecting a single seed from each plant",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/breedingmethods/{}",
            seeded.tenant_a.secondary_breeding_method_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "tenant secondary breeding method detail",
    )?;
    require_json_string(
        &body,
        "/result/breedingMethodDbId",
        &seeded.tenant_a.secondary_breeding_method_db_id,
    )?;
    require_json_string(
        &body,
        "/result/breedingMethodName",
        &seeded.tenant_a.secondary_breeding_method_name,
    )?;
    require_json_string(
        &body,
        "/result/abbreviation",
        &seeded.tenant_a.secondary_breeding_method_abbreviation,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/breedingmethods/{}-missing",
            seeded.tenant_a.breeding_method_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "missing breeding method detail",
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/breedingmethods/{}",
            seeded.tenant_b.breeding_method_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant breeding method detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/crossingprojects?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/crossingprojects")?;
    let crossing_project_ids = list_field_values(&body, "crossingProjectDbId")?;
    require_contains(
        &crossing_project_ids,
        &seeded.tenant_a.crossing_project_db_id,
        "crossing project list",
    )?;
    require_not_contains(
        &crossing_project_ids,
        &seeded.tenant_b.crossing_project_db_id,
        "crossing project list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/crossingprojects/{}",
            seeded.tenant_a.crossing_project_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant crossing project detail")?;
    require_json_string(
        &body,
        "/result/crossingProjectDbId",
        &seeded.tenant_a.crossing_project_db_id,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/crossingprojects/{}",
            seeded.tenant_b.crossing_project_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant crossing project detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/crosses?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/crosses")?;
    let cross_ids = list_field_values(&body, "crossDbId")?;
    require_contains(&cross_ids, &seeded.tenant_a.cross_db_id, "cross list")?;
    require_not_contains(&cross_ids, &seeded.tenant_b.cross_db_id, "cross list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/crosses?crossingProjectDbId={}&crossType=BIPARENTAL&pageSize=50",
            seeded.tenant_a.crossing_project_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "filtered cross list")?;
    let filtered_cross_ids = list_field_values(&body, "crossDbId")?;
    require_contains(
        &filtered_cross_ids,
        &seeded.tenant_a.cross_db_id,
        "filtered cross list",
    )?;
    require_not_contains(
        &filtered_cross_ids,
        &seeded.tenant_b.cross_db_id,
        "filtered cross list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/crosses/{}", seeded.tenant_a.cross_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant cross detail")?;
    require_json_string(&body, "/result/crossDbId", &seeded.tenant_a.cross_db_id)?;
    require_json_string(
        &body,
        "/result/crossingProjectDbId",
        &seeded.tenant_a.crossing_project_db_id,
    )?;
    require_json_string(
        &body,
        "/result/parent1DbId",
        &seeded.tenant_a.germplasm_db_id,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/crosses/{}", seeded.tenant_b.cross_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant cross detail")?;

    let (status, body) = get_json(router, token, "/brapi/v2/plannedcrosses?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/plannedcrosses")?;
    let planned_cross_ids = list_field_values(&body, "plannedCrossDbId")?;
    require_contains(
        &planned_cross_ids,
        &seeded.tenant_a.planned_cross_db_id,
        "planned cross list",
    )?;
    require_not_contains(
        &planned_cross_ids,
        &seeded.tenant_b.planned_cross_db_id,
        "planned cross list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/plannedcrosses?crossingProjectDbId={}&status=TODO&pageSize=50",
            seeded.tenant_a.crossing_project_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "filtered planned cross list")?;
    let filtered_planned_cross_ids = list_field_values(&body, "plannedCrossDbId")?;
    require_contains(
        &filtered_planned_cross_ids,
        &seeded.tenant_a.planned_cross_db_id,
        "filtered planned cross list",
    )?;
    require_not_contains(
        &filtered_planned_cross_ids,
        &seeded.tenant_b.planned_cross_db_id,
        "filtered planned cross list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/plannedcrosses/{}",
            seeded.tenant_a.planned_cross_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant planned cross detail")?;
    require_json_string(
        &body,
        "/result/plannedCrossDbId",
        &seeded.tenant_a.planned_cross_db_id,
    )?;
    require_json_string(
        &body,
        "/result/crossingProjectDbId",
        &seeded.tenant_a.crossing_project_db_id,
    )?;
    require_json_string(
        &body,
        "/result/parent1/germplasmDbId",
        &seeded.tenant_a.germplasm_db_id,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/plannedcrosses/{}",
            seeded.tenant_b.planned_cross_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant planned cross detail",
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/seedlots?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/seedlots")?;
    let seedlot_ids = list_field_values(&body, "seedLotDbId")?;
    require_order_prefix(
        &seedlot_ids,
        &[
            seeded.tenant_a.seedlot_db_id.as_str(),
            seeded.tenant_a.secondary_seedlot_db_id.as_str(),
        ],
        "seedlot list",
    )?;
    require_contains(&seedlot_ids, &seeded.tenant_a.seedlot_db_id, "seedlot list")?;
    require_contains(
        &seedlot_ids,
        &seeded.tenant_a.secondary_seedlot_db_id,
        "seedlot list",
    )?;
    require_not_contains(&seedlot_ids, &seeded.tenant_b.seedlot_db_id, "seedlot list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots?germplasmDbId={}&pageSize=50",
            seeded.tenant_a.germplasm_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot germplasm filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let germplasm_filtered_seedlot_ids = list_field_values(&body, "seedLotDbId")?;
    require_contains(
        &germplasm_filtered_seedlot_ids,
        &seeded.tenant_a.seedlot_db_id,
        "seedlot germplasm filter",
    )?;
    require_not_contains(
        &germplasm_filtered_seedlot_ids,
        &seeded.tenant_a.secondary_seedlot_db_id,
        "seedlot germplasm filter",
    )?;
    require_not_contains(
        &germplasm_filtered_seedlot_ids,
        &seeded.tenant_b.seedlot_db_id,
        "seedlot germplasm filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots?locationDbId={}&pageSize=50",
            seeded.tenant_a.null_coordinate_location_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot location filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let location_filtered_seedlot_ids = list_field_values(&body, "seedLotDbId")?;
    require_contains(
        &location_filtered_seedlot_ids,
        &seeded.tenant_a.secondary_seedlot_db_id,
        "seedlot location filter",
    )?;
    require_not_contains(
        &location_filtered_seedlot_ids,
        &seeded.tenant_a.seedlot_db_id,
        "seedlot location filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots?programDbId={}&pageSize=50",
            seeded.tenant_a.secondary_program_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot program filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let program_filtered_seedlot_ids = list_field_values(&body, "seedLotDbId")?;
    require_contains(
        &program_filtered_seedlot_ids,
        &seeded.tenant_a.secondary_seedlot_db_id,
        "seedlot program filter",
    )?;
    require_not_contains(
        &program_filtered_seedlot_ids,
        &seeded.tenant_a.seedlot_db_id,
        "seedlot program filter",
    )?;
    require_not_contains(
        &program_filtered_seedlot_ids,
        &seeded.tenant_b.secondary_seedlot_db_id,
        "seedlot program filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots?seedLotDbId={}&pageSize=50",
            seeded.tenant_a.seedlot_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_seedlot_ids = list_field_values(&body, "seedLotDbId")?;
    require_contains(
        &id_filtered_seedlot_ids,
        &seeded.tenant_a.seedlot_db_id,
        "seedlot ID filter",
    )?;
    require_not_contains(
        &id_filtered_seedlot_ids,
        &seeded.tenant_a.secondary_seedlot_db_id,
        "seedlot ID filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots?seedLotName={}&pageSize=50",
            seeded.tenant_a.secondary_seedlot_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_seedlot_ids = list_field_values(&body, "seedLotDbId")?;
    require_contains(
        &name_filtered_seedlot_ids,
        &seeded.tenant_a.secondary_seedlot_db_id,
        "seedlot name filter",
    )?;
    require_not_contains(
        &name_filtered_seedlot_ids,
        &seeded.tenant_a.seedlot_db_id,
        "seedlot name filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/seedlots?seedLotName=codex-live-no-match&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot no-match filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/seedlots/{}", seeded.tenant_a.seedlot_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant seedlot detail")?;
    require_json_string(&body, "/result/seedLotDbId", &seeded.tenant_a.seedlot_db_id)?;
    require_json_string(&body, "/result/seedLotName", &seeded.tenant_a.seedlot_name)?;
    require_json_string(
        &body,
        "/result/germplasmDbId",
        &seeded.tenant_a.germplasm_db_id,
    )?;
    require_json_string(
        &body,
        "/result/locationDbId",
        &seeded.tenant_a.location_db_id,
    )?;
    require_json_string(&body, "/result/programDbId", &seeded.tenant_a.program_db_id)?;
    require_json_u64(&body, "/result/count", 42)?;
    require_json_string(&body, "/result/units", "seeds")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots/{}",
            seeded.tenant_a.secondary_seedlot_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant secondary seedlot detail")?;
    require_json_string(
        &body,
        "/result/seedLotDbId",
        &seeded.tenant_a.secondary_seedlot_db_id,
    )?;
    require_json_string(
        &body,
        "/result/seedLotName",
        &seeded.tenant_a.secondary_seedlot_name,
    )?;
    require_json_string(
        &body,
        "/result/germplasmDbId",
        &seeded.tenant_a.secondary_germplasm_db_id,
    )?;
    require_json_string(
        &body,
        "/result/locationDbId",
        &seeded.tenant_a.null_coordinate_location_db_id,
    )?;
    require_json_string(
        &body,
        "/result/programDbId",
        &seeded.tenant_a.secondary_program_db_id,
    )?;

    let (status, _) = get_json(
        router,
        token,
        &format!("/brapi/v2/seedlots/{}", seeded.tenant_b.seedlot_db_id),
    )
    .await?;
    require_status(status, StatusCode::NOT_FOUND, "cross-tenant seedlot detail")?;

    let (status, body) =
        get_json(router, token, "/brapi/v2/seedlots/transactions?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/seedlots/transactions")?;
    let transaction_ids = list_field_values(&body, "transactionDbId")?;
    require_order_prefix(
        &transaction_ids,
        &[
            seeded.tenant_a.transaction_db_id.as_str(),
            seeded.tenant_a.secondary_transaction_db_id.as_str(),
        ],
        "seedlot transaction list",
    )?;
    require_contains(
        &transaction_ids,
        &seeded.tenant_a.transaction_db_id,
        "seedlot transaction list",
    )?;
    require_contains(
        &transaction_ids,
        &seeded.tenant_a.secondary_transaction_db_id,
        "seedlot transaction list",
    )?;
    require_not_contains(
        &transaction_ids,
        &seeded.tenant_b.transaction_db_id,
        "seedlot transaction list",
    )?;
    require_json_string(
        &body,
        "/result/data/0/transactionTimestamp",
        "2026-06-17T00:00:00Z",
    )?;
    require_json_f64(&body, "/result/data/0/amount", 7.0)?;
    require_json_string(
        &body,
        "/result/data/1/transactionTimestamp",
        "2026-06-18T00:00:00Z",
    )?;
    require_json_f64(&body, "/result/data/1/amount", 3.0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots/transactions?seedLotDbId={}&pageSize=50",
            seeded.tenant_a.seedlot_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot transaction seedlot filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let seedlot_filtered_transaction_ids = list_field_values(&body, "transactionDbId")?;
    require_contains(
        &seedlot_filtered_transaction_ids,
        &seeded.tenant_a.transaction_db_id,
        "seedlot transaction seedlot filter",
    )?;
    require_not_contains(
        &seedlot_filtered_transaction_ids,
        &seeded.tenant_a.secondary_transaction_db_id,
        "seedlot transaction seedlot filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots/transactions?transactionDbId={}&pageSize=50",
            seeded.tenant_a.secondary_transaction_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "seedlot transaction ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_transaction_ids = list_field_values(&body, "transactionDbId")?;
    require_contains(
        &id_filtered_transaction_ids,
        &seeded.tenant_a.secondary_transaction_db_id,
        "seedlot transaction ID filter",
    )?;
    require_not_contains(
        &id_filtered_transaction_ids,
        &seeded.tenant_a.transaction_db_id,
        "seedlot transaction ID filter",
    )?;
    require_not_contains(
        &id_filtered_transaction_ids,
        &seeded.tenant_b.secondary_transaction_db_id,
        "seedlot transaction ID filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/seedlots/transactions?transactionDbId=codex-live-no-match&pageSize=50",
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "seedlot transaction no-match filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots/{}/transactions?pageSize=50",
            seeded.tenant_a.seedlot_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant seedlot-scoped transactions")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let scoped_transaction_ids = list_field_values(&body, "transactionDbId")?;
    require_contains(
        &scoped_transaction_ids,
        &seeded.tenant_a.transaction_db_id,
        "seedlot-scoped transaction list",
    )?;
    require_not_contains(
        &scoped_transaction_ids,
        &seeded.tenant_a.secondary_transaction_db_id,
        "seedlot-scoped transaction list",
    )?;
    require_json_string(
        &body,
        "/result/data/0/transactionTimestamp",
        "2026-06-17T00:00:00Z",
    )?;
    require_json_f64(&body, "/result/data/0/amount", 7.0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots/{}/transactions?pageSize=50",
            seeded.tenant_a.secondary_seedlot_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "tenant secondary seedlot-scoped transactions",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let secondary_scoped_transaction_ids = list_field_values(&body, "transactionDbId")?;
    require_contains(
        &secondary_scoped_transaction_ids,
        &seeded.tenant_a.secondary_transaction_db_id,
        "secondary seedlot-scoped transaction list",
    )?;
    require_not_contains(
        &secondary_scoped_transaction_ids,
        &seeded.tenant_a.transaction_db_id,
        "secondary seedlot-scoped transaction list",
    )?;
    require_json_string(
        &body,
        "/result/data/0/transactionTimestamp",
        "2026-06-18T00:00:00Z",
    )?;
    require_json_f64(&body, "/result/data/0/amount", 3.0)?;

    let (status, _) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/seedlots/{}/transactions",
            seeded.tenant_b.seedlot_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::NOT_FOUND,
        "cross-tenant seedlot-scoped transactions",
    )?;

    let (status, body) = get_json(router, token, "/api/v2/seed-inventory/summary").await?;
    require_status(status, StatusCode::OK, "seed inventory summary")?;
    require_json_bool(&body, "/success", true)?;
    require_json_u64(&body, "/total_lots", 2)?;
    require_json_f64(&body, "/total_quantity_g", 55.0)?;
    require_json_u64(&body, "/by_status/active", 1)?;
    require_json_u64(&body, "/by_status/low_stock", 1)?;
    require_json_u64(&body, "/by_storage_type/long_term", 1)?;
    require_json_u64(&body, "/by_storage_type/short_term", 1)?;
    require_json_u64(&body, "/by_species/Oryza sativa/lots", 1)?;
    require_json_f64(&body, "/by_species/Oryza sativa/quantity_g", 42.0)?;
    require_json_u64(&body, "/by_species/Oryza glaberrima/lots", 1)?;
    require_json_f64(&body, "/by_species/Oryza glaberrima/quantity_g", 13.0)?;
    require_array_len(&body, "/lots_needing_viability_test", 1)?;
    require_json_string(
        &body,
        "/lots_needing_viability_test/0/lot_id",
        &seeded.tenant_a.seedlot_db_id,
    )?;
    require_json_f64(&body, "/lots_needing_viability_test/0/last_viability", 82.5)?;
    let days_since_test = body
        .pointer("/lots_needing_viability_test/0/days_since_test")
        .and_then(Value::as_i64)
        .ok_or_else(|| test_error("missing days_since_test in seed inventory summary"))?;
    if days_since_test <= 365 {
        return Err(test_error(format!(
            "expected seed inventory summary days_since_test > 365, got {days_since_test}"
        )));
    }
    require_json_u64(&body, "/pending_requests", 0)?;

    let (status, body) = get_json(router, token, "/brapi/v2/variantsets?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/variantsets")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let variant_set_ids = list_field_values(&body, "variantSetDbId")?;
    require_order_prefix(
        &variant_set_ids,
        &[
            seeded.tenant_a.variant_set_db_id.as_str(),
            seeded.tenant_a.secondary_variant_set_db_id.as_str(),
        ],
        "variant set list",
    )?;
    require_contains(
        &variant_set_ids,
        &seeded.tenant_a.variant_set_db_id,
        "variant set list",
    )?;
    require_contains(
        &variant_set_ids,
        &seeded.tenant_a.secondary_variant_set_db_id,
        "variant set list",
    )?;
    require_not_contains(
        &variant_set_ids,
        &seeded.tenant_b.variant_set_db_id,
        "variant set list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variantsets?variantSetDbId={}&pageSize=50",
            seeded.tenant_a.secondary_variant_set_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "variant set ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/variantSetDbId",
        &seeded.tenant_a.secondary_variant_set_db_id,
    )?;
    require_json_string(
        &body,
        "/result/data/0/variantSetName",
        &seeded.tenant_a.secondary_variant_set_name,
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variantsets?studyDbId={}&pageSize=50",
            seeded.tenant_a.study_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "variant set study filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let study_filtered_variant_set_ids = list_field_values(&body, "variantSetDbId")?;
    require_contains(
        &study_filtered_variant_set_ids,
        &seeded.tenant_a.variant_set_db_id,
        "variant set study filter",
    )?;
    require_contains(
        &study_filtered_variant_set_ids,
        &seeded.tenant_a.secondary_variant_set_db_id,
        "variant set study filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variantsets?referenceSetDbId={}&pageSize=50",
            seeded.tenant_a.secondary_reference_set_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "variant set reference filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/variantSetDbId",
        &seeded.tenant_a.secondary_variant_set_db_id,
    )?;
    require_json_string(
        &body,
        "/result/data/0/referenceSetDbId",
        &seeded.tenant_a.secondary_reference_set_db_id,
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variantsets?studyDbId={}&pageSize=50",
            seeded.tenant_b.study_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "cross-tenant variant set study filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(router, token, "/brapi/v2/variantsets?pageSize=1").await?;
    require_status(status, StatusCode::OK, "variant set pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variantsets/{}",
            seeded.tenant_a.variant_set_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant variant set detail")?;
    require_json_string(
        &body,
        "/result/variantSetDbId",
        &seeded.tenant_a.variant_set_db_id,
    )?;
    require_json_string(
        &body,
        "/result/variantSetName",
        &seeded.tenant_a.variant_set_name,
    )?;
    require_json_string(
        &body,
        "/result/referenceSetDbId",
        &seeded.tenant_a.reference_set_db_id,
    )?;
    require_json_string(&body, "/result/studyDbId", &seeded.tenant_a.study_db_id)?;
    require_json_string(
        &body,
        "/result/analysis/0/analysisName",
        "Live genotyping fixture",
    )?;
    require_json_string(&body, "/result/availableFormats/0/dataFormat", "VCF")?;
    require_json_u64(&body, "/result/callSetCount", 1)?;
    require_json_u64(&body, "/result/variantCount", 0)?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/variantsets/{}",
            seeded.tenant_b.variant_set_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "cross-tenant variant set detail")?;
    require_json_null(&body, "/result")?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(router, token, "/brapi/v2/callsets?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/callsets")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let callset_ids = list_field_values(&body, "callSetDbId")?;
    require_order_prefix(
        &callset_ids,
        &[
            seeded.tenant_a.call_set_db_id.as_str(),
            seeded.tenant_a.secondary_call_set_db_id.as_str(),
        ],
        "callset list",
    )?;
    require_contains(
        &callset_ids,
        &seeded.tenant_a.call_set_db_id,
        "callset list",
    )?;
    require_contains(
        &callset_ids,
        &seeded.tenant_a.secondary_call_set_db_id,
        "callset list",
    )?;
    require_not_contains(
        &callset_ids,
        &seeded.tenant_b.call_set_db_id,
        "callset list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/callsets?callSetDbId={}&pageSize=50",
            seeded.tenant_a.call_set_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "callset ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_callset_ids = list_field_values(&body, "callSetDbId")?;
    require_contains(
        &id_filtered_callset_ids,
        &seeded.tenant_a.call_set_db_id,
        "callset ID filter",
    )?;
    require_not_contains(
        &id_filtered_callset_ids,
        &seeded.tenant_a.secondary_call_set_db_id,
        "callset ID filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/callsets?callSetName={}&pageSize=50",
            seeded.tenant_a.secondary_call_set_name
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "callset name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let name_filtered_callset_ids = list_field_values(&body, "callSetDbId")?;
    require_contains(
        &name_filtered_callset_ids,
        &seeded.tenant_a.secondary_call_set_db_id,
        "callset name filter",
    )?;
    require_not_contains(
        &name_filtered_callset_ids,
        &seeded.tenant_a.call_set_db_id,
        "callset name filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/callsets?sampleDbId={}&pageSize=50",
            seeded.tenant_a.secondary_sample_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "callset sample filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let sample_filtered_callset_ids = list_field_values(&body, "callSetDbId")?;
    require_contains(
        &sample_filtered_callset_ids,
        &seeded.tenant_a.secondary_call_set_db_id,
        "callset sample filter",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/callsets?variantSetDbId={}&pageSize=50",
            seeded.tenant_a.secondary_variant_set_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "callset variant set filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let variant_set_filtered_callset_ids = list_field_values(&body, "callSetDbId")?;
    require_contains(
        &variant_set_filtered_callset_ids,
        &seeded.tenant_a.secondary_call_set_db_id,
        "callset variant set filter",
    )?;
    require_json_string(
        &body,
        "/result/data/0/variantSetDbIds/0",
        &seeded.tenant_a.secondary_variant_set_db_id,
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/callsets?pageSize=1").await?;
    require_status(status, StatusCode::OK, "callset pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/callsets/{}", seeded.tenant_a.call_set_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant callset detail")?;
    require_json_string(
        &body,
        "/result/callSetDbId",
        &seeded.tenant_a.call_set_db_id,
    )?;
    require_json_string(&body, "/result/callSetName", &seeded.tenant_a.call_set_name)?;
    require_json_string(&body, "/result/sampleDbId", &seeded.tenant_a.sample_db_id)?;
    require_json_string(
        &body,
        "/result/variantSetDbIds/0",
        &seeded.tenant_a.variant_set_db_id,
    )?;
    require_json_string(&body, "/result/created", "2026-06-19T00:00:00Z")?;
    require_json_string(&body, "/result/updated", "2026-06-20T00:00:00Z")?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/callsets/{}", seeded.tenant_b.call_set_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "cross-tenant callset detail")?;
    require_json_null(&body, "/result")?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(router, token, "/brapi/v2/maps?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/maps")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let map_ids = list_field_values(&body, "mapDbId")?;
    require_order_prefix(
        &map_ids,
        &[
            seeded.tenant_a.map_db_id.as_str(),
            seeded.tenant_a.secondary_map_db_id.as_str(),
        ],
        "map list",
    )?;
    require_contains(&map_ids, &seeded.tenant_a.map_db_id, "map list")?;
    require_contains(&map_ids, &seeded.tenant_a.secondary_map_db_id, "map list")?;
    require_not_contains(&map_ids, &seeded.tenant_b.map_db_id, "map list")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/maps?mapDbId={}&pageSize=50",
            seeded.tenant_a.map_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "map ID filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    let id_filtered_map_ids = list_field_values(&body, "mapDbId")?;
    require_contains(
        &id_filtered_map_ids,
        &seeded.tenant_a.map_db_id,
        "map ID filter",
    )?;
    require_not_contains(
        &id_filtered_map_ids,
        &seeded.tenant_a.secondary_map_db_id,
        "map ID filter",
    )?;

    let primary_map_pui = format!("doi:10.1/{}", seeded.tenant_a.map_db_id);
    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/maps?mapPUI={primary_map_pui}&pageSize=50"),
    )
    .await?;
    require_status(status, StatusCode::OK, "map PUI filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(&body, "/result/data/0/mapDbId", &seeded.tenant_a.map_db_id)?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/maps?commonCropName=chick&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "map crop filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/mapDbId",
        &seeded.tenant_a.secondary_map_db_id,
    )?;
    require_json_string(
        &body,
        "/result/data/0/mapName",
        &seeded.tenant_a.secondary_map_name,
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/maps?scientificName=Cicer&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "map scientific name filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/mapDbId",
        &seeded.tenant_a.secondary_map_db_id,
    )?;

    let (status, body) =
        get_json(router, token, "/brapi/v2/maps?type=Physical&pageSize=50").await?;
    require_status(status, StatusCode::OK, "map type filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/mapDbId",
        &seeded.tenant_a.secondary_map_db_id,
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/maps?pageSize=1").await?;
    require_status(status, StatusCode::OK, "map pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/maps/{}", seeded.tenant_a.map_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant map detail")?;
    require_json_string(&body, "/result/mapDbId", &seeded.tenant_a.map_db_id)?;
    require_json_string(&body, "/result/mapName", &seeded.tenant_a.map_name)?;
    require_json_string(&body, "/result/mapPUI", &primary_map_pui)?;
    require_json_string(&body, "/result/commonCropName", "rice")?;
    require_json_string(&body, "/result/type", "Genetic")?;
    require_json_string(&body, "/result/unit", "cM")?;
    require_json_string(&body, "/result/scientificName", "Oryza sativa")?;
    require_json_string(&body, "/result/publishedDate", "2026-06-19")?;
    require_json_string(
        &body,
        "/result/documentationURL",
        "https://example.test/map-primary",
    )?;
    require_json_u64(&body, "/result/linkageGroupCount", 1)?;
    require_json_u64(&body, "/result/markerCount", 42)?;
    require_json_string(
        &body,
        "/result/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/maps/{}/linkagegroups?pageSize=50",
            seeded.tenant_a.map_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "tenant map linkage groups")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/linkageGroupName",
        &seeded.tenant_a.linkage_group_name,
    )?;
    require_json_f64(&body, "/result/data/0/maxPosition", 123.4)?;
    require_json_u64(&body, "/result/data/0/markerCount", 42)?;
    require_json_string(&body, "/result/data/0/mapDbId", &seeded.tenant_a.map_db_id)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/maps/{}/linkagegroups?pageSize=50",
            seeded.tenant_a.secondary_map_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "tenant secondary map linkage groups",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/linkageGroupName",
        &seeded.tenant_a.secondary_linkage_group_name,
    )?;
    require_json_f64(&body, "/result/data/0/maxPosition", 987.6)?;
    require_json_u64(&body, "/result/data/0/markerCount", 13)?;
    require_json_string(
        &body,
        "/result/data/0/mapDbId",
        &seeded.tenant_a.secondary_map_db_id,
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/markerpositions?pageSize=50").await?;
    require_status(status, StatusCode::OK, "/brapi/v2/markerpositions")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    let marker_position_ids = list_field_values(&body, "markerPositionDbId")?;
    require_order_prefix(
        &marker_position_ids,
        &[
            seeded.tenant_a.marker_position_db_id.as_str(),
            seeded.tenant_a.secondary_marker_position_db_id.as_str(),
        ],
        "marker position list",
    )?;
    require_contains(
        &marker_position_ids,
        &seeded.tenant_a.marker_position_db_id,
        "marker position list",
    )?;
    require_contains(
        &marker_position_ids,
        &seeded.tenant_a.secondary_marker_position_db_id,
        "marker position list",
    )?;
    require_not_contains(
        &marker_position_ids,
        &seeded.tenant_b.marker_position_db_id,
        "marker position list",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/markerpositions?mapDbId={}&pageSize=50",
            seeded.tenant_a.map_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "marker position map filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/markerPositionDbId",
        &seeded.tenant_a.marker_position_db_id,
    )?;
    require_json_string(
        &body,
        "/result/data/0/variantDbId",
        &seeded.tenant_a.marker_variant_db_id,
    )?;
    require_json_string(
        &body,
        "/result/data/0/variantName",
        &seeded.tenant_a.marker_variant_name,
    )?;
    require_json_string(&body, "/result/data/0/mapDbId", &seeded.tenant_a.map_db_id)?;
    require_json_string(&body, "/result/data/0/mapName", &seeded.tenant_a.map_name)?;
    require_json_string(
        &body,
        "/result/data/0/linkageGroupName",
        &seeded.tenant_a.linkage_group_name,
    )?;
    require_json_f64(&body, "/result/data/0/position", 12.5)?;
    require_json_string(
        &body,
        "/result/data/0/additionalInfo/fixture",
        "live-postgres-brapi",
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/markerpositions?linkageGroupName={}&pageSize=50",
            seeded.tenant_a.secondary_linkage_group_name
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "marker position linkage group filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/markerPositionDbId",
        &seeded.tenant_a.secondary_marker_position_db_id,
    )?;
    require_json_string(
        &body,
        "/result/data/0/mapDbId",
        &seeded.tenant_a.secondary_map_db_id,
    )?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/markerpositions?variantDbId={}&pageSize=50",
            seeded.tenant_a.secondary_marker_variant_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "marker position variant filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/variantName",
        &seeded.tenant_a.secondary_marker_variant_name,
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/markerpositions?maxPosition=20&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "marker position max filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/markerPositionDbId",
        &seeded.tenant_a.marker_position_db_id,
    )?;

    let (status, body) = get_json(
        router,
        token,
        "/brapi/v2/markerpositions?minPosition=80&pageSize=50",
    )
    .await?;
    require_status(status, StatusCode::OK, "marker position min filter")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 1)?;
    require_json_string(
        &body,
        "/result/data/0/markerPositionDbId",
        &seeded.tenant_a.secondary_marker_position_db_id,
    )?;

    let (status, body) = get_json(router, token, "/brapi/v2/markerpositions?pageSize=1").await?;
    require_status(status, StatusCode::OK, "marker position pagination")?;
    require_json_u64(&body, "/metadata/pagination/pageSize", 1)?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 2)?;
    require_json_u64(&body, "/metadata/pagination/totalPages", 2)?;
    require_array_len(&body, "/result/data", 1)?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/markerpositions?mapDbId={}&pageSize=50",
            seeded.tenant_b.map_db_id
        ),
    )
    .await?;
    require_status(
        status,
        StatusCode::OK,
        "cross-tenant marker position map filter",
    )?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    let (status, body) = get_json(
        router,
        token,
        &format!("/brapi/v2/maps/{}", seeded.tenant_b.map_db_id),
    )
    .await?;
    require_status(status, StatusCode::OK, "cross-tenant map detail")?;
    require_json_null(&body, "/result")?;
    require_json_string(&body, "/metadata/status/0/messageType", "ERROR")?;

    let (status, body) = get_json(
        router,
        token,
        &format!(
            "/brapi/v2/maps/{}/linkagegroups?pageSize=50",
            seeded.tenant_b.map_db_id
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, "cross-tenant map linkage groups")?;
    require_json_u64(&body, "/metadata/pagination/totalCount", 0)?;
    require_array_len(&body, "/result/data", 0)?;

    Ok(())
}

async fn assert_live_pagination_load_windows(
    router: &Router,
    token: &str,
    seeded: &SeededData,
    prefix: &str,
) -> TestResult {
    let expected_total = (2 + PAGINATION_LOAD_EXTRA_ROWS) as u64;
    let last_index = PAGINATION_LOAD_EXTRA_ROWS - 1;
    let first_program_id = format!("{prefix}-pagination-load-program-000");
    let last_program_id = format!("{prefix}-pagination-load-program-{last_index:03}");
    assert_pagination_load_route(
        router,
        token,
        PaginationLoadCase {
            path: "/brapi/v2/programs",
            id_field: "programDbId",
            context: "program pagination load",
            expected_total,
            max_page_size: 1000,
            first_extra_id: &first_program_id,
            last_extra_id: &last_program_id,
            forbidden_id: &seeded.tenant_b.program_db_id,
        },
    )
    .await?;

    let first_germplasm_id = format!("{prefix}-pagination-load-germplasm-000");
    let last_germplasm_id = format!("{prefix}-pagination-load-germplasm-{last_index:03}");
    assert_pagination_load_route(
        router,
        token,
        PaginationLoadCase {
            path: "/brapi/v2/germplasm",
            id_field: "germplasmDbId",
            context: "germplasm pagination load",
            expected_total,
            max_page_size: 1000,
            first_extra_id: &first_germplasm_id,
            last_extra_id: &last_germplasm_id,
            forbidden_id: &seeded.tenant_b.germplasm_db_id,
        },
    )
    .await?;

    Ok(())
}

struct PaginationLoadCase<'a> {
    path: &'a str,
    id_field: &'a str,
    context: &'a str,
    expected_total: u64,
    max_page_size: u64,
    first_extra_id: &'a str,
    last_extra_id: &'a str,
    forbidden_id: &'a str,
}

async fn assert_pagination_load_route(
    router: &Router,
    token: &str,
    case: PaginationLoadCase<'_>,
) -> TestResult {
    let over_cap_path = format!("{}?pageSize={}", case.path, case.max_page_size * 5);
    let (status, body) = get_json(router, token, &over_cap_path).await?;
    require_status(status, StatusCode::OK, case.context)?;
    require_json_u64(&body, "/metadata/pagination/currentPage", 0)?;
    require_json_u64(&body, "/metadata/pagination/pageSize", case.max_page_size)?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalCount",
        case.expected_total,
    )?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalPages",
        pagination_total_pages(case.expected_total, case.max_page_size),
    )?;
    require_array_len(&body, "/result/data", case.expected_total as usize)?;
    let all_ids = list_field_values(&body, case.id_field)?;
    require_contains(&all_ids, case.first_extra_id, case.context)?;
    require_contains(&all_ids, case.last_extra_id, case.context)?;
    require_not_contains(&all_ids, case.forbidden_id, case.context)?;

    let window_page_size = 10;
    let (status, body) = get_json(
        router,
        token,
        &format!("{}?page=1&pageSize={window_page_size}", case.path),
    )
    .await?;
    require_status(status, StatusCode::OK, case.context)?;
    require_json_u64(&body, "/metadata/pagination/currentPage", 1)?;
    require_json_u64(&body, "/metadata/pagination/pageSize", window_page_size)?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalCount",
        case.expected_total,
    )?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalPages",
        pagination_total_pages(case.expected_total, window_page_size),
    )?;
    require_array_len(&body, "/result/data", window_page_size as usize)?;

    let tail_page = case.expected_total / window_page_size;
    let tail_len = case.expected_total - (tail_page * window_page_size);
    let (status, body) = get_json(
        router,
        token,
        &format!("{}?page={tail_page}&pageSize={window_page_size}", case.path),
    )
    .await?;
    require_status(status, StatusCode::OK, case.context)?;
    require_json_u64(&body, "/metadata/pagination/currentPage", tail_page)?;
    require_json_u64(&body, "/metadata/pagination/pageSize", window_page_size)?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalCount",
        case.expected_total,
    )?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalPages",
        pagination_total_pages(case.expected_total, window_page_size),
    )?;
    require_array_len(&body, "/result/data", tail_len as usize)?;

    let empty_page = pagination_total_pages(case.expected_total, window_page_size);
    let (status, body) = get_json(
        router,
        token,
        &format!(
            "{}?page={empty_page}&pageSize={window_page_size}",
            case.path
        ),
    )
    .await?;
    require_status(status, StatusCode::OK, case.context)?;
    require_json_u64(&body, "/metadata/pagination/currentPage", empty_page)?;
    require_json_u64(&body, "/metadata/pagination/pageSize", window_page_size)?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalCount",
        case.expected_total,
    )?;
    require_json_u64(
        &body,
        "/metadata/pagination/totalPages",
        pagination_total_pages(case.expected_total, window_page_size),
    )?;
    require_array_len(&body, "/result/data", 0)?;

    Ok(())
}

fn pagination_total_pages(total_count: u64, page_size: u64) -> u64 {
    if page_size == 0 {
        return 0;
    }
    total_count.div_ceil(page_size)
}

async fn seed_brapi_fixture(pool: &PgPool, prefix: &str) -> TestResult<SeededData> {
    let mut tx = pool.begin().await?;
    set_admin_context(&mut tx).await?;
    let tenant_a = seed_tenant(&mut tx, prefix, "a").await?;
    let tenant_b = seed_tenant(&mut tx, prefix, "b").await?;
    tx.commit().await?;

    Ok(SeededData { tenant_a, tenant_b })
}

async fn seed_pagination_load_rows(
    pool: &PgPool,
    prefix: &str,
    tenant: &SeededTenant,
) -> TestResult {
    let mut tx = pool.begin().await?;
    set_admin_context(&mut tx).await?;

    for index in 0..PAGINATION_LOAD_EXTRA_ROWS {
        let program_db_id = format!("{prefix}-pagination-load-program-{index:03}");
        let program_name = format!("{prefix}-pagination-load-program-name-{index:03}");
        let program_abbreviation = format!("LDP{index:03}");
        sqlx::query(
            r#"
            INSERT INTO programs (
                created_at,
                updated_at,
                organization_id,
                program_db_id,
                program_name,
                abbreviation,
                objective,
                additional_info,
                external_references
            )
            VALUES (
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                $1,
                $2,
                $3,
                $4,
                'Pagination load program generated by the live BrAPI integration test',
                $5,
                $6
            )
            "#,
        )
        .bind(tenant.org_id)
        .bind(&program_db_id)
        .bind(&program_name)
        .bind(&program_abbreviation)
        .bind(Json(json!({
            "fixture": "live-postgres-brapi",
            "load": "pagination",
            "row": index
        })))
        .bind(Json(json!([
            {"referenceSource": "live-test", "referenceId": program_db_id}
        ])))
        .execute(&mut *tx)
        .await?;

        let germplasm_db_id = format!("{prefix}-pagination-load-germplasm-{index:03}");
        let germplasm_name = format!("{prefix}-pagination-load-germplasm-name-{index:03}");
        sqlx::query(
            r#"
            INSERT INTO germplasm (
                created_at,
                updated_at,
                organization_id,
                germplasm_db_id,
                germplasm_name,
                default_display_name,
                common_crop_name,
                genus,
                species,
                synonyms,
                donors,
                additional_info,
                external_references
            )
            VALUES (
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                $1,
                $2,
                $3,
                $3,
                'rice',
                'Oryza',
                'Oryza-sativa',
                $4,
                $5,
                $6,
                $7
            )
            "#,
        )
        .bind(tenant.org_id)
        .bind(&germplasm_db_id)
        .bind(&germplasm_name)
        .bind(Json(json!([format!("pagination-load-{index:03}")])))
        .bind(Json(json!([])))
        .bind(Json(json!({
            "fixture": "live-postgres-brapi",
            "load": "pagination",
            "row": index
        })))
        .bind(Json(json!([
            {"referenceSource": "live-test", "referenceId": germplasm_db_id}
        ])))
        .execute(&mut *tx)
        .await?;
    }

    tx.commit().await?;
    Ok(())
}

async fn seed_tenant(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    prefix: &str,
    label: &str,
) -> TestResult<SeededTenant> {
    let org_name = format!("{prefix}-org-{label}");
    let email = format!("{prefix}-{label}@example.test");
    let inactive_email = format!("{prefix}-{label}-inactive@example.test");
    let program_db_id = format!("{prefix}-program-{label}");
    let secondary_program_db_id = format!("{prefix}-program-{label}-secondary");
    let program_name = format!("{prefix}-program-name-{label}");
    let secondary_program_name = format!("{prefix}-program-name-{label}-secondary");
    let program_abbreviation = format!("LP-{label}");
    let secondary_program_abbreviation = format!("LP2-{label}");
    let location_db_id = format!("{prefix}-location-{label}");
    let null_coordinate_location_db_id = format!("{prefix}-location-{label}-null");
    let location_type = "FIELD".to_string();
    let trial_db_id = format!("{prefix}-trial-{label}");
    let inactive_trial_db_id = format!("{prefix}-trial-{label}-inactive");
    let trial_start_date = "2026-06-01".to_string();
    let trial_end_date = "2026-10-31".to_string();
    let study_db_id = format!("{prefix}-study-{label}");
    let inactive_study_db_id = format!("{prefix}-study-{label}-inactive");
    let null_observation_levels_study_db_id = format!("{prefix}-study-{label}-null-levels");
    let study_start_date = "2026-06-15".to_string();
    let study_end_date = "2026-09-30".to_string();
    let season_db_id = format!("{prefix}-season-{label}-2026");
    let previous_season_db_id = format!("{prefix}-season-{label}-2025");
    let season_year = 2026;
    let previous_season_year = 2025;
    let person_db_id = format!("{prefix}-person-{label}");
    let secondary_person_db_id = format!("{prefix}-person-{label}-secondary");
    let person_first_name = format!("Anika{label}");
    let person_last_name = format!("Rao{label}");
    let secondary_person_first_name = format!("Bhavin{label}");
    let secondary_person_last_name = format!("Patel{label}");
    let list_db_id = format!("{prefix}-list-{label}");
    let secondary_list_db_id = format!("{prefix}-list-{label}-secondary");
    let list_name = format!("{prefix}-list-name-{label}");
    let secondary_list_name = format!("{prefix}-list-name-{label}-secondary");
    let list_type = "germplasm".to_string();
    let secondary_list_type = "programs".to_string();
    let list_source = "breeding-team".to_string();
    let secondary_list_source = "analytics-team".to_string();
    let ontology_db_id = format!("{prefix}-ontology-{label}");
    let secondary_ontology_db_id = format!("{prefix}-ontology-{label}-secondary");
    let ontology_name = format!("{prefix}-ontology-name-{label}");
    let secondary_ontology_name = format!("{prefix}-ontology-name-{label}-secondary");
    let germplasm_db_id = format!("{prefix}-germplasm-{label}");
    let secondary_germplasm_db_id = format!("{prefix}-germplasm-{label}-secondary");
    let germplasm_name = format!("{prefix}-germplasm-name-{label}");
    let secondary_germplasm_name = format!("{prefix}-secondary-germplasm-name-{label}");
    let germplasm_common_crop_name = "rice".to_string();
    let secondary_germplasm_common_crop_name = "chickpea".to_string();
    let germplasm_genus = "Oryza".to_string();
    let secondary_germplasm_genus = "Cicer".to_string();
    let germplasm_species = "Oryza-sativa".to_string();
    let secondary_germplasm_species = "Cicer-arietinum".to_string();
    let attribute_db_id = format!("{prefix}-attribute-{label}");
    let secondary_attribute_db_id = format!("{prefix}-attribute-{label}-secondary");
    let attribute_name = format!("{prefix}-grain-color-{label}");
    let secondary_attribute_name = format!("{prefix}-drought-score-{label}");
    let attribute_category = "Quality".to_string();
    let secondary_attribute_category = "Abiotic Stress".to_string();
    let attribute_value_db_id = format!("{prefix}-attribute-value-{label}");
    let secondary_attribute_value_db_id = format!("{prefix}-attribute-value-{label}-secondary");
    let breeding_method_db_id = format!("{prefix}-breeding-method-{label}");
    let secondary_breeding_method_db_id = format!("{prefix}-breeding-method-{label}-secondary");
    let breeding_method_name = format!("{prefix}-single-seed-descent-{label}");
    let secondary_breeding_method_name = format!("{prefix}-marker-assisted-backcross-{label}");
    let breeding_method_abbreviation = format!("SSD-{label}");
    let secondary_breeding_method_abbreviation = format!("MABC-{label}");
    let observation_variable_db_id = format!("{prefix}-trait-{label}");
    let secondary_observation_variable_db_id = format!("{prefix}-trait-{label}-secondary");
    let observation_variable_name = format!("{prefix}-plant-height-{label}");
    let secondary_observation_variable_name = format!("{prefix}-grain-quality-{label}");
    let observation_unit_db_id = format!("{prefix}-observation-unit-{label}");
    let secondary_observation_unit_db_id = format!("{prefix}-observation-unit-{label}-secondary");
    let observation_db_id = format!("{prefix}-observation-{label}");
    let secondary_observation_db_id = format!("{prefix}-observation-{label}-secondary");
    let trait_class = "agronomic".to_string();
    let secondary_trait_class = "quality".to_string();
    let trait_common_crop_name = "rice".to_string();
    let secondary_trait_common_crop_name = "chickpea".to_string();
    let method_db_id = format!("{prefix}-method-{label}");
    let secondary_method_db_id = format!("{prefix}-method-{label}-secondary");
    let method_name = format!("{prefix}-field-ruler-{label}");
    let secondary_method_name = format!("{prefix}-quality-panel-{label}");
    let method_class = "Measurement".to_string();
    let secondary_method_class = "Estimation".to_string();
    let scale_db_id = format!("{prefix}-scale-{label}");
    let secondary_scale_db_id = format!("{prefix}-scale-{label}-secondary");
    let scale_name = format!("{prefix}-centimeter-{label}");
    let secondary_scale_name = format!("{prefix}-score-{label}");
    let scale_data_type = "Numerical".to_string();
    let secondary_scale_data_type = "Ordinal".to_string();
    let crossing_project_db_id = format!("{prefix}-crossing-project-{label}");
    let cross_db_id = format!("{prefix}-cross-{label}");
    let planned_cross_db_id = format!("{prefix}-planned-cross-{label}");
    let seedlot_db_id = format!("{prefix}-seedlot-{label}");
    let secondary_seedlot_db_id = format!("{prefix}-seedlot-{label}-secondary");
    let seedlot_name = format!("{prefix}-seedlot-name-{label}");
    let secondary_seedlot_name = format!("{prefix}-seedlot-name-{label}-secondary");
    let transaction_db_id = format!("{prefix}-transaction-{label}");
    let secondary_transaction_db_id = format!("{prefix}-transaction-{label}-secondary");
    let reference_set_db_id = format!("{prefix}-reference-set-{label}");
    let secondary_reference_set_db_id = format!("{prefix}-reference-set-{label}-secondary");
    let variant_set_db_id = format!("{prefix}-variant-set-{label}");
    let secondary_variant_set_db_id = format!("{prefix}-variant-set-{label}-secondary");
    let variant_set_name = format!("{prefix}-variant-set-name-{label}");
    let secondary_variant_set_name = format!("{prefix}-variant-set-name-{label}-secondary");
    let call_set_db_id = format!("{prefix}-call-set-{label}");
    let secondary_call_set_db_id = format!("{prefix}-call-set-{label}-secondary");
    let call_set_name = format!("{prefix}-call-set-name-{label}");
    let secondary_call_set_name = format!("{prefix}-call-set-name-{label}-secondary");
    let sample_db_id = format!("{prefix}-sample-{label}");
    let secondary_sample_db_id = format!("{prefix}-sample-{label}-secondary");
    let map_db_id = format!("{prefix}-map-{label}");
    let secondary_map_db_id = format!("{prefix}-map-{label}-secondary");
    let map_name = format!("{prefix}-map-name-{label}");
    let secondary_map_name = format!("{prefix}-map-name-{label}-secondary");
    let linkage_group_name = format!("{prefix}-lg-{label}-chr1");
    let secondary_linkage_group_name = format!("{prefix}-lg-{label}-chr2");
    let marker_position_db_id = format!("{prefix}-marker-position-{label}");
    let secondary_marker_position_db_id = format!("{prefix}-marker-position-{label}-secondary");
    let marker_variant_db_id = format!("{prefix}-variant-{label}");
    let secondary_marker_variant_db_id = format!("{prefix}-variant-{label}-secondary");
    let marker_variant_name = format!("{prefix}-variant-name-{label}");
    let secondary_marker_variant_name = format!("{prefix}-variant-name-{label}-secondary");

    let org_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO organizations (created_at, updated_at, name, is_active)
        VALUES (CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, $1, TRUE)
        RETURNING id
        "#,
    )
    .bind(&org_name)
    .fetch_one(&mut **tx)
    .await?;

    let user_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO users (
            created_at,
            updated_at,
            organization_id,
            email,
            hashed_password,
            full_name,
            is_active,
            is_superuser
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            'not-used-by-live-brapi-test',
            $3,
            TRUE,
            $4
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&email)
    .bind(format!("Live BrAPI {label}"))
    .bind(label == "a")
    .fetch_one(&mut **tx)
    .await?;

    let inactive_user_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO users (
            created_at,
            updated_at,
            organization_id,
            email,
            hashed_password,
            full_name,
            is_active,
            is_superuser
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            'not-used-by-live-brapi-test',
            $3,
            FALSE,
            FALSE
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&inactive_email)
    .bind(format!("Inactive Live BrAPI {label}"))
    .fetch_one(&mut **tx)
    .await?;

    if label == "a" {
        sqlx::query(
            r#"
            INSERT INTO auth_identities (
                created_at,
                updated_at,
                organization_id,
                user_id,
                provider,
                issuer,
                subject,
                email_at_login
            )
            VALUES (
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                $1,
                $2,
                'keycloak',
                $3,
                $4,
                $5
            )
            "#,
        )
        .bind(org_id)
        .bind(user_id)
        .bind(KEYCLOAK_ISSUER)
        .bind(KEYCLOAK_SUBJECT)
        .bind(&email)
        .execute(&mut **tx)
        .await?;
    }

    sqlx::query(
        r#"
        INSERT INTO people (
            created_at,
            updated_at,
            organization_id,
            person_db_id,
            first_name,
            last_name,
            middle_name,
            email_address,
            phone_number,
            mailing_address,
            user_id,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'Live',
            $5,
            '+91-555-0100',
            'Live BrAPI integration test address',
            $6,
            $7,
            $8
        )
        "#,
    )
    .bind(org_id)
    .bind(&person_db_id)
    .bind(&person_first_name)
    .bind(&person_last_name)
    .bind(format!("{person_db_id}@example.test"))
    .bind(user_id.to_string())
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "linkedUser": true}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": person_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO people (
            created_at,
            updated_at,
            organization_id,
            person_db_id,
            first_name,
            last_name,
            middle_name,
            email_address,
            phone_number,
            mailing_address,
            user_id,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            NULL,
            $5,
            '+91-555-0101',
            'Live BrAPI integration test secondary address',
            NULL,
            $6,
            $7
        )
        "#,
    )
    .bind(org_id)
    .bind(&secondary_person_db_id)
    .bind(&secondary_person_first_name)
    .bind(&secondary_person_last_name)
    .bind(format!("{secondary_person_db_id}@example.test"))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "linkedUser": false}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_person_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO breeding_methods (
            created_at,
            updated_at,
            organization_id,
            breeding_method_db_id,
            breeding_method_name,
            abbreviation,
            description,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'Advancing generations by selecting a single seed from each plant',
            $5,
            $6
        )
        "#,
    )
    .bind(org_id)
    .bind(&breeding_method_db_id)
    .bind(&breeding_method_name)
    .bind(&breeding_method_abbreviation)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": breeding_method_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO breeding_methods (
            created_at,
            updated_at,
            organization_id,
            breeding_method_db_id,
            breeding_method_name,
            abbreviation,
            description,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'Backcrossing with molecular marker selection',
            $5,
            $6
        )
        "#,
    )
    .bind(org_id)
    .bind(&secondary_breeding_method_db_id)
    .bind(&secondary_breeding_method_name)
    .bind(&secondary_breeding_method_abbreviation)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_breeding_method_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO lists (
            created_at,
            updated_at,
            organization_id,
            list_db_id,
            list_name,
            list_description,
            list_type,
            list_size,
            list_source,
            list_owner_name,
            list_owner_person_db_id,
            date_created,
            date_modified,
            data,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Reference list generated by the live BrAPI integration test',
            $4,
            2,
            $5,
            $6,
            $7,
            '2026-06-17T00:00:00Z',
            '2026-06-18T00:00:00Z',
            $8,
            $9,
            $10
        )
        "#,
    )
    .bind(org_id)
    .bind(&list_db_id)
    .bind(&list_name)
    .bind(&list_type)
    .bind(&list_source)
    .bind(format!("{} {}", person_first_name, person_last_name))
    .bind(&person_db_id)
    .bind(Json(json!([&germplasm_db_id, &secondary_germplasm_db_id])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": list_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO lists (
            created_at,
            updated_at,
            organization_id,
            list_db_id,
            list_name,
            list_description,
            list_type,
            list_size,
            list_source,
            list_owner_name,
            list_owner_person_db_id,
            date_created,
            date_modified,
            data,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Secondary reference list generated by the live BrAPI integration test',
            $4,
            1,
            $5,
            $6,
            $7,
            '2026-06-19T00:00:00Z',
            '2026-06-20T00:00:00Z',
            $8,
            $9,
            $10
        )
        "#,
    )
    .bind(org_id)
    .bind(&secondary_list_db_id)
    .bind(&secondary_list_name)
    .bind(&secondary_list_type)
    .bind(&secondary_list_source)
    .bind(format!(
        "{} {}",
        secondary_person_first_name, secondary_person_last_name
    ))
    .bind(&secondary_person_db_id)
    .bind(Json(json!([&program_db_id])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_list_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO ontologies (
            created_at,
            updated_at,
            organization_id,
            ontology_db_id,
            ontology_name,
            description,
            authors,
            version,
            copyright,
            licence,
            documentation_url,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Ontology generated by the live BrAPI integration test',
            'Bijmantra Live Test',
            '1.0',
            'Copyright 2026 Bijmantra',
            'CC-BY-4.0',
            'https://example.test/ontology-primary',
            $4,
            $5
        )
        "#,
    )
    .bind(org_id)
    .bind(&ontology_db_id)
    .bind(&ontology_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": ontology_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO ontologies (
            created_at,
            updated_at,
            organization_id,
            ontology_db_id,
            ontology_name,
            description,
            authors,
            version,
            copyright,
            licence,
            documentation_url,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Secondary ontology generated by the live BrAPI integration test',
            'Bijmantra Live Test',
            '2.0',
            'Copyright 2026 Bijmantra',
            'CC-BY-4.0',
            'https://example.test/ontology-secondary',
            $4,
            $5
        )
        "#,
    )
    .bind(org_id)
    .bind(&secondary_ontology_db_id)
    .bind(&secondary_ontology_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_ontology_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO methods (
            created_at,
            updated_at,
            organization_id,
            method_db_id,
            method_name,
            method_pui,
            method_class,
            description,
            formula,
            reference,
            bibliographical_reference,
            ontology_db_id,
            ontology_name,
            ontology_version,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            'Measure plant height in centimeters',
            NULL,
            'Live field SOP',
            'Bijmantra live method reference',
            $6,
            $7,
            '1.0',
            $8,
            $9
        )
        "#,
    )
    .bind(org_id)
    .bind(&method_db_id)
    .bind(&method_name)
    .bind(format!("https://example.test/{method_db_id}"))
    .bind(&method_class)
    .bind(&ontology_db_id)
    .bind(&ontology_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary-method"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": method_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO methods (
            created_at,
            updated_at,
            organization_id,
            method_db_id,
            method_name,
            method_pui,
            method_class,
            description,
            formula,
            reference,
            bibliographical_reference,
            ontology_db_id,
            ontology_name,
            ontology_version,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            NULL,
            $4,
            'Estimate quality by panel assessment',
            'mean(panel_scores)',
            'Live quality SOP',
            'Bijmantra live secondary method reference',
            $5,
            $6,
            '2.0',
            $7,
            $8
        )
        "#,
    )
    .bind(org_id)
    .bind(&secondary_method_db_id)
    .bind(&secondary_method_name)
    .bind(&secondary_method_class)
    .bind(&secondary_ontology_db_id)
    .bind(&secondary_ontology_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary-method"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_method_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO scales (
            created_at,
            updated_at,
            organization_id,
            scale_db_id,
            scale_name,
            scale_pui,
            data_type,
            decimal_places,
            valid_values_min,
            valid_values_max,
            valid_values_categories,
            ontology_db_id,
            ontology_name,
            ontology_version,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            1,
            0,
            250,
            $6,
            $7,
            $8,
            '1.0',
            $9,
            $10
        )
        "#,
    )
    .bind(org_id)
    .bind(&scale_db_id)
    .bind(&scale_name)
    .bind(format!("https://example.test/{scale_db_id}"))
    .bind(&scale_data_type)
    .bind(Json(json!([
        {"label": "short", "value": "short"},
        {"label": "tall", "value": "tall"}
    ])))
    .bind(&ontology_db_id)
    .bind(&ontology_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary-scale"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": scale_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO scales (
            created_at,
            updated_at,
            organization_id,
            scale_db_id,
            scale_name,
            scale_pui,
            data_type,
            decimal_places,
            valid_values_min,
            valid_values_max,
            valid_values_categories,
            ontology_db_id,
            ontology_name,
            ontology_version,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            NULL,
            $4,
            0,
            1,
            9,
            $5,
            $6,
            $7,
            '2.0',
            $8,
            $9
        )
        "#,
    )
    .bind(org_id)
    .bind(&secondary_scale_db_id)
    .bind(&secondary_scale_name)
    .bind(&secondary_scale_data_type)
    .bind(Json(json!([
        {"label": "poor", "value": "1"},
        {"label": "excellent", "value": "9"}
    ])))
    .bind(&secondary_ontology_db_id)
    .bind(&secondary_ontology_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary-scale"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_scale_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let observation_variable_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO observation_variables (
            created_at,
            updated_at,
            organization_id,
            observation_variable_db_id,
            observation_variable_name,
            common_crop_name,
            default_value,
            status,
            trait_db_id,
            trait_name,
            trait_description,
            trait_class,
            method_db_id,
            method_name,
            method_description,
            scale_db_id,
            scale_name,
            data_type,
            valid_values,
            ontology_db_id,
            ontology_name,
            ontology_term_id,
            ontology_version,
            ontology_documentation_links,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            '0',
            'active',
            $5,
            'Plant height',
            'Height from soil surface to flag leaf',
            $6,
            $7,
            'Field ruler',
            'Measure plant height in centimeters',
            $8,
            'centimeter',
            'Numerical',
            $9,
            $10,
            $11,
            $12,
            '1.0',
            $13,
            $14,
            $15
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&observation_variable_db_id)
    .bind(&observation_variable_name)
    .bind(&trait_common_crop_name)
    .bind(format!("{observation_variable_db_id}-trait"))
    .bind(&trait_class)
    .bind(format!("{observation_variable_db_id}-method"))
    .bind(format!("{observation_variable_db_id}-scale"))
    .bind(Json(json!({"min": 0.0, "max": 250.0})))
    .bind(&ontology_db_id)
    .bind(&ontology_name)
    .bind(format!("{ontology_db_id}:0001"))
    .bind(Json(json!([
        {"URL": "https://example.test/ontology-primary"}
    ])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary-trait"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": observation_variable_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_observation_variable_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO observation_variables (
            created_at,
            updated_at,
            organization_id,
            observation_variable_db_id,
            observation_variable_name,
            common_crop_name,
            default_value,
            status,
            trait_db_id,
            trait_name,
            trait_description,
            trait_class,
            method_db_id,
            method_name,
            method_description,
            scale_db_id,
            scale_name,
            data_type,
            valid_values,
            ontology_db_id,
            ontology_name,
            ontology_term_id,
            ontology_version,
            ontology_documentation_links,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'medium',
            'active',
            $5,
            'Grain quality',
            'Visual grain quality score',
            $6,
            $7,
            'Panel score',
            'Score grain quality by panel assessment',
            $8,
            'score',
            'Ordinal',
            $9,
            $10,
            $11,
            $12,
            '2.0',
            $13,
            $14,
            $15
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&secondary_observation_variable_db_id)
    .bind(&secondary_observation_variable_name)
    .bind(&secondary_trait_common_crop_name)
    .bind(format!("{secondary_observation_variable_db_id}-trait"))
    .bind(&secondary_trait_class)
    .bind(format!("{secondary_observation_variable_db_id}-method"))
    .bind(format!("{secondary_observation_variable_db_id}-scale"))
    .bind(Json(json!({"min": 1.0, "max": 9.0})))
    .bind(&secondary_ontology_db_id)
    .bind(&secondary_ontology_name)
    .bind(format!("{secondary_ontology_db_id}:0002"))
    .bind(Json(json!([
        {"URL": "https://example.test/ontology-secondary"}
    ])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary-trait"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_observation_variable_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let program_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO programs (
            created_at,
            updated_at,
            organization_id,
            program_db_id,
            program_name,
            abbreviation,
            objective,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'Primary program generated by the live BrAPI integration test',
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&program_db_id)
    .bind(&program_name)
    .bind(&program_abbreviation)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "role": "primary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": program_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_program_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO programs (
            created_at,
            updated_at,
            organization_id,
            program_db_id,
            program_name,
            abbreviation,
            objective,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'Secondary program generated by the live BrAPI integration test',
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&secondary_program_db_id)
    .bind(&secondary_program_name)
    .bind(&secondary_program_abbreviation)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "role": "secondary"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_program_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO seasons (
            created_at,
            updated_at,
            organization_id,
            season_db_id,
            season_name,
            year,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            'Kharif',
            $3,
            $4,
            $5
        )
        "#,
    )
    .bind(org_id)
    .bind(&season_db_id)
    .bind(season_year)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "year": season_year}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": season_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO seasons (
            created_at,
            updated_at,
            organization_id,
            season_db_id,
            season_name,
            year,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            'Rabi',
            $3,
            $4,
            $5
        )
        "#,
    )
    .bind(org_id)
    .bind(&previous_season_db_id)
    .bind(previous_season_year)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "year": previous_season_year}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": previous_season_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let location_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO locations (
            created_at,
            updated_at,
            organization_id,
            location_db_id,
            location_name,
            location_type,
            abbreviation,
            country_name,
            country_code,
            institute_name,
            institute_address,
            coordinates,
            coordinate_uncertainty,
            coordinate_description,
            altitude,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            'India',
            'IND',
            'Live BrAPI Test Institute',
            'Integration test address',
            ST_SetSRID(ST_MakePoint($6, $7), 4326),
            '5 m',
            'Live test plot center',
            '12.5 m',
            $8,
            $9
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&location_db_id)
    .bind(format!("Live Field Location {label}"))
    .bind(&location_type)
    .bind(format!("LF-{label}"))
    .bind(72.8311_f64)
    .bind(21.1702_f64)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "coordinates": "present"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": location_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let null_coordinate_location_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO locations (
            created_at,
            updated_at,
            organization_id,
            location_db_id,
            location_name,
            location_type,
            abbreviation,
            country_name,
            country_code,
            institute_name,
            institute_address,
            coordinates,
            coordinate_uncertainty,
            coordinate_description,
            altitude,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'GREENHOUSE',
            $4,
            'India',
            'IND',
            'Live BrAPI Test Institute',
            'Integration test address',
            NULL,
            NULL,
            NULL,
            NULL,
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&null_coordinate_location_db_id)
    .bind(format!("Live Greenhouse Location {label}"))
    .bind(format!("LG-{label}"))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "coordinates": "null"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": null_coordinate_location_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let trial_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO trials (
            created_at,
            updated_at,
            organization_id,
            program_id,
            location_id,
            trial_db_id,
            trial_name,
            trial_description,
            trial_type,
            start_date,
            end_date,
            active,
            common_crop_name,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            'Active trial generated by the live BrAPI integration test',
            'yield',
            $6,
            $7,
            TRUE,
            'rice',
            $8,
            $9
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(program_id)
    .bind(location_id)
    .bind(&trial_db_id)
    .bind(format!("Live Active Trial {label}"))
    .bind(&trial_start_date)
    .bind(&trial_end_date)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "active": true}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": trial_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let inactive_trial_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO trials (
            created_at,
            updated_at,
            organization_id,
            program_id,
            location_id,
            trial_db_id,
            trial_name,
            trial_description,
            trial_type,
            start_date,
            end_date,
            active,
            common_crop_name,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            'Inactive trial generated by the live BrAPI integration test',
            'yield',
            '2025-06-01',
            '2025-10-31',
            FALSE,
            'rice',
            $6,
            $7
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(program_id)
    .bind(location_id)
    .bind(&inactive_trial_db_id)
    .bind(format!("Live Inactive Trial {label}"))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "active": false}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": inactive_trial_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let study_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO studies (
            created_at,
            updated_at,
            organization_id,
            trial_id,
            location_id,
            study_db_id,
            study_name,
            study_description,
            study_type,
            study_code,
            start_date,
            end_date,
            active,
            common_crop_name,
            cultural_practices,
            observation_levels,
            observation_units_description,
            license,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            'Active study generated by the live BrAPI integration test',
            'nursery',
            $6,
            $7,
            $8,
            TRUE,
            'rice',
            'standard agronomic practices',
            $9,
            'Single plot observations',
            'CC-BY-4.0',
            $10,
            $11
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(trial_id)
    .bind(location_id)
    .bind(&study_db_id)
    .bind(format!("Live Active Study {label}"))
    .bind(format!("LS-{label}"))
    .bind(&study_start_date)
    .bind(&study_end_date)
    .bind(Json(json!([
        {"levelName": "plot", "levelOrder": "1"},
        {"levelName": "plant", "levelOrder": "2"}
    ])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "active": true}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": study_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO studies (
            created_at,
            updated_at,
            organization_id,
            trial_id,
            location_id,
            study_db_id,
            study_name,
            study_description,
            study_type,
            study_code,
            start_date,
            end_date,
            active,
            common_crop_name,
            cultural_practices,
            observation_levels,
            observation_units_description,
            license,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            'Inactive study generated by the live BrAPI integration test',
            'nursery',
            $6,
            '2025-06-15',
            '2025-09-30',
            FALSE,
            'rice',
            'archived agronomic practices',
            $7,
            'Archived plot observations',
            'CC-BY-4.0',
            $8,
            $9
        )
        "#,
    )
    .bind(org_id)
    .bind(inactive_trial_id)
    .bind(location_id)
    .bind(&inactive_study_db_id)
    .bind(format!("Live Inactive Study {label}"))
    .bind(format!("LIS-{label}"))
    .bind(Json(json!([])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "active": false, "observationLevels": "empty"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": inactive_study_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO studies (
            created_at,
            updated_at,
            organization_id,
            trial_id,
            location_id,
            study_db_id,
            study_name,
            study_description,
            study_type,
            study_code,
            start_date,
            end_date,
            active,
            common_crop_name,
            cultural_practices,
            observation_levels,
            observation_units_description,
            license,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            'Null observation-level study generated by the live BrAPI integration test',
            'nursery',
            $6,
            '2026-07-01',
            '2026-08-31',
            TRUE,
            'rice',
            'minimal agronomic practices',
            NULL,
            NULL,
            'CC-BY-4.0',
            $7,
            $8
        )
        "#,
    )
    .bind(org_id)
    .bind(trial_id)
    .bind(location_id)
    .bind(&null_observation_levels_study_db_id)
    .bind(format!("Live Null Levels Study {label}"))
    .bind(format!("LNS-{label}"))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "observationLevels": "null"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": null_observation_levels_study_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let germplasm_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO germplasm (
            created_at,
            updated_at,
            organization_id,
            germplasm_db_id,
            germplasm_name,
            default_display_name,
            common_crop_name,
            genus,
            species,
            synonyms,
            donors,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            $9,
            $10
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&germplasm_db_id)
    .bind(&germplasm_name)
    .bind(&germplasm_common_crop_name)
    .bind(&germplasm_genus)
    .bind(&germplasm_species)
    .bind(Json(json!([format!("live-synonym-{label}")])))
    .bind(Json(json!([
        {
            "donorAccessionNumber": format!("donor-accession-{label}"),
            "donorInstitute": "Bijmantra Live Donor Bank"
        }
    ])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": germplasm_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_germplasm_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO germplasm (
            created_at,
            updated_at,
            organization_id,
            germplasm_db_id,
            germplasm_name,
            default_display_name,
            common_crop_name,
            genus,
            species,
            synonyms,
            donors,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            $9,
            $10
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&secondary_germplasm_db_id)
    .bind(&secondary_germplasm_name)
    .bind(&secondary_germplasm_common_crop_name)
    .bind(&secondary_germplasm_genus)
    .bind(&secondary_germplasm_species)
    .bind(Json(json!([format!("live-secondary-synonym-{label}")])))
    .bind(Json(json!([])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "secondary": true}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_germplasm_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let attribute_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO germplasm_attribute_definitions (
            created_at,
            updated_at,
            organization_id,
            attribute_db_id,
            attribute_name,
            attribute_pui,
            attribute_description,
            attribute_category,
            common_crop_name,
            context_of_use,
            default_value,
            documentation_url,
            growth_stage,
            institution,
            language,
            scientist,
            status,
            submission_timestamp,
            synonyms,
            trait_db_id,
            trait_name,
            trait_description,
            trait_class,
            method_db_id,
            method_name,
            method_description,
            method_class,
            scale_db_id,
            scale_name,
            data_type,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'Grain color scored at harvest',
            $5,
            $6,
            $7,
            'white',
            'https://example.test/attribute-primary',
            'maturity',
            'Bijmantra Live Lab',
            'en',
            'Anika Rao',
            'active',
            '2026-06-19T00:00:00Z',
            $8,
            $9,
            'Grain color',
            'Visual grain color',
            'quality',
            $10,
            $11,
            'Visual panel assessment',
            $12,
            $13,
            $14,
            'Categorical',
            $15,
            $16
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&attribute_db_id)
    .bind(&attribute_name)
    .bind(format!("https://example.test/{attribute_db_id}"))
    .bind(&attribute_category)
    .bind(&germplasm_common_crop_name)
    .bind(Json(json!(["field", "harvest"])))
    .bind(Json(json!(["kernel color", "grain shade"])))
    .bind(format!("{attribute_db_id}-trait"))
    .bind(&method_db_id)
    .bind(&method_name)
    .bind(&method_class)
    .bind(&scale_db_id)
    .bind(&scale_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary-attribute"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": attribute_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_attribute_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO germplasm_attribute_definitions (
            created_at,
            updated_at,
            organization_id,
            attribute_db_id,
            attribute_name,
            attribute_pui,
            attribute_description,
            attribute_category,
            common_crop_name,
            context_of_use,
            default_value,
            documentation_url,
            growth_stage,
            institution,
            language,
            scientist,
            status,
            submission_timestamp,
            synonyms,
            trait_db_id,
            trait_name,
            trait_description,
            trait_class,
            method_db_id,
            method_name,
            method_description,
            method_class,
            scale_db_id,
            scale_name,
            data_type,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            NULL,
            'Drought stress score under managed stress',
            $4,
            $5,
            $6,
            '5',
            'https://example.test/attribute-secondary',
            'flowering',
            'Bijmantra Live Lab',
            'en',
            'Bhavin Patel',
            'active',
            '2026-06-20T00:00:00Z',
            $7,
            $8,
            'Drought score',
            'Visual drought stress score',
            'stress',
            $9,
            $10,
            'Panel stress assessment',
            $11,
            $12,
            $13,
            'Ordinal',
            $14,
            $15
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&secondary_attribute_db_id)
    .bind(&secondary_attribute_name)
    .bind(&secondary_attribute_category)
    .bind(&secondary_germplasm_common_crop_name)
    .bind(Json(json!(["screenhouse"])))
    .bind(Json(json!(["stress score"])))
    .bind(format!("{secondary_attribute_db_id}-trait"))
    .bind(&secondary_method_db_id)
    .bind(&secondary_method_name)
    .bind(&secondary_method_class)
    .bind(&secondary_scale_db_id)
    .bind(&secondary_scale_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary-attribute"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_attribute_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO germplasm_attribute_values (
            created_at,
            updated_at,
            organization_id,
            germplasm_id,
            attribute_definition_id,
            attribute_value_db_id,
            attribute_db_id,
            attribute_name,
            germplasm_db_id,
            germplasm_name,
            value,
            determined_date,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            'white',
            '2026-07-01',
            $9,
            $10
        )
        "#,
    )
    .bind(org_id)
    .bind(germplasm_id)
    .bind(attribute_id)
    .bind(&attribute_value_db_id)
    .bind(&attribute_db_id)
    .bind(&attribute_name)
    .bind(&germplasm_db_id)
    .bind(&germplasm_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "primary-attribute-value"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": attribute_value_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO germplasm_attribute_values (
            created_at,
            updated_at,
            organization_id,
            germplasm_id,
            attribute_definition_id,
            attribute_value_db_id,
            attribute_db_id,
            attribute_name,
            germplasm_db_id,
            germplasm_name,
            value,
            determined_date,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            '7',
            '2026-07-02',
            $9,
            $10
        )
        "#,
    )
    .bind(org_id)
    .bind(secondary_germplasm_id)
    .bind(secondary_attribute_id)
    .bind(&secondary_attribute_value_db_id)
    .bind(&secondary_attribute_db_id)
    .bind(&secondary_attribute_name)
    .bind(&secondary_germplasm_db_id)
    .bind(&secondary_germplasm_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "kind": "secondary-attribute-value"}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_attribute_value_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let observation_unit_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO observation_units (
            created_at,
            updated_at,
            organization_id,
            study_id,
            germplasm_id,
            observation_unit_db_id,
            observation_unit_name,
            observation_unit_pui,
            observation_level,
            observation_level_code,
            observation_level_order,
            position_coordinate_x,
            position_coordinate_x_type,
            position_coordinate_y,
            position_coordinate_y_type,
            entry_type,
            geo_coordinates,
            treatments,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            'plot',
            'PLOT',
            1,
            '101',
            'GRID_COL',
            '202',
            'GRID_ROW',
            'CHECK',
            $7,
            $8,
            $9,
            $10
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(study_id)
    .bind(germplasm_id)
    .bind(&observation_unit_db_id)
    .bind(format!("Live Observation Unit {label}"))
    .bind(format!("https://example.test/{observation_unit_db_id}"))
    .bind(Json(
        json!({"type": "Point", "coordinates": [72.8311, 21.1702]}),
    ))
    .bind(Json(json!([
        {"factor": "water", "modality": "irrigated"}
    ])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": observation_unit_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_observation_unit_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO observation_units (
            created_at,
            updated_at,
            organization_id,
            study_id,
            germplasm_id,
            observation_unit_db_id,
            observation_unit_name,
            observation_unit_pui,
            observation_level,
            observation_level_code,
            observation_level_order,
            position_coordinate_x,
            position_coordinate_x_type,
            position_coordinate_y,
            position_coordinate_y_type,
            entry_type,
            geo_coordinates,
            treatments,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            'plot',
            'PLOT',
            2,
            '102',
            'GRID_COL',
            '203',
            'GRID_ROW',
            'TEST',
            $7,
            $8,
            $9,
            $10
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(study_id)
    .bind(secondary_germplasm_id)
    .bind(&secondary_observation_unit_db_id)
    .bind(format!("Live Secondary Observation Unit {label}"))
    .bind(format!(
        "https://example.test/{secondary_observation_unit_db_id}"
    ))
    .bind(Json(
        json!({"type": "Point", "coordinates": [72.8320, 21.1710]}),
    ))
    .bind(Json(json!([
        {"factor": "water", "modality": "rainfed"}
    ])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "secondary": true}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_observation_unit_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO observations (
            created_at,
            updated_at,
            organization_id,
            observation_unit_id,
            observation_variable_id,
            study_id,
            germplasm_id,
            observation_db_id,
            collector,
            observation_time_stamp,
            season_db_id,
            upload_timestamp,
            value,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            'Anika Rao',
            '2026-07-01T08:00:00Z',
            $7,
            '2026-07-01T09:00:00Z',
            '123.4',
            $8,
            $9
        )
        "#,
    )
    .bind(org_id)
    .bind(observation_unit_id)
    .bind(observation_variable_id)
    .bind(study_id)
    .bind(germplasm_id)
    .bind(&observation_db_id)
    .bind(&season_db_id)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": observation_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO observations (
            created_at,
            updated_at,
            organization_id,
            observation_unit_id,
            observation_variable_id,
            study_id,
            germplasm_id,
            observation_db_id,
            collector,
            observation_time_stamp,
            season_db_id,
            upload_timestamp,
            value,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            'Bhavin Patel',
            '2026-07-02T08:00:00Z',
            $7,
            '2026-07-02T09:00:00Z',
            'excellent',
            $8,
            $9
        )
        "#,
    )
    .bind(org_id)
    .bind(secondary_observation_unit_id)
    .bind(secondary_observation_variable_id)
    .bind(study_id)
    .bind(secondary_germplasm_id)
    .bind(&secondary_observation_db_id)
    .bind(&previous_season_db_id)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "secondary": true}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_observation_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let crossing_project_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO crossing_projects (
            created_at,
            updated_at,
            organization_id,
            program_id,
            crossing_project_db_id,
            crossing_project_name,
            crossing_project_description,
            common_crop_name,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'Crossing project generated by the live BrAPI integration test',
            'rice',
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(program_id)
    .bind(&crossing_project_db_id)
    .bind(format!("Live Crossing Project {label}"))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": crossing_project_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO crosses (
            created_at,
            updated_at,
            organization_id,
            crossing_project_id,
            cross_db_id,
            cross_name,
            cross_type,
            parent1_db_id,
            parent1_type,
            parent2_db_id,
            parent2_type,
            crossing_year,
            pollination_time_stamp,
            cross_status,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'BIPARENTAL',
            $5,
            'FEMALE',
            $5,
            'MALE',
            2026,
            '2026-06-17T00:00:00Z',
            'COMPLETED',
            $6,
            $7
        )
        "#,
    )
    .bind(org_id)
    .bind(crossing_project_id)
    .bind(&cross_db_id)
    .bind(format!("Live Cross {label}"))
    .bind(germplasm_id)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": cross_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO planned_crosses (
            created_at,
            updated_at,
            organization_id,
            crossing_project_id,
            planned_cross_db_id,
            planned_cross_name,
            cross_type,
            parent1_db_id,
            parent1_type,
            parent2_db_id,
            parent2_type,
            number_of_progeny,
            status,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'BIPARENTAL',
            $5,
            'FEMALE',
            $5,
            'MALE',
            24,
            'TODO',
            $6,
            $7
        )
        "#,
    )
    .bind(org_id)
    .bind(crossing_project_id)
    .bind(&planned_cross_db_id)
    .bind(format!("Live Planned Cross {label}"))
    .bind(germplasm_id)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": planned_cross_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let seedlot_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO seedlots (
            created_at,
            updated_at,
            organization_id,
            germplasm_id,
            program_id,
            location_id,
            seedlot_db_id,
            seedlot_name,
            seedlot_description,
            source_collection,
            storage_location,
            count,
            units,
            creation_date,
            last_updated,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            'Seed lot generated by the live BrAPI integration test',
            'integration-test',
            'cold-room-1',
            42,
            'seeds',
            CURRENT_DATE,
            CURRENT_DATE,
            $7,
            $8
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(germplasm_id)
    .bind(program_id)
    .bind(location_id)
    .bind(&seedlot_db_id)
    .bind(&seedlot_name)
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "status": "active",
        "storage_type": "long_term",
        "species": "Oryza sativa",
        "initial_quantity": 42,
        "current_viability": 82.5,
        "last_viability_test": "2024-01-01"
    })))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": seedlot_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_seedlot_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO seedlots (
            created_at,
            updated_at,
            organization_id,
            germplasm_id,
            program_id,
            location_id,
            seedlot_db_id,
            seedlot_name,
            seedlot_description,
            source_collection,
            storage_location,
            count,
            units,
            creation_date,
            last_updated,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            'Secondary seed lot generated by the live BrAPI integration test',
            'integration-test-secondary',
            'cold-room-2',
            13,
            'seeds',
            CURRENT_DATE,
            CURRENT_DATE,
            $7,
            $8
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(secondary_germplasm_id)
    .bind(secondary_program_id)
    .bind(null_coordinate_location_id)
    .bind(&secondary_seedlot_db_id)
    .bind(&secondary_seedlot_name)
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "secondary": true,
        "status": "low_stock",
        "storage_type": "short_term",
        "species": "Oryza glaberrima",
        "initial_quantity": 13,
        "current_viability": 91.0
    })))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_seedlot_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO seedlot_transactions (
            created_at,
            updated_at,
            organization_id,
            seedlot_id,
            transaction_db_id,
            transaction_description,
            transaction_timestamp,
            amount,
            units,
            from_seedlot_db_id,
            to_seedlot_db_id,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Live test transaction',
            '2026-06-17T00:00:00Z',
            7.0,
            'seeds',
            NULL,
            $4,
            $5,
            $6
        )
        "#,
    )
    .bind(org_id)
    .bind(seedlot_id)
    .bind(&transaction_db_id)
    .bind(&seedlot_db_id)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": transaction_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO seedlot_transactions (
            created_at,
            updated_at,
            organization_id,
            seedlot_id,
            transaction_db_id,
            transaction_description,
            transaction_timestamp,
            amount,
            units,
            from_seedlot_db_id,
            to_seedlot_db_id,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Live secondary test transaction',
            '2026-06-18T00:00:00Z',
            3.0,
            'seeds',
            $4,
            $5,
            $6,
            $7
        )
        "#,
    )
    .bind(org_id)
    .bind(secondary_seedlot_id)
    .bind(&secondary_transaction_db_id)
    .bind(&seedlot_db_id)
    .bind(&secondary_seedlot_db_id)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label, "secondary": true}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_transaction_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let map_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO genome_maps (
            created_at,
            updated_at,
            organization_id,
            map_db_id,
            map_name,
            map_pui,
            common_crop_name,
            type,
            unit,
            scientific_name,
            published_date,
            comments,
            documentation_url,
            linkage_group_count,
            marker_count,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'rice',
            'Genetic',
            'cM',
            'Oryza sativa',
            '2026-06-19',
            'Live map generated by the Rust integration fixture',
            'https://example.test/map-primary',
            1,
            42,
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&map_db_id)
    .bind(&map_name)
    .bind(format!("doi:10.1/{map_db_id}"))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": map_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_map_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO genome_maps (
            created_at,
            updated_at,
            organization_id,
            map_db_id,
            map_name,
            map_pui,
            common_crop_name,
            type,
            unit,
            scientific_name,
            published_date,
            comments,
            documentation_url,
            linkage_group_count,
            marker_count,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            'chickpea',
            'Physical',
            'bp',
            'Cicer arietinum',
            '2026-06-20',
            'Secondary live map generated by the Rust integration fixture',
            'https://example.test/map-secondary',
            1,
            13,
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&secondary_map_db_id)
    .bind(&secondary_map_name)
    .bind(format!("doi:10.1/{secondary_map_db_id}"))
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "secondary": true
    })))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_map_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO linkage_groups (
            created_at,
            updated_at,
            organization_id,
            map_id,
            linkage_group_name,
            max_position,
            marker_count,
            additional_info
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            123.4,
            42,
            $4
        ),
        (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $5,
            $6,
            987.6,
            13,
            $7
        )
        "#,
    )
    .bind(org_id)
    .bind(map_id)
    .bind(&linkage_group_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(secondary_map_id)
    .bind(&secondary_linkage_group_name)
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "secondary": true
    })))
    .execute(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO marker_positions (
            created_at,
            updated_at,
            organization_id,
            map_id,
            marker_position_db_id,
            variant_db_id,
            variant_name,
            linkage_group_name,
            position,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            12.5,
            $7,
            $8
        ),
        (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $9,
            $10,
            $11,
            $12,
            $13,
            87.25,
            $14,
            $15
        )
        "#,
    )
    .bind(org_id)
    .bind(map_id)
    .bind(&marker_position_db_id)
    .bind(&marker_variant_db_id)
    .bind(&marker_variant_name)
    .bind(&linkage_group_name)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": marker_position_db_id}
    ])))
    .bind(secondary_map_id)
    .bind(&secondary_marker_position_db_id)
    .bind(&secondary_marker_variant_db_id)
    .bind(&secondary_marker_variant_name)
    .bind(&secondary_linkage_group_name)
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "secondary": true
    })))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_marker_position_db_id}
    ])))
    .execute(&mut **tx)
    .await?;

    let reference_set_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO reference_sets (
            created_at,
            updated_at,
            organization_id,
            reference_set_db_id,
            reference_set_name,
            description,
            assembly_pui,
            source_uri,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Primary reference set generated by the Rust integration fixture',
            'doi:10.1/reference-primary',
            'https://example.test/reference-primary.fa',
            $4,
            $5
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&reference_set_db_id)
    .bind(format!("{prefix}-reference-set-name-{label}"))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": reference_set_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_reference_set_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO reference_sets (
            created_at,
            updated_at,
            organization_id,
            reference_set_db_id,
            reference_set_name,
            description,
            assembly_pui,
            source_uri,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            'Secondary reference set generated by the Rust integration fixture',
            'doi:10.1/reference-secondary',
            'https://example.test/reference-secondary.fa',
            $4,
            $5
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&secondary_reference_set_db_id)
    .bind(format!("{prefix}-reference-set-name-{label}-secondary"))
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "secondary": true
    })))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_reference_set_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let variant_set_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO variant_sets (
            created_at,
            updated_at,
            organization_id,
            study_id,
            reference_set_id,
            variant_set_db_id,
            variant_set_name,
            analysis,
            available_formats,
            call_set_count,
            variant_count,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            1,
            0,
            $8,
            $9
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(study_id)
    .bind(reference_set_id)
    .bind(&variant_set_db_id)
    .bind(&variant_set_name)
    .bind(Json(json!([{"analysisName": "Live genotyping fixture"}])))
    .bind(Json(json!([{"dataFormat": "VCF"}])))
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": variant_set_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_variant_set_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO variant_sets (
            created_at,
            updated_at,
            organization_id,
            study_id,
            reference_set_id,
            variant_set_db_id,
            variant_set_name,
            analysis,
            available_formats,
            call_set_count,
            variant_count,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            1,
            0,
            $8,
            $9
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(study_id)
    .bind(secondary_reference_set_id)
    .bind(&secondary_variant_set_db_id)
    .bind(&secondary_variant_set_name)
    .bind(Json(
        json!([{"analysisName": "Live secondary genotyping fixture"}]),
    ))
    .bind(Json(json!([{"dataFormat": "VCF"}])))
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "secondary": true
    })))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_variant_set_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let call_set_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO call_sets (
            created_at,
            updated_at,
            organization_id,
            call_set_db_id,
            call_set_name,
            sample_db_id,
            created,
            updated,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            '2026-06-19T00:00:00Z',
            '2026-06-20T00:00:00Z',
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&call_set_db_id)
    .bind(&call_set_name)
    .bind(&sample_db_id)
    .bind(Json(
        json!({"fixture": "live-postgres-brapi", "tenant": label}),
    ))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": call_set_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    let secondary_call_set_id = sqlx::query_scalar::<_, i64>(
        r#"
        INSERT INTO call_sets (
            created_at,
            updated_at,
            organization_id,
            call_set_db_id,
            call_set_name,
            sample_db_id,
            created,
            updated,
            additional_info,
            external_references
        )
        VALUES (
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            $1,
            $2,
            $3,
            $4,
            '2026-06-21T00:00:00Z',
            '2026-06-22T00:00:00Z',
            $5,
            $6
        )
        RETURNING id
        "#,
    )
    .bind(org_id)
    .bind(&secondary_call_set_db_id)
    .bind(&secondary_call_set_name)
    .bind(&secondary_sample_db_id)
    .bind(Json(json!({
        "fixture": "live-postgres-brapi",
        "tenant": label,
        "secondary": true
    })))
    .bind(Json(json!([
        {"referenceSource": "live-test", "referenceId": secondary_call_set_db_id}
    ])))
    .fetch_one(&mut **tx)
    .await?;

    sqlx::query(
        r#"
        INSERT INTO variant_set_call_sets (variant_set_id, call_set_id)
        VALUES ($1, $2), ($3, $4)
        "#,
    )
    .bind(variant_set_id)
    .bind(call_set_id)
    .bind(secondary_variant_set_id)
    .bind(secondary_call_set_id)
    .execute(&mut **tx)
    .await?;

    Ok(SeededTenant {
        org_id,
        user_id,
        inactive_user_id,
        program_db_id,
        secondary_program_db_id,
        program_name,
        program_abbreviation,
        location_db_id,
        null_coordinate_location_db_id,
        location_type,
        trial_db_id,
        inactive_trial_db_id,
        trial_start_date,
        trial_end_date,
        study_db_id,
        inactive_study_db_id,
        null_observation_levels_study_db_id,
        study_start_date,
        study_end_date,
        season_db_id,
        previous_season_db_id,
        season_year,
        previous_season_year,
        person_db_id,
        secondary_person_db_id,
        person_first_name,
        person_last_name,
        secondary_person_first_name,
        secondary_person_last_name,
        list_db_id,
        secondary_list_db_id,
        list_name,
        secondary_list_name,
        list_type,
        secondary_list_type,
        list_source,
        secondary_list_source,
        ontology_db_id,
        secondary_ontology_db_id,
        ontology_name,
        secondary_ontology_name,
        germplasm_db_id,
        secondary_germplasm_db_id,
        germplasm_name,
        secondary_germplasm_name,
        germplasm_common_crop_name,
        secondary_germplasm_common_crop_name,
        germplasm_genus,
        secondary_germplasm_genus,
        germplasm_species,
        secondary_germplasm_species,
        attribute_db_id,
        secondary_attribute_db_id,
        attribute_name,
        secondary_attribute_name,
        attribute_category,
        secondary_attribute_category,
        attribute_value_db_id,
        secondary_attribute_value_db_id,
        breeding_method_db_id,
        secondary_breeding_method_db_id,
        breeding_method_name,
        secondary_breeding_method_name,
        breeding_method_abbreviation,
        secondary_breeding_method_abbreviation,
        observation_variable_db_id,
        secondary_observation_variable_db_id,
        observation_variable_name,
        observation_unit_db_id,
        secondary_observation_unit_db_id,
        observation_db_id,
        secondary_observation_db_id,
        study_id,
        germplasm_id,
        secondary_germplasm_id,
        trait_class,
        secondary_trait_class,
        trait_common_crop_name,
        secondary_trait_common_crop_name,
        method_db_id,
        secondary_method_db_id,
        method_name,
        method_class,
        secondary_method_class,
        scale_db_id,
        secondary_scale_db_id,
        scale_name,
        scale_data_type,
        secondary_scale_data_type,
        crossing_project_db_id,
        cross_db_id,
        planned_cross_db_id,
        seedlot_db_id,
        secondary_seedlot_db_id,
        seedlot_name,
        secondary_seedlot_name,
        transaction_db_id,
        secondary_transaction_db_id,
        reference_set_db_id,
        secondary_reference_set_db_id,
        variant_set_db_id,
        secondary_variant_set_db_id,
        variant_set_name,
        secondary_variant_set_name,
        call_set_db_id,
        secondary_call_set_db_id,
        call_set_name,
        secondary_call_set_name,
        sample_db_id,
        secondary_sample_db_id,
        map_db_id,
        secondary_map_db_id,
        map_name,
        secondary_map_name,
        linkage_group_name,
        secondary_linkage_group_name,
        marker_position_db_id,
        secondary_marker_position_db_id,
        marker_variant_db_id,
        secondary_marker_variant_db_id,
        marker_variant_name,
        secondary_marker_variant_name,
    })
}

async fn cleanup_seed_data(pool: &PgPool, prefix: &str) -> TestResult {
    let mut tx = pool.begin().await?;
    set_admin_context(&mut tx).await?;
    let pattern = format!("{prefix}%");

    sqlx::query(
        r#"
        DELETE FROM germplasm_attribute_values
        WHERE attribute_value_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM observations
        WHERE observation_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM variant_set_call_sets
        WHERE call_set_id IN (
            SELECT id FROM call_sets WHERE call_set_db_id LIKE $1
        )
           OR variant_set_id IN (
            SELECT id FROM variant_sets WHERE variant_set_db_id LIKE $1
        )
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM call_sets
        WHERE call_set_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM variant_sets
        WHERE variant_set_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM reference_sets
        WHERE reference_set_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM marker_positions
        WHERE map_id IN (
            SELECT id FROM genome_maps WHERE map_db_id LIKE $1
        )
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM linkage_groups
        WHERE map_id IN (
            SELECT id FROM genome_maps WHERE map_db_id LIKE $1
        )
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM genome_maps
        WHERE map_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM seedlot_transactions
        WHERE transaction_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM seedlot_inventory_adjustments
        WHERE seedlot_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM seedlots
        WHERE seedlot_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM crosses
        WHERE cross_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM planned_crosses
        WHERE planned_cross_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM observation_units
        WHERE observation_unit_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM observation_variables
        WHERE observation_variable_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM scales
        WHERE scale_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM methods
        WHERE method_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM crossing_projects
        WHERE crossing_project_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM studies
        WHERE study_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM trials
        WHERE trial_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM seasons
        WHERE season_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM locations
        WHERE location_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM germplasm_attribute_definitions
        WHERE attribute_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM breeding_methods
        WHERE breeding_method_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM germplasm
        WHERE germplasm_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM lists
        WHERE list_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM ontologies
        WHERE ontology_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM programs
        WHERE program_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM people
        WHERE person_db_id LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM audit_logs
        WHERE target_type = 'seedlot_inventory_adjustment'
          AND changes->>'seedLotDbId' LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM users
        WHERE email LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    sqlx::query(
        r#"
        DELETE FROM organizations
        WHERE name LIKE $1
        "#,
    )
    .bind(&pattern)
    .execute(&mut *tx)
    .await?;

    tx.commit().await?;
    Ok(())
}

async fn assert_no_seed_residue(pool: &PgPool, prefix: &str) -> TestResult {
    let pattern = format!("{prefix}%");
    let rows = sqlx::query(
        r#"
        SELECT table_name, residue_count
        FROM (
            SELECT 'organizations' AS table_name, COUNT(*)::bigint AS residue_count FROM organizations WHERE name LIKE $1
            UNION ALL SELECT 'users', COUNT(*)::bigint FROM users WHERE email LIKE $1
            UNION ALL SELECT 'auth_identities', COUNT(*)::bigint FROM auth_identities WHERE email_at_login LIKE $1
            UNION ALL SELECT 'people', COUNT(*)::bigint FROM people WHERE person_db_id LIKE $1
            UNION ALL SELECT 'programs', COUNT(*)::bigint FROM programs WHERE program_db_id LIKE $1
            UNION ALL SELECT 'locations', COUNT(*)::bigint FROM locations WHERE location_db_id LIKE $1
            UNION ALL SELECT 'trials', COUNT(*)::bigint FROM trials WHERE trial_db_id LIKE $1
            UNION ALL SELECT 'studies', COUNT(*)::bigint FROM studies WHERE study_db_id LIKE $1
            UNION ALL SELECT 'seasons', COUNT(*)::bigint FROM seasons WHERE season_db_id LIKE $1
            UNION ALL SELECT 'lists', COUNT(*)::bigint FROM lists WHERE list_db_id LIKE $1
            UNION ALL SELECT 'ontologies', COUNT(*)::bigint FROM ontologies WHERE ontology_db_id LIKE $1
            UNION ALL SELECT 'germplasm', COUNT(*)::bigint FROM germplasm WHERE germplasm_db_id LIKE $1
            UNION ALL SELECT 'germplasm_attribute_definitions', COUNT(*)::bigint FROM germplasm_attribute_definitions WHERE attribute_db_id LIKE $1
            UNION ALL SELECT 'germplasm_attribute_values', COUNT(*)::bigint FROM germplasm_attribute_values WHERE attribute_value_db_id LIKE $1
            UNION ALL SELECT 'breeding_methods', COUNT(*)::bigint FROM breeding_methods WHERE breeding_method_db_id LIKE $1
            UNION ALL SELECT 'methods', COUNT(*)::bigint FROM methods WHERE method_db_id LIKE $1
            UNION ALL SELECT 'scales', COUNT(*)::bigint FROM scales WHERE scale_db_id LIKE $1
            UNION ALL SELECT 'observation_variables', COUNT(*)::bigint FROM observation_variables WHERE observation_variable_db_id LIKE $1
            UNION ALL SELECT 'observation_units', COUNT(*)::bigint FROM observation_units WHERE observation_unit_db_id LIKE $1
            UNION ALL SELECT 'observations', COUNT(*)::bigint FROM observations WHERE observation_db_id LIKE $1
            UNION ALL SELECT 'crossing_projects', COUNT(*)::bigint FROM crossing_projects WHERE crossing_project_db_id LIKE $1
            UNION ALL SELECT 'crosses', COUNT(*)::bigint FROM crosses WHERE cross_db_id LIKE $1
            UNION ALL SELECT 'planned_crosses', COUNT(*)::bigint FROM planned_crosses WHERE planned_cross_db_id LIKE $1
            UNION ALL SELECT 'seedlots', COUNT(*)::bigint FROM seedlots WHERE seedlot_db_id LIKE $1
            UNION ALL SELECT 'seedlot_transactions', COUNT(*)::bigint FROM seedlot_transactions WHERE transaction_db_id LIKE $1
            UNION ALL SELECT 'seedlot_inventory_adjustments', COUNT(*)::bigint FROM seedlot_inventory_adjustments WHERE seedlot_db_id LIKE $1
            UNION ALL SELECT 'reference_sets', COUNT(*)::bigint FROM reference_sets WHERE reference_set_db_id LIKE $1
            UNION ALL SELECT 'variant_sets', COUNT(*)::bigint FROM variant_sets WHERE variant_set_db_id LIKE $1
            UNION ALL SELECT 'call_sets', COUNT(*)::bigint FROM call_sets WHERE call_set_db_id LIKE $1
            UNION ALL SELECT 'variant_set_call_sets', COUNT(*)::bigint
            FROM variant_set_call_sets vsc
            LEFT JOIN variant_sets vs ON vs.id = vsc.variant_set_id
            LEFT JOIN call_sets cs ON cs.id = vsc.call_set_id
            WHERE vs.variant_set_db_id LIKE $1 OR cs.call_set_db_id LIKE $1
            UNION ALL SELECT 'genome_maps', COUNT(*)::bigint FROM genome_maps WHERE map_db_id LIKE $1
            UNION ALL SELECT 'linkage_groups', COUNT(*)::bigint FROM linkage_groups WHERE linkage_group_name LIKE $1
            UNION ALL SELECT 'marker_positions', COUNT(*)::bigint FROM marker_positions WHERE marker_position_db_id LIKE $1
            UNION ALL SELECT 'audit_logs', COUNT(*)::bigint FROM audit_logs WHERE target_type = 'seedlot_inventory_adjustment' AND changes->>'seedLotDbId' LIKE $1
        ) residue
        WHERE residue_count > 0
        ORDER BY table_name
        "#,
    )
    .bind(&pattern)
    .fetch_all(pool)
    .await?;

    if rows.is_empty() {
        return Ok(());
    }

    let residue = rows
        .iter()
        .map(|row| {
            format!(
                "{}={}",
                row.get::<String, _>("table_name"),
                row.get::<i64, _>("residue_count")
            )
        })
        .collect::<Vec<_>>()
        .join(", ");
    Err(test_error(format!(
        "live BrAPI cleanup left prefixed residue for {prefix}: {residue}"
    )))
}

async fn set_admin_context(tx: &mut sqlx::Transaction<'_, sqlx::Postgres>) -> TestResult {
    sqlx::query("SELECT set_config('app.current_organization_id', '0', true)")
        .execute(&mut **tx)
        .await?;
    Ok(())
}

async fn ensure_migrated_database(pool: &PgPool) -> TestResult {
    let alembic_version_exists = sqlx::query_scalar::<_, Option<String>>(
        "SELECT to_regclass('public.alembic_version')::text",
    )
    .fetch_one(pool)
    .await?
    .is_some();
    if !alembic_version_exists {
        validate_alembic_versions(&[])?;
    } else {
        let versions = sqlx::query_scalar::<_, String>(
            "SELECT version_num FROM alembic_version ORDER BY version_num",
        )
        .fetch_all(pool)
        .await?;
        validate_alembic_versions(&versions)?;
    }

    for table in [
        "public.organizations",
        "public.users",
        "public.audit_logs",
        "public.auth_identities",
        "public.people",
        "public.programs",
        "public.locations",
        "public.trials",
        "public.studies",
        "public.seasons",
        "public.lists",
        "public.ontologies",
        "public.methods",
        "public.scales",
        "public.observation_variables",
        "public.observation_units",
        "public.observations",
        "public.germplasm",
        "public.germplasm_attribute_definitions",
        "public.germplasm_attribute_values",
        "public.breeding_methods",
        "public.crossing_projects",
        "public.crosses",
        "public.planned_crosses",
        "public.seedlots",
        "public.seedlot_transactions",
        "public.seedlot_inventory_adjustments",
        "public.reference_sets",
        "public.variant_sets",
        "public.call_sets",
        "public.variant_set_call_sets",
        "public.genome_maps",
        "public.linkage_groups",
        "public.marker_positions",
    ] {
        let exists = sqlx::query_scalar::<_, Option<String>>("SELECT to_regclass($1)::text")
            .bind(table)
            .fetch_one(pool)
            .await?
            .is_some();
        if !exists {
            return Err(test_error(format!(
                "live database is missing required table {table}"
            )));
        }
    }

    ensure_required_indexes(pool).await?;

    Ok(())
}

fn validate_alembic_versions(versions: &[String]) -> TestResult {
    if versions.is_empty() {
        return Err(test_error(
            "live database is missing alembic_version; run Alembic first",
        ));
    }

    let trimmed_versions = versions
        .iter()
        .map(|version| version.trim().to_string())
        .collect::<Vec<_>>();

    if trimmed_versions.iter().any(String::is_empty) {
        return Err(test_error(format!(
            "live database has an empty Alembic version; got {}",
            format_alembic_versions(&trimmed_versions)
        )));
    }

    if trimmed_versions.len() == 1 && trimmed_versions[0] == EXPECTED_ALEMBIC_HEAD {
        return Ok(());
    }

    Err(test_error(format!(
        "live database Alembic head mismatch: expected {EXPECTED_ALEMBIC_HEAD}, got {}; run `cd backend && uv run alembic upgrade head` against the database configured by BIJMANTRA_LIVE_DATABASE_URL",
        format_alembic_versions(&trimmed_versions)
    )))
}

fn format_alembic_versions(versions: &[String]) -> String {
    if versions.is_empty() {
        return "<none>".to_string();
    }

    versions.join(", ")
}

fn alembic_migration_heads() -> TestResult<BTreeSet<String>> {
    let versions_dir = workspace_root().join("backend/alembic/versions");
    let mut revisions = BTreeSet::new();
    let mut down_revisions = BTreeSet::new();

    for entry in fs::read_dir(&versions_dir).map_err(|error| {
        test_error(format!(
            "failed to read Alembic versions directory {}: {error}",
            versions_dir.display()
        ))
    })? {
        let path = entry?.path();
        if path.extension().and_then(|extension| extension.to_str()) != Some("py") {
            continue;
        }

        let text = fs::read_to_string(&path)?;
        let revision = parse_alembic_assignment(&text, "revision").ok_or_else(|| {
            test_error(format!(
                "Alembic migration {} is missing a revision assignment",
                path.display()
            ))
        })?;
        revisions.insert(revision);
        down_revisions.extend(parse_alembic_down_revisions(&text));
    }

    Ok(revisions.difference(&down_revisions).cloned().collect())
}

fn parse_alembic_assignment(text: &str, name: &str) -> Option<String> {
    text.lines().find_map(|line| {
        let trimmed = line.trim_start();
        if !trimmed.starts_with(name) {
            return None;
        }

        let (_, rhs) = trimmed.split_once('=')?;
        extract_quoted_values(rhs).into_iter().next()
    })
}

fn parse_alembic_down_revisions(text: &str) -> Vec<String> {
    text.lines()
        .find_map(|line| {
            let trimmed = line.trim_start();
            if !trimmed.starts_with("down_revision") {
                return None;
            }

            let (_, rhs) = trimmed.split_once('=')?;
            Some(extract_quoted_values(rhs))
        })
        .unwrap_or_default()
}

fn extract_quoted_values(input: &str) -> Vec<String> {
    let mut values = Vec::new();
    let mut chars = input.chars();

    while let Some(ch) = chars.next() {
        if ch != '\'' && ch != '"' {
            continue;
        }

        let quote = ch;
        let mut value = String::new();
        for value_ch in chars.by_ref() {
            if value_ch == quote {
                break;
            }
            value.push(value_ch);
        }
        values.push(value);
    }

    values
}

fn workspace_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .ancestors()
        .nth(2)
        .expect("server crate should live under <workspace>/crates/bijmantra-server")
        .to_path_buf()
}

async fn ensure_required_indexes(pool: &PgPool) -> TestResult {
    for index in [
        // Auth and active-user lookup.
        "public.ix_users_organization_id",
        "public.uq_auth_identities_provider_issuer_subject",
        "public.ix_auth_identities_organization_id",
        "public.ix_auth_identities_user_id",
        // Core protected reads.
        "public.ix_people_person_db_id",
        "public.ix_people_organization_id",
        "public.ix_programs_program_db_id",
        "public.ix_programs_program_name",
        "public.ix_programs_organization_id",
        "public.ix_locations_location_db_id",
        "public.ix_locations_location_name",
        "public.ix_locations_organization_id",
        "public.idx_locations_coordinates",
        "public.ix_trials_trial_db_id",
        "public.ix_trials_trial_name",
        "public.ix_trials_program_id",
        "public.ix_trials_location_id",
        "public.ix_trials_organization_id",
        "public.ix_studies_study_db_id",
        "public.ix_studies_study_name",
        "public.ix_studies_trial_id",
        "public.ix_studies_location_id",
        "public.ix_studies_organization_id",
        "public.ix_seasons_season_db_id",
        "public.ix_seasons_year",
        "public.ix_seasons_organization_id",
        "public.ix_lists_list_db_id",
        "public.ix_lists_list_name",
        "public.ix_lists_list_type",
        "public.ix_lists_organization_id",
        "public.ix_ontologies_ontology_db_id",
        "public.ix_ontologies_ontology_name",
        "public.ix_ontologies_organization_id",
        // Observation/ontology reads.
        "public.ix_methods_method_db_id",
        "public.ix_methods_method_name",
        "public.ix_methods_organization_id",
        "public.ix_scales_scale_db_id",
        "public.ix_scales_scale_name",
        "public.ix_scales_organization_id",
        "public.ix_observation_variables_observation_variable_db_id",
        "public.ix_observation_variables_observation_variable_name",
        "public.ix_observation_variables_trait_db_id",
        "public.ix_observation_variables_ontology_term_id",
        "public.ix_observation_variables_organization_id",
        "public.ix_observation_units_observation_unit_db_id",
        "public.ix_observation_units_observation_unit_name",
        "public.ix_observation_units_study_id",
        "public.ix_observation_units_germplasm_id",
        "public.ix_observation_units_organization_id",
        "public.ix_observations_observation_db_id",
        "public.ix_observations_study_id",
        "public.ix_observations_germplasm_id",
        "public.ix_observations_observation_variable_id",
        "public.ix_observations_observation_unit_id",
        "public.ix_observations_organization_id",
        "public.idx_observations_org_created_at",
        // Germplasm and attribute reads.
        "public.ix_germplasm_germplasm_db_id",
        "public.ix_germplasm_germplasm_name",
        "public.idx_germplasm_name_trgm",
        "public.ix_germplasm_common_crop_name",
        "public.ix_germplasm_genus",
        "public.ix_germplasm_organization_id",
        "public.ix_germplasm_attribute_definitions_attribute_db_id",
        "public.ix_germplasm_attribute_definitions_attribute_name",
        "public.ix_germplasm_attribute_definitions_attribute_category",
        "public.ix_germplasm_attribute_definitions_organization_id",
        "public.ix_germplasm_attribute_values_attribute_value_db_id",
        "public.ix_germplasm_attribute_values_attribute_db_id",
        "public.ix_germplasm_attribute_values_germplasm_id",
        "public.ix_germplasm_attribute_values_organization_id",
        "public.ix_breeding_methods_breeding_method_db_id",
        "public.ix_breeding_methods_organization_id",
        // Cross workflow reads.
        "public.ix_crossing_projects_crossing_project_db_id",
        "public.ix_crossing_projects_program_id",
        "public.ix_crossing_projects_organization_id",
        "public.ix_crosses_cross_db_id",
        "public.ix_crosses_crossing_project_id",
        "public.ix_crosses_organization_id",
        "public.ix_planned_crosses_planned_cross_db_id",
        "public.ix_planned_crosses_crossing_project_id",
        "public.ix_planned_crosses_organization_id",
        // Seedlot inventory reads.
        "public.ix_seedlots_seedlot_db_id",
        "public.ix_seedlots_germplasm_id",
        "public.ix_seedlots_location_id",
        "public.ix_seedlots_program_id",
        "public.ix_seedlots_organization_id",
        "public.ix_seedlot_transactions_transaction_db_id",
        "public.ix_seedlot_transactions_seedlot_id",
        "public.ix_seedlot_transactions_organization_id",
        "public.ix_seedlot_inventory_adjustments_organization_id",
        "public.ix_seedlot_inventory_adjustments_seedlot_db_id",
        "public.ix_seedlot_inventory_adjustments_created_at",
        "public.ix_seedlot_inventory_adjustments_reversal_of_public_id",
        // Genotyping reads.
        "public.ix_reference_sets_reference_set_db_id",
        "public.ix_reference_sets_organization_id",
        "public.ix_variant_sets_variant_set_db_id",
        "public.ix_variant_sets_variant_set_name",
        "public.ix_variant_sets_study_id",
        "public.ix_variant_sets_reference_set_id",
        "public.ix_variant_sets_organization_id",
        "public.ix_call_sets_call_set_db_id",
        "public.ix_call_sets_call_set_name",
        "public.ix_call_sets_sample_db_id",
        "public.ix_call_sets_organization_id",
        "public.variant_set_call_sets_pkey",
        // Genome map and marker-position reads.
        "public.ix_genome_maps_map_db_id",
        "public.ix_genome_maps_map_name",
        "public.ix_genome_maps_organization_id",
        "public.ix_linkage_groups_linkage_group_name",
        "public.ix_linkage_groups_map_id",
        "public.ix_linkage_groups_organization_id",
        "public.ix_marker_positions_marker_position_db_id",
        "public.ix_marker_positions_map_id",
        "public.ix_marker_positions_linkage_group_name",
        "public.ix_marker_positions_variant_db_id",
        "public.ix_marker_positions_variant_name",
        "public.ix_marker_positions_organization_id",
    ] {
        let exists = sqlx::query_scalar::<_, Option<String>>("SELECT to_regclass($1)::text")
            .bind(index)
            .fetch_one(pool)
            .await?
            .is_some();
        if !exists {
            return Err(test_error(format!(
                "live database is missing required read index {index}"
            )));
        }
    }

    Ok(())
}

async fn get_json(router: &Router, token: &str, uri: &str) -> TestResult<(StatusCode, Value)> {
    let response = router
        .clone()
        .oneshot(
            Request::builder()
                .uri(uri)
                .header("authorization", format!("Bearer {token}"))
                .body(Body::empty())?,
        )
        .await?;
    let status = response.status();
    let body = to_bytes(response.into_body(), 1024 * 1024).await?;
    let value = serde_json::from_slice(&body).unwrap_or_else(|_| {
        json!({
            "raw": String::from_utf8_lossy(&body)
        })
    });
    Ok((status, value))
}

async fn post_json(
    router: &Router,
    token: &str,
    uri: &str,
    body: &Value,
) -> TestResult<(StatusCode, Value)> {
    let response = router
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(uri)
                .header("authorization", format!("Bearer {token}"))
                .header("content-type", "application/json")
                .body(Body::from(serde_json::to_vec(body)?))?,
        )
        .await?;
    let status = response.status();
    let body = to_bytes(response.into_body(), 1024 * 1024).await?;
    let value = serde_json::from_slice(&body).unwrap_or_else(|_| {
        json!({
            "raw": String::from_utf8_lossy(&body)
        })
    });
    Ok((status, value))
}

async fn upsert_capability_installation(
    pool: &PgPool,
    organization_id: i64,
    capability_id: &str,
    installed_by_user_id: i64,
    granted_permissions: &[&str],
    data_scopes: &[&str],
) -> TestResult {
    let mut tx = pool.begin().await?;
    sqlx::query("SELECT set_config('app.current_organization_id', $1, true)")
        .bind(organization_id.to_string())
        .execute(&mut *tx)
        .await?;
    sqlx::query(
        r#"
        INSERT INTO organization_capability_installations (
            organization_id,
            capability_id,
            enabled,
            lifecycle_state,
            granted_permissions,
            data_scopes,
            installed_by_user_id,
            disabled_by_user_id,
            disabled_at
        )
        VALUES (
            $1,
            $2,
            TRUE,
            'installed',
            $3::json,
            $4::json,
            $5,
            NULL,
            NULL
        )
        ON CONFLICT (organization_id, capability_id) DO UPDATE
        SET enabled = EXCLUDED.enabled,
            lifecycle_state = EXCLUDED.lifecycle_state,
            granted_permissions = EXCLUDED.granted_permissions,
            data_scopes = EXCLUDED.data_scopes,
            installed_by_user_id = EXCLUDED.installed_by_user_id,
            disabled_by_user_id = NULL,
            disabled_at = NULL
        "#,
    )
    .bind(organization_id)
    .bind(capability_id)
    .bind(Json(json!(granted_permissions)))
    .bind(Json(json!(data_scopes)))
    .bind(installed_by_user_id)
    .execute(&mut *tx)
    .await?;
    tx.commit().await?;
    Ok(())
}

async fn delete_capability_installation(
    pool: &PgPool,
    organization_id: i64,
    capability_id: &str,
) -> TestResult {
    let mut tx = pool.begin().await?;
    set_admin_context(&mut tx).await?;
    sqlx::query(
        r#"
        DELETE FROM organization_capability_installations
        WHERE organization_id = $1
          AND capability_id = $2
        "#,
    )
    .bind(organization_id)
    .bind(capability_id)
    .execute(&mut *tx)
    .await?;
    tx.commit().await?;
    Ok(())
}

async fn serve_keycloak_jwks_once() -> TestResult<String> {
    let listener = tokio::net::TcpListener::bind(("127.0.0.1", 0)).await?;
    let address = listener.local_addr()?;
    let body = keycloak_jwks_body();
    tokio::spawn(async move {
        let Ok((mut stream, _)) = listener.accept().await else {
            return;
        };
        let mut request = [0_u8; 1024];
        let _ = stream.read(&mut request).await;
        let response = format!(
            "HTTP/1.1 200 OK\r\ncontent-type: application/json\r\ncontent-length: {}\r\nconnection: close\r\n\r\n{}",
            body.len(),
            body
        );
        let _ = stream.write_all(response.as_bytes()).await;
    });

    Ok(format!("http://{address}/certs"))
}

fn keycloak_jwks_body() -> String {
    json!({
        "keys": [{
            "kty": "RSA",
            "n": "n2SjVzUo7vXgOg5DrseHYy75SZjQIxgSxygYoDCXL3WhvwKaKpEQGBiP_N-swfg_Z6AoSegTSWRNBm497BvctZ9rpOwpJ-do4nifoKL295YBjaY0-pWKSgr-lE3DgnBrLC6bJwR8EjZtrjfQGFzzvQjpXxAB5fRqJUqccr_Tj42FTXx3vjEWgrHApAVAfbxTKV2a1A2txHEfi11ApAti1O0UHidj8BwUrefKiFL6v_dSNySe7LQa_txa0G1_vQuxc0jr3dqeSrURHY-m3uzTMke2sE382_Djj7-7FccbxbC8Is_4Zi2izqv10Iuqoc67xA9YMR8nKA92FuJEl5MO7w",
            "e": "AQAB",
            "kid": "bij-test-key",
            "alg": "RS256",
            "use": "sig"
        }]
    })
    .to_string()
}

fn access_token(secret: &str, user_id: i64, organization_id: i64) -> TestResult<String> {
    access_token_with_superuser(secret, user_id, organization_id, false)
}

fn access_token_with_superuser(
    secret: &str,
    user_id: i64,
    organization_id: i64,
    is_superuser: bool,
) -> TestResult<String> {
    Ok(encode(
        &Header::new(Algorithm::HS256),
        &TestClaims {
            sub: user_id.to_string(),
            organization_id,
            is_superuser,
            exp: 4_102_444_800,
        },
        &EncodingKey::from_secret(secret.as_bytes()),
    )?)
}

fn live_database_url() -> Option<String> {
    std::env::var("BIJMANTRA_LIVE_DATABASE_URL")
        .ok()
        .map(|url| normalize_for_sqlx(&url))
        .filter(|url| !url.trim().is_empty())
}

fn normalize_for_sqlx(url: &str) -> String {
    url.trim()
        .strip_prefix("postgresql+asyncpg://")
        .map(|rest| format!("postgres://{rest}"))
        .or_else(|| {
            url.trim()
                .strip_prefix("postgres+asyncpg://")
                .map(|rest| format!("postgres://{rest}"))
        })
        .unwrap_or_else(|| url.trim().to_string())
}

fn unique_suffix() -> TestResult<u128> {
    Ok(SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| test_error(format!("system clock is before UNIX_EPOCH: {error}")))?
        .as_nanos())
}

async fn seedlot_count_text(
    pool: &PgPool,
    organization_id: i64,
    seedlot_db_id: &str,
) -> TestResult<String> {
    let mut tx = pool.begin().await?;
    sqlx::query("SELECT set_config('app.current_organization_id', $1, true)")
        .bind(organization_id.to_string())
        .execute(&mut *tx)
        .await?;
    let count = sqlx::query_scalar::<_, String>(
        r#"
        SELECT count::text
        FROM seedlots
        WHERE organization_id = $1
          AND seedlot_db_id = $2
        "#,
    )
    .bind(organization_id)
    .bind(seedlot_db_id)
    .fetch_one(&mut *tx)
    .await?;
    tx.commit().await?;
    Ok(count)
}

async fn seedlot_adjustment_count(
    pool: &PgPool,
    organization_id: i64,
    seedlot_db_id: &str,
) -> TestResult<i64> {
    let mut tx = pool.begin().await?;
    sqlx::query("SELECT set_config('app.current_organization_id', $1, true)")
        .bind(organization_id.to_string())
        .execute(&mut *tx)
        .await?;
    let count = sqlx::query_scalar::<_, i64>(
        r#"
        SELECT COUNT(*)::bigint
        FROM seedlot_inventory_adjustments
        WHERE organization_id = $1
          AND seedlot_db_id = $2
        "#,
    )
    .bind(organization_id)
    .bind(seedlot_db_id)
    .fetch_one(&mut *tx)
    .await?;
    tx.commit().await?;
    Ok(count)
}

async fn seedlot_adjustment_audit_count(
    pool: &PgPool,
    organization_id: i64,
    seedlot_db_id: &str,
) -> TestResult<i64> {
    let mut tx = pool.begin().await?;
    sqlx::query("SELECT set_config('app.current_organization_id', $1, true)")
        .bind(organization_id.to_string())
        .execute(&mut *tx)
        .await?;
    let count = sqlx::query_scalar::<_, i64>(
        r#"
        SELECT COUNT(*)::bigint
        FROM audit_logs
        WHERE organization_id = $1
          AND action = 'seed_lot.adjusted'
          AND target_type = 'seedlot_inventory_adjustment'
          AND changes->>'seedLotDbId' = $2
        "#,
    )
    .bind(organization_id)
    .bind(seedlot_db_id)
    .fetch_one(&mut *tx)
    .await?;
    tx.commit().await?;
    Ok(count)
}

fn debug_error(error: impl std::fmt::Debug) -> TestError {
    test_error(format!("{error:?}"))
}

fn list_field_values(body: &Value, field: &str) -> TestResult<Vec<String>> {
    let data = body
        .pointer("/result/data")
        .and_then(Value::as_array)
        .ok_or_else(|| test_error("expected BrAPI list response at /result/data"))?;

    Ok(data
        .iter()
        .filter_map(|item| item.get(field).and_then(Value::as_str))
        .map(ToOwned::to_owned)
        .collect())
}

#[track_caller]
fn require_json_string(body: &Value, pointer: &str, expected: &str) -> TestResult {
    match body.pointer(pointer).and_then(Value::as_str) {
        Some(actual) if actual == expected => Ok(()),
        Some(actual) => Err(test_error(format!(
            "expected {pointer} to be {expected}, got {actual}"
        ))),
        None => Err(test_error(format!("missing JSON string at {pointer}"))),
    }
}

#[track_caller]
fn require_json_u64(body: &Value, pointer: &str, expected: u64) -> TestResult {
    let caller = std::panic::Location::caller();
    match body.pointer(pointer).and_then(Value::as_u64) {
        Some(actual) if actual == expected => Ok(()),
        Some(actual) => Err(test_error(format!(
            "{}:{} expected {pointer} to be {expected}, got {actual}",
            caller.file(),
            caller.line()
        ))),
        None => Err(test_error(format!(
            "{}:{} missing JSON integer at {pointer}",
            caller.file(),
            caller.line()
        ))),
    }
}

#[track_caller]
fn require_json_bool(body: &Value, pointer: &str, expected: bool) -> TestResult {
    match body.pointer(pointer).and_then(Value::as_bool) {
        Some(actual) if actual == expected => Ok(()),
        Some(actual) => Err(test_error(format!(
            "expected {pointer} to be {expected}, got {actual}"
        ))),
        None => Err(test_error(format!("missing JSON boolean at {pointer}"))),
    }
}

#[track_caller]
fn require_json_f64(body: &Value, pointer: &str, expected: f64) -> TestResult {
    match body.pointer(pointer).and_then(Value::as_f64) {
        Some(actual) if (actual - expected).abs() <= 0.000_001 => Ok(()),
        Some(actual) => Err(test_error(format!(
            "expected {pointer} to be {expected}, got {actual}"
        ))),
        None => Err(test_error(format!("missing JSON number at {pointer}"))),
    }
}

#[track_caller]
fn require_json_null(body: &Value, pointer: &str) -> TestResult {
    match body.pointer(pointer) {
        Some(Value::Null) => Ok(()),
        Some(actual) => Err(test_error(format!(
            "expected {pointer} to be null, got {actual}"
        ))),
        None => Err(test_error(format!("missing JSON value at {pointer}"))),
    }
}

#[track_caller]
fn require_array_len(body: &Value, pointer: &str, expected: usize) -> TestResult {
    match body.pointer(pointer).and_then(Value::as_array) {
        Some(actual) if actual.len() == expected => Ok(()),
        Some(actual) => Err(test_error(format!(
            "expected {pointer} to contain {expected} items, got {}",
            actual.len()
        ))),
        None => Err(test_error(format!("missing JSON array at {pointer}"))),
    }
}

#[track_caller]
fn require_status(actual: StatusCode, expected: StatusCode, context: &str) -> TestResult {
    if actual == expected {
        Ok(())
    } else {
        Err(test_error(format!(
            "expected {context} to return {expected}, got {actual}"
        )))
    }
}

#[track_caller]
fn require_contains(values: &[String], expected: &str, context: &str) -> TestResult {
    if values.iter().any(|value| value == expected) {
        Ok(())
    } else {
        Err(test_error(format!(
            "expected {context} to contain {expected}; got {values:?}"
        )))
    }
}

#[track_caller]
fn require_not_contains(values: &[String], forbidden: &str, context: &str) -> TestResult {
    if values.iter().any(|value| value == forbidden) {
        Err(test_error(format!(
            "expected {context} not to contain {forbidden}; got {values:?}"
        )))
    } else {
        Ok(())
    }
}

#[track_caller]
fn require_order_prefix(values: &[String], expected: &[&str], context: &str) -> TestResult {
    let actual_prefix = values
        .iter()
        .take(expected.len())
        .map(String::as_str)
        .collect::<Vec<_>>();
    if actual_prefix == expected {
        return Ok(());
    }

    let caller = std::panic::Location::caller();
    Err(test_error(format!(
        "{}:{} expected {context} order prefix {expected:?}; got {values:?}",
        caller.file(),
        caller.line()
    )))
}

fn test_error(message: impl Into<String>) -> TestError {
    Box::new(io::Error::other(message.into()))
}
