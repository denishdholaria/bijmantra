use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Stdio;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::process::Command;

const REGISTRY_VERSION: u16 = 1;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TrackedProcess {
    pub service_name: String,
    pub pid: u32,
    pub log_path: PathBuf,
    pub command: Vec<String>,
    pub work_dir: Option<PathBuf>,
    pub started_at: DateTime<Utc>,
}

impl TrackedProcess {
    pub fn new(
        service_name: impl Into<String>,
        pid: u32,
        log_path: PathBuf,
        command: Vec<String>,
        work_dir: Option<PathBuf>,
    ) -> Self {
        Self {
            service_name: service_name.into(),
            pid,
            log_path,
            command,
            work_dir,
            started_at: Utc::now(),
        }
    }
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProcessRegistry {
    pub version: u16,
    #[serde(default)]
    pub processes: BTreeMap<String, TrackedProcess>,
}

impl ProcessRegistry {
    pub fn empty() -> Self {
        Self {
            version: REGISTRY_VERSION,
            processes: BTreeMap::new(),
        }
    }

    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let Ok(raw) = fs::read_to_string(path) else {
            return Ok(Self::empty());
        };
        let mut registry: Self = serde_json::from_str(&raw).map_err(|error| {
            anyhow::anyhow!("load process registry {}: {error}", path.display())
        })?;
        if registry.version == 0 {
            registry.version = REGISTRY_VERSION;
        }
        Ok(registry)
    }

    pub fn save(&self, path: &Path) -> anyhow::Result<()> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)?;
        }

        let tmp_path = path.with_extension("json.tmp");
        let raw = serde_json::to_string_pretty(self)?;
        fs::write(&tmp_path, raw)?;

        if path.exists() {
            fs::remove_file(path)?;
        }
        fs::rename(&tmp_path, path)?;
        Ok(())
    }

    pub fn upsert(&mut self, process: TrackedProcess) {
        self.processes.insert(process.service_name.clone(), process);
    }

    pub fn remove(&mut self, service_name: &str) -> Option<TrackedProcess> {
        self.processes.remove(service_name)
    }

    pub fn get(&self, service_name: &str) -> Option<&TrackedProcess> {
        self.processes.get(service_name)
    }

    pub fn list(&self) -> impl Iterator<Item = &TrackedProcess> {
        self.processes.values()
    }

    pub fn is_empty(&self) -> bool {
        self.processes.is_empty()
    }
}

pub fn runtime_state_dir(workspace: &Path) -> PathBuf {
    workspace.join(".bijmantra").join("runtime")
}

pub fn process_registry_path(workspace: &Path) -> PathBuf {
    runtime_state_dir(workspace).join("processes.json")
}

pub async fn is_pid_running(pid: u32) -> anyhow::Result<bool> {
    if pid == 0 {
        return Ok(false);
    }
    is_pid_running_impl(pid).await
}

pub async fn terminate_pid(pid: u32, force: bool) -> anyhow::Result<()> {
    if pid == 0 {
        anyhow::bail!("refusing to terminate pid 0");
    }
    terminate_pid_impl(pid, force).await
}

#[cfg(windows)]
async fn is_pid_running_impl(pid: u32) -> anyhow::Result<bool> {
    let pid_text = pid.to_string();
    let filter = format!("PID eq {pid_text}");
    let output = Command::new("tasklist")
        .args(["/FI", filter.as_str(), "/FO", "CSV", "/NH"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await?;

    if !output.status.success() {
        anyhow::bail!("{}", command_output_message(&output));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.lines().any(|line| {
        line.split(',')
            .nth(1)
            .map(|field| field.trim().trim_matches('"') == pid_text)
            .unwrap_or(false)
    }))
}

#[cfg(not(windows))]
async fn is_pid_running_impl(pid: u32) -> anyhow::Result<bool> {
    let output = Command::new("kill")
        .arg("-0")
        .arg(pid.to_string())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await?;

    Ok(output.status.success())
}

#[cfg(windows)]
async fn terminate_pid_impl(pid: u32, force: bool) -> anyhow::Result<()> {
    let pid_text = pid.to_string();
    let mut args = vec!["/PID", pid_text.as_str(), "/T"];
    if force {
        args.push("/F");
    }
    let output = Command::new("taskkill")
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await?;

    if output.status.success() {
        Ok(())
    } else {
        anyhow::bail!("{}", command_output_message(&output))
    }
}

#[cfg(not(windows))]
async fn terminate_pid_impl(pid: u32, force: bool) -> anyhow::Result<()> {
    let signal = if force { "-KILL" } else { "-TERM" };
    let output = Command::new("kill")
        .arg(signal)
        .arg(pid.to_string())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .await?;

    if output.status.success() {
        Ok(())
    } else {
        anyhow::bail!("{}", command_output_message(&output))
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn registry_round_trips_process_records() {
        let root = unique_temp_dir("registry-round-trip");
        let path = root
            .join(".bijmantra")
            .join("runtime")
            .join("processes.json");
        let mut registry = ProcessRegistry::empty();
        registry.upsert(TrackedProcess::new(
            "backend",
            42,
            PathBuf::from("logs/backend.log"),
            vec!["uv".to_string(), "run".to_string()],
            Some(PathBuf::from("backend")),
        ));

        registry.save(&path).unwrap();
        let loaded = ProcessRegistry::load(&path).unwrap();

        let backend = loaded.get("backend").unwrap();
        assert_eq!(backend.pid, 42);
        assert_eq!(backend.command, vec!["uv", "run"]);

        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn missing_registry_loads_as_empty() {
        let root = unique_temp_dir("missing-registry");
        let path = root.join("missing.json");

        let registry = ProcessRegistry::load(&path).unwrap();

        assert!(registry.is_empty());
        assert_eq!(registry.version, REGISTRY_VERSION);

        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn registry_path_lives_under_runtime_state_dir() {
        let workspace = Path::new("C:/bijmantra");

        assert_eq!(
            process_registry_path(workspace),
            PathBuf::from("C:/bijmantra/.bijmantra/runtime/processes.json")
        );
    }

    fn unique_temp_dir(name: &str) -> PathBuf {
        let root = std::env::temp_dir().join(format!("bijmantra-{name}-{}", std::process::id()));
        if root.exists() {
            fs::remove_dir_all(&root).unwrap();
        }
        fs::create_dir_all(&root).unwrap();
        root
    }
}
