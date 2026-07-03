use std::fmt;
use std::path::PathBuf;
use std::process::Stdio;
use std::time::{Duration, Instant};

use bijmantra_runtime::{
    ProcessRegistry, Service, ServiceGroup, ServiceState, ServiceType, TrackedProcess,
    build_process_command, is_pid_running, probe_service, process_registry_path, restart_container,
    start_container, start_process, stop_container, terminate_pid, verify_compose,
};
use serde::Serialize;
use serde_json::json;
use tokio::process::Command;
use tokio::time::sleep;

use crate::runtime_commands::{
    OutputFormat, RuntimeAction, RuntimeActionKind, RuntimeCommandContext, dev_plan,
    service_group_name, service_type_name, stop_plan,
};

#[derive(Debug, Clone)]
pub struct StartArgs {
    pub workspace: Option<PathBuf>,
    pub service: String,
    pub output: OutputFormat,
    pub verify_compose: bool,
}

#[derive(Debug, Clone)]
pub struct StopArgs {
    pub workspace: Option<PathBuf>,
    pub service: String,
    pub output: OutputFormat,
    pub force: bool,
    pub verify_compose: bool,
}

#[derive(Debug, Clone)]
pub struct RestartArgs {
    pub workspace: Option<PathBuf>,
    pub service: String,
    pub output: OutputFormat,
    pub force: bool,
    pub verify_compose: bool,
}

#[derive(Debug, Clone)]
pub struct ProcessesArgs {
    pub workspace: Option<PathBuf>,
    pub output: OutputFormat,
    pub prune_stale: bool,
}

#[derive(Debug, Clone)]
pub struct StackDevArgs {
    pub workspace: Option<PathBuf>,
    pub group: ServiceGroup,
    pub output: OutputFormat,
    pub verify_compose: bool,
    pub skip_migrations: bool,
    pub wait: bool,
    pub wait_timeout: Duration,
    pub rollback: bool,
}

#[derive(Debug, Clone)]
pub struct StackStopArgs {
    pub workspace: Option<PathBuf>,
    pub group: ServiceGroup,
    pub output: OutputFormat,
    pub force: bool,
    pub verify_compose: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OperationResult {
    pub service: String,
    pub label: String,
    pub service_type: String,
    pub action: String,
    pub state: String,
    pub pid: Option<u32>,
    pub log_path: Option<String>,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProcessStatus {
    pub service: String,
    pub pid: u32,
    pub running: bool,
    pub log_path: String,
    pub command: Vec<String>,
    pub work_dir: Option<String>,
    pub started_at: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StackOperationResult {
    pub command: String,
    pub group: String,
    pub workspace: String,
    pub actions: Vec<OperationResult>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StackFailureEvent {
    pub command: String,
    pub group: String,
    pub workspace: String,
    pub failed_service: String,
    pub error: String,
    pub rollback_enabled: bool,
    pub rollback_summary: String,
    pub rollback_actions: Vec<OperationResult>,
}

#[derive(Debug, Clone)]
pub struct StackStartupError {
    event: StackFailureEvent,
}

impl StackStartupError {
    fn new(event: StackFailureEvent) -> Self {
        Self { event }
    }

    pub fn event(&self) -> &StackFailureEvent {
        &self.event
    }
}

impl fmt::Display for StackStartupError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "stack startup failed at {}: {}; rollback: {}",
            self.event.failed_service, self.event.error, self.event.rollback_summary
        )
    }
}

impl std::error::Error for StackStartupError {}

pub async fn handle_start(args: StartArgs) -> anyhow::Result<String> {
    let context = RuntimeCommandContext::load(args.workspace, false)?;
    let service = context.service(&args.service)?;
    let result = start_service(&context, &service, args.verify_compose).await?;
    render_operation(&result, args.output)
}

pub async fn handle_stop(args: StopArgs) -> anyhow::Result<String> {
    let context = RuntimeCommandContext::load(args.workspace, false)?;
    let service = context.service(&args.service)?;
    let result = stop_service(&context, &service, args.force, args.verify_compose).await?;
    render_operation(&result, args.output)
}

pub async fn handle_restart(args: RestartArgs) -> anyhow::Result<String> {
    let context = RuntimeCommandContext::load(args.workspace, false)?;
    let service = context.service(&args.service)?;

    if service.service_type == ServiceType::Container {
        if args.verify_compose {
            verify_compose(&context.podman)?;
        }
        restart_container(
            &context.podman,
            &context.workspace.join("compose.yaml"),
            &service,
        )
        .await?;
        return render_operation(
            &operation_result(
                &service,
                "restart",
                "restarted",
                None,
                None,
                "compose service restarted",
            ),
            args.output,
        );
    }

    let stop_result = stop_service(&context, &service, args.force, false).await?;
    let start_result = start_service(&context, &service, false).await?;
    render_restart(&stop_result, &start_result, args.output)
}

pub async fn handle_processes(args: ProcessesArgs) -> anyhow::Result<String> {
    let context = RuntimeCommandContext::load(args.workspace, false)?;
    let path = process_registry_path(&context.workspace);
    let mut registry = ProcessRegistry::load(&path)?;
    let mut statuses = process_statuses(&registry).await?;

    if args.prune_stale {
        let stale = statuses
            .iter()
            .filter(|status| !status.running)
            .map(|status| status.service.clone())
            .collect::<Vec<_>>();
        for service in &stale {
            registry.remove(service);
        }
        if !stale.is_empty() {
            registry.save(&path)?;
            statuses.retain(|status| status.running);
        }
    }

    render_processes(&statuses, args.output)
}

pub async fn handle_stack_dev(args: StackDevArgs) -> anyhow::Result<String> {
    let context = RuntimeCommandContext::load(args.workspace, args.verify_compose)?;
    let services = context.selected_services(args.group);
    let plan = dev_plan(&context, args.group, &services);
    let mut actions = Vec::new();
    let mut started = Vec::new();

    for action in &plan.actions {
        if action.kind == RuntimeActionKind::RunMigrations {
            match run_migrations_action(action, args.skip_migrations).await {
                Ok(result) => actions.push(result),
                Err(error) => {
                    return fail_stack_startup(
                        &context,
                        args.group,
                        &started,
                        args.rollback,
                        &action.service,
                        error,
                    )
                    .await;
                }
            }
            continue;
        }

        let service = context.service(&action.service)?;
        match start_service(&context, &service, false).await {
            Ok(result) => {
                actions.push(result);
                started.push(service.clone());
            }
            Err(error) => {
                return fail_stack_startup(
                    &context,
                    args.group,
                    &started,
                    args.rollback,
                    &action.service,
                    error,
                )
                .await;
            }
        }
        if args.wait {
            match wait_for_service(&service, args.wait_timeout).await {
                Ok(result) => actions.push(result),
                Err(error) => {
                    return fail_stack_startup(
                        &context,
                        args.group,
                        &started,
                        args.rollback,
                        &action.service,
                        error,
                    )
                    .await;
                }
            }
        }
    }

    render_stack(
        StackOperationResult {
            command: "dev".to_string(),
            group: service_group_name(args.group).to_string(),
            workspace: context.workspace.display().to_string(),
            actions,
        },
        args.output,
    )
}

async fn fail_stack_startup(
    context: &RuntimeCommandContext,
    group: ServiceGroup,
    started: &[Service],
    rollback: bool,
    failed_service: &str,
    error: anyhow::Error,
) -> anyhow::Result<String> {
    let rollback_actions = if rollback && !started.is_empty() {
        rollback_started_services(context, started).await
    } else {
        Vec::new()
    };
    let rollback_summary = if rollback_actions.is_empty() {
        if rollback {
            "not run: no started services".to_string()
        } else {
            "not run: rollback disabled".to_string()
        }
    } else {
        rollback_summary(&rollback_actions)
    };

    let event = StackFailureEvent {
        command: "dev".to_string(),
        group: service_group_name(group).to_string(),
        workspace: context.workspace.display().to_string(),
        failed_service: failed_service.to_string(),
        error: error.to_string(),
        rollback_enabled: rollback,
        rollback_summary,
        rollback_actions,
    };

    Err(StackStartupError::new(event).into())
}

async fn rollback_started_services(
    context: &RuntimeCommandContext,
    started: &[Service],
) -> Vec<OperationResult> {
    let mut results = Vec::new();
    for service in started.iter().rev() {
        match stop_service(context, service, false, false).await {
            Ok(mut result) => {
                result.action = format!("rollback-{}", result.action);
                result.detail = format!("rollback: {}", result.detail);
                results.push(result);
            }
            Err(error) => results.push(operation_result(
                service,
                "rollback",
                "failed",
                None,
                None,
                &error.to_string(),
            )),
        }
    }
    results
}

fn rollback_summary(results: &[OperationResult]) -> String {
    results
        .iter()
        .map(|result| format!("{}={}", result.service, result.state))
        .collect::<Vec<_>>()
        .join(", ")
}

pub async fn handle_stack_stop(args: StackStopArgs) -> anyhow::Result<String> {
    let context = RuntimeCommandContext::load(args.workspace, args.verify_compose)?;
    let services = context.selected_services(args.group);
    let plan = stop_plan(&context, args.group, &services, args.force);
    let mut actions = Vec::new();

    for action in &plan.actions {
        let service = context.service(&action.service)?;
        actions.push(stop_service(&context, &service, args.force, false).await?);
    }

    render_stack(
        StackOperationResult {
            command: "stop".to_string(),
            group: service_group_name(args.group).to_string(),
            workspace: context.workspace.display().to_string(),
            actions,
        },
        args.output,
    )
}

async fn start_service(
    context: &RuntimeCommandContext,
    service: &Service,
    verify_compose_runtime: bool,
) -> anyhow::Result<OperationResult> {
    match service.service_type {
        ServiceType::Container => {
            if verify_compose_runtime {
                verify_compose(&context.podman)?;
            }
            start_container(
                &context.podman,
                &context.workspace.join("compose.yaml"),
                service,
            )
            .await?;
            Ok(operation_result(
                service,
                "start",
                "started",
                None,
                None,
                "compose service started",
            ))
        }
        ServiceType::Process => {
            let registry_path = process_registry_path(&context.workspace);
            let mut registry = ProcessRegistry::load(&registry_path)?;
            if let Some(existing) = registry.get(&service.name)
                && is_pid_running(existing.pid).await?
            {
                anyhow::bail!(
                    "service {:?} is already tracked as pid {}",
                    service.name,
                    existing.pid
                );
            }

            let log_dir = context.workspace.join("logs");
            let command = build_process_command(service, &log_dir)?;
            let process = start_process(service, &log_dir).await?;
            let pid = process.pid();
            let log_path = process.log_path().to_path_buf();
            registry.upsert(TrackedProcess::new(
                &service.name,
                pid,
                log_path.clone(),
                command_spec_parts(&command.command),
                command.command.current_dir,
            ));
            registry.save(&registry_path)?;

            Ok(operation_result(
                service,
                "start",
                "started",
                Some(pid),
                Some(log_path.display().to_string()),
                "process started and tracked",
            ))
        }
    }
}

async fn stop_service(
    context: &RuntimeCommandContext,
    service: &Service,
    force: bool,
    verify_compose_runtime: bool,
) -> anyhow::Result<OperationResult> {
    match service.service_type {
        ServiceType::Container => {
            if verify_compose_runtime {
                verify_compose(&context.podman)?;
            }
            stop_container(
                &context.podman,
                &context.workspace.join("compose.yaml"),
                service,
            )
            .await?;
            Ok(operation_result(
                service,
                "stop",
                "stopped",
                None,
                None,
                "compose service stopped",
            ))
        }
        ServiceType::Process => {
            let registry_path = process_registry_path(&context.workspace);
            let mut registry = ProcessRegistry::load(&registry_path)?;
            let Some(record) = registry.remove(&service.name) else {
                return Ok(operation_result(
                    service,
                    "stop",
                    "not-tracked",
                    None,
                    None,
                    "no tracked process record",
                ));
            };

            let running = is_pid_running(record.pid).await?;
            if running {
                terminate_pid(record.pid, force).await?;
            }
            registry.save(&registry_path)?;

            Ok(operation_result(
                service,
                "stop",
                if running { "stopped" } else { "stale-cleared" },
                Some(record.pid),
                Some(record.log_path.display().to_string()),
                if running {
                    "tracked process terminated"
                } else {
                    "stale process record removed"
                },
            ))
        }
    }
}

async fn run_migrations_action(
    action: &RuntimeAction,
    skip_migrations: bool,
) -> anyhow::Result<OperationResult> {
    if skip_migrations {
        return Ok(OperationResult {
            service: action.service.clone(),
            label: action.label.clone(),
            service_type: "process".to_string(),
            action: "migrate".to_string(),
            state: "skipped".to_string(),
            pid: None,
            log_path: None,
            detail: "database migrations skipped".to_string(),
        });
    }

    let Some(program) = action.command.first() else {
        anyhow::bail!("migration action has no command");
    };

    let output = Command::new(program)
        .args(action.command.iter().skip(1))
        .current_dir(
            action
                .work_dir
                .as_ref()
                .ok_or_else(|| anyhow::anyhow!("migration action has no work directory"))?,
        )
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await?;

    if output.status.success() {
        Ok(OperationResult {
            service: action.service.clone(),
            label: action.label.clone(),
            service_type: "process".to_string(),
            action: "migrate".to_string(),
            state: "completed".to_string(),
            pid: None,
            log_path: None,
            detail: "database migrations completed".to_string(),
        })
    } else {
        anyhow::bail!(
            "database migrations failed: {}",
            command_output_message(&output)
        )
    }
}

async fn wait_for_service(
    service: &Service,
    wait_timeout: Duration,
) -> anyhow::Result<OperationResult> {
    let started_at = Instant::now();

    loop {
        let result = probe_service(service).await;
        if result.state == ServiceState::Ready {
            return Ok(operation_result(
                service,
                "probe",
                "ready",
                None,
                None,
                &format!(
                    "health probe passed in {}ms",
                    started_at.elapsed().as_millis()
                ),
            ));
        }

        if started_at.elapsed() >= wait_timeout {
            let detail = result
                .error
                .clone()
                .unwrap_or_else(|| "not ready".to_string());
            anyhow::bail!(
                "service {:?} did not become ready within {:?}: {}",
                service.name,
                wait_timeout,
                detail
            );
        }

        sleep(Duration::from_secs(1)).await;
    }
}

async fn process_statuses(registry: &ProcessRegistry) -> anyhow::Result<Vec<ProcessStatus>> {
    let mut statuses = Vec::new();
    for process in registry.list() {
        statuses.push(ProcessStatus {
            service: process.service_name.clone(),
            pid: process.pid,
            running: is_pid_running(process.pid).await?,
            log_path: process.log_path.display().to_string(),
            command: process.command.clone(),
            work_dir: process
                .work_dir
                .as_ref()
                .map(|path| path.display().to_string()),
            started_at: process.started_at.to_rfc3339(),
        });
    }
    Ok(statuses)
}

fn command_spec_parts(spec: &bijmantra_runtime::CommandSpec) -> Vec<String> {
    let mut parts = vec![spec.program.display().to_string()];
    parts.extend(spec.args.clone());
    parts
}

fn operation_result(
    service: &Service,
    action: &str,
    state: &str,
    pid: Option<u32>,
    log_path: Option<String>,
    detail: &str,
) -> OperationResult {
    OperationResult {
        service: service.name.clone(),
        label: service.label.clone(),
        service_type: service_type_name(service.service_type).to_string(),
        action: action.to_string(),
        state: state.to_string(),
        pid,
        log_path,
        detail: detail.to_string(),
    }
}

fn render_operation(result: &OperationResult, output: OutputFormat) -> anyhow::Result<String> {
    match output {
        OutputFormat::Json => Ok(serde_json::to_string_pretty(result)?),
        OutputFormat::Table => Ok(format!(
            "{:<20} {:<18} {:<10} {:<14} {:<8} {}\n",
            "service", "label", "action", "state", "pid", "detail"
        ) + &format_operation_row(result)),
    }
}

fn render_restart(
    stop_result: &OperationResult,
    start_result: &OperationResult,
    output: OutputFormat,
) -> anyhow::Result<String> {
    match output {
        OutputFormat::Json => Ok(serde_json::to_string_pretty(&json!({
            "actions": [stop_result, start_result],
        }))?),
        OutputFormat::Table => Ok(format!(
            "{:<20} {:<18} {:<10} {:<14} {:<8} {}\n{}{}",
            "service",
            "label",
            "action",
            "state",
            "pid",
            "detail",
            format_operation_row(stop_result),
            format_operation_row(start_result)
        )),
    }
}

fn render_processes(statuses: &[ProcessStatus], output: OutputFormat) -> anyhow::Result<String> {
    match output {
        OutputFormat::Json => Ok(serde_json::to_string_pretty(statuses)?),
        OutputFormat::Table => {
            let mut out = format!(
                "{:<20} {:<8} {:<8} {:<25} {}\n",
                "service", "pid", "running", "started", "log"
            );
            for status in statuses {
                out.push_str(&format!(
                    "{:<20} {:<8} {:<8} {:<25} {}\n",
                    status.service, status.pid, status.running, status.started_at, status.log_path
                ));
            }
            Ok(out)
        }
    }
}

fn render_stack(result: StackOperationResult, output: OutputFormat) -> anyhow::Result<String> {
    match output {
        OutputFormat::Json => Ok(serde_json::to_string_pretty(&result)?),
        OutputFormat::Table => {
            let mut out = String::new();
            out.push_str(&format!("command: {}\n", result.command));
            out.push_str(&format!("workspace: {}\n", result.workspace));
            out.push_str(&format!("group: {}\n\n", result.group));
            out.push_str(&format!(
                "{:<20} {:<18} {:<10} {:<14} {:<8} {}\n",
                "service", "label", "action", "state", "pid", "detail"
            ));
            for action in &result.actions {
                out.push_str(&format_operation_row(action));
            }
            Ok(out)
        }
    }
}

pub fn render_stack_failure(
    event: &StackFailureEvent,
    output: OutputFormat,
) -> anyhow::Result<String> {
    match output {
        OutputFormat::Json => Ok(serde_json::to_string_pretty(event)?),
        OutputFormat::Table => {
            let mut out = String::new();
            out.push_str(&format!("command: {}\n", event.command));
            out.push_str(&format!("workspace: {}\n", event.workspace));
            out.push_str(&format!("group: {}\n", event.group));
            out.push_str(&format!("failed service: {}\n", event.failed_service));
            out.push_str(&format!("error: {}\n", event.error));
            out.push_str(&format!(
                "rollback: {} ({})\n",
                if event.rollback_enabled {
                    "enabled"
                } else {
                    "disabled"
                },
                event.rollback_summary
            ));

            if !event.rollback_actions.is_empty() {
                out.push('\n');
                out.push_str(&format!(
                    "{:<20} {:<18} {:<10} {:<14} {:<8} {}\n",
                    "service", "label", "action", "state", "pid", "detail"
                ));
                for action in &event.rollback_actions {
                    out.push_str(&format_operation_row(action));
                }
            }
            Ok(out)
        }
    }
}

fn format_operation_row(result: &OperationResult) -> String {
    format!(
        "{:<20} {:<18} {:<10} {:<14} {:<8} {}\n",
        result.service,
        result.label,
        result.action,
        result.state,
        result
            .pid
            .map(|pid| pid.to_string())
            .unwrap_or_else(|| "-".to_string()),
        result.detail
    )
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn render_stack_table_contains_command_group_and_action_rows() {
        let output = render_stack(
            StackOperationResult {
                command: "dev".to_string(),
                group: "core".to_string(),
                workspace: "C:/bijmantra".to_string(),
                actions: vec![OperationResult {
                    service: "backend".to_string(),
                    label: "Backend API".to_string(),
                    service_type: "process".to_string(),
                    action: "start".to_string(),
                    state: "started".to_string(),
                    pid: Some(42),
                    log_path: Some("logs/backend.log".to_string()),
                    detail: "process started and tracked".to_string(),
                }],
            },
            OutputFormat::Table,
        )
        .unwrap();

        assert!(output.contains("command: dev"));
        assert!(output.contains("group: core"));
        assert!(output.contains("backend"));
        assert!(output.contains("started"));
    }

    #[tokio::test]
    async fn migration_action_can_be_skipped_without_executing_command() {
        let action = RuntimeAction {
            service: "_migrations".to_string(),
            label: "Database migrations".to_string(),
            kind: RuntimeActionKind::RunMigrations,
            command: vec!["definitely-not-a-real-command".to_string()],
            work_dir: Some(PathBuf::from("backend")),
            detail: "run migrations".to_string(),
        };

        let result = run_migrations_action(&action, true).await.unwrap();

        assert_eq!(result.action, "migrate");
        assert_eq!(result.state, "skipped");
    }

    #[test]
    fn rollback_summary_lists_service_states() {
        let results = vec![
            OperationResult {
                service: "frontend".to_string(),
                label: "Frontend".to_string(),
                service_type: "process".to_string(),
                action: "rollback-stop".to_string(),
                state: "stopped".to_string(),
                pid: Some(101),
                log_path: None,
                detail: "rollback: tracked process terminated".to_string(),
            },
            OperationResult {
                service: "postgres".to_string(),
                label: "PostgreSQL".to_string(),
                service_type: "container".to_string(),
                action: "rollback-stop".to_string(),
                state: "stopped".to_string(),
                pid: None,
                log_path: None,
                detail: "rollback: compose service stopped".to_string(),
            },
        ];

        assert_eq!(
            rollback_summary(&results),
            "frontend=stopped, postgres=stopped"
        );
    }

    #[test]
    fn stack_failure_event_renders_json_with_rollback_actions() {
        let event = StackFailureEvent {
            command: "dev".to_string(),
            group: "infra".to_string(),
            workspace: "/repo".to_string(),
            failed_service: "backend".to_string(),
            error: "health probe timed out".to_string(),
            rollback_enabled: true,
            rollback_summary: "postgres=stopped".to_string(),
            rollback_actions: vec![OperationResult {
                service: "postgres".to_string(),
                label: "PostgreSQL".to_string(),
                service_type: "container".to_string(),
                action: "rollback-stop".to_string(),
                state: "stopped".to_string(),
                pid: None,
                log_path: None,
                detail: "rollback: compose service stopped".to_string(),
            }],
        };

        let output = render_stack_failure(&event, OutputFormat::Json).unwrap();
        let value: serde_json::Value = serde_json::from_str(&output).unwrap();

        assert_eq!(value["command"], "dev");
        assert_eq!(value["failedService"], "backend");
        assert_eq!(value["rollbackEnabled"], true);
        assert_eq!(value["rollbackActions"][0]["action"], "rollback-stop");
    }

    #[test]
    fn stack_startup_error_display_preserves_failure_and_rollback_summary() {
        let event = StackFailureEvent {
            command: "dev".to_string(),
            group: "infra".to_string(),
            workspace: "/repo".to_string(),
            failed_service: "backend".to_string(),
            error: "health probe timed out".to_string(),
            rollback_enabled: false,
            rollback_summary: "not run: rollback disabled".to_string(),
            rollback_actions: Vec::new(),
        };

        let error = StackStartupError::new(event);

        assert_eq!(
            error.to_string(),
            "stack startup failed at backend: health probe timed out; rollback: not run: rollback disabled"
        );
    }
}
