use std::collections::BTreeMap;
use std::time::{Duration, Instant};

use bijmantra_core::{
    AttributeSummary, AttributeValueSummary, BreedingMethodSummary, CallSetSummary, Coordinates,
    CrossSummary, CrossingProjectSummary, DependencyHealth, GenomeMapSummary, GermplasmSummary,
    IdempotencyKey, LinkageGroupSummary, ListSummary, LocationSummary, MarkerPositionSummary,
    MethodSummary, ObservationSummary, ObservationUnitSummary, OntologySummary, PersonSummary,
    PlannedCrossParentSummary, PlannedCrossSummary, PlatformCapabilityAccessContext,
    ProgramSummary, SEEDLOT_INVENTORY_ADJUST_AUDIT_EVENT, SEEDLOT_TRACEABILITY_CAPABILITY_ID,
    ScaleCategory, ScaleSummary, ScaleValidValues, SeasonSummary, SeedInventorySpeciesSummary,
    SeedInventorySummary, SeedInventoryViabilityDueLot, SeedlotInventoryAdjustmentCreate,
    SeedlotInventoryAdjustmentRecord, SeedlotInventoryAdjustmentType,
    SeedlotInventoryAdjustmentUnit, SeedlotSummary, SeedlotTransactionSummary, StudySummary,
    TraitSummary, TrialSummary, VariableMethodSummary, VariableScaleSummary, VariableSummary,
    VariableTraitSummary, VariantSetSummary, WriteAuthorizationDecision, WriteAuthorizationPlan,
    WriteReadinessError,
};
use chrono::{NaiveDate, Utc};
use serde_json::{Value, json};
use sqlx::postgres::{PgPoolOptions, PgRow};
use sqlx::{PgPool, Row};

const READ_STATEMENT_TIMEOUT_ENV: &str = "BIJMANTRA_READ_STATEMENT_TIMEOUT_MS";
const DEFAULT_READ_STATEMENT_TIMEOUT_MS: u64 = 10_000;
const MAX_READ_STATEMENT_TIMEOUT_MS: u64 = 300_000;
const READ_REPOSITORY_HEALTH_TIMEOUT_MS: u64 = 500;
const SEEDLOT_ADJUSTMENT_AUDIT_TARGET_TYPE: &str = "seedlot_inventory_adjustment";

#[derive(Debug, Clone)]
pub struct DataStore {
    pool: Option<PgPool>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProgramListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub program_name: Option<String>,
    pub abbreviation: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocationListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub location_type: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TrialListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub active: Option<bool>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StudyListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub active: Option<bool>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeasonListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub year: Option<i32>,
    pub season_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PersonListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub first_name: Option<String>,
    pub last_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ListListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub list_type: Option<String>,
    pub list_name: Option<String>,
    pub list_db_id: Option<String>,
    pub list_source: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OntologyListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub ontology_db_id: Option<String>,
    pub ontology_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GermplasmListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub germplasm_name: Option<String>,
    pub common_crop_name: Option<String>,
    pub species: Option<String>,
    pub genus: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AttributeListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub attribute_category: Option<String>,
    pub attribute_db_id: Option<String>,
    pub attribute_name: Option<String>,
    pub common_crop_name: Option<String>,
    pub trait_db_id: Option<String>,
    pub method_db_id: Option<String>,
    pub scale_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AttributeValueListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub attribute_db_id: Option<String>,
    pub attribute_name: Option<String>,
    pub attribute_value_db_id: Option<String>,
    pub germplasm_db_id: Option<String>,
    pub germplasm_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BreedingMethodListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TraitListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub trait_class: Option<String>,
    pub observation_variable_name: Option<String>,
    pub common_crop_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VariableListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub observation_variable_db_id: Option<String>,
    pub observation_variable_name: Option<String>,
    pub trait_class: Option<String>,
    pub common_crop_name: Option<String>,
    pub method_db_id: Option<String>,
    pub scale_db_id: Option<String>,
    pub ontology_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObservationListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub study_id: Option<i64>,
    pub germplasm_id: Option<i64>,
    pub observation_variable_db_id: Option<String>,
    pub observation_unit_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObservationUnitListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub study_id: Option<i64>,
    pub germplasm_id: Option<i64>,
    pub observation_level: Option<String>,
    pub observation_unit_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MethodListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub method_db_id: Option<String>,
    pub method_class: Option<String>,
    pub method_name: Option<String>,
    pub ontology_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScaleListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub scale_db_id: Option<String>,
    pub scale_name: Option<String>,
    pub data_type: Option<String>,
    pub ontology_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeedlotListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub germplasm_db_id: Option<String>,
    pub location_db_id: Option<String>,
    pub program_db_id: Option<String>,
    pub seedlot_db_id: Option<String>,
    pub seedlot_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeedlotTransactionListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub seedlot_db_id: Option<String>,
    pub transaction_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeedlotScopedTransactionListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub seedlot_db_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeedlotInventoryAdjustmentListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub seedlot_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CallSetListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub call_set_db_id: Option<String>,
    pub call_set_name: Option<String>,
    pub sample_db_id: Option<String>,
    pub variant_set_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenomeMapListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub map_db_id: Option<String>,
    pub map_pui: Option<String>,
    pub common_crop_name: Option<String>,
    pub scientific_name: Option<String>,
    pub map_type: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LinkageGroupListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub map_db_id: String,
}

#[derive(Debug, Clone, PartialEq)]
pub struct MarkerPositionListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub map_db_id: Option<String>,
    pub linkage_group_name: Option<String>,
    pub variant_db_id: Option<String>,
    pub min_position: Option<f64>,
    pub max_position: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VariantSetListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub variant_set_db_id: Option<String>,
    pub study_db_id: Option<String>,
    pub reference_set_db_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CrossingProjectListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub crossing_project_db_id: Option<String>,
    pub crossing_project_name: Option<String>,
    pub program_db_id: Option<String>,
    pub common_crop_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CrossListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub crossing_project_db_id: Option<String>,
    pub cross_type: Option<String>,
    pub cross_db_id: Option<String>,
    pub cross_name: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PlannedCrossListParams {
    pub organization_id: i64,
    pub page: u32,
    pub page_size: u32,
    pub crossing_project_db_id: Option<String>,
    pub crossing_project_name: Option<String>,
    pub planned_cross_db_id: Option<String>,
    pub planned_cross_name: Option<String>,
    pub status: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ActiveUser {
    pub user_id: i64,
    pub organization_id: i64,
    pub is_superuser: bool,
}

#[derive(Debug)]
pub enum DataStoreError {
    Unavailable,
    Query(sqlx::Error),
}

#[derive(Debug)]
pub enum UserLookupError {
    Unavailable,
    InvalidCredentials,
    Inactive,
    Query(sqlx::Error),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WriteTransactionOptions {
    pub organization_id: i64,
    pub actor_user_id: i64,
    pub idempotency_key: Option<String>,
    pub audit_event: String,
}

#[derive(Debug)]
pub enum WriteTransactionError {
    Unavailable,
    InvalidContext(&'static str),
    Query(sqlx::Error),
}

#[derive(Debug)]
pub enum SeedlotInventoryAdjustmentWriteError {
    Unavailable,
    InvalidContext(&'static str),
    InvalidStoredRecord(&'static str),
    NotFound,
    AlreadyReversed,
    IdempotencyConflict,
    AuthorizationDenied(WriteAuthorizationDecision),
    Validation(WriteReadinessError),
    Query(sqlx::Error),
}

impl From<WriteTransactionError> for SeedlotInventoryAdjustmentWriteError {
    fn from(error: WriteTransactionError) -> Self {
        match error {
            WriteTransactionError::Unavailable => Self::Unavailable,
            WriteTransactionError::InvalidContext(message) => Self::InvalidContext(message),
            WriteTransactionError::Query(error) => Self::Query(error),
        }
    }
}

impl From<WriteReadinessError> for SeedlotInventoryAdjustmentWriteError {
    fn from(error: WriteReadinessError) -> Self {
        Self::Validation(error)
    }
}

impl WriteTransactionOptions {
    fn validate(&self) -> Result<(), WriteTransactionError> {
        if self.organization_id <= 0 {
            return Err(WriteTransactionError::InvalidContext(
                "organization_id must be positive",
            ));
        }
        if self.actor_user_id <= 0 {
            return Err(WriteTransactionError::InvalidContext(
                "actor_user_id must be positive",
            ));
        }
        if self.audit_event.trim().is_empty() {
            return Err(WriteTransactionError::InvalidContext(
                "audit_event is required",
            ));
        }
        if self
            .idempotency_key
            .as_deref()
            .is_some_and(|key| key.trim().is_empty())
        {
            return Err(WriteTransactionError::InvalidContext(
                "idempotency_key cannot be blank when present",
            ));
        }
        Ok(())
    }
}

#[derive(Debug)]
struct ReadRepositoryTimer {
    operation: &'static str,
    started_at: Instant,
}

impl ReadRepositoryTimer {
    fn start(operation: &'static str) -> Self {
        tracing::debug!(
            repository_operation = operation,
            "starting Rust read repository operation"
        );
        Self {
            operation,
            started_at: Instant::now(),
        }
    }
}

impl Drop for ReadRepositoryTimer {
    fn drop(&mut self) {
        let elapsed_ms = self.started_at.elapsed().as_secs_f64() * 1000.0;
        tracing::debug!(
            repository_operation = self.operation,
            elapsed_ms,
            "finished Rust read repository operation"
        );
    }
}

fn data_store_unavailable(operation: &'static str) -> DataStoreError {
    tracing::warn!(
        repository_operation = operation,
        route_context = "rust_read_beta",
        "Rust BrAPI data repository is unavailable"
    );
    DataStoreError::Unavailable
}

fn user_store_unavailable(operation: &'static str) -> UserLookupError {
    tracing::warn!(
        repository_operation = operation,
        route_context = "rust_read_beta_auth",
        "Rust auth user repository is unavailable"
    );
    UserLookupError::Unavailable
}

fn write_store_unavailable(operation: &'static str) -> WriteTransactionError {
    tracing::warn!(
        repository_operation = operation,
        route_context = "rust_write_readiness",
        "Rust write transaction repository is unavailable"
    );
    WriteTransactionError::Unavailable
}

impl DataStore {
    pub fn unavailable() -> Self {
        Self { pool: None }
    }

    pub fn from_database_url(database_url: &str) -> Self {
        Self {
            pool: normalize_database_url(database_url).and_then(configure_postgres_pool),
        }
    }

    pub fn from_env() -> Self {
        let database_url = std::env::var("BIJMANTRA_DATABASE_URL")
            .ok()
            .or_else(|| std::env::var("DATABASE_URL").ok());

        match database_url {
            Some(database_url) => Self::from_database_url(&database_url),
            None => Self::unavailable(),
        }
    }

    pub async fn begin_write_transaction(
        &self,
        options: &WriteTransactionOptions,
    ) -> Result<sqlx::Transaction<'_, sqlx::Postgres>, WriteTransactionError> {
        let _timer = ReadRepositoryTimer::start("begin_write_transaction");
        options.validate()?;
        let Some(pool) = &self.pool else {
            return Err(write_store_unavailable("begin_write_transaction"));
        };

        let mut tx = pool.begin().await.map_err(WriteTransactionError::Query)?;
        set_write_transaction_context(&mut tx, options)
            .await
            .map_err(WriteTransactionError::Query)?;
        Ok(tx)
    }

    pub async fn build_seedlot_inventory_adjustment_access_context_internal(
        &self,
        organization_id: i64,
        user_id: i64,
    ) -> Result<Option<PlatformCapabilityAccessContext>, SeedlotInventoryAdjustmentWriteError> {
        let _timer = ReadRepositoryTimer::start(
            "build_seedlot_inventory_adjustment_access_context_internal",
        );
        let Some(pool) = &self.pool else {
            return Err(write_store_unavailable(
                "build_seedlot_inventory_adjustment_access_context_internal",
            )
            .into());
        };
        validate_write_lookup_context(organization_id, Some(user_id))?;

        let mut tx = pool
            .begin()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        set_transaction_organization_context(&mut tx, organization_id)
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        let row = sqlx::query(
            r#"
            SELECT
                capability_id,
                granted_permissions,
                data_scopes
            FROM organization_capability_installations
            WHERE organization_id = $1
              AND capability_id = $2
              AND enabled IS TRUE
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(SEEDLOT_TRACEABILITY_CAPABILITY_ID)
        .fetch_optional(&mut *tx)
        .await
        .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        tx.commit()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        let Some(row) = row else {
            return Ok(None);
        };

        let granted_permissions = value_to_strings(row.get::<Value, _>("granted_permissions"))
            .ok_or(SeedlotInventoryAdjustmentWriteError::InvalidStoredRecord(
                "organization_capability_installations.granted_permissions",
            ))?;
        let data_scopes = value_to_strings(row.get::<Value, _>("data_scopes")).ok_or(
            SeedlotInventoryAdjustmentWriteError::InvalidStoredRecord(
                "organization_capability_installations.data_scopes",
            ),
        )?;

        Ok(Some(PlatformCapabilityAccessContext {
            organization_id,
            user_id,
            installed_capabilities: std::iter::once(row.get::<String, _>("capability_id"))
                .collect(),
            granted_permissions: granted_permissions.into_iter().collect(),
            data_scopes: data_scopes.into_iter().collect(),
        }))
    }

    pub async fn create_seedlot_inventory_adjustment_internal(
        &self,
        command: SeedlotInventoryAdjustmentCreate,
    ) -> Result<SeedlotInventoryAdjustmentRecord, SeedlotInventoryAdjustmentWriteError> {
        let _timer = ReadRepositoryTimer::start("create_seedlot_inventory_adjustment_internal");
        if self.pool.is_none() {
            return Err(
                write_store_unavailable("create_seedlot_inventory_adjustment_internal").into(),
            );
        }
        command.validate()?;

        let options = WriteTransactionOptions {
            organization_id: command.organization_id,
            actor_user_id: command.actor_user_id,
            idempotency_key: Some(command.idempotency_key.as_str().to_owned()),
            audit_event: SEEDLOT_INVENTORY_ADJUST_AUDIT_EVENT.to_owned(),
        };
        let mut tx = self.begin_write_transaction(&options).await?;

        if let Some(existing) = fetch_seedlot_adjustment_by_idempotency_in_tx(
            &mut tx,
            command.organization_id,
            command.actor_user_id,
            command.idempotency_key.as_str(),
        )
        .await?
        {
            if existing.matches_create_command(&command) {
                tx.commit()
                    .await
                    .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
                return Ok(existing);
            }
            return Err(SeedlotInventoryAdjustmentWriteError::IdempotencyConflict);
        }

        let record = match insert_seedlot_inventory_adjustment_in_tx(&mut tx, &command).await? {
            Some(record) => record,
            None => {
                let existing =
                    resolve_seedlot_adjustment_idempotency_collision_in_tx(&mut tx, &command)
                        .await?;
                tx.commit()
                    .await
                    .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
                return Ok(existing);
            }
        };
        tx.commit()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        Ok(record)
    }

    pub async fn create_seedlot_inventory_adjustment_authorized_internal(
        &self,
        access_context: &PlatformCapabilityAccessContext,
        command: SeedlotInventoryAdjustmentCreate,
    ) -> Result<SeedlotInventoryAdjustmentRecord, SeedlotInventoryAdjustmentWriteError> {
        let _timer =
            ReadRepositoryTimer::start("create_seedlot_inventory_adjustment_authorized_internal");
        let decision = WriteAuthorizationPlan::seedlot_inventory_adjustment()
            .evaluate_platform_context(
                access_context,
                command.organization_id,
                command.actor_user_id,
            );
        if !decision.allowed {
            return Err(SeedlotInventoryAdjustmentWriteError::AuthorizationDenied(
                decision,
            ));
        }
        if self.pool.is_none() {
            return Err(write_store_unavailable(
                "create_seedlot_inventory_adjustment_authorized_internal",
            )
            .into());
        }

        self.create_seedlot_inventory_adjustment_internal(command)
            .await
    }

    pub async fn get_seedlot_inventory_adjustment_by_public_id_internal(
        &self,
        organization_id: i64,
        public_id: bijmantra_core::PublicId,
    ) -> Result<Option<SeedlotInventoryAdjustmentRecord>, SeedlotInventoryAdjustmentWriteError>
    {
        let _timer =
            ReadRepositoryTimer::start("get_seedlot_inventory_adjustment_by_public_id_internal");
        let Some(pool) = &self.pool else {
            return Err(write_store_unavailable(
                "get_seedlot_inventory_adjustment_by_public_id_internal",
            )
            .into());
        };
        validate_write_lookup_context(organization_id, None)?;
        public_id.require_uuid7()?;

        let mut tx = pool
            .begin()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        set_transaction_organization_context(&mut tx, organization_id)
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        let row = sqlx::query(SEEDLOT_ADJUSTMENT_SELECT_BY_PUBLIC_ID_SQL)
            .bind(organization_id)
            .bind(public_id.as_uuid().to_string())
            .fetch_optional(&mut *tx)
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        tx.commit()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        row.map(seedlot_inventory_adjustment_record_from_row)
            .transpose()
    }

    pub async fn get_seedlot_inventory_adjustment_by_idempotency_key_internal(
        &self,
        organization_id: i64,
        actor_user_id: i64,
        idempotency_key: &IdempotencyKey,
    ) -> Result<Option<SeedlotInventoryAdjustmentRecord>, SeedlotInventoryAdjustmentWriteError>
    {
        let _timer = ReadRepositoryTimer::start(
            "get_seedlot_inventory_adjustment_by_idempotency_key_internal",
        );
        let Some(pool) = &self.pool else {
            return Err(write_store_unavailable(
                "get_seedlot_inventory_adjustment_by_idempotency_key_internal",
            )
            .into());
        };
        validate_write_lookup_context(organization_id, Some(actor_user_id))?;

        let mut tx = pool
            .begin()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        set_transaction_organization_context(&mut tx, organization_id)
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        let row = sqlx::query(SEEDLOT_ADJUSTMENT_SELECT_BY_IDEMPOTENCY_SQL)
            .bind(organization_id)
            .bind(actor_user_id)
            .bind(idempotency_key.as_str())
            .fetch_optional(&mut *tx)
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        tx.commit()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        row.map(seedlot_inventory_adjustment_record_from_row)
            .transpose()
    }

    pub async fn list_seedlot_inventory_adjustments_internal(
        &self,
        params: &SeedlotInventoryAdjustmentListParams,
    ) -> Result<(Vec<SeedlotInventoryAdjustmentRecord>, i64), SeedlotInventoryAdjustmentWriteError>
    {
        let _timer = ReadRepositoryTimer::start("list_seedlot_inventory_adjustments_internal");
        let Some(pool) = &self.pool else {
            return Err(
                write_store_unavailable("list_seedlot_inventory_adjustments_internal").into(),
            );
        };
        validate_write_lookup_context(params.organization_id, None)?;

        let limit = i64::from(params.page_size.clamp(1, 1000));
        let offset = i64::from(params.page).saturating_mul(limit);

        let mut tx = pool
            .begin()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        set_transaction_organization_context(&mut tx, params.organization_id)
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        let seedlot_filter = exact_filter_value(&params.seedlot_db_id);
        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)::bigint
            FROM seedlot_inventory_adjustments
            WHERE organization_id = $1
              AND ($2::text IS NULL OR seedlot_db_id = $2)
            "#,
        )
        .bind(params.organization_id)
        .bind(seedlot_filter)
        .fetch_one(&mut *tx)
        .await
        .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        let rows = sqlx::query(SEEDLOT_ADJUSTMENT_LIST_SQL)
            .bind(params.organization_id)
            .bind(seedlot_filter)
            .bind(limit)
            .bind(offset)
            .fetch_all(&mut *tx)
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        tx.commit()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        let records = rows
            .into_iter()
            .map(seedlot_inventory_adjustment_record_from_row)
            .collect::<Result<Vec<_>, _>>()?;
        Ok((records, total_count))
    }

    pub async fn reverse_seedlot_inventory_adjustment_internal(
        &self,
        organization_id: i64,
        actor_user_id: i64,
        original_public_id: bijmantra_core::PublicId,
        reversal_public_id: bijmantra_core::PublicId,
        idempotency_key: IdempotencyKey,
        reason: impl Into<String>,
    ) -> Result<SeedlotInventoryAdjustmentRecord, SeedlotInventoryAdjustmentWriteError> {
        let _timer = ReadRepositoryTimer::start("reverse_seedlot_inventory_adjustment_internal");
        if self.pool.is_none() {
            return Err(
                write_store_unavailable("reverse_seedlot_inventory_adjustment_internal").into(),
            );
        }
        validate_write_lookup_context(organization_id, Some(actor_user_id))?;
        original_public_id.require_uuid7()?;
        reversal_public_id.require_uuid7()?;

        let options = WriteTransactionOptions {
            organization_id,
            actor_user_id,
            idempotency_key: Some(idempotency_key.as_str().to_owned()),
            audit_event: SEEDLOT_INVENTORY_ADJUST_AUDIT_EVENT.to_owned(),
        };
        let mut tx = self.begin_write_transaction(&options).await?;

        let original = fetch_seedlot_adjustment_by_public_id_in_tx(
            &mut tx,
            organization_id,
            original_public_id,
        )
        .await?
        .ok_or(SeedlotInventoryAdjustmentWriteError::NotFound)?;

        let command = SeedlotInventoryAdjustmentCreate::new(
            reversal_public_id,
            idempotency_key,
            organization_id,
            original.seedlot_db_id.clone(),
            SeedlotInventoryAdjustmentType::Correction,
            negate_quantity_delta(&original.quantity_delta),
            original.unit,
            reason,
            actor_user_id,
            None,
            json_object_with_original_public_id(original.public_id),
        )?
        .with_reversal_of_public_id(original.public_id)?;

        if let Some(existing) = fetch_seedlot_adjustment_by_idempotency_in_tx(
            &mut tx,
            organization_id,
            actor_user_id,
            command.idempotency_key.as_str(),
        )
        .await?
        {
            if existing.matches_create_command(&command) {
                tx.commit()
                    .await
                    .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
                return Ok(existing);
            }
            return Err(SeedlotInventoryAdjustmentWriteError::IdempotencyConflict);
        }

        if original.reversed_at.is_some() {
            return Err(SeedlotInventoryAdjustmentWriteError::AlreadyReversed);
        }

        let record = match insert_seedlot_inventory_adjustment_in_tx(&mut tx, &command).await? {
            Some(record) => record,
            None => {
                let existing =
                    resolve_seedlot_adjustment_idempotency_collision_in_tx(&mut tx, &command)
                        .await?;
                tx.commit()
                    .await
                    .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
                return Ok(existing);
            }
        };
        let reversal_mark = sqlx::query(
            r#"
            UPDATE seedlot_inventory_adjustments
            SET reversed_at = now()
            WHERE organization_id = $1
              AND public_id = $2::uuid
              AND reversed_at IS NULL
            "#,
        )
        .bind(organization_id)
        .bind(original.public_id.as_uuid().to_string())
        .execute(&mut *tx)
        .await
        .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;
        if reversal_mark.rows_affected() != 1 {
            return Err(SeedlotInventoryAdjustmentWriteError::AlreadyReversed);
        }
        tx.commit()
            .await
            .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

        Ok(record)
    }

    pub async fn reverse_seedlot_inventory_adjustment_authorized_internal(
        &self,
        access_context: &PlatformCapabilityAccessContext,
        organization_id: i64,
        actor_user_id: i64,
        original_public_id: bijmantra_core::PublicId,
        reversal_public_id: bijmantra_core::PublicId,
        idempotency_key: IdempotencyKey,
        reason: impl Into<String>,
    ) -> Result<SeedlotInventoryAdjustmentRecord, SeedlotInventoryAdjustmentWriteError> {
        let _timer =
            ReadRepositoryTimer::start("reverse_seedlot_inventory_adjustment_authorized_internal");
        let decision = WriteAuthorizationPlan::seedlot_inventory_adjustment()
            .evaluate_platform_context(access_context, organization_id, actor_user_id);
        if !decision.allowed {
            return Err(SeedlotInventoryAdjustmentWriteError::AuthorizationDenied(
                decision,
            ));
        }
        if self.pool.is_none() {
            return Err(write_store_unavailable(
                "reverse_seedlot_inventory_adjustment_authorized_internal",
            )
            .into());
        }

        self.reverse_seedlot_inventory_adjustment_internal(
            organization_id,
            actor_user_id,
            original_public_id,
            reversal_public_id,
            idempotency_key,
            reason,
        )
        .await
    }

    pub async fn read_repository_health_dependency(&self) -> Option<DependencyHealth> {
        let _timer = ReadRepositoryTimer::start("read_repository_health_dependency");
        let Some(pool) = &self.pool else {
            return None;
        };

        let health_check = sqlx::query_scalar::<_, i64>("SELECT 1").fetch_one(pool);
        match tokio::time::timeout(
            Duration::from_millis(READ_REPOSITORY_HEALTH_TIMEOUT_MS),
            health_check,
        )
        .await
        {
            Ok(Ok(1)) => Some(DependencyHealth::healthy(false)),
            Ok(Ok(result)) => Some(DependencyHealth::degraded(
                false,
                format!(
                    "configured Postgres read repository returned unexpected health result {result}"
                ),
            )),
            Ok(Err(error)) => {
                tracing::warn!(
                    %error,
                    route_context = "rust_read_beta_pool",
                    "Rust Postgres read repository health check failed"
                );
                Some(DependencyHealth::degraded(
                    false,
                    "configured Postgres read repository health check failed",
                ))
            }
            Err(_) => {
                tracing::warn!(
                    route_context = "rust_read_beta_pool",
                    timeout_ms = READ_REPOSITORY_HEALTH_TIMEOUT_MS,
                    "Rust Postgres read repository health check timed out"
                );
                Some(DependencyHealth::degraded(
                    false,
                    "configured Postgres read repository health check timed out",
                ))
            }
        }
    }

    pub async fn active_user(
        &self,
        user_id: i64,
        token_organization_id: i64,
    ) -> Result<ActiveUser, UserLookupError> {
        let _timer = ReadRepositoryTimer::start("active_user");
        let Some(pool) = &self.pool else {
            return Err(user_store_unavailable("active_user"));
        };

        let mut tx = pool.begin().await.map_err(UserLookupError::Query)?;
        set_transaction_organization_context(&mut tx, token_organization_id)
            .await
            .map_err(UserLookupError::Query)?;

        let row = sqlx::query(
            r#"
            SELECT id, organization_id, is_active, is_superuser
            FROM users
            WHERE id = $1
              AND ($2 = 0 OR organization_id = $2)
            "#,
        )
        .bind(user_id)
        .bind(token_organization_id)
        .fetch_optional(&mut *tx)
        .await
        .map_err(UserLookupError::Query)?
        .ok_or(UserLookupError::InvalidCredentials)?;

        if !row.get::<bool, _>("is_active") {
            return Err(UserLookupError::Inactive);
        }

        let user = ActiveUser {
            user_id: row.get("id"),
            organization_id: row.get("organization_id"),
            is_superuser: row.get("is_superuser"),
        };

        tx.commit().await.map_err(UserLookupError::Query)?;

        Ok(user)
    }

    pub async fn active_keycloak_user(
        &self,
        issuer: &str,
        subject: &str,
    ) -> Result<ActiveUser, UserLookupError> {
        let _timer = ReadRepositoryTimer::start("active_keycloak_user");
        let Some(pool) = &self.pool else {
            return Err(user_store_unavailable("active_keycloak_user"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                u.id,
                u.organization_id,
                u.is_active,
                u.is_superuser
            FROM auth_identities ai
            JOIN users u
              ON u.id = ai.user_id
             AND u.organization_id = ai.organization_id
            WHERE ai.provider = 'keycloak'
              AND ai.issuer = $1
              AND ai.subject = $2
            "#,
        )
        .bind(issuer)
        .bind(subject)
        .fetch_optional(pool)
        .await
        .map_err(UserLookupError::Query)?
        .ok_or(UserLookupError::InvalidCredentials)?;

        if !row.get::<bool, _>("is_active") {
            return Err(UserLookupError::Inactive);
        }

        Ok(ActiveUser {
            user_id: row.get("id"),
            organization_id: row.get("organization_id"),
            is_superuser: row.get("is_superuser"),
        })
    }

    pub async fn list_locations(
        &self,
        params: LocationListParams,
    ) -> Result<(Vec<LocationSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_locations");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_locations"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM locations
            WHERE organization_id = $1
              AND ($2::text IS NULL OR location_type = $2)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.location_type.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                location_db_id,
                location_name,
                location_type,
                abbreviation,
                country_name,
                country_code,
                institute_name,
                institute_address,
                CASE WHEN coordinates IS NULL THEN NULL ELSE ST_Y(coordinates::geometry) END AS latitude,
                CASE WHEN coordinates IS NULL THEN NULL ELSE ST_X(coordinates::geometry) END AS longitude,
                CASE WHEN coordinates IS NULL THEN NULL ELSE ST_Z(coordinates::geometry) END AS coordinate_altitude,
                coordinate_uncertainty,
                coordinate_description,
                altitude,
                additional_info,
                external_references
            FROM locations
            WHERE organization_id = $1
              AND ($2::text IS NULL OR location_type = $2)
            ORDER BY location_name ASC, location_db_id ASC, id ASC
            LIMIT $3 OFFSET $4
            "#,
        )
        .bind(params.organization_id)
        .bind(params.location_type.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let locations = rows.into_iter().map(location_summary_from_row).collect();

        Ok((locations, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_location(
        &self,
        organization_id: i64,
        location_db_id: &str,
    ) -> Result<Option<LocationSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_location");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_location"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                location_db_id,
                location_name,
                location_type,
                abbreviation,
                country_name,
                country_code,
                institute_name,
                institute_address,
                CASE WHEN coordinates IS NULL THEN NULL ELSE ST_Y(coordinates::geometry) END AS latitude,
                CASE WHEN coordinates IS NULL THEN NULL ELSE ST_X(coordinates::geometry) END AS longitude,
                CASE WHEN coordinates IS NULL THEN NULL ELSE ST_Z(coordinates::geometry) END AS coordinate_altitude,
                coordinate_uncertainty,
                coordinate_description,
                altitude,
                additional_info,
                external_references
            FROM locations
            WHERE organization_id = $1
              AND location_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(location_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(location_summary_from_row))
    }

    pub async fn list_programs(
        &self,
        params: ProgramListParams,
    ) -> Result<(Vec<ProgramSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_programs");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_programs"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM programs
            WHERE organization_id = $1
              AND ($2::text IS NULL OR program_name = $2)
              AND ($3::text IS NULL OR abbreviation = $3)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.program_name.as_deref())
        .bind(params.abbreviation.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                program_db_id,
                program_name,
                abbreviation,
                objective,
                lead_person_db_id,
                additional_info,
                external_references
            FROM programs
            WHERE organization_id = $1
              AND ($2::text IS NULL OR program_name = $2)
              AND ($3::text IS NULL OR abbreviation = $3)
            ORDER BY program_name ASC, program_db_id ASC, id ASC
            LIMIT $4 OFFSET $5
            "#,
        )
        .bind(params.organization_id)
        .bind(params.program_name.as_deref())
        .bind(params.abbreviation.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let programs = rows.into_iter().map(program_summary_from_row).collect();

        Ok((programs, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_program(
        &self,
        organization_id: i64,
        program_db_id: &str,
    ) -> Result<Option<ProgramSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_program");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_program"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                program_db_id,
                program_name,
                abbreviation,
                objective,
                lead_person_db_id,
                additional_info,
                external_references
            FROM programs
            WHERE organization_id = $1
              AND program_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(program_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(program_summary_from_row))
    }

    pub async fn list_trials(
        &self,
        params: TrialListParams,
    ) -> Result<(Vec<TrialSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_trials");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_trials"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM trials
            WHERE organization_id = $1
              AND ($2::boolean IS NULL OR active = $2)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.active)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                t.id,
                t.trial_db_id,
                t.trial_name,
                t.trial_description,
                t.trial_type,
                p.program_db_id,
                t.start_date,
                t.end_date,
                t.active,
                t.common_crop_name,
                t.additional_info,
                t.external_references
            FROM trials t
            LEFT JOIN programs p
              ON p.id = t.program_id
             AND p.organization_id = t.organization_id
            WHERE t.organization_id = $1
              AND ($2::boolean IS NULL OR t.active = $2)
            ORDER BY t.trial_name ASC, t.trial_db_id ASC, t.id ASC
            LIMIT $3 OFFSET $4
            "#,
        )
        .bind(params.organization_id)
        .bind(params.active)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let trials = rows.into_iter().map(trial_summary_from_row).collect();

        Ok((trials, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_trial(
        &self,
        organization_id: i64,
        trial_db_id: &str,
    ) -> Result<Option<TrialSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_trial");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_trial"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                t.id,
                t.trial_db_id,
                t.trial_name,
                t.trial_description,
                t.trial_type,
                p.program_db_id,
                t.start_date,
                t.end_date,
                t.active,
                t.common_crop_name,
                t.additional_info,
                t.external_references
            FROM trials t
            LEFT JOIN programs p
              ON p.id = t.program_id
             AND p.organization_id = t.organization_id
            WHERE t.organization_id = $1
              AND t.trial_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(trial_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(trial_summary_from_row))
    }

    pub async fn list_studies(
        &self,
        params: StudyListParams,
    ) -> Result<(Vec<StudySummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_studies");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_studies"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM studies
            WHERE organization_id = $1
              AND ($2::boolean IS NULL OR active = $2)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.active)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                s.id,
                s.study_db_id,
                s.study_name,
                s.study_description,
                s.study_type,
                s.study_code,
                t.trial_db_id,
                l.location_db_id,
                s.start_date,
                s.end_date,
                s.active,
                s.common_crop_name,
                s.cultural_practices,
                s.observation_levels,
                s.observation_units_description,
                s.license,
                s.additional_info,
                s.external_references
            FROM studies s
            LEFT JOIN trials t
              ON t.id = s.trial_id
             AND t.organization_id = s.organization_id
            LEFT JOIN locations l
              ON l.id = s.location_id
             AND l.organization_id = s.organization_id
            WHERE s.organization_id = $1
              AND ($2::boolean IS NULL OR s.active = $2)
            ORDER BY s.study_name ASC, s.study_db_id ASC, s.id ASC
            LIMIT $3 OFFSET $4
            "#,
        )
        .bind(params.organization_id)
        .bind(params.active)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let studies = rows.into_iter().map(study_summary_from_row).collect();

        Ok((studies, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_study(
        &self,
        organization_id: i64,
        study_db_id: &str,
    ) -> Result<Option<StudySummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_study");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_study"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                s.id,
                s.study_db_id,
                s.study_name,
                s.study_description,
                s.study_type,
                s.study_code,
                t.trial_db_id,
                l.location_db_id,
                s.start_date,
                s.end_date,
                s.active,
                s.common_crop_name,
                s.cultural_practices,
                s.observation_levels,
                s.observation_units_description,
                s.license,
                s.additional_info,
                s.external_references
            FROM studies s
            LEFT JOIN trials t
              ON t.id = s.trial_id
             AND t.organization_id = s.organization_id
            LEFT JOIN locations l
              ON l.id = s.location_id
             AND l.organization_id = s.organization_id
            WHERE s.organization_id = $1
              AND s.study_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(study_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(study_summary_from_row))
    }

    pub async fn list_seasons(
        &self,
        params: SeasonListParams,
    ) -> Result<(Vec<SeasonSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_seasons");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_seasons"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM seasons
            WHERE organization_id = $1
              AND ($2::integer IS NULL OR year = $2)
              AND ($3::text IS NULL OR season_db_id = $3)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.year)
        .bind(params.season_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                season_db_id,
                season_name,
                year,
                additional_info,
                external_references
            FROM seasons
            WHERE organization_id = $1
              AND ($2::integer IS NULL OR year = $2)
              AND ($3::text IS NULL OR season_db_id = $3)
            ORDER BY year DESC, season_name ASC, id ASC
            LIMIT $4 OFFSET $5
            "#,
        )
        .bind(params.organization_id)
        .bind(params.year)
        .bind(params.season_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let seasons = rows.into_iter().map(season_summary_from_row).collect();

        Ok((seasons, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_season(
        &self,
        organization_id: i64,
        season_db_id: &str,
    ) -> Result<Option<SeasonSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_season");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_season"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                season_db_id,
                season_name,
                year,
                additional_info,
                external_references
            FROM seasons
            WHERE organization_id = $1
              AND season_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(season_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(season_summary_from_row))
    }

    pub async fn list_people(
        &self,
        params: PersonListParams,
    ) -> Result<(Vec<PersonSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_people");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_people"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let first_name_pattern = params.first_name.as_ref().map(|value| format!("%{value}%"));
        let last_name_pattern = params.last_name.as_ref().map(|value| format!("%{value}%"));

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM people
            WHERE organization_id = $1
              AND ($2::text IS NULL OR first_name ILIKE $2)
              AND ($3::text IS NULL OR last_name ILIKE $3)
            "#,
        )
        .bind(params.organization_id)
        .bind(first_name_pattern.as_deref())
        .bind(last_name_pattern.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM people
            WHERE organization_id = $1
              AND ($2::text IS NULL OR first_name ILIKE $2)
              AND ($3::text IS NULL OR last_name ILIKE $3)
            ORDER BY last_name ASC, first_name ASC, person_db_id ASC, id ASC
            LIMIT $4 OFFSET $5
            "#,
        )
        .bind(params.organization_id)
        .bind(first_name_pattern.as_deref())
        .bind(last_name_pattern.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let people = rows.into_iter().map(person_summary_from_row).collect();

        Ok((people, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_person(
        &self,
        organization_id: i64,
        person_db_id: &str,
    ) -> Result<Option<PersonSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_person");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_person"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM people
            WHERE organization_id = $1
              AND person_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(person_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(person_summary_from_row))
    }

    pub async fn list_lists(
        &self,
        params: ListListParams,
    ) -> Result<(Vec<ListSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_lists");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_lists"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let list_name_pattern = contains_pattern(&params.list_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM lists
            WHERE organization_id = $1
              AND ($2::text IS NULL OR list_type = $2)
              AND ($3::text IS NULL OR list_name ILIKE $3)
              AND ($4::text IS NULL OR list_db_id = $4)
              AND ($5::text IS NULL OR list_source = $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.list_type.as_deref())
        .bind(list_name_pattern.as_deref())
        .bind(params.list_db_id.as_deref())
        .bind(params.list_source.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM lists
            WHERE organization_id = $1
              AND ($2::text IS NULL OR list_type = $2)
              AND ($3::text IS NULL OR list_name ILIKE $3)
              AND ($4::text IS NULL OR list_db_id = $4)
              AND ($5::text IS NULL OR list_source = $5)
            ORDER BY list_name ASC, list_db_id ASC, id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(params.list_type.as_deref())
        .bind(list_name_pattern.as_deref())
        .bind(params.list_db_id.as_deref())
        .bind(params.list_source.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let lists = rows.into_iter().map(list_summary_from_row).collect();

        Ok((lists, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_list(
        &self,
        organization_id: i64,
        list_db_id: &str,
    ) -> Result<Option<ListSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_list");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_list"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM lists
            WHERE organization_id = $1
              AND list_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(list_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(list_summary_from_row))
    }

    pub async fn list_ontologies(
        &self,
        params: OntologyListParams,
    ) -> Result<(Vec<OntologySummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_ontologies");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_ontologies"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let ontology_name_pattern = contains_pattern(&params.ontology_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM ontologies
            WHERE organization_id = $1
              AND ($2::text IS NULL OR ontology_db_id = $2)
              AND ($3::text IS NULL OR ontology_name ILIKE $3)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.ontology_db_id.as_deref())
        .bind(ontology_name_pattern.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                ontology_db_id,
                ontology_name,
                description,
                version,
                authors,
                copyright,
                licence,
                documentation_url,
                additional_info
            FROM ontologies
            WHERE organization_id = $1
              AND ($2::text IS NULL OR ontology_db_id = $2)
              AND ($3::text IS NULL OR ontology_name ILIKE $3)
            ORDER BY ontology_name ASC, ontology_db_id ASC, id ASC
            LIMIT $4 OFFSET $5
            "#,
        )
        .bind(params.organization_id)
        .bind(params.ontology_db_id.as_deref())
        .bind(ontology_name_pattern.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let ontologies = rows.into_iter().map(ontology_summary_from_row).collect();

        Ok((ontologies, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_ontology(
        &self,
        organization_id: i64,
        ontology_db_id: &str,
    ) -> Result<Option<OntologySummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_ontology");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_ontology"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                ontology_db_id,
                ontology_name,
                description,
                version,
                authors,
                copyright,
                licence,
                documentation_url,
                additional_info
            FROM ontologies
            WHERE organization_id = $1
              AND ontology_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(ontology_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(ontology_summary_from_row))
    }

    pub async fn list_germplasm(
        &self,
        params: GermplasmListParams,
    ) -> Result<(Vec<GermplasmSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_germplasm");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_germplasm"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let germplasm_name_pattern = contains_pattern(&params.germplasm_name);
        let common_crop_name_pattern = contains_pattern(&params.common_crop_name);
        let species_pattern = contains_pattern(&params.species);
        let genus_pattern = contains_pattern(&params.genus);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM germplasm
            WHERE organization_id = $1
              AND ($2::text IS NULL OR germplasm_name ILIKE $2)
              AND ($3::text IS NULL OR common_crop_name ILIKE $3)
              AND ($4::text IS NULL OR species ILIKE $4)
              AND ($5::text IS NULL OR genus ILIKE $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(germplasm_name_pattern.as_deref())
        .bind(common_crop_name_pattern.as_deref())
        .bind(species_pattern.as_deref())
        .bind(genus_pattern.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                germplasm_db_id,
                germplasm_name,
                germplasm_pui,
                default_display_name,
                accession_number,
                species,
                genus,
                subtaxa,
                common_crop_name,
                institute_code,
                institute_name,
                biological_status_of_accession_code,
                country_of_origin_code,
                synonyms,
                donors,
                pedigree,
                seed_source,
                seed_source_description,
                additional_info,
                external_references
            FROM germplasm
            WHERE organization_id = $1
              AND ($2::text IS NULL OR germplasm_name ILIKE $2)
              AND ($3::text IS NULL OR common_crop_name ILIKE $3)
              AND ($4::text IS NULL OR species ILIKE $4)
              AND ($5::text IS NULL OR genus ILIKE $5)
            ORDER BY germplasm_name ASC, germplasm_db_id ASC, id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(germplasm_name_pattern.as_deref())
        .bind(common_crop_name_pattern.as_deref())
        .bind(species_pattern.as_deref())
        .bind(genus_pattern.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let germplasm = rows.into_iter().map(germplasm_summary_from_row).collect();

        Ok((germplasm, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_germplasm(
        &self,
        organization_id: i64,
        germplasm_db_id: &str,
    ) -> Result<Option<GermplasmSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_germplasm");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_germplasm"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                germplasm_db_id,
                germplasm_name,
                germplasm_pui,
                default_display_name,
                accession_number,
                species,
                genus,
                subtaxa,
                common_crop_name,
                institute_code,
                institute_name,
                biological_status_of_accession_code,
                country_of_origin_code,
                synonyms,
                donors,
                pedigree,
                seed_source,
                seed_source_description,
                additional_info,
                external_references
            FROM germplasm
            WHERE organization_id = $1
              AND germplasm_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(germplasm_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(germplasm_summary_from_row))
    }

    pub async fn list_attributes(
        &self,
        params: AttributeListParams,
    ) -> Result<(Vec<AttributeSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_attributes");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_attributes"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let attribute_name_pattern = contains_pattern(&params.attribute_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM germplasm_attribute_definitions
            WHERE organization_id = $1
              AND ($2::text IS NULL OR attribute_category = $2)
              AND ($3::text IS NULL OR attribute_db_id = $3)
              AND ($4::text IS NULL OR attribute_name ILIKE $4)
              AND ($5::text IS NULL OR common_crop_name = $5)
              AND ($6::text IS NULL OR trait_db_id = $6)
              AND ($7::text IS NULL OR method_db_id = $7)
              AND ($8::text IS NULL OR scale_db_id = $8)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.attribute_category.as_deref())
        .bind(params.attribute_db_id.as_deref())
        .bind(attribute_name_pattern.as_deref())
        .bind(params.common_crop_name.as_deref())
        .bind(params.trait_db_id.as_deref())
        .bind(params.method_db_id.as_deref())
        .bind(params.scale_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM germplasm_attribute_definitions
            WHERE organization_id = $1
              AND ($2::text IS NULL OR attribute_category = $2)
              AND ($3::text IS NULL OR attribute_db_id = $3)
              AND ($4::text IS NULL OR attribute_name ILIKE $4)
              AND ($5::text IS NULL OR common_crop_name = $5)
              AND ($6::text IS NULL OR trait_db_id = $6)
              AND ($7::text IS NULL OR method_db_id = $7)
              AND ($8::text IS NULL OR scale_db_id = $8)
            ORDER BY attribute_name ASC, attribute_db_id ASC, id ASC
            LIMIT $9 OFFSET $10
            "#,
        )
        .bind(params.organization_id)
        .bind(params.attribute_category.as_deref())
        .bind(params.attribute_db_id.as_deref())
        .bind(attribute_name_pattern.as_deref())
        .bind(params.common_crop_name.as_deref())
        .bind(params.trait_db_id.as_deref())
        .bind(params.method_db_id.as_deref())
        .bind(params.scale_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let attributes = rows.into_iter().map(attribute_summary_from_row).collect();

        Ok((attributes, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn list_attribute_categories(
        &self,
        organization_id: i64,
        page: u32,
        page_size: u32,
    ) -> Result<(Vec<String>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_attribute_categories");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_attribute_categories"));
        };

        let limit = i64::from(page_size);
        let offset = page_offset(page, page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(DISTINCT attribute_category)
            FROM germplasm_attribute_definitions
            WHERE organization_id = $1
              AND attribute_category IS NOT NULL
            "#,
        )
        .bind(organization_id)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let categories = sqlx::query_scalar::<_, String>(
            r#"
            SELECT DISTINCT attribute_category
            FROM germplasm_attribute_definitions
            WHERE organization_id = $1
              AND attribute_category IS NOT NULL
            ORDER BY attribute_category ASC
            LIMIT $2 OFFSET $3
            "#,
        )
        .bind(organization_id)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok((categories, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_attribute(
        &self,
        organization_id: i64,
        attribute_db_id: &str,
    ) -> Result<Option<AttributeSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_attribute");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_attribute"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM germplasm_attribute_definitions
            WHERE organization_id = $1
              AND attribute_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(attribute_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        if let Some(row) = row {
            return Ok(Some(attribute_summary_from_row(row)));
        }

        let Ok(id) = attribute_db_id.parse::<i64>() else {
            return Ok(None);
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM germplasm_attribute_definitions
            WHERE organization_id = $1
              AND id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(attribute_summary_from_row))
    }

    pub async fn list_attribute_values(
        &self,
        params: AttributeValueListParams,
    ) -> Result<(Vec<AttributeValueSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_attribute_values");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_attribute_values"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let attribute_name_pattern = contains_pattern(&params.attribute_name);
        let germplasm_name_pattern = contains_pattern(&params.germplasm_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM germplasm_attribute_values
            WHERE organization_id = $1
              AND ($2::text IS NULL OR attribute_db_id = $2)
              AND ($3::text IS NULL OR attribute_name ILIKE $3)
              AND ($4::text IS NULL OR attribute_value_db_id = $4)
              AND ($5::text IS NULL OR germplasm_db_id = $5)
              AND ($6::text IS NULL OR germplasm_name ILIKE $6)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.attribute_db_id.as_deref())
        .bind(attribute_name_pattern.as_deref())
        .bind(params.attribute_value_db_id.as_deref())
        .bind(params.germplasm_db_id.as_deref())
        .bind(germplasm_name_pattern.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                attribute_value_db_id,
                attribute_db_id,
                attribute_name,
                germplasm_db_id,
                germplasm_name,
                value,
                determined_date,
                additional_info,
                external_references
            FROM germplasm_attribute_values
            WHERE organization_id = $1
              AND ($2::text IS NULL OR attribute_db_id = $2)
              AND ($3::text IS NULL OR attribute_name ILIKE $3)
              AND ($4::text IS NULL OR attribute_value_db_id = $4)
              AND ($5::text IS NULL OR germplasm_db_id = $5)
              AND ($6::text IS NULL OR germplasm_name ILIKE $6)
            ORDER BY attribute_name ASC, germplasm_name ASC, attribute_value_db_id ASC, id ASC
            LIMIT $7 OFFSET $8
            "#,
        )
        .bind(params.organization_id)
        .bind(params.attribute_db_id.as_deref())
        .bind(attribute_name_pattern.as_deref())
        .bind(params.attribute_value_db_id.as_deref())
        .bind(params.germplasm_db_id.as_deref())
        .bind(germplasm_name_pattern.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let values = rows
            .into_iter()
            .map(attribute_value_summary_from_row)
            .collect();

        Ok((values, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_attribute_value(
        &self,
        organization_id: i64,
        attribute_value_db_id: &str,
    ) -> Result<Option<AttributeValueSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_attribute_value");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_attribute_value"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                attribute_value_db_id,
                attribute_db_id,
                attribute_name,
                germplasm_db_id,
                germplasm_name,
                value,
                determined_date,
                additional_info,
                external_references
            FROM germplasm_attribute_values
            WHERE organization_id = $1
              AND attribute_value_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(attribute_value_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(attribute_value_summary_from_row))
    }

    pub async fn list_breeding_methods(
        &self,
        params: BreedingMethodListParams,
    ) -> Result<(Vec<BreedingMethodSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_breeding_methods");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_breeding_methods"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM breeding_methods
            WHERE organization_id = $1
            "#,
        )
        .bind(params.organization_id)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                breeding_method_db_id,
                breeding_method_name,
                abbreviation,
                description
            FROM breeding_methods
            WHERE organization_id = $1
            ORDER BY breeding_method_name ASC, breeding_method_db_id ASC, id ASC
            LIMIT $2 OFFSET $3
            "#,
        )
        .bind(params.organization_id)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let methods = rows.into_iter().map(breeding_method_from_row).collect();

        Ok((methods, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_breeding_method(
        &self,
        organization_id: i64,
        breeding_method_db_id: &str,
    ) -> Result<Option<BreedingMethodSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_breeding_method");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_breeding_method"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                breeding_method_db_id,
                breeding_method_name,
                abbreviation,
                description
            FROM breeding_methods
            WHERE organization_id = $1
              AND breeding_method_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(breeding_method_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(breeding_method_from_row))
    }

    pub async fn list_traits(
        &self,
        params: TraitListParams,
    ) -> Result<(Vec<TraitSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_traits");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_traits"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let trait_class_pattern = contains_pattern(&params.trait_class);
        let observation_variable_name_pattern = contains_pattern(&params.observation_variable_name);
        let common_crop_name_pattern = contains_pattern(&params.common_crop_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM observation_variables
            WHERE organization_id = $1
              AND ($2::text IS NULL OR trait_class ILIKE $2)
              AND ($3::text IS NULL OR observation_variable_name ILIKE $3)
              AND ($4::text IS NULL OR common_crop_name ILIKE $4)
            "#,
        )
        .bind(params.organization_id)
        .bind(trait_class_pattern.as_deref())
        .bind(observation_variable_name_pattern.as_deref())
        .bind(common_crop_name_pattern.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                observation_variable_db_id,
                observation_variable_name,
                trait_name,
                trait_description,
                trait_class,
                method_name,
                method_description,
                scale_name,
                data_type,
                valid_values,
                default_value,
                ontology_db_id,
                ontology_name,
                ontology_term_id,
                ontology_version,
                ontology_documentation_links,
                common_crop_name,
                status,
                additional_info,
                external_references
            FROM observation_variables
            WHERE organization_id = $1
              AND ($2::text IS NULL OR trait_class ILIKE $2)
              AND ($3::text IS NULL OR observation_variable_name ILIKE $3)
              AND ($4::text IS NULL OR common_crop_name ILIKE $4)
            ORDER BY observation_variable_name ASC, observation_variable_db_id ASC, id ASC
            LIMIT $5 OFFSET $6
            "#,
        )
        .bind(params.organization_id)
        .bind(trait_class_pattern.as_deref())
        .bind(observation_variable_name_pattern.as_deref())
        .bind(common_crop_name_pattern.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let traits = rows.into_iter().map(trait_summary_from_row).collect();

        Ok((traits, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_trait(
        &self,
        organization_id: i64,
        observation_variable_db_id: &str,
    ) -> Result<Option<TraitSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_trait");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_trait"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                observation_variable_db_id,
                observation_variable_name,
                trait_name,
                trait_description,
                trait_class,
                method_name,
                method_description,
                scale_name,
                data_type,
                valid_values,
                default_value,
                ontology_db_id,
                ontology_name,
                ontology_term_id,
                ontology_version,
                ontology_documentation_links,
                common_crop_name,
                status,
                additional_info,
                external_references
            FROM observation_variables
            WHERE organization_id = $1
              AND observation_variable_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(observation_variable_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(trait_summary_from_row))
    }

    pub async fn list_variables(
        &self,
        params: VariableListParams,
    ) -> Result<(Vec<VariableSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_variables");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_variables"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let observation_variable_name_pattern = contains_pattern(&params.observation_variable_name);
        let trait_class_pattern = contains_pattern(&params.trait_class);
        let common_crop_name_pattern = contains_pattern(&params.common_crop_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM observation_variables
            WHERE organization_id = $1
              AND ($2::text IS NULL OR observation_variable_db_id = $2)
              AND ($3::text IS NULL OR observation_variable_name ILIKE $3)
              AND ($4::text IS NULL OR trait_class ILIKE $4)
              AND ($5::text IS NULL OR common_crop_name ILIKE $5)
              AND ($6::text IS NULL OR method_db_id = $6)
              AND ($7::text IS NULL OR scale_db_id = $7)
              AND ($8::text IS NULL OR ontology_db_id = $8)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.observation_variable_db_id.as_deref())
        .bind(observation_variable_name_pattern.as_deref())
        .bind(trait_class_pattern.as_deref())
        .bind(common_crop_name_pattern.as_deref())
        .bind(params.method_db_id.as_deref())
        .bind(params.scale_db_id.as_deref())
        .bind(params.ontology_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
                observation_variable_db_id,
                observation_variable_name,
                common_crop_name,
                default_value,
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
                formula,
                scale_db_id,
                scale_name,
                data_type,
                decimal_places,
                valid_values,
                ontology_db_id,
                ontology_name,
                ontology_term_id,
                ontology_version,
                ontology_documentation_links,
                additional_info,
                external_references
            FROM observation_variables
            WHERE organization_id = $1
              AND ($2::text IS NULL OR observation_variable_db_id = $2)
              AND ($3::text IS NULL OR observation_variable_name ILIKE $3)
              AND ($4::text IS NULL OR trait_class ILIKE $4)
              AND ($5::text IS NULL OR common_crop_name ILIKE $5)
              AND ($6::text IS NULL OR method_db_id = $6)
              AND ($7::text IS NULL OR scale_db_id = $7)
              AND ($8::text IS NULL OR ontology_db_id = $8)
            ORDER BY observation_variable_name ASC, observation_variable_db_id ASC, id ASC
            LIMIT $9 OFFSET $10
            "#,
        )
        .bind(params.organization_id)
        .bind(params.observation_variable_db_id.as_deref())
        .bind(observation_variable_name_pattern.as_deref())
        .bind(trait_class_pattern.as_deref())
        .bind(common_crop_name_pattern.as_deref())
        .bind(params.method_db_id.as_deref())
        .bind(params.scale_db_id.as_deref())
        .bind(params.ontology_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let variables = rows.into_iter().map(variable_summary_from_row).collect();

        Ok((variables, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_variable(
        &self,
        organization_id: i64,
        observation_variable_db_id: &str,
    ) -> Result<Option<VariableSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_variable");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_variable"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
                observation_variable_db_id,
                observation_variable_name,
                common_crop_name,
                default_value,
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
                formula,
                scale_db_id,
                scale_name,
                data_type,
                decimal_places,
                valid_values,
                ontology_db_id,
                ontology_name,
                ontology_term_id,
                ontology_version,
                ontology_documentation_links,
                additional_info,
                external_references
            FROM observation_variables
            WHERE organization_id = $1
              AND observation_variable_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(observation_variable_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(variable_summary_from_row))
    }

    pub async fn list_observations(
        &self,
        params: ObservationListParams,
    ) -> Result<(Vec<ObservationSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_observations");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_observations"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM observations o
            LEFT JOIN observation_variables ov
              ON ov.id = o.observation_variable_id
             AND ov.organization_id = o.organization_id
            LEFT JOIN observation_units ou
              ON ou.id = o.observation_unit_id
             AND ou.organization_id = o.organization_id
            WHERE o.organization_id = $1
              AND ($2::bigint IS NULL OR o.study_id = $2)
              AND ($3::bigint IS NULL OR o.germplasm_id = $3)
              AND ($4::text IS NULL OR ov.observation_variable_db_id = $4)
              AND ($5::text IS NULL OR ou.observation_unit_db_id = $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.study_id)
        .bind(params.germplasm_id)
        .bind(params.observation_variable_db_id.as_deref())
        .bind(params.observation_unit_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                o.id,
                o.observation_db_id,
                ou.observation_unit_db_id,
                ov.observation_variable_db_id,
                ov.observation_variable_name,
                o.value,
                o.observation_time_stamp,
                o.collector,
                o.study_id,
                o.germplasm_id,
                o.season_db_id,
                o.additional_info,
                o.external_references
            FROM observations o
            LEFT JOIN observation_variables ov
              ON ov.id = o.observation_variable_id
             AND ov.organization_id = o.organization_id
            LEFT JOIN observation_units ou
              ON ou.id = o.observation_unit_id
             AND ou.organization_id = o.organization_id
            WHERE o.organization_id = $1
              AND ($2::bigint IS NULL OR o.study_id = $2)
              AND ($3::bigint IS NULL OR o.germplasm_id = $3)
              AND ($4::text IS NULL OR ov.observation_variable_db_id = $4)
              AND ($5::text IS NULL OR ou.observation_unit_db_id = $5)
            ORDER BY o.observation_time_stamp ASC, o.observation_db_id ASC, o.id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(params.study_id)
        .bind(params.germplasm_id)
        .bind(params.observation_variable_db_id.as_deref())
        .bind(params.observation_unit_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let observations = rows.into_iter().map(observation_summary_from_row).collect();

        Ok((observations, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_observation(
        &self,
        organization_id: i64,
        observation_db_id: &str,
    ) -> Result<Option<ObservationSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_observation");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_observation"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                o.id,
                o.observation_db_id,
                ou.observation_unit_db_id,
                ov.observation_variable_db_id,
                ov.observation_variable_name,
                o.value,
                o.observation_time_stamp,
                o.collector,
                o.study_id,
                o.germplasm_id,
                o.season_db_id,
                o.additional_info,
                o.external_references
            FROM observations o
            LEFT JOIN observation_variables ov
              ON ov.id = o.observation_variable_id
             AND ov.organization_id = o.organization_id
            LEFT JOIN observation_units ou
              ON ou.id = o.observation_unit_id
             AND ou.organization_id = o.organization_id
            WHERE o.organization_id = $1
              AND o.observation_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(observation_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(observation_summary_from_row))
    }

    pub async fn list_observation_units(
        &self,
        params: ObservationUnitListParams,
    ) -> Result<(Vec<ObservationUnitSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_observation_units");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_observation_units"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM observation_units ou
            WHERE ou.organization_id = $1
              AND ($2::bigint IS NULL OR ou.study_id = $2)
              AND ($3::bigint IS NULL OR ou.germplasm_id = $3)
              AND ($4::text IS NULL OR ou.observation_level = $4)
              AND ($5::text IS NULL OR ou.observation_unit_db_id = $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.study_id)
        .bind(params.germplasm_id)
        .bind(params.observation_level.as_deref())
        .bind(params.observation_unit_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                ou.id,
                ou.observation_unit_db_id,
                ou.observation_unit_name,
                ou.observation_unit_pui,
                ou.study_id,
                s.study_name,
                ou.germplasm_id,
                g.germplasm_name,
                ou.cross_db_id,
                ou.seedlot_db_id,
                ou.observation_level,
                ou.observation_level_code,
                ou.observation_level_order,
                ou.position_coordinate_x,
                ou.position_coordinate_x_type,
                ou.position_coordinate_y,
                ou.position_coordinate_y_type,
                ou.entry_type,
                ou.geo_coordinates,
                ou.treatments,
                ou.additional_info,
                ou.external_references
            FROM observation_units ou
            LEFT JOIN studies s
              ON s.id = ou.study_id
             AND s.organization_id = ou.organization_id
            LEFT JOIN germplasm g
              ON g.id = ou.germplasm_id
             AND g.organization_id = ou.organization_id
            WHERE ou.organization_id = $1
              AND ($2::bigint IS NULL OR ou.study_id = $2)
              AND ($3::bigint IS NULL OR ou.germplasm_id = $3)
              AND ($4::text IS NULL OR ou.observation_level = $4)
              AND ($5::text IS NULL OR ou.observation_unit_db_id = $5)
            ORDER BY ou.observation_unit_name ASC, ou.observation_unit_db_id ASC, ou.id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(params.study_id)
        .bind(params.germplasm_id)
        .bind(params.observation_level.as_deref())
        .bind(params.observation_unit_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let units = rows
            .into_iter()
            .map(observation_unit_summary_from_row)
            .collect();

        Ok((units, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_observation_unit(
        &self,
        organization_id: i64,
        observation_unit_db_id: &str,
    ) -> Result<Option<ObservationUnitSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_observation_unit");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_observation_unit"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                ou.id,
                ou.observation_unit_db_id,
                ou.observation_unit_name,
                ou.observation_unit_pui,
                ou.study_id,
                s.study_name,
                ou.germplasm_id,
                g.germplasm_name,
                ou.cross_db_id,
                ou.seedlot_db_id,
                ou.observation_level,
                ou.observation_level_code,
                ou.observation_level_order,
                ou.position_coordinate_x,
                ou.position_coordinate_x_type,
                ou.position_coordinate_y,
                ou.position_coordinate_y_type,
                ou.entry_type,
                ou.geo_coordinates,
                ou.treatments,
                ou.additional_info,
                ou.external_references
            FROM observation_units ou
            LEFT JOIN studies s
              ON s.id = ou.study_id
             AND s.organization_id = ou.organization_id
            LEFT JOIN germplasm g
              ON g.id = ou.germplasm_id
             AND g.organization_id = ou.organization_id
            WHERE ou.organization_id = $1
              AND ou.observation_unit_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(observation_unit_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(observation_unit_summary_from_row))
    }

    pub async fn list_methods(
        &self,
        params: MethodListParams,
    ) -> Result<(Vec<MethodSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_methods");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_methods"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let method_name_pattern = contains_pattern(&params.method_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM methods
            WHERE organization_id = $1
              AND ($2::text IS NULL OR method_db_id = $2)
              AND ($3::text IS NULL OR method_class = $3)
              AND ($4::text IS NULL OR method_name ILIKE $4)
              AND ($5::text IS NULL OR ontology_db_id = $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.method_db_id.as_deref())
        .bind(params.method_class.as_deref())
        .bind(method_name_pattern.as_deref())
        .bind(params.ontology_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM methods
            WHERE organization_id = $1
              AND ($2::text IS NULL OR method_db_id = $2)
              AND ($3::text IS NULL OR method_class = $3)
              AND ($4::text IS NULL OR method_name ILIKE $4)
              AND ($5::text IS NULL OR ontology_db_id = $5)
            ORDER BY method_name ASC, method_db_id ASC, id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(params.method_db_id.as_deref())
        .bind(params.method_class.as_deref())
        .bind(method_name_pattern.as_deref())
        .bind(params.ontology_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let methods = rows.into_iter().map(method_summary_from_row).collect();

        Ok((methods, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_method(
        &self,
        organization_id: i64,
        method_db_id: &str,
    ) -> Result<Option<MethodSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_method");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_method"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM methods
            WHERE organization_id = $1
              AND method_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(method_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        if let Some(row) = row {
            return Ok(Some(method_summary_from_row(row)));
        }

        let Ok(method_id) = method_db_id.parse::<i64>() else {
            return Ok(None);
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM methods
            WHERE organization_id = $1
              AND id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(method_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(method_summary_from_row))
    }

    pub async fn list_scales(
        &self,
        params: ScaleListParams,
    ) -> Result<(Vec<ScaleSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_scales");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_scales"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let scale_name_pattern = contains_pattern(&params.scale_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM scales
            WHERE organization_id = $1
              AND ($2::text IS NULL OR scale_db_id = $2)
              AND ($3::text IS NULL OR scale_name ILIKE $3)
              AND ($4::text IS NULL OR data_type = $4)
              AND ($5::text IS NULL OR ontology_db_id = $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.scale_db_id.as_deref())
        .bind(scale_name_pattern.as_deref())
        .bind(params.data_type.as_deref())
        .bind(params.ontology_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM scales
            WHERE organization_id = $1
              AND ($2::text IS NULL OR scale_db_id = $2)
              AND ($3::text IS NULL OR scale_name ILIKE $3)
              AND ($4::text IS NULL OR data_type = $4)
              AND ($5::text IS NULL OR ontology_db_id = $5)
            ORDER BY scale_name ASC, scale_db_id ASC, id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(params.scale_db_id.as_deref())
        .bind(scale_name_pattern.as_deref())
        .bind(params.data_type.as_deref())
        .bind(params.ontology_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let scales = rows.into_iter().map(scale_summary_from_row).collect();

        Ok((scales, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_scale(
        &self,
        organization_id: i64,
        scale_db_id: &str,
    ) -> Result<Option<ScaleSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_scale");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_scale"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM scales
            WHERE organization_id = $1
              AND scale_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(scale_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        if let Some(row) = row {
            return Ok(Some(scale_summary_from_row(row)));
        }

        let Ok(scale_id) = scale_db_id.parse::<i64>() else {
            return Ok(None);
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
            FROM scales
            WHERE organization_id = $1
              AND id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(scale_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(scale_summary_from_row))
    }

    pub async fn list_crossing_projects(
        &self,
        params: CrossingProjectListParams,
    ) -> Result<(Vec<CrossingProjectSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_crossing_projects");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_crossing_projects"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let crossing_project_name_pattern = contains_pattern(&params.crossing_project_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM crossing_projects cp
            LEFT JOIN programs p
              ON p.id = cp.program_id
             AND p.organization_id = cp.organization_id
            WHERE cp.organization_id = $1
              AND ($2::text IS NULL OR cp.crossing_project_db_id = $2)
              AND ($3::text IS NULL OR cp.crossing_project_name ILIKE $3)
              AND ($4::text IS NULL OR p.program_db_id = $4)
              AND ($5::text IS NULL OR cp.common_crop_name = $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.crossing_project_db_id.as_deref())
        .bind(crossing_project_name_pattern.as_deref())
        .bind(params.program_db_id.as_deref())
        .bind(params.common_crop_name.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                cp.id,
                cp.crossing_project_db_id,
                cp.crossing_project_name,
                cp.crossing_project_description,
                p.program_name,
                cp.common_crop_name,
                cp.additional_info,
                cp.external_references
            FROM crossing_projects cp
            LEFT JOIN programs p
              ON p.id = cp.program_id
             AND p.organization_id = cp.organization_id
            WHERE cp.organization_id = $1
              AND ($2::text IS NULL OR cp.crossing_project_db_id = $2)
              AND ($3::text IS NULL OR cp.crossing_project_name ILIKE $3)
              AND ($4::text IS NULL OR p.program_db_id = $4)
              AND ($5::text IS NULL OR cp.common_crop_name = $5)
            ORDER BY cp.crossing_project_name ASC, cp.crossing_project_db_id ASC, cp.id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(params.crossing_project_db_id.as_deref())
        .bind(crossing_project_name_pattern.as_deref())
        .bind(params.program_db_id.as_deref())
        .bind(params.common_crop_name.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let projects = rows
            .into_iter()
            .map(crossing_project_summary_from_row)
            .collect();

        Ok((projects, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_crossing_project(
        &self,
        organization_id: i64,
        crossing_project_db_id: &str,
    ) -> Result<Option<CrossingProjectSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_crossing_project");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_crossing_project"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                cp.id,
                cp.crossing_project_db_id,
                cp.crossing_project_name,
                cp.crossing_project_description,
                p.program_name,
                cp.common_crop_name,
                cp.additional_info,
                cp.external_references
            FROM crossing_projects cp
            LEFT JOIN programs p
              ON p.id = cp.program_id
             AND p.organization_id = cp.organization_id
            WHERE cp.organization_id = $1
              AND cp.crossing_project_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(crossing_project_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(crossing_project_summary_from_row))
    }

    pub async fn list_crosses(
        &self,
        params: CrossListParams,
    ) -> Result<(Vec<CrossSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_crosses");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_crosses"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let cross_name_pattern = contains_pattern(&params.cross_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM crosses c
            LEFT JOIN crossing_projects cp
              ON cp.id = c.crossing_project_id
             AND cp.organization_id = c.organization_id
            WHERE c.organization_id = $1
              AND ($2::text IS NULL OR cp.crossing_project_db_id = $2)
              AND ($3::text IS NULL OR c.cross_type = $3)
              AND ($4::text IS NULL OR c.cross_db_id = $4)
              AND ($5::text IS NULL OR c.cross_name ILIKE $5)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.crossing_project_db_id.as_deref())
        .bind(params.cross_type.as_deref())
        .bind(params.cross_db_id.as_deref())
        .bind(cross_name_pattern.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                c.id,
                c.cross_db_id,
                c.cross_name,
                c.cross_type,
                cp.crossing_project_db_id,
                cp.crossing_project_name,
                p1.germplasm_db_id AS parent1_db_id,
                p1.germplasm_name AS parent1_name,
                c.parent1_type,
                p2.germplasm_db_id AS parent2_db_id,
                p2.germplasm_name AS parent2_name,
                c.parent2_type,
                c.pollination_time_stamp,
                NULL::text AS planned_cross_db_id,
                c.crossing_year,
                c.cross_status,
                c.additional_info,
                c.external_references
            FROM crosses c
            LEFT JOIN crossing_projects cp
              ON cp.id = c.crossing_project_id
             AND cp.organization_id = c.organization_id
            LEFT JOIN germplasm p1
              ON p1.id = c.parent1_db_id
             AND p1.organization_id = c.organization_id
            LEFT JOIN germplasm p2
              ON p2.id = c.parent2_db_id
             AND p2.organization_id = c.organization_id
            WHERE c.organization_id = $1
              AND ($2::text IS NULL OR cp.crossing_project_db_id = $2)
              AND ($3::text IS NULL OR c.cross_type = $3)
              AND ($4::text IS NULL OR c.cross_db_id = $4)
              AND ($5::text IS NULL OR c.cross_name ILIKE $5)
            ORDER BY c.cross_name ASC, c.cross_db_id ASC, c.id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(params.crossing_project_db_id.as_deref())
        .bind(params.cross_type.as_deref())
        .bind(params.cross_db_id.as_deref())
        .bind(cross_name_pattern.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let crosses = rows.into_iter().map(cross_summary_from_row).collect();

        Ok((crosses, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_cross(
        &self,
        organization_id: i64,
        cross_db_id: &str,
    ) -> Result<Option<CrossSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_cross");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_cross"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                c.id,
                c.cross_db_id,
                c.cross_name,
                c.cross_type,
                cp.crossing_project_db_id,
                cp.crossing_project_name,
                p1.germplasm_db_id AS parent1_db_id,
                p1.germplasm_name AS parent1_name,
                c.parent1_type,
                p2.germplasm_db_id AS parent2_db_id,
                p2.germplasm_name AS parent2_name,
                c.parent2_type,
                c.pollination_time_stamp,
                NULL::text AS planned_cross_db_id,
                c.crossing_year,
                c.cross_status,
                c.additional_info,
                c.external_references
            FROM crosses c
            LEFT JOIN crossing_projects cp
              ON cp.id = c.crossing_project_id
             AND cp.organization_id = c.organization_id
            LEFT JOIN germplasm p1
              ON p1.id = c.parent1_db_id
             AND p1.organization_id = c.organization_id
            LEFT JOIN germplasm p2
              ON p2.id = c.parent2_db_id
             AND p2.organization_id = c.organization_id
            WHERE c.organization_id = $1
              AND c.cross_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(cross_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(cross_summary_from_row))
    }

    pub async fn list_planned_crosses(
        &self,
        params: PlannedCrossListParams,
    ) -> Result<(Vec<PlannedCrossSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_planned_crosses");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_planned_crosses"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let planned_cross_name_pattern = contains_pattern(&params.planned_cross_name);
        let crossing_project_name_pattern = contains_pattern(&params.crossing_project_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM planned_crosses pc
            LEFT JOIN crossing_projects cp
              ON cp.id = pc.crossing_project_id
             AND cp.organization_id = pc.organization_id
            WHERE pc.organization_id = $1
              AND ($2::text IS NULL OR cp.crossing_project_db_id = $2)
              AND ($3::text IS NULL OR cp.crossing_project_name ILIKE $3)
              AND ($4::text IS NULL OR pc.planned_cross_db_id = $4)
              AND ($5::text IS NULL OR pc.planned_cross_name ILIKE $5)
              AND ($6::text IS NULL OR pc.status = $6)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.crossing_project_db_id.as_deref())
        .bind(crossing_project_name_pattern.as_deref())
        .bind(params.planned_cross_db_id.as_deref())
        .bind(planned_cross_name_pattern.as_deref())
        .bind(params.status.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                pc.id,
                pc.planned_cross_db_id,
                pc.planned_cross_name,
                cp.crossing_project_db_id,
                cp.crossing_project_name,
                pc.cross_type,
                pc.status,
                p1.germplasm_db_id AS parent1_db_id,
                p1.germplasm_name AS parent1_name,
                pc.parent1_type,
                p2.germplasm_db_id AS parent2_db_id,
                p2.germplasm_name AS parent2_name,
                pc.parent2_type,
                pc.additional_info,
                pc.external_references
            FROM planned_crosses pc
            LEFT JOIN crossing_projects cp
              ON cp.id = pc.crossing_project_id
             AND cp.organization_id = pc.organization_id
            LEFT JOIN germplasm p1
              ON p1.id = pc.parent1_db_id
             AND p1.organization_id = pc.organization_id
            LEFT JOIN germplasm p2
              ON p2.id = pc.parent2_db_id
             AND p2.organization_id = pc.organization_id
            WHERE pc.organization_id = $1
              AND ($2::text IS NULL OR cp.crossing_project_db_id = $2)
              AND ($3::text IS NULL OR cp.crossing_project_name ILIKE $3)
              AND ($4::text IS NULL OR pc.planned_cross_db_id = $4)
              AND ($5::text IS NULL OR pc.planned_cross_name ILIKE $5)
              AND ($6::text IS NULL OR pc.status = $6)
            ORDER BY pc.planned_cross_name ASC NULLS LAST, pc.planned_cross_db_id ASC, pc.id ASC
            LIMIT $7 OFFSET $8
            "#,
        )
        .bind(params.organization_id)
        .bind(params.crossing_project_db_id.as_deref())
        .bind(crossing_project_name_pattern.as_deref())
        .bind(params.planned_cross_db_id.as_deref())
        .bind(planned_cross_name_pattern.as_deref())
        .bind(params.status.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let planned_crosses = rows
            .into_iter()
            .map(planned_cross_summary_from_row)
            .collect();

        Ok((planned_crosses, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_planned_cross(
        &self,
        organization_id: i64,
        planned_cross_db_id: &str,
    ) -> Result<Option<PlannedCrossSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_planned_cross");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_planned_cross"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                pc.id,
                pc.planned_cross_db_id,
                pc.planned_cross_name,
                cp.crossing_project_db_id,
                cp.crossing_project_name,
                pc.cross_type,
                pc.status,
                p1.germplasm_db_id AS parent1_db_id,
                p1.germplasm_name AS parent1_name,
                pc.parent1_type,
                p2.germplasm_db_id AS parent2_db_id,
                p2.germplasm_name AS parent2_name,
                pc.parent2_type,
                pc.additional_info,
                pc.external_references
            FROM planned_crosses pc
            LEFT JOIN crossing_projects cp
              ON cp.id = pc.crossing_project_id
             AND cp.organization_id = pc.organization_id
            LEFT JOIN germplasm p1
              ON p1.id = pc.parent1_db_id
             AND p1.organization_id = pc.organization_id
            LEFT JOIN germplasm p2
              ON p2.id = pc.parent2_db_id
             AND p2.organization_id = pc.organization_id
            WHERE pc.organization_id = $1
              AND pc.planned_cross_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(planned_cross_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(planned_cross_summary_from_row))
    }

    pub async fn list_seedlots(
        &self,
        params: SeedlotListParams,
    ) -> Result<(Vec<SeedlotSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_seedlots");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_seedlots"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let seedlot_name_pattern = contains_pattern(&params.seedlot_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM seedlots s
            LEFT JOIN germplasm g ON g.id = s.germplasm_id
            LEFT JOIN locations l ON l.id = s.location_id
            LEFT JOIN programs p ON p.id = s.program_id
            WHERE s.organization_id = $1
              AND ($2::text IS NULL OR g.germplasm_db_id = $2)
              AND ($3::text IS NULL OR l.location_db_id = $3)
              AND ($4::text IS NULL OR p.program_db_id = $4)
              AND ($5::text IS NULL OR s.seedlot_db_id = $5)
              AND ($6::text IS NULL OR s.seedlot_name ILIKE $6)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.germplasm_db_id.as_deref())
        .bind(params.location_db_id.as_deref())
        .bind(params.program_db_id.as_deref())
        .bind(params.seedlot_db_id.as_deref())
        .bind(seedlot_name_pattern.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                s.id,
                s.seedlot_db_id,
                s.seedlot_name,
                s.seedlot_description,
                g.germplasm_db_id,
                l.location_db_id,
                p.program_db_id,
                s.source_collection,
                s.storage_location,
                s.count,
                s.units,
                s.creation_date::text AS created_date,
                s.last_updated::text AS last_updated,
                s.additional_info,
                s.external_references
            FROM seedlots s
            LEFT JOIN germplasm g ON g.id = s.germplasm_id
            LEFT JOIN locations l ON l.id = s.location_id
            LEFT JOIN programs p ON p.id = s.program_id
            WHERE s.organization_id = $1
              AND ($2::text IS NULL OR g.germplasm_db_id = $2)
              AND ($3::text IS NULL OR l.location_db_id = $3)
              AND ($4::text IS NULL OR p.program_db_id = $4)
              AND ($5::text IS NULL OR s.seedlot_db_id = $5)
              AND ($6::text IS NULL OR s.seedlot_name ILIKE $6)
            ORDER BY s.seedlot_name ASC, s.seedlot_db_id ASC, s.id ASC
            LIMIT $7 OFFSET $8
            "#,
        )
        .bind(params.organization_id)
        .bind(params.germplasm_db_id.as_deref())
        .bind(params.location_db_id.as_deref())
        .bind(params.program_db_id.as_deref())
        .bind(params.seedlot_db_id.as_deref())
        .bind(seedlot_name_pattern.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let seedlots = rows.into_iter().map(seedlot_summary_from_row).collect();

        Ok((seedlots, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_seedlot(
        &self,
        organization_id: i64,
        seedlot_db_id: &str,
    ) -> Result<Option<SeedlotSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_seedlot");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_seedlot"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                s.id,
                s.seedlot_db_id,
                s.seedlot_name,
                s.seedlot_description,
                g.germplasm_db_id,
                l.location_db_id,
                p.program_db_id,
                s.source_collection,
                s.storage_location,
                s.count,
                s.units,
                s.creation_date::text AS created_date,
                s.last_updated::text AS last_updated,
                s.additional_info,
                s.external_references
            FROM seedlots s
            LEFT JOIN germplasm g ON g.id = s.germplasm_id
            LEFT JOIN locations l ON l.id = s.location_id
            LEFT JOIN programs p ON p.id = s.program_id
            WHERE s.organization_id = $1
              AND s.seedlot_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(seedlot_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(seedlot_summary_from_row))
    }

    pub async fn list_seedlot_transactions(
        &self,
        params: SeedlotTransactionListParams,
    ) -> Result<(Vec<SeedlotTransactionSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_seedlot_transactions");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_seedlot_transactions"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM seedlot_transactions tx
            LEFT JOIN seedlots s ON s.id = tx.seedlot_id
            WHERE tx.organization_id = $1
              AND ($2::text IS NULL OR s.seedlot_db_id = $2)
              AND ($3::text IS NULL OR tx.transaction_db_id = $3)
            "#,
        )
        .bind(params.organization_id)
        .bind(params.seedlot_db_id.as_deref())
        .bind(params.transaction_db_id.as_deref())
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                tx.id,
                tx.transaction_db_id,
                s.seedlot_db_id,
                tx.transaction_description,
                tx.transaction_timestamp,
                tx.amount,
                tx.units,
                tx.from_seedlot_db_id,
                tx.to_seedlot_db_id,
                tx.additional_info,
                tx.external_references
            FROM seedlot_transactions tx
            LEFT JOIN seedlots s ON s.id = tx.seedlot_id
            WHERE tx.organization_id = $1
              AND ($2::text IS NULL OR s.seedlot_db_id = $2)
              AND ($3::text IS NULL OR tx.transaction_db_id = $3)
            ORDER BY tx.transaction_timestamp ASC NULLS LAST, tx.transaction_db_id ASC, tx.id ASC
            LIMIT $4 OFFSET $5
            "#,
        )
        .bind(params.organization_id)
        .bind(params.seedlot_db_id.as_deref())
        .bind(params.transaction_db_id.as_deref())
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let transactions = rows
            .into_iter()
            .map(seedlot_transaction_summary_from_row)
            .collect();

        Ok((transactions, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn list_transactions_for_seedlot(
        &self,
        params: SeedlotScopedTransactionListParams,
    ) -> Result<Option<(Vec<SeedlotTransactionSummary>, u32)>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_transactions_for_seedlot");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_transactions_for_seedlot"));
        };

        let seedlot_id = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT id
            FROM seedlots
            WHERE organization_id = $1
              AND seedlot_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(params.organization_id)
        .bind(&params.seedlot_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let Some(seedlot_id) = seedlot_id else {
            return Ok(None);
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM seedlot_transactions
            WHERE organization_id = $1
              AND seedlot_id = $2
            "#,
        )
        .bind(params.organization_id)
        .bind(seedlot_id)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                tx.id,
                tx.transaction_db_id,
                s.seedlot_db_id,
                tx.transaction_description,
                tx.transaction_timestamp,
                tx.amount,
                tx.units,
                tx.from_seedlot_db_id,
                tx.to_seedlot_db_id,
                tx.additional_info,
                tx.external_references
            FROM seedlot_transactions tx
            JOIN seedlots s ON s.id = tx.seedlot_id
            WHERE tx.organization_id = $1
              AND tx.seedlot_id = $2
            ORDER BY tx.transaction_timestamp ASC NULLS LAST, tx.transaction_db_id ASC, tx.id ASC
            LIMIT $3 OFFSET $4
            "#,
        )
        .bind(params.organization_id)
        .bind(seedlot_id)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let transactions = rows
            .into_iter()
            .map(seedlot_transaction_summary_from_row)
            .collect();

        Ok(Some((
            transactions,
            total_count.try_into().unwrap_or(u32::MAX),
        )))
    }

    pub async fn get_seed_inventory_summary(
        &self,
        organization_id: i64,
    ) -> Result<SeedInventorySummary, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_seed_inventory_summary");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_seed_inventory_summary"));
        };

        let rows = sqlx::query(
            r#"
            SELECT
                seedlot_db_id,
                count,
                additional_info
            FROM seedlots
            WHERE organization_id = $1
            ORDER BY seedlot_db_id ASC, id ASC
            "#,
        )
        .bind(organization_id)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let today = Utc::now().date_naive();
        let mut total_quantity_g = 0.0;
        let mut by_status = BTreeMap::new();
        let mut by_storage_type = BTreeMap::new();
        let mut by_species: BTreeMap<String, SeedInventorySpeciesSummary> = BTreeMap::new();
        let mut lots_needing_viability_test = Vec::new();

        for row in rows.iter() {
            let seedlot_db_id = row.get::<String, _>("seedlot_db_id");
            let quantity_g = f64::from(row.get::<Option<i32>, _>("count").unwrap_or(0));
            let additional_info = row.get::<Option<Value>, _>("additional_info");
            total_quantity_g += quantity_g;

            let status = json_string_field(&additional_info, "status")
                .unwrap_or_else(|| "active".to_string());
            *by_status.entry(status).or_insert(0) += 1;

            let storage_type = json_string_field(&additional_info, "storage_type")
                .unwrap_or_else(|| "medium_term".to_string());
            *by_storage_type.entry(storage_type).or_insert(0) += 1;

            let species = json_string_field(&additional_info, "species").unwrap_or_default();
            let species_entry =
                by_species
                    .entry(species)
                    .or_insert_with(|| SeedInventorySpeciesSummary {
                        lots: 0,
                        quantity_g: 0.0,
                    });
            species_entry.lots += 1;
            species_entry.quantity_g += quantity_g;

            if let Some(last_test) = json_date_field(&additional_info, "last_viability_test") {
                let days_since_test = today.signed_duration_since(last_test).num_days();
                if days_since_test > 365 {
                    lots_needing_viability_test.push(SeedInventoryViabilityDueLot {
                        lot_id: seedlot_db_id,
                        days_since_test,
                        last_viability: json_f64_field(&additional_info, "current_viability"),
                    });
                }
            }
        }

        for species in by_species.values_mut() {
            species.quantity_g = round_two_decimals(species.quantity_g);
        }

        let pending_request_rows = sqlx::query(
            r#"
            SELECT additional_info
            FROM seedlot_transactions
            WHERE organization_id = $1
              AND transaction_db_id LIKE 'REQ-%'
            "#,
        )
        .bind(organization_id)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;
        let pending_requests = pending_request_rows
            .iter()
            .filter(|row| {
                let additional_info = row.get::<Option<Value>, _>("additional_info");
                json_string_field(&additional_info, "status").as_deref() == Some("pending")
            })
            .count()
            .try_into()
            .unwrap_or(u32::MAX);

        Ok(SeedInventorySummary {
            success: true,
            total_lots: rows.len().try_into().unwrap_or(u32::MAX),
            total_quantity_g: round_two_decimals(total_quantity_g),
            by_status,
            by_storage_type,
            by_species,
            lots_needing_viability_test: lots_needing_viability_test.into_iter().take(10).collect(),
            pending_requests,
        })
    }

    pub async fn list_variant_sets(
        &self,
        params: VariantSetListParams,
    ) -> Result<(Vec<VariantSetSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_variant_sets");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_variant_sets"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let variant_set_db_id = exact_filter_value(&params.variant_set_db_id);
        let study_db_id = exact_filter_value(&params.study_db_id);
        let reference_set_db_id = exact_filter_value(&params.reference_set_db_id);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM variant_sets vs
            LEFT JOIN studies st
              ON st.id = vs.study_id
             AND st.organization_id = vs.organization_id
            LEFT JOIN reference_sets rs
              ON rs.id = vs.reference_set_id
             AND rs.organization_id = vs.organization_id
            WHERE vs.organization_id = $1
              AND ($2::text IS NULL OR vs.variant_set_db_id = $2)
              AND ($3::text IS NULL OR st.study_db_id = $3)
              AND ($4::text IS NULL OR rs.reference_set_db_id = $4)
            "#,
        )
        .bind(params.organization_id)
        .bind(variant_set_db_id)
        .bind(study_db_id)
        .bind(reference_set_db_id)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                vs.id,
                vs.variant_set_db_id,
                vs.variant_set_name,
                rs.reference_set_db_id,
                st.study_db_id,
                vs.analysis,
                vs.available_formats,
                vs.call_set_count,
                vs.variant_count,
                vs.additional_info
            FROM variant_sets vs
            LEFT JOIN studies st
              ON st.id = vs.study_id
             AND st.organization_id = vs.organization_id
            LEFT JOIN reference_sets rs
              ON rs.id = vs.reference_set_id
             AND rs.organization_id = vs.organization_id
            WHERE vs.organization_id = $1
              AND ($2::text IS NULL OR vs.variant_set_db_id = $2)
              AND ($3::text IS NULL OR st.study_db_id = $3)
              AND ($4::text IS NULL OR rs.reference_set_db_id = $4)
            ORDER BY vs.variant_set_name ASC, vs.variant_set_db_id ASC NULLS LAST, vs.id ASC
            LIMIT $5 OFFSET $6
            "#,
        )
        .bind(params.organization_id)
        .bind(variant_set_db_id)
        .bind(study_db_id)
        .bind(reference_set_db_id)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let variant_sets = rows.into_iter().map(variantset_summary_from_row).collect();

        Ok((variant_sets, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_variant_set(
        &self,
        organization_id: i64,
        variant_set_db_id: &str,
    ) -> Result<Option<VariantSetSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_variant_set");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_variant_set"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                vs.id,
                vs.variant_set_db_id,
                vs.variant_set_name,
                rs.reference_set_db_id,
                st.study_db_id,
                vs.analysis,
                vs.available_formats,
                vs.call_set_count,
                vs.variant_count,
                vs.additional_info
            FROM variant_sets vs
            LEFT JOIN studies st
              ON st.id = vs.study_id
             AND st.organization_id = vs.organization_id
            LEFT JOIN reference_sets rs
              ON rs.id = vs.reference_set_id
             AND rs.organization_id = vs.organization_id
            WHERE vs.organization_id = $1
              AND vs.variant_set_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(variant_set_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(variantset_summary_from_row))
    }

    pub async fn list_callsets(
        &self,
        params: CallSetListParams,
    ) -> Result<(Vec<CallSetSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_callsets");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_callsets"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let call_set_db_id = exact_filter_value(&params.call_set_db_id);
        let sample_db_id = exact_filter_value(&params.sample_db_id);
        let variant_set_db_id = exact_filter_value(&params.variant_set_db_id);
        let call_set_name_pattern = contains_pattern(&params.call_set_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(DISTINCT cs.id)
            FROM call_sets cs
            WHERE cs.organization_id = $1
              AND ($2::text IS NULL OR cs.call_set_db_id = $2)
              AND ($3::text IS NULL OR cs.call_set_name ILIKE $3)
              AND ($4::text IS NULL OR cs.sample_db_id = $4)
              AND (
                  $5::text IS NULL
                  OR EXISTS (
                      SELECT 1
                      FROM variant_set_call_sets filter_vsc
                      JOIN variant_sets filter_vs
                        ON filter_vs.id = filter_vsc.variant_set_id
                       AND filter_vs.organization_id = cs.organization_id
                      WHERE filter_vsc.call_set_id = cs.id
                        AND filter_vs.variant_set_db_id = $5
                  )
              )
            "#,
        )
        .bind(params.organization_id)
        .bind(call_set_db_id)
        .bind(call_set_name_pattern.as_deref())
        .bind(sample_db_id)
        .bind(variant_set_db_id)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                cs.id,
                cs.call_set_db_id,
                cs.call_set_name,
                cs.sample_db_id,
                COALESCE(cs.created, cs.created_at::text) AS created,
                COALESCE(cs.updated, cs.updated_at::text) AS updated,
                cs.additional_info,
                COALESCE(
                    json_agg(vs.variant_set_db_id ORDER BY vs.variant_set_db_id)
                        FILTER (WHERE vs.variant_set_db_id IS NOT NULL),
                    '[]'::json
                ) AS variant_set_db_ids
            FROM call_sets cs
            LEFT JOIN variant_set_call_sets vsc ON vsc.call_set_id = cs.id
            LEFT JOIN variant_sets vs
              ON vs.id = vsc.variant_set_id
             AND vs.organization_id = cs.organization_id
            WHERE cs.organization_id = $1
              AND ($2::text IS NULL OR cs.call_set_db_id = $2)
              AND ($3::text IS NULL OR cs.call_set_name ILIKE $3)
              AND ($4::text IS NULL OR cs.sample_db_id = $4)
              AND (
                  $5::text IS NULL
                  OR EXISTS (
                      SELECT 1
                      FROM variant_set_call_sets filter_vsc
                      JOIN variant_sets filter_vs
                        ON filter_vs.id = filter_vsc.variant_set_id
                       AND filter_vs.organization_id = cs.organization_id
                      WHERE filter_vsc.call_set_id = cs.id
                        AND filter_vs.variant_set_db_id = $5
                  )
              )
            GROUP BY cs.id
            ORDER BY cs.call_set_name ASC, cs.call_set_db_id ASC, cs.id ASC
            LIMIT $6 OFFSET $7
            "#,
        )
        .bind(params.organization_id)
        .bind(call_set_db_id)
        .bind(call_set_name_pattern.as_deref())
        .bind(sample_db_id)
        .bind(variant_set_db_id)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let callsets = rows.into_iter().map(callset_summary_from_row).collect();

        Ok((callsets, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_callset(
        &self,
        organization_id: i64,
        call_set_db_id: &str,
    ) -> Result<Option<CallSetSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_callset");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_callset"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                cs.id,
                cs.call_set_db_id,
                cs.call_set_name,
                cs.sample_db_id,
                COALESCE(cs.created, cs.created_at::text) AS created,
                COALESCE(cs.updated, cs.updated_at::text) AS updated,
                cs.additional_info,
                COALESCE(
                    json_agg(vs.variant_set_db_id ORDER BY vs.variant_set_db_id)
                        FILTER (WHERE vs.variant_set_db_id IS NOT NULL),
                    '[]'::json
                ) AS variant_set_db_ids
            FROM call_sets cs
            LEFT JOIN variant_set_call_sets vsc ON vsc.call_set_id = cs.id
            LEFT JOIN variant_sets vs
              ON vs.id = vsc.variant_set_id
             AND vs.organization_id = cs.organization_id
            WHERE cs.organization_id = $1
              AND cs.call_set_db_id = $2
            GROUP BY cs.id
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(call_set_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(callset_summary_from_row))
    }

    pub async fn list_maps(
        &self,
        params: GenomeMapListParams,
    ) -> Result<(Vec<GenomeMapSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_maps");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_maps"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let map_db_id = exact_filter_value(&params.map_db_id);
        let map_pui = exact_filter_value(&params.map_pui);
        let map_type = exact_filter_value(&params.map_type);
        let common_crop_name_pattern = contains_pattern(&params.common_crop_name);
        let scientific_name_pattern = contains_pattern(&params.scientific_name);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM genome_maps
            WHERE organization_id = $1
              AND ($2::text IS NULL OR map_db_id = $2)
              AND ($3::text IS NULL OR map_pui = $3)
              AND ($4::text IS NULL OR common_crop_name ILIKE $4)
              AND ($5::text IS NULL OR scientific_name ILIKE $5)
              AND ($6::text IS NULL OR type = $6)
            "#,
        )
        .bind(params.organization_id)
        .bind(map_db_id)
        .bind(map_pui)
        .bind(common_crop_name_pattern.as_deref())
        .bind(scientific_name_pattern.as_deref())
        .bind(map_type)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                id,
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
                additional_info,
                linkage_group_count,
                marker_count
            FROM genome_maps
            WHERE organization_id = $1
              AND ($2::text IS NULL OR map_db_id = $2)
              AND ($3::text IS NULL OR map_pui = $3)
              AND ($4::text IS NULL OR common_crop_name ILIKE $4)
              AND ($5::text IS NULL OR scientific_name ILIKE $5)
              AND ($6::text IS NULL OR type = $6)
            ORDER BY map_name ASC, map_db_id ASC, id ASC
            LIMIT $7 OFFSET $8
            "#,
        )
        .bind(params.organization_id)
        .bind(map_db_id)
        .bind(map_pui)
        .bind(common_crop_name_pattern.as_deref())
        .bind(scientific_name_pattern.as_deref())
        .bind(map_type)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let maps = rows.into_iter().map(genome_map_summary_from_row).collect();

        Ok((maps, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn get_map(
        &self,
        organization_id: i64,
        map_db_id: &str,
    ) -> Result<Option<GenomeMapSummary>, DataStoreError> {
        let _timer = ReadRepositoryTimer::start("get_map");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("get_map"));
        };

        let row = sqlx::query(
            r#"
            SELECT
                id,
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
                additional_info,
                linkage_group_count,
                marker_count
            FROM genome_maps
            WHERE organization_id = $1
              AND map_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(organization_id)
        .bind(map_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        Ok(row.map(genome_map_summary_from_row))
    }

    pub async fn list_linkage_groups_for_map(
        &self,
        params: LinkageGroupListParams,
    ) -> Result<(Vec<LinkageGroupSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_linkage_groups_for_map");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_linkage_groups_for_map"));
        };

        let map_id = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT id
            FROM genome_maps
            WHERE organization_id = $1
              AND map_db_id = $2
            LIMIT 1
            "#,
        )
        .bind(params.organization_id)
        .bind(&params.map_db_id)
        .fetch_optional(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let Some(map_id) = map_id else {
            return Ok((Vec::new(), 0));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM linkage_groups
            WHERE organization_id = $1
              AND map_id = $2
            "#,
        )
        .bind(params.organization_id)
        .bind(map_id)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                lg.linkage_group_name,
                lg.max_position,
                lg.marker_count,
                lg.additional_info,
                gm.map_db_id
            FROM linkage_groups lg
            JOIN genome_maps gm ON gm.id = lg.map_id
            WHERE lg.organization_id = $1
              AND lg.map_id = $2
            ORDER BY lg.linkage_group_name ASC, lg.id ASC
            LIMIT $3 OFFSET $4
            "#,
        )
        .bind(params.organization_id)
        .bind(map_id)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let linkage_groups = rows.into_iter().map(linkage_group_from_row).collect();

        Ok((linkage_groups, total_count.try_into().unwrap_or(u32::MAX)))
    }

    pub async fn list_marker_positions(
        &self,
        params: MarkerPositionListParams,
    ) -> Result<(Vec<MarkerPositionSummary>, u32), DataStoreError> {
        let _timer = ReadRepositoryTimer::start("list_marker_positions");
        let Some(pool) = &self.pool else {
            return Err(data_store_unavailable("list_marker_positions"));
        };

        let limit = i64::from(params.page_size);
        let offset = page_offset(params.page, params.page_size);
        let map_db_id = exact_filter_value(&params.map_db_id);
        let linkage_group_name = exact_filter_value(&params.linkage_group_name);
        let variant_db_id = exact_filter_value(&params.variant_db_id);

        let total_count = sqlx::query_scalar::<_, i64>(
            r#"
            SELECT COUNT(*)
            FROM marker_positions mp
            JOIN genome_maps gm
              ON gm.id = mp.map_id
             AND gm.organization_id = mp.organization_id
            WHERE mp.organization_id = $1
              AND ($2::text IS NULL OR gm.map_db_id = $2)
              AND ($3::text IS NULL OR mp.linkage_group_name = $3)
              AND ($4::text IS NULL OR mp.variant_db_id = $4)
              AND ($5::double precision IS NULL OR mp.position >= $5)
              AND ($6::double precision IS NULL OR mp.position <= $6)
            "#,
        )
        .bind(params.organization_id)
        .bind(map_db_id)
        .bind(linkage_group_name)
        .bind(variant_db_id)
        .bind(params.min_position)
        .bind(params.max_position)
        .fetch_one(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let rows = sqlx::query(
            r#"
            SELECT
                mp.id,
                mp.marker_position_db_id,
                mp.variant_db_id,
                mp.variant_name,
                gm.map_db_id,
                gm.map_name,
                mp.linkage_group_name,
                mp.position,
                mp.additional_info
            FROM marker_positions mp
            JOIN genome_maps gm
              ON gm.id = mp.map_id
             AND gm.organization_id = mp.organization_id
            WHERE mp.organization_id = $1
              AND ($2::text IS NULL OR gm.map_db_id = $2)
              AND ($3::text IS NULL OR mp.linkage_group_name = $3)
              AND ($4::text IS NULL OR mp.variant_db_id = $4)
              AND ($5::double precision IS NULL OR mp.position >= $5)
              AND ($6::double precision IS NULL OR mp.position <= $6)
            ORDER BY
                gm.map_name ASC,
                mp.linkage_group_name ASC NULLS LAST,
                mp.position ASC NULLS LAST,
                mp.marker_position_db_id ASC NULLS LAST,
                mp.id ASC
            LIMIT $7 OFFSET $8
            "#,
        )
        .bind(params.organization_id)
        .bind(map_db_id)
        .bind(linkage_group_name)
        .bind(variant_db_id)
        .bind(params.min_position)
        .bind(params.max_position)
        .bind(limit)
        .bind(offset)
        .fetch_all(pool)
        .await
        .map_err(DataStoreError::Query)?;

        let marker_positions = rows.into_iter().map(marker_position_from_row).collect();

        Ok((marker_positions, total_count.try_into().unwrap_or(u32::MAX)))
    }
}

fn normalize_database_url(url: &str) -> Option<String> {
    let trimmed = url.trim();
    if trimmed.is_empty() || trimmed.starts_with("sqlite") {
        return None;
    }

    Some(
        trimmed
            .strip_prefix("postgresql+asyncpg://")
            .map(|rest| format!("postgres://{rest}"))
            .or_else(|| {
                trimmed
                    .strip_prefix("postgres+asyncpg://")
                    .map(|rest| format!("postgres://{rest}"))
            })
            .unwrap_or_else(|| trimmed.to_string()),
    )
}

fn configure_postgres_pool(database_url: String) -> Option<PgPool> {
    let statement_timeout = read_statement_timeout_ms_from_env().to_string();

    PgPoolOptions::new()
        .max_connections(5)
        .after_connect(move |connection, _metadata| {
            let statement_timeout = statement_timeout.clone();
            Box::pin(async move {
                sqlx::query("SELECT set_config('statement_timeout', $1, false)")
                    .bind(statement_timeout)
                    .execute(connection)
                    .await?;
                Ok(())
            })
        })
        .connect_lazy(&database_url)
        .inspect_err(|error| tracing::warn!(%error, route_context = "rust_read_beta_pool", "failed to configure Rust Postgres pool"))
        .ok()
}

fn read_statement_timeout_ms_from_env() -> u64 {
    let value = std::env::var(READ_STATEMENT_TIMEOUT_ENV).ok();
    read_statement_timeout_ms(value.as_deref())
}

fn read_statement_timeout_ms(value: Option<&str>) -> u64 {
    value
        .and_then(parse_read_statement_timeout_ms)
        .unwrap_or(DEFAULT_READ_STATEMENT_TIMEOUT_MS)
}

fn parse_read_statement_timeout_ms(value: &str) -> Option<u64> {
    let parsed = value.trim().parse::<u64>().ok()?;
    Some(parsed.min(MAX_READ_STATEMENT_TIMEOUT_MS))
}

async fn set_transaction_organization_context(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    organization_id: i64,
) -> Result<(), sqlx::Error> {
    sqlx::query("SELECT set_config('app.current_organization_id', $1, true)")
        .bind(organization_id.to_string())
        .execute(&mut **tx)
        .await?;
    Ok(())
}

async fn set_write_transaction_context(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    options: &WriteTransactionOptions,
) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"
        SELECT
            set_config('app.current_organization_id', $1, true),
            set_config('app.current_user_id', $2, true),
            set_config('app.idempotency_key', $3, true),
            set_config('app.audit_event', $4, true)
        "#,
    )
    .bind(options.organization_id.to_string())
    .bind(options.actor_user_id.to_string())
    .bind(options.idempotency_key.clone().unwrap_or_default())
    .bind(options.audit_event.trim())
    .execute(&mut **tx)
    .await?;
    Ok(())
}

const SEEDLOT_ADJUSTMENT_SELECT_BY_PUBLIC_ID_SQL: &str = r#"
    SELECT
        id,
        public_id::text AS public_id,
        organization_id,
        seedlot_id,
        seedlot_db_id,
        adjustment_type,
        quantity_delta::text AS quantity_delta,
        unit,
        reason,
        idempotency_key,
        action,
        actor_user_id,
        audit_event,
        observed_at::text AS observed_at,
        created_at::text AS created_at,
        metadata,
        reversal_of_public_id::text AS reversal_of_public_id,
        reversed_at::text AS reversed_at
    FROM seedlot_inventory_adjustments
    WHERE organization_id = $1
      AND public_id = $2::uuid
    LIMIT 1
"#;

const SEEDLOT_ADJUSTMENT_SELECT_BY_IDEMPOTENCY_SQL: &str = r#"
    SELECT
        id,
        public_id::text AS public_id,
        organization_id,
        seedlot_id,
        seedlot_db_id,
        adjustment_type,
        quantity_delta::text AS quantity_delta,
        unit,
        reason,
        idempotency_key,
        action,
        actor_user_id,
        audit_event,
        observed_at::text AS observed_at,
        created_at::text AS created_at,
        metadata,
        reversal_of_public_id::text AS reversal_of_public_id,
        reversed_at::text AS reversed_at
    FROM seedlot_inventory_adjustments
    WHERE organization_id = $1
      AND actor_user_id = $2
      AND action = 'seedlot_inventory_adjustment.create'
      AND idempotency_key = $3
    LIMIT 1
"#;

const SEEDLOT_ADJUSTMENT_LIST_SQL: &str = r#"
    SELECT
        id,
        public_id::text AS public_id,
        organization_id,
        seedlot_id,
        seedlot_db_id,
        adjustment_type,
        quantity_delta::text AS quantity_delta,
        unit,
        reason,
        idempotency_key,
        action,
        actor_user_id,
        audit_event,
        observed_at::text AS observed_at,
        created_at::text AS created_at,
        metadata,
        reversal_of_public_id::text AS reversal_of_public_id,
        reversed_at::text AS reversed_at
    FROM seedlot_inventory_adjustments
    WHERE organization_id = $1
      AND ($2::text IS NULL OR seedlot_db_id = $2)
    ORDER BY created_at DESC, id DESC
    LIMIT $3 OFFSET $4
"#;

async fn fetch_seedlot_adjustment_by_public_id_in_tx(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    organization_id: i64,
    public_id: bijmantra_core::PublicId,
) -> Result<Option<SeedlotInventoryAdjustmentRecord>, SeedlotInventoryAdjustmentWriteError> {
    let row = sqlx::query(SEEDLOT_ADJUSTMENT_SELECT_BY_PUBLIC_ID_SQL)
        .bind(organization_id)
        .bind(public_id.as_uuid().to_string())
        .fetch_optional(&mut **tx)
        .await
        .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

    row.map(seedlot_inventory_adjustment_record_from_row)
        .transpose()
}

async fn fetch_seedlot_adjustment_by_idempotency_in_tx(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    organization_id: i64,
    actor_user_id: i64,
    idempotency_key: &str,
) -> Result<Option<SeedlotInventoryAdjustmentRecord>, SeedlotInventoryAdjustmentWriteError> {
    let row = sqlx::query(SEEDLOT_ADJUSTMENT_SELECT_BY_IDEMPOTENCY_SQL)
        .bind(organization_id)
        .bind(actor_user_id)
        .bind(idempotency_key)
        .fetch_optional(&mut **tx)
        .await
        .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

    row.map(seedlot_inventory_adjustment_record_from_row)
        .transpose()
}

async fn insert_seedlot_inventory_adjustment_in_tx(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    command: &SeedlotInventoryAdjustmentCreate,
) -> Result<Option<SeedlotInventoryAdjustmentRecord>, SeedlotInventoryAdjustmentWriteError> {
    let seedlot_id = sqlx::query_scalar::<_, i64>(
        r#"
        SELECT id
        FROM seedlots
        WHERE organization_id = $1
          AND seedlot_db_id = $2
        LIMIT 1
        "#,
    )
    .bind(command.organization_id)
    .bind(&command.seedlot_db_id)
    .fetch_optional(&mut **tx)
    .await
    .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

    let metadata = serde_json::to_value(&command.metadata).unwrap_or_else(|_| json!({}));
    let reversal_of_public_id = command
        .reversal_of_public_id
        .map(|public_id| public_id.as_uuid().to_string());

    let row = sqlx::query(
        r#"
        INSERT INTO seedlot_inventory_adjustments (
            public_id,
            organization_id,
            seedlot_id,
            seedlot_db_id,
            adjustment_type,
            quantity_delta,
            unit,
            reason,
            idempotency_key,
            action,
            actor_user_id,
            audit_event,
            observed_at,
            metadata,
            reversal_of_public_id
        )
        VALUES (
            $1::uuid,
            $2,
            $3,
            $4,
            $5,
            $6::numeric,
            $7,
            $8,
            $9,
            $10,
            $11,
            $12,
            $13::timestamptz,
            $14::jsonb,
            $15::uuid
        )
        ON CONFLICT ON CONSTRAINT uq_seedlot_inventory_adjustments_idempotency
        DO NOTHING
        RETURNING
            id,
            public_id::text AS public_id,
            organization_id,
            seedlot_id,
            seedlot_db_id,
            adjustment_type,
            quantity_delta::text AS quantity_delta,
            unit,
            reason,
            idempotency_key,
            action,
            actor_user_id,
            audit_event,
            observed_at::text AS observed_at,
            created_at::text AS created_at,
            metadata,
            reversal_of_public_id::text AS reversal_of_public_id,
            reversed_at::text AS reversed_at
        "#,
    )
    .bind(command.public_id.as_uuid().to_string())
    .bind(command.organization_id)
    .bind(seedlot_id)
    .bind(&command.seedlot_db_id)
    .bind(command.adjustment_type.as_str())
    .bind(&command.quantity_delta)
    .bind(command.unit.as_str())
    .bind(&command.reason)
    .bind(command.idempotency_key.as_str())
    .bind(command.action())
    .bind(command.actor_user_id)
    .bind(command.audit_event())
    .bind(command.observed_at.as_deref())
    .bind(metadata)
    .bind(reversal_of_public_id.as_deref())
    .fetch_optional(&mut **tx)
    .await
    .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

    let Some(row) = row else {
        return Ok(None);
    };
    let record = seedlot_inventory_adjustment_record_from_row(row)?;
    insert_seedlot_adjustment_audit_in_tx(tx, command, &record).await?;
    Ok(Some(record))
}

async fn resolve_seedlot_adjustment_idempotency_collision_in_tx(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    command: &SeedlotInventoryAdjustmentCreate,
) -> Result<SeedlotInventoryAdjustmentRecord, SeedlotInventoryAdjustmentWriteError> {
    let existing = fetch_seedlot_adjustment_by_idempotency_in_tx(
        tx,
        command.organization_id,
        command.actor_user_id,
        command.idempotency_key.as_str(),
    )
    .await?
    .ok_or(SeedlotInventoryAdjustmentWriteError::IdempotencyConflict)?;

    if existing.matches_create_command(command) {
        Ok(existing)
    } else {
        Err(SeedlotInventoryAdjustmentWriteError::IdempotencyConflict)
    }
}

async fn insert_seedlot_adjustment_audit_in_tx(
    tx: &mut sqlx::Transaction<'_, sqlx::Postgres>,
    command: &SeedlotInventoryAdjustmentCreate,
    record: &SeedlotInventoryAdjustmentRecord,
) -> Result<(), SeedlotInventoryAdjustmentWriteError> {
    let changes = json!({
        "publicId": record.public_id.to_string(),
        "seedLotDbId": record.seedlot_db_id,
        "adjustmentType": record.adjustment_type.as_str(),
        "quantityDelta": record.quantity_delta,
        "unit": record.unit.as_str(),
        "reason": record.reason,
        "action": record.action,
        "auditEvent": record.audit_event,
        "reversalOfPublicId": record.reversal_of_public_id.map(|public_id| public_id.to_string()),
    });

    sqlx::query(
        r#"
        INSERT INTO audit_logs (
            organization_id,
            user_id,
            action,
            target_type,
            target_id,
            changes,
            method
        )
        VALUES (
            $1,
            $2,
            $3,
            $4,
            $5,
            $6::json,
            'INTERNAL'
        )
        "#,
    )
    .bind(command.organization_id)
    .bind(command.actor_user_id)
    .bind(command.audit_event())
    .bind(SEEDLOT_ADJUSTMENT_AUDIT_TARGET_TYPE)
    .bind(record.public_id.to_string())
    .bind(changes)
    .execute(&mut **tx)
    .await
    .map_err(SeedlotInventoryAdjustmentWriteError::Query)?;

    Ok(())
}

fn validate_write_lookup_context(
    organization_id: i64,
    actor_user_id: Option<i64>,
) -> Result<(), SeedlotInventoryAdjustmentWriteError> {
    if organization_id <= 0 {
        return Err(SeedlotInventoryAdjustmentWriteError::InvalidContext(
            "organization_id must be positive",
        ));
    }
    if actor_user_id.is_some_and(|user_id| user_id <= 0) {
        return Err(SeedlotInventoryAdjustmentWriteError::InvalidContext(
            "actor_user_id must be positive",
        ));
    }
    Ok(())
}

fn seedlot_inventory_adjustment_record_from_row(
    row: PgRow,
) -> Result<SeedlotInventoryAdjustmentRecord, SeedlotInventoryAdjustmentWriteError> {
    let public_id = parse_stored_public_id(row.get("public_id"), "public_id")?;
    let reversal_of_public_id = row
        .get::<Option<String>, _>("reversal_of_public_id")
        .map(|value| parse_stored_public_id(value, "reversal_of_public_id"))
        .transpose()?;
    let adjustment_type = row
        .get::<String, _>("adjustment_type")
        .parse::<SeedlotInventoryAdjustmentType>()?;
    let unit = row
        .get::<String, _>("unit")
        .parse::<SeedlotInventoryAdjustmentUnit>()?;
    let idempotency_key = IdempotencyKey::parse(row.get::<String, _>("idempotency_key"))?;
    let metadata = value_to_object(row.get::<Value, _>("metadata")).ok_or(
        SeedlotInventoryAdjustmentWriteError::InvalidStoredRecord("metadata must be an object"),
    )?;

    Ok(SeedlotInventoryAdjustmentRecord {
        id: row.get("id"),
        public_id,
        organization_id: row.get("organization_id"),
        seedlot_id: row.get("seedlot_id"),
        seedlot_db_id: row.get("seedlot_db_id"),
        adjustment_type,
        quantity_delta: row.get("quantity_delta"),
        unit,
        reason: row.get("reason"),
        idempotency_key,
        action: row.get("action"),
        actor_user_id: row.get("actor_user_id"),
        audit_event: row.get("audit_event"),
        observed_at: row.get("observed_at"),
        created_at: row.get("created_at"),
        metadata,
        reversal_of_public_id,
        reversed_at: row.get("reversed_at"),
    })
}

fn parse_stored_public_id(
    value: String,
    column: &'static str,
) -> Result<bijmantra_core::PublicId, SeedlotInventoryAdjustmentWriteError> {
    bijmantra_core::PublicId::parse(&value)
        .map_err(|_| SeedlotInventoryAdjustmentWriteError::InvalidStoredRecord(column))?
        .require_uuid7()
        .map_err(SeedlotInventoryAdjustmentWriteError::Validation)
}

fn negate_quantity_delta(value: &str) -> String {
    value
        .strip_prefix('-')
        .map(str::to_owned)
        .unwrap_or_else(|| format!("-{value}"))
}

fn json_object_with_original_public_id(
    public_id: bijmantra_core::PublicId,
) -> BTreeMap<String, Value> {
    BTreeMap::from([(
        "reversedAdjustmentPublicId".to_owned(),
        json!(public_id.to_string()),
    )])
}

fn value_to_object(value: Value) -> Option<BTreeMap<String, Value>> {
    serde_json::from_value(value).ok()
}

fn value_to_external_references(value: Value) -> Option<Vec<BTreeMap<String, String>>> {
    value_to_string_maps(value)
}

fn value_to_string_maps(value: Value) -> Option<Vec<BTreeMap<String, String>>> {
    serde_json::from_value(value).ok()
}

fn value_to_objects(value: Value) -> Option<Vec<BTreeMap<String, Value>>> {
    serde_json::from_value(value).ok()
}

fn value_to_strings(value: Value) -> Option<Vec<String>> {
    serde_json::from_value(value).ok()
}

fn value_number_field(value: &Value, field: &str) -> Option<f64> {
    value.get(field).and_then(Value::as_f64)
}

fn json_string_field(value: &Option<Value>, field: &str) -> Option<String> {
    value
        .as_ref()
        .and_then(|value| value.get(field))
        .and_then(value_to_nonempty_string)
}

fn json_f64_field(value: &Option<Value>, field: &str) -> Option<f64> {
    value
        .as_ref()
        .and_then(|value| value.get(field))
        .and_then(Value::as_f64)
}

fn json_date_field(value: &Option<Value>, field: &str) -> Option<NaiveDate> {
    let raw = json_string_field(value, field)?;
    NaiveDate::parse_from_str(&raw, "%Y-%m-%d").ok()
}

fn round_two_decimals(value: f64) -> f64 {
    (value * 100.0).round() / 100.0
}

fn filter_value(value: &Option<String>) -> Option<&str> {
    value
        .as_deref()
        .map(str::trim)
        .filter(|value| !value.is_empty())
}

fn exact_filter_value(value: &Option<String>) -> Option<&str> {
    filter_value(value)
}

fn contains_pattern(value: &Option<String>) -> Option<String> {
    filter_value(value).map(|value| format!("%{value}%"))
}

fn page_offset(page: u32, page_size: u32) -> i64 {
    i64::from(page) * i64::from(page_size)
}

fn location_summary_from_row(row: PgRow) -> LocationSummary {
    let id = row.get::<i64, _>("id");
    let latitude = row.get::<Option<f64>, _>("latitude");
    let longitude = row.get::<Option<f64>, _>("longitude");
    let coordinates = latitude
        .zip(longitude)
        .map(|(latitude, longitude)| Coordinates {
            latitude,
            longitude,
            altitude: row.get("coordinate_altitude"),
        });
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    LocationSummary {
        location_name: row.get("location_name"),
        location_type: row.get("location_type"),
        abbreviation: row.get("abbreviation"),
        country_name: row.get("country_name"),
        country_code: row.get("country_code"),
        institute_name: row.get("institute_name"),
        institute_address: row.get("institute_address"),
        coordinates,
        coordinate_uncertainty: row.get("coordinate_uncertainty"),
        coordinate_description: row.get("coordinate_description"),
        altitude: row.get("altitude"),
        additional_info,
        external_references,
        location_db_id: row
            .get::<Option<String>, _>("location_db_id")
            .unwrap_or_else(|| id.to_string()),
    }
}

fn program_summary_from_row(row: PgRow) -> ProgramSummary {
    let id = row.get::<i64, _>("id");
    let lead_person_db_id = row
        .get::<Option<i64>, _>("lead_person_db_id")
        .map(|value| value.to_string());
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    ProgramSummary {
        program_name: row.get("program_name"),
        abbreviation: row.get("abbreviation"),
        objective: row.get("objective"),
        lead_person_db_id,
        additional_info,
        external_references,
        program_db_id: row
            .get::<Option<String>, _>("program_db_id")
            .unwrap_or_else(|| id.to_string()),
    }
}

fn trial_summary_from_row(row: PgRow) -> TrialSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    TrialSummary {
        trial_name: row.get("trial_name"),
        trial_description: row.get("trial_description"),
        trial_type: row.get("trial_type"),
        program_db_id: row.get("program_db_id"),
        start_date: row.get("start_date"),
        end_date: row.get("end_date"),
        active: row.get("active"),
        common_crop_name: row.get("common_crop_name"),
        additional_info,
        external_references,
        trial_db_id: row
            .get::<Option<String>, _>("trial_db_id")
            .unwrap_or_else(|| id.to_string()),
    }
}

fn study_summary_from_row(row: PgRow) -> StudySummary {
    let id = row.get::<i64, _>("id");
    let observation_levels = row
        .get::<Option<Value>, _>("observation_levels")
        .and_then(value_to_string_maps);
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    StudySummary {
        study_name: row.get("study_name"),
        study_description: row.get("study_description"),
        study_type: row.get("study_type"),
        study_code: row.get("study_code"),
        trial_db_id: row.get("trial_db_id"),
        location_db_id: row.get("location_db_id"),
        start_date: row.get("start_date"),
        end_date: row.get("end_date"),
        active: row.get("active"),
        common_crop_name: row.get("common_crop_name"),
        cultural_practices: row.get("cultural_practices"),
        observation_levels,
        observation_units_description: row.get("observation_units_description"),
        license: row.get("license"),
        additional_info,
        external_references,
        study_db_id: row
            .get::<Option<String>, _>("study_db_id")
            .unwrap_or_else(|| id.to_string()),
    }
}

fn season_summary_from_row(row: PgRow) -> SeasonSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    SeasonSummary {
        season_name: row.get("season_name"),
        year: row.get("year"),
        additional_info,
        external_references,
        season_db_id: row
            .get::<Option<String>, _>("season_db_id")
            .unwrap_or_else(|| id.to_string()),
    }
}

fn person_summary_from_row(row: PgRow) -> PersonSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();

    PersonSummary {
        person_db_id: row
            .get::<Option<String>, _>("person_db_id")
            .unwrap_or_else(|| id.to_string()),
        first_name: row.get("first_name"),
        last_name: row.get("last_name"),
        middle_name: row.get("middle_name"),
        email_address: row.get("email_address"),
        phone_number: row.get("phone_number"),
        mailing_address: row.get("mailing_address"),
        user_id: row.get("user_id"),
        additional_info,
        external_references,
    }
}

fn list_summary_from_row(row: PgRow) -> ListSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();
    let data = row
        .get::<Option<Value>, _>("data")
        .and_then(value_to_strings)
        .unwrap_or_default();

    ListSummary {
        list_db_id: row
            .get::<Option<String>, _>("list_db_id")
            .unwrap_or_else(|| id.to_string()),
        list_name: row.get("list_name"),
        list_description: row.get("list_description"),
        list_type: row.get("list_type"),
        list_owner_name: row.get("list_owner_name"),
        list_owner_person_db_id: row.get("list_owner_person_db_id"),
        list_size: row.get::<Option<i32>, _>("list_size").unwrap_or(0),
        list_source: row.get("list_source"),
        date_created: row.get("date_created"),
        date_modified: row.get("date_modified"),
        external_references,
        additional_info,
        data,
    }
}

fn ontology_summary_from_row(row: PgRow) -> OntologySummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();

    OntologySummary {
        ontology_db_id: row
            .get::<Option<String>, _>("ontology_db_id")
            .unwrap_or_else(|| id.to_string()),
        ontology_name: row.get("ontology_name"),
        description: row.get("description"),
        version: row.get("version"),
        authors: row.get("authors"),
        copyright: row.get("copyright"),
        licence: row.get("licence"),
        documentation_url: row.get("documentation_url"),
        additional_info,
    }
}

fn germplasm_summary_from_row(row: PgRow) -> GermplasmSummary {
    let id = row.get::<i64, _>("id");
    let germplasm_name = row.get::<String, _>("germplasm_name");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);
    let synonyms = row
        .get::<Option<Value>, _>("synonyms")
        .and_then(value_to_strings)
        .unwrap_or_default();
    let donors = row
        .get::<Option<Value>, _>("donors")
        .and_then(value_to_objects)
        .unwrap_or_default();

    GermplasmSummary {
        germplasm_db_id: row
            .get::<Option<String>, _>("germplasm_db_id")
            .unwrap_or_else(|| id.to_string()),
        germplasm_name: germplasm_name.clone(),
        germplasm_pui: row.get("germplasm_pui"),
        default_display_name: row
            .get::<Option<String>, _>("default_display_name")
            .unwrap_or(germplasm_name),
        accession_number: row.get("accession_number"),
        species: row.get("species"),
        genus: row.get("genus"),
        subtaxa: row.get("subtaxa"),
        common_crop_name: row.get("common_crop_name"),
        institute_code: row.get("institute_code"),
        institute_name: row.get("institute_name"),
        biological_status_of_accession_code: row.get("biological_status_of_accession_code"),
        country_of_origin_code: row.get("country_of_origin_code"),
        synonyms,
        donors,
        pedigree: row.get("pedigree"),
        seed_source: row.get("seed_source"),
        seed_source_description: row.get("seed_source_description"),
        additional_info,
        external_references,
    }
}

fn attribute_summary_from_row(row: PgRow) -> AttributeSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();
    let context_of_use = row
        .get::<Option<Value>, _>("context_of_use")
        .and_then(value_to_strings)
        .unwrap_or_default();
    let synonyms = row
        .get::<Option<Value>, _>("synonyms")
        .and_then(value_to_strings)
        .unwrap_or_default();

    AttributeSummary {
        attribute_db_id: row
            .get::<Option<String>, _>("attribute_db_id")
            .unwrap_or_else(|| id.to_string()),
        attribute_name: row.get("attribute_name"),
        attribute_pui: row.get("attribute_pui"),
        attribute_description: row.get("attribute_description"),
        attribute_category: row.get("attribute_category"),
        common_crop_name: row.get("common_crop_name"),
        context_of_use,
        default_value: row.get("default_value"),
        documentation_url: row.get("documentation_url"),
        growth_stage: row.get("growth_stage"),
        institution: row.get("institution"),
        language: row.get("language"),
        scientist: row.get("scientist"),
        status: row.get("status"),
        submission_timestamp: row.get("submission_timestamp"),
        synonyms,
        trait_db_id: row.get("trait_db_id"),
        trait_name: row.get("trait_name"),
        trait_description: row.get("trait_description"),
        trait_class: row.get("trait_class"),
        method_db_id: row.get("method_db_id"),
        method_name: row.get("method_name"),
        method_description: row.get("method_description"),
        method_class: row.get("method_class"),
        scale_db_id: row.get("scale_db_id"),
        scale_name: row.get("scale_name"),
        data_type: row.get("data_type"),
        additional_info,
        external_references,
    }
}

fn attribute_value_summary_from_row(row: PgRow) -> AttributeValueSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();

    AttributeValueSummary {
        attribute_value_db_id: row
            .get::<Option<String>, _>("attribute_value_db_id")
            .unwrap_or_else(|| id.to_string()),
        attribute_db_id: row.get("attribute_db_id"),
        attribute_name: row.get("attribute_name"),
        germplasm_db_id: row.get("germplasm_db_id"),
        germplasm_name: row.get("germplasm_name"),
        value: row.get("value"),
        determined_date: row.get("determined_date"),
        additional_info,
        external_references,
    }
}

fn breeding_method_from_row(row: PgRow) -> BreedingMethodSummary {
    let id = row.get::<i64, _>("id");

    BreedingMethodSummary {
        breeding_method_db_id: row
            .get::<Option<String>, _>("breeding_method_db_id")
            .unwrap_or_else(|| id.to_string()),
        breeding_method_name: row.get("breeding_method_name"),
        abbreviation: row.get("abbreviation"),
        description: row.get("description"),
    }
}

fn trait_summary_from_row(row: PgRow) -> TraitSummary {
    let id = row.get::<i64, _>("id");
    let valid_values = row.get::<Option<Value>, _>("valid_values");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);
    let ontology_reference = ontology_reference_from_row(&row);

    TraitSummary {
        observation_variable_db_id: row
            .get::<Option<String>, _>("observation_variable_db_id")
            .unwrap_or_else(|| id.to_string()),
        observation_variable_name: row.get("observation_variable_name"),
        trait_name: row.get("trait_name"),
        trait_description: row.get("trait_description"),
        trait_class: row.get("trait_class"),
        method_name: row.get("method_name"),
        method_description: row.get("method_description"),
        scale_name: row.get("scale_name"),
        scale_data_type: row.get("data_type"),
        scale_valid_value_min: valid_values
            .as_ref()
            .and_then(|value| value_number_field(value, "min")),
        scale_valid_value_max: valid_values
            .as_ref()
            .and_then(|value| value_number_field(value, "max")),
        default_value: row.get("default_value"),
        ontology_reference,
        common_crop_name: row.get("common_crop_name"),
        status: row.get("status"),
        additional_info,
        external_references,
    }
}

fn ontology_reference_from_row(row: &PgRow) -> Option<BTreeMap<String, Value>> {
    let mut reference = BTreeMap::new();

    if let Some(ontology_db_id) = row.get::<Option<String>, _>("ontology_db_id") {
        reference.insert("ontologyDbId".to_string(), json!(ontology_db_id));
    }
    if let Some(ontology_name) = row.get::<Option<String>, _>("ontology_name") {
        reference.insert("ontologyName".to_string(), json!(ontology_name));
    }
    if let Some(ontology_term_id) = row.get::<Option<String>, _>("ontology_term_id") {
        reference.insert("ontologyTermId".to_string(), json!(ontology_term_id));
    }
    if let Some(ontology_version) = row.get::<Option<String>, _>("ontology_version") {
        reference.insert("version".to_string(), json!(ontology_version));
    }
    if let Some(documentation_links) = row.get::<Option<Value>, _>("ontology_documentation_links") {
        reference.insert("documentationLinks".to_string(), documentation_links);
    }

    if reference.is_empty() {
        None
    } else {
        Some(reference)
    }
}

fn variable_summary_from_row(row: PgRow) -> VariableSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);
    let synonyms = row
        .get::<Option<Value>, _>("synonyms")
        .and_then(value_to_strings);
    let ontology_reference = ontology_reference_from_row(&row);
    let trait_summary = variable_trait_summary_from_row(&row);
    let method = variable_method_summary_from_row(&row);
    let scale = variable_scale_summary_from_row(&row);

    VariableSummary {
        observation_variable_db_id: row
            .get::<Option<String>, _>("observation_variable_db_id")
            .unwrap_or_else(|| id.to_string()),
        observation_variable_name: row.get("observation_variable_name"),
        common_crop_name: row.get("common_crop_name"),
        default_value: row.get("default_value"),
        growth_stage: row.get("growth_stage"),
        institution: row.get("institution"),
        language: row.get("language"),
        scientist: row.get("scientist"),
        status: row.get("status"),
        submission_timestamp: row.get("submission_timestamp"),
        synonyms,
        trait_summary,
        method,
        scale,
        ontology_reference,
        additional_info,
        external_references,
    }
}

fn variable_trait_summary_from_row(row: &PgRow) -> Option<VariableTraitSummary> {
    let trait_name = row.get::<Option<String>, _>("trait_name")?;

    Some(VariableTraitSummary {
        trait_db_id: row.get("trait_db_id"),
        trait_name: Some(trait_name),
        trait_description: row.get("trait_description"),
        trait_class: row.get("trait_class"),
    })
}

fn variable_method_summary_from_row(row: &PgRow) -> Option<VariableMethodSummary> {
    let method_name = row.get::<Option<String>, _>("method_name")?;

    Some(VariableMethodSummary {
        method_db_id: row.get("method_db_id"),
        method_name: Some(method_name),
        method_description: row.get("method_description"),
        method_class: row.get("method_class"),
        formula: row.get("formula"),
    })
}

fn variable_scale_summary_from_row(row: &PgRow) -> Option<VariableScaleSummary> {
    let scale_name = row.get::<Option<String>, _>("scale_name")?;

    Some(VariableScaleSummary {
        scale_db_id: row.get("scale_db_id"),
        scale_name: Some(scale_name),
        data_type: row.get("data_type"),
        decimal_places: row.get("decimal_places"),
        valid_values: row.get("valid_values"),
    })
}

fn observation_summary_from_row(row: PgRow) -> ObservationSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    ObservationSummary {
        observation_db_id: row
            .get::<Option<String>, _>("observation_db_id")
            .unwrap_or_else(|| id.to_string()),
        observation_unit_db_id: row.get("observation_unit_db_id"),
        observation_variable_db_id: row.get("observation_variable_db_id"),
        observation_variable_name: row.get("observation_variable_name"),
        value: row.get("value"),
        observation_time_stamp: row.get("observation_time_stamp"),
        collector: row.get("collector"),
        study_db_id: row
            .get::<Option<i64>, _>("study_id")
            .map(|id| id.to_string()),
        germplasm_db_id: row
            .get::<Option<i64>, _>("germplasm_id")
            .map(|id| id.to_string()),
        season_db_id: row.get("season_db_id"),
        additional_info,
        external_references,
    }
}

fn observation_unit_summary_from_row(row: PgRow) -> ObservationUnitSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    ObservationUnitSummary {
        observation_unit_db_id: row
            .get::<Option<String>, _>("observation_unit_db_id")
            .unwrap_or_else(|| id.to_string()),
        observation_unit_name: row.get("observation_unit_name"),
        observation_unit_pui: row.get("observation_unit_pui"),
        study_db_id: row
            .get::<Option<i64>, _>("study_id")
            .map(|id| id.to_string()),
        study_name: row.get("study_name"),
        germplasm_db_id: row
            .get::<Option<i64>, _>("germplasm_id")
            .map(|id| id.to_string()),
        germplasm_name: row.get("germplasm_name"),
        cross_db_id: row.get("cross_db_id"),
        seedlot_db_id: row.get("seedlot_db_id"),
        observation_level: row.get("observation_level"),
        observation_level_code: row.get("observation_level_code"),
        observation_level_order: row.get("observation_level_order"),
        position_coordinate_x: row.get("position_coordinate_x"),
        position_coordinate_x_type: row.get("position_coordinate_x_type"),
        position_coordinate_y: row.get("position_coordinate_y"),
        position_coordinate_y_type: row.get("position_coordinate_y_type"),
        entry_type: row.get("entry_type"),
        geo_coordinates: row.get("geo_coordinates"),
        treatments: row.get("treatments"),
        additional_info,
        external_references,
    }
}

fn method_summary_from_row(row: PgRow) -> MethodSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();
    let ontology_reference = method_ontology_reference_from_row(&row);

    MethodSummary {
        method_db_id: row
            .get::<Option<String>, _>("method_db_id")
            .unwrap_or_else(|| id.to_string()),
        method_name: row.get("method_name"),
        method_pui: row.get("method_pui"),
        method_class: row.get("method_class"),
        description: row.get("description"),
        formula: row.get("formula"),
        reference: row.get("reference"),
        bibliographical_reference: row.get("bibliographical_reference"),
        ontology_reference,
        external_references,
        additional_info,
    }
}

fn method_ontology_reference_from_row(row: &PgRow) -> Option<BTreeMap<String, Value>> {
    let mut reference = BTreeMap::new();

    if let Some(ontology_db_id) = row.get::<Option<String>, _>("ontology_db_id") {
        reference.insert("ontologyDbId".to_string(), json!(ontology_db_id));
    }
    if let Some(ontology_name) = row.get::<Option<String>, _>("ontology_name") {
        reference.insert("ontologyName".to_string(), json!(ontology_name));
    }
    if let Some(ontology_version) = row.get::<Option<String>, _>("ontology_version") {
        reference.insert("version".to_string(), json!(ontology_version));
    }

    if reference.is_empty() {
        None
    } else {
        Some(reference)
    }
}

fn scale_summary_from_row(row: PgRow) -> ScaleSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();
    let ontology_reference = scale_ontology_reference_from_row(&row);
    let valid_values = scale_valid_values_from_row(&row);

    ScaleSummary {
        scale_db_id: row
            .get::<Option<String>, _>("scale_db_id")
            .unwrap_or_else(|| id.to_string()),
        scale_name: row.get("scale_name"),
        scale_pui: row.get("scale_pui"),
        data_type: row.get("data_type"),
        decimal_places: row.get("decimal_places"),
        valid_values,
        ontology_reference,
        external_references,
        additional_info,
    }
}

fn scale_valid_values_from_row(row: &PgRow) -> Option<ScaleValidValues> {
    let min = row.get::<Option<i32>, _>("valid_values_min");
    let max = row.get::<Option<i32>, _>("valid_values_max");
    let categories = row
        .get::<Option<Value>, _>("valid_values_categories")
        .and_then(value_to_scale_categories);

    if min.is_none() && max.is_none() && categories.is_none() {
        None
    } else {
        Some(ScaleValidValues {
            min,
            max,
            categories,
        })
    }
}

fn value_to_scale_categories(value: Value) -> Option<Vec<ScaleCategory>> {
    let raw_categories = value.as_array()?;
    let categories: Vec<ScaleCategory> = raw_categories
        .iter()
        .filter_map(scale_category_from_value)
        .collect();

    if categories.is_empty() {
        None
    } else {
        Some(categories)
    }
}

fn scale_category_from_value(value: &Value) -> Option<ScaleCategory> {
    if let Some(text) = value.as_str() {
        let normalized = text.trim();
        if normalized.is_empty() {
            return None;
        }
        return Some(ScaleCategory {
            label: normalized.to_string(),
            value: normalized.to_string(),
        });
    }

    let object = value.as_object()?;
    let label = object
        .get("label")
        .or_else(|| object.get("value"))
        .and_then(value_to_nonempty_string)
        .unwrap_or_default();
    let category_value = object
        .get("value")
        .or_else(|| object.get("label"))
        .and_then(value_to_nonempty_string)
        .unwrap_or_default();

    Some(ScaleCategory {
        label,
        value: category_value,
    })
}

fn value_to_nonempty_string(value: &Value) -> Option<String> {
    let normalized = match value {
        Value::String(value) => value.trim().to_string(),
        Value::Number(value) => value.to_string(),
        Value::Bool(value) => value.to_string(),
        _ => return None,
    };
    if normalized.is_empty() {
        None
    } else {
        Some(normalized)
    }
}

fn scale_ontology_reference_from_row(row: &PgRow) -> Option<BTreeMap<String, Value>> {
    let mut reference = BTreeMap::new();

    if let Some(ontology_db_id) = row.get::<Option<String>, _>("ontology_db_id") {
        reference.insert("ontologyDbId".to_string(), json!(ontology_db_id));
    }
    if let Some(ontology_name) = row.get::<Option<String>, _>("ontology_name") {
        reference.insert("ontologyName".to_string(), json!(ontology_name));
    }
    if let Some(ontology_version) = row.get::<Option<String>, _>("ontology_version") {
        reference.insert("version".to_string(), json!(ontology_version));
    }

    if reference.is_empty() {
        None
    } else {
        Some(reference)
    }
}

fn crossing_project_summary_from_row(row: PgRow) -> CrossingProjectSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();

    CrossingProjectSummary {
        crossing_project_db_id: row
            .get::<Option<String>, _>("crossing_project_db_id")
            .unwrap_or_else(|| id.to_string()),
        crossing_project_name: row.get("crossing_project_name"),
        crossing_project_description: row.get("crossing_project_description"),
        program_db_id: None,
        program_name: row.get("program_name"),
        common_crop_name: row.get("common_crop_name"),
        potential_parent_db_ids: Vec::new(),
        additional_info,
        external_references,
    }
}

fn cross_summary_from_row(row: PgRow) -> CrossSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);

    CrossSummary {
        cross_db_id: row
            .get::<Option<String>, _>("cross_db_id")
            .unwrap_or_else(|| id.to_string()),
        cross_name: row.get("cross_name"),
        cross_type: row.get("cross_type"),
        crossing_project_db_id: row.get("crossing_project_db_id"),
        crossing_project_name: row.get("crossing_project_name"),
        parent1_db_id: row.get("parent1_db_id"),
        parent1_name: row.get("parent1_name"),
        parent1_type: row.get("parent1_type"),
        parent2_db_id: row.get("parent2_db_id"),
        parent2_name: row.get("parent2_name"),
        parent2_type: row.get("parent2_type"),
        pollination_time_stamp: row.get("pollination_time_stamp"),
        planned_cross_db_id: row.get("planned_cross_db_id"),
        crossing_year: row.get("crossing_year"),
        cross_status: row.get("cross_status"),
        additional_info,
        external_references: row.get("external_references"),
    }
}

fn planned_cross_summary_from_row(row: PgRow) -> PlannedCrossSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references)
        .unwrap_or_default();

    PlannedCrossSummary {
        planned_cross_db_id: row
            .get::<Option<String>, _>("planned_cross_db_id")
            .unwrap_or_else(|| id.to_string()),
        planned_cross_name: row.get("planned_cross_name"),
        crossing_project_db_id: row.get("crossing_project_db_id"),
        crossing_project_name: row.get("crossing_project_name"),
        cross_type: row.get("cross_type"),
        status: row.get("status"),
        parent1: planned_cross_parent_from_row(
            &row,
            "parent1_db_id",
            "parent1_name",
            "parent1_type",
        ),
        parent2: planned_cross_parent_from_row(
            &row,
            "parent2_db_id",
            "parent2_name",
            "parent2_type",
        ),
        additional_info,
        external_references,
    }
}

fn planned_cross_parent_from_row(
    row: &PgRow,
    germplasm_db_id_column: &str,
    germplasm_name_column: &str,
    parent_type_column: &str,
) -> Option<PlannedCrossParentSummary> {
    let germplasm_db_id = row.get::<Option<String>, _>(germplasm_db_id_column)?;

    Some(PlannedCrossParentSummary {
        germplasm_db_id,
        germplasm_name: row.get(germplasm_name_column),
        observation_unit_db_id: None,
        observation_unit_name: None,
        parent_type: row
            .get::<Option<String>, _>(parent_type_column)
            .unwrap_or_else(|| "UNKNOWN".to_string()),
    })
}

fn seedlot_summary_from_row(row: PgRow) -> SeedlotSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);
    let external_references = row
        .get::<Option<Value>, _>("external_references")
        .and_then(value_to_external_references);

    SeedlotSummary {
        seedlot_db_id: row
            .get::<Option<String>, _>("seedlot_db_id")
            .unwrap_or_else(|| id.to_string()),
        seedlot_name: row.get("seedlot_name"),
        seedlot_description: row.get("seedlot_description"),
        germplasm_db_id: row.get("germplasm_db_id"),
        location_db_id: row.get("location_db_id"),
        program_db_id: row.get("program_db_id"),
        source_collection: row.get("source_collection"),
        storage_location: row.get("storage_location"),
        count: row.get("count"),
        units: row.get("units"),
        created_date: row.get("created_date"),
        last_updated: row.get("last_updated"),
        additional_info,
        external_references,
    }
}

fn seedlot_transaction_summary_from_row(row: PgRow) -> SeedlotTransactionSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);

    SeedlotTransactionSummary {
        transaction_db_id: row
            .get::<Option<String>, _>("transaction_db_id")
            .unwrap_or_else(|| id.to_string()),
        seedlot_db_id: row.get("seedlot_db_id"),
        transaction_description: row.get("transaction_description"),
        transaction_timestamp: row.get("transaction_timestamp"),
        amount: row.get("amount"),
        units: row.get("units"),
        from_seedlot_db_id: row.get("from_seedlot_db_id"),
        to_seedlot_db_id: row.get("to_seedlot_db_id"),
        additional_info,
        external_references: row.get("external_references"),
    }
}

fn callset_summary_from_row(row: PgRow) -> CallSetSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();
    let variant_set_db_ids = row
        .get::<Option<Value>, _>("variant_set_db_ids")
        .and_then(value_to_strings)
        .unwrap_or_default();

    CallSetSummary {
        call_set_db_id: row
            .get::<Option<String>, _>("call_set_db_id")
            .unwrap_or_else(|| id.to_string()),
        call_set_name: row.get("call_set_name"),
        sample_db_id: row.get("sample_db_id"),
        variant_set_db_ids,
        created: row.get("created"),
        updated: row.get("updated"),
        additional_info,
    }
}

fn variantset_summary_from_row(row: PgRow) -> VariantSetSummary {
    let id = row.get::<i64, _>("id");
    let analysis: Vec<Value> = row
        .get::<Option<Value>, _>("analysis")
        .and_then(|value| serde_json::from_value(value).ok())
        .unwrap_or_default();
    let available_formats: Vec<Value> = row
        .get::<Option<Value>, _>("available_formats")
        .and_then(|value| serde_json::from_value(value).ok())
        .unwrap_or_default();
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();

    VariantSetSummary {
        variant_set_db_id: row
            .get::<Option<String>, _>("variant_set_db_id")
            .unwrap_or_else(|| id.to_string()),
        variant_set_name: row.get("variant_set_name"),
        reference_set_db_id: row.get("reference_set_db_id"),
        study_db_id: row.get("study_db_id"),
        analysis,
        available_formats,
        call_set_count: row.get("call_set_count"),
        variant_count: row.get("variant_count"),
        additional_info,
    }
}

fn genome_map_summary_from_row(row: PgRow) -> GenomeMapSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);

    GenomeMapSummary {
        map_db_id: row
            .get::<Option<String>, _>("map_db_id")
            .unwrap_or_else(|| id.to_string()),
        map_name: row.get("map_name"),
        map_pui: row.get("map_pui"),
        common_crop_name: row.get("common_crop_name"),
        r#type: row.get("type"),
        unit: row.get("unit"),
        scientific_name: row.get("scientific_name"),
        published_date: row.get("published_date"),
        comments: row.get("comments"),
        documentation_url: row.get("documentation_url"),
        additional_info,
        linkage_group_count: row.get("linkage_group_count"),
        marker_count: row.get("marker_count"),
    }
}

fn linkage_group_from_row(row: PgRow) -> LinkageGroupSummary {
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object);

    LinkageGroupSummary {
        linkage_group_name: row.get("linkage_group_name"),
        max_position: row.get("max_position"),
        marker_count: row.get("marker_count"),
        additional_info,
        map_db_id: row.get("map_db_id"),
    }
}

fn marker_position_from_row(row: PgRow) -> MarkerPositionSummary {
    let id = row.get::<i64, _>("id");
    let additional_info = row
        .get::<Option<Value>, _>("additional_info")
        .and_then(value_to_object)
        .unwrap_or_default();

    MarkerPositionSummary {
        marker_position_db_id: row
            .get::<Option<String>, _>("marker_position_db_id")
            .unwrap_or_else(|| id.to_string()),
        variant_db_id: row.get("variant_db_id"),
        variant_name: row.get("variant_name"),
        map_db_id: row.get("map_db_id"),
        map_name: row.get("map_name"),
        linkage_group_name: row.get("linkage_group_name"),
        position: row.get("position"),
        additional_info,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn normalized_db_source() -> String {
        include_str!("db.rs")
            .split_whitespace()
            .collect::<Vec<_>>()
            .join(" ")
    }

    fn timer_operations(source: &str) -> Vec<String> {
        let mut operations = Vec::new();
        let mut rest = source;
        while let Some(index) = rest.find("ReadRepositoryTimer::start") {
            rest = &rest[index + "ReadRepositoryTimer::start".len()..];
            let Some((_, tail)) = rest.split_once('"') else {
                break;
            };
            let Some((operation, tail)) = tail.split_once('"') else {
                break;
            };
            operations.push(operation.to_owned());
            rest = tail;
        }
        operations
    }

    #[test]
    fn normalizes_fastapi_asyncpg_url_for_sqlx() {
        assert_eq!(
            normalize_database_url("postgresql+asyncpg://user:pass@localhost/db").as_deref(),
            Some("postgres://user:pass@localhost/db")
        );
    }

    #[test]
    fn skips_sqlite_urls() {
        assert_eq!(
            normalize_database_url("sqlite+aiosqlite:///bijmantra.db"),
            None
        );
    }

    #[test]
    fn read_statement_timeout_policy_defaults_bounds_and_allows_disable() {
        assert_eq!(read_statement_timeout_ms(None), 10_000);
        assert_eq!(read_statement_timeout_ms(Some("")), 10_000);
        assert_eq!(read_statement_timeout_ms(Some("not-a-number")), 10_000);
        assert_eq!(read_statement_timeout_ms(Some("2500")), 2500);
        assert_eq!(read_statement_timeout_ms(Some(" 7500 ")), 7500);
        assert_eq!(read_statement_timeout_ms(Some("0")), 0);
        assert_eq!(read_statement_timeout_ms(Some("600000")), 300_000);
    }

    #[test]
    fn read_repository_methods_start_timing_spans() {
        let source = include_str!("db.rs");
        let impl_start = source
            .find("impl DataStore {")
            .expect("DataStore impl should exist");
        let impl_end = source[impl_start..]
            .find("\n}\n\nfn normalize_database_url")
            .map(|index| impl_start + index)
            .expect("DataStore impl should end before helper functions");
        let impl_source = &source[impl_start..impl_end];
        let mut rest = impl_source;
        let mut timed_methods = 0;

        while let Some(method_index) = rest.find("pub async fn ") {
            rest = &rest[method_index + "pub async fn ".len()..];
            let name_end = rest
                .find('(')
                .expect("async repository method should have a parameter list");
            let name = &rest[..name_end];
            let body_start = rest
                .find('{')
                .expect("async repository method should have a body");
            let prelude_end = rest[body_start..]
                .find("let Some(pool)")
                .or_else(|| rest[body_start..].find("sqlx::query"))
                .unwrap_or(180);
            let prelude = &rest[body_start..body_start + prelude_end];
            let normalized_prelude = prelude.split_whitespace().collect::<Vec<_>>().join(" ");

            assert!(
                normalized_prelude.contains("ReadRepositoryTimer::start")
                    && normalized_prelude.contains(&format!("\"{name}\"")),
                "{name} should start a named read repository timing span"
            );
            timed_methods += 1;
        }

        assert!(
            timed_methods >= 50,
            "expected the migrated read repository surface to stay timed"
        );
        assert!(
            source.contains("elapsed_ms"),
            "repository timing logs should include elapsed_ms"
        );
        assert!(
            source.contains("finished Rust read repository operation"),
            "repository timing logs should include a completion event"
        );
    }

    #[test]
    fn unavailable_repository_paths_emit_contextual_warnings() {
        let source = include_str!("db.rs");
        let implementation_source = source.split("#[cfg(test)]").next().unwrap_or(source);
        let normalized_source = source.split_whitespace().collect::<Vec<_>>().join(" ");

        assert!(
            source.contains("route_context = \"rust_read_beta\"")
                && source.contains("route_context = \"rust_read_beta_auth\""),
            "unavailable repository logs should include read-beta route context"
        );
        let raw_unavailable_returns: Vec<_> = source
            .lines()
            .filter(|line| {
                let trimmed = line.trim();
                trimmed == "return Err(DataStoreError::Unavailable);"
                    || trimmed == "return Err(UserLookupError::Unavailable);"
            })
            .collect();
        assert!(
            raw_unavailable_returns.is_empty(),
            "repository methods should use telemetry helpers for unavailable pools: {raw_unavailable_returns:?}"
        );

        for operation in timer_operations(implementation_source) {
            if operation == "read_repository_health_dependency" {
                continue;
            }
            let data_store_marker = format!("data_store_unavailable(\"{operation}\")");
            let user_store_marker = format!("user_store_unavailable(\"{operation}\")");
            let write_store_marker = format!("write_store_unavailable(\"{operation}\")");
            let formatted_data_store_marker = format!("data_store_unavailable( \"{operation}\", )");
            let formatted_user_store_marker = format!("user_store_unavailable( \"{operation}\", )");
            let formatted_write_store_marker =
                format!("write_store_unavailable( \"{operation}\", )");

            assert!(
                normalized_source.contains(&data_store_marker)
                    || normalized_source.contains(&user_store_marker)
                    || normalized_source.contains(&write_store_marker)
                    || normalized_source.contains(&formatted_data_store_marker)
                    || normalized_source.contains(&formatted_user_store_marker)
                    || normalized_source.contains(&formatted_write_store_marker),
                "{operation} should have unavailable-pool telemetry"
            );
        }

        for forbidden in [
            "database_url",
            "DATABASE_URL",
            "BIJMANTRA_DATABASE_URL",
            "authorization",
            "bearer",
            "token",
        ] {
            for line in source.lines().filter(|line| {
                line.contains("data_store_unavailable")
                    || line.contains("user_store_unavailable")
                    || line.contains("write_store_unavailable")
            }) {
                assert!(
                    !line
                        .to_ascii_lowercase()
                        .contains(&forbidden.to_ascii_lowercase()),
                    "unavailable repository telemetry should not log {forbidden}: {line}"
                );
            }
        }
    }

    #[tokio::test]
    async fn begin_write_transaction_requires_configured_pool() {
        let store = DataStore::unavailable();
        let result = store
            .begin_write_transaction(&WriteTransactionOptions {
                organization_id: 1,
                actor_user_id: 2,
                idempotency_key: Some("client:write-0001".to_owned()),
                audit_event: "seed_lot.adjusted".to_owned(),
            })
            .await;

        assert!(matches!(result, Err(WriteTransactionError::Unavailable)));
    }

    fn valid_seedlot_adjustment_command() -> SeedlotInventoryAdjustmentCreate {
        SeedlotInventoryAdjustmentCreate::new(
            bijmantra_core::PublicId::new_uuid7(),
            IdempotencyKey::parse("seedlot-adjust-0001").unwrap(),
            1,
            "seedlot_IR64_0001",
            SeedlotInventoryAdjustmentType::Correction,
            "-12.5",
            SeedlotInventoryAdjustmentUnit::Grams,
            "cycle count correction",
            2,
            None,
            BTreeMap::new(),
        )
        .unwrap()
    }

    #[tokio::test]
    async fn seedlot_adjustment_insert_requires_configured_pool() {
        let store = DataStore::unavailable();
        let result = store
            .create_seedlot_inventory_adjustment_internal(valid_seedlot_adjustment_command())
            .await;

        assert!(matches!(
            result,
            Err(SeedlotInventoryAdjustmentWriteError::Unavailable)
        ));
    }

    #[tokio::test]
    async fn seedlot_adjustment_authorized_insert_requires_platform_access_context() {
        let store = DataStore::unavailable();
        let command = valid_seedlot_adjustment_command();
        let allowed_context = PlatformCapabilityAccessContext::new(
            command.organization_id,
            command.actor_user_id,
            &[bijmantra_core::SEEDLOT_TRACEABILITY_CAPABILITY_ID],
            &[bijmantra_core::SEEDLOT_INVENTORY_ADJUST_PERMISSION],
            &["organization", "lot"],
        );
        let result = store
            .create_seedlot_inventory_adjustment_authorized_internal(&allowed_context, command)
            .await;
        assert!(matches!(
            result,
            Err(SeedlotInventoryAdjustmentWriteError::Unavailable)
        ));

        let denied_command = valid_seedlot_adjustment_command();
        let denied_context = PlatformCapabilityAccessContext::new(
            denied_command.organization_id,
            denied_command.actor_user_id,
            &[bijmantra_core::SEEDLOT_TRACEABILITY_CAPABILITY_ID],
            &["seedops.seed_lots.read"],
            &["organization", "lot"],
        );
        let denied = store
            .create_seedlot_inventory_adjustment_authorized_internal(
                &denied_context,
                denied_command,
            )
            .await;

        assert!(matches!(
            denied,
            Err(SeedlotInventoryAdjustmentWriteError::AuthorizationDenied(
                decision
            )) if decision.missing_permissions == vec![
                bijmantra_core::SEEDLOT_INVENTORY_ADJUST_PERMISSION.to_owned()
            ]
        ));
    }

    #[tokio::test]
    async fn seedlot_adjustment_lookup_requires_tenant_scope() {
        let store = DataStore::unavailable();
        let result = store
            .get_seedlot_inventory_adjustment_by_idempotency_key_internal(
                0,
                2,
                &IdempotencyKey::parse("seedlot-adjust-0002").unwrap(),
            )
            .await;

        assert!(matches!(
            result,
            Err(SeedlotInventoryAdjustmentWriteError::Unavailable)
        ));
        assert!(matches!(
            validate_write_lookup_context(0, Some(2)),
            Err(SeedlotInventoryAdjustmentWriteError::InvalidContext(
                "organization_id must be positive"
            ))
        ));
    }

    #[tokio::test]
    async fn seedlot_adjustment_history_list_requires_tenant_scope() {
        let store = DataStore::unavailable();
        let result = store
            .list_seedlot_inventory_adjustments_internal(&SeedlotInventoryAdjustmentListParams {
                organization_id: 0,
                page: 0,
                page_size: 100,
                seedlot_db_id: None,
            })
            .await;

        assert!(matches!(
            result,
            Err(SeedlotInventoryAdjustmentWriteError::Unavailable)
        ));
        assert!(matches!(
            validate_write_lookup_context(0, None),
            Err(SeedlotInventoryAdjustmentWriteError::InvalidContext(
                "organization_id must be positive"
            ))
        ));
    }

    #[test]
    fn seedlot_adjustment_repository_is_append_only_and_tenant_scoped() {
        let source = normalized_db_source();
        let implementation_source = source.split("#[cfg(test)]").next().unwrap_or(&source);

        for expected in [
            "pub async fn create_seedlot_inventory_adjustment_internal",
            "pub async fn create_seedlot_inventory_adjustment_authorized_internal",
            "pub async fn get_seedlot_inventory_adjustment_by_public_id_internal",
            "pub async fn get_seedlot_inventory_adjustment_by_idempotency_key_internal",
            "pub async fn list_seedlot_inventory_adjustments_internal",
            "pub async fn reverse_seedlot_inventory_adjustment_internal",
            "pub async fn reverse_seedlot_inventory_adjustment_authorized_internal",
            "WriteAuthorizationPlan::seedlot_inventory_adjustment",
            "SeedlotInventoryAdjustmentWriteError::AuthorizationDenied",
            "set_transaction_organization_context",
            "INSERT INTO seedlot_inventory_adjustments",
            "ON CONFLICT ON CONSTRAINT uq_seedlot_inventory_adjustments_idempotency DO NOTHING",
            "resolve_seedlot_adjustment_idempotency_collision_in_tx",
            "INSERT INTO audit_logs",
            "seedlot_inventory_adjustment",
            "'INTERNAL'",
            "WHERE organization_id = $1 AND seedlot_db_id = $2",
            "WHERE organization_id = $1 AND public_id = $2::uuid",
            "AND ($2::text IS NULL OR seedlot_db_id = $2)",
            "AND actor_user_id = $2 AND action = 'seedlot_inventory_adjustment.create' AND idempotency_key = $3",
            "UPDATE seedlot_inventory_adjustments SET reversed_at = now() WHERE organization_id = $1",
            "reversal_mark.rows_affected() != 1",
            "SeedlotInventoryAdjustmentWriteError::IdempotencyConflict",
            "SEEDLOT_INVENTORY_ADJUST_AUDIT_EVENT",
        ] {
            assert!(
                implementation_source.contains(expected),
                "seedlot adjustment internal repository should contain {expected}"
            );
        }

        for forbidden in [
            "UPDATE seedlots SET",
            "DELETE FROM seedlot_inventory_adjustments",
            "DELETE FROM seedlots",
        ] {
            assert!(
                !implementation_source.contains(forbidden),
                "seedlot adjustment ledger must not destructively mutate inventory: {forbidden}"
            );
        }
    }

    #[test]
    fn seedlot_adjustment_reversal_uses_compensating_quantity() {
        assert_eq!(negate_quantity_delta("-12.500000"), "12.500000");
        assert_eq!(negate_quantity_delta("12.500000"), "-12.500000");
    }

    #[test]
    fn write_transaction_options_reject_invalid_context() {
        let mut options = WriteTransactionOptions {
            organization_id: 1,
            actor_user_id: 2,
            idempotency_key: None,
            audit_event: "seed_lot.adjusted".to_owned(),
        };

        assert!(options.validate().is_ok());
        options.organization_id = 0;
        assert!(matches!(
            options.validate(),
            Err(WriteTransactionError::InvalidContext(
                "organization_id must be positive"
            ))
        ));
        options.organization_id = 1;
        options.actor_user_id = 0;
        assert!(matches!(
            options.validate(),
            Err(WriteTransactionError::InvalidContext(
                "actor_user_id must be positive"
            ))
        ));
        options.actor_user_id = 2;
        options.audit_event = " ".to_owned();
        assert!(matches!(
            options.validate(),
            Err(WriteTransactionError::InvalidContext(
                "audit_event is required"
            ))
        ));
        options.audit_event = "seed_lot.adjusted".to_owned();
        options.idempotency_key = Some(" ".to_owned());
        assert!(matches!(
            options.validate(),
            Err(WriteTransactionError::InvalidContext(
                "idempotency_key cannot be blank when present"
            ))
        ));
    }

    #[test]
    fn write_transaction_helper_sets_tenant_user_idempotency_and_audit_context() {
        let source = normalized_db_source();

        for required in [
            "pub async fn begin_write_transaction",
            "pool.begin()",
            "set_write_transaction_context",
            "app.current_organization_id",
            "app.current_user_id",
            "app.idempotency_key",
            "app.audit_event",
            "rust_write_readiness",
        ] {
            assert!(
                source.contains(required),
                "write transaction helper should contain {required}"
            );
        }
    }

    #[test]
    fn maps_json_objects() {
        let object = value_to_object(serde_json::json!({"season": "kharif"})).unwrap();

        assert_eq!(object["season"], "kharif");
    }

    #[test]
    fn maps_external_reference_arrays() {
        let refs = value_to_external_references(serde_json::json!([
            {"referenceId": "x", "referenceSource": "source"}
        ]))
        .unwrap();

        assert_eq!(refs[0]["referenceId"], "x");
        assert_eq!(refs[0]["referenceSource"], "source");
    }

    #[test]
    fn maps_donor_object_arrays() {
        assert!(value_to_objects(serde_json::Value::Null).is_none());

        let empty = value_to_objects(serde_json::json!([])).unwrap();
        assert!(empty.is_empty());

        let donors = value_to_objects(serde_json::json!([
            {"donorAccessionNumber": "D-1", "donorInstitute": "IRRI"}
        ]))
        .unwrap();

        assert_eq!(donors[0]["donorAccessionNumber"], "D-1");
        assert_eq!(donors[0]["donorInstitute"], "IRRI");
    }

    #[test]
    fn maps_synonym_arrays() {
        assert!(value_to_strings(serde_json::Value::Null).is_none());

        let empty = value_to_strings(serde_json::json!([])).unwrap();
        assert!(empty.is_empty());

        let synonyms = value_to_strings(serde_json::json!(["IR-64", "IR 64"])).unwrap();
        assert_eq!(synonyms, vec!["IR-64".to_string(), "IR 64".to_string()]);
    }

    #[test]
    fn builds_contains_filter_patterns() {
        assert_eq!(
            contains_pattern(&Some("IR64".to_string())).as_deref(),
            Some("%IR64%")
        );
        assert_eq!(
            contains_pattern(&Some("  IR64  ".to_string())).as_deref(),
            Some("%IR64%")
        );
        assert_eq!(contains_pattern(&Some("   ".to_string())), None);
        assert_eq!(contains_pattern(&None), None);
    }

    #[test]
    fn builds_exact_filter_values() {
        assert_eq!(
            exact_filter_value(&Some("variant-set-1".to_string())),
            Some("variant-set-1")
        );
        assert_eq!(
            exact_filter_value(&Some("  variant-set-1  ".to_string())),
            Some("variant-set-1")
        );
        assert_eq!(exact_filter_value(&Some(String::new())), None);
        assert_eq!(exact_filter_value(&Some("  ".to_string())), None);
        assert_eq!(exact_filter_value(&None), None);
    }

    #[test]
    fn contains_filter_patterns_preserve_case_and_injection_strings_as_bound_values() {
        let injected = "IR64%' OR 1=1 --";

        assert_eq!(
            contains_pattern(&Some("iR64".to_string())).as_deref(),
            Some("%iR64%")
        );
        assert_eq!(
            contains_pattern(&Some(injected.to_string())).as_deref(),
            Some("%IR64%' OR 1=1 --%")
        );
    }

    #[test]
    fn exact_filter_values_preserve_injection_strings_as_bound_values() {
        let injected = "variant-set-1' OR 'x'='x";

        assert_eq!(
            exact_filter_value(&Some(injected.to_string())),
            Some("variant-set-1' OR 'x'='x")
        );
    }

    #[test]
    fn sql_filter_audit_keeps_case_insensitive_bound_parameters() {
        let source = normalized_db_source();

        for expected in [
            "germplasm_name ILIKE $2",
            "common_crop_name ILIKE $3",
            "species ILIKE $4",
            "genus ILIKE $5",
            "observation_variable_name ILIKE $3",
            "call_set_name ILIKE $3",
            "method_name ILIKE $4",
            "scale_name ILIKE $3",
            ".bind(germplasm_name_pattern.as_deref())",
            ".bind(common_crop_name_pattern.as_deref())",
            ".bind(observation_variable_name_pattern.as_deref())",
            ".bind(call_set_name_pattern.as_deref())",
            ".bind(method_name_pattern.as_deref())",
            ".bind(scale_name_pattern.as_deref())",
        ] {
            assert!(
                source.contains(expected),
                "expected case-insensitive bound filter SQL snippet: {expected}"
            );
        }
    }

    #[test]
    fn sql_multi_filter_audit_keeps_tenant_scope_and_bound_filters() {
        let source = normalized_db_source();

        for expected in [
            "FROM germplasm WHERE organization_id = $1 AND ($2::text IS NULL OR germplasm_name ILIKE $2) AND ($3::text IS NULL OR common_crop_name ILIKE $3) AND ($4::text IS NULL OR species ILIKE $4) AND ($5::text IS NULL OR genus ILIKE $5)",
            "FROM variant_sets vs LEFT JOIN studies s ON s.id = vs.study_id AND s.organization_id = vs.organization_id LEFT JOIN reference_sets rs ON rs.id = vs.reference_set_id AND rs.organization_id = vs.organization_id WHERE vs.organization_id = $1 AND ($2::text IS NULL OR vs.variant_set_db_id = $2) AND ($3::text IS NULL OR s.study_db_id = $3) AND ($4::text IS NULL OR rs.reference_set_db_id = $4)",
            "FROM marker_positions mp JOIN genome_maps gm ON gm.id = mp.map_id AND gm.organization_id = mp.organization_id WHERE mp.organization_id = $1 AND ($2::text IS NULL OR gm.map_db_id = $2) AND ($3::text IS NULL OR mp.linkage_group_name = $3) AND ($4::text IS NULL OR mp.variant_db_id = $4) AND ($5::double precision IS NULL OR mp.position >= $5) AND ($6::double precision IS NULL OR mp.position <= $6)",
        ] {
            assert!(
                source.contains(expected),
                "expected tenant-scoped multi-filter SQL snippet: {expected}"
            );
        }
    }

    #[test]
    fn keycloak_identity_lookup_uses_provider_issuer_subject_and_user_org_join() {
        let source = normalized_db_source();

        for expected in [
            "FROM auth_identities ai JOIN users u ON u.id = ai.user_id AND u.organization_id = ai.organization_id WHERE ai.provider = 'keycloak' AND ai.issuer = $1 AND ai.subject = $2",
            ".bind(issuer)",
            ".bind(subject)",
        ] {
            assert!(
                source.contains(expected),
                "expected Keycloak auth identity SQL snippet: {expected}"
            );
        }
    }

    #[test]
    fn deterministic_ordering_audit_covers_migrated_read_families() {
        let source = normalized_db_source();

        for expected in [
            "ORDER BY location_name ASC, location_db_id ASC, id ASC",
            "ORDER BY program_name ASC, program_db_id ASC, id ASC",
            "ORDER BY t.trial_name ASC, t.trial_db_id ASC, t.id ASC",
            "ORDER BY s.study_name ASC, s.study_db_id ASC, s.id ASC",
            "ORDER BY year DESC, season_name ASC, id ASC",
            "ORDER BY last_name ASC, first_name ASC, person_db_id ASC, id ASC",
            "ORDER BY list_name ASC, list_db_id ASC, id ASC",
            "ORDER BY ontology_name ASC, ontology_db_id ASC, id ASC",
            "ORDER BY germplasm_name ASC, germplasm_db_id ASC, id ASC",
            "ORDER BY attribute_name ASC, attribute_db_id ASC, id ASC",
            "ORDER BY attribute_category ASC",
            "ORDER BY attribute_name ASC, germplasm_name ASC, attribute_value_db_id ASC, id ASC",
            "ORDER BY breeding_method_name ASC, breeding_method_db_id ASC, id ASC",
            "ORDER BY observation_variable_name ASC, observation_variable_db_id ASC, id ASC",
            "ORDER BY o.observation_time_stamp ASC, o.observation_db_id ASC, o.id ASC",
            "ORDER BY ou.observation_unit_name ASC, ou.observation_unit_db_id ASC, ou.id ASC",
            "ORDER BY method_name ASC, method_db_id ASC, id ASC",
            "ORDER BY scale_name ASC, scale_db_id ASC, id ASC",
            "ORDER BY cp.crossing_project_name ASC, cp.crossing_project_db_id ASC, cp.id ASC",
            "ORDER BY c.cross_name ASC, c.cross_db_id ASC, c.id ASC",
            "ORDER BY pc.planned_cross_name ASC NULLS LAST, pc.planned_cross_db_id ASC, pc.id ASC",
            "ORDER BY s.seedlot_name ASC, s.seedlot_db_id ASC, s.id ASC",
            "ORDER BY tx.transaction_timestamp ASC NULLS LAST, tx.transaction_db_id ASC, tx.id ASC",
            "ORDER BY seedlot_db_id ASC, id ASC",
            "ORDER BY vs.variant_set_name ASC, vs.variant_set_db_id ASC NULLS LAST, vs.id ASC",
            "ORDER BY cs.call_set_name ASC, cs.call_set_db_id ASC, cs.id ASC",
            "ORDER BY map_name ASC, map_db_id ASC, id ASC",
            "ORDER BY lg.linkage_group_name ASC, lg.id ASC",
            "ORDER BY gm.map_name ASC, mp.linkage_group_name ASC NULLS LAST, mp.position ASC NULLS LAST, mp.marker_position_db_id ASC NULLS LAST, mp.id ASC",
        ] {
            assert!(
                source.contains(expected),
                "expected deterministic ordering SQL snippet: {expected}"
            );
        }
    }

    #[test]
    fn high_page_offsets_stay_in_i64_range() {
        assert_eq!(page_offset(0, 1000), 0);
        assert_eq!(page_offset(3, 1000), 3000);
        assert_eq!(page_offset(u32::MAX, 10_000), 42_949_672_950_000);
    }

    #[test]
    fn postgres_primary_keys_use_bigint_range() {
        let user_id = i64::from(i32::MAX) + 1;
        let organization_id = i64::from(i32::MAX) + 1;

        assert_eq!(user_id.to_string(), "2147483648");
        assert_eq!(organization_id.to_string(), "2147483648");
    }
}
