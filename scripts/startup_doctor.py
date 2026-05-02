#!/usr/bin/env python3
"""Diagnose common local BijMantra startup issues without changing state."""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
REQUIRED_SERVICES = ("postgres",)
OPTIONAL_SERVICES = ("redis", "minio", "meilisearch")


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _icon(status: str) -> str:
    return {
        "PASS": "[PASS]",
        "WARN": "[WARN]",
        "FAIL": "[FAIL]",
        "SKIP": "[SKIP]",
    }.get(status, "[INFO]")


def print_result(result: CheckResult) -> None:
    print(f"{_icon(result.status)} {result.name}: {result.detail}")


def detect_container_runtime() -> str | None:
    candidates = [
        os.environ.get("CONTAINER_RUNTIME"),
        "/opt/podman/bin/podman",
        shutil.which("podman"),
        shutil.which("docker"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
        if candidate and shutil.which(candidate):
            return shutil.which(candidate)
    return None


def run_command(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def check_command(name: str, command: str) -> CheckResult:
    resolved = shutil.which(command)
    if resolved:
        return CheckResult(name, "PASS", f"Found at {resolved}")
    return CheckResult(name, "FAIL", f"Missing required command '{command}'")


def check_path(name: str, path: Path, suggestion: str) -> CheckResult:
    if path.exists():
        return CheckResult(name, "PASS", f"Found {path.relative_to(ROOT)}")
    return CheckResult(name, "FAIL", suggestion)


def inspect_running_services(runtime: str) -> tuple[set[str] | None, str | None]:
    result = run_command([runtime, "compose", "ps", "--services", "--status", "running"])
    if result.returncode == 0:
        running = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        return running, None

    fallback = run_command([runtime, "ps", "--format", "{{.Names}}"])
    if fallback.returncode != 0:
        stderr = fallback.stderr.strip() or result.stderr.strip() or result.stdout.strip() or "service status unavailable"
        return None, stderr

    running_containers = {line.strip() for line in fallback.stdout.splitlines() if line.strip()}
    inferred = set()
    for service in REQUIRED_SERVICES + OPTIONAL_SERVICES:
        if any(service in container_name for container_name in running_containers):
            inferred.add(service)
    return inferred, None


def check_compose_services(runtime: str | None) -> CheckResult:
    if not runtime:
        return CheckResult("Core infrastructure", "SKIP", "No container runtime found; service checks skipped")

    running, error = inspect_running_services(runtime)
    if running is None:
        return CheckResult("Core infrastructure", "WARN", f"Could not inspect running containers: {error}")

    missing = [service for service in REQUIRED_SERVICES if service not in running]
    if missing:
        return CheckResult(
            "Core infrastructure",
            "WARN",
            "Core database not running: " + ", ".join(missing) + ". Start with 'make dev' or 'bash ./start-bijmantra-app.sh'",
        )
    return CheckResult("Core infrastructure", "PASS", "postgres is running")


def check_optional_services(runtime: str | None) -> CheckResult:
    if not runtime:
        return CheckResult("Optional infrastructure", "SKIP", "No container runtime found; optional service checks skipped")

    running, error = inspect_running_services(runtime)
    if running is None:
        return CheckResult("Optional infrastructure", "SKIP", f"Optional service status unavailable: {error}")

    active = [service for service in OPTIONAL_SERVICES if service in running]
    inactive = [service for service in OPTIONAL_SERVICES if service not in running]
    if not active:
        return CheckResult(
            "Optional infrastructure",
            "PASS",
            "Redis, MinIO, and Meilisearch are off by default. Start only the ones your current feature needs.",
        )

    detail = "Running: " + ", ".join(active)
    if inactive:
        detail += ". Off by default: " + ", ".join(inactive)
    return CheckResult("Optional infrastructure", "PASS", detail)


def check_http(name: str, url: str) -> CheckResult:
    try:
        with urllib.request.urlopen(url, timeout=2):
            return CheckResult(name, "PASS", f"Reachable at {url}")
    except urllib.error.URLError as exc:
        return CheckResult(name, "WARN", f"Unavailable at {url}: {exc.reason}")
    except Exception as exc:  # pragma: no cover - defensive path
        return CheckResult(name, "WARN", f"Unavailable at {url}: {exc}")


def check_port(name: str, host: str, port: int, suggestion: str) -> CheckResult:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.5)
        try:
            sock.connect((host, port))
        except OSError:
            return CheckResult(name, "WARN", suggestion)
    return CheckResult(name, "PASS", f"Port {port} is accepting connections")


def check_runtime_preference(runtime: str | None) -> CheckResult:
    if not runtime:
        return CheckResult("Container runtime", "FAIL", "Neither Podman nor Docker was found")

    runtime_name = Path(runtime).name
    if runtime_name == "podman":
        return CheckResult("Container runtime", "PASS", f"Using Podman runtime at {runtime}")
    return CheckResult(
        "Container runtime",
        "WARN",
        f"Using {runtime_name} at {runtime}; BijMantra prefers Podman-oriented workflows",
    )


def run_doctor(strict: bool) -> int:
    runtime = detect_container_runtime()
    js_package_manager = os.environ.get("BIJMANTRA_JS_PACKAGE_MANAGER", "bun")

    results = [
        check_runtime_preference(runtime),
        check_command("Python", "python3"),
        check_command("Node.js", "node"),
        check_command("JavaScript package manager", js_package_manager),
        check_path("Backend virtualenv", BACKEND_DIR / "venv" / "bin" / "python", "Missing backend virtualenv; run 'bash ./setup.sh' or 'make install'"),
        check_path("Frontend dependencies", FRONTEND_DIR / "node_modules", "Missing frontend/node_modules; run 'cd frontend && bun install'"),
        check_compose_services(runtime),
        check_optional_services(runtime),
        check_http("Backend health", "http://localhost:8000/health"),
        check_port("Frontend dev server", "127.0.0.1", 5173, "Frontend not responding on 5173; run 'make dev-frontend' after dependencies are installed"),
    ]

    has_fail = False
    has_warn = False
    for result in results:
        print_result(result)
        has_fail = has_fail or result.status == "FAIL"
        has_warn = has_warn or result.status == "WARN"

    print()
    if has_fail:
        print("Next step: resolve the failing prerequisite or runtime issue above, then rerun 'make startup-doctor'.")
        print("If startup reaches the migration stage and fails there, run 'make migration-doctor'.")
    elif has_warn:
        print("Startup doctor completed with warnings. Inspect the services or URLs above if local startup is still blocked.")
    else:
        print("Startup doctor found no obvious local startup blockers.")

    if strict and has_fail:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose common local BijMantra startup issues.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when failing checks are found")
    args = parser.parse_args()
    return run_doctor(strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())