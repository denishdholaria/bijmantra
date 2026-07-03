use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use bijmantra_server::{AppState, DataStore, app};
use serde_json::{Value, json};
use tower::ServiceExt;

fn fixture_root(name: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock should be after unix epoch")
        .as_nanos();
    let path = std::env::temp_dir().join(format!(
        "bijmantra-server-api-contract-{name}-{}-{nonce}",
        std::process::id()
    ));
    fs::create_dir_all(&path).expect("fixture directory should be created");
    path
}

fn write_metrics(root: &Path, metrics: Value) {
    fs::write(
        root.join("metrics.json"),
        serde_json::to_vec_pretty(&metrics).expect("metrics fixture should serialize"),
    )
    .expect("metrics fixture should be written");
}

async fn get_json(root: &Path, uri: &str) -> Value {
    get_json_with_state(
        AppState::new(root).with_data_store(DataStore::unavailable()),
        uri,
    )
    .await
}

async fn get_json_with_state(state: AppState, uri: &str) -> Value {
    let response = app(state)
        .oneshot(
            Request::builder()
                .uri(uri)
                .body(Body::empty())
                .expect("request should build"),
        )
        .await
        .expect("router should respond");

    assert_eq!(response.status(), StatusCode::OK);

    let body = to_bytes(response.into_body(), 1024 * 1024)
        .await
        .expect("response body should be readable");
    serde_json::from_slice(&body).expect("response should be json")
}

#[tokio::test]
async fn root_endpoint_preserves_fastapi_public_shape() {
    let root = fixture_root("root");

    let body = get_json(&root, "/").await;

    assert_eq!(body["brapi_version"], "2.1");
    assert_eq!(body["docs"], "/docs");
    assert!(
        body["version"]
            .as_str()
            .is_some_and(|version| !version.is_empty())
    );
    assert!(body["message"].as_str().is_some_and(|message| {
        message.contains("Welcome") && message.contains("Bij") && message.contains("API")
    }));
}

#[tokio::test]
async fn health_endpoint_reports_dependency_aware_shape() {
    let root = fixture_root("health");
    write_metrics(
        &root,
        json!({
            "api": {
                "totalEndpoints": 1906,
                "brapiEndpoints": 249,
                "brapiPublishedEndpoints": 201,
                "brapiExposedEndpoints": 249,
                "brapiCoverage": 100
            }
        }),
    );

    let body = get_json(&root, "/health").await;

    assert_eq!(body["status"], "healthy");
    assert!(
        body["timestamp"]
            .as_str()
            .is_some_and(|timestamp| !timestamp.is_empty())
    );

    let dependencies = body["dependencies"]
        .as_object()
        .expect("health dependencies should be an object");
    assert_eq!(dependencies["rust_runtime"]["status"], "healthy");
    assert_eq!(dependencies["rust_runtime"]["critical"], true);
    assert_eq!(dependencies["metrics_file"]["status"], "healthy");
    assert_eq!(dependencies["metrics_file"]["critical"], false);
    assert!(
        !dependencies.contains_key("postgres_read_repository"),
        "unconfigured DB should not degrade the public health contract"
    );
}

#[tokio::test]
async fn missing_metrics_file_keeps_health_useful_and_stats_defaulted() {
    let root = fixture_root("missing-metrics");

    let health = get_json(&root, "/health").await;

    assert_eq!(health["status"], "degraded");
    assert!(
        health["timestamp"]
            .as_str()
            .is_some_and(|timestamp| !timestamp.is_empty())
    );
    let dependencies = health["dependencies"]
        .as_object()
        .expect("health dependencies should be an object");
    assert_eq!(dependencies["rust_runtime"]["status"], "healthy");
    assert_eq!(dependencies["rust_runtime"]["critical"], true);
    assert_eq!(dependencies["metrics_file"]["status"], "degraded");
    assert_eq!(dependencies["metrics_file"]["critical"], false);
    assert!(
        dependencies["metrics_file"]["detail"]
            .as_str()
            .is_some_and(|detail| detail.contains("metrics.json")),
        "missing metrics detail should identify the missing file"
    );

    let stats = get_json(&root, "/api/stats").await;

    assert_eq!(stats["status"], "operational");
    assert_eq!(stats["name"], "Bijmantra API");
    assert_eq!(stats["brapi_version"], "2.1");
    assert_eq!(stats["total_endpoints"], 1728);
    assert_eq!(stats["brapi_endpoints"], 201);
    assert_eq!(stats["brapi_published_endpoints"], 201);
    assert_eq!(stats["brapi_exposed_endpoints"], 201);
    assert_eq!(stats["brapi_coverage"], 100);
    assert!(
        stats["modules"]
            .as_array()
            .is_some_and(|modules| modules.iter().any(|module| module == "BrAPI Core")),
        "default stats should still include product module names"
    );
}

#[tokio::test]
async fn configured_db_health_dependency_reports_degraded_when_unreachable() {
    let root = fixture_root("db-health-unreachable");
    write_metrics(
        &root,
        json!({
            "api": {
                "totalEndpoints": 1906,
                "brapiEndpoints": 249,
                "brapiPublishedEndpoints": 201,
                "brapiExposedEndpoints": 249,
                "brapiCoverage": 100
            }
        }),
    );

    let body = get_json_with_state(
        AppState::new(&root).with_data_store(DataStore::from_database_url(
            "postgres://bijmantra_user:local_test_secret@127.0.0.1:1/bijmantra",
        )),
        "/health",
    )
    .await;

    assert_eq!(body["status"], "degraded");
    let dependencies = body["dependencies"]
        .as_object()
        .expect("health dependencies should be an object");
    assert_eq!(dependencies["rust_runtime"]["status"], "healthy");
    assert_eq!(dependencies["metrics_file"]["status"], "healthy");
    assert_eq!(
        dependencies["postgres_read_repository"]["status"],
        "degraded"
    );
    assert_eq!(dependencies["postgres_read_repository"]["critical"], false);
    assert!(
        dependencies["postgres_read_repository"]["detail"]
            .as_str()
            .is_some_and(|detail| detail.contains("configured Postgres read repository")),
        "configured DB dependency should explain the degraded read repository health"
    );
}

#[tokio::test]
async fn stats_endpoint_reads_metrics_json_and_preserves_fastapi_field_names() {
    let root = fixture_root("stats");
    write_metrics(
        &root,
        json!({
            "api": {
                "totalEndpoints": 1906,
                "brapiEndpoints": 249,
                "brapiPublishedEndpoints": 201,
                "brapiExposedEndpoints": 249,
                "brapiCoverage": 100,
                "customEndpoints": 1657
            }
        }),
    );

    let body = get_json(&root, "/api/stats").await;

    assert!(
        body["name"]
            .as_str()
            .is_some_and(|name| name.eq_ignore_ascii_case("Bijmantra API"))
    );
    assert_eq!(body["brapi_version"], "2.1");
    assert_eq!(body["total_endpoints"], 1906);
    assert_eq!(body["brapi_endpoints"], 249);
    assert_eq!(body["brapi_published_endpoints"], 201);
    assert_eq!(body["brapi_exposed_endpoints"], 249);
    assert_eq!(body["brapi_coverage"], 100);
    assert_eq!(body["status"], "operational");

    let modules = body["modules"]
        .as_array()
        .expect("stats modules should be an array");
    assert!(modules.iter().any(|module| module == "BrAPI Core"));
    assert!(modules.iter().any(|module| module == "Compute Engine"));
    assert!(
        modules
            .iter()
            .any(|module| module == "CHAITANYA Orchestrator")
    );
}

#[tokio::test]
async fn manifest_endpoint_exposes_product_runtime_contract() {
    let root = fixture_root("manifest");

    let body = get_json(&root, "/api/manifest").await;

    assert_eq!(body["name"], "BijMantra");
    assert_eq!(body["api_name"], "Bijmantra API");
    assert_eq!(body["brapi_version"], "2.1");

    let profiles = body["profiles"]
        .as_array()
        .expect("manifest profiles should be an array");
    assert!(profiles.iter().any(|profile| profile == "development"));
    assert!(profiles.iter().any(|profile| profile == "production"));
    assert!(profiles.iter().any(|profile| profile == "offline-first"));
    assert!(profiles.iter().any(|profile| profile == "institutional"));

    let modules = body["modules"]
        .as_array()
        .expect("manifest modules should be an array");
    assert!(modules.iter().any(|module| {
        module["id"] == "brapi-core"
            && module["name"] == "BrAPI Core"
            && module["domain"] == "interoperability"
    }));
    assert!(modules.iter().any(|module| {
        module["id"] == "trial-design"
            && module["name"] == "Trial Design"
            && module["domain"] == "breeding"
    }));
}

#[tokio::test]
async fn brapi_serverinfo_preserves_brapi_v2_acronym_fields() {
    let root = fixture_root("serverinfo");

    let body = get_json(&root, "/brapi/v2/serverinfo").await;

    assert_eq!(body["metadata"]["datafiles"], json!([]));
    assert_eq!(body["metadata"]["pagination"]["currentPage"], 0);
    assert_eq!(body["metadata"]["pagination"]["pageSize"], 1);
    assert_eq!(body["metadata"]["pagination"]["totalCount"], 1);
    assert_eq!(body["metadata"]["pagination"]["totalPages"], 1);
    assert_eq!(body["metadata"]["status"][0]["message"], "Success");
    assert_eq!(body["metadata"]["status"][0]["messageType"], "INFO");

    let result = body["result"]
        .as_object()
        .expect("serverinfo result should be an object");
    assert!(result.contains_key("calls"));
    assert!(result.contains_key("contactEmail"));
    assert!(result.contains_key("documentationURL"));
    assert!(result.contains_key("organizationURL"));
    assert!(result.contains_key("organizationName"));
    assert!(result.contains_key("serverDescription"));
    assert!(result.contains_key("serverName"));
    assert!(!result.contains_key("documentationUrl"));
    assert!(!result.contains_key("organizationUrl"));

    let calls = result["calls"]
        .as_array()
        .expect("serverinfo calls should be an array");
    assert!(
        calls.iter().any(|call| {
            call["service"] == "serverinfo"
                && call["methods"] == json!(["GET"])
                && call["contentTypes"] == json!(["application/json"])
                && call["dataTypes"] == json!([])
                && call["versions"] == json!(["2.1"])
        }),
        "serverinfo should expose FastAPI-compatible BrAPI call objects"
    );
    assert!(calls.iter().any(|call| call["service"] == "calls"));
    assert!(
        calls
            .iter()
            .any(|call| call["service"] == "seedlots/{seedLotDbId}")
    );
}

#[tokio::test]
async fn brapi_calls_endpoint_exposes_current_rust_route_registry() {
    let root = fixture_root("calls");

    let body = get_json(&root, "/brapi/v2/calls").await;

    let data = body["result"]["data"]
        .as_array()
        .expect("calls result data should be an array");
    assert!(!data.is_empty());
    assert_eq!(body["metadata"]["pagination"]["currentPage"], 0);
    assert_eq!(
        body["metadata"]["pagination"]["pageSize"],
        data.len() as u64
    );
    assert_eq!(
        body["metadata"]["pagination"]["totalCount"],
        data.len() as u64
    );
    assert_eq!(body["metadata"]["pagination"]["totalPages"], 1);
    assert!(data.iter().any(|call| {
        call["service"] == "calls"
            && call["methods"] == json!(["GET"])
            && call["contentTypes"] == json!(["application/json"])
            && call["dataTypes"] == json!([])
            && call["versions"] == json!(["2.1"])
    }));
    assert!(
        data.iter()
            .any(|call| call["service"] == "programs/{programDbId}")
    );
    assert!(data.iter().any(|call| call["service"] == "commoncropnames"));
    assert!(data.iter().any(|call| call["service"] == "ontologies"));
    assert!(
        data.iter()
            .any(|call| call["service"] == "ontologies/{ontologyDbId}")
    );
    assert!(data.iter().any(|call| {
        call["service"] == "seedlots/{seedLotDbId}/transactions"
            && call["methods"] == json!(["GET"])
    }));
}

#[tokio::test]
async fn brapi_commoncropnames_preserves_fastapi_pagination_shape() {
    let root = fixture_root("commoncropnames");

    let body = get_json(&root, "/brapi/v2/commoncropnames").await;

    assert_eq!(body["metadata"]["pagination"]["currentPage"], 0);
    assert_eq!(body["metadata"]["pagination"]["pageSize"], 1000);
    assert_eq!(body["metadata"]["pagination"]["totalCount"], 50);
    assert_eq!(body["metadata"]["pagination"]["totalPages"], 1);
    let data = body["result"]["data"]
        .as_array()
        .expect("common crop names result data should be an array");
    assert_eq!(data.first(), Some(&json!("Rice")));
    assert_eq!(data.last(), Some(&json!("Jute")));

    let body = get_json(&root, "/brapi/v2/commoncropnames?page=1&pageSize=2").await;

    assert_eq!(body["metadata"]["pagination"]["currentPage"], 1);
    assert_eq!(body["metadata"]["pagination"]["pageSize"], 2);
    assert_eq!(body["metadata"]["pagination"]["totalCount"], 50);
    assert_eq!(body["metadata"]["pagination"]["totalPages"], 25);
    assert_eq!(body["result"]["data"], json!(["Maize", "Sorghum"]));
}
