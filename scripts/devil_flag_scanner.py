#!/usr/bin/env python3
"""Scan hot files for red/orange devil-file flags and surface warnings through hooks."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (ROOT / "backend" / "app", ROOT / "frontend" / "src")
SOURCE_SUFFIXES = {".py", ".ts", ".tsx"}
EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "vendor",
}

FILE_ORANGE_THRESHOLD = 1500
FILE_RED_THRESHOLD = 3000
PYTHON_UNIT_ORANGE_THRESHOLD = 600
PYTHON_UNIT_RED_THRESHOLD = 1200

HOOK_CONTEXT_PATHS = (
    ".github/copilot-instructions.md",
    ".github/instructions/anti-devil-file-growth.instructions.md",
)

PATCH_FILE_RE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File:\s+(.+?)\s*$", re.MULTILINE)
AGENT_INDEX_RE = re.compile(r"\b[A-Z0-9_]+_AGENT_INDEX\b")

VALID_HOOK_EVENTS = {
    "SessionStart",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PreCompact",
    "SubagentStart",
    "SubagentStop",
    "Stop",
}

READ_ONLY_TOOL_HINTS = (
    "await_terminal",
    "copilot_getnotebooksummary",
    "fetch",
    "file_search",
    "get_changed_files",
    "get_errors",
    "get_python_environment",
    "get_python_executable",
    "get_search_view_results",
    "get_task_output",
    "get_terminal_output",
    "grep",
    "kill_terminal",
    "list",
    "read",
    "resolve_memory_file_uri",
    "run_notebook_cell",
    "search",
    "semantic",
    "test_failure",
    "terminal_",
    "view",
    "wait",
)

WRITE_TOOL_HINTS = (
    "apply_patch",
    "create",
    "delete",
    "edit",
    "insert",
    "rename",
    "replace",
    "str_replace",
    "update",
    "write",
)

TOOL_PATH_KEYS = {
    "filepath",
    "filepaths",
    "resourcepath",
    "old_path",
    "new_path",
    "oldpath",
    "newpath",
}


def _is_source_file(path: Path) -> bool:
    return path.is_file() and path.suffix in SOURCE_SUFFIXES and not any(part in EXCLUDED_PARTS for part in path.parts)


def _is_in_scan_roots(path: Path) -> bool:
    return any(root in path.parents or path == root for root in SCAN_ROOTS)


def _safe_relative_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def _classify_file_kind(path: Path) -> str:
    relative = _safe_relative_path(path)
    if ".test." in path.name or "/tests/" in f"/{relative}/" or path.name.startswith("test_"):
        return "test"
    return "runtime"


def _detect_agent_index(text: str) -> bool:
    return bool(AGENT_INDEX_RE.search(text))


def _largest_python_unit(text: str) -> dict[str, Any] | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None

    best: dict[str, Any] | None = None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end_lineno = getattr(node, "end_lineno", node.lineno)
        span = max(end_lineno - node.lineno + 1, 1)
        candidate = {
            "name": node.name,
            "kind": node.__class__.__name__.replace("Def", "").lower(),
            "lines": span,
            "start_line": node.lineno,
            "end_line": end_lineno,
        }
        if best is None or candidate["lines"] > best["lines"]:
            best = candidate
    return best


def _determine_flag_level(line_count: int, largest_python_unit: dict[str, Any] | None) -> str | None:
    unit_lines = largest_python_unit["lines"] if largest_python_unit else 0
    if line_count >= FILE_RED_THRESHOLD or unit_lines >= PYTHON_UNIT_RED_THRESHOLD:
        return "red"
    if line_count >= FILE_ORANGE_THRESHOLD or unit_lines >= PYTHON_UNIT_ORANGE_THRESHOLD:
        return "orange"
    return None


def _flag_reasons(line_count: int, largest_python_unit: dict[str, Any] | None) -> list[str]:
    reasons: list[str] = []
    if line_count >= FILE_RED_THRESHOLD:
        reasons.append(f"file >= {FILE_RED_THRESHOLD} LOC")
    elif line_count >= FILE_ORANGE_THRESHOLD:
        reasons.append(f"file >= {FILE_ORANGE_THRESHOLD} LOC")

    if largest_python_unit:
        unit_threshold = PYTHON_UNIT_RED_THRESHOLD if largest_python_unit["lines"] >= PYTHON_UNIT_RED_THRESHOLD else PYTHON_UNIT_ORANGE_THRESHOLD
        if largest_python_unit["lines"] >= PYTHON_UNIT_ORANGE_THRESHOLD:
            reasons.append(
                f"largest python unit {largest_python_unit['name']} >= {unit_threshold} LOC"
            )
    return reasons


def _iter_scan_files(paths: list[Path] | None = None) -> list[Path]:
    if not paths:
        discovered: list[Path] = []
        for root in SCAN_ROOTS:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if _is_source_file(path):
                    discovered.append(path)
        return sorted(set(discovered))

    discovered = []
    for raw_path in paths:
        path = raw_path.resolve()
        if path.is_dir():
            for child in path.rglob("*"):
                if _is_source_file(child) and _is_in_scan_roots(child):
                    discovered.append(child)
            continue
        if _is_source_file(path) and _is_in_scan_roots(path):
            discovered.append(path)
    return sorted(set(discovered))


def _build_flag_record(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    line_count = _count_lines(text)
    largest_python_unit = _largest_python_unit(text) if path.suffix == ".py" else None
    flag_level = _determine_flag_level(line_count, largest_python_unit)
    if flag_level is None:
        return None

    return {
        "flag": flag_level,
        "path": _safe_relative_path(path),
        "absolute_path": path.as_posix(),
        "file_kind": _classify_file_kind(path),
        "line_count": line_count,
        "has_agent_index": _detect_agent_index(text),
        "largest_python_unit": largest_python_unit,
        "reasons": _flag_reasons(line_count, largest_python_unit),
    }


def _sort_key(record: dict[str, Any]) -> tuple[int, int, int, str]:
    severity_rank = 0 if record["flag"] == "red" else 1
    file_kind_rank = 0 if record["file_kind"] == "runtime" else 1
    return (severity_rank, file_kind_rank, -record["line_count"], record["path"])


def collect_flags(paths: list[Path] | None = None) -> list[dict[str, Any]]:
    records = []
    for path in _iter_scan_files(paths):
        record = _build_flag_record(path)
        if record is not None:
            records.append(record)
    return sorted(records, key=_sort_key)


def build_report(paths: list[Path] | None = None, max_results: int | None = None) -> dict[str, Any]:
    flags = collect_flags(paths)
    if max_results is not None:
        flags = flags[:max_results]

    red_count = sum(record["flag"] == "red" for record in flags)
    orange_count = sum(record["flag"] == "orange" for record in flags)
    return {
        "root": ROOT.as_posix(),
        "thresholds": {
            "file_orange": FILE_ORANGE_THRESHOLD,
            "file_red": FILE_RED_THRESHOLD,
            "python_unit_orange": PYTHON_UNIT_ORANGE_THRESHOLD,
            "python_unit_red": PYTHON_UNIT_RED_THRESHOLD,
        },
        "summary": {
            "red_count": red_count,
            "orange_count": orange_count,
            "total_count": len(flags),
        },
        "flags": flags,
    }


def _render_record(record: dict[str, Any]) -> str:
    details = [f"{record['line_count']} LOC"]
    if record["largest_python_unit"]:
        unit = record["largest_python_unit"]
        details.append(f"largest {unit['kind']} {unit['name']}={unit['lines']} LOC")
    if record["has_agent_index"]:
        details.append("indexed")
    return f"{record['flag'].upper():6} {record['path']} | " + " | ".join(details)


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "Devil File Flags",
        f"Red: {report['summary']['red_count']} | Orange: {report['summary']['orange_count']}",
        "",
    ]
    if not report["flags"]:
        lines.append("No red or orange flags detected.")
        return "\n".join(lines)

    for record in report["flags"]:
        lines.append(_render_record(record))
    return "\n".join(lines)


def _is_write_like_tool(payload: dict[str, Any]) -> bool:
    tool_name = str(payload.get("tool_name", "")).lower()
    if not tool_name:
        return False
    if any(hint in tool_name for hint in READ_ONLY_TOOL_HINTS):
        return False
    if any(hint in tool_name for hint in WRITE_TOOL_HINTS):
        return True

    tool_input = payload.get("tool_input")
    serialized = json.dumps(tool_input, sort_keys=True) if tool_input is not None else ""
    return bool(PATCH_FILE_RE.search(serialized))


def _resolve_path_string(raw_value: str) -> Path | None:
    candidate = raw_value.strip()
    if not candidate or any(token in candidate for token in ("*", "?", "[", "]")):
        return None
    path = Path(candidate)
    if not path.is_absolute():
        path = ROOT / candidate
    try:
        resolved = path.resolve()
    except OSError:
        return None
    return resolved if resolved.exists() else None


def _extract_paths_from_value(value: Any, *, key: str | None = None) -> set[Path]:
    discovered: set[Path] = set()

    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            discovered.update(_extract_paths_from_value(nested_value, key=nested_key.lower()))
        return discovered

    if isinstance(value, list):
        for item in value:
            discovered.update(_extract_paths_from_value(item, key=key))
        return discovered

    if not isinstance(value, str):
        return discovered

    if key in TOOL_PATH_KEYS:
        resolved = _resolve_path_string(value)
        if resolved is not None:
            discovered.add(resolved)

    for match in PATCH_FILE_RE.finditer(value):
        resolved = _resolve_path_string(match.group(1))
        if resolved is not None:
            discovered.add(resolved)

    return discovered


def _summarize_flags(flags: list[dict[str, Any]], *, limit: int) -> str:
    selected = flags[:limit]
    return "; ".join(
        f"{record['path']} ({record['line_count']} LOC{' , indexed' if record['has_agent_index'] else ''})".replace(" ,", ",")
        for record in selected
    )


def _session_start_output() -> dict[str, Any]:
    report = build_report(max_results=12)
    flags = report["flags"]
    red_flags = [record for record in flags if record["flag"] == "red"]
    orange_flags = [record for record in flags if record["flag"] == "orange"]
    if not red_flags and not orange_flags:
        return {}

    message_parts = []
    if red_flags:
        message_parts.append(f"red hotspots: {_summarize_flags(red_flags, limit=2)}")
    if orange_flags:
        message_parts.append(f"orange hotspots: {_summarize_flags(orange_flags, limit=3)}")

    return {
        "systemMessage": "Devil-file watch active: " + " | ".join(message_parts),
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "Anti-devil protocol active. Treat red and orange flagged files as extraction-first surfaces. "
                f"Policy paths: {', '.join(HOOK_CONTEXT_PATHS)}"
            ),
        },
    }


def _tool_hook_output(payload: dict[str, Any], *, event_name: str) -> dict[str, Any]:
    if not _is_write_like_tool(payload):
        return {}

    target_paths = sorted(_extract_paths_from_value(payload.get("tool_input", {})))
    if not target_paths:
        return {}

    flags = collect_flags(target_paths)
    if not flags:
        return {}

    red_flags = [record for record in flags if record["flag"] == "red"]
    orange_flags = [record for record in flags if record["flag"] == "orange"]
    if event_name == "PreToolUse":
        if red_flags:
            summary = _summarize_flags(red_flags, limit=2)
            return {
                "systemMessage": f"Red devil-file edit warning: {summary}. Prefer extraction-first and update the dated .ai/tasks handoff if the refactor is deferred.",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": "Red devil-file target requires explicit confirmation.",
                    "additionalContext": (
                        "Red devil-file edit detected. Follow the Anti-Devil File Protocol before deepening the file. "
                        f"Policy paths: {', '.join(HOOK_CONTEXT_PATHS)}"
                    ),
                },
            }
        if orange_flags:
            summary = _summarize_flags(orange_flags, limit=3)
            return {
                "systemMessage": f"Orange devil-file warning: {summary}. Keep the change local or extract first if the slice adds new non-local logic.",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": "Orange devil-file warning only.",
                    "additionalContext": (
                        "Orange devil-file edit detected. Prefer extraction-first if this is more than a small local fix. "
                        f"Policy paths: {', '.join(HOOK_CONTEXT_PATHS)}"
                    ),
                },
            }
        return {}

    summary_source = red_flags or orange_flags
    summary = _summarize_flags(summary_source, limit=3)
    flag_label = "Red" if red_flags else "Orange"
    return {
        "systemMessage": f"{flag_label} devil-file post-edit warning: {summary}. Reassess whether this file now needs an extraction or a dated .ai/tasks handoff.",
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "A write tool touched a flagged file. Re-check whether the edit stayed local enough for the Anti-Devil File Protocol. "
                f"Policy paths: {', '.join(HOOK_CONTEXT_PATHS)}"
            ),
        },
    }


def build_hook_output(payload: dict[str, Any]) -> dict[str, Any]:
    event_name = str(payload.get("hookEventName", ""))
    if event_name not in VALID_HOOK_EVENTS:
        return {}
    if event_name == "SessionStart":
        return _session_start_output()
    if event_name in {"PreToolUse", "PostToolUse"}:
        return _tool_hook_output(payload, event_name=event_name)
    return {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Optional file or directory paths to scan")
    parser.add_argument("--format", choices={"text", "json"}, default="text")
    parser.add_argument("--hook", action="store_true", help="Read hook input JSON from stdin and return hook JSON on stdout")
    parser.add_argument("--max-results", type=int, default=None)
    parser.add_argument("--fail-on-red", action="store_true", help="Exit non-zero when red flags are present")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.hook:
        payload = json.load(sys.stdin)
        json.dump(build_hook_output(payload), sys.stdout)
        sys.stdout.write("\n")
        return 0

    paths = [Path(raw_path) for raw_path in args.paths] if args.paths else None
    report = build_report(paths=paths, max_results=args.max_results)
    if args.format == "json":
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_text(report))

    if args.fail_on_red and report["summary"]["red_count"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())