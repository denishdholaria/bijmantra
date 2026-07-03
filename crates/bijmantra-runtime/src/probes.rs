use std::process::Stdio;
use std::time::{Duration, Instant};

use serde::{Deserialize, Serialize};
use thiserror::Error;
use tokio::net::TcpStream;
use tokio::process::Command;
use tokio::time::timeout;

use crate::registry::{Probe, Service, ServiceState};

#[derive(Debug, Error)]
pub enum ProbeError {
    #[error("service has no health probe")]
    Missing,
    #[error("tcp probe {host}:{port}: {source}")]
    Tcp {
        host: String,
        port: u16,
        source: std::io::Error,
    },
    #[error("http probe {url}: {message}")]
    Http { url: String, message: String },
    #[error("exec probe {container}: {message}")]
    Exec { container: String, message: String },
    #[error("container running probe {container}: container not running")]
    ContainerNotRunning { container: String },
    #[error("probe timed out after {0:?}")]
    Timeout(Duration),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProbeResult {
    pub name: String,
    pub label: String,
    pub state: ServiceState,
    pub latency_ms: u128,
    pub error: Option<String>,
}

pub async fn probe_services(services: &[Service]) -> Vec<ProbeResult> {
    let mut results = Vec::with_capacity(services.len());
    for service in services {
        results.push(probe_service(service).await);
    }
    results
}

pub async fn probe_service(service: &Service) -> ProbeResult {
    let started_at = Instant::now();
    let outcome = match service.probe.as_ref() {
        Some(probe) => timeout(Duration::from_secs(3), run_probe(probe)).await,
        None => Ok(Err(ProbeError::Missing)),
    };

    match outcome {
        Ok(Ok(())) => ProbeResult {
            name: service.name.clone(),
            label: service.label.clone(),
            state: ServiceState::Ready,
            latency_ms: started_at.elapsed().as_millis(),
            error: None,
        },
        Ok(Err(error)) => ProbeResult {
            name: service.name.clone(),
            label: service.label.clone(),
            state: ServiceState::Degraded,
            latency_ms: started_at.elapsed().as_millis(),
            error: Some(error.to_string()),
        },
        Err(_) => ProbeResult {
            name: service.name.clone(),
            label: service.label.clone(),
            state: ServiceState::Degraded,
            latency_ms: started_at.elapsed().as_millis(),
            error: Some(ProbeError::Timeout(Duration::from_secs(3)).to_string()),
        },
    }
}

async fn run_probe(probe: &Probe) -> Result<(), ProbeError> {
    match probe {
        Probe::Tcp { host, port } => {
            TcpStream::connect((host.as_str(), *port))
                .await
                .map_err(|source| ProbeError::Tcp {
                    host: host.clone(),
                    port: *port,
                    source,
                })?;
            Ok(())
        }
        Probe::Http { url } => {
            let response = reqwest::get(url).await.map_err(|error| ProbeError::Http {
                url: url.clone(),
                message: error.to_string(),
            })?;
            if response.status().is_success() {
                Ok(())
            } else {
                Err(ProbeError::Http {
                    url: url.clone(),
                    message: format!("status {}", response.status()),
                })
            }
        }
        Probe::Exec {
            runtime,
            container,
            cmd,
        } => {
            let output = Command::new(runtime)
                .arg("exec")
                .arg(container)
                .args(cmd)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .output()
                .await
                .map_err(|error| ProbeError::Exec {
                    container: container.clone(),
                    message: error.to_string(),
                })?;
            if output.status.success() {
                Ok(())
            } else {
                Err(ProbeError::Exec {
                    container: container.clone(),
                    message: command_output_message(&output),
                })
            }
        }
        Probe::ContainerRunning { runtime, container } => {
            let output = Command::new(runtime)
                .args(["ps", "--filter"])
                .arg(format!("name={container}"))
                .args(["--format", "{{.Names}}"])
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .output()
                .await
                .map_err(|error| ProbeError::Exec {
                    container: container.clone(),
                    message: error.to_string(),
                })?;
            if !output.status.success() {
                return Err(ProbeError::Exec {
                    container: container.clone(),
                    message: command_output_message(&output),
                });
            }
            let stdout = String::from_utf8_lossy(&output.stdout);
            if stdout.lines().any(|line| line.trim() == container) {
                Ok(())
            } else {
                Err(ProbeError::ContainerNotRunning {
                    container: container.clone(),
                })
            }
        }
    }
}

fn command_output_message(output: &std::process::Output) -> String {
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    if !stderr.is_empty() {
        return stderr;
    }
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if !stdout.is_empty() {
        return stdout;
    }
    output.status.to_string()
}
