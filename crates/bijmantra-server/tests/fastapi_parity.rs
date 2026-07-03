use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use axum::body::{Body, to_bytes};
use axum::http::{HeaderMap, Request, StatusCode};
use bijmantra_server::{AppState, AuthConfig, DataStore, app};
use serde::Deserialize;
use serde_json::{Value, json};
use tower::ServiceExt;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ParityContract {
    routes: Vec<RouteContract>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RouteContract {
    method: String,
    path: String,
    route_status: String,
    status: u16,
    #[serde(default)]
    headers: BTreeMap<String, String>,
    #[serde(default)]
    request_headers: BTreeMap<String, String>,
    #[serde(default)]
    required: Vec<String>,
    #[serde(default)]
    exact: BTreeMap<String, Value>,
    #[serde(default)]
    array_contains: BTreeMap<String, Vec<Value>>,
    #[serde(default)]
    forbidden: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustRouteInventory {
    routes: Vec<RustRouteEntry>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustRouteEntry {
    method: String,
    path: String,
    normalized_path: String,
    surface: String,
    route_status: String,
}

#[derive(Debug)]
struct FastApiRouteSnapshot {
    declared_total: usize,
    rows: Vec<FastApiRouteRow>,
}

#[derive(Debug)]
struct FastApiRouteRow {
    path: String,
    source: String,
    line: usize,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadRouteDiff {
    counts: ReadRouteDiffCounts,
    matched_rust_brapi_routes: Vec<MatchedRustBrapiRoute>,
    rust_brapi_without_fastapi_match: Vec<RustBrapiWithoutFastApiMatch>,
    rust_only_runtime_or_product_reads: Vec<RustOnlyRoute>,
    deferred_fastapi_brapi_routes: Vec<DeferredFastApiRoute>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadRouteDiffCounts {
    rust_read_routes: usize,
    rust_brapi_read_routes: usize,
    fastapi_brapi_get_routes: usize,
    matched_rust_brapi_routes: usize,
    rust_brapi_without_fastapi_match: usize,
    deferred_fastapi_brapi_routes: usize,
    rust_only_runtime_or_product_reads: usize,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct MatchedRustBrapiRoute {
    rust_path: String,
    fastapi_path: String,
    surface: String,
    route_status: String,
    source: String,
    line: usize,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustBrapiWithoutFastApiMatch {
    rust_path: String,
    normalized_path: String,
    surface: String,
    route_status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustOnlyRoute {
    method: String,
    path: String,
    normalized_path: String,
    surface: String,
    route_status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct DeferredFastApiRoute {
    path: String,
    source: String,
    line: usize,
    route_status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadContractExamples {
    examples: Vec<ReadContractExample>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadContractExample {
    name: String,
    surface: String,
    source_contract: String,
    rust_inventory_path: String,
    method: String,
    path: String,
    #[serde(default)]
    request_headers: BTreeMap<String, String>,
    route_status: String,
    expected_status: u16,
    #[serde(default)]
    expected_headers: BTreeMap<String, String>,
    #[serde(default)]
    required: Vec<String>,
    #[serde(default)]
    exact: BTreeMap<String, Value>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadQueryExamples {
    examples: Vec<ReadQueryExample>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadQueryExample {
    name: String,
    category: String,
    surface: String,
    #[serde(default)]
    source_contract: Option<String>,
    rust_inventory_path: String,
    method: String,
    path: String,
    query_parameters: Vec<String>,
    auth_required: bool,
    semantics: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadDocsGate {
    scope: String,
    status: String,
    route_status_taxonomy: Vec<String>,
    surface_families: Vec<String>,
    route_diff_summary: ReadRouteDiffCounts,
    reviewer_path: Vec<DocsGateReviewerPath>,
    link_validation: DocsGateLinkValidation,
    evidence_artifacts: Vec<DocsGateEvidenceArtifact>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct DocsGateReviewerPath {
    name: String,
    file: String,
    required_phrases: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct DocsGateLinkValidation {
    status: String,
    checked_sources: Vec<String>,
    path_prefixes: Vec<String>,
    checked_extensions: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct DocsGateEvidenceArtifact {
    path: String,
    category: String,
    required_in_status_doc: bool,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadLatencySmoke {
    thresholds: ReadLatencyThresholds,
    routes: Vec<ReadLatencyRoute>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadLatencyThresholds {
    max_route_elapsed_ms: u64,
    max_suite_elapsed_ms: u64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadLatencyRoute {
    name: String,
    method: String,
    path: String,
    rust_inventory_path: String,
    expected_status: u16,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadObservabilityPlan {
    scope: String,
    status: String,
    pool_health_plan: PoolHealthPlan,
    request_id_plan: RequestIdPlan,
    production_log_config: ProductionLogConfig,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PoolHealthPlan {
    dependency_name: String,
    current_behavior: String,
    target_behavior: String,
    implementation_steps: Vec<String>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RequestIdPlan {
    incoming_header: String,
    response_header: String,
    target_behavior: String,
    implementation_steps: Vec<String>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ProductionLogConfig {
    local_default: String,
    production_default: String,
    json_recommendation: String,
    plain_recommendation: String,
    required_fields: Vec<String>,
    secret_rules: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadResponseSizeBaseline {
    routes: Vec<ResponseSizeRoute>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ResponseSizeRoute {
    name: String,
    method: String,
    path: String,
    rust_inventory_path: String,
    max_bytes: usize,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadJsonMappingAudit {
    scope: String,
    status: String,
    source_files: Vec<String>,
    mapping_helpers: Vec<String>,
    hotspots: Vec<JsonMappingHotspot>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct JsonMappingHotspot {
    name: String,
    status: String,
    evidence: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadSlowQueryAudit {
    scope: String,
    status: String,
    method: String,
    source_files: Vec<String>,
    heavy_routes: Vec<SlowQueryRoute>,
    watch_list: Vec<SlowQueryWatchItem>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SlowQueryRoute {
    name: String,
    method: String,
    route: String,
    surface: String,
    repository_operation: String,
    fastapi_parity: String,
    query_shape: Vec<String>,
    repository_markers: Vec<String>,
    expected_indexes: Vec<String>,
    index_plan_status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SlowQueryWatchItem {
    route: String,
    reason: String,
    current_mitigation: String,
    follow_up: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadSecurityRiskRegister {
    scope: String,
    status: String,
    sources: Vec<String>,
    risks: Vec<ReadSecurityRisk>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadSecurityRisk {
    id: String,
    area: String,
    risk: String,
    current_controls: Vec<String>,
    evidence: Vec<ReadSecurityRiskEvidence>,
    remaining_work: String,
    lane_decision: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReadSecurityRiskEvidence {
    file: String,
    phrase: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustModuleOwnershipMap {
    scope: String,
    status: String,
    architecture_model: String,
    modules: Vec<RustModuleOwnership>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustModuleOwnership {
    id: String,
    owner_domain: String,
    supporting_domains: Vec<String>,
    capability_ids: Vec<String>,
    route_surfaces: Vec<String>,
    source_files: Vec<String>,
    test_files: Vec<String>,
    read_responsibilities: Vec<String>,
    non_responsibilities: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustGeneratedArtifactAudit {
    scope: String,
    status: String,
    guard_command: String,
    personal_path_policy: PersonalPathPolicy,
    generated_artifacts: Vec<GeneratedArtifact>,
    local_ignored_roots: Vec<LocalIgnoredRoot>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct PersonalPathPolicy {
    forbidden_fragments: Vec<String>,
    placeholder_fragments: Vec<String>,
    evidence_files: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct GeneratedArtifact {
    path: String,
    category: String,
    decision: String,
    producer: String,
    output_root: String,
    contains_personal_home_paths: bool,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct LocalIgnoredRoot {
    path: String,
    reason: String,
    gitignore_pattern: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustArtifactOutputPolicy {
    scope: String,
    status: String,
    allowed_output_roots: Vec<AllowedOutputRoot>,
    script_outputs: Vec<ScriptOutputPolicy>,
    screenshot_policy: ScreenshotPolicy,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct AllowedOutputRoot {
    path: String,
    classification: String,
    tracked: bool,
    gitignore_pattern: Option<String>,
    allowed_file_kinds: Vec<String>,
    personal_path_rule: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ScriptOutputPolicy {
    script: String,
    output_argument: Option<String>,
    default_path: String,
    allowed_root: String,
    configurable: bool,
    fixed_tracked_exception: bool,
    notes: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ScreenshotPolicy {
    current_read_beta_screenshot_helpers: Vec<String>,
    default_root: String,
    rule: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustDependencyBaseline {
    scope: String,
    status: String,
    verified_at: String,
    local_verification: LocalDependencyVerification,
    toolchain_baseline: Vec<ToolchainBaseline>,
    cross_os_command_pairs: Vec<CrossOsCommandPair>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct LocalDependencyVerification {
    platform: String,
    commands: Vec<LocalDependencyCommand>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct LocalDependencyCommand {
    tool: String,
    command: String,
    observed: String,
    status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ToolchainBaseline {
    tool: String,
    required_for: Vec<String>,
    macos_install: String,
    windows_install: String,
    verification_commands: Vec<String>,
    docs: Vec<String>,
    status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct CrossOsCommandPair {
    task: String,
    windows: String,
    macos: String,
    equivalence: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustFirstRunDocsAudit {
    scope: String,
    status: String,
    docs: Vec<String>,
    path_policy: FirstRunPathPolicy,
    first_run_steps: Vec<FirstRunStep>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FirstRunPathPolicy {
    forbidden_concrete_home_path_fragments: Vec<String>,
    allowed_placeholders: Vec<String>,
    required_relative_path_phrases: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FirstRunStep {
    id: String,
    doc: String,
    required_phrases: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustLiveDbOptionalGate {
    scope: String,
    status: String,
    env_var: String,
    default_behavior: String,
    secret_handling: String,
    required_command: Vec<String>,
    helper_commands: Vec<String>,
    ci_gate: LiveDbCiGate,
    fixture_sources: Vec<String>,
    docs_sources: Vec<String>,
    required_fixture_phrases: Vec<String>,
    required_doc_phrases: Vec<String>,
    coverage_claims: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct LiveDbCiGate {
    workflow: String,
    default_command: String,
    requires_env_var_by_default: bool,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustReadSecuritySmoke {
    scope: String,
    status: String,
    run_date: String,
    local_commands: Vec<SecuritySmokeCommand>,
    required_risk_ids: Vec<String>,
    source_files: Vec<String>,
    live_gated: SecuritySmokeLiveGate,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SecuritySmokeCommand {
    name: String,
    command: String,
    status: String,
    coverage: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SecuritySmokeLiveGate {
    env_var: String,
    current_shell_status: String,
    command: String,
    status: String,
    verified_claims: Vec<String>,
    remaining_claims: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustReadBetaReleaseNotes {
    scope: String,
    status: String,
    release_date: String,
    route_diff_source: String,
    route_counts: ReadRouteDiffCounts,
    capabilities: Vec<String>,
    accepted_limits: Vec<String>,
    verification: Vec<ReleaseVerification>,
    fallback_plan: String,
    status_doc: String,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReleaseVerification {
    name: String,
    command: Option<String>,
    artifact: Option<String>,
    status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustReadFallbackPlan {
    scope: String,
    status: String,
    route_diff_source: String,
    fastapi_reference: FallbackFastApiReference,
    rust_beta_boundary: FallbackRustBetaBoundary,
    fallback_rule: String,
    unsupported_route_behavior: Vec<String>,
    rollback_path: Vec<String>,
    deferred_families: Vec<String>,
    evidence: Vec<String>,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FallbackFastApiReference {
    snapshot: String,
    route_count: usize,
    rule: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct FallbackRustBetaBoundary {
    rust_read_routes: usize,
    rust_brapi_read_routes: usize,
    matched_rust_brapi_routes: usize,
    rust_brapi_without_fastapi_match: usize,
    deferred_fastapi_brapi_routes: usize,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustReadBetaReviewArtifact {
    scope: String,
    status: String,
    created_date: String,
    review_surfaces: Vec<String>,
    verification_commands: Vec<ReviewVerificationCommand>,
    ready_checks: Vec<String>,
    accepted_limits: Vec<String>,
    milestone_rows: Vec<u16>,
    next_human_action: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ReviewVerificationCommand {
    name: String,
    command: String,
    status: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct RustReadBetaDeclaration {
    scope: String,
    status: String,
    prepared_date: String,
    review_artifact: String,
    release_notes: String,
    fallback_plan: String,
    security_smoke: String,
    green_checklist: Vec<DeclarationChecklistItem>,
    accepted_limits: Vec<String>,
    declaration_text: String,
    non_goals: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct DeclarationChecklistItem {
    id: String,
    status: String,
    evidence: String,
}

fn contract_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("contracts")
        .join("fastapi-parity")
}

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
}

fn load_contract(name: &str) -> ParityContract {
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} parity contract should be readable: {error}"));
    serde_json::from_str(&raw).expect("parity contract should be valid json")
}

fn load_rust_route_inventory() -> RustRouteInventory {
    let name = "rust-read-routes.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} route inventory should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust route inventory should be valid json")
}

fn load_rust_write_route_inventory() -> RustRouteInventory {
    let name = "rust-write-routes.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} route inventory should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust write route inventory should be valid json")
}

fn load_read_route_diff() -> ReadRouteDiff {
    let name = "read-route-diff.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} route diff should be readable: {error}"));
    serde_json::from_str(&raw).expect("read route diff should be valid json")
}

fn load_read_contract_examples() -> ReadContractExamples {
    let name = "read-contract-examples.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} examples should be readable: {error}"));
    serde_json::from_str(&raw).expect("read contract examples should be valid json")
}

fn load_read_query_examples() -> ReadQueryExamples {
    let name = "read-query-examples.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} examples should be readable: {error}"));
    serde_json::from_str(&raw).expect("read query examples should be valid json")
}

fn load_read_docs_gate() -> ReadDocsGate {
    let name = "read-docs-gate.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} docs gate should be readable: {error}"));
    serde_json::from_str(&raw).expect("read docs gate should be valid json")
}

fn load_read_latency_smoke() -> ReadLatencySmoke {
    let name = "read-latency-smoke.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} latency smoke should be readable: {error}"));
    serde_json::from_str(&raw).expect("read latency smoke should be valid json")
}

fn load_read_observability_plan() -> ReadObservabilityPlan {
    let name = "read-observability-plan.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} observability plan should be readable: {error}"));
    serde_json::from_str(&raw).expect("read observability plan should be valid json")
}

fn load_read_response_size_baseline() -> ReadResponseSizeBaseline {
    let name = "read-response-size-baseline.json";
    let raw = fs::read_to_string(contract_dir().join(name)).unwrap_or_else(|error| {
        panic!("{name} response size baseline should be readable: {error}")
    });
    serde_json::from_str(&raw).expect("read response size baseline should be valid json")
}

fn load_read_json_mapping_audit() -> ReadJsonMappingAudit {
    let name = "read-json-mapping-audit.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} JSON mapping audit should be readable: {error}"));
    serde_json::from_str(&raw).expect("read JSON mapping audit should be valid json")
}

fn load_read_slow_query_audit() -> ReadSlowQueryAudit {
    let name = "read-slow-query-audit.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} slow-query audit should be readable: {error}"));
    serde_json::from_str(&raw).expect("read slow-query audit should be valid json")
}

fn load_read_security_risk_register() -> ReadSecurityRiskRegister {
    let name = "read-security-risk-register.json";
    let raw = fs::read_to_string(contract_dir().join(name)).unwrap_or_else(|error| {
        panic!("{name} security risk register should be readable: {error}")
    });
    serde_json::from_str(&raw).expect("read security risk register should be valid json")
}

fn load_rust_module_ownership_map() -> RustModuleOwnershipMap {
    let name = "rust-module-ownership.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} module ownership map should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust module ownership map should be valid json")
}

fn load_rust_generated_artifact_audit() -> RustGeneratedArtifactAudit {
    let name = "rust-generated-artifact-audit.json";
    let raw = fs::read_to_string(contract_dir().join(name)).unwrap_or_else(|error| {
        panic!("{name} generated-artifact audit should be readable: {error}")
    });
    serde_json::from_str(&raw).expect("Rust generated-artifact audit should be valid json")
}

fn load_rust_artifact_output_policy() -> RustArtifactOutputPolicy {
    let name = "rust-artifact-output-policy.json";
    let raw = fs::read_to_string(contract_dir().join(name)).unwrap_or_else(|error| {
        panic!("{name} artifact-output policy should be readable: {error}")
    });
    serde_json::from_str(&raw).expect("Rust artifact-output policy should be valid json")
}

fn load_rust_dependency_baseline() -> RustDependencyBaseline {
    let name = "rust-dependency-baseline.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} dependency baseline should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust dependency baseline should be valid json")
}

fn load_rust_first_run_docs_audit() -> RustFirstRunDocsAudit {
    let name = "rust-first-run-docs-audit.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} first-run docs audit should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust first-run docs audit should be valid json")
}

fn load_rust_live_db_optional_gate() -> RustLiveDbOptionalGate {
    let name = "rust-live-db-optional-gate.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} live DB optional gate should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust live DB optional gate should be valid json")
}

fn load_rust_read_security_smoke() -> RustReadSecuritySmoke {
    let name = "rust-read-security-smoke.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} security smoke should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust read security smoke should be valid json")
}

fn load_rust_read_beta_release_notes() -> RustReadBetaReleaseNotes {
    let name = "rust-read-beta-release-notes.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} release notes should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust read beta release notes should be valid json")
}

fn load_rust_read_fallback_plan() -> RustReadFallbackPlan {
    let name = "rust-read-fallback-plan.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} fallback plan should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust read fallback plan should be valid json")
}

fn load_rust_read_beta_review_artifact() -> RustReadBetaReviewArtifact {
    let name = "rust-read-beta-review-artifact.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} review artifact should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust read beta review artifact should be valid json")
}

fn load_rust_read_beta_declaration() -> RustReadBetaDeclaration {
    let name = "rust-read-beta-declaration.json";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} declaration should be readable: {error}"));
    serde_json::from_str(&raw).expect("Rust read beta declaration should be valid json")
}

fn assert_repo_relative_path(label: &str, path: &str) {
    assert!(
        !path.trim().is_empty(),
        "{label} should not be an empty artifact path"
    );
    assert!(
        !path.starts_with('/'),
        "{label} should be repository-relative: {path}"
    );
    assert!(
        !path.contains(":\\"),
        "{label} should not contain a Windows absolute path: {path}"
    );
    assert!(
        !path.contains("/Users/") && !path.contains("/home/") && !path.contains("C:\\Users\\"),
        "{label} should not contain a concrete home path: {path}"
    );
}

fn contains_concrete_home_path(text: &str) -> bool {
    for marker in ["/Users/", "/home/"] {
        let mut search_from = 0;
        while let Some(relative_index) = text[search_from..].find(marker) {
            let value_start = search_from + relative_index + marker.len();
            let next = text[value_start..].chars().next();
            if matches!(next, Some(character) if !matches!(character, '<' | '"' | '\'' | ',' | ')' | ']' | '}' | '`' | ' ' | '\t' | '\n' | '\r'))
            {
                return true;
            }
            search_from = value_start;
        }
    }

    let marker = "C:\\Users\\";
    let mut search_from = 0;
    while let Some(relative_index) = text[search_from..].find(marker) {
        let value_start = search_from + relative_index + marker.len();
        let next = text[value_start..].chars().next();
        if matches!(next, Some(character) if !matches!(character, '<' | '"' | '\'' | ',' | ')' | ']' | '}' | '`' | ' ' | '\t' | '\n' | '\r'))
        {
            return true;
        }
        search_from = value_start;
    }

    false
}

fn repo_link_paths(
    text: &str,
    path_prefixes: &[String],
    checked_extensions: &[String],
) -> BTreeSet<String> {
    let mut links = BTreeSet::new();

    for prefix in path_prefixes {
        let mut search_from = 0;
        while let Some(relative_index) = text[search_from..].find(prefix) {
            let start = search_from + relative_index;
            let mut end = start;
            for (offset, character) in text[start..].char_indices() {
                let allowed =
                    character.is_ascii_alphanumeric() || matches!(character, '/' | '-' | '_' | '.');
                if !allowed {
                    break;
                }
                end = start + offset + character.len_utf8();
            }

            let candidate = text[start..end]
                .trim_matches(|character: char| matches!(character, '.' | ',' | ';' | ':'))
                .to_string();
            if checked_extensions
                .iter()
                .any(|extension| candidate.ends_with(extension))
            {
                links.insert(candidate);
            }
            search_from = end.max(start + prefix.len());
        }
    }

    links
}

fn fixture_root() -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock should be after unix epoch")
        .as_nanos();
    let path = std::env::temp_dir().join(format!(
        "bijmantra-server-fastapi-parity-{}-{nonce}",
        std::process::id()
    ));
    fs::create_dir_all(&path).expect("fixture directory should be created");
    fs::write(
        path.join("metrics.json"),
        serde_json::to_vec_pretty(&json!({
            "api": {
                "totalEndpoints": 1906,
                "brapiEndpoints": 249,
                "brapiPublishedEndpoints": 201,
                "brapiExposedEndpoints": 249,
                "brapiCoverage": 100
            }
        }))
        .expect("metrics fixture should serialize"),
    )
    .expect("metrics fixture should be written");
    path
}

async fn request_json(
    root: &Path,
    method: &str,
    uri: &str,
    request_headers: &BTreeMap<String, String>,
) -> (StatusCode, HeaderMap, Value) {
    let mut request = Request::builder().method(method).uri(uri);
    for (name, value) in request_headers {
        request = request.header(name, value);
    }

    let state = AppState::new(root)
        .with_auth_config(AuthConfig::local_hs256("fastapi-parity-secret"))
        .with_data_store(DataStore::unavailable());

    let response = app(state)
        .oneshot(request.body(Body::empty()).expect("request should build"))
        .await
        .expect("router should respond");

    let status = response.status();
    let headers = response.headers().clone();
    let body = to_bytes(response.into_body(), 1024 * 1024)
        .await
        .expect("response body should be readable");
    let json = serde_json::from_slice(&body).expect("response should be json");
    (status, headers, json)
}

async fn request_bytes(
    root: &Path,
    method: &str,
    uri: &str,
    request_headers: &BTreeMap<String, String>,
) -> (StatusCode, HeaderMap, Vec<u8>) {
    let mut request = Request::builder().method(method).uri(uri);
    for (name, value) in request_headers {
        request = request.header(name, value);
    }

    let state = AppState::new(root)
        .with_auth_config(AuthConfig::local_hs256("fastapi-parity-secret"))
        .with_data_store(DataStore::unavailable());

    let response = app(state)
        .oneshot(request.body(Body::empty()).expect("request should build"))
        .await
        .expect("router should respond");

    let status = response.status();
    let headers = response.headers().clone();
    let body = to_bytes(response.into_body(), 1024 * 1024)
        .await
        .expect("response body should be readable")
        .to_vec();
    (status, headers, body)
}

#[tokio::test]
async fn rust_routes_match_fastapi_parity_contracts() {
    let root = fixture_root();
    let contracts = [
        load_contract("public-readonly.json"),
        load_contract("protected-readonly.json"),
    ];

    for route in contracts.into_iter().flat_map(|contract| contract.routes) {
        assert!(
            matches!(route.route_status.as_str(), "done" | "active" | "deferred"),
            "{} should use the shared routeStatus taxonomy",
            route.path
        );

        let (status, headers, body) =
            request_json(&root, &route.method, &route.path, &route.request_headers).await;
        assert_eq!(
            status.as_u16(),
            route.status,
            "{} should preserve FastAPI status",
            route.path
        );

        for (name, expected) in &route.headers {
            let actual = headers
                .get(name)
                .and_then(|value| value.to_str().ok())
                .unwrap_or_else(|| panic!("{} should include response header {name}", route.path));
            assert_eq!(
                actual, expected,
                "{} should preserve FastAPI header {name}",
                route.path
            );
        }

        for required in &route.required {
            assert!(
                json_path(&body, required).is_some(),
                "{} should include required FastAPI field {required}",
                route.path
            );
        }

        for (path, expected) in &route.exact {
            assert_eq!(
                json_path(&body, path),
                Some(expected),
                "{} should preserve FastAPI field {path}",
                route.path
            );
        }

        for (path, expected_items) in &route.array_contains {
            let actual = json_path(&body, path)
                .and_then(Value::as_array)
                .unwrap_or_else(|| panic!("{} field {path} should be an array", route.path));
            for expected in expected_items {
                assert!(
                    actual.contains(expected),
                    "{} field {path} should contain {expected:?}",
                    route.path
                );
            }
        }

        for forbidden in &route.forbidden {
            assert!(
                json_path(&body, forbidden).is_none(),
                "{} should not include forbidden non-FastAPI field {forbidden}",
                route.path
            );
        }
    }
}

#[tokio::test]
async fn read_contract_examples_are_backed_by_contracts_and_router() {
    let root = fixture_root();
    let examples = load_read_contract_examples();
    let public_contract = load_contract("public-readonly.json");
    let protected_contract = load_contract("protected-readonly.json");
    let inventory_paths: BTreeSet<_> = load_rust_route_inventory()
        .routes
        .into_iter()
        .map(|route| route.path)
        .collect();

    for example in examples.examples {
        assert!(
            inventory_paths.contains(&example.rust_inventory_path),
            "{} should point at an existing Rust inventory path",
            example.name
        );
        assert!(
            !example.surface.trim().is_empty(),
            "{} should name its surface",
            example.name
        );

        let source_routes = match example.source_contract.as_str() {
            "public-readonly.json" => &public_contract.routes,
            "protected-readonly.json" => &protected_contract.routes,
            other => panic!("{} references unexpected contract {other}", example.name),
        };
        let contract = source_routes
            .iter()
            .find(|route| {
                route.method == example.method
                    && route.path == example.path
                    && route.request_headers == example.request_headers
            })
            .unwrap_or_else(|| panic!("{} should reference a parity contract route", example.name));

        assert_eq!(
            example.route_status, contract.route_status,
            "{} should mirror contract routeStatus",
            example.name
        );
        assert_eq!(
            example.expected_status, contract.status,
            "{} should mirror contract status",
            example.name
        );
        assert_eq!(
            example.expected_headers, contract.headers,
            "{} should mirror contract headers",
            example.name
        );
        assert_eq!(
            example.required, contract.required,
            "{} should mirror contract required fields",
            example.name
        );
        assert_eq!(
            example.exact, contract.exact,
            "{} should mirror contract exact fields",
            example.name
        );

        let (status, headers, body) = request_json(
            &root,
            &example.method,
            &example.path,
            &example.request_headers,
        )
        .await;
        assert_eq!(
            status.as_u16(),
            example.expected_status,
            "{} should return the documented example status",
            example.name
        );
        for (name, expected) in &example.expected_headers {
            let actual = headers
                .get(name)
                .and_then(|value| value.to_str().ok())
                .unwrap_or_else(|| {
                    panic!("{} should include response header {name}", example.name)
                });
            assert_eq!(
                actual, expected,
                "{} should return the documented example header {name}",
                example.name
            );
        }
        for required in &example.required {
            assert!(
                json_path(&body, required).is_some(),
                "{} should include documented field {required}",
                example.name
            );
        }
        for (path, expected) in &example.exact {
            assert_eq!(
                json_path(&body, path),
                Some(expected),
                "{} should return documented field {path}",
                example.name
            );
        }
    }
}

#[tokio::test]
async fn read_query_examples_target_real_read_routes() {
    let root = fixture_root();
    let examples = load_read_query_examples();
    let public_contract = load_contract("public-readonly.json");
    let protected_contract = load_contract("protected-readonly.json");
    let inventory_paths: BTreeSet<_> = load_rust_route_inventory()
        .routes
        .into_iter()
        .map(|route| route.path)
        .collect();
    let mut categories = BTreeSet::new();

    for example in examples.examples {
        assert!(
            categories.insert(example.category.clone())
                || matches!(example.category.as_str(), "filter" | "pagination"),
            "{} should use a known query example category",
            example.name
        );
        assert!(
            matches!(example.category.as_str(), "filter" | "pagination"),
            "{} should use a known query example category",
            example.name
        );
        assert_eq!(
            example.method, "GET",
            "{} should remain read-only",
            example.name
        );
        assert!(
            !example.surface.trim().is_empty(),
            "{} should name its surface",
            example.name
        );
        assert!(
            !example.semantics.trim().is_empty(),
            "{} should document query semantics",
            example.name
        );
        assert!(
            inventory_paths.contains(&example.rust_inventory_path),
            "{} should point at an existing Rust inventory route",
            example.name
        );
        assert!(
            example
                .path
                .starts_with(&format!("{}?", example.rust_inventory_path)),
            "{} query path should start with its Rust inventory path",
            example.name
        );
        assert!(
            !example.query_parameters.is_empty(),
            "{} should list query parameters",
            example.name
        );
        let actual_query_params = query_parameter_names(&example.path);
        let declared_query_params: BTreeSet<_> = example
            .query_parameters
            .iter()
            .map(String::as_str)
            .collect();
        assert_eq!(
            actual_query_params, declared_query_params,
            "{} should keep queryParameters aligned with the URI",
            example.name
        );

        if example.category == "pagination" {
            assert!(
                declared_query_params.contains("page")
                    && declared_query_params.contains("pageSize"),
                "{} pagination example should include page and pageSize",
                example.name
            );
        }

        if let Some(source_contract) = example.source_contract.as_deref() {
            let source_routes = match source_contract {
                "public-readonly.json" => &public_contract.routes,
                "protected-readonly.json" => &protected_contract.routes,
                other => panic!("{} references unexpected contract {other}", example.name),
            };
            let contract = source_routes
                .iter()
                .find(|route| route.method == example.method && route.path == example.path)
                .unwrap_or_else(|| {
                    panic!(
                        "{} should reference an existing parity contract",
                        example.name
                    )
                });

            let (status, _, body) =
                request_json(&root, &example.method, &example.path, &BTreeMap::new()).await;
            assert_eq!(
                status.as_u16(),
                contract.status,
                "{} should preserve source contract status",
                example.name
            );
            for required in &contract.required {
                assert!(
                    json_path(&body, required).is_some(),
                    "{} should include source contract field {required}",
                    example.name
                );
            }
            for (path, expected) in &contract.exact {
                assert_eq!(
                    json_path(&body, path),
                    Some(expected),
                    "{} should preserve source contract field {path}",
                    example.name
                );
            }
        } else {
            assert!(
                example.auth_required,
                "{} uncontracted query examples should be protected live-data examples",
                example.name
            );
        }
    }

    assert!(
        categories.contains("filter") && categories.contains("pagination"),
        "query examples should cover both filters and pagination"
    );
}

#[tokio::test]
async fn public_read_latency_smoke_stays_within_recorded_budget() {
    let root = fixture_root();
    let smoke = load_read_latency_smoke();
    let inventory_paths: BTreeSet<_> = load_rust_route_inventory()
        .routes
        .into_iter()
        .map(|route| route.path)
        .collect();
    let route_budget = Duration::from_millis(smoke.thresholds.max_route_elapsed_ms);
    let suite_budget = Duration::from_millis(smoke.thresholds.max_suite_elapsed_ms);

    assert!(
        !smoke.routes.is_empty(),
        "latency smoke should exercise public read routes"
    );
    assert!(
        smoke.thresholds.max_route_elapsed_ms > 0 && smoke.thresholds.max_suite_elapsed_ms > 0,
        "latency smoke thresholds should be positive"
    );

    let suite_start = Instant::now();
    for route in smoke.routes {
        assert_eq!(
            route.method, "GET",
            "{} should stay inside the read-only beta",
            route.name
        );
        assert!(
            inventory_paths.contains(&route.rust_inventory_path),
            "{} should point at an existing Rust inventory path",
            route.name
        );
        assert!(
            route.path.starts_with(route.rust_inventory_path.as_str()),
            "{} latency route should target its inventory path",
            route.name
        );

        let started_at = Instant::now();
        let (status, _, body) =
            request_json(&root, &route.method, &route.path, &BTreeMap::new()).await;
        let elapsed = started_at.elapsed();

        assert_eq!(
            status.as_u16(),
            route.expected_status,
            "{} should return the recorded latency smoke status",
            route.name
        );
        assert!(
            !body.is_null(),
            "{} should return a JSON response body",
            route.name
        );
        assert!(
            elapsed <= route_budget,
            "{} exceeded latency smoke route budget: {:?} > {:?}",
            route.name,
            elapsed,
            route_budget
        );
    }

    let suite_elapsed = suite_start.elapsed();
    assert!(
        suite_elapsed <= suite_budget,
        "public read latency smoke exceeded suite budget: {:?} > {:?}",
        suite_elapsed,
        suite_budget
    );
}

#[tokio::test]
async fn public_read_response_size_baseline_stays_under_budget() {
    let root = fixture_root();
    let baseline = load_read_response_size_baseline();
    let inventory_paths: BTreeSet<_> = load_rust_route_inventory()
        .routes
        .into_iter()
        .map(|route| route.path)
        .collect();

    assert!(
        !baseline.routes.is_empty(),
        "response size baseline should exercise public read routes"
    );

    for route in baseline.routes {
        assert_eq!(
            route.method, "GET",
            "{} should stay inside the read-only beta",
            route.name
        );
        assert!(
            inventory_paths.contains(&route.rust_inventory_path),
            "{} should point at an existing Rust inventory path",
            route.name
        );
        assert!(
            route.path.starts_with(route.rust_inventory_path.as_str()),
            "{} response-size route should target its inventory path",
            route.name
        );
        assert!(
            route.max_bytes > 0,
            "{} response-size budget should be positive",
            route.name
        );

        let (status, _, body) =
            request_bytes(&root, &route.method, &route.path, &BTreeMap::new()).await;
        assert_eq!(
            status,
            StatusCode::OK,
            "{} should return a successful public response",
            route.name
        );
        assert!(
            body.len() <= route.max_bytes,
            "{} response exceeded size baseline: {} > {} bytes",
            route.name,
            body.len(),
            route.max_bytes
        );
        let _: Value = serde_json::from_slice(&body)
            .unwrap_or_else(|error| panic!("{} should return JSON: {error}", route.name));
    }
}

#[test]
fn rust_read_route_inventory_matches_app_router_source() {
    let inventory = load_rust_route_inventory();
    let fastapi_brapi_routes = load_fastapi_brapi_snapshot_routes();
    let mut inventory_routes = BTreeSet::new();

    for route in inventory.routes {
        assert_eq!(
            route.normalized_path,
            normalized_fastapi_path(&route.path),
            "{} should carry the normalized FastAPI-comparable path",
            route.path
        );
        if route.path.starts_with("/brapi/v2/") {
            assert!(
                fastapi_brapi_routes.contains(&route.normalized_path),
                "{} should have a normalized FastAPI BrAPI GET route match",
                route.path
            );
        }
        assert_eq!(
            route.method, "GET",
            "{} should stay inside the read-only Rust beta",
            route.path
        );
        assert!(
            matches!(route.route_status.as_str(), "done" | "active" | "deferred"),
            "{} should use the shared routeStatus taxonomy",
            route.path
        );
        assert!(
            inventory_routes.insert((route.method, route.path.clone())),
            "Rust route inventory should not duplicate {}",
            route.path
        );
    }

    let source = fs::read_to_string(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("src/lib.rs"))
        .expect("server lib source should be readable");
    let router_routes = extract_app_routes(&source);
    let read_router_routes: BTreeSet<_> = router_routes
        .into_iter()
        .filter(|(method, _)| method == "GET")
        .collect();

    assert_eq!(
        inventory_routes, read_router_routes,
        "Rust read route inventory should match app router source"
    );
}

#[test]
fn rust_write_route_inventory_matches_app_router_source() {
    let inventory = load_rust_write_route_inventory();
    let source = fs::read_to_string(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("src/lib.rs"))
        .expect("server lib source should be readable");
    let router_routes = extract_app_routes(&source);
    let write_router_routes: BTreeSet<_> = router_routes
        .into_iter()
        .filter(|(method, _)| method == "POST")
        .collect();
    let mut inventory_routes = BTreeSet::new();

    for route in inventory.routes {
        assert_eq!(
            route.method, "POST",
            "Rust write inventory should only contain POST routes"
        );
        assert_eq!(
            route.path, "/api/v2/seed-inventory/adjustments",
            "Rust write inventory should only expose the guarded seedlot adjustment route"
        );
        assert!(
            inventory_routes.insert((route.method, route.path.clone())),
            "Rust write route inventory should not duplicate {}",
            route.path
        );
    }

    assert_eq!(
        inventory_routes, write_router_routes,
        "Rust write route inventory should match app router source"
    );
    assert_eq!(
        inventory_routes.len(),
        1,
        "Rust should expose exactly one public write route"
    );
}

#[test]
fn rust_module_ownership_map_covers_current_read_route_surfaces() {
    let ownership = load_rust_module_ownership_map();
    let inventory = load_rust_route_inventory();

    assert_eq!(ownership.status, "active");
    assert!(
        ownership.scope.contains("Read-only")
            && ownership.scope.contains("No write")
            && ownership.scope.contains("UUID7"),
        "module ownership map should stay inside the read-only/no-UUID7 beta boundary"
    );
    assert!(
        ownership
            .architecture_model
            .contains("bounded Rust runtime island"),
        "module ownership should reflect the accepted Rust architecture boundary"
    );
    assert!(
        !ownership.modules.is_empty(),
        "module ownership map should list owned modules"
    );

    let inventory_surfaces = inventory
        .routes
        .iter()
        .map(|route| route.surface.as_str())
        .collect::<BTreeSet<_>>();
    let mut owned_surfaces = BTreeSet::new();
    let mut module_ids = BTreeSet::new();

    for module in &ownership.modules {
        assert!(
            module_ids.insert(module.id.as_str()),
            "module ownership should not duplicate {}",
            module.id
        );
        assert!(
            !module.owner_domain.trim().is_empty(),
            "{} should name an owner domain",
            module.id
        );
        assert!(
            !module.supporting_domains.is_empty(),
            "{} should name supporting domains",
            module.id
        );
        assert!(
            !module.capability_ids.is_empty(),
            "{} should name capability IDs",
            module.id
        );
        assert!(
            !module.route_surfaces.is_empty(),
            "{} should list route surfaces",
            module.id
        );
        assert!(
            !module.read_responsibilities.is_empty(),
            "{} should describe read responsibilities",
            module.id
        );
        assert!(
            module
                .non_responsibilities
                .iter()
                .any(|item| item.contains("No")
                    && (item.contains("write") || item.contains("UUID7"))),
            "{} should explicitly exclude writes or UUID7 work",
            module.id
        );

        for surface in &module.route_surfaces {
            assert!(
                inventory_surfaces.contains(surface.as_str()),
                "{} should reference an existing Rust route surface {surface}",
                module.id
            );
            owned_surfaces.insert(surface.as_str());
        }
        for path in module.source_files.iter().chain(module.test_files.iter()) {
            assert!(
                workspace_root().join(path).exists(),
                "{} ownership path should exist: {path}",
                module.id
            );
        }
    }

    assert_eq!(
        owned_surfaces, inventory_surfaces,
        "module ownership map should cover every Rust read route surface"
    );
    for required in [
        "rust-runtime-shell",
        "brapi-reference-reads",
        "core-protected-breeding-reads",
        "germplasm-and-phenotyping-reads",
        "seedlot-cross-and-genotyping-reads",
        "read-auth-and-tenant-guard",
    ] {
        assert!(
            module_ids.contains(required),
            "module ownership map should include {required}"
        );
    }
}

#[test]
fn rust_generated_artifact_audit_has_keep_ignore_decisions_without_home_paths() {
    let audit = load_rust_generated_artifact_audit();
    let gitignore =
        fs::read_to_string(workspace_root().join(".gitignore")).expect(".gitignore should exist");

    assert_eq!(audit.status, "active");
    assert!(
        audit.scope.contains("Read-only")
            && audit.scope.contains("No write")
            && audit.scope.contains("UUID7"),
        "generated-artifact audit should stay inside the read-only/no-UUID7 lane"
    );
    assert_eq!(
        audit.guard_command, "uv run python scripts/check_repo_hygiene.py --all-files",
        "generated-artifact audit should use the repo package-manager convention"
    );
    assert!(
        audit
            .personal_path_policy
            .forbidden_fragments
            .iter()
            .any(|fragment| fragment == "/Users/")
            && audit
                .personal_path_policy
                .forbidden_fragments
                .iter()
                .any(|fragment| fragment == "/home/")
            && audit
                .personal_path_policy
                .forbidden_fragments
                .iter()
                .any(|fragment| fragment == "C:\\Users\\"),
        "generated-artifact audit should name the OS home-path patterns it rejects"
    );
    assert!(
        audit
            .personal_path_policy
            .placeholder_fragments
            .iter()
            .any(|fragment| fragment == "<workspace-root>"),
        "generated-artifact audit should prefer placeholders over machine paths"
    );
    for evidence_file in &audit.personal_path_policy.evidence_files {
        assert_repo_relative_path("personal-path policy evidence file", evidence_file);
        assert!(
            workspace_root().join(evidence_file).exists(),
            "{evidence_file} should exist as personal-path policy evidence"
        );
    }

    assert!(
        !audit.generated_artifacts.is_empty(),
        "generated-artifact audit should list tracked artifacts"
    );
    let mut categories = BTreeSet::new();
    for artifact in &audit.generated_artifacts {
        assert_repo_relative_path("generated artifact path", &artifact.path);
        assert_repo_relative_path("generated artifact output root", &artifact.output_root);
        assert!(
            artifact.path.starts_with(&artifact.output_root),
            "{} should live under declared output root {}",
            artifact.path,
            artifact.output_root
        );
        assert_eq!(
            artifact.decision, "keep-tracked",
            "{} should have an explicit keep/ignore decision",
            artifact.path
        );
        assert!(
            !artifact.category.trim().is_empty() && !artifact.producer.trim().is_empty(),
            "{} should classify category and producer",
            artifact.path
        );
        assert!(
            !artifact.contains_personal_home_paths,
            "{} should declare no personal home paths",
            artifact.path
        );
        let artifact_text = fs::read_to_string(workspace_root().join(&artifact.path))
            .unwrap_or_else(|error| {
                panic!(
                    "{} generated artifact should be readable: {error}",
                    artifact.path
                )
            });
        assert!(
            !contains_concrete_home_path(&artifact_text),
            "{} should not contain a concrete user home path",
            artifact.path
        );
        categories.insert(artifact.category.as_str());
    }
    for required_category in [
        "fastapi-reference-snapshot",
        "rust-read-route-inventory",
        "route-diff",
        "artifact-hygiene-audit",
        "artifact-output-policy",
    ] {
        assert!(
            categories.contains(required_category),
            "generated-artifact audit should include {required_category}"
        );
    }

    assert!(
        !audit.local_ignored_roots.is_empty(),
        "generated-artifact audit should list ignored local roots"
    );
    for ignored_root in &audit.local_ignored_roots {
        assert_repo_relative_path("ignored local artifact root", &ignored_root.path);
        assert!(
            !ignored_root.reason.trim().is_empty(),
            "{} should explain why it stays local",
            ignored_root.path
        );
        assert!(
            gitignore.contains(&ignored_root.gitignore_pattern),
            "{} should be covered by .gitignore pattern {}",
            ignored_root.path,
            ignored_root.gitignore_pattern
        );
    }
    assert!(
        audit.non_goals.iter().any(|goal| goal.contains("UUID7")),
        "generated-artifact audit should exclude UUID7 artifacts"
    );
}

#[test]
fn rust_artifact_output_policy_pins_allowed_roots_and_script_outputs() {
    let policy = load_rust_artifact_output_policy();
    let gitignore =
        fs::read_to_string(workspace_root().join(".gitignore")).expect(".gitignore should exist");

    assert_eq!(policy.status, "active");
    assert!(
        policy.scope.contains("Rust read-beta")
            && policy.scope.contains("No write")
            && policy.scope.contains("UUID7"),
        "artifact-output policy should stay inside the read-only/no-UUID7 lane"
    );
    assert!(
        !policy.allowed_output_roots.is_empty(),
        "artifact-output policy should list allowed roots"
    );

    let mut allowed_roots = BTreeSet::new();
    for root in &policy.allowed_output_roots {
        assert_repo_relative_path("allowed output root", &root.path);
        assert!(
            allowed_roots.insert(root.path.as_str()),
            "artifact-output policy should not duplicate root {}",
            root.path
        );
        assert!(
            !root.classification.trim().is_empty()
                && !root.allowed_file_kinds.is_empty()
                && !root.personal_path_rule.trim().is_empty(),
            "{} should classify allowed output behavior",
            root.path
        );
        if root.tracked {
            if let Some(pattern) = &root.gitignore_pattern {
                assert!(
                    gitignore.contains(pattern),
                    "{} tracked root should reference an existing ignored derived subpath {pattern}",
                    root.path
                );
            }
        } else {
            let pattern = root.gitignore_pattern.as_deref().unwrap_or_else(|| {
                panic!(
                    "{} ignored root should name a .gitignore pattern",
                    root.path
                )
            });
            assert!(
                gitignore.contains(pattern),
                "{} ignored root should be covered by .gitignore pattern {pattern}",
                root.path
            );
        }
    }

    assert!(
        !policy.script_outputs.is_empty(),
        "artifact-output policy should list report helper outputs"
    );
    for output in &policy.script_outputs {
        assert_repo_relative_path("script-output script", &output.script);
        assert_repo_relative_path("script-output default path", &output.default_path);
        assert_repo_relative_path("script-output allowed root", &output.allowed_root);
        assert!(
            allowed_roots.contains(output.allowed_root.as_str()),
            "{} should target an allowed output root",
            output.script
        );
        assert!(
            output.default_path.starts_with(&output.allowed_root),
            "{} default path should stay under {}",
            output.default_path,
            output.allowed_root
        );
        assert!(
            !output.notes.trim().is_empty(),
            "{} should explain its output policy",
            output.script
        );

        let source_path = workspace_root().join(&output.script);
        let source = fs::read_to_string(&source_path)
            .unwrap_or_else(|error| panic!("{} should be readable: {error}", output.script));
        if output.configurable {
            let argument = output.output_argument.as_deref().unwrap_or_else(|| {
                panic!(
                    "{} configurable output should name its argument",
                    output.script
                )
            });
            assert!(
                source.contains(argument),
                "{} should expose configurable output argument {argument}",
                output.script
            );
            assert!(
                !output.fixed_tracked_exception,
                "{} should not also be marked as a fixed-output exception",
                output.script
            );
        } else {
            assert!(
                output.fixed_tracked_exception,
                "{} fixed output should be an explicit tracked exception",
                output.script
            );
        }
    }

    assert!(
        policy
            .screenshot_policy
            .current_read_beta_screenshot_helpers
            .is_empty(),
        "read-beta lane should not invent screenshot helpers"
    );
    assert!(
        allowed_roots.contains(policy.screenshot_policy.default_root.as_str()),
        "screenshot default root should be governed by the output policy"
    );
    assert!(
        policy
            .screenshot_policy
            .rule
            .contains("local runtime artifacts"),
        "screenshot policy should keep captures local unless promoted by review"
    );
    assert!(
        policy.non_goals.iter().any(|goal| goal.contains("UUID7")),
        "artifact-output policy should exclude UUID7 artifacts"
    );
}

#[test]
fn rust_dependency_baseline_covers_cross_os_toolchain_and_docs() {
    let baseline = load_rust_dependency_baseline();

    assert_eq!(baseline.status, "active");
    assert!(
        baseline.scope.contains("Rust read-beta")
            && baseline.scope.contains("No write")
            && baseline.scope.contains("UUID7"),
        "dependency baseline should stay inside the read-only/no-UUID7 lane"
    );
    assert_eq!(
        baseline.verified_at, "2026-06-27",
        "dependency baseline should record its verification date"
    );
    assert_eq!(baseline.local_verification.platform, "macOS");

    let local_tools = baseline
        .local_verification
        .commands
        .iter()
        .map(|command| command.tool.as_str())
        .collect::<BTreeSet<_>>();
    for tool in [
        "rustc",
        "cargo",
        "rustup",
        "uv",
        "bun",
        "podman",
        "podman-compose",
    ] {
        assert!(
            local_tools.contains(tool),
            "dependency baseline should include local verification for {tool}"
        );
    }
    for command in &baseline.local_verification.commands {
        assert!(
            !command.command.trim().is_empty()
                && !command.observed.trim().is_empty()
                && command.status == "verified-local",
            "{} should record a verified local command and observed version",
            command.tool
        );
        assert!(
            !command.command.contains("npm ")
                && !command.command.contains("pip ")
                && !command.command.contains("docker "),
            "{} should follow repo package-manager/runtime rules",
            command.tool
        );
    }

    let tools = baseline
        .toolchain_baseline
        .iter()
        .map(|tool| tool.tool.as_str())
        .collect::<BTreeSet<_>>();
    for required_tool in [
        "Rust stable toolchain",
        "Podman with compose",
        "Bun",
        "UV",
        "PowerShell wrapper",
    ] {
        assert!(
            tools.contains(required_tool),
            "dependency baseline should include {required_tool}"
        );
    }

    for tool in &baseline.toolchain_baseline {
        assert!(
            !tool.required_for.is_empty()
                && !tool.macos_install.trim().is_empty()
                && !tool.windows_install.trim().is_empty()
                && !tool.verification_commands.is_empty()
                && !tool.docs.is_empty()
                && !tool.status.trim().is_empty(),
            "{} should describe install, verification, docs, and status",
            tool.tool
        );
        assert!(
            tool.status.contains("macos") || tool.status.contains("windows"),
            "{} should name cross-OS verification/documentation status",
            tool.tool
        );
        for doc in &tool.docs {
            assert_repo_relative_path("dependency baseline doc", doc);
            assert!(
                workspace_root().join(doc).exists(),
                "{} should exist for dependency baseline {}",
                doc,
                tool.tool
            );
        }
        for command in &tool.verification_commands {
            assert!(
                !command.contains("npm ")
                    && !command.contains("pip ")
                    && !command.contains("docker "),
                "{} verification command should follow repo package-manager/runtime rules: {command}",
                tool.tool
            );
        }
    }

    let command_pair_tasks = baseline
        .cross_os_command_pairs
        .iter()
        .map(|pair| pair.task.as_str())
        .collect::<BTreeSet<_>>();
    for task in [
        "format",
        "check",
        "test",
        "doctor",
        "live-postgres-read-tests",
    ] {
        assert!(
            command_pair_tasks.contains(task),
            "dependency baseline should include cross-OS pair for {task}"
        );
    }
    for pair in &baseline.cross_os_command_pairs {
        assert!(
            !pair.windows.trim().is_empty()
                && !pair.macos.trim().is_empty()
                && !pair.equivalence.trim().is_empty(),
            "{} should define Windows and macOS equivalents",
            pair.task
        );
        assert!(
            pair.windows.contains("rust_product.ps1") || pair.windows.contains("$env:"),
            "{} should use the Windows wrapper or PowerShell env syntax",
            pair.task
        );
        assert!(
            pair.macos.contains("cargo") || pair.macos.contains("BIJMANTRA_LIVE_DATABASE_URL"),
            "{} should use macOS shell/Cargo syntax",
            pair.task
        );
    }
    assert!(
        baseline.non_goals.iter().any(|goal| goal.contains("UUID7")),
        "dependency baseline should exclude UUID7 dependency freeze"
    );
}

#[test]
fn rust_first_run_docs_audit_pins_relative_bootstrap_path() {
    let audit = load_rust_first_run_docs_audit();

    assert_eq!(audit.status, "active");
    assert!(
        audit.scope.contains("Rust read-beta")
            && audit.scope.contains("No write")
            && audit.scope.contains("UUID7"),
        "first-run docs audit should stay inside the read-only/no-UUID7 lane"
    );
    assert!(
        audit
            .path_policy
            .forbidden_concrete_home_path_fragments
            .iter()
            .any(|fragment| fragment == "/Users/")
            && audit
                .path_policy
                .forbidden_concrete_home_path_fragments
                .iter()
                .any(|fragment| fragment == "/home/")
            && audit
                .path_policy
                .forbidden_concrete_home_path_fragments
                .iter()
                .any(|fragment| fragment == "C:\\Users\\"),
        "first-run docs audit should name concrete home-path fragments"
    );
    assert!(
        audit
            .path_policy
            .allowed_placeholders
            .iter()
            .any(|placeholder| placeholder == "<workspace-root>"),
        "first-run docs audit should allow workspace placeholders"
    );

    let mut doc_text_by_path = BTreeMap::new();
    for doc in &audit.docs {
        assert_repo_relative_path("first-run doc", doc);
        let text = fs::read_to_string(workspace_root().join(doc))
            .unwrap_or_else(|error| panic!("{doc} first-run doc should be readable: {error}"));
        assert!(
            !contains_concrete_home_path(&text),
            "{doc} should not require a concrete local home path for first run"
        );
        doc_text_by_path.insert(doc.as_str(), text);
    }

    let combined_docs = doc_text_by_path
        .values()
        .map(String::as_str)
        .collect::<Vec<_>>()
        .join("\n");
    for phrase in &audit.path_policy.required_relative_path_phrases {
        assert!(
            combined_docs.contains(phrase),
            "first-run docs should contain relative path phrase {phrase:?}"
        );
    }

    let step_ids = audit
        .first_run_steps
        .iter()
        .map(|step| step.id.as_str())
        .collect::<BTreeSet<_>>();
    for required_step in [
        "read-repo-agent-entry",
        "install-macos-toolchain",
        "verify-windows-entrypoint",
        "run-rust-quick-checks",
        "run-doctor-from-workspace",
        "configure-local-secrets-without-hardcoding",
        "run-read-beta-with-optional-db",
        "review-read-beta-artifacts",
    ] {
        assert!(
            step_ids.contains(required_step),
            "first-run docs audit should include {required_step}"
        );
    }

    for step in &audit.first_run_steps {
        assert!(
            !step.required_phrases.is_empty(),
            "{} should define first-run anchors",
            step.id
        );
        let text = doc_text_by_path
            .get(step.doc.as_str())
            .unwrap_or_else(|| panic!("{} should be listed in first-run docs", step.doc));
        for phrase in &step.required_phrases {
            assert!(
                text.contains(phrase),
                "{} should contain first-run phrase {phrase:?}",
                step.doc
            );
        }
    }
    assert!(
        audit
            .non_goals
            .iter()
            .any(|goal| goal.contains("live database")),
        "first-run docs audit should keep live DB optional"
    );
}

#[test]
fn rust_live_db_optional_gate_is_opt_in_and_secret_safe() {
    let gate = load_rust_live_db_optional_gate();

    assert_eq!(gate.status, "closed");
    assert!(
        gate.scope.contains("Read-only")
            && gate.scope.contains("No write")
            && gate.scope.contains("UUID7"),
        "live DB optional gate should stay inside the read-only/no-UUID7 lane"
    );
    assert_eq!(gate.env_var, "BIJMANTRA_LIVE_DATABASE_URL");
    assert_eq!(gate.default_behavior, "skip-when-unconfigured");
    assert!(
        gate.secret_handling.contains("without recording")
            && gate.secret_handling.contains("printing the database URL"),
        "live DB gate should document secret-safe URL handling"
    );
    assert_eq!(
        gate.required_command,
        vec![
            "cargo",
            "test",
            "-p",
            "bijmantra-server",
            "--test",
            "live_postgres_brapi",
            "--locked",
            "--",
            "--nocapture",
        ],
        "live DB gate should pin the opt-in Rust live fixture command"
    );
    assert!(
        !gate
            .required_command
            .iter()
            .any(|part| part.contains("://")),
        "live DB gate command should not embed a database URL"
    );

    assert_repo_relative_path("live DB CI workflow", &gate.ci_gate.workflow);
    let workflow = fs::read_to_string(workspace_root().join(&gate.ci_gate.workflow))
        .expect("Rust product workflow should be readable");
    assert!(
        workflow.contains(&gate.ci_gate.default_command),
        "workflow should keep the default Rust test command documented by the optional gate"
    );
    assert!(
        !gate.ci_gate.requires_env_var_by_default,
        "default CI should not require BIJMANTRA_LIVE_DATABASE_URL"
    );
    if workflow.contains("BIJMANTRA_LIVE_DATABASE_URL:") {
        assert!(
            workflow.contains("workflow_dispatch")
                && workflow.contains("inputs.live_postgres == 'true'"),
            "BIJMANTRA_LIVE_DATABASE_URL may appear only behind the manual live_postgres workflow-dispatch gate"
        );
    }

    for source in &gate.fixture_sources {
        assert_repo_relative_path("live DB fixture source", source);
        assert!(
            workspace_root().join(source).exists(),
            "{source} live DB fixture source should exist"
        );
    }
    let fixture_text = fs::read_to_string(workspace_root().join(&gate.fixture_sources[0]))
        .expect("live Postgres fixture should be readable");
    for phrase in &gate.required_fixture_phrases {
        assert!(
            fixture_text.contains(phrase),
            "live fixture should contain required optional-gate phrase {phrase:?}"
        );
    }

    let cli_text = fs::read_to_string(workspace_root().join("crates/bijmantra-cli/src/main.rs"))
        .expect("Rust CLI source should be readable");
    assert!(
        cli_text.contains("envConfigured")
            && cli_text.contains("plan.get(\"databaseUrl\").is_none()"),
        "live-test helper should expose configured state and test that no databaseUrl field is emitted"
    );
    assert!(
        cli_text.contains("plan.get(\"url\").is_none()"),
        "live-test helper tests should reject a generic url field"
    );

    let helper_corpus = [
        fs::read_to_string(workspace_root().join("Makefile")).expect("Makefile should be readable"),
        fs::read_to_string(workspace_root().join("scripts/rust_product.ps1"))
            .expect("PowerShell wrapper should be readable"),
    ]
    .join("\n");
    for command in &gate.helper_commands {
        assert!(
            command.contains("live-test"),
            "live DB helper command should route through live-test: {command}"
        );
    }
    assert!(helper_corpus.contains("rust-live-test"));
    assert!(helper_corpus.contains("\"live-test\""));

    let docs_corpus = gate
        .docs_sources
        .iter()
        .map(|source| {
            assert_repo_relative_path("live DB docs source", source);
            fs::read_to_string(workspace_root().join(source))
                .unwrap_or_else(|error| panic!("{source} should be readable: {error}"))
        })
        .collect::<Vec<_>>()
        .join("\n");
    for phrase in &gate.required_doc_phrases {
        assert!(
            docs_corpus.contains(phrase),
            "live DB docs should contain required phrase {phrase:?}"
        );
    }

    let coverage_claims = gate
        .coverage_claims
        .iter()
        .map(String::as_str)
        .collect::<BTreeSet<_>>();
    for claim in [
        "tenant isolation",
        "auth behavior",
        "pagination",
        "sorting",
        "migrated-schema index preflight",
        "seed cleanup",
    ] {
        assert!(
            coverage_claims.contains(claim),
            "live DB gate should claim {claim} coverage"
        );
    }
}

#[test]
fn fastapi_brapi_get_snapshot_is_well_formed_and_unique() {
    let snapshot = load_fastapi_brapi_snapshot();
    assert_eq!(
        snapshot.rows.len(),
        snapshot.declared_total,
        "FastAPI BrAPI GET snapshot row count should match declared total"
    );

    let mut paths = BTreeSet::new();
    for row in snapshot.rows {
        assert!(
            row.path.starts_with('/'),
            "FastAPI BrAPI route should be root-relative: {}",
            row.path
        );
        assert!(
            row.source.starts_with("backend/app/api/brapi/v2/")
                || row.source
                    == "backend/app/domains/germplasm/capabilities/accession_passport/adapters/api/brapi_germplasm.py",
            "{} should come from a declared FastAPI BrAPI source",
            row.source
        );
        assert!(
            row.line > 0,
            "{} should include a positive source line",
            row.path
        );
        assert!(
            paths.insert(row.path.clone()),
            "FastAPI BrAPI GET snapshot should not duplicate {}",
            row.path
        );
    }
}

#[test]
fn read_route_diff_matches_validated_route_sets() {
    let diff = load_read_route_diff();
    let inventory = load_rust_route_inventory();
    let snapshot = load_fastapi_brapi_snapshot();
    let fastapi_paths: BTreeSet<_> = snapshot.rows.iter().map(|row| row.path.as_str()).collect();

    let rust_brapi: Vec<_> = inventory
        .routes
        .iter()
        .filter(|route| route.path.starts_with("/brapi/v2/"))
        .collect();
    let rust_only: Vec<_> = inventory
        .routes
        .iter()
        .filter(|route| !route.path.starts_with("/brapi/v2/"))
        .collect();
    let matched: Vec<_> = rust_brapi
        .iter()
        .copied()
        .filter(|route| fastapi_paths.contains(route.normalized_path.as_str()))
        .collect();
    let unmatched: Vec<_> = rust_brapi
        .iter()
        .copied()
        .filter(|route| !fastapi_paths.contains(route.normalized_path.as_str()))
        .collect();
    let rust_brapi_paths: BTreeSet<_> = rust_brapi
        .iter()
        .map(|route| route.normalized_path.as_str())
        .collect();
    let deferred: Vec<_> = snapshot
        .rows
        .iter()
        .filter(|row| !rust_brapi_paths.contains(row.path.as_str()))
        .collect();

    assert_eq!(diff.counts.rust_read_routes, inventory.routes.len());
    assert_eq!(diff.counts.rust_brapi_read_routes, rust_brapi.len());
    assert_eq!(diff.counts.fastapi_brapi_get_routes, snapshot.rows.len());
    assert_eq!(diff.counts.matched_rust_brapi_routes, matched.len());
    assert_eq!(
        diff.counts.rust_brapi_without_fastapi_match,
        unmatched.len()
    );
    assert_eq!(diff.counts.deferred_fastapi_brapi_routes, deferred.len());
    assert_eq!(
        diff.counts.rust_only_runtime_or_product_reads,
        rust_only.len()
    );

    let expected_matched: BTreeSet<_> = matched
        .iter()
        .map(|route| {
            (
                route.path.as_str(),
                route.normalized_path.as_str(),
                route.surface.as_str(),
                route.route_status.as_str(),
            )
        })
        .collect();
    let actual_matched: BTreeSet<_> = diff
        .matched_rust_brapi_routes
        .iter()
        .map(|route| {
            (
                route.rust_path.as_str(),
                route.fastapi_path.as_str(),
                route.surface.as_str(),
                route.route_status.as_str(),
            )
        })
        .collect();
    assert_eq!(
        actual_matched, expected_matched,
        "route diff should list the computed Rust/FastAPI BrAPI matches"
    );

    let expected_unmatched: BTreeSet<_> = unmatched
        .iter()
        .map(|route| {
            (
                route.path.as_str(),
                route.normalized_path.as_str(),
                route.surface.as_str(),
                route.route_status.as_str(),
            )
        })
        .collect();
    let actual_unmatched: BTreeSet<_> = diff
        .rust_brapi_without_fastapi_match
        .iter()
        .map(|route| {
            (
                route.rust_path.as_str(),
                route.normalized_path.as_str(),
                route.surface.as_str(),
                route.route_status.as_str(),
            )
        })
        .collect();
    assert_eq!(
        actual_unmatched, expected_unmatched,
        "route diff should list every unmatched Rust BrAPI read"
    );

    let expected_rust_only: BTreeSet<_> = rust_only
        .iter()
        .map(|route| {
            (
                route.method.as_str(),
                route.path.as_str(),
                route.normalized_path.as_str(),
                route.surface.as_str(),
                route.route_status.as_str(),
            )
        })
        .collect();
    let actual_rust_only: BTreeSet<_> = diff
        .rust_only_runtime_or_product_reads
        .iter()
        .map(|route| {
            (
                route.method.as_str(),
                route.path.as_str(),
                route.normalized_path.as_str(),
                route.surface.as_str(),
                route.route_status.as_str(),
            )
        })
        .collect();
    assert_eq!(
        actual_rust_only, expected_rust_only,
        "route diff should list Rust-only runtime/product reads"
    );

    let expected_deferred: BTreeSet<_> = deferred
        .iter()
        .map(|row| (row.path.as_str(), row.source.as_str(), row.line, "deferred"))
        .collect();
    let actual_deferred: BTreeSet<_> = diff
        .deferred_fastapi_brapi_routes
        .iter()
        .map(|row| {
            (
                row.path.as_str(),
                row.source.as_str(),
                row.line,
                row.route_status.as_str(),
            )
        })
        .collect();
    assert_eq!(
        actual_deferred, expected_deferred,
        "route diff should list deferred FastAPI BrAPI reads"
    );
}

#[test]
fn fastapi_protected_read_reference_map_has_route_status_for_every_route() {
    let router_source =
        fs::read_to_string(workspace_root().join("backend/app/api/brapi/v2/router.py"))
            .expect("FastAPI BrAPI v2 router should be readable");
    assert!(
        router_source.contains("dependencies=[Depends(get_current_user)]"),
        "FastAPI BrAPI v2 router should keep its router-level auth dependency"
    );

    let snapshot = load_fastapi_brapi_snapshot();
    let diff = load_read_route_diff();
    let snapshot_by_path = snapshot
        .rows
        .iter()
        .map(|row| (row.path.as_str(), row))
        .collect::<BTreeMap<_, _>>();
    let rust_public_reference_delta = BTreeSet::from(["/serverinfo", "/calls", "/commoncropnames"]);
    let mut protected_status_by_path = BTreeMap::new();

    for route in &diff.matched_rust_brapi_routes {
        let row = snapshot_by_path
            .get(route.fastapi_path.as_str())
            .unwrap_or_else(|| {
                panic!(
                    "{} should point at a FastAPI BrAPI GET snapshot route",
                    route.rust_path
                )
            });
        assert_eq!(
            route.source, row.source,
            "{} should keep the FastAPI source file in the route diff",
            route.fastapi_path
        );
        assert_eq!(
            route.line, row.line,
            "{} should keep the FastAPI source line in the route diff",
            route.fastapi_path
        );
        if rust_public_reference_delta.contains(route.fastapi_path.as_str()) {
            assert_eq!(
                route.surface, "brapi-reference",
                "{} should be documented as a Rust beta public reference delta",
                route.fastapi_path
            );
            assert_eq!(
                route.route_status, "done",
                "{} should be complete when exposed as a Rust beta public reference delta",
                route.fastapi_path
            );
        }
        assert!(
            protected_status_by_path
                .insert(
                    route.fastapi_path.as_str(),
                    (route.route_status.as_str(), "matched"),
                )
                .is_none(),
            "{} should receive one FastAPI protected-read parity status",
            route.fastapi_path
        );
    }

    for route in &diff.deferred_fastapi_brapi_routes {
        let row = snapshot_by_path
            .get(route.path.as_str())
            .unwrap_or_else(|| {
                panic!(
                    "{} should point at a FastAPI BrAPI GET snapshot route",
                    route.path
                )
            });
        assert_eq!(
            route.source, row.source,
            "{} should keep the FastAPI source file in the route diff",
            route.path
        );
        assert_eq!(
            route.line, row.line,
            "{} should keep the FastAPI source line in the route diff",
            route.path
        );
        assert!(
            protected_status_by_path
                .insert(
                    route.path.as_str(),
                    (route.route_status.as_str(), "deferred")
                )
                .is_none(),
            "{} should receive one FastAPI protected-read parity status",
            route.path
        );
    }

    assert_eq!(
        protected_status_by_path.len(),
        snapshot.rows.len(),
        "every FastAPI protected BrAPI GET route should have a route diff status"
    );
    for row in &snapshot.rows {
        let (route_status, parity_status) = protected_status_by_path
            .get(row.path.as_str())
            .unwrap_or_else(|| {
                panic!(
                    "{} should have a protected-read parity status in the route diff",
                    row.path
                )
            });
        assert!(
            matches!(*route_status, "done" | "active" | "deferred"),
            "{} should use the shared routeStatus taxonomy",
            row.path
        );
        if *parity_status == "deferred" {
            assert_eq!(
                *route_status, "deferred",
                "{} should use deferred routeStatus when Rust does not implement it",
                row.path
            );
        }
    }
}

#[test]
fn read_docs_gate_matches_route_status_and_reviewer_sources() {
    let gate = load_read_docs_gate();
    let inventory = load_rust_route_inventory();
    let diff = load_read_route_diff();
    let status_doc = fs::read_to_string(contract_dir().join("read-route-status.md"))
        .expect("read route status doc should be readable");

    assert_eq!(
        gate.status, "closed",
        "read docs gate should close only when its verifier is in place"
    );
    assert!(
        gate.scope.contains("Read-only") && gate.scope.contains("No write"),
        "docs gate scope should stay inside the read-only beta boundary"
    );
    assert!(
        gate.scope.contains("No write") && gate.scope.contains("no UUID7"),
        "docs gate scope should explicitly exclude writes and UUID7 migration"
    );

    let taxonomy: BTreeSet<_> = gate
        .route_status_taxonomy
        .iter()
        .map(String::as_str)
        .collect();
    assert_eq!(
        taxonomy,
        BTreeSet::from(["active", "deferred", "done"]),
        "docs gate should use the shared route status taxonomy"
    );

    let inventory_surfaces: BTreeSet<_> = inventory
        .routes
        .iter()
        .map(|route| route.surface.as_str())
        .collect();
    let gate_surfaces: BTreeSet<_> = gate.surface_families.iter().map(String::as_str).collect();
    assert_eq!(
        gate_surfaces, inventory_surfaces,
        "docs gate surface families should match the Rust route inventory"
    );
    for route in &inventory.routes {
        assert!(
            taxonomy.contains(route.route_status.as_str()),
            "{} should use a docs-gate route status",
            route.path
        );
    }

    assert_eq!(
        gate.route_diff_summary.rust_read_routes,
        diff.counts.rust_read_routes
    );
    assert_eq!(
        gate.route_diff_summary.rust_brapi_read_routes,
        diff.counts.rust_brapi_read_routes
    );
    assert_eq!(
        gate.route_diff_summary.fastapi_brapi_get_routes,
        diff.counts.fastapi_brapi_get_routes
    );
    assert_eq!(
        gate.route_diff_summary.matched_rust_brapi_routes,
        diff.counts.matched_rust_brapi_routes
    );
    assert_eq!(
        gate.route_diff_summary.rust_brapi_without_fastapi_match,
        diff.counts.rust_brapi_without_fastapi_match
    );
    assert_eq!(
        gate.route_diff_summary.deferred_fastapi_brapi_routes,
        diff.counts.deferred_fastapi_brapi_routes
    );
    assert_eq!(
        gate.route_diff_summary.rust_only_runtime_or_product_reads,
        diff.counts.rust_only_runtime_or_product_reads
    );

    assert_eq!(
        gate.link_validation.status, "closed",
        "docs-gate link validation should be closed only when Rust tests enforce it"
    );
    let checked_extensions: BTreeSet<_> = gate
        .link_validation
        .checked_extensions
        .iter()
        .map(String::as_str)
        .collect();
    assert!(
        checked_extensions.contains(".md") && checked_extensions.contains(".json"),
        "docs-gate link validation should cover markdown and json control-plane links"
    );
    let checked_sources: BTreeSet<_> = gate
        .link_validation
        .checked_sources
        .iter()
        .map(String::as_str)
        .collect();
    assert!(
        checked_sources.contains("contracts/fastapi-parity/read-docs-gate.json"),
        "docs-gate link validation should include the machine-readable gate"
    );
    for item in &gate.reviewer_path {
        assert!(
            checked_sources.contains(item.file.as_str()),
            "{} should be scanned by docs-gate link validation",
            item.file
        );
    }

    let mut discovered_links = BTreeSet::new();
    for source in &gate.link_validation.checked_sources {
        assert_repo_relative_path("docs-gate link-validation source", source);
        let text = fs::read_to_string(workspace_root().join(source))
            .unwrap_or_else(|error| panic!("{source} should be readable: {error}"));
        let links = repo_link_paths(
            &text,
            &gate.link_validation.path_prefixes,
            &gate.link_validation.checked_extensions,
        );
        assert!(
            !links.is_empty(),
            "{source} should contain repo-local docs-gate links"
        );
        for link in links {
            assert_repo_relative_path("docs-gate internal link", &link);
            assert!(
                workspace_root().join(&link).exists(),
                "{source} links missing docs-gate target {link}"
            );
            discovered_links.insert(link);
        }
    }

    assert!(
        !gate.reviewer_path.is_empty(),
        "docs gate should provide reviewer navigation"
    );
    for item in &gate.reviewer_path {
        let file_path = workspace_root().join(&item.file);
        let text = fs::read_to_string(&file_path)
            .unwrap_or_else(|error| panic!("{} should be readable: {error}", item.file));
        assert!(
            !item.name.trim().is_empty(),
            "{} should name the reviewer step",
            item.file
        );
        assert!(
            !item.required_phrases.is_empty(),
            "{} should define reviewer anchors",
            item.file
        );
        for phrase in &item.required_phrases {
            assert!(
                text.contains(phrase),
                "{} should contain docs-gate phrase {phrase:?}",
                item.file
            );
        }
    }

    assert!(
        !gate.evidence_artifacts.is_empty(),
        "docs gate should list evidence artifacts"
    );
    for artifact in &gate.evidence_artifacts {
        assert!(
            workspace_root().join(&artifact.path).exists(),
            "{} docs-gate artifact should exist",
            artifact.path
        );
        assert!(
            !artifact.category.trim().is_empty(),
            "{} should classify its docs-gate evidence category",
            artifact.path
        );
        if artifact.required_in_status_doc {
            assert!(
                status_doc.contains(&artifact.path),
                "read-route-status.md should link required artifact {}",
                artifact.path
            );
        }
        assert!(
            discovered_links.contains(&artifact.path),
            "{} should be discoverable by docs-gate link validation",
            artifact.path
        );
    }
}

#[test]
fn read_security_risk_register_covers_rls_keycloak_tenant_and_uuid_boundaries() {
    let register = load_read_security_risk_register();

    assert_eq!(register.status, "active");
    assert!(
        register.scope.contains("Read-only")
            && register.scope.contains("No write")
            && register.scope.contains("UUID7"),
        "security risk register should stay inside the read-only/no-UUID7 lane"
    );

    for source in &register.sources {
        assert!(
            workspace_root().join(source).exists(),
            "{source} risk-register source should exist"
        );
    }

    let required_ids = BTreeSet::from([
        "read-tenant-scope-regression",
        "read-org-zero-superuser-widening",
        "read-keycloak-identity-confusion",
        "read-local-token-claim-drift",
        "read-public-reference-auth-delta",
        "read-rls-context-gap",
        "read-uuid7-boundary-creep",
    ]);
    let actual_ids: BTreeSet<_> = register.risks.iter().map(|risk| risk.id.as_str()).collect();
    for id in &required_ids {
        assert!(
            actual_ids.contains(id),
            "security risk register should include {id}"
        );
    }

    let areas: BTreeSet<_> = register
        .risks
        .iter()
        .map(|risk| risk.area.as_str())
        .collect();
    for area in [
        "tenant-isolation",
        "keycloak",
        "auth",
        "auth-posture",
        "rls",
        "uuid7-boundary",
    ] {
        assert!(
            areas.contains(area),
            "security risk register should cover {area}"
        );
    }

    for risk in &register.risks {
        assert!(
            !risk.risk.trim().is_empty(),
            "{} should describe risk",
            risk.id
        );
        assert!(
            !risk.current_controls.is_empty(),
            "{} should list current controls",
            risk.id
        );
        assert!(
            !risk.remaining_work.trim().is_empty(),
            "{} should document remaining work",
            risk.id
        );
        assert!(
            !risk.lane_decision.trim().is_empty(),
            "{} should record the lane decision",
            risk.id
        );
        assert!(
            !risk.evidence.is_empty(),
            "{} should link evidence anchors",
            risk.id
        );

        for evidence in &risk.evidence {
            let path = workspace_root().join(&evidence.file);
            let text = fs::read_to_string(&path)
                .unwrap_or_else(|error| panic!("{} should be readable: {error}", evidence.file));
            assert!(
                text.contains(&evidence.phrase),
                "{} evidence phrase {:?} should exist in {}",
                risk.id,
                evidence.phrase,
                evidence.file
            );
        }
    }

    assert!(
        register.risks.iter().any(|risk| {
            risk.id == "read-keycloak-identity-confusion"
                && risk
                    .current_controls
                    .iter()
                    .any(|control| control.contains("provider, issuer, and subject"))
        }),
        "Keycloak risk should pin provider/issuer/subject controls"
    );
    assert!(
        register.risks.iter().any(|risk| {
            risk.id == "read-uuid7-boundary-creep"
                && risk
                    .remaining_work
                    .contains("separate write-readiness slice")
        }),
        "UUID7 risk should keep write-readiness work separate"
    );
}

#[test]
fn rust_read_security_smoke_records_local_passes_and_live_gate() {
    let smoke = load_rust_read_security_smoke();
    let register = load_read_security_risk_register();

    assert_eq!(smoke.status, "local-and-live-passed");
    assert_eq!(smoke.run_date, "2026-06-29");
    assert!(
        smoke.scope.contains("Read-only")
            && smoke.scope.contains("No write")
            && smoke.scope.contains("UUID7"),
        "security smoke should stay inside the read-only/no-UUID7 lane"
    );
    assert!(
        smoke.local_commands.len() >= 8,
        "security smoke should record the local command set"
    );
    for command in &smoke.local_commands {
        assert_eq!(
            command.status, "passed-local",
            "{} should pass",
            command.name
        );
        assert!(
            command
                .command
                .starts_with("cargo test -p bijmantra-server"),
            "{} should be a Rust server test command",
            command.name
        );
        assert!(
            !command.command.contains("://")
                && !command.command.contains("write")
                && !command.command.contains("UUID7"),
            "{} should not embed URLs or out-of-lane scope",
            command.name
        );
        assert!(
            !command.coverage.is_empty(),
            "{} should record smoke coverage",
            command.name
        );
    }

    let command_names = smoke
        .local_commands
        .iter()
        .map(|command| command.name.as_str())
        .collect::<BTreeSet<_>>();
    for required in [
        "auth-token-unit-smoke",
        "protected-read-route-smoke",
        "security-risk-register-smoke",
        "token-log-hygiene-smoke",
        "protected-error-request-id-smoke",
        "invalid-bearer-smoke",
        "auth-config-required-smoke",
        "jwt-before-persistence-smoke",
    ] {
        assert!(
            command_names.contains(required),
            "security smoke should include {required}"
        );
    }

    let risk_ids = register
        .risks
        .iter()
        .map(|risk| risk.id.as_str())
        .collect::<BTreeSet<_>>();
    for id in &smoke.required_risk_ids {
        assert!(
            risk_ids.contains(id.as_str()),
            "security smoke should reference known risk id {id}"
        );
    }

    let source_corpus = smoke
        .source_files
        .iter()
        .map(|source| {
            assert_repo_relative_path("security smoke source", source);
            fs::read_to_string(workspace_root().join(source))
                .unwrap_or_else(|error| panic!("{source} should be readable: {error}"))
        })
        .collect::<Vec<_>>()
        .join("\n");
    for required_symbol in [
        "protected_read_handlers_resolve_active_user_before_repository_access",
        "protected_read_route_surface_requires_bearer_authentication",
        "tracing_statements_do_not_log_bearer_or_token_material",
        "request_id_header_is_echoed_on_protected_error_responses",
        "brapi_programs_rejects_invalid_bearer_token",
        "brapi_programs_requires_configured_auth_adapter_before_bearer_use",
        "brapi_programs_validates_local_jwt_before_persistence",
        "rejects_keycloak_tokens_with_wrong_audience",
        "verifies_keycloak_rs256_claims_from_cached_jwks",
    ] {
        assert!(
            source_corpus.contains(required_symbol),
            "security smoke source corpus should contain {required_symbol}"
        );
    }

    assert_eq!(smoke.live_gated.env_var, "BIJMANTRA_LIVE_DATABASE_URL");
    assert_eq!(smoke.live_gated.status, "passed-live");
    assert!(
        smoke.live_gated.current_shell_status.contains("configured")
            && smoke
                .live_gated
                .current_shell_status
                .contains("bijmantra-rust-live-postgres")
            && !smoke.live_gated.current_shell_status.contains("://"),
        "security smoke should record the live DB gate without a URL"
    );
    assert!(
        smoke
            .live_gated
            .command
            .contains("--test live_postgres_brapi")
            && !smoke.live_gated.command.contains("://"),
        "live security command should name the fixture without embedding a URL"
    );
    for claim in [
        "wrong-organization JWT rejection against migrated Postgres",
        "missing-user JWT rejection against migrated Postgres",
        "inactive-user rejection against migrated Postgres",
        "tenant A/B exclusion across migrated read families",
        "Keycloak issuer/subject mapping through auth_identities",
    ] {
        assert!(
            smoke
                .live_gated
                .verified_claims
                .iter()
                .any(|verified| verified == claim),
            "security smoke should verify live-gated claim {claim}"
        );
    }
    assert!(
        smoke.live_gated.remaining_claims.is_empty(),
        "security smoke should have no remaining live claims after the live fixture passes"
    );
    assert!(
        smoke
            .non_goals
            .iter()
            .any(|goal| goal.contains("write-route"))
            && smoke.non_goals.iter().any(|goal| goal.contains("UUID7"))
            && smoke
                .non_goals
                .iter()
                .any(|goal| goal.contains("database URL")),
        "security smoke should exclude writes, UUID7, and secret capture"
    );
}

#[test]
fn rust_read_beta_release_notes_match_route_diff_and_limits() {
    let notes = load_rust_read_beta_release_notes();
    let diff = load_read_route_diff();
    let smoke = load_rust_read_security_smoke();

    assert_eq!(notes.status, "stakeholder-ready");
    assert_eq!(notes.release_date, "2026-06-29");
    assert!(
        notes.scope.contains("Read-only")
            && notes.scope.contains("No write")
            && notes.scope.contains("UUID7"),
        "release notes should stay inside the read-only/no-UUID7 lane"
    );
    assert_eq!(
        notes.route_diff_source,
        "contracts/fastapi-parity/read-route-diff.json"
    );
    assert_eq!(
        notes.route_counts.rust_read_routes,
        diff.counts.rust_read_routes
    );
    assert_eq!(
        notes.route_counts.rust_brapi_read_routes,
        diff.counts.rust_brapi_read_routes
    );
    assert_eq!(
        notes.route_counts.fastapi_brapi_get_routes,
        diff.counts.fastapi_brapi_get_routes
    );
    assert_eq!(
        notes.route_counts.matched_rust_brapi_routes,
        diff.counts.matched_rust_brapi_routes
    );
    assert_eq!(
        notes.route_counts.rust_brapi_without_fastapi_match,
        diff.counts.rust_brapi_without_fastapi_match
    );
    assert_eq!(
        notes.route_counts.deferred_fastapi_brapi_routes,
        diff.counts.deferred_fastapi_brapi_routes
    );
    assert_eq!(
        notes.route_counts.rust_only_runtime_or_product_reads,
        diff.counts.rust_only_runtime_or_product_reads
    );

    let capability_text = notes.capabilities.join("\n");
    for required in [
        "58 matched BrAPI GET routes",
        "contract-tested",
        "Keycloak RS256",
        "tenant-scoped",
        "live cleanup",
    ] {
        assert!(
            capability_text.contains(required),
            "release notes capabilities should mention {required}"
        );
    }
    let limits = notes.accepted_limits.join("\n");
    for required in [
        "No write routes",
        "No UUID7 migration",
        "75 FastAPI BrAPI GET routes",
        "FastAPI remains the reference implementation",
        "not yet a full FastAPI backend replacement",
    ] {
        assert!(
            limits.contains(required),
            "release notes accepted limits should mention {required}"
        );
    }

    assert_eq!(
        notes.fallback_plan,
        "contracts/fastapi-parity/rust-read-fallback-plan.json"
    );
    assert_eq!(
        notes.status_doc,
        "contracts/fastapi-parity/read-route-status.md"
    );
    for path in [&notes.fallback_plan, &notes.status_doc] {
        assert!(
            workspace_root().join(path).exists(),
            "{path} release-note target should exist"
        );
    }
    let verification_names = notes
        .verification
        .iter()
        .map(|item| item.name.as_str())
        .collect::<BTreeSet<_>>();
    for required in [
        "full Rust quick suite",
        "route parity suite",
        "live Postgres BrAPI suite",
        "read security smoke",
    ] {
        assert!(
            verification_names.contains(required),
            "release notes should include {required} verification"
        );
    }
    for item in &notes.verification {
        assert!(
            matches!(
                item.status.as_str(),
                "passed-local" | "passed-live" | "local-and-live-passed"
            ),
            "{} should record a passing verification status",
            item.name
        );
        if let Some(command) = &item.command {
            assert!(
                command.starts_with("cargo test") && !command.contains("://"),
                "{} command should be Rust-only and secret-free",
                item.name
            );
        }
        if let Some(artifact) = &item.artifact {
            assert_eq!(
                artifact,
                "contracts/fastapi-parity/rust-read-security-smoke.json"
            );
            assert_eq!(smoke.status, item.status);
        }
    }
    assert!(
        notes
            .non_goals
            .iter()
            .any(|goal| goal.contains("write DTO"))
            && notes.non_goals.iter().any(|goal| goal.contains("UUID7"))
            && notes.non_goals.iter().any(|goal| goal.contains("frontend")),
        "release notes should exclude writes, UUID7, and frontend smoke"
    );
}

#[test]
fn rust_read_fallback_plan_matches_deferred_fastapi_routes() {
    let plan = load_rust_read_fallback_plan();
    let diff = load_read_route_diff();

    assert_eq!(plan.status, "ready-for-review");
    assert!(
        plan.scope.contains("Read-only")
            && plan.scope.contains("No write")
            && plan.scope.contains("UUID7"),
        "fallback plan should stay inside the read-only/no-UUID7 lane"
    );
    assert_eq!(
        plan.route_diff_source,
        "contracts/fastapi-parity/read-route-diff.json"
    );
    assert_eq!(
        plan.fastapi_reference.snapshot,
        "contracts/fastapi-parity/fastapi-brapi-get-routes.md"
    );
    assert_eq!(
        plan.fastapi_reference.route_count,
        diff.counts.fastapi_brapi_get_routes
    );
    assert!(
        plan.fastapi_reference
            .rule
            .contains("FastAPI remains the reference implementation")
            && plan
                .fastapi_reference
                .rule
                .contains("deferred BrAPI GET routes"),
        "fallback plan should keep FastAPI as deferred-route reference"
    );
    assert_eq!(
        plan.rust_beta_boundary.rust_read_routes,
        diff.counts.rust_read_routes
    );
    assert_eq!(
        plan.rust_beta_boundary.rust_brapi_read_routes,
        diff.counts.rust_brapi_read_routes
    );
    assert_eq!(
        plan.rust_beta_boundary.matched_rust_brapi_routes,
        diff.counts.matched_rust_brapi_routes
    );
    assert_eq!(
        plan.rust_beta_boundary.rust_brapi_without_fastapi_match,
        diff.counts.rust_brapi_without_fastapi_match
    );
    assert_eq!(
        plan.rust_beta_boundary.deferred_fastapi_brapi_routes,
        diff.counts.deferred_fastapi_brapi_routes
    );
    assert!(
        plan.fallback_rule
            .contains("implemented read-beta GET surface")
            && plan.fallback_rule.contains("FastAPI"),
        "fallback rule should route unsupported reads back to FastAPI"
    );
    let unsupported = plan.unsupported_route_behavior.join("\n");
    for required in [
        "Do not silently expose deferred FastAPI read families in Rust.",
        "Do not add Rust write routes",
        "Do not introduce UUID7",
    ] {
        assert!(
            unsupported.contains(required),
            "fallback unsupported behavior should mention {required}"
        );
    }
    let rollback = plan.rollback_path.join("\n");
    for required in [
        "Keep FastAPI deployment",
        "Route clients back to FastAPI",
        "Disable Rust beta routing",
        "read-route-diff.json",
    ] {
        assert!(
            rollback.contains(required),
            "fallback rollback path should mention {required}"
        );
    }
    for path in &plan.evidence {
        assert_repo_relative_path("fallback evidence", path);
        assert!(
            workspace_root().join(path).exists(),
            "{path} fallback evidence should exist"
        );
    }
    assert!(
        plan.deferred_families.len() >= 10
            && plan
                .deferred_families
                .iter()
                .any(|family| family == "variants")
            && plan
                .deferred_families
                .iter()
                .any(|family| family == "search-result reads"),
        "fallback plan should summarize major deferred read families"
    );
    assert!(
        plan.non_goals.iter().any(|goal| goal.contains("write"))
            && plan.non_goals.iter().any(|goal| goal.contains("frontend"))
            && plan.non_goals.iter().any(|goal| goal.contains("UUID7")),
        "fallback plan should exclude writes, frontend routing, and UUID7"
    );
}

#[test]
fn rust_read_beta_review_artifact_links_green_read_beta_evidence() {
    let artifact = load_rust_read_beta_review_artifact();
    let release_notes = load_rust_read_beta_release_notes();
    let fallback = load_rust_read_fallback_plan();
    let smoke = load_rust_read_security_smoke();

    assert_eq!(artifact.status, "ready-for-review");
    assert_eq!(artifact.created_date, "2026-06-29");
    assert!(
        artifact.scope.contains("Read-only")
            && artifact.scope.contains("No write")
            && artifact.scope.contains("UUID7"),
        "review artifact should stay inside the read-only/no-UUID7 lane"
    );

    let surfaces = artifact
        .review_surfaces
        .iter()
        .map(String::as_str)
        .collect::<BTreeSet<_>>();
    for required in [
        "contracts/fastapi-parity/read-route-status.md",
        "contracts/fastapi-parity/read-route-diff.json",
        "contracts/fastapi-parity/rust-read-beta-release-notes.json",
        "contracts/fastapi-parity/rust-read-fallback-plan.json",
        "contracts/fastapi-parity/rust-read-security-smoke.json",
        "contracts/fastapi-parity/rust-live-db-optional-gate.json",
    ] {
        assert!(
            surfaces.contains(required),
            "review artifact should include {required}"
        );
        assert!(
            workspace_root().join(required).exists(),
            "{required} review surface should exist"
        );
    }
    assert_eq!(release_notes.status, "stakeholder-ready");
    assert_eq!(fallback.status, "ready-for-review");
    assert_eq!(smoke.status, "local-and-live-passed");

    let command_names = artifact
        .verification_commands
        .iter()
        .map(|command| command.name.as_str())
        .collect::<BTreeSet<_>>();
    for required in [
        "route parity and artifact gate",
        "full Rust quick suite",
        "live Postgres BrAPI suite",
    ] {
        assert!(
            command_names.contains(required),
            "review artifact should include {required} verification"
        );
    }
    for command in &artifact.verification_commands {
        assert!(
            command.command.starts_with("cargo test") && !command.command.contains("://"),
            "{} should be a secret-free Rust test command",
            command.name
        );
        assert!(
            matches!(command.status.as_str(), "passed-local" | "passed-live"),
            "{} should have a passing status",
            command.name
        );
    }

    let ready = artifact.ready_checks.join("\n");
    for required in [
        "58 matched Rust BrAPI GET routes",
        "75 FastAPI BrAPI GET routes remain deferred",
        "Security smoke passed",
        "Tracked artifacts do not record the live database URL",
    ] {
        assert!(
            ready.contains(required),
            "review artifact ready checks should mention {required}"
        );
    }
    let limits = artifact.accepted_limits.join("\n");
    for required in [
        "FastAPI remains the reference implementation",
        "Rust beta is read-only",
        "Write routes",
        "UUID7 migration",
        "frontend smoke",
    ] {
        assert!(
            limits.contains(required),
            "review artifact accepted limits should mention {required}"
        );
    }
    assert_eq!(artifact.milestone_rows, vec![322, 326, 327, 328, 329]);
    assert!(
        artifact
            .next_human_action
            .contains("accept the Rust API Beta declaration")
            && artifact.next_human_action.contains("documented limits"),
        "review artifact should name the next human acceptance action"
    );
}

#[test]
fn rust_read_beta_declaration_is_ready_but_preserves_human_acceptance_gate() {
    let declaration = load_rust_read_beta_declaration();
    let review_artifact = load_rust_read_beta_review_artifact();
    let release_notes = load_rust_read_beta_release_notes();
    let fallback = load_rust_read_fallback_plan();
    let smoke = load_rust_read_security_smoke();

    assert_eq!(declaration.status, "ready-for-human-acceptance");
    assert_eq!(declaration.prepared_date, "2026-06-29");
    assert!(
        declaration.scope.contains("Read-only")
            && declaration.scope.contains("No write")
            && declaration.scope.contains("UUID7"),
        "declaration should stay inside the read-only/no-UUID7 lane"
    );
    assert_eq!(
        declaration.review_artifact,
        "contracts/fastapi-parity/rust-read-beta-review-artifact.json"
    );
    assert_eq!(
        declaration.release_notes,
        "contracts/fastapi-parity/rust-read-beta-release-notes.json"
    );
    assert_eq!(
        declaration.fallback_plan,
        "contracts/fastapi-parity/rust-read-fallback-plan.json"
    );
    assert_eq!(
        declaration.security_smoke,
        "contracts/fastapi-parity/rust-read-security-smoke.json"
    );
    assert_eq!(review_artifact.status, "ready-for-review");
    assert_eq!(release_notes.status, "stakeholder-ready");
    assert_eq!(fallback.status, "ready-for-review");
    assert_eq!(smoke.status, "local-and-live-passed");

    let mut pending = Vec::new();
    let checklist_ids = declaration
        .green_checklist
        .iter()
        .map(|item| item.id.as_str())
        .collect::<BTreeSet<_>>();
    for required in [
        "route-parity",
        "docs-gate",
        "full-rust-quick-suite",
        "live-postgres-suite",
        "security-smoke",
        "release-notes",
        "fallback-plan",
        "human-acceptance",
    ] {
        assert!(
            checklist_ids.contains(required),
            "declaration checklist should include {required}"
        );
    }
    for item in &declaration.green_checklist {
        assert!(
            !item.evidence.trim().is_empty(),
            "{} should include evidence",
            item.id
        );
        if item.status == "pending" {
            pending.push(item.id.as_str());
        } else {
            assert_eq!(
                item.status, "green",
                "{} should be green or pending",
                item.id
            );
            if item.evidence.starts_with("contracts/") {
                assert!(
                    workspace_root().join(&item.evidence).exists(),
                    "{} evidence file should exist",
                    item.id
                );
            } else {
                assert!(
                    item.evidence.starts_with("cargo test"),
                    "{} command evidence should be a Rust test command",
                    item.id
                );
            }
        }
    }
    assert_eq!(
        pending,
        vec!["human-acceptance"],
        "only human acceptance should remain pending"
    );

    let limits = declaration.accepted_limits.join("\n");
    for required in [
        "read-only GET routes",
        "FastAPI remains reference",
        "No write routes",
        "UUID7 migration",
        "frontend smoke",
        "packaging release",
    ] {
        assert!(
            limits.contains(required),
            "declaration accepted limits should mention {required}"
        );
    }
    assert!(
        declaration
            .declaration_text
            .contains("ready for human acceptance")
            && declaration.declaration_text.contains("read-only scope"),
        "declaration text should preserve the acceptance boundary"
    );
    assert!(
        declaration
            .non_goals
            .iter()
            .any(|goal| goal.contains("No team acceptance"))
            && declaration
                .non_goals
                .iter()
                .any(|goal| goal.contains("UUID7"))
            && declaration
                .non_goals
                .iter()
                .any(|goal| goal.contains("frontend")),
        "declaration should avoid fake acceptance and out-of-scope claims"
    );
}

#[test]
fn read_observability_plan_documents_pool_health_path() {
    let plan = load_read_observability_plan();
    let status_doc = fs::read_to_string(contract_dir().join("read-route-status.md"))
        .expect("read route status doc should be readable");

    assert_eq!(plan.status, "active");
    assert!(
        plan.scope.contains("Read-only") && plan.scope.contains("No write"),
        "observability plan should stay inside the read-only beta boundary"
    );
    assert!(
        plan.scope.contains("no UUID7"),
        "observability plan should exclude UUID7 migration"
    );

    let pool_plan = plan.pool_health_plan;
    assert_eq!(
        pool_plan.dependency_name, "postgres_read_repository",
        "pool health plan should name the future health dependency"
    );
    assert!(
        pool_plan.current_behavior.contains("/health")
            && pool_plan.current_behavior.contains("503"),
        "pool health plan should describe current health and protected-read failure behavior"
    );
    for expected in [
        "BIJMANTRA_DATABASE_URL",
        "DATABASE_URL",
        "/health",
        "non-critical",
        "omit the dependency",
    ] {
        assert!(
            pool_plan.target_behavior.contains(expected),
            "pool health target behavior should mention {expected}"
        );
    }
    assert!(
        pool_plan
            .implementation_steps
            .iter()
            .any(|step| step.contains("SELECT 1")),
        "pool health plan should call for a cheap live pool check"
    );
    assert!(
        pool_plan
            .implementation_steps
            .iter()
            .any(|step| step.contains("non-critical")),
        "pool health plan should preserve read-beta fallback semantics"
    );
    assert!(
        pool_plan
            .non_goals
            .iter()
            .any(|goal| goal.contains("Do not make an unconfigured optional read repository")),
        "pool health plan should preserve the no-DB public health contract"
    );
    assert!(
        pool_plan
            .non_goals
            .iter()
            .any(|goal| goal.contains("tokens")),
        "pool health plan should keep credential and token material out of logs"
    );
    assert!(
        status_doc.contains("contracts/fastapi-parity/read-observability-plan.json")
            && status_doc.contains("## Pool Health Plan"),
        "read-route-status.md should link and summarize the pool health plan"
    );
}

#[test]
fn read_observability_plan_documents_request_id_and_log_config() {
    let plan = load_read_observability_plan();
    let status_doc = fs::read_to_string(contract_dir().join("read-route-status.md"))
        .expect("read route status doc should be readable");

    let request_id = plan.request_id_plan;
    assert_eq!(request_id.incoming_header, "x-request-id");
    assert_eq!(request_id.response_header, "x-request-id");
    for expected in [
        "Accept a caller-supplied `x-request-id`",
        "generate one when absent",
        "request tracing spans",
        "read repository warning fields",
    ] {
        assert!(
            request_id.target_behavior.contains(expected),
            "request ID plan should mention {expected}"
        );
    }
    assert!(
        request_id
            .implementation_steps
            .iter()
            .any(|step| step.contains("incoming ID propagation")),
        "request ID plan should include propagation tests"
    );
    assert!(
        request_id
            .non_goals
            .iter()
            .any(|goal| goal.contains("bearer tokens") && goal.contains("database URLs")),
        "request ID plan should keep secrets out of correlation IDs"
    );

    let log_config = plan.production_log_config;
    assert!(
        log_config.local_default.contains("bijmantra_server=debug")
            && log_config
                .production_default
                .contains("bijmantra_server=info"),
        "log config should distinguish local and production defaults"
    );
    assert!(
        log_config.json_recommendation.contains("production")
            && log_config.plain_recommendation.contains("local"),
        "log config should document JSON and plain guidance"
    );
    for expected in [
        "timestamp",
        "level",
        "target",
        "route_context",
        "repository_operation",
        "elapsed_ms",
        "request_id",
    ] {
        assert!(
            log_config
                .required_fields
                .iter()
                .any(|field| field == expected),
            "production log config should include required field {expected}"
        );
    }
    assert!(
        log_config
            .secret_rules
            .iter()
            .any(|rule| rule.contains("authorization headers") && rule.contains("bearer tokens")),
        "production log config should document secret redaction rules"
    );
    assert!(
        status_doc.contains("## Request ID Plan")
            && status_doc.contains("## Production Log Config")
            && status_doc.contains("x-request-id"),
        "read-route-status.md should summarize request ID and production log plans"
    );
}

#[test]
fn read_slow_query_audit_matches_routes_repositories_and_indexes() {
    let audit = load_read_slow_query_audit();
    assert_eq!(audit.status, "audited");
    assert!(
        audit.scope.contains("Read-only") && audit.scope.contains("No write"),
        "slow-query audit should stay inside the read-only beta boundary"
    );
    assert!(
        audit.scope.contains("UUID7"),
        "slow-query audit should explicitly exclude UUID7 migration"
    );
    assert!(
        audit.method.contains("Static audit")
            && audit.method.contains("not a production latency benchmark"),
        "slow-query audit should describe its static source/index-plan method"
    );

    for source_file in &audit.source_files {
        assert!(
            workspace_root().join(source_file).exists(),
            "{source_file} should exist for the slow-query audit"
        );
    }

    let inventory = load_rust_route_inventory();
    let route_lookup: BTreeMap<_, _> = inventory
        .routes
        .iter()
        .map(|route| ((route.method.as_str(), route.path.as_str()), route))
        .collect();
    let diff = load_read_route_diff();
    let matched_routes: BTreeSet<_> = diff
        .matched_rust_brapi_routes
        .iter()
        .map(|route| route.rust_path.as_str())
        .collect();

    let db_source = fs::read_to_string(workspace_root().join("crates/bijmantra-server/src/db.rs"))
        .expect("db.rs should be readable");
    let live_fixture_source = fs::read_to_string(
        workspace_root().join("crates/bijmantra-server/tests/live_postgres_brapi.rs"),
    )
    .expect("live Postgres fixture should be readable");
    let status_doc = fs::read_to_string(contract_dir().join("read-route-status.md"))
        .expect("read route status doc should be readable");

    assert!(
        audit.heavy_routes.len() >= 8,
        "slow-query audit should cover representative high-fanout read routes"
    );

    let allowed_index_plan_statuses = BTreeSet::from(["covered", "watchlist"]);
    let mut audited_names = BTreeSet::new();
    let mut audited_routes = BTreeSet::new();
    let mut watch_status_routes = BTreeSet::new();

    for route in &audit.heavy_routes {
        assert!(
            audited_names.insert(route.name.as_str()),
            "{} should be unique in the slow-query audit",
            route.name
        );
        assert!(
            audited_routes.insert(route.route.as_str()),
            "{} should be unique in the slow-query audit",
            route.route
        );
        assert_eq!(
            route.method, "GET",
            "{} should remain read-only",
            route.name
        );
        let inventory_route = route_lookup
            .get(&(route.method.as_str(), route.route.as_str()))
            .unwrap_or_else(|| {
                panic!("{} should target a maintained Rust read route", route.route)
            });
        assert_eq!(
            inventory_route.surface, route.surface,
            "{} should keep its audited surface in sync with route inventory",
            route.route
        );
        assert_eq!(
            route.fastapi_parity, "matched",
            "{} should explicitly name FastAPI route-diff status",
            route.route
        );
        assert!(
            matched_routes.contains(route.route.as_str()),
            "{} should be matched in read-route-diff.json",
            route.route
        );

        let timer_marker = format!(
            "ReadRepositoryTimer::start(\"{}\")",
            route.repository_operation
        );
        assert!(
            db_source.contains(&timer_marker),
            "{} should point at a timed repository operation",
            route.repository_operation
        );
        for marker in &route.repository_markers {
            assert!(
                db_source.contains(marker),
                "{} should retain slow-query marker {marker:?}",
                route.repository_operation
            );
        }
        assert!(
            route
                .query_shape
                .iter()
                .any(|shape| shape.contains("organization_id")),
            "{} should document tenant-filter shape",
            route.name
        );
        assert!(
            route
                .query_shape
                .iter()
                .any(|shape| shape.contains("LIMIT/OFFSET")),
            "{} should document pagination shape",
            route.name
        );
        assert!(
            allowed_index_plan_statuses.contains(route.index_plan_status.as_str()),
            "{} should use an allowed index-plan status",
            route.name
        );
        if route.index_plan_status == "watchlist" {
            watch_status_routes.insert(route.route.as_str());
        }
        assert!(
            !route.expected_indexes.is_empty(),
            "{} should name expected migrated-schema indexes",
            route.name
        );
        for index in &route.expected_indexes {
            assert!(
                live_fixture_source.contains(index),
                "{} should be covered by the live index preflight",
                index
            );
        }
    }

    let watch_routes: BTreeSet<_> = audit
        .watch_list
        .iter()
        .map(|watch| watch.route.as_str())
        .collect();
    assert_eq!(
        watch_routes, watch_status_routes,
        "every watch-list route should have matching route-level status"
    );
    for watch in &audit.watch_list {
        assert!(
            audited_routes.contains(watch.route.as_str()),
            "{} should refer to an audited heavy route",
            watch.route
        );
        assert!(
            !watch.reason.trim().is_empty()
                && !watch.current_mitigation.trim().is_empty()
                && !watch.follow_up.trim().is_empty(),
            "{} should include reason, mitigation, and follow-up",
            watch.route
        );
    }

    assert!(
        status_doc.contains("contracts/fastapi-parity/read-slow-query-audit.json")
            && status_doc.contains("## Slow Query Audit"),
        "read-route-status.md should link and summarize the slow-query audit"
    );
    assert!(
        audit
            .non_goals
            .iter()
            .any(|goal| goal.contains("write APIs") && goal.contains("write-route")),
        "slow-query audit should exclude write API work"
    );
    assert!(
        audit.non_goals.iter().any(|goal| goal.contains("UUID7")),
        "slow-query audit should exclude UUID7 migration work"
    );
}

#[test]
fn read_json_mapping_audit_matches_current_sources() {
    let audit = load_read_json_mapping_audit();
    assert_eq!(audit.status, "audited");
    assert!(
        audit.scope.contains("Read-only") && audit.scope.contains("No write"),
        "JSON mapping audit should stay inside the read-only beta boundary"
    );
    assert!(
        audit.scope.contains("UUID7"),
        "JSON mapping audit should explicitly exclude UUID7 migration"
    );

    for source_file in &audit.source_files {
        assert!(
            workspace_root().join(source_file).exists(),
            "{source_file} should exist for the JSON mapping audit"
        );
    }

    let db_source = fs::read_to_string(workspace_root().join("crates/bijmantra-server/src/db.rs"))
        .expect("db.rs should be readable");
    let lib_source =
        fs::read_to_string(workspace_root().join("crates/bijmantra-server/src/lib.rs"))
            .expect("lib.rs should be readable");
    let brapi_source =
        fs::read_to_string(workspace_root().join("crates/bijmantra-core/src/brapi.rs"))
            .expect("brapi.rs should be readable");

    for helper in &audit.mapping_helpers {
        assert!(
            db_source.contains(&format!("fn {helper}")),
            "JSON mapping helper {helper} should exist in db.rs"
        );
    }
    assert!(
        !db_source.contains("serde_json::to_string") && !db_source.contains("serde_json::from_str"),
        "row mapping should avoid JSON string round-trips"
    );
    assert!(
        lib_source
            .matches("serde_json::to_value(BrApiSingleResponse::from_item")
            .count()
            >= 5,
        "BrAPI helper detail fallbacks should remain explicit and auditable"
    );
    assert!(
        brapi_source.contains("BrApiSingleResponse") && brapi_source.contains("BrApiListResponse"),
        "typed BrAPI DTOs should remain the response serialization boundary"
    );

    let hotspot_names: BTreeSet<_> = audit
        .hotspots
        .iter()
        .map(|hotspot| hotspot.name.as_str())
        .collect();
    for expected in [
        "json-column-pass-through",
        "brapi-null-detail-fallbacks",
        "public-in-memory-responses",
    ] {
        assert!(
            hotspot_names.contains(expected),
            "JSON mapping audit should name hotspot {expected}"
        );
    }
    for hotspot in &audit.hotspots {
        assert_eq!(hotspot.status, "acceptable");
        assert!(
            !hotspot.evidence.trim().is_empty(),
            "{} should include evidence",
            hotspot.name
        );
    }
    assert!(
        audit
            .non_goals
            .iter()
            .any(|goal| goal.contains("write DTOs") && goal.contains("UUID7")),
        "JSON mapping audit should exclude write DTO and UUID7 work"
    );
}

fn load_fastapi_brapi_snapshot_routes() -> BTreeSet<String> {
    load_fastapi_brapi_snapshot()
        .rows
        .into_iter()
        .map(|row| row.path)
        .collect()
}

fn load_fastapi_brapi_snapshot() -> FastApiRouteSnapshot {
    let name = "fastapi-brapi-get-routes.md";
    let raw = fs::read_to_string(contract_dir().join(name))
        .unwrap_or_else(|error| panic!("{name} route snapshot should be readable: {error}"));

    let declared_total = raw
        .lines()
        .find_map(|line| {
            line.strip_prefix("Total FastAPI BrAPI GET routes: ")
                .and_then(|count| count.parse::<usize>().ok())
        })
        .expect("FastAPI BrAPI GET snapshot should declare its total route count");
    let rows = raw.lines().filter_map(parse_fastapi_snapshot_row).collect();

    FastApiRouteSnapshot {
        declared_total,
        rows,
    }
}

fn parse_fastapi_snapshot_row(line: &str) -> Option<FastApiRouteRow> {
    let cells: Vec<_> = line
        .trim()
        .trim_matches('|')
        .split('|')
        .map(str::trim)
        .collect();

    if cells.len() != 3 || !cells[0].starts_with('`') {
        return None;
    }

    let path = cells[0].strip_prefix('`')?.strip_suffix('`')?.to_string();
    let source = cells[1].strip_prefix('`')?.strip_suffix('`')?.to_string();
    let line = cells[2].parse::<usize>().ok()?;

    Some(FastApiRouteRow { path, source, line })
}

fn query_parameter_names(path: &str) -> BTreeSet<&str> {
    let query = path
        .split_once('?')
        .map(|(_, query)| query)
        .expect("query example path should include a query string");

    query
        .split('&')
        .map(|pair| {
            pair.split_once('=')
                .map(|(name, _)| name)
                .expect("query parameter should include a value")
        })
        .collect()
}

fn normalized_fastapi_path(rust_path: &str) -> String {
    let without_prefix = rust_path.strip_prefix("/brapi/v2").unwrap_or(rust_path);
    let mut normalized = String::new();
    let mut rest = without_prefix;

    while let Some(open) = rest.find('{') {
        normalized.push_str(&rest[..open]);
        let after_open = &rest[open + 1..];
        let close = after_open
            .find('}')
            .expect("route parameter should close with }");
        let parameter = &after_open[..close];
        normalized.push('{');
        normalized.push_str(&normalized_parameter_name(parameter));
        normalized.push('}');
        rest = &after_open[close + 1..];
    }

    normalized.push_str(rest);
    normalized
}

fn normalized_parameter_name(parameter: &str) -> String {
    if parameter == "seedlot_db_id" {
        return "seedLotDbId".to_string();
    }

    let mut parts = parameter.split('_');
    let mut normalized = parts.next().unwrap_or_default().to_string();
    for part in parts {
        let mut chars = part.chars();
        if let Some(first) = chars.next() {
            normalized.push(first.to_ascii_uppercase());
            normalized.extend(chars);
        }
    }
    normalized
}

fn extract_app_routes(source: &str) -> BTreeSet<(String, String)> {
    let app_source = app_router_source(source);
    let mut routes = BTreeSet::new();
    let mut rest = app_source;

    while let Some(route_index) = rest.find(".route(") {
        rest = &rest[route_index + ".route(".len()..];
        let trimmed = rest.trim_start();
        let after_open_quote = trimmed
            .strip_prefix('"')
            .expect("app router route path should be the first route argument");
        let path_end = after_open_quote
            .find('"')
            .expect("app router route path should close its string literal");
        let path = &after_open_quote[..path_end];
        let after_path = &after_open_quote[path_end + 1..];
        let call_end = after_path.find(".route(").unwrap_or(after_path.len());
        let route_call = &after_path[..call_end];
        let mut methods = Vec::new();
        for (needle, method) in [
            ("get(", "GET"),
            ("post(", "POST"),
            ("put(", "PUT"),
            ("patch(", "PATCH"),
            ("delete(", "DELETE"),
        ] {
            if route_call.contains(needle) {
                methods.push(method);
            }
        }

        if methods.is_empty() {
            panic!("{path} should register a recognized HTTP method");
        }

        if path == "/api/v2/seed-inventory/adjustments" {
            assert!(
                methods.contains(&"GET"),
                "{path} should register the guarded Rust history read route"
            );
            assert!(
                methods.contains(&"POST"),
                "{path} should register the guarded Rust write route"
            );
            for forbidden in ["PUT", "PATCH", "DELETE"] {
                assert!(
                    !methods.contains(&forbidden),
                    "{path} should not register write method {forbidden}"
                );
            }
        } else {
            assert_eq!(
                methods,
                vec!["GET"],
                "{path} should use GET in the Rust read beta"
            );
            for forbidden in ["post(", "put(", "patch(", "delete("] {
                assert!(
                    !route_call.contains(forbidden),
                    "{path} should not register write method {forbidden}"
                );
            }
        }
        for method in methods {
            assert!(
                routes.insert((method.to_string(), path.to_string())),
                "app router should not duplicate {method} {path}"
            );
        }

        rest = after_path;
    }

    routes
}

fn app_router_source(source: &str) -> &str {
    let app_start = source
        .find("pub fn app")
        .expect("app router function should exist");
    let app_tail = &source[app_start..];
    let app_end = app_tail
        .find("\npub async fn serve")
        .expect("serve function should follow app router function");
    &app_tail[..app_end]
}

fn json_path<'a>(value: &'a Value, path: &str) -> Option<&'a Value> {
    let mut current = value;
    for segment in path.split('.') {
        current = match current {
            Value::Object(map) => map.get(segment)?,
            Value::Array(items) => items.get(segment.parse::<usize>().ok()?)?,
            _ => return None,
        };
    }
    Some(current)
}
