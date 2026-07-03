use std::ffi::OsStr;
use std::fmt;
use std::fs::{self, OpenOptions};
use std::path::{Path, PathBuf};
use std::process::{ExitStatus, Stdio};
use std::time::{Duration, SystemTime};

use thiserror::Error;
use tokio::process::{Child, Command};
use tokio::time::timeout;

use crate::registry::{Service, ServiceType};

const DEFAULT_PROCESS_STOP_TIMEOUT: Duration = Duration::from_secs(10);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ComposeAction {
    Start,
    Stop,
    Restart,
}

impl ComposeAction {
    fn lifecycle_args(self) -> &'static [&'static str] {
        match self {
            Self::Start => &["up", "-d"],
            Self::Stop => &["stop"],
            Self::Restart => &["restart"],
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandSpec {
    pub program: PathBuf,
    pub args: Vec<String>,
    pub current_dir: Option<PathBuf>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProcessCommandSpec {
    pub command: CommandSpec,
    pub log_path: PathBuf,
}

pub struct ManagedProcess {
    service_name: String,
    pid: u32,
    log_path: PathBuf,
    started_at: SystemTime,
    child: Child,
}

impl ManagedProcess {
    pub fn service_name(&self) -> &str {
        &self.service_name
    }

    pub fn pid(&self) -> u32 {
        self.pid
    }

    pub fn log_path(&self) -> &Path {
        &self.log_path
    }

    pub fn started_at(&self) -> SystemTime {
        self.started_at
    }
}

impl fmt::Debug for ManagedProcess {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ManagedProcess")
            .field("service_name", &self.service_name)
            .field("pid", &self.pid)
            .field("log_path", &self.log_path)
            .field("started_at", &self.started_at)
            .finish_non_exhaustive()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProcessExit {
    pub service_name: String,
    pub pid: u32,
    pub status_code: Option<i32>,
    pub forced: bool,
}

#[derive(Debug, Error)]
pub enum OrchestrationError {
    #[error("podman path is empty")]
    EmptyPodmanPath,
    #[error("compose file path is empty")]
    EmptyComposeFile,
    #[error("service {name:?} is not a container service")]
    NotContainerService {
        name: String,
        service_type: ServiceType,
    },
    #[error("service has no compose target")]
    MissingComposeTarget,
    #[error("podman {args}: {message}")]
    ComposeFailed { args: String, message: String },
    #[error("run podman compose: {source}")]
    ComposeIo {
        #[source]
        source: std::io::Error,
    },
    #[error("service {name:?} is not a process service")]
    NotProcessService {
        name: String,
        service_type: ServiceType,
    },
    #[error("service {name:?} has no process command")]
    MissingProcessCommand { name: String },
    #[error("log directory is empty")]
    EmptyLogDirectory,
    #[error("service name is empty")]
    EmptyServiceName,
    #[error("service name {name:?} cannot be used as a log file name")]
    InvalidServiceName { name: String },
    #[error("create log directory {path}: {source}")]
    CreateLogDirectory {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    #[error("open process log {path}: {source}")]
    OpenProcessLog {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    #[error("start process {name:?}: {source}")]
    StartProcess {
        name: String,
        #[source]
        source: std::io::Error,
    },
    #[error("process {name:?} started without an observable pid")]
    MissingStartedPid { name: String },
    #[error("inspect process {name:?}: {source}")]
    InspectProcess {
        name: String,
        #[source]
        source: std::io::Error,
    },
    #[error("signal process pid {pid}: {message}")]
    SignalProcess { pid: u32, message: String },
    #[error("wait for process {name:?}: {source}")]
    WaitProcess {
        name: String,
        #[source]
        source: std::io::Error,
    },
    #[error("kill process {name:?}: {source}")]
    KillProcess {
        name: String,
        #[source]
        source: std::io::Error,
    },
}

pub fn build_compose_command(
    podman: &Path,
    compose_file: &Path,
    service: &Service,
    action: ComposeAction,
) -> Result<CommandSpec, OrchestrationError> {
    if is_empty_path(podman) {
        return Err(OrchestrationError::EmptyPodmanPath);
    }
    if is_empty_path(compose_file) {
        return Err(OrchestrationError::EmptyComposeFile);
    }
    if service.service_type != ServiceType::Container {
        return Err(OrchestrationError::NotContainerService {
            name: service.name.clone(),
            service_type: service.service_type,
        });
    }

    let target = compose_target(service)?;
    let mut args = vec!["compose".to_string()];
    for profile in &service.compose_profiles {
        args.push("--profile".to_string());
        args.push(profile.clone());
    }
    args.extend([
        "--file".to_string(),
        compose_file.to_string_lossy().to_string(),
    ]);
    args.extend(
        action
            .lifecycle_args()
            .iter()
            .map(|argument| (*argument).to_string()),
    );
    args.push(target);

    Ok(CommandSpec {
        program: podman.to_path_buf(),
        args,
        current_dir: None,
    })
}

pub fn compose_target(service: &Service) -> Result<String, OrchestrationError> {
    first_non_empty([
        service.compose_service.as_deref(),
        Some(service.name.as_str()),
        service.container_name.as_deref(),
    ])
    .map(str::to_string)
    .ok_or(OrchestrationError::MissingComposeTarget)
}

pub async fn start_container(
    podman: &Path,
    compose_file: &Path,
    service: &Service,
) -> Result<(), OrchestrationError> {
    run_compose_command(build_compose_command(
        podman,
        compose_file,
        service,
        ComposeAction::Start,
    )?)
    .await
}

pub async fn stop_container(
    podman: &Path,
    compose_file: &Path,
    service: &Service,
) -> Result<(), OrchestrationError> {
    run_compose_command(build_compose_command(
        podman,
        compose_file,
        service,
        ComposeAction::Stop,
    )?)
    .await
}

pub async fn restart_container(
    podman: &Path,
    compose_file: &Path,
    service: &Service,
) -> Result<(), OrchestrationError> {
    run_compose_command(build_compose_command(
        podman,
        compose_file,
        service,
        ComposeAction::Restart,
    )?)
    .await
}

async fn run_compose_command(spec: CommandSpec) -> Result<(), OrchestrationError> {
    let output = Command::new(&spec.program)
        .args(&spec.args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await
        .map_err(|source| OrchestrationError::ComposeIo { source })?;

    if output.status.success() {
        Ok(())
    } else {
        Err(OrchestrationError::ComposeFailed {
            args: spec.args.join(" "),
            message: command_output_message(&output),
        })
    }
}

pub fn build_process_command(
    service: &Service,
    log_dir: &Path,
) -> Result<ProcessCommandSpec, OrchestrationError> {
    if service.service_type != ServiceType::Process {
        return Err(OrchestrationError::NotProcessService {
            name: service.name.clone(),
            service_type: service.service_type,
        });
    }
    if is_empty_path(log_dir) {
        return Err(OrchestrationError::EmptyLogDirectory);
    }

    let Some(program) = first_non_empty([service.cmd.first().map(String::as_str)]) else {
        return Err(OrchestrationError::MissingProcessCommand {
            name: service.name.clone(),
        });
    };

    let log_path = process_log_path(log_dir, service)?;
    Ok(ProcessCommandSpec {
        command: CommandSpec {
            program: PathBuf::from(program),
            args: service.cmd.iter().skip(1).cloned().collect(),
            current_dir: service.work_dir.clone(),
        },
        log_path,
    })
}

pub fn process_log_path(log_dir: &Path, service: &Service) -> Result<PathBuf, OrchestrationError> {
    if is_empty_path(log_dir) {
        return Err(OrchestrationError::EmptyLogDirectory);
    }

    let name = service.name.trim();
    if name.is_empty() {
        return Err(OrchestrationError::EmptyServiceName);
    }
    if name.contains('/') || name.contains('\\') || name == "." || name == ".." {
        return Err(OrchestrationError::InvalidServiceName {
            name: service.name.clone(),
        });
    }

    Ok(log_dir.join(format!("{name}.log")))
}

pub async fn start_process(
    service: &Service,
    log_dir: &Path,
) -> Result<ManagedProcess, OrchestrationError> {
    let spec = build_process_command(service, log_dir)?;

    fs::create_dir_all(log_dir).map_err(|source| OrchestrationError::CreateLogDirectory {
        path: log_dir.to_path_buf(),
        source,
    })?;

    let stdout = open_log_append(&spec.log_path)?;
    let stderr = open_log_append(&spec.log_path)?;

    let mut command = Command::new(&spec.command.program);
    command
        .args(&spec.command.args)
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr));
    if let Some(work_dir) = &spec.command.current_dir {
        command.current_dir(work_dir);
    }

    let child = command
        .spawn()
        .map_err(|source| OrchestrationError::StartProcess {
            name: service.name.clone(),
            source,
        })?;
    let pid = child
        .id()
        .ok_or_else(|| OrchestrationError::MissingStartedPid {
            name: service.name.clone(),
        })?;

    Ok(ManagedProcess {
        service_name: service.name.clone(),
        pid,
        log_path: spec.log_path,
        started_at: SystemTime::now(),
        child,
    })
}

pub async fn stop_process(
    mut process: ManagedProcess,
    force: bool,
    graceful_timeout: Option<Duration>,
) -> Result<ProcessExit, OrchestrationError> {
    if let Some(status) =
        process
            .child
            .try_wait()
            .map_err(|source| OrchestrationError::InspectProcess {
                name: process.service_name.clone(),
                source,
            })?
    {
        return Ok(process_exit(&process, status, false));
    }

    if force {
        kill_process(&mut process).await?;
        let status = wait_process(&mut process).await?;
        return Ok(process_exit(&process, status, true));
    }

    if let Err(error) = signal_process(process.pid).await {
        if let Some(status) =
            process
                .child
                .try_wait()
                .map_err(|source| OrchestrationError::InspectProcess {
                    name: process.service_name.clone(),
                    source,
                })?
        {
            return Ok(process_exit(&process, status, false));
        }
        return Err(error);
    }

    let wait_timeout = graceful_timeout
        .filter(|duration| !duration.is_zero())
        .unwrap_or(DEFAULT_PROCESS_STOP_TIMEOUT);

    match timeout(wait_timeout, wait_process(&mut process)).await {
        Ok(Ok(status)) => Ok(process_exit(&process, status, false)),
        Ok(Err(error)) => Err(error),
        Err(_) => {
            kill_process(&mut process).await?;
            let status = wait_process(&mut process).await?;
            Ok(process_exit(&process, status, true))
        }
    }
}

async fn wait_process(process: &mut ManagedProcess) -> Result<ExitStatus, OrchestrationError> {
    process
        .child
        .wait()
        .await
        .map_err(|source| OrchestrationError::WaitProcess {
            name: process.service_name.clone(),
            source,
        })
}

async fn kill_process(process: &mut ManagedProcess) -> Result<(), OrchestrationError> {
    process
        .child
        .start_kill()
        .map_err(|source| OrchestrationError::KillProcess {
            name: process.service_name.clone(),
            source,
        })
}

#[cfg(windows)]
async fn signal_process(pid: u32) -> Result<(), OrchestrationError> {
    let pid_arg = pid.to_string();
    let output = Command::new("taskkill")
        .args(["/PID", pid_arg.as_str(), "/T"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await
        .map_err(|source| OrchestrationError::SignalProcess {
            pid,
            message: source.to_string(),
        })?;

    if output.status.success() {
        Ok(())
    } else {
        Err(OrchestrationError::SignalProcess {
            pid,
            message: command_output_message(&output),
        })
    }
}

#[cfg(not(windows))]
async fn signal_process(pid: u32) -> Result<(), OrchestrationError> {
    let output = Command::new("kill")
        .arg("-TERM")
        .arg(pid.to_string())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await
        .map_err(|source| OrchestrationError::SignalProcess {
            pid,
            message: source.to_string(),
        })?;

    if output.status.success() {
        Ok(())
    } else {
        Err(OrchestrationError::SignalProcess {
            pid,
            message: command_output_message(&output),
        })
    }
}

fn process_exit(process: &ManagedProcess, status: ExitStatus, forced: bool) -> ProcessExit {
    ProcessExit {
        service_name: process.service_name.clone(),
        pid: process.pid,
        status_code: status.code(),
        forced,
    }
}

fn open_log_append(path: &Path) -> Result<std::fs::File, OrchestrationError> {
    OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map_err(|source| OrchestrationError::OpenProcessLog {
            path: path.to_path_buf(),
            source,
        })
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

fn first_non_empty<const N: usize>(values: [Option<&str>; N]) -> Option<&str> {
    values
        .into_iter()
        .flatten()
        .map(str::trim)
        .find(|value| !value.is_empty())
}

fn is_empty_path(path: &Path) -> bool {
    path.as_os_str() == OsStr::new("")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::registry::{Probe, ServiceGroup, ServiceState};

    #[test]
    fn compose_start_command_uses_compose_file_and_service_target() {
        let service = container_service("postgres", Some("db"), Some("bijmantra-postgres"));

        let spec = build_compose_command(
            Path::new("podman"),
            Path::new("compose.yaml"),
            &service,
            ComposeAction::Start,
        )
        .unwrap();

        assert_eq!(spec.program, PathBuf::from("podman"));
        assert_eq!(spec.current_dir, None);
        assert_eq!(
            spec.args,
            vec!["compose", "--file", "compose.yaml", "up", "-d", "db"]
        );
    }

    #[test]
    fn compose_stop_and_restart_commands_match_podman_compose_lifecycle() {
        let service = container_service("redis", None, Some("bijmantra-redis"));

        let stop = build_compose_command(
            Path::new("podman"),
            Path::new("compose.yaml"),
            &service,
            ComposeAction::Stop,
        )
        .unwrap();
        let restart = build_compose_command(
            Path::new("podman"),
            Path::new("compose.yaml"),
            &service,
            ComposeAction::Restart,
        )
        .unwrap();

        assert_eq!(
            stop.args,
            vec!["compose", "--file", "compose.yaml", "stop", "redis"]
        );
        assert_eq!(
            restart.args,
            vec!["compose", "--file", "compose.yaml", "restart", "redis"]
        );
    }

    #[test]
    fn compose_command_includes_service_profiles() {
        let mut service = container_service("redis", None, Some("bijmantra-redis"));
        service.compose_profiles = vec!["infra".to_string()];

        let spec = build_compose_command(
            Path::new("podman"),
            Path::new("compose.yaml"),
            &service,
            ComposeAction::Start,
        )
        .unwrap();

        assert_eq!(
            spec.args,
            vec![
                "compose",
                "--profile",
                "infra",
                "--file",
                "compose.yaml",
                "up",
                "-d",
                "redis"
            ]
        );
    }

    #[test]
    fn compose_target_falls_back_to_container_name_when_name_is_empty() {
        let service = Service {
            name: String::new(),
            label: "Container".to_string(),
            service_type: ServiceType::Container,
            group: ServiceGroup::Core,
            experimental: false,
            port: None,
            compose_service: None,
            container_name: Some("bijmantra-container".to_string()),
            compose_profiles: Vec::new(),
            cmd: Vec::new(),
            work_dir: None,
            probe: None,
            state: ServiceState::Waiting,
        };

        assert_eq!(compose_target(&service).unwrap(), "bijmantra-container");
    }

    #[test]
    fn compose_command_rejects_process_services() {
        let service = process_service("backend");

        let error = build_compose_command(
            Path::new("podman"),
            Path::new("compose.yaml"),
            &service,
            ComposeAction::Start,
        )
        .unwrap_err();

        assert!(matches!(
            error,
            OrchestrationError::NotContainerService { .. }
        ));
    }

    #[test]
    fn process_command_spec_uses_service_command_work_dir_and_log_path() {
        let mut service = process_service("backend");
        service.cmd = vec![
            "uv".to_string(),
            "run".to_string(),
            "uvicorn".to_string(),
            "app.main:app".to_string(),
        ];
        service.work_dir = Some(PathBuf::from("backend"));

        let spec = build_process_command(&service, Path::new("logs")).unwrap();

        assert_eq!(spec.command.program, PathBuf::from("uv"));
        assert_eq!(spec.command.args, vec!["run", "uvicorn", "app.main:app"]);
        assert_eq!(spec.command.current_dir, Some(PathBuf::from("backend")));
        assert_eq!(spec.log_path, PathBuf::from("logs").join("backend.log"));
    }

    #[test]
    fn process_command_rejects_missing_command() {
        let mut service = process_service("backend");
        service.cmd.clear();

        let error = build_process_command(&service, Path::new("logs")).unwrap_err();

        assert!(matches!(
            error,
            OrchestrationError::MissingProcessCommand { .. }
        ));
    }

    #[test]
    fn process_log_path_rejects_path_traversal_names() {
        let service = process_service("../backend");

        let error = process_log_path(Path::new("logs"), &service).unwrap_err();

        assert!(matches!(
            error,
            OrchestrationError::InvalidServiceName { .. }
        ));
    }

    #[test]
    fn process_log_path_rejects_empty_log_directory() {
        let service = process_service("backend");

        let error = process_log_path(Path::new(""), &service).unwrap_err();

        assert!(matches!(error, OrchestrationError::EmptyLogDirectory));
    }

    fn container_service(
        name: &str,
        compose_service: Option<&str>,
        container_name: Option<&str>,
    ) -> Service {
        Service {
            name: name.to_string(),
            label: name.to_string(),
            service_type: ServiceType::Container,
            group: ServiceGroup::Core,
            experimental: false,
            port: None,
            compose_service: compose_service.map(str::to_string),
            container_name: container_name.map(str::to_string),
            compose_profiles: Vec::new(),
            cmd: Vec::new(),
            work_dir: None,
            probe: Some(Probe::ContainerRunning {
                runtime: PathBuf::from("podman"),
                container: container_name.unwrap_or(name).to_string(),
            }),
            state: ServiceState::Waiting,
        }
    }

    fn process_service(name: &str) -> Service {
        Service {
            name: name.to_string(),
            label: name.to_string(),
            service_type: ServiceType::Process,
            group: ServiceGroup::Core,
            experimental: false,
            port: Some(8000),
            compose_service: None,
            container_name: None,
            compose_profiles: Vec::new(),
            cmd: vec!["uv".to_string(), "run".to_string()],
            work_dir: Some(PathBuf::from(".")),
            probe: Some(Probe::Http {
                url: "http://localhost:8000/health".to_string(),
            }),
            state: ServiceState::Waiting,
        }
    }
}
