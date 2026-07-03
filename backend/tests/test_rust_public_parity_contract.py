"""Guard the read-only contracts shared with the Rust API."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app


CONTRACT_DIR = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "fastapi-parity"
)


def _json_path(payload: Any, path: str) -> Any | None:
    current = payload
    for segment in path.split("."):
        if isinstance(current, dict):
            current = current.get(segment)
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            current = current[index] if index < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current


def _load_routes() -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for name in ("public-readonly.json", "protected-readonly.json"):
        routes.extend(json.loads((CONTRACT_DIR / name).read_text())["routes"])
    return routes


@pytest.mark.parametrize("route", _load_routes())
def test_fastapi_readonly_contracts_for_rust_migration(route: dict[str, Any]) -> None:
    with TestClient(app) as client:
        response = client.request(route["method"], route["path"])

    assert response.status_code == route["status"]
    for name, expected in route.get("headers", {}).items():
        assert response.headers.get(name) == expected, name

    payload = response.json()

    for required in route.get("required", []):
        assert _json_path(payload, required) is not None, required

    for path, expected in route.get("exact", {}).items():
        assert _json_path(payload, path) == expected, path

    for path, expected_items in route.get("arrayContains", {}).items():
        actual = _json_path(payload, path)
        assert isinstance(actual, list), path
        for expected in expected_items:
            assert expected in actual, f"{path} missing {expected!r}"

    for forbidden in route.get("forbidden", []):
        assert _json_path(payload, forbidden) is None, forbidden
