#![allow(dead_code)]

use std::collections::BTreeSet;
use std::fmt;
use std::path::{Path, PathBuf};

use anyhow::Context;
use bijmantra_runtime::{
    ProbeResult, Service, ServiceGroup, ServiceState, ServiceType, apply_config, default_registry,
    detect_podman, load_config, probe_services, resolve_workspace, services_for_group,
    verify_compose,
};
use serde_json::json;

const MIGRATIONS_STEP: &str = "_migrations";
const BOOT_ORDER: &[&[&str]] = &[
    &["postgres"],
    &["redis", "minio", "meilisearch"],
    &[MIGRATIONS_STEP],
    &["backend"],
    &["frontend"],
    &[
        "beingbijmantra",
        "chloe-gateway",
        "chloe-cli",
        "chloe-sandbox",
    ],
];

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum OutputFormat {
    #[default]
    Table,
    Json,
}

impl OutputFormat {
    pub fn from_json(json: bool) -> Self {
        if json { Self::Json } else { Self::Table }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandOutput {
    body: String,
}

impl CommandOutput {
    pub fn new(body: impl Into<String>) -> Self {
        Self { body: body.into() }
    }

    pub fn body(&self) -> &str {
        &self.body
    }

    pub fn into_string(self) -> String {
        self.body
    }

    pub fn is_empty(&self) -> bool {
        self.body.is_empty()
    }
}

impl fmt::Display for CommandOutput {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.body)
    }
}

#[derive(Debug, Clone)]
pub struct RuntimeCommandContext {
    pub workspace: PathBuf,
    pub podman: PathBuf,
    pub services: Vec<Service>,
}

impl RuntimeCommandContext {
    pub fn load(workspace: Option<PathBuf>, verify_compose_runtime: bool) -> anyhow::Result<Self> {
        let workspace = resolve_workspace(workspace)?;
        let config = load_config(&workspace).with_context(|| {
            format!("failed to load runtime config from {}", workspace.display())
        })?;
        let podman = detect_podman(config.podman.as_deref())?;

        if verify_compose_runtime {
            verify_compose(&podman)?;
        }

        let mut services = default_registry(&workspace, &podman);
        apply_config(&mut services, &config);

        Ok(Self {
            workspace,
            podman,
            services,
        })
    }

    pub fn selected_services(&self, group: ServiceGroup) -> Vec<Service> {
        services_for_group(&self.services, group)
    }

    pub fn service(&self, name: &str) -> anyhow::Result<Service> {
        find_service(&self.services, name)
            .cloned()
            .ok_or_else(|| unknown_service_error(name, &self.services))
    }
}

#[derive(Debug, Clone)]
pub struct DevArgs {
    pub workspace: Option<PathBuf>,
    pub group: ServiceGroup,
    pub output: OutputFormat,
    pub verify_compose: bool,
}

impl Default for DevArgs {
    fn default() -> Self {
        Self {
            workspace: None,
            group: ServiceGroup::Infra,
            output: OutputFormat::Table,
            verify_compose: true,
        }
    }
}

#[derive(Debug, Clone)]
pub struct StatusArgs {
    pub workspace: Option<PathBuf>,
    pub group: ServiceGroup,
    pub output: OutputFormat,
    pub probe: bool,
}

impl Default for StatusArgs {
    fn default() -> Self {
        Self {
            workspace: None,
            group: ServiceGroup::Autonomy,
            output: OutputFormat::Table,
            probe: true,
        }
    }
}

#[derive(Debug, Clone)]
pub struct StopArgs {
    pub workspace: Option<PathBuf>,
    pub group: ServiceGroup,
    pub output: OutputFormat,
    pub force: bool,
    pub verify_compose: bool,
}

impl Default for StopArgs {
    fn default() -> Self {
        Self {
            workspace: None,
            group: ServiceGroup::Autonomy,
            output: OutputFormat::Table,
            force: false,
            verify_compose: true,
        }
    }
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
pub struct LogsArgs {
    pub workspace: Option<PathBuf>,
    pub service: Option<String>,
    pub group: ServiceGroup,
    pub output: OutputFormat,
    pub lines: usize,
    pub follow: bool,
}

impl Default for LogsArgs {
    fn default() -> Self {
        Self {
            workspace: None,
            service: None,
            group: ServiceGroup::Autonomy,
            output: OutputFormat::Table,
            lines: 50,
            follow: true,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimePlan {
    pub command: &'static str,
    pub workspace: PathBuf,
    pub group: Option<ServiceGroup>,
    pub actions: Vec<RuntimeAction>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimeAction {
    pub service: String,
    pub label: String,
    pub kind: RuntimeActionKind,
    pub command: Vec<String>,
    pub work_dir: Option<PathBuf>,
    pub detail: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RuntimeActionKind {
    StartContainer,
    StartProcess,
    StopContainer,
    StopProcess,
    RestartContainer,
    RunMigrations,
    Probe,
    TailContainerLogs,
    TailFileLogs,
    SelectLogSource,
}

impl RuntimeActionKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::StartContainer => "start-container",
            Self::StartProcess => "start-process",
            Self::StopContainer => "stop-container",
            Self::StopProcess => "stop-process",
            Self::RestartContainer => "restart-container",
            Self::RunMigrations => "run-migrations",
            Self::Probe => "probe",
            Self::TailContainerLogs => "tail-container-logs",
            Self::TailFileLogs => "tail-file-logs",
            Self::SelectLogSource => "select-log-source",
        }
    }
}

pub fn handle_dev(args: DevArgs) -> anyhow::Result<CommandOutput> {
    let context = RuntimeCommandContext::load(args.workspace, args.verify_compose)?;
    let services = context.selected_services(args.group);
    let plan = dev_plan(&context, args.group, &services);
    render_plan_output(&plan, args.output)
}

pub async fn handle_status(args: StatusArgs) -> anyhow::Result<CommandOutput> {
    let context = RuntimeCommandContext::load(args.workspace, false)?;
    let services = context.selected_services(args.group);

    if !args.probe {
        return match args.output {
            OutputFormat::Table => Ok(CommandOutput::new(format_services_table(&services))),
            OutputFormat::Json => {
                let services = serde_json::to_value(&services)?;
                render_json_value(json!({
                    "workspace": context.workspace.display().to_string(),
                    "group": service_group_name(args.group),
                    "services": services,
                }))
            }
        };
    }

    let results = probe_services(&services).await;
    render_probe_output(&context.workspace, args.group, &results, args.output)
}

pub fn handle_stop(args: StopArgs) -> anyhow::Result<CommandOutput> {
    let context = RuntimeCommandContext::load(args.workspace, args.verify_compose)?;
    let services = context.selected_services(args.group);
    let plan = stop_plan(&context, args.group, &services, args.force);
    render_plan_output(&plan, args.output)
}

pub fn handle_restart(args: RestartArgs) -> anyhow::Result<CommandOutput> {
    let context = RuntimeCommandContext::load(args.workspace, args.verify_compose)?;
    let service = context.service(&args.service)?;
    let plan = restart_plan(&context, service, args.force);
    render_plan_output(&plan, args.output)
}

pub fn handle_logs(args: LogsArgs) -> anyhow::Result<CommandOutput> {
    let context = RuntimeCommandContext::load(args.workspace, false)?;
    let services = match &args.service {
        Some(name) => vec![context.service(name)?],
        None => context.selected_services(args.group),
    };
    let group = if args.service.is_some() {
        None
    } else {
        Some(args.group)
    };
    let plan = logs_plan(&context, group, &services, args.lines, args.follow);
    render_plan_output(&plan, args.output)
}

pub fn format_services_table(services: &[Service]) -> String {
    let mut out = String::new();
    out.push_str(&format!(
        "{:<20} {:<18} {:<10} {:<10} {:<8} {}\n",
        "name", "label", "type", "group", "port", "target"
    ));

    for service in services {
        out.push_str(&format!(
            "{:<20} {:<18} {:<10} {:<10} {:<8} {}\n",
            service.name,
            service.label,
            service_type_name(service.service_type),
            service_group_name(service.group),
            format_port(service.port),
            service_target(service)
        ));
    }

    out
}

pub fn format_probe_results_table(results: &[ProbeResult]) -> String {
    let mut out = String::new();
    out.push_str(&format!(
        "{:<20} {:<18} {:<10} {:<10} {}\n",
        "name", "label", "state", "latency", "detail"
    ));

    for result in results {
        out.push_str(&format!(
            "{:<20} {:<18} {:<10} {:>6}ms   {}\n",
            result.name,
            result.label,
            service_state_name(result.state),
            result.latency_ms,
            result.error.as_deref().unwrap_or("ok")
        ));
    }

    out
}

pub fn format_plan_table(plan: &RuntimePlan) -> String {
    let mut out = String::new();
    out.push_str(&format!("command: {}\n", plan.command));
    out.push_str(&format!("workspace: {}\n", plan.workspace.display()));
    if let Some(group) = plan.group {
        out.push_str(&format!("group: {}\n", service_group_name(group)));
    }
    out.push('\n');
    out.push_str(&format!(
        "{:<20} {:<18} {:<21} {}\n",
        "service", "label", "action", "detail"
    ));

    for action in &plan.actions {
        let detail = if action.command.is_empty() {
            action.detail.clone()
        } else {
            format!("{} | {}", action.detail, shell_join(&action.command))
        };
        out.push_str(&format!(
            "{:<20} {:<18} {:<21} {}\n",
            action.service,
            action.label,
            action.kind.as_str(),
            detail
        ));
    }

    out
}

pub fn service_group_name(group: ServiceGroup) -> &'static str {
    match group {
        ServiceGroup::Core => "core",
        ServiceGroup::Infra => "infra",
        ServiceGroup::Autonomy => "autonomy",
    }
}

pub fn service_type_name(service_type: ServiceType) -> &'static str {
    match service_type {
        ServiceType::Container => "container",
        ServiceType::Process => "process",
    }
}

pub fn service_state_name(state: ServiceState) -> &'static str {
    match state {
        ServiceState::Waiting => "waiting",
        ServiceState::Ready => "ready",
        ServiceState::Degraded => "degraded",
    }
}

pub(crate) fn dev_plan(
    context: &RuntimeCommandContext,
    group: ServiceGroup,
    services: &[Service],
) -> RuntimePlan {
    let selected = service_name_set(services);
    let mut planned = BTreeSet::new();
    let mut actions = Vec::new();

    for tier in BOOT_ORDER {
        if tier.contains(&MIGRATIONS_STEP) {
            if selected.contains("backend") {
                actions.push(migrations_action(&context.workspace));
            }
            continue;
        }

        for name in *tier {
            if !selected.contains(*name) {
                continue;
            }
            if let Some(service) = find_service(services, name) {
                actions.push(start_action(context, service));
                planned.insert(service.name.clone());
            }
        }
    }

    for service in services {
        if planned.insert(service.name.clone()) {
            actions.push(start_action(context, service));
        }
    }

    RuntimePlan {
        command: "dev",
        workspace: context.workspace.clone(),
        group: Some(group),
        actions,
    }
}

pub(crate) fn stop_plan(
    context: &RuntimeCommandContext,
    group: ServiceGroup,
    services: &[Service],
    force: bool,
) -> RuntimePlan {
    let selected = service_name_set(services);
    let mut planned = BTreeSet::new();
    let mut actions = Vec::new();

    for tier in BOOT_ORDER.iter().rev() {
        for name in tier.iter().rev() {
            if *name == MIGRATIONS_STEP || !selected.contains(*name) {
                continue;
            }
            if let Some(service) = find_service(services, name) {
                actions.push(stop_action(context, service, force));
                planned.insert(service.name.clone());
            }
        }
    }

    for service in services.iter().rev() {
        if planned.insert(service.name.clone()) {
            actions.push(stop_action(context, service, force));
        }
    }

    RuntimePlan {
        command: "stop",
        workspace: context.workspace.clone(),
        group: Some(group),
        actions,
    }
}

fn restart_plan(context: &RuntimeCommandContext, service: Service, force: bool) -> RuntimePlan {
    let mut actions = Vec::new();

    match service.service_type {
        ServiceType::Container => {
            actions.push(container_compose_action(
                context,
                &service,
                RuntimeActionKind::RestartContainer,
                &["restart"],
                "restart compose service",
            ));
        }
        ServiceType::Process => {
            actions.push(stop_process_action(&service, force));
            actions.push(start_process_action(&service));
        }
    }
    actions.push(probe_action(&service));

    RuntimePlan {
        command: "restart",
        workspace: context.workspace.clone(),
        group: None,
        actions,
    }
}

fn logs_plan(
    context: &RuntimeCommandContext,
    group: Option<ServiceGroup>,
    services: &[Service],
    lines: usize,
    follow: bool,
) -> RuntimePlan {
    let actions = services
        .iter()
        .map(|service| log_action(context, service, lines, follow))
        .collect();

    RuntimePlan {
        command: "logs",
        workspace: context.workspace.clone(),
        group,
        actions,
    }
}

fn start_action(context: &RuntimeCommandContext, service: &Service) -> RuntimeAction {
    match service.service_type {
        ServiceType::Container => container_compose_action(
            context,
            service,
            RuntimeActionKind::StartContainer,
            &["up", "-d"],
            "start compose service",
        ),
        ServiceType::Process => start_process_action(service),
    }
}

fn stop_action(context: &RuntimeCommandContext, service: &Service, force: bool) -> RuntimeAction {
    match service.service_type {
        ServiceType::Container => container_compose_action(
            context,
            service,
            RuntimeActionKind::StopContainer,
            &["stop"],
            "stop compose service",
        ),
        ServiceType::Process => stop_process_action(service, force),
    }
}

fn container_compose_action(
    context: &RuntimeCommandContext,
    service: &Service,
    kind: RuntimeActionKind,
    compose_args: &[&str],
    detail: &str,
) -> RuntimeAction {
    let mut command = vec![context.podman.display().to_string(), "compose".to_string()];
    for profile in &service.compose_profiles {
        command.push("--profile".to_string());
        command.push(profile.clone());
    }
    command.extend([
        "--file".to_string(),
        context.workspace.join("compose.yaml").display().to_string(),
    ]);
    command.extend(compose_args.iter().map(|arg| (*arg).to_string()));
    command.push(compose_target(service));

    RuntimeAction {
        service: service.name.clone(),
        label: service.label.clone(),
        kind,
        command,
        work_dir: None,
        detail: compose_profile_detail(service, detail),
    }
}

fn start_process_action(service: &Service) -> RuntimeAction {
    RuntimeAction {
        service: service.name.clone(),
        label: service.label.clone(),
        kind: RuntimeActionKind::StartProcess,
        command: service.cmd.clone(),
        work_dir: service.work_dir.clone(),
        detail: match &service.work_dir {
            Some(path) => format!("start process in {}", path.display()),
            None => "start process".to_string(),
        },
    }
}

fn stop_process_action(service: &Service, force: bool) -> RuntimeAction {
    RuntimeAction {
        service: service.name.clone(),
        label: service.label.clone(),
        kind: RuntimeActionKind::StopProcess,
        command: Vec::new(),
        work_dir: service.work_dir.clone(),
        detail: if force {
            "terminate tracked process with force".to_string()
        } else {
            "terminate tracked process gracefully".to_string()
        },
    }
}

fn migrations_action(workspace: &Path) -> RuntimeAction {
    RuntimeAction {
        service: MIGRATIONS_STEP.to_string(),
        label: "Database migrations".to_string(),
        kind: RuntimeActionKind::RunMigrations,
        command: vec![
            "uv".to_string(),
            "run".to_string(),
            "alembic".to_string(),
            "upgrade".to_string(),
            "head".to_string(),
        ],
        work_dir: Some(workspace.join("backend")),
        detail: "run backend database migrations before API startup".to_string(),
    }
}

fn probe_action(service: &Service) -> RuntimeAction {
    RuntimeAction {
        service: service.name.clone(),
        label: service.label.clone(),
        kind: RuntimeActionKind::Probe,
        command: Vec::new(),
        work_dir: None,
        detail: "wait for health probe to pass".to_string(),
    }
}

fn log_action(
    context: &RuntimeCommandContext,
    service: &Service,
    lines: usize,
    follow: bool,
) -> RuntimeAction {
    match service.service_type {
        ServiceType::Container => {
            let container = service
                .container_name
                .clone()
                .unwrap_or_else(|| service.name.clone());
            let mut command = vec![
                context.podman.display().to_string(),
                "logs".to_string(),
                "--tail".to_string(),
                lines.to_string(),
            ];
            if follow {
                command.push("--follow".to_string());
            }
            command.push(container.clone());

            RuntimeAction {
                service: service.name.clone(),
                label: service.label.clone(),
                kind: RuntimeActionKind::TailContainerLogs,
                command,
                work_dir: None,
                detail: format!("tail podman logs from {container}"),
            }
        }
        ServiceType::Process => {
            let path = context
                .workspace
                .join("logs")
                .join(format!("{}.log", service.name));
            let command = process_log_tail_command(&path, lines, follow);
            RuntimeAction {
                service: service.name.clone(),
                label: service.label.clone(),
                kind: RuntimeActionKind::TailFileLogs,
                command,
                work_dir: None,
                detail: format!(
                    "tail last {lines} lines from {}{}",
                    path.display(),
                    if follow { " and follow" } else { "" }
                ),
            }
        }
    }
}

fn process_log_tail_command(path: &Path, lines: usize, follow: bool) -> Vec<String> {
    if cfg!(windows) {
        let mut script = format!("Get-Content -Path '{}' -Tail {lines}", path.display());
        if follow {
            script.push_str(" -Wait");
        }
        return vec![
            "powershell".to_string(),
            "-NoProfile".to_string(),
            "-Command".to_string(),
            script,
        ];
    }

    let mut command = vec!["tail".to_string(), "-n".to_string(), lines.to_string()];
    if follow {
        command.push("-f".to_string());
    }
    command.push(path.display().to_string());
    command
}

fn render_plan_output(plan: &RuntimePlan, output: OutputFormat) -> anyhow::Result<CommandOutput> {
    match output {
        OutputFormat::Table => Ok(CommandOutput::new(format_plan_table(plan))),
        OutputFormat::Json => render_json_value(plan_json(plan)),
    }
}

fn render_probe_output(
    workspace: &Path,
    group: ServiceGroup,
    results: &[ProbeResult],
    output: OutputFormat,
) -> anyhow::Result<CommandOutput> {
    match output {
        OutputFormat::Table => Ok(CommandOutput::new(format_probe_results_table(results))),
        OutputFormat::Json => {
            let results = serde_json::to_value(results)?;
            render_json_value(json!({
                "workspace": workspace.display().to_string(),
                "group": service_group_name(group),
                "results": results,
            }))
        }
    }
}

fn render_json_value(value: serde_json::Value) -> anyhow::Result<CommandOutput> {
    Ok(CommandOutput::new(serde_json::to_string_pretty(&value)?))
}

fn plan_json(plan: &RuntimePlan) -> serde_json::Value {
    let actions: Vec<_> = plan
        .actions
        .iter()
        .map(|action| {
            json!({
                "service": action.service,
                "label": action.label,
                "kind": action.kind.as_str(),
                "command": action.command,
                "workDir": action.work_dir.as_ref().map(|path| path.display().to_string()),
                "detail": action.detail,
            })
        })
        .collect();

    json!({
        "command": plan.command,
        "workspace": plan.workspace.display().to_string(),
        "group": plan.group.map(service_group_name),
        "actions": actions,
    })
}

fn find_service<'a>(services: &'a [Service], name: &str) -> Option<&'a Service> {
    services.iter().find(|service| service.name == name)
}

fn unknown_service_error(name: &str, services: &[Service]) -> anyhow::Error {
    anyhow::anyhow!(
        "unknown service {name:?}; valid services: {}",
        services
            .iter()
            .map(|service| service.name.as_str())
            .collect::<Vec<_>>()
            .join(", ")
    )
}

fn service_name_set(services: &[Service]) -> BTreeSet<String> {
    services
        .iter()
        .map(|service| service.name.clone())
        .collect::<BTreeSet<_>>()
}

fn compose_target(service: &Service) -> String {
    service
        .compose_service
        .clone()
        .or_else(|| service.container_name.clone())
        .unwrap_or_else(|| service.name.clone())
}

fn compose_profile_detail(service: &Service, detail: &str) -> String {
    if service.compose_profiles.is_empty() {
        return detail.to_string();
    }

    format!(
        "{detail}; profiles: {}",
        service.compose_profiles.join(", ")
    )
}

fn service_target(service: &Service) -> String {
    service
        .compose_service
        .as_deref()
        .or(service.container_name.as_deref())
        .map(str::to_string)
        .or_else(|| {
            service
                .work_dir
                .as_ref()
                .map(|path| path.display().to_string())
        })
        .unwrap_or_else(|| "-".to_string())
}

fn format_port(port: Option<u16>) -> String {
    port.map(|port| port.to_string())
        .unwrap_or_else(|| "-".to_string())
}

fn shell_join(args: &[String]) -> String {
    args.iter()
        .map(|arg| {
            if arg.contains(char::is_whitespace) {
                format!("{arg:?}")
            } else {
                arg.clone()
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn context() -> RuntimeCommandContext {
        let workspace = PathBuf::from("C:/bijmantra");
        let podman = PathBuf::from("podman");
        let services = default_registry(&workspace, &podman);

        RuntimeCommandContext {
            workspace,
            podman,
            services,
        }
    }

    #[test]
    fn dev_plan_includes_migrations_before_backend() {
        let context = context();
        let services = context.selected_services(ServiceGroup::Core);
        let plan = dev_plan(&context, ServiceGroup::Core, &services);
        let positions = plan
            .actions
            .iter()
            .enumerate()
            .map(|(index, action)| (action.service.as_str(), index))
            .collect::<std::collections::BTreeMap<_, _>>();

        assert!(positions[MIGRATIONS_STEP] < positions["backend"]);
    }

    #[test]
    fn restart_plan_for_process_uses_stop_start_probe_sequence() {
        let context = context();
        let service = context.service("backend").unwrap();
        let plan = restart_plan(&context, service, false);
        let kinds = plan
            .actions
            .iter()
            .map(|action| action.kind)
            .collect::<Vec<_>>();

        assert_eq!(
            kinds,
            vec![
                RuntimeActionKind::StopProcess,
                RuntimeActionKind::StartProcess,
                RuntimeActionKind::Probe,
            ]
        );
    }

    #[test]
    fn format_plan_table_contains_command_and_services() {
        let context = context();
        let services = context.selected_services(ServiceGroup::Core);
        let plan = dev_plan(&context, ServiceGroup::Core, &services);
        let output = format_plan_table(&plan);

        assert!(output.contains("command: dev"));
        assert!(output.contains("postgres"));
        assert!(output.contains("backend"));
    }

    #[test]
    fn logs_plan_for_process_services_includes_runnable_tail_command() {
        let context = context();
        let services = context.selected_services(ServiceGroup::Core);
        let plan = logs_plan(&context, Some(ServiceGroup::Core), &services, 25, true);
        let backend = plan
            .actions
            .iter()
            .find(|action| action.service == "backend")
            .expect("backend log action should be present");

        assert_eq!(backend.kind, RuntimeActionKind::TailFileLogs);
        assert!(!backend.command.is_empty());
        assert!(
            backend
                .command
                .iter()
                .any(|part| part.contains("backend.log")),
            "backend log command should include the backend log path"
        );
        if cfg!(windows) {
            assert!(
                backend
                    .command
                    .iter()
                    .any(|part| part.contains("Get-Content"))
            );
            assert!(backend.command.iter().any(|part| part.contains("-Wait")));
        } else {
            assert_eq!(backend.command[0], "tail");
            assert!(backend.command.contains(&"-f".to_string()));
        }
    }

    #[test]
    fn grouped_no_follow_logs_emit_bounded_container_and_process_commands() {
        let context = context();
        let services = context.selected_services(ServiceGroup::Core);
        let plan = logs_plan(&context, Some(ServiceGroup::Core), &services, 10, false);
        let postgres = plan
            .actions
            .iter()
            .find(|action| action.service == "postgres")
            .expect("postgres log action should be present");
        let backend = plan
            .actions
            .iter()
            .find(|action| action.service == "backend")
            .expect("backend log action should be present");

        assert_eq!(plan.group, Some(ServiceGroup::Core));
        assert_eq!(postgres.kind, RuntimeActionKind::TailContainerLogs);
        assert!(postgres.command.contains(&"--tail".to_string()));
        assert!(postgres.command.contains(&"10".to_string()));
        assert!(!postgres.command.contains(&"--follow".to_string()));
        assert_eq!(backend.kind, RuntimeActionKind::TailFileLogs);
        if cfg!(windows) {
            assert!(!backend.command.iter().any(|part| part.contains("-Wait")));
        } else {
            assert!(!backend.command.contains(&"-f".to_string()));
        }
    }

    #[test]
    fn single_service_logs_json_omits_group_metadata() {
        let context = context();
        let service = context.service("backend").unwrap();
        let plan = logs_plan(&context, None, &[service], 20, false);
        let value = plan_json(&plan);

        assert!(value["group"].is_null());
        assert_eq!(value["actions"][0]["service"], "backend");
    }
}
