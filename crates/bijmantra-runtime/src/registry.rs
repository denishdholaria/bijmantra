use std::path::{Path, PathBuf};
use std::str::FromStr;

use serde::{Deserialize, Serialize};

use crate::config::Config;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ServiceType {
    Container,
    Process,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ServiceGroup {
    Core,
    Infra,
    Autonomy,
}

impl ServiceGroup {
    pub fn includes(self, service: &Service) -> bool {
        service.group <= self
    }
}

impl FromStr for ServiceGroup {
    type Err = anyhow::Error;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "core" => Ok(Self::Core),
            "infra" => Ok(Self::Infra),
            "autonomy" => Ok(Self::Autonomy),
            _ => {
                anyhow::bail!("unknown service group {value:?}; expected core, infra, or autonomy")
            }
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ServiceState {
    Waiting,
    Ready,
    Degraded,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "kebab-case")]
pub enum Probe {
    Tcp {
        host: String,
        port: u16,
    },
    Http {
        url: String,
    },
    Exec {
        runtime: PathBuf,
        container: String,
        cmd: Vec<String>,
    },
    ContainerRunning {
        runtime: PathBuf,
        container: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Service {
    pub name: String,
    pub label: String,
    pub service_type: ServiceType,
    pub group: ServiceGroup,
    pub experimental: bool,
    pub port: Option<u16>,
    pub compose_service: Option<String>,
    pub container_name: Option<String>,
    pub compose_profiles: Vec<String>,
    pub cmd: Vec<String>,
    pub work_dir: Option<PathBuf>,
    pub probe: Option<Probe>,
    pub state: ServiceState,
}

impl Service {
    fn container(
        name: &str,
        label: &str,
        group: ServiceGroup,
        port: Option<u16>,
        compose_service: &str,
        container_name: &str,
        probe: Probe,
    ) -> Self {
        Self {
            name: name.to_string(),
            label: label.to_string(),
            service_type: ServiceType::Container,
            group,
            experimental: false,
            port,
            compose_service: Some(compose_service.to_string()),
            container_name: Some(container_name.to_string()),
            compose_profiles: Vec::new(),
            cmd: Vec::new(),
            work_dir: None,
            probe: Some(probe),
            state: ServiceState::Waiting,
        }
    }

    fn process(
        name: &str,
        label: &str,
        group: ServiceGroup,
        port: u16,
        cmd: Vec<String>,
        work_dir: PathBuf,
        probe: Probe,
    ) -> Self {
        Self {
            name: name.to_string(),
            label: label.to_string(),
            service_type: ServiceType::Process,
            group,
            experimental: false,
            port: Some(port),
            compose_service: None,
            container_name: None,
            compose_profiles: Vec::new(),
            cmd,
            work_dir: Some(work_dir),
            probe: Some(probe),
            state: ServiceState::Waiting,
        }
    }
}

pub fn default_registry(workspace: &Path, podman: &Path) -> Vec<Service> {
    let mut services = vec![
        Service::container(
            "postgres",
            "PostgreSQL",
            ServiceGroup::Core,
            Some(5432),
            "postgres",
            "bijmantra-postgres",
            Probe::Exec {
                runtime: podman.to_path_buf(),
                container: "bijmantra-postgres".to_string(),
                cmd: vec![
                    "pg_isready".to_string(),
                    "-U".to_string(),
                    "bijmantra_user".to_string(),
                    "-d".to_string(),
                    "bijmantra_db".to_string(),
                ],
            },
        ),
        Service::container(
            "redis",
            "Redis",
            ServiceGroup::Infra,
            Some(6379),
            "redis",
            "bijmantra-redis",
            Probe::Exec {
                runtime: podman.to_path_buf(),
                container: "bijmantra-redis".to_string(),
                cmd: vec!["redis-cli".to_string(), "ping".to_string()],
            },
        ),
        Service::container(
            "minio",
            "MinIO",
            ServiceGroup::Infra,
            Some(9000),
            "minio",
            "bijmantra-minio",
            Probe::Http {
                url: "http://localhost:9000/minio/health/live".to_string(),
            },
        ),
        Service::container(
            "meilisearch",
            "Meilisearch",
            ServiceGroup::Infra,
            Some(7700),
            "meilisearch",
            "bijmantra-meilisearch",
            Probe::Http {
                url: "http://localhost:7700/health".to_string(),
            },
        ),
        Service::container(
            "beingbijmantra",
            "BeingBijmantra",
            ServiceGroup::Autonomy,
            Some(8083),
            "beingbijmantra-surrealdb",
            "beingbijmantra-surrealdb",
            Probe::Tcp {
                host: "localhost".to_string(),
                port: 8083,
            },
        ),
        Service::process(
            "backend",
            "Backend API",
            ServiceGroup::Core,
            8000,
            backend_command(8000),
            workspace.join("backend"),
            Probe::Http {
                url: "http://localhost:8000/health".to_string(),
            },
        ),
        Service::process(
            "frontend",
            "Frontend",
            ServiceGroup::Core,
            5656,
            vec!["bun".to_string(), "run".to_string(), "dev".to_string()],
            workspace.join("frontend"),
            Probe::Http {
                url: "http://localhost:5656/".to_string(),
            },
        ),
        Service::container(
            "chloe-gateway",
            "Chloe Gateway",
            ServiceGroup::Autonomy,
            Some(18790),
            "chloe-gateway",
            "bijmantra-chloe-gateway",
            Probe::Http {
                url: "http://127.0.0.1:18790/healthz".to_string(),
            },
        ),
        Service::container(
            "chloe-cli",
            "Chloe CLI",
            ServiceGroup::Autonomy,
            None,
            "chloe-cli",
            "bijmantra-chloe-cli",
            Probe::ContainerRunning {
                runtime: podman.to_path_buf(),
                container: "bijmantra-chloe-cli".to_string(),
            },
        ),
        Service::container(
            "chloe-sandbox",
            "Chloe Sandbox",
            ServiceGroup::Autonomy,
            None,
            "chloe-sandbox",
            "bijmantra-chloe-sandbox",
            Probe::ContainerRunning {
                runtime: podman.to_path_buf(),
                container: "bijmantra-chloe-sandbox".to_string(),
            },
        ),
    ];

    for service in &mut services {
        match service.name.as_str() {
            "redis" | "minio" | "meilisearch" => {
                service.compose_profiles = vec!["infra".to_string()]
            }
            "beingbijmantra" => {
                service.experimental = true;
                service.compose_profiles = vec!["beingbijmantra".to_string()];
            }
            "chloe-gateway" | "chloe-cli" | "chloe-sandbox" => {
                service.experimental = true;
                service.compose_profiles = vec!["chloe".to_string()];
            }
            _ => {}
        }
    }

    services
}

pub fn apply_config(services: &mut [Service], config: &Config) {
    for service in services {
        let Some(override_config) = config.services.get(&service.name) else {
            continue;
        };

        let had_cmd_override = override_config.cmd.is_some();
        if let Some(port) = override_config.port {
            service.port = Some(port);
        }
        if let Some(cmd) = &override_config.cmd {
            service.cmd = cmd.clone();
        }
        if service.name == "backend" && service.port.is_some() && !had_cmd_override {
            service.cmd = backend_command(service.port.unwrap_or(8000));
        }
        refresh_probe(service);
    }
}

pub fn services_for_group(services: &[Service], group: ServiceGroup) -> Vec<Service> {
    services
        .iter()
        .filter(|service| group.includes(service))
        .cloned()
        .collect()
}

fn refresh_probe(service: &mut Service) {
    let Some(port) = service.port else {
        return;
    };

    service.probe = match service.name.as_str() {
        "minio" => Some(Probe::Http {
            url: format!("http://localhost:{port}/minio/health/live"),
        }),
        "meilisearch" => Some(Probe::Http {
            url: format!("http://localhost:{port}/health"),
        }),
        "beingbijmantra" => Some(Probe::Tcp {
            host: "localhost".to_string(),
            port,
        }),
        "backend" => Some(Probe::Http {
            url: format!("http://localhost:{port}/health"),
        }),
        "frontend" => Some(Probe::Http {
            url: format!("http://localhost:{port}/"),
        }),
        "chloe-gateway" => Some(Probe::Http {
            url: format!("http://127.0.0.1:{port}/healthz"),
        }),
        _ => service.probe.clone(),
    };
}

fn backend_command(port: u16) -> Vec<String> {
    vec![
        "uv".to_string(),
        "run".to_string(),
        "uvicorn".to_string(),
        "app.main:app".to_string(),
        "--reload".to_string(),
        "--host".to_string(),
        "0.0.0.0".to_string(),
        "--port".to_string(),
        port.to_string(),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn infra_group_includes_core_and_infra_services() {
        let services = default_registry(Path::new("."), Path::new("podman"));
        let selected = services_for_group(&services, ServiceGroup::Infra);
        let names: Vec<_> = selected
            .iter()
            .map(|service| service.name.as_str())
            .collect();

        assert!(names.contains(&"postgres"));
        assert!(names.contains(&"backend"));
        assert!(names.contains(&"frontend"));
        assert!(names.contains(&"redis"));
        assert!(!names.contains(&"chloe-gateway"));
    }

    #[test]
    fn backend_port_override_refreshes_command_and_probe() {
        let mut services = default_registry(Path::new("."), Path::new("podman"));
        let mut config = Config::default();
        config.services.insert(
            "backend".to_string(),
            crate::config::ServiceOverride {
                port: Some(18000),
                cmd: None,
            },
        );

        apply_config(&mut services, &config);

        let backend = services
            .iter()
            .find(|service| service.name == "backend")
            .unwrap();
        assert!(backend.cmd.contains(&"18000".to_string()));
        assert_eq!(
            backend.probe,
            Some(Probe::Http {
                url: "http://localhost:18000/health".to_string()
            })
        );
    }
}
