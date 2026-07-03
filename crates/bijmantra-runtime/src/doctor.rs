use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::net::TcpListener;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde::{Deserialize, Serialize};

use crate::config::load_config;
use crate::registry::{Service, apply_config, default_registry};
use crate::workspace::{detect_podman, resolve_workspace, verify_compose};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RuntimeCheck {
    pub name: String,
    pub ok: bool,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DoctorReport {
    pub workspace: Option<PathBuf>,
    pub podman: Option<PathBuf>,
    pub services: usize,
    pub checks: Vec<RuntimeCheck>,
}

impl DoctorReport {
    pub fn healthy(&self) -> bool {
        self.checks.iter().all(|check| check.ok)
    }
}

pub fn run_doctor(workspace_override: Option<PathBuf>) -> DoctorReport {
    let mut report = DoctorReport {
        workspace: None,
        podman: None,
        services: 0,
        checks: Vec::new(),
    };

    let workspace = match resolve_workspace(workspace_override) {
        Ok(workspace) => {
            report.checks.push(RuntimeCheck {
                name: "workspace".to_string(),
                ok: true,
                detail: workspace.display().to_string(),
            });
            report.workspace = Some(workspace.clone());
            workspace
        }
        Err(error) => {
            report.checks.push(RuntimeCheck {
                name: "workspace".to_string(),
                ok: false,
                detail: error.to_string(),
            });
            return report;
        }
    };

    let config = match load_config(&workspace) {
        Ok(config) => {
            report.checks.push(RuntimeCheck {
                name: "config".to_string(),
                ok: true,
                detail: ".env/.bij.yaml loaded".to_string(),
            });
            config
        }
        Err(error) => {
            report.checks.push(RuntimeCheck {
                name: "config".to_string(),
                ok: false,
                detail: error.to_string(),
            });
            Default::default()
        }
    };
    report.checks.push(compose_network_check(&workspace));

    let podman = match detect_podman(config.podman.as_deref()) {
        Ok(podman) => {
            report.checks.push(RuntimeCheck {
                name: "podman".to_string(),
                ok: true,
                detail: podman.display().to_string(),
            });
            report.podman = Some(podman.clone());
            podman
        }
        Err(error) => {
            report.checks.push(RuntimeCheck {
                name: "podman".to_string(),
                ok: false,
                detail: error.to_string(),
            });
            PathBuf::from("podman")
        }
    };

    report
        .checks
        .push(podman_compose_check(verify_compose(&podman)));

    for tool in ["cargo", "bun", "uv"] {
        report.checks.push(command_check(tool));
    }
    report.checks.push(runtime_database_url_check_from_values(
        env::var("BIJMANTRA_DATABASE_URL").ok().as_deref(),
        env::var("DATABASE_URL").ok().as_deref(),
    ));
    report.checks.push(live_database_url_check_from_value(
        env::var("BIJMANTRA_LIVE_DATABASE_URL").ok().as_deref(),
    ));

    let mut services = default_registry(&workspace, &podman);
    apply_config(&mut services, &config);
    report.services = services.len();
    report.checks.push(port_conflict_check(&services));
    report.checks.push(RuntimeCheck {
        name: "service-registry".to_string(),
        ok: !services.is_empty(),
        detail: format!("{} services registered", services.len()),
    });

    report
}

fn command_check(command: &str) -> RuntimeCheck {
    if let Some(path) = windows_winget_link(command) {
        return RuntimeCheck {
            name: command.to_string(),
            ok: true,
            detail: path.display().to_string(),
        };
    }

    let output = if cfg!(windows) {
        Command::new("where.exe").arg(command).output()
    } else {
        Command::new("sh")
            .args(["-c", &format!("command -v {command}")])
            .output()
    };

    match output {
        Ok(output) if output.status.success() => RuntimeCheck {
            name: command.to_string(),
            ok: true,
            detail: String::from_utf8_lossy(&output.stdout)
                .lines()
                .next()
                .unwrap_or("available")
                .trim()
                .to_string(),
        },
        Ok(output) => RuntimeCheck {
            name: command.to_string(),
            ok: false,
            detail: String::from_utf8_lossy(&output.stderr).trim().to_string(),
        },
        Err(error) => RuntimeCheck {
            name: command.to_string(),
            ok: false,
            detail: error.to_string(),
        },
    }
}

fn compose_network_check(workspace: &Path) -> RuntimeCheck {
    let compose_path = workspace.join("compose.yaml");
    match fs::read_to_string(&compose_path) {
        Ok(text) => compose_network_check_from_text(&text),
        Err(error) => RuntimeCheck {
            name: "compose-network".to_string(),
            ok: false,
            detail: format!("read compose.yaml: {error}"),
        },
    }
}

fn compose_network_check_from_text(text: &str) -> RuntimeCheck {
    let has_networks_section = text.contains("\nnetworks:");
    let has_bijmantra_network = text.contains("bijmantra-network:");
    let has_postgres_container = text.contains("container_name: bijmantra-postgres");
    let has_postgres_service = text.contains("\n  postgres:");

    if has_networks_section
        && has_bijmantra_network
        && has_postgres_container
        && has_postgres_service
    {
        return RuntimeCheck {
            name: "compose-network".to_string(),
            ok: true,
            detail: "compose declares bijmantra-network and bijmantra-postgres".to_string(),
        };
    }

    let mut missing = Vec::new();
    if !has_networks_section || !has_bijmantra_network {
        missing.push("bijmantra-network");
    }
    if !has_postgres_service {
        missing.push("postgres service");
    }
    if !has_postgres_container {
        missing.push("bijmantra-postgres container_name");
    }

    RuntimeCheck {
        name: "compose-network".to_string(),
        ok: false,
        detail: format!("compose.yaml missing {}", missing.join(", ")),
    }
}

fn port_conflict_check(services: &[Service]) -> RuntimeCheck {
    let service_ports = services
        .iter()
        .filter_map(|service| service.port.map(|port| (service.name.clone(), port)))
        .collect::<Vec<_>>();
    port_conflict_check_with_probe(&service_ports, port_is_available)
}

fn port_conflict_check_with_probe<F>(
    service_ports: &[(String, u16)],
    mut is_available: F,
) -> RuntimeCheck
where
    F: FnMut(u16) -> bool,
{
    if service_ports.is_empty() {
        return RuntimeCheck {
            name: "port-conflicts".to_string(),
            ok: true,
            detail: "no configured service ports".to_string(),
        };
    }

    let mut by_port: BTreeMap<u16, Vec<&str>> = BTreeMap::new();
    for (service, port) in service_ports {
        by_port.entry(*port).or_default().push(service.as_str());
    }

    let mut conflicts = Vec::new();
    for (port, services) in &by_port {
        if services.len() > 1 {
            conflicts.push(format!("{}={} duplicate", services.join("+"), port));
        } else if !is_available(*port) {
            conflicts.push(format!("{}={}", services[0], port));
        }
    }

    if conflicts.is_empty() {
        return RuntimeCheck {
            name: "port-conflicts".to_string(),
            ok: true,
            detail: format!("ports available: {}", format_service_ports(service_ports)),
        };
    }

    RuntimeCheck {
        name: "port-conflicts".to_string(),
        ok: false,
        detail: format!(
            "occupied or duplicated ports: {}; stop the conflicting service or override the port in .env/.bij.yaml before `bij dev`",
            conflicts.join(", ")
        ),
    }
}

fn port_is_available(port: u16) -> bool {
    TcpListener::bind(("127.0.0.1", port)).is_ok()
}

fn format_service_ports(service_ports: &[(String, u16)]) -> String {
    service_ports
        .iter()
        .map(|(service, port)| format!("{service}={port}"))
        .collect::<Vec<_>>()
        .join(", ")
}

fn podman_compose_check(result: anyhow::Result<()>) -> RuntimeCheck {
    match result {
        Ok(()) => RuntimeCheck {
            name: "podman-compose".to_string(),
            ok: true,
            detail: "available".to_string(),
        },
        Err(error) => RuntimeCheck {
            name: "podman-compose".to_string(),
            ok: false,
            detail: podman_compose_error_detail(&error.to_string()),
        },
    }
}

fn podman_compose_error_detail(message: &str) -> String {
    let lower = message.to_ascii_lowercase();
    let looks_like_stopped_machine = [
        "machine",
        "cannot connect",
        "connection refused",
        "connection reset",
        "no such file or directory",
        "podman.sock",
        "is the podman api socket running",
    ]
    .iter()
    .any(|needle| lower.contains(needle));

    if looks_like_stopped_machine {
        return format!(
            "{message}; Podman may be stopped, run `podman machine start` and rerun `bij doctor`"
        );
    }

    message.to_string()
}

fn runtime_database_url_check_from_values(
    primary: Option<&str>,
    fallback: Option<&str>,
) -> RuntimeCheck {
    if let Some(url) = non_empty_env(primary) {
        return database_url_check("runtime-database-url", "BIJMANTRA_DATABASE_URL", url);
    }
    if let Some(url) = non_empty_env(fallback) {
        return database_url_check("runtime-database-url", "DATABASE_URL", url);
    }
    RuntimeCheck {
        name: "runtime-database-url".to_string(),
        ok: true,
        detail: "optional: no BIJMANTRA_DATABASE_URL or DATABASE_URL configured; protected Rust reads report repository unavailable".to_string(),
    }
}

fn live_database_url_check_from_value(value: Option<&str>) -> RuntimeCheck {
    let Some(url) = non_empty_env(value) else {
        return RuntimeCheck {
            name: "live-database-url".to_string(),
            ok: true,
            detail:
                "optional: BIJMANTRA_LIVE_DATABASE_URL not configured; live BrAPI read tests skip"
                    .to_string(),
        };
    };
    database_url_check("live-database-url", "BIJMANTRA_LIVE_DATABASE_URL", url)
}

fn database_url_check(check_name: &str, env_name: &str, url: &str) -> RuntimeCheck {
    if is_supported_postgres_url(url) {
        return RuntimeCheck {
            name: check_name.to_string(),
            ok: true,
            detail: format!("configured from {env_name}: postgres-compatible"),
        };
    }

    RuntimeCheck {
        name: check_name.to_string(),
        ok: false,
        detail: format!(
            "{env_name} uses unsupported database URL scheme; expected postgres://, postgresql://, postgres+asyncpg://, or postgresql+asyncpg://"
        ),
    }
}

fn non_empty_env(value: Option<&str>) -> Option<&str> {
    value.map(str::trim).filter(|value| !value.is_empty())
}

fn is_supported_postgres_url(url: &str) -> bool {
    let trimmed = url.trim();
    trimmed.starts_with("postgres://")
        || trimmed.starts_with("postgresql://")
        || trimmed.starts_with("postgres+asyncpg://")
        || trimmed.starts_with("postgresql+asyncpg://")
}

fn windows_winget_link(command: &str) -> Option<PathBuf> {
    if !cfg!(windows) {
        return None;
    }
    let local_app_data = env::var_os("LOCALAPPDATA")?;
    let candidate = Path::new(&local_app_data)
        .join("Microsoft")
        .join("WinGet")
        .join("Links")
        .join(format!("{command}.exe"));
    candidate.is_file().then_some(candidate)
}

#[cfg(test)]
mod tests {
    use super::{
        compose_network_check_from_text, is_supported_postgres_url,
        live_database_url_check_from_value, podman_compose_error_detail,
        port_conflict_check_with_probe, runtime_database_url_check_from_values,
    };

    #[test]
    fn runtime_database_url_check_is_optional_when_unconfigured() {
        let check = runtime_database_url_check_from_values(None, None);

        assert_eq!(check.name, "runtime-database-url");
        assert!(check.ok);
        assert!(check.detail.contains("optional"));
        assert!(check.detail.contains("protected Rust reads"));
    }

    #[test]
    fn runtime_database_url_check_prefers_primary_and_redacts_value() {
        let check = runtime_database_url_check_from_values(
            Some("postgres://user:secret@example.test/bijmantra"),
            Some("sqlite:///should-not-appear.db"),
        );

        assert!(check.ok);
        assert!(check.detail.contains("BIJMANTRA_DATABASE_URL"));
        assert!(check.detail.contains("postgres-compatible"));
        assert!(!check.detail.contains("secret"));
        assert!(!check.detail.contains("example.test"));
        assert!(!check.detail.contains("sqlite"));
    }

    #[test]
    fn runtime_database_url_check_accepts_fastapi_asyncpg_fallback() {
        let check = runtime_database_url_check_from_values(
            Some("   "),
            Some("postgresql+asyncpg://user:secret@example.test/bijmantra"),
        );

        assert!(check.ok);
        assert!(check.detail.contains("DATABASE_URL"));
        assert!(!check.detail.contains("secret"));
    }

    #[test]
    fn live_database_url_check_rejects_unsupported_scheme_without_echoing_value() {
        let check = live_database_url_check_from_value(Some("sqlite:///tmp/bijmantra.db"));

        assert_eq!(check.name, "live-database-url");
        assert!(!check.ok);
        assert!(check.detail.contains("BIJMANTRA_LIVE_DATABASE_URL"));
        assert!(check.detail.contains("unsupported database URL scheme"));
        assert!(!check.detail.contains("tmp/bijmantra.db"));
    }

    #[test]
    fn supported_postgres_url_schemes_match_rust_read_normalization_boundary() {
        for url in [
            "postgres://user:pass@localhost/db",
            "postgresql://user:pass@localhost/db",
            "postgres+asyncpg://user:pass@localhost/db",
            "postgresql+asyncpg://user:pass@localhost/db",
        ] {
            assert!(is_supported_postgres_url(url));
        }

        for url in ["sqlite:///bijmantra.db", "mysql://localhost/db", ""] {
            assert!(!is_supported_postgres_url(url));
        }
    }

    #[test]
    fn podman_compose_error_detail_explains_stopped_machine_recovery() {
        let detail =
            podman_compose_error_detail("podman compose version: Cannot connect to Podman socket");

        assert!(detail.contains("podman machine start"));
        assert!(detail.contains("bij doctor"));
    }

    #[test]
    fn podman_compose_error_detail_preserves_unrelated_errors() {
        let message = "podman compose version exited with exit status: 125";

        assert_eq!(podman_compose_error_detail(message), message);
    }

    #[test]
    fn compose_network_check_finds_expected_network_and_postgres_container() {
        let text = r#"
services:
  postgres:
    container_name: bijmantra-postgres
    networks:
      - bijmantra-network
networks:
  bijmantra-network:
    driver: bridge
"#;

        let check = compose_network_check_from_text(text);

        assert_eq!(check.name, "compose-network");
        assert!(check.ok);
        assert!(check.detail.contains("bijmantra-network"));
        assert!(check.detail.contains("bijmantra-postgres"));
    }

    #[test]
    fn compose_network_check_reports_missing_network_anchors() {
        let check = compose_network_check_from_text("services:\n  postgres:\n");

        assert_eq!(check.name, "compose-network");
        assert!(!check.ok);
        assert!(check.detail.contains("bijmantra-network"));
        assert!(check.detail.contains("bijmantra-postgres container_name"));
    }

    #[test]
    fn port_conflict_check_reports_available_ports() {
        let service_ports = vec![
            ("backend".to_string(), 8000),
            ("frontend".to_string(), 5656),
        ];

        let check = port_conflict_check_with_probe(&service_ports, |_| true);

        assert_eq!(check.name, "port-conflicts");
        assert!(check.ok);
        assert!(check.detail.contains("backend=8000"));
        assert!(check.detail.contains("frontend=5656"));
    }

    #[test]
    fn port_conflict_check_reports_occupied_ports_with_remedy() {
        let service_ports = vec![
            ("backend".to_string(), 8000),
            ("frontend".to_string(), 5656),
        ];

        let check = port_conflict_check_with_probe(&service_ports, |port| port != 8000);

        assert_eq!(check.name, "port-conflicts");
        assert!(!check.ok);
        assert!(check.detail.contains("backend=8000"));
        assert!(check.detail.contains("override the port"));
        assert!(check.detail.contains("bij dev"));
    }

    #[test]
    fn port_conflict_check_reports_duplicate_configured_ports() {
        let service_ports = vec![
            ("backend".to_string(), 8000),
            ("frontend".to_string(), 8000),
        ];

        let check = port_conflict_check_with_probe(&service_ports, |_| true);

        assert_eq!(check.name, "port-conflicts");
        assert!(!check.ok);
        assert!(check.detail.contains("backend+frontend=8000 duplicate"));
    }
}
