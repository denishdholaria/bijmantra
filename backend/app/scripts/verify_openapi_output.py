"""Sanity-check generated API spec coverage."""

from __future__ import annotations

import json
from pathlib import Path

from app.scripts.generate_api_docs import SPEC_SNAPSHOT_PATH


def main() -> int:
    if not SPEC_SNAPSHOT_PATH.exists():
        print("Snapshot missing. Run generate_api_docs first.")
        return 1

    spec = json.loads(SPEC_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    routes = spec.get("routes", [])
    brapi = [route for route in routes if route.get("path", "").startswith("/brapi/v2")]

    if len(routes) < 500:
        print(f"Insufficient route coverage: {len(routes)}")
        return 1
    if len(brapi) < 201:
        print(f"Insufficient BrAPI coverage: {len(brapi)}")
        return 1

    print(f"Spec coverage ok: total={len(routes)}, brapi={len(brapi)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
