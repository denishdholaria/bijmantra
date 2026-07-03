use std::collections::BTreeMap;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

use axum::body::to_bytes;
use axum::extract::{Path as AxumPath, Query, Request as AxumRequest, State};
use axum::http::header::{AUTHORIZATION, WWW_AUTHENTICATE};
use axum::http::{HeaderMap, HeaderName, HeaderValue, StatusCode};
use axum::middleware::{Next, from_fn};
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use bijmantra_core::{
    ApiMetrics, ApiStats, AttributeSummary, AttributeValueSummary, BrApiCall, BrApiListResponse,
    BrApiServerInfo, BrApiSingleResponse, BreedingMethodSummary, COMMON_CROPS, CallSetSummary,
    CrossSummary, CrossingProjectSummary, DependencyHealth, GenomeMapSummary, GermplasmSummary,
    HealthReport, LinkageGroupSummary, ListSummary, LocationSummary, MarkerPositionSummary,
    MethodSummary, ObservationSummary, ObservationUnitSummary, OntologySummary, PersonSummary,
    PlannedCrossSummary, PlatformCapabilityAccessContext, ProductManifest, ProgramSummary,
    PublicId, ScaleSummary, SeasonSummary, SeedInventorySummary,
    SeedlotInventoryAdjustmentDetailResponse, SeedlotInventoryAdjustmentHistoryMetadata,
    SeedlotInventoryAdjustmentHistoryResponse, SeedlotInventoryAdjustmentRequest,
    SeedlotInventoryAdjustmentResponse, SeedlotSummary, SeedlotTransactionSummary, StudySummary,
    TraitSummary, TrialSummary, VariableSummary, VariantSetSummary, WriteAuthorizationDecision,
    WriteAuthorizationPlan, api_stats, load_api_metrics, rust_brapi_calls,
};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

mod auth;
mod db;

static REQUEST_ID_COUNTER: AtomicU64 = AtomicU64::new(1);

pub use auth::{AuthConfig, AuthError, AuthPrincipal};
pub use db::{
    ActiveUser, AttributeListParams, AttributeValueListParams, BreedingMethodListParams,
    CallSetListParams, CrossListParams, CrossingProjectListParams, DataStore, DataStoreError,
    GenomeMapListParams, GermplasmListParams, LinkageGroupListParams, ListListParams,
    LocationListParams, MarkerPositionListParams, MethodListParams, ObservationListParams,
    ObservationUnitListParams, OntologyListParams, PersonListParams, PlannedCrossListParams,
    ProgramListParams, ScaleListParams, SeasonListParams, SeedlotInventoryAdjustmentListParams,
    SeedlotInventoryAdjustmentWriteError, SeedlotListParams, SeedlotScopedTransactionListParams,
    SeedlotTransactionListParams, StudyListParams, TraitListParams, TrialListParams,
    UserLookupError, VariableListParams, VariantSetListParams, WriteTransactionError,
    WriteTransactionOptions,
};

#[derive(Debug, Clone)]
pub struct AppState {
    workspace_root: PathBuf,
    auth_config: AuthConfig,
    data_store: DataStore,
}

impl AppState {
    pub fn new(workspace_root: impl Into<PathBuf>) -> Self {
        Self {
            workspace_root: workspace_root.into(),
            auth_config: AuthConfig::from_env(),
            data_store: DataStore::from_env(),
        }
    }

    pub fn with_auth_config(mut self, auth_config: AuthConfig) -> Self {
        self.auth_config = auth_config;
        self
    }

    pub fn with_data_store(mut self, data_store: DataStore) -> Self {
        self.data_store = data_store;
        self
    }

    pub fn workspace_root(&self) -> &Path {
        &self.workspace_root
    }

    fn metrics_path(&self) -> PathBuf {
        self.workspace_root.join("metrics.json")
    }
}

#[derive(Debug, Serialize)]
struct RootResponse {
    message: &'static str,
    version: &'static str,
    brapi_version: &'static str,
    docs: &'static str,
}

#[derive(Debug, Deserialize)]
struct ProgramListQuery {
    #[serde(default)]
    page: u32,
    #[serde(
        default = "default_page_size",
        rename = "pageSize",
        alias = "page_size"
    )]
    page_size: u32,
    #[serde(rename = "programName")]
    program_name: Option<String>,
    #[serde(rename = "abbreviation")]
    abbreviation: Option<String>,
    #[serde(rename = "commonCropName")]
    common_crop_name: Option<String>,
}

#[derive(Debug, Deserialize)]
struct LocationListQuery {
    #[serde(default)]
    page: u32,
    #[serde(
        default = "default_page_size",
        rename = "pageSize",
        alias = "page_size"
    )]
    page_size: u32,
    #[serde(rename = "locationType")]
    location_type: Option<String>,
}

#[derive(Debug, Deserialize)]
struct TrialListQuery {
    #[serde(default)]
    page: u32,
    #[serde(
        default = "default_page_size",
        rename = "pageSize",
        alias = "page_size"
    )]
    page_size: u32,
    #[serde(rename = "programDbId")]
    program_db_id: Option<String>,
    active: Option<bool>,
}

#[derive(Debug, Deserialize)]
struct StudyListQuery {
    #[serde(default)]
    page: u32,
    #[serde(
        default = "default_page_size",
        rename = "pageSize",
        alias = "page_size"
    )]
    page_size: u32,
    #[serde(rename = "trialDbId")]
    trial_db_id: Option<String>,
    active: Option<bool>,
}

#[derive(Debug, Deserialize)]
struct SeasonListQuery {
    #[serde(default)]
    page: u32,
    #[serde(
        default = "default_page_size",
        rename = "pageSize",
        alias = "page_size"
    )]
    page_size: u32,
    year: Option<i32>,
    #[serde(rename = "seasonDbId")]
    season_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct PersonListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "firstName")]
    first_name: Option<String>,
    #[serde(rename = "lastName")]
    last_name: Option<String>,
}

#[derive(Debug, Deserialize)]
struct ListListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "listType")]
    list_type: Option<String>,
    #[serde(rename = "listName")]
    list_name: Option<String>,
    #[serde(rename = "listDbId")]
    list_db_id: Option<String>,
    #[serde(rename = "listSource")]
    list_source: Option<String>,
    #[serde(rename = "externalReferenceID")]
    external_reference_id: Option<String>,
    #[serde(rename = "externalReferenceSource")]
    external_reference_source: Option<String>,
}

#[derive(Debug, Deserialize)]
struct OntologyListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "ontologyDbId")]
    ontology_db_id: Option<String>,
    #[serde(rename = "ontologyName")]
    ontology_name: Option<String>,
}

#[derive(Debug, Deserialize)]
struct GermplasmListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "germplasmName")]
    germplasm_name: Option<String>,
    #[serde(rename = "commonCropName")]
    common_crop_name: Option<String>,
    species: Option<String>,
    genus: Option<String>,
}

#[derive(Debug, Deserialize)]
struct AttributeListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "attributeCategory")]
    attribute_category: Option<String>,
    #[serde(rename = "attributeDbId")]
    attribute_db_id: Option<String>,
    #[serde(rename = "attributeName")]
    attribute_name: Option<String>,
    #[serde(rename = "attributePUI")]
    attribute_pui: Option<String>,
    #[serde(rename = "commonCropName")]
    common_crop_name: Option<String>,
    #[serde(rename = "germplasmDbId")]
    germplasm_db_id: Option<String>,
    #[serde(rename = "programDbId")]
    program_db_id: Option<String>,
    #[serde(rename = "traitDbId")]
    trait_db_id: Option<String>,
    #[serde(rename = "methodDbId")]
    method_db_id: Option<String>,
    #[serde(rename = "scaleDbId")]
    scale_db_id: Option<String>,
    #[serde(rename = "externalReferenceID")]
    external_reference_id: Option<String>,
    #[serde(rename = "externalReferenceSource")]
    external_reference_source: Option<String>,
}

#[derive(Debug, Deserialize)]
struct AttributeCategoryListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
}

#[derive(Debug, Deserialize)]
struct AttributeValueListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "attributeDbId")]
    attribute_db_id: Option<String>,
    #[serde(rename = "attributeName")]
    attribute_name: Option<String>,
    #[serde(rename = "attributeValueDbId")]
    attribute_value_db_id: Option<String>,
    #[serde(rename = "germplasmDbId")]
    germplasm_db_id: Option<String>,
    #[serde(rename = "germplasmName")]
    germplasm_name: Option<String>,
    #[serde(rename = "externalReferenceID")]
    external_reference_id: Option<String>,
    #[serde(rename = "externalReferenceSource")]
    external_reference_source: Option<String>,
}

#[derive(Debug, Deserialize)]
struct BreedingMethodListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
}

#[derive(Debug, Deserialize)]
struct TraitListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "traitClass")]
    trait_class: Option<String>,
    #[serde(rename = "observationVariableName")]
    observation_variable_name: Option<String>,
    #[serde(rename = "commonCropName")]
    common_crop_name: Option<String>,
}

#[derive(Debug, Deserialize)]
struct VariableListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "observationVariableDbId")]
    observation_variable_db_id: Option<String>,
    #[serde(rename = "observationVariableName")]
    observation_variable_name: Option<String>,
    #[serde(rename = "traitClass")]
    trait_class: Option<String>,
    #[serde(rename = "commonCropName")]
    common_crop_name: Option<String>,
    #[serde(rename = "methodDbId")]
    method_db_id: Option<String>,
    #[serde(rename = "scaleDbId")]
    scale_db_id: Option<String>,
    #[serde(rename = "ontologyDbId")]
    ontology_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct ObservationListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "studyDbId")]
    study_db_id: Option<String>,
    #[serde(rename = "germplasmDbId")]
    germplasm_db_id: Option<String>,
    #[serde(rename = "observationVariableDbId")]
    observation_variable_db_id: Option<String>,
    #[serde(rename = "observationUnitDbId")]
    observation_unit_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct ObservationUnitListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "studyDbId")]
    study_db_id: Option<String>,
    #[serde(rename = "germplasmDbId")]
    germplasm_db_id: Option<String>,
    #[serde(rename = "observationLevel")]
    observation_level: Option<String>,
    #[serde(rename = "observationUnitDbId")]
    observation_unit_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct MethodListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "methodDbId")]
    method_db_id: Option<String>,
    #[serde(rename = "methodClass")]
    method_class: Option<String>,
    #[serde(rename = "methodName")]
    method_name: Option<String>,
    #[serde(rename = "ontologyDbId")]
    ontology_db_id: Option<String>,
    #[serde(rename = "externalReferenceId")]
    external_reference_id: Option<String>,
    #[serde(rename = "externalReferenceSource")]
    external_reference_source: Option<String>,
}

#[derive(Debug, Deserialize)]
struct ScaleListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "scaleDbId")]
    scale_db_id: Option<String>,
    #[serde(rename = "scaleName")]
    scale_name: Option<String>,
    #[serde(rename = "dataType")]
    data_type: Option<String>,
    #[serde(rename = "ontologyDbId")]
    ontology_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct SeedlotListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "germplasmDbId")]
    germplasm_db_id: Option<String>,
    #[serde(rename = "locationDbId")]
    location_db_id: Option<String>,
    #[serde(rename = "programDbId")]
    program_db_id: Option<String>,
    #[serde(rename = "seedLotDbId")]
    seedlot_db_id: Option<String>,
    #[serde(rename = "seedLotName")]
    seedlot_name: Option<String>,
}

#[derive(Debug, Deserialize)]
struct SeedlotTransactionListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "seedLotDbId")]
    seedlot_db_id: Option<String>,
    #[serde(rename = "transactionDbId")]
    transaction_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct SeedlotScopedTransactionListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
}

#[derive(Debug, Deserialize)]
struct VariantSetListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "variantSetDbId")]
    variant_set_db_id: Option<String>,
    #[serde(rename = "variantDbId")]
    variant_db_id: Option<String>,
    #[serde(rename = "callSetDbId")]
    call_set_db_id: Option<String>,
    #[serde(rename = "referenceSetDbId")]
    reference_set_db_id: Option<String>,
    #[serde(rename = "studyDbId")]
    study_db_id: Option<String>,
    #[serde(rename = "studyName")]
    study_name: Option<String>,
}

#[derive(Debug, Deserialize)]
struct CallSetListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "callSetDbId")]
    call_set_db_id: Option<String>,
    #[serde(rename = "callSetName")]
    call_set_name: Option<String>,
    #[serde(rename = "sampleDbId")]
    sample_db_id: Option<String>,
    #[serde(rename = "variantSetDbId")]
    variant_set_db_id: Option<String>,
    #[serde(rename = "germplasmDbId")]
    germplasm_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct GenomeMapListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "mapDbId")]
    map_db_id: Option<String>,
    #[serde(rename = "mapPUI")]
    map_pui: Option<String>,
    #[serde(rename = "commonCropName")]
    common_crop_name: Option<String>,
    #[serde(rename = "scientificName")]
    scientific_name: Option<String>,
    r#type: Option<String>,
    #[serde(rename = "programDbId")]
    program_db_id: Option<String>,
    #[serde(rename = "trialDbId")]
    trial_db_id: Option<String>,
    #[serde(rename = "studyDbId")]
    study_db_id: Option<String>,
}

#[derive(Debug, Deserialize)]
struct LinkageGroupListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
}

#[derive(Debug, Deserialize)]
struct MarkerPositionListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "mapDbId")]
    map_db_id: Option<String>,
    #[serde(rename = "linkageGroupName")]
    linkage_group_name: Option<String>,
    #[serde(rename = "variantDbId")]
    variant_db_id: Option<String>,
    #[serde(rename = "minPosition")]
    min_position: Option<f64>,
    #[serde(rename = "maxPosition")]
    max_position: Option<f64>,
}

#[derive(Debug, Deserialize)]
struct CrossingProjectListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "crossingProjectDbId")]
    crossing_project_db_id: Option<String>,
    #[serde(rename = "crossingProjectName")]
    crossing_project_name: Option<String>,
    #[serde(rename = "programDbId")]
    program_db_id: Option<String>,
    #[serde(rename = "commonCropName")]
    common_crop_name: Option<String>,
    #[serde(rename = "externalReferenceID")]
    external_reference_id: Option<String>,
    #[serde(rename = "externalReferenceSource")]
    external_reference_source: Option<String>,
}

#[derive(Debug, Deserialize)]
struct CrossListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_people_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "crossingProjectDbId")]
    crossing_project_db_id: Option<String>,
    #[serde(rename = "crossType")]
    cross_type: Option<String>,
    #[serde(rename = "crossDbId")]
    cross_db_id: Option<String>,
    #[serde(rename = "crossName")]
    cross_name: Option<String>,
}

#[derive(Debug, Deserialize)]
struct PlannedCrossListQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_crossing_project_page_size", rename = "pageSize")]
    page_size: u32,
    #[serde(rename = "crossingProjectDbId")]
    crossing_project_db_id: Option<String>,
    #[serde(rename = "crossingProjectName")]
    crossing_project_name: Option<String>,
    #[serde(rename = "plannedCrossDbId")]
    planned_cross_db_id: Option<String>,
    #[serde(rename = "plannedCrossName")]
    planned_cross_name: Option<String>,
    status: Option<String>,
    #[serde(rename = "externalReferenceID")]
    external_reference_id: Option<String>,
    #[serde(rename = "externalReferenceSource")]
    external_reference_source: Option<String>,
}

#[derive(Debug, Deserialize)]
struct CommonCropNamesQuery {
    #[serde(default)]
    page: u32,
    #[serde(default = "default_common_crop_page_size", rename = "pageSize")]
    page_size: u32,
}

#[derive(Debug, Deserialize)]
struct SeedlotInventoryAdjustmentListQuery {
    #[serde(default)]
    page: u32,
    #[serde(
        default = "default_page_size",
        rename = "pageSize",
        alias = "page_size"
    )]
    page_size: u32,
    #[serde(rename = "seedLotDbId", alias = "seedlotDbId", alias = "seedlot_db_id")]
    seedlot_db_id: Option<String>,
}

#[derive(Debug, Serialize)]
struct ErrorDetail {
    detail: &'static str,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct WriteRouteErrorDetail {
    code: &'static str,
    message: String,
    details: Value,
    request_id: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct WriteRouteErrorBody {
    success: bool,
    error: WriteRouteErrorDetail,
}

#[derive(Debug)]
enum SeedlotInventoryAdjustmentRouteError {
    Auth(ProtectedRouteError),
    Response {
        status: StatusCode,
        code: &'static str,
        message: String,
        details: Value,
        request_id: String,
    },
}

impl From<ProtectedRouteError> for SeedlotInventoryAdjustmentRouteError {
    fn from(error: ProtectedRouteError) -> Self {
        Self::Auth(error)
    }
}

impl SeedlotInventoryAdjustmentRouteError {
    fn response(
        status: StatusCode,
        code: &'static str,
        message: impl Into<String>,
        details: Value,
        request_id: String,
    ) -> Self {
        Self::Response {
            status,
            code,
            message: message.into(),
            details,
            request_id,
        }
    }

    fn validation(message: impl Into<String>, request_id: String, details: Value) -> Self {
        Self::response(
            StatusCode::UNPROCESSABLE_ENTITY,
            "validation_failed",
            message,
            details,
            request_id,
        )
    }

    fn forbidden(message: impl Into<String>, request_id: String, details: Value) -> Self {
        Self::response(
            StatusCode::FORBIDDEN,
            "forbidden",
            message,
            details,
            request_id,
        )
    }

    fn not_found(message: impl Into<String>, request_id: String, details: Value) -> Self {
        Self::response(
            StatusCode::NOT_FOUND,
            "not_found",
            message,
            details,
            request_id,
        )
    }

    fn conflict(message: impl Into<String>, request_id: String, details: Value) -> Self {
        Self::response(
            StatusCode::CONFLICT,
            "idempotency_conflict",
            message,
            details,
            request_id,
        )
    }

    fn internal(message: impl Into<String>, request_id: String, details: Value) -> Self {
        Self::response(
            StatusCode::INTERNAL_SERVER_ERROR,
            "internal_error",
            message,
            details,
            request_id,
        )
    }
}

#[derive(Debug)]
enum ProtectedRouteError {
    Unauthenticated,
    InvalidCredentials,
    InactiveUser,
    AuthAdapterUnavailable,
    AuthProviderUnavailable,
    UserRepositoryUnavailable,
    DataRepositoryUnavailable,
    NotFound(&'static str),
}

fn default_page_size() -> u32 {
    100
}

fn default_people_page_size() -> u32 {
    20
}

fn default_crossing_project_page_size() -> u32 {
    1000
}

fn default_common_crop_page_size() -> u32 {
    1000
}

fn bounded_page_size(page_size: u32, max_page_size: u32) -> u32 {
    page_size.clamp(1, max_page_size)
}

impl SeedlotInventoryAdjustmentListQuery {
    fn params(&self, organization_id: i64) -> SeedlotInventoryAdjustmentListParams {
        SeedlotInventoryAdjustmentListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            seedlot_db_id: self.seedlot_db_id.clone(),
        }
    }
}

impl ProgramListQuery {
    fn params(&self, organization_id: i64) -> ProgramListParams {
        let _common_crop_name = self.common_crop_name.as_deref();

        ProgramListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            program_name: self.program_name.clone(),
            abbreviation: self.abbreviation.clone(),
        }
    }
}

impl IntoResponse for SeedlotInventoryAdjustmentRouteError {
    fn into_response(self) -> Response {
        match self {
            Self::Auth(error) => error.into_response(),
            Self::Response {
                status,
                code,
                message,
                details,
                request_id,
            } => (
                status,
                Json(WriteRouteErrorBody {
                    success: false,
                    error: WriteRouteErrorDetail {
                        code,
                        message,
                        details,
                        request_id,
                    },
                }),
            )
                .into_response(),
        }
    }
}

impl LocationListQuery {
    fn params(&self, organization_id: i64) -> LocationListParams {
        LocationListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            location_type: self.location_type.clone(),
        }
    }
}

impl TrialListQuery {
    fn params(&self, organization_id: i64) -> TrialListParams {
        let _program_db_id = self.program_db_id.as_deref();

        TrialListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            active: self.active,
        }
    }
}

impl StudyListQuery {
    fn params(&self, organization_id: i64) -> StudyListParams {
        let _trial_db_id = self.trial_db_id.as_deref();

        StudyListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            active: self.active,
        }
    }
}

impl SeasonListQuery {
    fn params(&self, organization_id: i64) -> SeasonListParams {
        SeasonListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            year: self.year,
            season_db_id: self.season_db_id.clone(),
        }
    }
}

impl PersonListQuery {
    fn params(&self, organization_id: i64) -> PersonListParams {
        PersonListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            first_name: self.first_name.clone(),
            last_name: self.last_name.clone(),
        }
    }
}

impl ListListQuery {
    fn params(&self, organization_id: i64) -> ListListParams {
        let _external_reference_id = self.external_reference_id.as_deref();
        let _external_reference_source = self.external_reference_source.as_deref();

        ListListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 2000),
            list_type: self.list_type.clone(),
            list_name: self.list_name.clone(),
            list_db_id: self.list_db_id.clone(),
            list_source: self.list_source.clone(),
        }
    }
}

impl OntologyListQuery {
    fn params(&self, organization_id: i64) -> OntologyListParams {
        OntologyListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            ontology_db_id: self.ontology_db_id.clone(),
            ontology_name: self.ontology_name.clone(),
        }
    }
}

impl GermplasmListQuery {
    fn params(&self, organization_id: i64) -> GermplasmListParams {
        GermplasmListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            germplasm_name: self.germplasm_name.clone(),
            common_crop_name: self.common_crop_name.clone(),
            species: self.species.clone(),
            genus: self.genus.clone(),
        }
    }
}

impl AttributeListQuery {
    fn params(&self, organization_id: i64) -> AttributeListParams {
        let _attribute_pui = self.attribute_pui.as_deref();
        let _germplasm_db_id = self.germplasm_db_id.as_deref();
        let _program_db_id = self.program_db_id.as_deref();
        let _external_reference_id = self.external_reference_id.as_deref();
        let _external_reference_source = self.external_reference_source.as_deref();

        AttributeListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 2000),
            attribute_category: self.attribute_category.clone(),
            attribute_db_id: self.attribute_db_id.clone(),
            attribute_name: self.attribute_name.clone(),
            common_crop_name: self.common_crop_name.clone(),
            trait_db_id: self.trait_db_id.clone(),
            method_db_id: self.method_db_id.clone(),
            scale_db_id: self.scale_db_id.clone(),
        }
    }
}

impl AttributeValueListQuery {
    fn params(&self, organization_id: i64) -> AttributeValueListParams {
        let _external_reference_id = self.external_reference_id.as_deref();
        let _external_reference_source = self.external_reference_source.as_deref();

        AttributeValueListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 2000),
            attribute_db_id: self.attribute_db_id.clone(),
            attribute_name: self.attribute_name.clone(),
            attribute_value_db_id: self.attribute_value_db_id.clone(),
            germplasm_db_id: self.germplasm_db_id.clone(),
            germplasm_name: self.germplasm_name.clone(),
        }
    }
}

impl BreedingMethodListQuery {
    fn params(&self, organization_id: i64) -> BreedingMethodListParams {
        BreedingMethodListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 2000),
        }
    }
}

impl TraitListQuery {
    fn params(&self, organization_id: i64) -> TraitListParams {
        TraitListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            trait_class: self.trait_class.clone(),
            observation_variable_name: self.observation_variable_name.clone(),
            common_crop_name: self.common_crop_name.clone(),
        }
    }
}

impl VariableListQuery {
    fn params(&self, organization_id: i64) -> VariableListParams {
        VariableListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            observation_variable_db_id: self.observation_variable_db_id.clone(),
            observation_variable_name: self.observation_variable_name.clone(),
            trait_class: self.trait_class.clone(),
            common_crop_name: self.common_crop_name.clone(),
            method_db_id: self.method_db_id.clone(),
            scale_db_id: self.scale_db_id.clone(),
            ontology_db_id: self.ontology_db_id.clone(),
        }
    }
}

impl ObservationListQuery {
    fn params(&self, organization_id: i64) -> ObservationListParams {
        ObservationListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            study_id: self
                .study_db_id
                .as_deref()
                .and_then(|value| value.parse::<i64>().ok()),
            germplasm_id: self
                .germplasm_db_id
                .as_deref()
                .and_then(|value| value.parse::<i64>().ok()),
            observation_variable_db_id: self.observation_variable_db_id.clone(),
            observation_unit_db_id: self.observation_unit_db_id.clone(),
        }
    }
}

impl ObservationUnitListQuery {
    fn params(&self, organization_id: i64) -> ObservationUnitListParams {
        ObservationUnitListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            study_id: self
                .study_db_id
                .as_deref()
                .and_then(|value| value.parse::<i64>().ok()),
            germplasm_id: self
                .germplasm_db_id
                .as_deref()
                .and_then(|value| value.parse::<i64>().ok()),
            observation_level: self.observation_level.clone(),
            observation_unit_db_id: self.observation_unit_db_id.clone(),
        }
    }
}

impl MethodListQuery {
    fn params(&self, organization_id: i64) -> MethodListParams {
        let _external_reference_id = self.external_reference_id.as_deref();
        let _external_reference_source = self.external_reference_source.as_deref();

        MethodListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            method_db_id: self.method_db_id.clone(),
            method_class: self.method_class.clone(),
            method_name: self.method_name.clone(),
            ontology_db_id: self.ontology_db_id.clone(),
        }
    }
}

impl ScaleListQuery {
    fn params(&self, organization_id: i64) -> ScaleListParams {
        ScaleListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            scale_db_id: self.scale_db_id.clone(),
            scale_name: self.scale_name.clone(),
            data_type: self.data_type.clone(),
            ontology_db_id: self.ontology_db_id.clone(),
        }
    }
}

impl SeedlotListQuery {
    fn params(&self, organization_id: i64) -> SeedlotListParams {
        SeedlotListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            germplasm_db_id: self.germplasm_db_id.clone(),
            location_db_id: self.location_db_id.clone(),
            program_db_id: self.program_db_id.clone(),
            seedlot_db_id: self.seedlot_db_id.clone(),
            seedlot_name: self.seedlot_name.clone(),
        }
    }
}

impl SeedlotTransactionListQuery {
    fn params(&self, organization_id: i64) -> SeedlotTransactionListParams {
        SeedlotTransactionListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            seedlot_db_id: self.seedlot_db_id.clone(),
            transaction_db_id: self.transaction_db_id.clone(),
        }
    }
}

impl SeedlotScopedTransactionListQuery {
    fn params(
        &self,
        organization_id: i64,
        seedlot_db_id: String,
    ) -> SeedlotScopedTransactionListParams {
        SeedlotScopedTransactionListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            seedlot_db_id,
        }
    }
}

impl VariantSetListQuery {
    fn params(&self, organization_id: i64) -> VariantSetListParams {
        let _variant_db_id = self.variant_db_id.as_deref();
        let _call_set_db_id = self.call_set_db_id.as_deref();
        let _study_name = self.study_name.as_deref();

        VariantSetListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            variant_set_db_id: self.variant_set_db_id.clone(),
            study_db_id: self.study_db_id.clone(),
            reference_set_db_id: self.reference_set_db_id.clone(),
        }
    }
}

impl CallSetListQuery {
    fn params(&self, organization_id: i64) -> CallSetListParams {
        let _germplasm_db_id = self.germplasm_db_id.as_deref();

        CallSetListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            call_set_db_id: self.call_set_db_id.clone(),
            call_set_name: self.call_set_name.clone(),
            sample_db_id: self.sample_db_id.clone(),
            variant_set_db_id: self.variant_set_db_id.clone(),
        }
    }
}

impl GenomeMapListQuery {
    fn params(&self, organization_id: i64) -> GenomeMapListParams {
        let _program_db_id = self.program_db_id.as_deref();
        let _trial_db_id = self.trial_db_id.as_deref();
        let _study_db_id = self.study_db_id.as_deref();

        GenomeMapListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            map_db_id: self.map_db_id.clone(),
            map_pui: self.map_pui.clone(),
            common_crop_name: self.common_crop_name.clone(),
            scientific_name: self.scientific_name.clone(),
            map_type: self.r#type.clone(),
        }
    }
}

impl LinkageGroupListQuery {
    fn params(&self, organization_id: i64, map_db_id: String) -> LinkageGroupListParams {
        LinkageGroupListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            map_db_id,
        }
    }
}

impl MarkerPositionListQuery {
    fn params(&self, organization_id: i64) -> MarkerPositionListParams {
        MarkerPositionListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 10000),
            map_db_id: self.map_db_id.clone(),
            linkage_group_name: self.linkage_group_name.clone(),
            variant_db_id: self.variant_db_id.clone(),
            min_position: self.min_position,
            max_position: self.max_position,
        }
    }
}

impl CrossingProjectListQuery {
    fn params(&self, organization_id: i64) -> CrossingProjectListParams {
        let _external_reference_id = self.external_reference_id.as_deref();
        let _external_reference_source = self.external_reference_source.as_deref();

        CrossingProjectListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 2000),
            crossing_project_db_id: self.crossing_project_db_id.clone(),
            crossing_project_name: self.crossing_project_name.clone(),
            program_db_id: self.program_db_id.clone(),
            common_crop_name: self.common_crop_name.clone(),
        }
    }
}

impl CrossListQuery {
    fn params(&self, organization_id: i64) -> CrossListParams {
        CrossListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 1000),
            crossing_project_db_id: self.crossing_project_db_id.clone(),
            cross_type: self.cross_type.clone(),
            cross_db_id: self.cross_db_id.clone(),
            cross_name: self.cross_name.clone(),
        }
    }
}

impl PlannedCrossListQuery {
    fn params(&self, organization_id: i64) -> PlannedCrossListParams {
        let _external_reference_id = self.external_reference_id.as_deref();
        let _external_reference_source = self.external_reference_source.as_deref();

        PlannedCrossListParams {
            organization_id,
            page: self.page,
            page_size: bounded_page_size(self.page_size, 2000),
            crossing_project_db_id: self.crossing_project_db_id.clone(),
            crossing_project_name: self.crossing_project_name.clone(),
            planned_cross_db_id: self.planned_cross_db_id.clone(),
            planned_cross_name: self.planned_cross_name.clone(),
            status: self.status.clone(),
        }
    }
}

pub fn app(state: AppState) -> Router {
    Router::new()
        .route("/", get(root))
        .route("/health", get(health))
        .route("/api/stats", get(stats))
        .route(
            "/api/v2/seed-inventory/summary",
            get(seed_inventory_summary),
        )
        .route(
            "/api/v2/seed-inventory/adjustments",
            get(seedlot_inventory_adjustments_list).post(seedlot_inventory_adjustments_create),
        )
        .route(
            "/api/v2/seed-inventory/adjustments/{public_id}",
            get(seedlot_inventory_adjustments_detail),
        )
        .route("/brapi/v2/serverinfo", get(serverinfo))
        .route("/brapi/v2/calls", get(calls))
        .route("/brapi/v2/commoncropnames", get(common_crop_names))
        .route("/brapi/v2/programs", get(programs))
        .route("/brapi/v2/programs/{program_db_id}", get(program))
        .route("/brapi/v2/locations", get(locations))
        .route("/brapi/v2/locations/{location_db_id}", get(location))
        .route("/brapi/v2/trials", get(trials))
        .route("/brapi/v2/trials/{trial_db_id}", get(trial))
        .route("/brapi/v2/studies", get(studies))
        .route("/brapi/v2/studies/{study_db_id}", get(study))
        .route("/brapi/v2/seasons", get(seasons))
        .route("/brapi/v2/seasons/{season_db_id}", get(season))
        .route("/brapi/v2/people", get(people))
        .route("/brapi/v2/people/{person_db_id}", get(person))
        .route("/brapi/v2/lists", get(lists))
        .route("/brapi/v2/lists/{list_db_id}", get(list))
        .route("/brapi/v2/ontologies", get(ontologies))
        .route("/brapi/v2/ontologies/{ontology_db_id}", get(ontology))
        .route("/brapi/v2/germplasm", get(germplasm_list))
        .route("/brapi/v2/germplasm/{germplasm_db_id}", get(germplasm))
        .route("/brapi/v2/attributes", get(attributes))
        .route("/brapi/v2/attributes/categories", get(attribute_categories))
        .route(
            "/brapi/v2/attributes/{attribute_db_id}",
            get(attribute_detail),
        )
        .route("/brapi/v2/attributevalues", get(attribute_values))
        .route(
            "/brapi/v2/attributevalues/{attribute_value_db_id}",
            get(attribute_value_detail),
        )
        .route("/brapi/v2/breedingmethods", get(breeding_methods))
        .route(
            "/brapi/v2/breedingmethods/{breeding_method_db_id}",
            get(breeding_method_detail),
        )
        .route("/brapi/v2/traits", get(traits))
        .route(
            "/brapi/v2/traits/{observation_variable_db_id}",
            get(trait_detail),
        )
        .route("/brapi/v2/variables", get(variables))
        .route(
            "/brapi/v2/variables/{observation_variable_db_id}",
            get(variable_detail),
        )
        .route("/brapi/v2/observations", get(observations))
        .route(
            "/brapi/v2/observations/{observation_db_id}",
            get(observation_detail),
        )
        .route("/brapi/v2/observationunits", get(observation_units))
        .route(
            "/brapi/v2/observationunits/{observation_unit_db_id}",
            get(observation_unit_detail),
        )
        .route("/brapi/v2/methods", get(methods))
        .route("/brapi/v2/methods/{method_db_id}", get(method_detail))
        .route("/brapi/v2/scales", get(scales))
        .route("/brapi/v2/scales/{scale_db_id}", get(scale_detail))
        .route("/brapi/v2/variantsets", get(variant_sets))
        .route(
            "/brapi/v2/variantsets/{variant_set_db_id}",
            get(variant_set),
        )
        .route("/brapi/v2/callsets", get(callsets))
        .route("/brapi/v2/callsets/{call_set_db_id}", get(callset))
        .route("/brapi/v2/maps", get(maps))
        .route(
            "/brapi/v2/maps/{map_db_id}/linkagegroups",
            get(map_linkage_groups),
        )
        .route("/brapi/v2/maps/{map_db_id}", get(map_detail))
        .route("/brapi/v2/markerpositions", get(marker_positions))
        .route("/brapi/v2/seedlots", get(seedlots))
        .route("/brapi/v2/seedlots/transactions", get(seedlot_transactions))
        .route(
            "/brapi/v2/seedlots/{seedlot_db_id}/transactions",
            get(seedlot_transactions_for_seedlot),
        )
        .route("/brapi/v2/seedlots/{seedlot_db_id}", get(seedlot))
        .route("/brapi/v2/crossingprojects", get(crossing_projects))
        .route(
            "/brapi/v2/crossingprojects/{crossing_project_db_id}",
            get(crossing_project),
        )
        .route("/brapi/v2/crosses", get(crosses))
        .route("/brapi/v2/crosses/{cross_db_id}", get(cross))
        .route("/brapi/v2/plannedcrosses", get(planned_crosses))
        .route(
            "/brapi/v2/plannedcrosses/{planned_cross_db_id}",
            get(planned_cross),
        )
        .route("/api/manifest", get(manifest))
        .layer(CorsLayer::permissive())
        .layer(
            TraceLayer::new_for_http().make_span_with(|request: &AxumRequest| {
                let request_id = request
                    .headers()
                    .get(request_id_header())
                    .and_then(|value| value.to_str().ok())
                    .unwrap_or("missing");
                tracing::info_span!(
                    "http_request",
                    request_id = %request_id,
                    method = %request.method(),
                    path = request.uri().path()
                )
            }),
        )
        .layer(from_fn(request_id_middleware))
        .with_state(state)
}

pub async fn serve(addr: SocketAddr, state: AppState) -> anyhow::Result<()> {
    let listener = tokio::net::TcpListener::bind(addr).await?;
    tracing::info!(%addr, workspace = %state.workspace_root().display(), "starting BijMantra Rust API");
    axum::serve(listener, app(state))
        .with_graceful_shutdown(shutdown_signal())
        .await?;
    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        if let Err(error) = tokio::signal::ctrl_c().await {
            tracing::warn!(%error, "failed to listen for Ctrl+C shutdown signal");
        }
    };

    #[cfg(unix)]
    let terminate = async {
        match tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()) {
            Ok(mut signal) => {
                signal.recv().await;
            }
            Err(error) => tracing::warn!(%error, "failed to listen for terminate signal"),
        }
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }
    tracing::info!("shutdown signal received");
}

async fn root() -> Json<RootResponse> {
    Json(RootResponse {
        message: "Welcome to Bijmantra API",
        version: bijmantra_core::product::APP_VERSION,
        brapi_version: bijmantra_core::product::BRAPI_VERSION,
        docs: "/docs",
    })
}

async fn health(State(state): State<AppState>) -> Json<HealthReport> {
    let mut dependencies =
        BTreeMap::from([("rust_runtime".to_string(), DependencyHealth::healthy(true))]);

    let metrics_dependency = match load_api_metrics(state.metrics_path()) {
        Ok(_) => DependencyHealth::healthy(false),
        Err(error) => DependencyHealth::degraded(false, error.to_string()),
    };
    dependencies.insert("metrics_file".to_string(), metrics_dependency);

    if let Some(postgres_dependency) = state.data_store.read_repository_health_dependency().await {
        dependencies.insert("postgres_read_repository".to_string(), postgres_dependency);
    }

    Json(HealthReport::from_dependencies(dependencies))
}

async fn stats(State(state): State<AppState>) -> Json<ApiStats> {
    let metrics = load_api_metrics(state.metrics_path()).unwrap_or_else(|_| ApiMetrics::default());
    Json(api_stats(metrics))
}

async fn seed_inventory_summary(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> Result<Json<SeedInventorySummary>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let summary = state
        .data_store
        .get_seed_inventory_summary(active_user.organization_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get seed inventory summary from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(summary))
}

async fn require_seedlot_inventory_adjustment_access(
    state: &AppState,
    active_user: &ActiveUser,
    request_id: &str,
    plan: &WriteAuthorizationPlan,
) -> Result<PlatformCapabilityAccessContext, SeedlotInventoryAdjustmentRouteError> {
    let capability_context = state
        .data_store
        .build_seedlot_inventory_adjustment_access_context_internal(
            active_user.organization_id,
            active_user.user_id,
        )
        .await
        .map_err(|error| {
            map_seedlot_inventory_adjustment_write_error(
                error,
                request_id.to_owned(),
                "load seed lot traceability capability context",
            )
        })?;

    let Some(capability_context) = capability_context else {
        return Err(SeedlotInventoryAdjustmentRouteError::forbidden(
            "Seed lot traceability capability is not installed for this organization.",
            request_id.to_owned(),
            json!({
                "reason": "capability_not_installed",
                "capabilityId": &plan.capability_id,
                "requiredPermission": &plan.required_permission,
                "requiredDataScopes": &plan.required_data_scopes,
                "missingPermissions": [],
                "missingDataScopes": [],
            }),
        ));
    };

    let decision = plan.evaluate_platform_context(
        &capability_context,
        active_user.organization_id,
        active_user.user_id,
    );
    if !decision.allowed {
        return Err(seedlot_inventory_adjustment_forbidden_error(
            request_id.to_owned(),
            plan,
            &decision,
        ));
    }

    Ok(capability_context)
}

async fn seedlot_inventory_adjustments_list(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<SeedlotInventoryAdjustmentListQuery>,
) -> Result<Json<SeedlotInventoryAdjustmentHistoryResponse>, SeedlotInventoryAdjustmentRouteError> {
    let request_id = request_id_string(&headers);
    let active_user = resolve_active_user(&headers, &state).await?;
    let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment_read();
    let _capability_context =
        require_seedlot_inventory_adjustment_access(&state, &active_user, &request_id, &plan)
            .await?;

    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;
    let (records, total_count) = state
        .data_store
        .list_seedlot_inventory_adjustments_internal(&params)
        .await
        .map_err(|error| {
            map_seedlot_inventory_adjustment_write_error(
                error,
                request_id.clone(),
                "list seed lot inventory adjustments",
            )
        })?;

    Ok(Json(SeedlotInventoryAdjustmentHistoryResponse {
        success: true,
        adjustments: records.into_iter().map(Into::into).collect(),
        metadata: SeedlotInventoryAdjustmentHistoryMetadata {
            page,
            page_size,
            total_count,
        },
    }))
}

async fn seedlot_inventory_adjustments_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(public_id): AxumPath<String>,
) -> Result<Json<SeedlotInventoryAdjustmentDetailResponse>, SeedlotInventoryAdjustmentRouteError> {
    let request_id = request_id_string(&headers);
    let active_user = resolve_active_user(&headers, &state).await?;

    let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment_read();
    let _capability_context =
        require_seedlot_inventory_adjustment_access(&state, &active_user, &request_id, &plan)
            .await?;

    let public_id = PublicId::parse(&public_id).map_err(|error| {
        SeedlotInventoryAdjustmentRouteError::validation(
            format!("publicId must be a UUID7 value: {error}"),
            request_id.clone(),
            json!({
                "publicId": public_id.clone(),
            }),
        )
    })?;
    let public_id = public_id.require_uuid7().map_err(|error| {
        SeedlotInventoryAdjustmentRouteError::validation(
            format!("publicId must be a UUID7 value: {error}"),
            request_id.clone(),
            json!({
                "error": error.to_string(),
            }),
        )
    })?;

    let record = state
        .data_store
        .get_seedlot_inventory_adjustment_by_public_id_internal(
            active_user.organization_id,
            public_id,
        )
        .await
        .map_err(|error| {
            map_seedlot_inventory_adjustment_write_error(
                error,
                request_id.clone(),
                "get seed lot inventory adjustment detail",
            )
        })?;

    let Some(record) = record else {
        return Err(SeedlotInventoryAdjustmentRouteError::not_found(
            "Seed lot inventory adjustment not found inside current organization.",
            request_id,
            json!({
                "organizationId": active_user.organization_id,
                "publicId": public_id.to_string(),
            }),
        ));
    };

    Ok(Json(record.into()))
}

async fn seedlot_inventory_adjustments_create(
    State(state): State<AppState>,
    request: AxumRequest,
) -> Result<
    (StatusCode, Json<SeedlotInventoryAdjustmentResponse>),
    SeedlotInventoryAdjustmentRouteError,
> {
    let (parts, body) = request.into_parts();
    let headers = parts.headers;
    let request_id = request_id_string(&headers);
    let active_user = resolve_active_user(&headers, &state).await?;

    let body = to_bytes(body, 1024 * 1024).await.map_err(|error| {
        SeedlotInventoryAdjustmentRouteError::validation(
            format!("Request body could not be read: {error}"),
            request_id.clone(),
            json!({
                "body": error.to_string(),
            }),
        )
    })?;

    let payload: SeedlotInventoryAdjustmentRequest =
        serde_json::from_slice(&body).map_err(|error| {
            SeedlotInventoryAdjustmentRouteError::validation(
                format!("Request body validation failed: {error}"),
                request_id.clone(),
                json!({
                    "body": error.to_string(),
                }),
            )
        })?;

    let command = payload
        .into_create_command(active_user.organization_id, active_user.user_id)
        .map_err(|error| {
            SeedlotInventoryAdjustmentRouteError::validation(
                format!("Request body validation failed: {error}"),
                request_id.clone(),
                json!({
                    "error": error.to_string(),
                }),
            )
        })?;

    if let Some(existing) = state
        .data_store
        .get_seedlot_inventory_adjustment_by_idempotency_key_internal(
            active_user.organization_id,
            active_user.user_id,
            &command.idempotency_key,
        )
        .await
        .map_err(|error| {
            map_seedlot_inventory_adjustment_write_error(
                error,
                request_id.clone(),
                "lookup existing seedlot inventory adjustment",
            )
        })?
    {
        if existing.matches_create_command(&command) {
            return Ok((StatusCode::OK, Json(existing.into())));
        }

        return Err(SeedlotInventoryAdjustmentRouteError::conflict(
            "Idempotency key replay conflicts with the original request.",
            request_id,
            json!({
                "idempotencyKey": command.idempotency_key.as_str(),
                "existingPublicId": existing.public_id.to_string(),
            }),
        ));
    }

    let capability_context = state
        .data_store
        .build_seedlot_inventory_adjustment_access_context_internal(
            active_user.organization_id,
            active_user.user_id,
        )
        .await
        .map_err(|error| {
            map_seedlot_inventory_adjustment_write_error(
                error,
                request_id.clone(),
                "load seed lot traceability capability context",
            )
        })?;

    let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment();
    let Some(capability_context) = capability_context else {
        return Err(SeedlotInventoryAdjustmentRouteError::forbidden(
            "Seed lot traceability capability is not installed for this organization.",
            request_id,
            json!({
                "reason": "capability_not_installed",
                "capabilityId": plan.capability_id,
                "requiredPermission": plan.required_permission,
                "requiredDataScopes": plan.required_data_scopes,
                "missingPermissions": [],
                "missingDataScopes": [],
            }),
        ));
    };

    let decision = plan.evaluate_platform_context(
        &capability_context,
        active_user.organization_id,
        active_user.user_id,
    );
    if !decision.allowed {
        return Err(seedlot_inventory_adjustment_forbidden_error(
            request_id.clone(),
            &plan,
            &decision,
        ));
    }

    let seedlot = state
        .data_store
        .get_seedlot(active_user.organization_id, &command.seedlot_db_id)
        .await
        .map_err(|error| {
            map_seedlot_inventory_adjustment_data_error(
                error,
                request_id.clone(),
                "lookup seed lot for inventory adjustment",
            )
        })?;
    if seedlot.is_none() {
        return Err(SeedlotInventoryAdjustmentRouteError::not_found(
            "Seed lot not found inside current organization.",
            request_id,
            json!({
                "organizationId": active_user.organization_id,
                "seedLotDbId": command.seedlot_db_id,
            }),
        ));
    }

    let record = state
        .data_store
        .create_seedlot_inventory_adjustment_authorized_internal(&capability_context, command)
        .await
        .map_err(|error| {
            map_seedlot_inventory_adjustment_write_error(
                error,
                request_id.clone(),
                "create seed lot inventory adjustment",
            )
        })?;

    Ok((StatusCode::CREATED, Json(record.into())))
}

async fn serverinfo() -> Json<BrApiServerInfo> {
    Json(BrApiServerInfo::current())
}

async fn calls() -> Json<BrApiListResponse<BrApiCall>> {
    let calls = rust_brapi_calls();
    let total_count = calls.len().try_into().unwrap_or(u32::MAX);
    Json(BrApiListResponse::from_data(
        calls,
        0,
        total_count,
        total_count,
    ))
}

async fn common_crop_names(
    Query(query): Query<CommonCropNamesQuery>,
) -> Json<BrApiListResponse<&'static str>> {
    let page_size = bounded_page_size(query.page_size, 2000);
    let total_count = COMMON_CROPS.len().try_into().unwrap_or(u32::MAX);
    let start = usize::try_from(query.page.saturating_mul(page_size)).unwrap_or(usize::MAX);
    let page_size_usize = usize::try_from(page_size).unwrap_or(usize::MAX);
    let data = if start >= COMMON_CROPS.len() {
        Vec::new()
    } else {
        let end = start
            .saturating_add(page_size_usize)
            .min(COMMON_CROPS.len());
        COMMON_CROPS[start..end].to_vec()
    };

    Json(BrApiListResponse::from_data(
        data,
        query.page,
        page_size,
        total_count,
    ))
}

async fn programs(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<ProgramListQuery>,
) -> Result<Json<BrApiListResponse<ProgramSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (programs, total_count) =
        state
            .data_store
            .list_programs(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI programs from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        programs,
        page,
        page_size,
        total_count,
    )))
}

async fn program(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(program_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<ProgramSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let program = state
        .data_store
        .get_program(active_user.organization_id, &program_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI program from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Program not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(program)))
}

async fn locations(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<LocationListQuery>,
) -> Result<Json<BrApiListResponse<LocationSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (locations, total_count) =
        state
            .data_store
            .list_locations(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI locations from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        locations,
        page,
        page_size,
        total_count,
    )))
}

async fn location(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(location_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<LocationSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let location = state
        .data_store
        .get_location(active_user.organization_id, &location_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI location from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Location not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(location)))
}

async fn trials(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<TrialListQuery>,
) -> Result<Json<BrApiListResponse<TrialSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (trials, total_count) = state
        .data_store
        .list_trials(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI trials from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        trials,
        page,
        page_size,
        total_count,
    )))
}

async fn trial(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(trial_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<TrialSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let trial = state
        .data_store
        .get_trial(active_user.organization_id, &trial_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI trial from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Trial not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(trial)))
}

async fn studies(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<StudyListQuery>,
) -> Result<Json<BrApiListResponse<StudySummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (studies, total_count) = state
        .data_store
        .list_studies(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI studies from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        studies,
        page,
        page_size,
        total_count,
    )))
}

async fn study(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(study_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<StudySummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let study = state
        .data_store
        .get_study(active_user.organization_id, &study_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI study from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Study not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(study)))
}

async fn seasons(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<SeasonListQuery>,
) -> Result<Json<BrApiListResponse<SeasonSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (seasons, total_count) = state
        .data_store
        .list_seasons(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI seasons from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        seasons,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn season(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(season_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<SeasonSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let season = state
        .data_store
        .get_season(active_user.organization_id, &season_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI season from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Season not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(season)))
}

async fn people(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<PersonListQuery>,
) -> Result<Json<BrApiListResponse<PersonSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (people, total_count) = state
        .data_store
        .list_people(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI people from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        people,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn person(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(person_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<PersonSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let person = state
        .data_store
        .get_person(active_user.organization_id, &person_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI person from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Person not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(person)))
}

async fn lists(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<ListListQuery>,
) -> Result<Json<BrApiListResponse<ListSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (lists, total_count) =
        state
            .data_store
            .list_lists(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI lists from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        lists,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn list(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(list_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<ListSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let list = state
        .data_store
        .get_list(active_user.organization_id, &list_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI list from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("List not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(list)))
}

async fn ontologies(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<OntologyListQuery>,
) -> Result<Json<BrApiListResponse<OntologySummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (ontologies, total_count) =
        state
            .data_store
            .list_ontologies(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI ontologies from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        ontologies,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn ontology(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(ontology_db_id): AxumPath<String>,
) -> Result<Json<Value>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let ontology = state
        .data_store
        .get_ontology(active_user.organization_id, &ontology_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI ontology from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    let body = match ontology {
        Some(ontology) => serde_json::to_value(BrApiSingleResponse::from_item(ontology))
            .unwrap_or_else(|_| json!({"metadata": {"status": []}, "result": null})),
        None => json!({
            "metadata": {
                "status": [{
                    "message": format!("Ontology {ontology_db_id} not found"),
                    "messageType": "ERROR",
                }]
            },
            "result": null
        }),
    };

    Ok(Json(body))
}

async fn germplasm_list(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<GermplasmListQuery>,
) -> Result<Json<BrApiListResponse<GermplasmSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (germplasm, total_count) =
        state
            .data_store
            .list_germplasm(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI germplasm from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        germplasm,
        page,
        page_size,
        total_count,
    )))
}

async fn germplasm(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(germplasm_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<GermplasmSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let germplasm = state
        .data_store
        .get_germplasm(active_user.organization_id, &germplasm_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI germplasm from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Germplasm not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(germplasm)))
}

async fn attributes(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<AttributeListQuery>,
) -> Result<Json<BrApiListResponse<AttributeSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (attributes, total_count) =
        state
            .data_store
            .list_attributes(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI attributes from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        attributes,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn attribute_categories(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<AttributeCategoryListQuery>,
) -> Result<Json<BrApiListResponse<String>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let page = query.page;
    let page_size = bounded_page_size(query.page_size, 2000);

    let (categories, total_count) = state
        .data_store
        .list_attribute_categories(active_user.organization_id, page, page_size)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI attribute categories from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        categories,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn attribute_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(attribute_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<AttributeSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let attribute = state
        .data_store
        .get_attribute(active_user.organization_id, &attribute_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI attribute from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Attribute not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(attribute)))
}

async fn attribute_values(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<AttributeValueListQuery>,
) -> Result<Json<BrApiListResponse<AttributeValueSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (values, total_count) =
        state
            .data_store
            .list_attribute_values(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI attribute values from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        values,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn attribute_value_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(attribute_value_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<AttributeValueSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let value = state
        .data_store
        .get_attribute_value(active_user.organization_id, &attribute_value_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI attribute value from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Attribute value not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(value)))
}

async fn breeding_methods(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<BreedingMethodListQuery>,
) -> Result<Json<BrApiListResponse<BreedingMethodSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (methods, total_count) = state
        .data_store
        .list_breeding_methods(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI breeding methods from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        methods,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn breeding_method_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(breeding_method_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<BreedingMethodSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let method = state
        .data_store
        .get_breeding_method(active_user.organization_id, &breeding_method_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI breeding method from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Breeding method not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(method)))
}

async fn traits(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<TraitListQuery>,
) -> Result<Json<BrApiListResponse<TraitSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (traits, total_count) = state
        .data_store
        .list_traits(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI traits from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        traits,
        page,
        page_size,
        total_count,
    )))
}

async fn trait_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(observation_variable_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<TraitSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let trait_summary = state
        .data_store
        .get_trait(active_user.organization_id, &observation_variable_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI trait from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Trait not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(trait_summary)))
}

async fn variables(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<VariableListQuery>,
) -> Result<Json<BrApiListResponse<VariableSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (variables, total_count) =
        state
            .data_store
            .list_variables(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI variables from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        variables,
        page,
        page_size,
        total_count,
    )))
}

async fn variable_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(observation_variable_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<VariableSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let variable = state
        .data_store
        .get_variable(active_user.organization_id, &observation_variable_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI variable from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound(
            "Observation variable not found",
        ))?;

    Ok(Json(BrApiSingleResponse::from_item(variable)))
}

async fn observations(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<ObservationListQuery>,
) -> Result<Json<BrApiListResponse<ObservationSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (observations, total_count) = state.data_store.list_observations(params).await.map_err(
        |error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI observations from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        },
    )?;

    Ok(Json(BrApiListResponse::from_data(
        observations,
        page,
        page_size,
        total_count,
    )))
}

async fn observation_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(observation_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<ObservationSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let observation = state
        .data_store
        .get_observation(active_user.organization_id, &observation_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI observation from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Observation not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(observation)))
}

async fn observation_units(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<ObservationUnitListQuery>,
) -> Result<Json<BrApiListResponse<ObservationUnitSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (units, total_count) =
        state
            .data_store
            .list_observation_units(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI observation units from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        units,
        page,
        page_size,
        total_count,
    )))
}

async fn observation_unit_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(observation_unit_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<ObservationUnitSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let unit = state
        .data_store
        .get_observation_unit(active_user.organization_id, &observation_unit_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI observation unit from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Observation unit not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(unit)))
}

async fn methods(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<MethodListQuery>,
) -> Result<Json<BrApiListResponse<MethodSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (methods, total_count) = state
        .data_store
        .list_methods(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI methods from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        methods,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn method_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(method_db_id): AxumPath<String>,
) -> Result<Json<Value>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let method = state
        .data_store
        .get_method(active_user.organization_id, &method_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI method from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    let body = match method {
        Some(method) => serde_json::to_value(BrApiSingleResponse::from_item(method))
            .unwrap_or_else(|_| json!({"metadata": {"status": []}, "result": null})),
        None => json!({
            "metadata": {
                "status": [{
                    "message": format!("Method {method_db_id} not found"),
                    "messageType": "ERROR",
                }]
            },
            "result": null
        }),
    };

    Ok(Json(body))
}

async fn scales(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<ScaleListQuery>,
) -> Result<Json<BrApiListResponse<ScaleSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (scales, total_count) = state
        .data_store
        .list_scales(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI scales from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data_with_total_pages_floor(
        scales,
        page,
        page_size,
        total_count,
        1,
    )))
}

async fn scale_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(scale_db_id): AxumPath<String>,
) -> Result<Json<Value>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let scale = state
        .data_store
        .get_scale(active_user.organization_id, &scale_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI scale from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    let body = match scale {
        Some(scale) => serde_json::to_value(BrApiSingleResponse::from_item(scale))
            .unwrap_or_else(|_| json!({"metadata": {"status": []}, "result": null})),
        None => json!({
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": 0,
                    "pageSize": 0,
                    "totalCount": 0,
                    "totalPages": 0,
                },
                "status": [{
                    "message": format!("Scale {scale_db_id} not found"),
                    "messageType": "ERROR",
                }]
            },
            "result": null
        }),
    };

    Ok(Json(body))
}

async fn variant_sets(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<VariantSetListQuery>,
) -> Result<Json<BrApiListResponse<VariantSetSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (variant_sets, total_count) = state.data_store.list_variant_sets(params).await.map_err(
        |error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI variant sets from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        },
    )?;

    Ok(Json(BrApiListResponse::from_data(
        variant_sets,
        page,
        page_size,
        total_count,
    )))
}

async fn variant_set(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(variant_set_db_id): AxumPath<String>,
) -> Result<Json<Value>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let variant_set = state
        .data_store
        .get_variant_set(active_user.organization_id, &variant_set_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI variant set from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    let body = match variant_set {
        Some(variant_set) => serde_json::to_value(BrApiSingleResponse::from_item(variant_set))
            .unwrap_or_else(|_| json!({"metadata": {"status": []}, "result": null})),
        None => json!({
            "metadata": {
                "status": [{
                    "message": format!("VariantSet {variant_set_db_id} not found"),
                    "messageType": "ERROR",
                }]
            },
            "result": null
        }),
    };

    Ok(Json(body))
}

async fn callsets(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<CallSetListQuery>,
) -> Result<Json<BrApiListResponse<CallSetSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (callsets, total_count) =
        state
            .data_store
            .list_callsets(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI callsets from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        callsets,
        page,
        page_size,
        total_count,
    )))
}

async fn callset(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(call_set_db_id): AxumPath<String>,
) -> Result<Json<Value>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let callset = state
        .data_store
        .get_callset(active_user.organization_id, &call_set_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI callset from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    let body = match callset {
        Some(callset) => serde_json::to_value(BrApiSingleResponse::from_item(callset))
            .unwrap_or_else(|_| json!({"metadata": {"status": []}, "result": null})),
        None => json!({
            "metadata": {
                "status": [{
                    "message": format!("CallSet {call_set_db_id} not found"),
                    "messageType": "ERROR",
                }]
            },
            "result": null
        }),
    };

    Ok(Json(body))
}

async fn maps(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<GenomeMapListQuery>,
) -> Result<Json<BrApiListResponse<GenomeMapSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (maps, total_count) =
        state
            .data_store
            .list_maps(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI maps from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        maps,
        page,
        page_size,
        total_count,
    )))
}

async fn map_detail(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(map_db_id): AxumPath<String>,
) -> Result<Json<Value>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let map = state
        .data_store
        .get_map(active_user.organization_id, &map_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI map from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    let body = match map {
        Some(map) => serde_json::to_value(BrApiSingleResponse::from_item(map))
            .unwrap_or_else(|_| json!({"metadata": {"status": []}, "result": null})),
        None => json!({
            "metadata": {
                "status": [{
                    "message": format!("Map {map_db_id} not found"),
                    "messageType": "ERROR",
                }]
            },
            "result": null
        }),
    };

    Ok(Json(body))
}

async fn map_linkage_groups(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(map_db_id): AxumPath<String>,
    Query(query): Query<LinkageGroupListQuery>,
) -> Result<Json<BrApiListResponse<LinkageGroupSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id, map_db_id);
    let page = params.page;
    let page_size = params.page_size;

    let (linkage_groups, total_count) = state
        .data_store
        .list_linkage_groups_for_map(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI map linkage groups from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        linkage_groups,
        page,
        page_size,
        total_count,
    )))
}

async fn marker_positions(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<MarkerPositionListQuery>,
) -> Result<Json<BrApiListResponse<MarkerPositionSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (marker_positions, total_count) = state
        .data_store
        .list_marker_positions(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI marker positions from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        marker_positions,
        page,
        page_size,
        total_count,
    )))
}

async fn seedlots(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<SeedlotListQuery>,
) -> Result<Json<BrApiListResponse<SeedlotSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (seedlots, total_count) =
        state
            .data_store
            .list_seedlots(params)
            .await
            .map_err(|error| match error {
                DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
                DataStoreError::Query(error) => {
                    tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI seedlots from Rust repository");
                    ProtectedRouteError::DataRepositoryUnavailable
                }
            })?;

    Ok(Json(BrApiListResponse::from_data(
        seedlots,
        page,
        page_size,
        total_count,
    )))
}

async fn seedlot(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(seedlot_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<SeedlotSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let seedlot = state
        .data_store
        .get_seedlot(active_user.organization_id, &seedlot_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI seedlot from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Seed lot not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(seedlot)))
}

async fn seedlot_transactions(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<SeedlotTransactionListQuery>,
) -> Result<Json<BrApiListResponse<SeedlotTransactionSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (transactions, total_count) = state
        .data_store
        .list_seedlot_transactions(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI seedlot transactions from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        transactions,
        page,
        page_size,
        total_count,
    )))
}

async fn seedlot_transactions_for_seedlot(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(seedlot_db_id): AxumPath<String>,
    Query(query): Query<SeedlotScopedTransactionListQuery>,
) -> Result<Json<BrApiListResponse<SeedlotTransactionSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id, seedlot_db_id);
    let page = params.page;
    let page_size = params.page_size;

    let (transactions, total_count) = state
        .data_store
        .list_transactions_for_seedlot(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI seedlot-scoped transactions from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Seed lot not found"))?;

    Ok(Json(BrApiListResponse::from_data(
        transactions,
        page,
        page_size,
        total_count,
    )))
}

async fn crossing_projects(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<CrossingProjectListQuery>,
) -> Result<Json<BrApiListResponse<CrossingProjectSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (projects, total_count) = state
        .data_store
        .list_crossing_projects(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI crossing projects from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        projects,
        page,
        page_size,
        total_count,
    )))
}

async fn crossing_project(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(crossing_project_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<CrossingProjectSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let project = state
        .data_store
        .get_crossing_project(active_user.organization_id, &crossing_project_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI crossing project from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Crossing project not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(project)))
}

async fn crosses(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<CrossListQuery>,
) -> Result<Json<BrApiListResponse<CrossSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (crosses, total_count) = state
        .data_store
        .list_crosses(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI crosses from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        crosses,
        page,
        page_size,
        total_count,
    )))
}

async fn cross(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(cross_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<CrossSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let cross = state
        .data_store
        .get_cross(active_user.organization_id, &cross_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI cross from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Cross not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(cross)))
}

async fn planned_crosses(
    State(state): State<AppState>,
    headers: HeaderMap,
    Query(query): Query<PlannedCrossListQuery>,
) -> Result<Json<BrApiListResponse<PlannedCrossSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;
    let params = query.params(active_user.organization_id);
    let page = params.page;
    let page_size = params.page_size;

    let (planned_crosses, total_count) = state
        .data_store
        .list_planned_crosses(params)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to list BrAPI planned crosses from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?;

    Ok(Json(BrApiListResponse::from_data(
        planned_crosses,
        page,
        page_size,
        total_count,
    )))
}

async fn planned_cross(
    State(state): State<AppState>,
    headers: HeaderMap,
    AxumPath(planned_cross_db_id): AxumPath<String>,
) -> Result<Json<BrApiSingleResponse<PlannedCrossSummary>>, ProtectedRouteError> {
    let active_user = resolve_active_user(&headers, &state).await?;

    let planned_cross = state
        .data_store
        .get_planned_cross(active_user.organization_id, &planned_cross_db_id)
        .await
        .map_err(|error| match error {
            DataStoreError::Unavailable => ProtectedRouteError::DataRepositoryUnavailable,
            DataStoreError::Query(error) => {
                tracing::warn!(%error, route_context = "rust_read_beta", "failed to get BrAPI planned cross from Rust repository");
                ProtectedRouteError::DataRepositoryUnavailable
            }
        })?
        .ok_or(ProtectedRouteError::NotFound("Planned cross not found"))?;

    Ok(Json(BrApiSingleResponse::from_item(planned_cross)))
}

async fn manifest() -> Json<ProductManifest> {
    Json(ProductManifest::current())
}

async fn request_id_middleware(mut request: AxumRequest, next: Next) -> Response {
    let request_id = request
        .headers()
        .get(request_id_header())
        .and_then(valid_request_id_header)
        .unwrap_or_else(generated_request_id);

    request
        .headers_mut()
        .insert(request_id_header(), request_id.clone());

    let mut response = next.run(request).await;
    response
        .headers_mut()
        .insert(request_id_header(), request_id);
    response
}

fn request_id_header() -> HeaderName {
    HeaderName::from_static("x-request-id")
}

fn valid_request_id_header(value: &HeaderValue) -> Option<HeaderValue> {
    let value = value.to_str().ok()?;
    is_valid_request_id(value).then(|| HeaderValue::from_str(value).ok())?
}

fn is_valid_request_id(value: &str) -> bool {
    !value.is_empty() && value.len() <= 128 && value.bytes().all(|byte| matches!(byte, 0x21..=0x7e))
}

fn generated_request_id() -> HeaderValue {
    let counter = REQUEST_ID_COUNTER.fetch_add(1, Ordering::Relaxed);
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    HeaderValue::from_str(&format!("rust-read-{nanos:x}-{counter:x}"))
        .expect("generated request ID should be a valid HTTP header value")
}

fn request_id_string(headers: &HeaderMap) -> String {
    headers
        .get(request_id_header())
        .and_then(|value| value.to_str().ok())
        .unwrap_or("missing")
        .to_owned()
}

fn seedlot_inventory_adjustment_forbidden_error(
    request_id: String,
    plan: &WriteAuthorizationPlan,
    decision: &WriteAuthorizationDecision,
) -> SeedlotInventoryAdjustmentRouteError {
    let message = match decision.reason {
        bijmantra_core::WriteAuthorizationReason::Allowed => {
            "Seed lot traceability access was unexpectedly allowed."
        }
        bijmantra_core::WriteAuthorizationReason::InvalidContext => {
            "Seed lot traceability access context is invalid."
        }
        bijmantra_core::WriteAuthorizationReason::TenantMismatch => {
            "Seed lot traceability access is scoped to a different tenant."
        }
        bijmantra_core::WriteAuthorizationReason::CapabilityNotInstalled => {
            "Seed lot traceability capability is not installed for this organization."
        }
        bijmantra_core::WriteAuthorizationReason::MissingPermission => {
            return SeedlotInventoryAdjustmentRouteError::forbidden(
                format!("Missing required permission {}.", plan.required_permission),
                request_id,
                json!({
                    "reason": decision.reason,
                    "capabilityId": decision.capability_id,
                    "requiredPermission": plan.required_permission,
                    "requiredDataScopes": plan.required_data_scopes,
                    "missingPermissions": decision.missing_permissions,
                    "missingDataScopes": decision.missing_data_scopes,
                }),
            );
        }
        bijmantra_core::WriteAuthorizationReason::MissingDataScope => {
            "Missing required data scope for seed lot traceability."
        }
    };

    SeedlotInventoryAdjustmentRouteError::forbidden(
        message,
        request_id,
        json!({
            "reason": decision.reason,
            "capabilityId": decision.capability_id,
            "requiredPermission": plan.required_permission,
            "requiredDataScopes": plan.required_data_scopes,
            "missingPermissions": decision.missing_permissions,
            "missingDataScopes": decision.missing_data_scopes,
        }),
    )
}

fn map_seedlot_inventory_adjustment_data_error(
    error: DataStoreError,
    request_id: String,
    operation: &'static str,
) -> SeedlotInventoryAdjustmentRouteError {
    match error {
        DataStoreError::Unavailable => SeedlotInventoryAdjustmentRouteError::internal(
            format!("Rust write repository is not configured for {operation}."),
            request_id,
            json!({ "operation": operation }),
        ),
        DataStoreError::Query(error) => SeedlotInventoryAdjustmentRouteError::internal(
            format!("Rust write repository query failed during {operation}: {error}"),
            request_id,
            json!({
                "operation": operation,
                "error": error.to_string(),
            }),
        ),
    }
}

fn map_seedlot_inventory_adjustment_write_error(
    error: SeedlotInventoryAdjustmentWriteError,
    request_id: String,
    operation: &'static str,
) -> SeedlotInventoryAdjustmentRouteError {
    match error {
        SeedlotInventoryAdjustmentWriteError::Unavailable => {
            SeedlotInventoryAdjustmentRouteError::internal(
                format!("Rust write repository is not configured for {operation}."),
                request_id,
                json!({ "operation": operation }),
            )
        }
        SeedlotInventoryAdjustmentWriteError::InvalidContext(message) => {
            SeedlotInventoryAdjustmentRouteError::validation(
                message.to_string(),
                request_id,
                json!({
                    "operation": operation,
                    "error": message,
                }),
            )
        }
        SeedlotInventoryAdjustmentWriteError::Validation(error) => {
            SeedlotInventoryAdjustmentRouteError::validation(
                error.to_string(),
                request_id,
                json!({
                    "operation": operation,
                    "error": error.to_string(),
                }),
            )
        }
        SeedlotInventoryAdjustmentWriteError::InvalidStoredRecord(column) => {
            SeedlotInventoryAdjustmentRouteError::internal(
                format!("Stored seed lot adjustment data is invalid in {column}."),
                request_id,
                json!({
                    "operation": operation,
                    "column": column,
                }),
            )
        }
        SeedlotInventoryAdjustmentWriteError::NotFound => {
            SeedlotInventoryAdjustmentRouteError::not_found(
                "Seed lot inventory adjustment not found.",
                request_id,
                json!({ "operation": operation }),
            )
        }
        SeedlotInventoryAdjustmentWriteError::AlreadyReversed => {
            SeedlotInventoryAdjustmentRouteError::conflict(
                "Seed lot inventory adjustment has already been reversed.",
                request_id,
                json!({ "operation": operation }),
            )
        }
        SeedlotInventoryAdjustmentWriteError::IdempotencyConflict => {
            SeedlotInventoryAdjustmentRouteError::conflict(
                "Idempotency key replay conflicts with the original request.",
                request_id,
                json!({ "operation": operation }),
            )
        }
        SeedlotInventoryAdjustmentWriteError::AuthorizationDenied(decision) => {
            let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment();
            seedlot_inventory_adjustment_forbidden_error(request_id, &plan, &decision)
        }
        SeedlotInventoryAdjustmentWriteError::Query(error) => {
            SeedlotInventoryAdjustmentRouteError::internal(
                format!("Rust write repository query failed during {operation}: {error}"),
                request_id,
                json!({
                    "operation": operation,
                    "error": error.to_string(),
                }),
            )
        }
    }
}

async fn resolve_active_user(
    headers: &HeaderMap,
    state: &AppState,
) -> Result<ActiveUser, ProtectedRouteError> {
    let token_principal = require_bearer_token(headers, &state.auth_config).await?;
    let user = match token_principal {
        AuthPrincipal::Local {
            user_id,
            organization_id,
            ..
        } => state.data_store.active_user(user_id, organization_id).await,
        AuthPrincipal::Keycloak { issuer, subject } => {
            state
                .data_store
                .active_keycloak_user(&issuer, &subject)
                .await
        }
    };

    user.map_err(|error| match error {
        UserLookupError::Unavailable => ProtectedRouteError::UserRepositoryUnavailable,
        UserLookupError::InvalidCredentials => ProtectedRouteError::InvalidCredentials,
        UserLookupError::Inactive => ProtectedRouteError::InactiveUser,
        UserLookupError::Query(error) => {
            tracing::warn!(%error, route_context = "rust_read_beta_auth", "failed to resolve Rust auth user");
            ProtectedRouteError::UserRepositoryUnavailable
        }
    })
}

async fn require_bearer_token(
    headers: &HeaderMap,
    auth_config: &AuthConfig,
) -> Result<AuthPrincipal, ProtectedRouteError> {
    let Some(value) = headers
        .get(AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
    else {
        return Err(ProtectedRouteError::Unauthenticated);
    };

    let Some(token) = value
        .strip_prefix("Bearer ")
        .map(str::trim)
        .filter(|token| !token.is_empty())
    else {
        return Err(ProtectedRouteError::Unauthenticated);
    };

    auth_config
        .verify_token(token)
        .await
        .map_err(|error| match error {
            AuthError::Invalid => ProtectedRouteError::InvalidCredentials,
            AuthError::Unavailable => ProtectedRouteError::AuthAdapterUnavailable,
            AuthError::ProviderUnavailable => ProtectedRouteError::AuthProviderUnavailable,
        })
}

impl IntoResponse for ProtectedRouteError {
    fn into_response(self) -> Response {
        match self {
            Self::Unauthenticated => {
                let mut response = (
                    StatusCode::UNAUTHORIZED,
                    Json(ErrorDetail {
                        detail: "Not authenticated",
                    }),
                )
                    .into_response();
                response
                    .headers_mut()
                    .insert(WWW_AUTHENTICATE, HeaderValue::from_static("Bearer"));
                response
            }
            Self::InvalidCredentials => {
                let mut response = (
                    StatusCode::UNAUTHORIZED,
                    Json(ErrorDetail {
                        detail: "Could not validate credentials",
                    }),
                )
                    .into_response();
                response
                    .headers_mut()
                    .insert(WWW_AUTHENTICATE, HeaderValue::from_static("Bearer"));
                response
            }
            Self::InactiveUser => (
                StatusCode::BAD_REQUEST,
                Json(ErrorDetail {
                    detail: "Inactive user",
                }),
            )
                .into_response(),
            Self::AuthAdapterUnavailable => (
                StatusCode::NOT_IMPLEMENTED,
                Json(ErrorDetail {
                    detail: "Rust BrAPI auth and persistence adapter is not enabled yet",
                }),
            )
                .into_response(),
            Self::AuthProviderUnavailable => (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(ErrorDetail {
                    detail: "Rust BrAPI auth provider is unavailable",
                }),
            )
                .into_response(),
            Self::UserRepositoryUnavailable => (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(ErrorDetail {
                    detail: "Rust auth user repository is not configured",
                }),
            )
                .into_response(),
            Self::DataRepositoryUnavailable => (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(ErrorDetail {
                    detail: "Rust BrAPI data repository is not configured",
                }),
            )
                .into_response(),
            Self::NotFound(detail) => {
                (StatusCode::NOT_FOUND, Json(ErrorDetail { detail })).into_response()
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::{Request, StatusCode};
    use jsonwebtoken::{Algorithm, EncodingKey, Header, encode};
    use serde::Serialize;
    use tower::ServiceExt;

    use super::*;

    #[derive(Debug, Serialize)]
    struct TestClaims<'a> {
        sub: &'a str,
        organization_id: i64,
        is_superuser: bool,
        exp: i64,
    }

    fn access_token(secret: &str) -> String {
        encode(
            &Header::new(Algorithm::HS256),
            &TestClaims {
                sub: "42",
                organization_id: 7,
                is_superuser: false,
                exp: 4_102_444_800,
            },
            &EncodingKey::from_secret(secret.as_bytes()),
        )
        .unwrap()
    }

    #[tokio::test]
    async fn request_id_header_echoes_valid_caller_id() {
        let response = app(
            AppState::new(env!("CARGO_MANIFEST_DIR")).with_data_store(DataStore::unavailable())
        )
        .oneshot(
            Request::builder()
                .uri("/")
                .header("x-request-id", "client-request-123")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(response.headers()["x-request-id"], "client-request-123");
    }

    #[tokio::test]
    async fn request_id_header_is_generated_when_absent() {
        let response = app(
            AppState::new(env!("CARGO_MANIFEST_DIR")).with_data_store(DataStore::unavailable())
        )
        .oneshot(Request::builder().uri("/").body(Body::empty()).unwrap())
        .await
        .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
        let request_id = response.headers()["x-request-id"].to_str().unwrap();
        assert!(request_id.starts_with("rust-read-"));
        assert!(is_valid_request_id(request_id));
    }

    #[tokio::test]
    async fn invalid_request_id_header_is_replaced() {
        let response = app(
            AppState::new(env!("CARGO_MANIFEST_DIR")).with_data_store(DataStore::unavailable())
        )
        .oneshot(
            Request::builder()
                .uri("/")
                .header("x-request-id", "client request with spaces")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
        let request_id = response.headers()["x-request-id"].to_str().unwrap();
        assert_ne!(request_id, "client request with spaces");
        assert!(request_id.starts_with("rust-read-"));
        assert!(is_valid_request_id(request_id));
    }

    #[tokio::test]
    async fn request_id_header_is_echoed_on_protected_error_responses() {
        let response = app(
            AppState::new(env!("CARGO_MANIFEST_DIR")).with_data_store(DataStore::unavailable())
        )
        .oneshot(
            Request::builder()
                .uri("/brapi/v2/programs")
                .header("x-request-id", "protected-error-123")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["x-request-id"], "protected-error-123");
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[test]
    fn tracing_statements_do_not_log_bearer_or_token_material() {
        let sources = [
            ("lib.rs", include_str!("lib.rs")),
            ("auth.rs", include_str!("auth.rs")),
            ("db.rs", include_str!("db.rs")),
        ];

        for (file, source) in sources {
            for (line_number, line) in source.lines().enumerate() {
                if !line.contains("tracing::") {
                    continue;
                }

                let lower = line.to_ascii_lowercase();
                for forbidden in ["authorization", "bearer", "token"] {
                    assert!(
                        !lower.contains(forbidden),
                        "{file}:{} tracing line should not log {forbidden} material",
                        line_number + 1
                    );
                }
            }
        }
    }

    #[test]
    fn structured_read_error_logs_include_context_fields() {
        let lib_source = include_str!("lib.rs");
        let db_source = include_str!("db.rs");
        let mut read_repository_warnings = 0;

        for line in lib_source
            .lines()
            .filter(|line| line.contains("tracing::warn!(%error"))
        {
            if line.contains("Rust repository") {
                assert!(
                    line.contains("route_context = \"rust_read_beta\""),
                    "read repository query warning should include read-beta context: {line}"
                );
                read_repository_warnings += 1;
            }
            if line.contains("failed to resolve Rust auth user") {
                assert!(
                    line.contains("route_context = \"rust_read_beta_auth\""),
                    "auth repository query warning should include auth read-beta context: {line}"
                );
            }
        }

        assert!(
            read_repository_warnings >= 50,
            "expected migrated read repository query warnings to carry structured context"
        );

        let pool_warning = db_source
            .lines()
            .find(|line| line.contains("failed to configure Rust Postgres pool"))
            .expect("Postgres pool configuration warning should exist");
        assert!(
            pool_warning.contains("route_context = \"rust_read_beta_pool\""),
            "pool configuration warning should include pool read-beta context"
        );
    }

    #[test]
    fn shared_page_size_bounds_match_beta_query_policy() {
        assert_eq!(bounded_page_size(0, 1000), 1);
        assert_eq!(bounded_page_size(1, 1000), 1);
        assert_eq!(bounded_page_size(250, 1000), 250);
        assert_eq!(bounded_page_size(1001, 1000), 1000);
    }

    #[test]
    fn list_query_params_preserve_tenant_scope_and_route_specific_page_bounds() {
        let program_params = ProgramListQuery {
            page: 3,
            page_size: 0,
            program_name: Some("IRRI".to_string()),
            abbreviation: None,
            common_crop_name: Some("Rice".to_string()),
        }
        .params(99);

        assert_eq!(program_params.organization_id, 99);
        assert_eq!(program_params.page, 3);
        assert_eq!(program_params.page_size, 1);
        assert_eq!(program_params.program_name.as_deref(), Some("IRRI"));

        let list_params = ListListQuery {
            page: 2,
            page_size: 5000,
            list_type: Some("germplasm".to_string()),
            list_name: None,
            list_db_id: None,
            list_source: None,
            external_reference_id: None,
            external_reference_source: None,
        }
        .params(99);

        assert_eq!(list_params.organization_id, 99);
        assert_eq!(list_params.page, 2);
        assert_eq!(list_params.page_size, 2000);
        assert_eq!(list_params.list_type.as_deref(), Some("germplasm"));

        let ontology_params = OntologyListQuery {
            page: 1,
            page_size: 50_000,
            ontology_db_id: Some("co-1".to_string()),
            ontology_name: None,
        }
        .params(99);

        assert_eq!(ontology_params.organization_id, 99);
        assert_eq!(ontology_params.page, 1);
        assert_eq!(ontology_params.page_size, 10_000);
        assert_eq!(ontology_params.ontology_db_id.as_deref(), Some("co-1"));
    }

    #[test]
    fn rust_read_beta_router_registers_exactly_one_guarded_write_route() {
        let source = include_str!("lib.rs");
        let app_start = source
            .find("pub fn app")
            .expect("app router function should exist");
        let app_tail = &source[app_start..];
        let app_end = app_tail
            .find("\npub async fn serve")
            .expect("serve function should follow app router function");
        let app_source = &app_tail[..app_end];

        assert_eq!(
            app_source.matches("post(").count(),
            1,
            "Rust server should register exactly one guarded POST route"
        );
        assert!(
            app_source.contains("post(seedlot_inventory_adjustments_create)"),
            "Rust server should register the guarded seedlot adjustment write route"
        );
        assert!(
            app_source.contains("get(seedlot_inventory_adjustments_list)"),
            "Rust server should register the guarded seedlot adjustment history read route"
        );
        assert!(
            app_source.contains("get(seedlot_inventory_adjustments_detail)"),
            "Rust server should register the guarded seedlot adjustment detail read route"
        );
        for forbidden in ["put(", "patch(", "delete("] {
            assert!(
                !app_source.contains(forbidden),
                "Rust server must not register additional write method {forbidden}"
            );
        }
        assert!(app_source.contains("/api/v2/seed-inventory/adjustments"));
    }

    #[tokio::test]
    async fn seedlot_adjustment_candidate_post_route_requires_authentication() {
        let response = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()))
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v2/seed-inventory/adjustments")
                .header("content-type", "application/json")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
    }

    #[test]
    fn protected_read_handlers_resolve_active_user_before_repository_access() {
        for handler in protected_read_handler_names() {
            let body = handler_body(include_str!("lib.rs"), handler);
            let auth_index = body
                .find("resolve_active_user")
                .unwrap_or_else(|| panic!("{handler} should resolve active user"));
            let repo_index = body
                .find("data_store")
                .unwrap_or_else(|| panic!("{handler} should access the repository"));
            assert!(
                auth_index < repo_index,
                "{handler} should resolve active user before repository access"
            );
        }
    }

    #[tokio::test]
    async fn protected_read_route_surface_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        for &uri in protected_read_route_samples() {
            let response = app
                .clone()
                .oneshot(Request::builder().uri(uri).body(Body::empty()).unwrap())
                .await
                .unwrap();

            assert_eq!(
                response.status(),
                StatusCode::UNAUTHORIZED,
                "{uri} should require bearer authentication"
            );
            assert_eq!(
                response.headers()["www-authenticate"],
                "Bearer",
                "{uri} should preserve the FastAPI Bearer challenge"
            );
        }
    }

    fn protected_read_route_samples() -> &'static [&'static str] {
        &[
            "/api/v2/seed-inventory/summary",
            "/api/v2/seed-inventory/adjustments",
            "/api/v2/seed-inventory/adjustments/01900000-0000-7000-8000-000000000001",
            "/brapi/v2/programs",
            "/brapi/v2/programs/program-1",
            "/brapi/v2/locations",
            "/brapi/v2/locations/location-1",
            "/brapi/v2/trials",
            "/brapi/v2/trials/trial-1",
            "/brapi/v2/studies",
            "/brapi/v2/studies/study-1",
            "/brapi/v2/seasons",
            "/brapi/v2/seasons/season-1",
            "/brapi/v2/people",
            "/brapi/v2/people/person-1",
            "/brapi/v2/lists",
            "/brapi/v2/lists/list-1",
            "/brapi/v2/ontologies",
            "/brapi/v2/ontologies/ontology-1",
            "/brapi/v2/germplasm",
            "/brapi/v2/germplasm/germplasm-1",
            "/brapi/v2/attributes",
            "/brapi/v2/attributes/categories",
            "/brapi/v2/attributes/attribute-1",
            "/brapi/v2/attributevalues",
            "/brapi/v2/attributevalues/attribute-value-1",
            "/brapi/v2/breedingmethods",
            "/brapi/v2/breedingmethods/breeding-method-1",
            "/brapi/v2/traits",
            "/brapi/v2/traits/trait-1",
            "/brapi/v2/variables",
            "/brapi/v2/variables/variable-1",
            "/brapi/v2/observations",
            "/brapi/v2/observations/observation-1",
            "/brapi/v2/observationunits",
            "/brapi/v2/observationunits/unit-1",
            "/brapi/v2/methods",
            "/brapi/v2/methods/method-1",
            "/brapi/v2/scales",
            "/brapi/v2/scales/scale-1",
            "/brapi/v2/variantsets",
            "/brapi/v2/variantsets/variant-set-1",
            "/brapi/v2/callsets",
            "/brapi/v2/callsets/call-set-1",
            "/brapi/v2/maps",
            "/brapi/v2/maps/map-1",
            "/brapi/v2/maps/map-1/linkagegroups",
            "/brapi/v2/markerpositions",
            "/brapi/v2/seedlots",
            "/brapi/v2/seedlots/seedlot-1",
            "/brapi/v2/seedlots/transactions",
            "/brapi/v2/seedlots/seedlot-1/transactions",
            "/brapi/v2/crossingprojects",
            "/brapi/v2/crossingprojects/crossing-project-1",
            "/brapi/v2/crosses",
            "/brapi/v2/crosses/cross-1",
            "/brapi/v2/plannedcrosses",
            "/brapi/v2/plannedcrosses/planned-cross-1",
        ]
    }

    fn protected_read_handler_names() -> &'static [&'static str] {
        &[
            "seed_inventory_summary",
            "seedlot_inventory_adjustments_list",
            "seedlot_inventory_adjustments_detail",
            "programs",
            "program",
            "locations",
            "location",
            "trials",
            "trial",
            "studies",
            "study",
            "seasons",
            "season",
            "people",
            "person",
            "lists",
            "list",
            "ontologies",
            "ontology",
            "germplasm_list",
            "germplasm",
            "attributes",
            "attribute_categories",
            "attribute_detail",
            "attribute_values",
            "attribute_value_detail",
            "breeding_methods",
            "breeding_method_detail",
            "traits",
            "trait_detail",
            "variables",
            "variable_detail",
            "observations",
            "observation_detail",
            "observation_units",
            "observation_unit_detail",
            "methods",
            "method_detail",
            "scales",
            "scale_detail",
            "variant_sets",
            "variant_set",
            "callsets",
            "callset",
            "maps",
            "map_detail",
            "map_linkage_groups",
            "marker_positions",
            "seedlots",
            "seedlot",
            "seedlot_transactions",
            "seedlot_transactions_for_seedlot",
            "crossing_projects",
            "crossing_project",
            "crosses",
            "cross",
            "planned_crosses",
            "planned_cross",
        ]
    }

    fn handler_body<'a>(source: &'a str, handler: &str) -> &'a str {
        let start_marker = format!("async fn {handler}(");
        let start = source
            .find(&start_marker)
            .unwrap_or_else(|| panic!("{handler} handler should exist"));
        let tail = &source[start + start_marker.len()..];
        let end = tail.find("\nasync fn ").unwrap_or(tail.len());
        &tail[..end]
    }

    #[tokio::test]
    async fn health_endpoint_returns_success() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR")));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/health")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn brapi_serverinfo_endpoint_returns_success() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR")));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/serverinfo")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn brapi_programs_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/programs")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_program_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/programs/program-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_locations_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/locations")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_location_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/locations/location-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_trials_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/trials")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_trial_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/trials/trial-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_studies_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/studies")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_study_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/studies/study-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_seasons_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/seasons")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_season_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/seasons/season-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_people_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/people")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_person_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/people/person-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_lists_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/lists")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_list_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/lists/list-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_ontologies_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/ontologies")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_ontology_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/ontologies/ontology-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_germplasm_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/germplasm")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_germplasm_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/germplasm/germplasm-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_attributes_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/attributes")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_attribute_categories_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/attributes/categories")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_attribute_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/attributes/attribute-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_attribute_values_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/attributevalues")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_attribute_value_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/attributevalues/attribute-value-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_breeding_methods_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/breedingmethods")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_breeding_method_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/breedingmethods/bm-001")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_traits_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/traits")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_trait_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/traits/variable-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_variables_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/variables")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_variable_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/variables/variable-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_observations_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/observations")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_observation_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/observations/observation-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_observation_units_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/observationunits")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_observation_unit_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/observationunits/unit-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_methods_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/methods")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_method_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/methods/method-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_scales_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/scales")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_scale_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/scales/scale-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_seedlots_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/seedlots")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_variant_sets_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/variantsets")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_variant_set_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/variantsets/variantset-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_callsets_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/callsets")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_callset_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/callsets/callset-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_maps_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/maps")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_map_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/maps/map-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_map_linkage_groups_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/maps/map-1/linkagegroups")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_marker_positions_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/markerpositions")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn seed_inventory_summary_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v2/seed-inventory/summary")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_seedlot_detail_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/seedlots/seedlot-1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_seedlot_transactions_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/seedlots/transactions")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_seedlot_scoped_transactions_requires_bearer_authentication() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/seedlots/seedlot-1/transactions")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_programs_requires_configured_auth_adapter_before_bearer_use() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256(""))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/programs")
                    .header("authorization", "Bearer development-token")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::NOT_IMPLEMENTED);
    }

    #[tokio::test]
    async fn brapi_programs_rejects_invalid_bearer_token() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/programs")
                    .header("authorization", "Bearer development-token")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(response.headers()["www-authenticate"], "Bearer");
    }

    #[tokio::test]
    async fn brapi_programs_validates_local_jwt_before_persistence() {
        let app = app(AppState::new(env!("CARGO_MANIFEST_DIR"))
            .with_auth_config(AuthConfig::local_hs256("secret"))
            .with_data_store(DataStore::unavailable()));

        let response = app
            .oneshot(
                Request::builder()
                    .uri("/brapi/v2/programs")
                    .header(
                        "authorization",
                        format!("Bearer {}", access_token("secret")),
                    )
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::SERVICE_UNAVAILABLE);
    }
}
