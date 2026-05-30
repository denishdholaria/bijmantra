"""Artifact integrity helpers for Plant Vision models."""

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def build_artifact_manifest(artifact_dir: Path) -> dict:
    files = {}
    for path in sorted(artifact_dir.glob("*")):
        if path.is_file() and path.name != "artifact_manifest.json":
            files[path.name] = {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }

    digest = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "artifact_checksum": f"sha256:{digest}",
        "files": files,
    }


def write_artifact_manifest(artifact_dir: Path) -> dict:
    manifest = build_artifact_manifest(artifact_dir)
    (artifact_dir / "artifact_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def load_artifact_manifest(artifact_dir: Path) -> dict | None:
    manifest_path = artifact_dir / "artifact_manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_artifact_checksum(artifact_dir: Path, expected_checksum: str | None) -> bool:
    if not expected_checksum:
        return False
    manifest = load_artifact_manifest(artifact_dir)
    if not manifest:
        return False
    current = build_artifact_manifest(artifact_dir)
    return (
        manifest.get("artifact_checksum") == expected_checksum
        and current.get("artifact_checksum") == expected_checksum
    )
