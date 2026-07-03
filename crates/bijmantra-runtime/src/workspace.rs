use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;

pub fn resolve_workspace(override_path: Option<PathBuf>) -> anyhow::Result<PathBuf> {
    if let Some(path) = override_path {
        return resolve_override(path);
    }

    let mut dir = env::current_dir()?.canonicalize()?;
    loop {
        if has_compose_file(&dir) {
            return Ok(dir);
        }
        if !dir.pop() {
            break;
        }
    }

    anyhow::bail!("resolve workspace: compose.yaml not found from current directory upward")
}

pub fn detect_podman(configured: Option<&str>) -> anyhow::Result<PathBuf> {
    if let Some(candidate) = configured
        && let Some(path) = resolve_executable(candidate)
    {
        return Ok(path);
    }
    if let Ok(candidate) = env::var("CONTAINER_RUNTIME")
        && let Some(path) = resolve_executable(&candidate)
    {
        return Ok(path);
    }

    #[cfg(unix)]
    {
        let default_path = PathBuf::from("/opt/podman/bin/podman");
        if default_path.is_file() {
            return Ok(default_path);
        }
    }

    for candidate in ["podman", "podman.exe"] {
        if let Some(path) = resolve_executable(candidate) {
            return Ok(path);
        }
    }

    anyhow::bail!("podman not found; install Podman from https://podman.io")
}

pub fn verify_compose(podman: &Path) -> anyhow::Result<()> {
    let output = Command::new(podman).args(["compose", "version"]).output()?;
    if output.status.success() {
        return Ok(());
    }

    let message = String::from_utf8_lossy(&output.stderr).trim().to_string();
    if message.is_empty() {
        anyhow::bail!("podman compose version exited with {}", output.status);
    }
    anyhow::bail!("podman compose version: {message}");
}

fn resolve_override(path: PathBuf) -> anyhow::Result<PathBuf> {
    let root = path.canonicalize()?;
    if !root.is_dir() {
        anyhow::bail!(
            "resolve workspace override {}: not a directory",
            root.display()
        );
    }
    if !has_compose_file(&root) {
        anyhow::bail!(
            "resolve workspace override {}: compose.yaml not found",
            root.display()
        );
    }
    Ok(root)
}

fn has_compose_file(dir: &Path) -> bool {
    dir.join("compose.yaml").is_file()
}

fn resolve_executable(candidate: &str) -> Option<PathBuf> {
    let candidate_path = PathBuf::from(candidate);
    if candidate_path.is_absolute() || candidate.contains(std::path::MAIN_SEPARATOR) {
        return candidate_path
            .canonicalize()
            .ok()
            .filter(|path| path.is_file());
    }

    let paths = env::var_os("PATH")?;
    env::split_paths(&paths)
        .flat_map(|path| executable_candidates(&path, candidate))
        .find(|path| path.is_file())
}

fn executable_candidates(path: &Path, candidate: &str) -> Vec<PathBuf> {
    let direct = path.join(candidate);
    if cfg!(windows) && !candidate.ends_with(".exe") {
        vec![direct, path.join(format!("{candidate}.exe"))]
    } else {
        vec![direct]
    }
}
