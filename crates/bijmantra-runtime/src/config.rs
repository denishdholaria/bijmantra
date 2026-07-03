use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Config {
    pub podman: Option<String>,
    #[serde(default)]
    pub services: BTreeMap<String, ServiceOverride>,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ServiceOverride {
    pub port: Option<u16>,
    pub cmd: Option<Vec<String>>,
}

pub fn load_config(workspace: &Path) -> anyhow::Result<Config> {
    let mut config = Config::default();
    apply_dot_env(&mut config, &workspace.join(".env"))?;
    apply_yaml(&mut config, &workspace.join(".bij.yaml"))?;
    Ok(config)
}

fn apply_dot_env(config: &mut Config, path: &Path) -> anyhow::Result<()> {
    let Ok(raw) = fs::read_to_string(path) else {
        return Ok(());
    };

    for (service, keys) in SERVICE_PORT_ENV {
        for key in *keys {
            let Some(value) = dot_env_value(&raw, key) else {
                continue;
            };
            let port = value
                .parse::<u16>()
                .map_err(|error| anyhow::anyhow!("load .env: invalid {key}={value:?}: {error}"))?;
            config
                .services
                .entry((*service).to_string())
                .or_default()
                .port = Some(port);
            break;
        }
    }

    Ok(())
}

fn apply_yaml(config: &mut Config, path: &Path) -> anyhow::Result<()> {
    let Ok(raw) = fs::read_to_string(path) else {
        return Ok(());
    };
    let file_config: Config =
        serde_yaml::from_str(&raw).map_err(|error| anyhow::anyhow!("load .bij.yaml: {error}"))?;

    if file_config.podman.is_some() {
        config.podman = file_config.podman;
    }
    for (name, override_config) in file_config.services {
        let current = config.services.entry(name).or_default();
        if override_config.port.is_some() {
            current.port = override_config.port;
        }
        if override_config.cmd.is_some() {
            current.cmd = override_config.cmd;
        }
    }

    Ok(())
}

fn dot_env_value(raw: &str, key: &str) -> Option<String> {
    raw.lines()
        .filter_map(|line| {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                return None;
            }
            let (line_key, value) = line.split_once('=')?;
            if line_key.trim() != key {
                return None;
            }
            Some(
                value
                    .trim()
                    .trim_matches('"')
                    .trim_matches('\'')
                    .to_string(),
            )
        })
        .next()
}

const SERVICE_PORT_ENV: &[(&str, &[&str])] = &[
    ("postgres", &["POSTGRES_PORT"]),
    ("redis", &["REDIS_PORT"]),
    ("minio", &["MINIO_PORT"]),
    ("meilisearch", &["MEILISEARCH_PORT"]),
    (
        "beingbijmantra",
        &["BEINGBIJMANTRA_PORT", "BEINGBIJMANTRA_SURREAL_PORT"],
    ),
    ("backend", &["BACKEND_PORT"]),
    ("frontend", &["FRONTEND_PORT"]),
    (
        "chloe-gateway",
        &["CHLOE_GATEWAY_PORT", "OPENCLAW_GATEWAY_PORT"],
    ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_dot_env_values_without_external_dependency() {
        let raw = r#"
            # comment
            BACKEND_PORT=18000
            FRONTEND_PORT="5657"
        "#;

        assert_eq!(
            dot_env_value(raw, "BACKEND_PORT"),
            Some("18000".to_string())
        );
        assert_eq!(
            dot_env_value(raw, "FRONTEND_PORT"),
            Some("5657".to_string())
        );
        assert_eq!(dot_env_value(raw, "MISSING"), None);
    }
}
