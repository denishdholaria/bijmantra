mod ops_commands;
mod runtime_commands;

use std::env;
use std::net::{IpAddr, SocketAddr};
use std::path::{Path, PathBuf};
use std::time::Duration;

use anyhow::Context;
use bijmantra_core::{ApiMetrics, ProductManifest, api_stats, load_api_metrics};
use bijmantra_runtime::{
    DoctorReport, ProbeResult, Service, ServiceGroup, apply_config, default_registry,
    detect_podman, load_config, probe_services, resolve_workspace, run_doctor, services_for_group,
};
use bijmantra_server::{AppState, serve};
use clap::{Parser, Subcommand};
use tracing_subscriber::EnvFilter;

#[derive(Debug, Parser)]
#[command(name = "bij")]
#[command(about = "BijMantra product runtime")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Start the ordered BijMantra development stack.
    Dev {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long, default_value = "infra")]
        group: String,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        no_verify_compose: bool,
        #[arg(long)]
        skip_migrations: bool,
        #[arg(long)]
        no_wait: bool,
        #[arg(long)]
        no_rollback: bool,
        #[arg(long, default_value_t = 60)]
        wait_timeout_seconds: u64,
    },
    /// Stop the ordered BijMantra development stack.
    Stop {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long, default_value = "infra")]
        group: String,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        no_verify_compose: bool,
    },
    /// Run the Rust API server.
    Serve {
        #[arg(long, env = "BIJMANTRA_HOST", default_value = "127.0.0.1")]
        host: IpAddr,
        #[arg(long, env = "BIJMANTRA_PORT", default_value_t = 8000)]
        port: u16,
        #[arg(long, env = "BIJMANTRA_WORKSPACE", default_value = ".")]
        workspace: PathBuf,
    },
    /// Print the health response from a running API.
    Status {
        #[arg(long, default_value = "http://127.0.0.1:8000")]
        api: String,
    },
    /// Inspect local product metadata without starting services.
    Inspect {
        #[arg(long, env = "BIJMANTRA_WORKSPACE", default_value = ".")]
        workspace: PathBuf,
    },
    /// Run local runtime prerequisite checks.
    Doctor {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        json: bool,
    },
    /// Print the opt-in live Postgres BrAPI read test command.
    LiveTest {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        json: bool,
    },
    /// List known BijMantra runtime services.
    Services {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long, default_value = "autonomy")]
        group: String,
        #[arg(long)]
        json: bool,
    },
    /// Probe local runtime service health.
    Probe {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long, default_value = "core")]
        group: String,
        #[arg(long)]
        json: bool,
    },
    /// Print log tail commands for one service or a service group.
    Logs {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        service: Option<String>,
        #[arg(long, default_value = "autonomy")]
        group: String,
        #[arg(long)]
        json: bool,
        #[arg(long, default_value_t = 50)]
        lines: usize,
        #[arg(long)]
        no_follow: bool,
    },
    /// Plan runtime stack operations without executing them.
    Plan {
        #[command(subcommand)]
        command: PlanCommand,
    },
    /// Execute one runtime operation and persist local process state.
    Run {
        #[command(subcommand)]
        command: RunCommand,
    },
    /// Print the Rust product version.
    Version,
}

#[derive(Debug, Subcommand)]
enum PlanCommand {
    /// Plan the ordered startup sequence for a service group.
    Dev {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long, default_value = "infra")]
        group: String,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        verify_compose: bool,
    },
    /// Plan/probe runtime service status for a service group.
    Status {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long, default_value = "autonomy")]
        group: String,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        no_probe: bool,
    },
    /// Plan the ordered shutdown sequence for a service group.
    Stop {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long, default_value = "infra")]
        group: String,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        verify_compose: bool,
    },
    /// Plan restart actions for one known service.
    Restart {
        service: String,
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        verify_compose: bool,
    },
    /// Plan log commands for one service or a service group.
    Logs {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        service: Option<String>,
        #[arg(long, default_value = "autonomy")]
        group: String,
        #[arg(long)]
        json: bool,
        #[arg(long, default_value_t = 50)]
        lines: usize,
        #[arg(long)]
        no_follow: bool,
    },
}

#[derive(Debug, Subcommand)]
enum RunCommand {
    /// Start one known service.
    Start {
        service: String,
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        no_verify_compose: bool,
    },
    /// Stop one known service.
    Stop {
        service: String,
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        no_verify_compose: bool,
    },
    /// Restart one known service.
    Restart {
        service: String,
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        force: bool,
        #[arg(long)]
        no_verify_compose: bool,
    },
    /// List tracked local process state.
    Processes {
        #[arg(long, env = "BIJMANTRA_WORKSPACE")]
        workspace: Option<PathBuf>,
        #[arg(long)]
        json: bool,
        #[arg(long)]
        prune_stale: bool,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Command::Dev {
            workspace,
            group,
            json,
            no_verify_compose,
            skip_migrations,
            no_wait,
            no_rollback,
            wait_timeout_seconds,
        } => {
            let output_format = runtime_commands::OutputFormat::from_json(json);
            let result = ops_commands::handle_stack_dev(ops_commands::StackDevArgs {
                workspace,
                group: parse_group(&group)?,
                output: output_format,
                verify_compose: !no_verify_compose,
                skip_migrations,
                wait: !no_wait,
                wait_timeout: Duration::from_secs(wait_timeout_seconds),
                rollback: !no_rollback,
            })
            .await;
            match result {
                Ok(output) => {
                    print!("{output}");
                    Ok(())
                }
                Err(error) => {
                    if let Some(stack_error) =
                        error.downcast_ref::<ops_commands::StackStartupError>()
                    {
                        let output =
                            ops_commands::render_stack_failure(stack_error.event(), output_format)?;
                        print!("{output}");
                        std::process::exit(1);
                    }
                    Err(error)
                }
            }
        }
        Command::Stop {
            workspace,
            group,
            json,
            force,
            no_verify_compose,
        } => {
            let output = ops_commands::handle_stack_stop(ops_commands::StackStopArgs {
                workspace,
                group: parse_group(&group)?,
                output: runtime_commands::OutputFormat::from_json(json),
                force,
                verify_compose: !no_verify_compose,
            })
            .await?;
            print!("{output}");
            Ok(())
        }
        Command::Serve {
            host,
            port,
            workspace,
        } => {
            tracing_subscriber::fmt()
                .with_env_filter(
                    EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()),
                )
                .init();

            let workspace = workspace
                .canonicalize()
                .with_context(|| format!("failed to resolve workspace {}", workspace.display()))?;
            serve(SocketAddr::new(host, port), AppState::new(workspace)).await
        }
        Command::Status { api } => {
            let url = format!("{}/health", api.trim_end_matches('/'));
            let response = reqwest::get(&url)
                .await
                .with_context(|| format!("failed to call {url}"))?
                .error_for_status()
                .with_context(|| format!("{url} returned an error status"))?;
            let value: serde_json::Value = response.json().await?;
            println!("{}", serde_json::to_string_pretty(&value)?);
            Ok(())
        }
        Command::Inspect { workspace } => {
            let manifest = ProductManifest::current();
            let metrics_path = workspace.join("metrics.json");
            let metrics = load_api_metrics(metrics_path).unwrap_or_else(|_| ApiMetrics::default());
            let stats = api_stats(metrics);
            let value = serde_json::json!({
                "manifest": manifest,
                "stats": stats,
            });
            println!("{}", serde_json::to_string_pretty(&value)?);
            Ok(())
        }
        Command::Doctor { workspace, json } => {
            let report = run_doctor(workspace);
            if json {
                println!("{}", serde_json::to_string_pretty(&report)?);
            } else {
                print_doctor(&report);
            }
            Ok(())
        }
        Command::LiveTest { workspace, json } => {
            let plan = live_test_plan(workspace)?;
            if json {
                println!("{}", serde_json::to_string_pretty(&plan)?);
            } else {
                print_live_test_plan(&plan);
            }
            Ok(())
        }
        Command::Services {
            workspace,
            group,
            json,
        } => {
            let group = parse_group(&group)?;
            let (_, services) = load_services(workspace, group)?;
            if json {
                println!("{}", serde_json::to_string_pretty(&services)?);
            } else {
                print_services(&services);
            }
            Ok(())
        }
        Command::Probe {
            workspace,
            group,
            json,
        } => {
            let group = parse_group(&group)?;
            let (_, services) = load_services(workspace, group)?;
            let results = probe_services(&services).await;
            if json {
                println!("{}", serde_json::to_string_pretty(&results)?);
            } else {
                print_probe_results(&results);
            }
            Ok(())
        }
        Command::Logs {
            workspace,
            service,
            group,
            json,
            lines,
            no_follow,
        } => {
            let output = runtime_commands::handle_logs(runtime_commands::LogsArgs {
                workspace,
                service,
                group: parse_group(&group)?,
                output: runtime_commands::OutputFormat::from_json(json),
                lines,
                follow: !no_follow,
            })?;
            print!("{output}");
            Ok(())
        }
        Command::Plan { command } => run_plan_command(command).await,
        Command::Run { command } => run_operation_command(command).await,
        Command::Version => {
            println!("{}", bijmantra_core::product::APP_VERSION);
            Ok(())
        }
    }
}

async fn run_plan_command(command: PlanCommand) -> anyhow::Result<()> {
    let output = match command {
        PlanCommand::Dev {
            workspace,
            group,
            json,
            verify_compose,
        } => runtime_commands::handle_dev(runtime_commands::DevArgs {
            workspace,
            group: parse_group(&group)?,
            output: runtime_commands::OutputFormat::from_json(json),
            verify_compose,
        })?,
        PlanCommand::Status {
            workspace,
            group,
            json,
            no_probe,
        } => {
            runtime_commands::handle_status(runtime_commands::StatusArgs {
                workspace,
                group: parse_group(&group)?,
                output: runtime_commands::OutputFormat::from_json(json),
                probe: !no_probe,
            })
            .await?
        }
        PlanCommand::Stop {
            workspace,
            group,
            json,
            force,
            verify_compose,
        } => runtime_commands::handle_stop(runtime_commands::StopArgs {
            workspace,
            group: parse_group(&group)?,
            output: runtime_commands::OutputFormat::from_json(json),
            force,
            verify_compose,
        })?,
        PlanCommand::Restart {
            service,
            workspace,
            json,
            force,
            verify_compose,
        } => runtime_commands::handle_restart(runtime_commands::RestartArgs {
            workspace,
            service,
            output: runtime_commands::OutputFormat::from_json(json),
            force,
            verify_compose,
        })?,
        PlanCommand::Logs {
            workspace,
            service,
            group,
            json,
            lines,
            no_follow,
        } => runtime_commands::handle_logs(runtime_commands::LogsArgs {
            workspace,
            service,
            group: parse_group(&group)?,
            output: runtime_commands::OutputFormat::from_json(json),
            lines,
            follow: !no_follow,
        })?,
    };

    print!("{output}");
    Ok(())
}

async fn run_operation_command(command: RunCommand) -> anyhow::Result<()> {
    let output = match command {
        RunCommand::Start {
            service,
            workspace,
            json,
            no_verify_compose,
        } => {
            ops_commands::handle_start(ops_commands::StartArgs {
                workspace,
                service,
                output: runtime_commands::OutputFormat::from_json(json),
                verify_compose: !no_verify_compose,
            })
            .await?
        }
        RunCommand::Stop {
            service,
            workspace,
            json,
            force,
            no_verify_compose,
        } => {
            ops_commands::handle_stop(ops_commands::StopArgs {
                workspace,
                service,
                output: runtime_commands::OutputFormat::from_json(json),
                force,
                verify_compose: !no_verify_compose,
            })
            .await?
        }
        RunCommand::Restart {
            service,
            workspace,
            json,
            force,
            no_verify_compose,
        } => {
            ops_commands::handle_restart(ops_commands::RestartArgs {
                workspace,
                service,
                output: runtime_commands::OutputFormat::from_json(json),
                force,
                verify_compose: !no_verify_compose,
            })
            .await?
        }
        RunCommand::Processes {
            workspace,
            json,
            prune_stale,
        } => {
            ops_commands::handle_processes(ops_commands::ProcessesArgs {
                workspace,
                output: runtime_commands::OutputFormat::from_json(json),
                prune_stale,
            })
            .await?
        }
    };

    print!("{output}");
    Ok(())
}

fn parse_group(group: &str) -> anyhow::Result<ServiceGroup> {
    group.parse()
}

fn load_services(
    workspace: Option<PathBuf>,
    group: ServiceGroup,
) -> anyhow::Result<(PathBuf, Vec<Service>)> {
    let workspace = resolve_workspace(workspace)?;
    let config = load_config(&workspace)?;
    let podman = detect_podman(config.podman.as_deref())?;
    let mut services = default_registry(&workspace, &podman);
    apply_config(&mut services, &config);
    Ok((workspace, services_for_group(&services, group)))
}

const LIVE_TEST_ENV: &str = "BIJMANTRA_LIVE_DATABASE_URL";

fn live_test_command() -> Vec<&'static str> {
    vec![
        "cargo",
        "test",
        "-p",
        "bijmantra-server",
        "--test",
        "live_postgres_brapi",
        "--locked",
        "--",
        "--nocapture",
    ]
}

fn live_test_plan(workspace: Option<PathBuf>) -> anyhow::Result<serde_json::Value> {
    let workspace = resolve_workspace(workspace)?;
    let configured = env::var_os(LIVE_TEST_ENV)
        .and_then(|value| value.into_string().ok())
        .is_some_and(|value| !value.trim().is_empty());
    Ok(live_test_plan_for(&workspace, configured))
}

fn live_test_plan_for(workspace: &Path, configured: bool) -> serde_json::Value {
    serde_json::json!({
        "workspace": workspace.display().to_string(),
        "envVar": LIVE_TEST_ENV,
        "envConfigured": configured,
        "command": live_test_command(),
        "scope": "read-only live Postgres BrAPI route confidence",
        "note": "Set BIJMANTRA_LIVE_DATABASE_URL to a disposable migrated Postgres database before running the command. The helper does not execute the live suite.",
    })
}

fn print_live_test_plan(plan: &serde_json::Value) {
    println!("BijMantra Rust live Postgres read-test helper");
    println!(
        "workspace: {}",
        plan.get("workspace")
            .and_then(serde_json::Value::as_str)
            .unwrap_or("-")
    );
    println!(
        "env: {} ({})",
        LIVE_TEST_ENV,
        if plan
            .get("envConfigured")
            .and_then(serde_json::Value::as_bool)
            .unwrap_or(false)
        {
            "configured"
        } else {
            "not configured"
        }
    );
    let command = plan
        .get("command")
        .and_then(serde_json::Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(serde_json::Value::as_str)
                .collect::<Vec<_>>()
                .join(" ")
        })
        .unwrap_or_else(|| live_test_command().join(" "));
    println!("command: {command}");
    if let Some(note) = plan.get("note").and_then(serde_json::Value::as_str) {
        println!("note: {note}");
    }
}

fn print_doctor(report: &DoctorReport) {
    println!("BijMantra runtime doctor");
    if let Some(workspace) = &report.workspace {
        println!("workspace: {}", workspace.display());
    }
    if let Some(podman) = &report.podman {
        println!("podman: {}", podman.display());
    }
    println!("services: {}", report.services);
    println!();

    for check in &report.checks {
        let state = if check.ok { "ok" } else { "fail" };
        println!("{state:>4}  {:<18} {}", check.name, check.detail);
    }
}

fn print_services(services: &[Service]) {
    println!(
        "{:<20} {:<18} {:<10} {:<10} {:<8} target",
        "name", "label", "type", "group", "port"
    );
    for service in services {
        let target = service
            .compose_service
            .as_deref()
            .or(service.container_name.as_deref())
            .or(service.work_dir.as_ref().and_then(|path| path.to_str()))
            .unwrap_or("-");
        let port = service
            .port
            .map(|port| port.to_string())
            .unwrap_or_else(|| "-".to_string());
        println!(
            "{:<20} {:<18} {:<10?} {:<10?} {:<8} {}",
            service.name, service.label, service.service_type, service.group, port, target
        );
    }
}

fn print_probe_results(results: &[ProbeResult]) {
    println!(
        "{:<20} {:<18} {:<10} {:<10} detail",
        "name", "label", "state", "latency"
    );
    for result in results {
        println!(
            "{:<20} {:<18} {:<10?} {:>6}ms   {}",
            result.name,
            result.label,
            result.state,
            result.latency_ms,
            result.error.as_deref().unwrap_or("ok")
        );
    }
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::{LIVE_TEST_ENV, live_test_command, live_test_plan_for};

    #[test]
    fn live_test_command_targets_read_only_live_postgres_suite() {
        let command = live_test_command();

        assert_eq!(command[0], "cargo");
        assert_eq!(command[1], "test");
        assert!(
            command
                .windows(2)
                .any(|args| args == ["-p", "bijmantra-server"])
        );
        assert!(
            command
                .windows(2)
                .any(|args| args == ["--test", "live_postgres_brapi"])
        );
        assert!(command.contains(&"--locked"));
        assert!(command.contains(&"--nocapture"));
    }

    #[test]
    fn live_test_plan_is_opt_in_and_does_not_capture_database_url() {
        let plan = live_test_plan_for(Path::new("."), true);

        assert_eq!(plan["envVar"], LIVE_TEST_ENV);
        assert_eq!(plan["envConfigured"], true);
        assert_eq!(
            plan["scope"],
            "read-only live Postgres BrAPI route confidence"
        );
        assert!(
            plan["note"]
                .as_str()
                .expect("note should be a string")
                .contains("disposable migrated Postgres database")
        );
        assert!(plan.get("databaseUrl").is_none());
        assert!(plan.get("url").is_none());
    }
}
