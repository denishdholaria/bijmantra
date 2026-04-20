#!/usr/bin/env python3
"""Update metrics.json from repo-grounded project state."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).parent.parent.absolute()
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_DIR = ROOT_DIR / "backend"

METRICS_FILE = ROOT_DIR / "metrics.json"
OFFICIAL_BRAPI_V21_PUBLISHED_ENDPOINTS = 201
SAFE_JSON_ENV_DEFAULTS = {
    "BACKEND_CORS_ORIGINS": '["http://localhost:5173", "http://localhost:3000"]',
    "ALLOWED_IMAGE_TYPES": '["image/jpeg", "image/png", "image/webp"]',
    "TRUSTED_PROXIES": "[]",
}
OPENAPI_COUNT_SCRIPT = """
import json

from app.main import app

http_methods = {"get", "post", "put", "delete", "patch", "options", "head", "trace"}
schema = app.openapi()
total_endpoints = 0
brapi_endpoints = 0
for path, path_item in schema.get("paths", {}).items():
    if not isinstance(path_item, dict):
        continue
    for method, operation in path_item.items():
        if method.lower() not in http_methods or not isinstance(operation, dict):
            continue
        total_endpoints += 1
        if path.startswith("/brapi/v2"):
            brapi_endpoints += 1

print(json.dumps({
    "totalEndpoints": total_endpoints,
    "brapiExposedEndpoints": brapi_endpoints,
}))
""".strip()


def count_pages():
    pages_dir = FRONTEND_DIR / "src" / "pages"
    if not pages_dir.exists():
        return 0, 0, 0

    total_pages = 0
    demo_pages = 0
    for root, _, files in os.walk(pages_dir):
        for file_name in files:
            if not file_name.endswith((".tsx", ".jsx")):
                continue
            total_pages += 1
            file_path = Path(root) / file_name
            try:
                content = file_path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "DEMO_" in content or "mock" in content.lower():
                demo_pages += 1
    return total_pages, total_pages - demo_pages, demo_pages


def get_bundle_size():
    dist_dir = FRONTEND_DIR / "dist"
    if not dist_dir.exists():
        return 0, "0.0MB"

    total_size = sum(file.stat().st_size for file in dist_dir.glob("**/*") if file.is_file())
    return int(total_size / 1024), f"{total_size / (1024 * 1024):.1f}MB"


def _with_safe_json_settings(env: dict[str, str]) -> dict[str, str]:
    normalized_env = dict(env)
    for key, default_value in SAFE_JSON_ENV_DEFAULTS.items():
        raw_value = normalized_env.get(key)
        if raw_value is None:
            normalized_env[key] = default_value
            continue
        try:
            parsed_value = json.loads(raw_value)
        except json.JSONDecodeError:
            normalized_env[key] = default_value
            continue
        if not isinstance(parsed_value, list):
            normalized_env[key] = default_value
    return normalized_env


def _candidate_backend_interpreters() -> list[Path]:
    candidates = [
        BACKEND_DIR / "venv" / "bin" / "python3.13",
        BACKEND_DIR / "venv" / "bin" / "python3",
        BACKEND_DIR / "venv" / "bin" / "python",
        BACKEND_DIR / ".venv" / "bin" / "python3.13",
        BACKEND_DIR / ".venv" / "bin" / "python3",
        BACKEND_DIR / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str in seen:
            continue
        seen.add(candidate_str)
        if candidate.exists():
            unique_candidates.append(candidate)
    return unique_candidates


def count_endpoints_from_openapi() -> dict[str, int] | None:
    env = _with_safe_json_settings(os.environ)
    env["PYTHONPATH"] = str(BACKEND_DIR)

    for interpreter in _candidate_backend_interpreters():
        result = subprocess.run(
            [str(interpreter), "-c", OPENAPI_COUNT_SCRIPT],
            cwd=BACKEND_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        stdout_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not stdout_lines:
            continue
        try:
            payload = json.loads(stdout_lines[-1])
        except json.JSONDecodeError:
            continue
        total_endpoints = payload.get("totalEndpoints")
        brapi_exposed_endpoints = payload.get("brapiExposedEndpoints")
        if not isinstance(total_endpoints, int) or not isinstance(brapi_exposed_endpoints, int):
            continue
        return {
            "totalEndpoints": total_endpoints,
            "brapiExposedEndpoints": brapi_exposed_endpoints,
        }

    return None


def main():
    print("Gathering metrics data...")

    total_pages, functional_pages, demo_pages = count_pages()
    endpoint_counts = count_endpoints_from_openapi()
    bundle_kb, bundle_mb = get_bundle_size()

    old_metrics: dict = {}
    if METRICS_FILE.exists():
        with METRICS_FILE.open(encoding="utf-8") as metrics_file:
            loaded = json.load(metrics_file)
            if isinstance(loaded, dict):
                old_metrics = loaded

    def get_dict(data: dict, key: str) -> dict:
        value = data.get(key, {})
        return value if isinstance(value, dict) else {}

    old_api_metrics = get_dict(old_metrics, "api")
    total_endpoints = (
        endpoint_counts["totalEndpoints"]
        if endpoint_counts is not None
        else old_api_metrics.get("totalEndpoints", 0)
    )
    brapi_exposed_endpoints = (
        endpoint_counts["brapiExposedEndpoints"]
        if endpoint_counts is not None
        else old_api_metrics.get(
            "brapiExposedEndpoints",
            old_api_metrics.get("brapiEndpoints", 0),
        )
    )
    brapi_coverage = (
        min(
            100,
            int(
                (
                    min(brapi_exposed_endpoints, OFFICIAL_BRAPI_V21_PUBLISHED_ENDPOINTS)
                    / OFFICIAL_BRAPI_V21_PUBLISHED_ENDPOINTS
                )
                * 100
            ),
        )
        if brapi_exposed_endpoints > 0
        else old_api_metrics.get("brapiCoverage", 0)
    )
    custom_endpoints = (
        max(total_endpoints - brapi_exposed_endpoints, 0)
        if total_endpoints > 0
        else old_api_metrics.get("customEndpoints", 0)
    )

    metrics = {
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "updatedBy": "Automated metrics script (OpenAPI-derived API counts)",
        "session": old_metrics.get("session", 0),
        "pages": {
            "total": total_pages if total_pages > 0 else get_dict(old_metrics, "pages").get("total", 0),
            "functional": functional_pages if total_pages > 0 else get_dict(old_metrics, "pages").get("functional", 0),
            "demo": demo_pages,
            "uiOnly": get_dict(old_metrics, "pages").get("uiOnly", 0),
            "removed": get_dict(old_metrics, "pages").get("removed", 0),
        },
        "api": {
            "totalEndpoints": total_endpoints,
            "brapiEndpoints": brapi_exposed_endpoints,
            "brapiPublishedEndpoints": OFFICIAL_BRAPI_V21_PUBLISHED_ENDPOINTS,
            "brapiExposedEndpoints": brapi_exposed_endpoints,
            "brapiCoverage": brapi_coverage,
            "customEndpoints": custom_endpoints,
        },
        "database": old_metrics.get("database", {}),
        "modules": old_metrics.get("modules", {}),
        "workspaces": old_metrics.get("workspaces", {}),
        "build": {
            "status": get_dict(old_metrics, "build").get("status", "passing"),
            "pwaEntries": get_dict(old_metrics, "build").get("pwaEntries", 0),
            "sizeKB": bundle_kb if bundle_kb > 0 else get_dict(old_metrics, "build").get("sizeKB", 0),
            "sizeMB": bundle_mb if bundle_kb > 0 else get_dict(old_metrics, "build").get("sizeMB", "0MB"),
        },
        "milestones": old_metrics.get("milestones", {}),
        "techStack": old_metrics.get("techStack", {}),
        "version": old_metrics.get("version", {"app": "0.2.0", "brapi": "2.1", "schema": "1.0.0"}),
        "tests": old_metrics.get("tests", {}),
    }

    with METRICS_FILE.open("w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, indent=2)
    print(f"Updated {METRICS_FILE}")


if __name__ == "__main__":
    main()
