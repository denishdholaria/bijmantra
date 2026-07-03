pub mod config;
pub mod doctor;
pub mod orchestrator;
pub mod probes;
pub mod registry;
pub mod supervision;
pub mod workspace;

pub use config::{Config, ServiceOverride, load_config};
pub use doctor::{DoctorReport, RuntimeCheck, run_doctor};
pub use orchestrator::{
    CommandSpec, ComposeAction, ManagedProcess, OrchestrationError, ProcessCommandSpec,
    ProcessExit, build_compose_command, build_process_command, compose_target, process_log_path,
    restart_container, start_container, start_process, stop_container, stop_process,
};
pub use probes::{ProbeError, ProbeResult, probe_service, probe_services};
pub use registry::{
    Probe, Service, ServiceGroup, ServiceState, ServiceType, apply_config, default_registry,
    services_for_group,
};
pub use supervision::{
    ProcessRegistry, TrackedProcess, is_pid_running, process_registry_path, runtime_state_dir,
    terminate_pid,
};
pub use workspace::{detect_podman, resolve_workspace, verify_compose};
