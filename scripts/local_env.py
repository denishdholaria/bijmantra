from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = ROOT / ".env"


def _parse_env_value(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return ""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]

    parsed: list[str] = []
    in_single = False
    in_double = False
    previous = ""
    for character in value:
        if character == "'" and not in_double and previous != "\\":
            in_single = not in_single
        elif character == '"' and not in_single and previous != "\\":
            in_double = not in_double
        elif character == "#" and not in_single and not in_double:
            break

        parsed.append(character)
        previous = character

    return "".join(parsed).strip()


def load_local_env(
    *,
    keys: Iterable[str] | None = None,
    env_path: Path = DEFAULT_ENV_PATH,
    override: bool = False,
) -> dict[str, str]:
    if not env_path.exists():
        return {}

    selected_keys = set(keys) if keys is not None else None
    loaded: dict[str, str] = {}

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            continue

        key, raw_value = raw_line.split("=", 1)
        key = key.strip()
        if not key or (selected_keys is not None and key not in selected_keys):
            continue

        value = _parse_env_value(raw_value)
        if override or key not in os.environ:
            os.environ[key] = value
        loaded[key] = os.environ[key]

    return loaded