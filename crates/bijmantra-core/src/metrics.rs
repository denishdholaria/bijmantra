use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};
use thiserror::Error;

use crate::product::{API_NAME, APP_VERSION, BRAPI_VERSION, product_modules};

#[derive(Debug, Error)]
pub enum MetricsError {
    #[error("failed to read metrics from {path}: {source}")]
    Read {
        path: String,
        #[source]
        source: std::io::Error,
    },
    #[error("failed to parse metrics from {path}: {source}")]
    Parse {
        path: String,
        #[source]
        source: serde_json::Error,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ApiMetrics {
    #[serde(default = "default_total_endpoints")]
    pub total_endpoints: u32,
    #[serde(default = "default_brapi_endpoints")]
    pub brapi_endpoints: u32,
    #[serde(default = "default_brapi_published_endpoints")]
    pub brapi_published_endpoints: u32,
    #[serde(default)]
    pub brapi_exposed_endpoints: Option<u32>,
    #[serde(default = "default_brapi_coverage")]
    pub brapi_coverage: u32,
}

impl Default for ApiMetrics {
    fn default() -> Self {
        Self {
            total_endpoints: default_total_endpoints(),
            brapi_endpoints: default_brapi_endpoints(),
            brapi_published_endpoints: default_brapi_published_endpoints(),
            brapi_exposed_endpoints: Some(default_brapi_published_endpoints()),
            brapi_coverage: default_brapi_coverage(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ApiStats {
    pub name: &'static str,
    pub version: &'static str,
    pub brapi_version: &'static str,
    pub total_endpoints: u32,
    pub brapi_endpoints: u32,
    pub brapi_published_endpoints: u32,
    pub brapi_exposed_endpoints: u32,
    pub brapi_coverage: u32,
    pub modules: Vec<&'static str>,
    pub status: &'static str,
}

#[derive(Debug, Deserialize)]
struct MetricsFile {
    #[serde(default)]
    api: ApiMetrics,
}

pub fn load_api_metrics(path: impl AsRef<Path>) -> Result<ApiMetrics, MetricsError> {
    let path = path.as_ref();
    let raw = fs::read_to_string(path).map_err(|source| MetricsError::Read {
        path: path.display().to_string(),
        source,
    })?;
    let parsed: MetricsFile = serde_json::from_str(&raw).map_err(|source| MetricsError::Parse {
        path: path.display().to_string(),
        source,
    })?;
    Ok(parsed.api)
}

pub fn api_stats(metrics: ApiMetrics) -> ApiStats {
    let exposed = metrics
        .brapi_exposed_endpoints
        .unwrap_or(metrics.brapi_endpoints)
        .max(metrics.brapi_published_endpoints);

    ApiStats {
        name: API_NAME,
        version: APP_VERSION,
        brapi_version: BRAPI_VERSION,
        total_endpoints: metrics.total_endpoints,
        brapi_endpoints: exposed,
        brapi_published_endpoints: metrics.brapi_published_endpoints,
        brapi_exposed_endpoints: exposed,
        brapi_coverage: metrics.brapi_coverage,
        modules: product_modules()
            .into_iter()
            .map(|module| module.name)
            .collect(),
        status: "operational",
    }
}

const fn default_total_endpoints() -> u32 {
    1728
}

const fn default_brapi_endpoints() -> u32 {
    201
}

const fn default_brapi_published_endpoints() -> u32 {
    201
}

const fn default_brapi_coverage() -> u32 {
    100
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn api_stats_preserves_fastapi_wire_shape() {
        let stats = api_stats(ApiMetrics::default());

        assert_eq!(stats.name, "Bijmantra API");
        assert_eq!(stats.brapi_version, "2.1");
        assert_eq!(stats.brapi_published_endpoints, 201);
        assert!(stats.modules.contains(&"Compute Engine"));
    }

    #[test]
    fn exposed_endpoints_fall_back_to_brapi_endpoints() {
        let stats = api_stats(ApiMetrics {
            brapi_endpoints: 212,
            brapi_published_endpoints: 201,
            brapi_exposed_endpoints: None,
            ..ApiMetrics::default()
        });

        assert_eq!(stats.brapi_exposed_endpoints, 212);
        assert_eq!(stats.brapi_endpoints, 212);
    }
}
