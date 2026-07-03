use std::collections::BTreeMap;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum HealthStatus {
    Healthy,
    Degraded,
    Critical,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DependencyHealth {
    pub status: HealthStatus,
    pub critical: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub detail: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

impl DependencyHealth {
    pub fn healthy(critical: bool) -> Self {
        Self {
            status: HealthStatus::Healthy,
            critical,
            detail: None,
            error: None,
        }
    }

    pub fn degraded(critical: bool, detail: impl Into<String>) -> Self {
        Self {
            status: HealthStatus::Degraded,
            critical,
            detail: Some(detail.into()),
            error: None,
        }
    }

    pub fn critical(error: impl Into<String>) -> Self {
        Self {
            status: HealthStatus::Critical,
            critical: true,
            detail: None,
            error: Some(error.into()),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HealthReport {
    pub status: HealthStatus,
    pub timestamp: DateTime<Utc>,
    pub dependencies: BTreeMap<String, DependencyHealth>,
}

impl HealthReport {
    pub fn from_dependencies(dependencies: BTreeMap<String, DependencyHealth>) -> Self {
        let has_critical = dependencies
            .values()
            .any(|dependency| dependency.status == HealthStatus::Critical);
        let has_degraded = dependencies
            .values()
            .any(|dependency| dependency.status == HealthStatus::Degraded);

        let status = if has_critical {
            HealthStatus::Critical
        } else if has_degraded {
            HealthStatus::Degraded
        } else {
            HealthStatus::Healthy
        };

        Self {
            status,
            timestamp: Utc::now(),
            dependencies,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn health_rolls_up_degraded_dependencies() {
        let dependencies = BTreeMap::from([
            ("runtime".to_string(), DependencyHealth::healthy(true)),
            (
                "metrics_file".to_string(),
                DependencyHealth::degraded(false, "using defaults"),
            ),
        ]);

        let report = HealthReport::from_dependencies(dependencies);

        assert_eq!(report.status, HealthStatus::Degraded);
    }
}
