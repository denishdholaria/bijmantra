#!/usr/bin/env python3
"""Export a repo-grounded current-state JSON for visualization tools.

This exporter is intentionally lightweight. It turns the most useful current
repository signals into one nested JSON document that can be loaded directly
into JSON Crack or other browser-based graph viewers.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "metrics.json"
TASKS_DIR = ROOT / ".ai" / "tasks"
DECISIONS_DIR = ROOT / ".ai" / "decisions"
AGENTS_DIR = ROOT / ".github" / "agents"
AGENT_JOBS_DIR = ROOT / ".agent" / "jobs"
ATLAS_DIR = ROOT / "docs-private" / "architecture" / "atlas"
AREA_BOARDS_DIR = ROOT / "docs-private" / "architecture" / "area-boards"
OUTPUT_PATH = ROOT / "docs-private" / "architecture" / "tracking" / "current-app-state.json"
OVERNIGHT_QUEUE_PATH = AGENT_JOBS_DIR / "overnight-queue.json"
OVERNIGHT_PLAN_PATH = ROOT / "docs-private" / "architecture" / "tracking" / "overnight-dispatch-plan.json"
TASK_TEMPLATE_PATH = TASKS_DIR / "TEMPLATE.md"

STATUS_RE = re.compile(r"\*\*Status:\*\*\s*([^\n]+)")
TITLE_RE = re.compile(r"#\s+Task:\s+([^\n]+)")
DECISION_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*([^\n]+)")
DECISION_TITLE_RE = re.compile(r"#\s+ADR-[^:]+:\s+([^\n]+)")


def load_metrics() -> dict:
    if not METRICS_PATH.exists():
        return {}
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


def git_info() -> dict:
    def run_git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception:
            return None
        return result.stdout.strip()

    branch = run_git("branch", "--show-current")
    commit = run_git("rev-parse", "--short", "HEAD")
    status_output = run_git("status", "--short") or ""
    changed_files = [line for line in status_output.splitlines() if line.strip()]
    return {
        "branch": branch,
        "commit": commit,
        "changedFileCount": len(changed_files),
        "changedFilesPreview": changed_files[:20],
    }


def parse_task_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    title_match = TITLE_RE.search(text)
    status_match = STATUS_RE.search(text)
    if title_match is None or status_match is None:
        return None
    return {
        "title": title_match.group(1).strip(),
        "status": status_match.group(1).strip(),
        "path": str(path.relative_to(ROOT)),
    }


def task_summary() -> dict:
    task_paths = [path for path in sorted(TASKS_DIR.glob("*.md")) if path != TASK_TEMPLATE_PATH]
    tasks = [item for item in (parse_task_file(path) for path in task_paths) if item]
    status_counts = Counter(task["status"] for task in tasks)
    active = [task for task in tasks if task["status"] in {"IN_PROGRESS", "TODO", "BLOCKED"}]
    return {
        "total": len(tasks),
        "statusCounts": dict(sorted(status_counts.items())),
        "active": active[:12],
    }


def parse_decision_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    title_match = DECISION_TITLE_RE.search(text)
    status_match = DECISION_STATUS_RE.search(text)
    if title_match is None or status_match is None:
        return None
    return {
        "title": title_match.group(1).strip(),
        "status": status_match.group(1).strip(),
        "path": str(path.relative_to(ROOT)),
    }


def decision_summary() -> dict:
    decisions = [
        item for item in (parse_decision_file(path) for path in sorted(DECISIONS_DIR.glob("ADR-*.md"))) if item
    ]
    status_counts = Counter(decision["status"] for decision in decisions)
    return {
        "total": len(decisions),
        "statusCounts": dict(sorted(status_counts.items())),
        "recent": decisions[-8:],
    }


def agent_summary() -> dict:
    agent_files = sorted(path.name for path in AGENTS_DIR.glob("*.agent.md"))
    return {
        "count": len(agent_files),
        "files": agent_files,
        "projectManagementTemplate": str(
            (AGENTS_DIR / "2026-03-15-om-shri-maatre-daily-project-management-template.md").relative_to(ROOT)
        ),
    }


def atlas_summary() -> dict:
    atlas_files = sorted(path.name for path in ATLAS_DIR.glob("*")) if ATLAS_DIR.exists() else []
    board_files = sorted(path.name for path in AREA_BOARDS_DIR.glob("*.md")) if AREA_BOARDS_DIR.exists() else []
    return {
        "atlasDir": str(ATLAS_DIR.relative_to(ROOT)),
        "areaBoardsDir": str(AREA_BOARDS_DIR.relative_to(ROOT)),
        "atlasFileCount": len(atlas_files),
        "boardCount": len(board_files),
        "boards": board_files,
    }


def overnight_queue_summary() -> dict:
    if not OVERNIGHT_QUEUE_PATH.exists():
        return {
            "queuePath": str(OVERNIGHT_QUEUE_PATH.relative_to(ROOT)),
            "dispatchPlanPath": str(OVERNIGHT_PLAN_PATH.relative_to(ROOT)),
            "present": False,
        }

    queue = json.loads(OVERNIGHT_QUEUE_PATH.read_text(encoding="utf-8"))
    jobs = queue.get("jobs", [])
    status_counts = Counter(job.get("status", "UNKNOWN") for job in jobs)
    priorities = Counter(job.get("priority", "UNKNOWN") for job in jobs)
    dispatch_plan = {}
    if OVERNIGHT_PLAN_PATH.exists():
        dispatch_plan = json.loads(OVERNIGHT_PLAN_PATH.read_text(encoding="utf-8"))

    return {
        "queuePath": str(OVERNIGHT_QUEUE_PATH.relative_to(ROOT)),
        "dispatchPlanPath": str(OVERNIGHT_PLAN_PATH.relative_to(ROOT)),
        "present": True,
        "total": len(jobs),
        "statusCounts": dict(sorted(status_counts.items())),
        "priorityCounts": dict(sorted(priorities.items())),
        "jobs": [
            {
                "jobId": job.get("jobId"),
                "title": job.get("title"),
                "status": job.get("status"),
                "priority": job.get("priority"),
                "primaryAgent": job.get("primaryAgent"),
                "executionMode": job.get("executionMode"),
            }
            for job in jobs[:12]
        ],
        "latestPlan": {
            "generatedAt": dispatch_plan.get("generatedAt"),
            "window": dispatch_plan.get("window"),
            "selectedJobCount": dispatch_plan.get("selectedJobCount", 0),
            "blockedJobCount": dispatch_plan.get("blockedJobCount", 0),
            "selectedJobIds": [job.get("jobId") for job in dispatch_plan.get("selectedJobs", [])],
        },
    }


def build_state() -> dict:
    metrics = load_metrics()
    return {
        "application": {
            "name": "BijMantra",
            "generatedAt": datetime.now(UTC).isoformat(),
            "repoRoot": str(ROOT),
            "visualization": {
                "primaryTool": "JSON Crack browser app",
                "recommendedUrl": "http://localhost:3101/editor",
                "generatedInput": str(OUTPUT_PATH.relative_to(ROOT)),
                "refreshCommand": "make update-state",
            },
            "git": git_info(),
            "metrics": metrics,
            "orchestration": {
                "agents": agent_summary(),
                "tasks": task_summary(),
                "decisions": decision_summary(),
                "overnightQueue": overnight_queue_summary(),
            },
            "architecture": {
                "atlas": atlas_summary(),
                "keyArtifacts": {
                    "metrics": str(METRICS_PATH.relative_to(ROOT)),
                    "appAtlas": str((ATLAS_DIR / "2026-03-07-app-atlas.md").relative_to(ROOT)),
                    "atlasMap": str((ATLAS_DIR / "2026-03-08-app-atlas-map.mmd").relative_to(ROOT)),
                    "overnightQueue": str(OVERNIGHT_QUEUE_PATH.relative_to(ROOT)),
                    "overnightDispatchPlan": str(OVERNIGHT_PLAN_PATH.relative_to(ROOT)),
                },
            },
        }
    }


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    state = build_state()
    OUTPUT_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())