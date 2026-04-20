"""Track generated API spec changes against previous snapshot."""

from __future__ import annotations

import json
from pathlib import Path

from app.scripts.generate_api_docs import SPEC_SNAPSHOT_PATH, _extract_models, _extract_routes


ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = ROOT / "docs" / "api" / "API_CHANGELOG.md"


def main() -> int:
    previous = {}
    if SPEC_SNAPSHOT_PATH.exists():
        previous = json.loads(SPEC_SNAPSHOT_PATH.read_text(encoding="utf-8"))

    current = {"routes": _extract_routes(), "models": _extract_models()}

    old_paths = {(item["method"], item["path"]) for item in previous.get("routes", [])}
    new_paths = {(item["method"], item["path"]) for item in current.get("routes", [])}

    added = sorted(new_paths - old_paths)
    removed = sorted(old_paths - new_paths)

    lines = ["# API Change Tracker", ""]
    lines.append(f"Added operations: **{len(added)}**")
    lines.append(f"Removed operations: **{len(removed)}**")
    lines.append("")

    if added:
        lines.append("## Added")
        lines.extend(f"- `{method} {path}`" for method, path in added)
        lines.append("")
    if removed:
        lines.append("## Removed")
        lines.extend(f"- `{method} {path}`" for method, path in removed)
        lines.append("")

    SPEC_SNAPSHOT_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
