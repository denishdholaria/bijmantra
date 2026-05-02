#!/usr/bin/env python3
"""Bridge BijMantra's overnight-queue.json to OpenClaw's cron scheduler.

Reads the dispatch plan (from run_overnight_queue.py) and syncs matching
cron jobs into a running OpenClaw Gateway via its WebSocket API.

Usage:
    # Sync jobs to OpenClaw (default: dry-run)
    python ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py

    # Actually create/update cron jobs
    python ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py --apply

    # Custom config
    python ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py --config ~/.bijmantra/runtime/claw/bridge-config.yaml --apply
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend" / "app" / "modules" / "ai" / "services"))

from claw_runtime_contract import (  # noqa: E402
    resolve_claw_runtime_home,
    runtime_agents_config_path,
    runtime_auth_store_path,
    runtime_bridge_config_path,
    runtime_cron_jobs_dir,
    runtime_cron_sync_state_path,
)

RUNTIME_HOME = resolve_claw_runtime_home(ROOT)
DEFAULT_CONFIG_PATH = runtime_bridge_config_path(RUNTIME_HOME)
DEFAULT_AGENTS_PATH = runtime_agents_config_path(RUNTIME_HOME)
QUEUE_PATH = ROOT / ".agent" / "jobs" / "overnight-queue.json"
PLAN_OUTPUT = (
    ROOT
    / ".github"
    / "docs"
    / "architecture"
    / "tracking"
    / "overnight-dispatch-plan.json"
)
CRON_SYNC_STATE = runtime_cron_sync_state_path(RUNTIME_HOME)
OPENCLAW_AUTH_STORE = runtime_auth_store_path(RUNTIME_HOME)
OPENCLAW_GATEWAY_CONTAINER_NAME = "bijmantra-openclaw-gateway"
OPENCLAW_CONTAINER_RUNTIME_HOME = "/home/node/.openclaw"

logger = logging.getLogger("bijmantra-cron-bridge")

# ── Schedule mapping ─────────────────────────────────────────────────

WINDOW_TO_CRON: dict[str, str] = {
    "nightly": "0 22 * * *",       # 10 PM daily
    "hourly": "0 * * * *",         # Top of every hour
    "continuous": "*/30 * * * *",   # Every 30 minutes
    "morning": "0 6 * * *",        # 6 AM daily
    "weekend": "0 22 * * 6,0",     # 10 PM on weekends
}

PRIORITY_STAGGER_MINUTES: dict[str, int] = {
    "p0": 0,
    "p1": 5,
    "p2": 15,
    "p3": 30,
}


@dataclass
class BridgeConfig:
    """Configuration for the cron bridge."""

    gateway_url: str = "ws://127.0.0.1:18789"
    gateway_token: str = ""
    timezone: str = "Asia/Kolkata"
    default_model: str = ""
    agent_id: str = "bijmantra-dev"
    sandbox_image: str = "bijmantra-sandbox:latest"
    notification_channel: str = ""
    notification_to: str = ""
    max_duration_minutes: int = 120
    git_branch_prefix: str = "auto/"
    workspace_path: str = str(ROOT)
    schedule_mode: str = "continuous"  # nightly | continuous | custom

    @classmethod
    def from_yaml(cls, path: Path) -> BridgeConfig:
        if not path.exists():
            logger.info("No config at %s, using defaults", path)
            config = cls()
        elif not HAS_YAML:
            logger.warning("PyYAML not installed; using defaults")
            config = cls()
        else:
            with open(path, encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
            bridge = raw.get("bridge", raw)
            config = cls(**{k: v for k, v in bridge.items() if k in cls.__dataclass_fields__})

        if not config.default_model:
            config.default_model = load_agent_model(DEFAULT_AGENTS_PATH, config.agent_id)
        return config


def load_agent_model(path: Path, agent_id: str) -> str:
    """Load the canonical model for an OpenClaw agent from agents.yaml."""
    if HAS_YAML:
        with open(path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        agent = (raw.get("agents") or {}).get(agent_id) or {}
        model = agent.get("model")
        if isinstance(model, str) and model.strip():
            return model.strip()
        raise ValueError(f"Agent {agent_id!r} in {path} is missing a model")

    raw_text = path.read_text(encoding="utf-8")
    anchors = {
        match.group("name"): normalize_yaml_scalar(match.group("value"))
        for match in re.finditer(
            r"(?m)^[^\s#][^:]+:\s*&(?P<name>[^\s]+)\s+(?P<value>[^#\n]+)",
            raw_text,
        )
    }
    agent_match = re.search(
        rf"(?ms)^  {re.escape(agent_id)}:\s*\n(?P<body>(?:    .*\n?)*)",
        raw_text,
    )
    if not agent_match:
        raise ValueError(f"Agent {agent_id!r} not found in {path}")

    model_match = re.search(r"(?m)^    model:\s*(?P<model>[^\n]+)", agent_match.group("body"))
    if not model_match:
        raise ValueError(f"Agent {agent_id!r} in {path} is missing a model")

    model = normalize_yaml_scalar(model_match.group("model"))
    if model.startswith("*"):
        anchor_name = model.removeprefix("*")
        if anchor_name not in anchors:
            raise ValueError(f"Model anchor {anchor_name!r} referenced by {agent_id!r} was not defined")
        return anchors[anchor_name]
    return model


def normalize_yaml_scalar(value: str) -> str:
    """Normalize a simple YAML scalar for the lightweight fallback parser."""
    return value.split(" #", 1)[0].strip().strip("'\"")


def ensure_auth_store_exists(path: Path = OPENCLAW_AUTH_STORE) -> None:
    """Fail fast when the OpenClaw runtime auth store has not been seeded."""
    if path.exists():
        return
    raise RuntimeError(
        "OpenClaw runtime credentials are not configured. Seed "
        f"{path} by linking a provider channel with `openclaw channels add` or `openclaw channels login`, "
        "then binding the existing `main` agent with `openclaw agents bind --agent main --bind <channel[:account]>`. "
        "This BijMantra integration no longer reads provider API keys from docker-compose env vars."
    )


@dataclass
class CronJobSpec:
    """A cron job to sync into OpenClaw."""

    label: str
    schedule_expr: str
    timezone: str
    session_target: str
    prompt: str
    model: str
    timeout_seconds: int
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Dispatch plan → Cron job specs ───────────────────────────────────

def resolve_job_branch(job: dict[str, Any], config: BridgeConfig) -> str | None:
    """Return the isolated review branch for jobs that require one."""
    execution_mode = job.get("executionMode", "isolated-sub-lane")
    if execution_mode == "same-control-plane":
        return None
    return f"{config.git_branch_prefix}{job['jobId']}"

def build_agent_prompt(job: dict, config: BridgeConfig) -> str:
    """Build the agent prompt from a dispatch plan job."""
    lane = job.get("lane", {})
    inputs = lane.get("inputs", [])
    criteria = job.get("successCriteria", [])
    verification = job.get("verificationCommands", [])

    branch_name = resolve_job_branch(job, config)

    prompt_parts = [
        f"## Job: {job['title']}",
        f"**Priority:** {job['priority']}",
        "",
        "### Objective",
        job.get("goal", ""),
        "",
        "### Lane Objective",
        lane.get("objective", ""),
        "",
        "### Input Files (read these first)",
    ]
    if branch_name:
        prompt_parts.insert(2, f"**Branch:** `{branch_name}` (create from `main` if it doesn't exist)")
    else:
        prompt_parts.insert(2, "**Workspace:** current checkout (no branch creation)")

    for inp in inputs:
        prompt_parts.append(f"- `{inp}`")

    prompt_parts.extend([
        "",
        "### Success Criteria",
    ])
    for criterion in criteria:
        prompt_parts.append(f"- {criterion}")

    prompt_parts.extend([
        "",
        "### Verification (run these after changes)",
    ])
    for cmd in verification:
        prompt_parts.append(f"```bash\n{cmd}\n```")

    prompt_parts.extend(["", "### Rules"])
    if branch_name:
        prompt_parts.extend([
            "1. Work ONLY on the branch specified above.",
            "2. Do NOT modify files outside the lane inputs unless the objective requires it.",
            "3. Run ALL verification commands before marking complete.",
            "4. If verification fails, attempt to fix. If stuck after 2 attempts, stop and report.",
            "5. Commit with descriptive messages prefixed with `[auto]`.",
            f"6. Do NOT merge to `main`. Leave on `{branch_name}` for human review.",
        ])
    else:
        prompt_parts.extend([
            "1. Work in the current checkout. Do NOT create or switch branches.",
            "2. Do NOT modify files outside the lane inputs unless the objective requires it.",
            "3. Run ALL verification commands before marking complete.",
            "4. If verification fails, attempt to fix. If stuck after 2 attempts, stop and report.",
            "5. Do NOT commit or merge. Leave changes uncommitted for human review.",
        ])

    if job.get("notes"):
        prompt_parts.extend(["", "### Notes", job["notes"]])

    return "\n".join(prompt_parts)


def job_to_cron_spec(job: dict, config: BridgeConfig) -> CronJobSpec:
    """Convert a dispatch plan job to an OpenClaw cron job spec."""
    priority = job.get("priority", "p2")
    stagger = PRIORITY_STAGGER_MINUTES.get(priority, 10)
    schedule = WINDOW_TO_CRON.get(config.schedule_mode, config.schedule_mode)
    branch_name = resolve_job_branch(job, config)

    # Stagger by priority so p0 runs first, p1 5 min later, etc.
    if stagger > 0 and schedule.startswith("0 "):
        schedule = f"{stagger} " + schedule[2:]

    execution_mode = job.get("executionMode", "isolated-sub-lane")
    # Keep each overnight lane in an isolated OpenClaw session so agent-message
    # jobs execute reliably and do not share transient session state.
    session_target = "isolated"

    return CronJobSpec(
        label=f"bijmantra:{job['jobId']}",
        schedule_expr=schedule,
        timezone=config.timezone,
        session_target=session_target,
        prompt=build_agent_prompt(job, config),
        model=config.default_model,
        timeout_seconds=config.max_duration_minutes * 60,
        metadata={
            "jobId": job["jobId"],
            "priority": priority,
            "primaryAgent": job.get("primaryAgent"),
            "sourceTask": job.get("sourceTask"),
            "executionMode": execution_mode,
        },
    )

    if branch_name:
        spec.metadata["branch"] = branch_name

    return spec


def dispatch_plan_to_cron_specs(plan: dict, config: BridgeConfig) -> list[CronJobSpec]:
    """Convert the full dispatch plan into a list of cron specs."""
    specs: list[CronJobSpec] = []
    for job in plan.get("selectedJobs", []):
        specs.append(job_to_cron_spec(job, config))
    return specs


# ── OpenClaw Gateway interaction ─────────────────────────────────────

def cron_spec_to_gateway_payload(spec: CronJobSpec) -> dict[str, Any]:
    """Convert a CronJobSpec to an OpenClaw Gateway cron job create payload."""
    return {
        "label": spec.label,
        "schedule": {
            "kind": "cron",
            "expr": spec.schedule_expr,
            "tz": spec.timezone,
        },
        "sessionTarget": spec.session_target,
        "wake": "now",
        "payload": {
            "kind": "agentTurn",
            "message": spec.prompt,
            "model": spec.model,
            "timeoutSeconds": spec.timeout_seconds,
            "lightContext": False,
        },
        "delivery": {
            "mode": "none",
        },
        "enabled": True,
        "metadata": spec.metadata,
    }


def list_gateway_cron_jobs() -> list[dict[str, Any]]:
    """Return existing gateway cron jobs for duplicate replacement."""
    result = subprocess.run(
        [
            "podman", "exec",
            "--env", f"OPENCLAW_CONFIG_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
            "--env", f"OPENCLAW_STATE_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
            "--env", f"OPENCLAW_CONFIG_PATH={OPENCLAW_CONTAINER_RUNTIME_HOME}/openclaw.json",
            OPENCLAW_GATEWAY_CONTAINER_NAME,
            "node", "openclaw.mjs", "cron", "list", "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Unable to list gateway cron jobs")

    payload = json.loads(result.stdout)
    jobs = payload.get("jobs", payload) if isinstance(payload, dict) else payload
    return jobs if isinstance(jobs, list) else []


def remove_gateway_cron_job(job_id: str) -> None:
    """Remove an existing gateway cron job by id."""
    result = subprocess.run(
        [
            "podman", "exec",
            "--env", f"OPENCLAW_CONFIG_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
            "--env", f"OPENCLAW_STATE_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
            "--env", f"OPENCLAW_CONFIG_PATH={OPENCLAW_CONTAINER_RUNTIME_HOME}/openclaw.json",
            OPENCLAW_GATEWAY_CONTAINER_NAME,
            "node", "openclaw.mjs", "cron", "rm", job_id,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Unable to remove gateway cron job {job_id}")


def sync_to_gateway_cli(specs: list[CronJobSpec], config: BridgeConfig, *, dry_run: bool = True) -> dict[str, Any]:
    """Sync cron specs to OpenClaw Gateway via the CLI.

    In production, this would use the WebSocket API directly. For the
    bootstrap phase, we write the specs to a file that OpenClaw can read.
    """
    sync_dir = runtime_cron_jobs_dir(RUNTIME_HOME)
    sync_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "dryRun": dry_run,
        "totalSpecs": len(specs),
        "jobs": [],
    }

    for spec in specs:
        payload = cron_spec_to_gateway_payload(spec)
        job_file = sync_dir / f"{spec.label.replace(':', '_')}.json"

        if dry_run:
            logger.info("[DRY-RUN] Would create cron job: %s", spec.label)
            results["jobs"].append({
                "label": spec.label,
                "action": "would-create",
                "file": str(job_file),
            })
        else:
            job_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            logger.info("Wrote cron job spec: %s → %s", spec.label, job_file)
            results["jobs"].append({
                "label": spec.label,
                "action": "created",
                "file": str(job_file),
            })

            # Attempt to submit to gateway via CLI if available
            try:
                existing_jobs = list_gateway_cron_jobs()
                replaced_job_ids = [
                    job.get("id")
                    for job in existing_jobs
                    if isinstance(job, dict)
                    and isinstance(job.get("id"), str)
                    and (job.get("name") == spec.label or job.get("label") == spec.label)
                ]
                for job_id in replaced_job_ids:
                    remove_gateway_cron_job(job_id)
                if replaced_job_ids:
                    results["jobs"][-1]["replacedJobIds"] = replaced_job_ids
                
                result = subprocess.run(
                    [
                        "podman", "exec",
                        "--env", f"OPENCLAW_CONFIG_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
                        "--env", f"OPENCLAW_STATE_DIR={OPENCLAW_CONTAINER_RUNTIME_HOME}",
                        "--env", f"OPENCLAW_CONFIG_PATH={OPENCLAW_CONTAINER_RUNTIME_HOME}/openclaw.json",
                        OPENCLAW_GATEWAY_CONTAINER_NAME,
                        "node", "openclaw.mjs", "cron", "add",
                        "--agent", config.agent_id,
                        "--name", spec.label,
                        "--cron", spec.schedule_expr,
                        "--tz", spec.timezone,
                        "--model", spec.model,
                        "--timeout-seconds", str(spec.timeout_seconds),
                        "--session", spec.session_target,
                        "--no-deliver",
                        "--wake", "now",
                        "--message", spec.prompt,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    logger.info("Submitted to gateway: %s", spec.label)
                    results["jobs"][-1]["gateway"] = "submitted"
                else:
                    logger.warning(
                        "Gateway submit failed for %s: %s",
                        spec.label,
                        result.stderr.strip(),
                    )
                    results["jobs"][-1]["gateway"] = "file-only"
                    results["jobs"][-1]["gatewayError"] = result.stderr.strip()
            except FileNotFoundError:
                logger.info("openclaw CLI not found; cron job written to file only")
                results["jobs"][-1]["gateway"] = "cli-not-found"
            except subprocess.TimeoutExpired:
                logger.warning("Gateway submit timed out for %s", spec.label)
                results["jobs"][-1]["gateway"] = "timeout"

    # Save sync state
    CRON_SYNC_STATE.parent.mkdir(parents=True, exist_ok=True)
    CRON_SYNC_STATE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("Sync state written to %s", CRON_SYNC_STATE)

    return results


# ── Main ─────────────────────────────────────────────────────────────

def generate_plan() -> dict:
    """Run run_overnight_queue.py and return the dispatch plan."""
    script = ROOT / "scripts" / "run_overnight_queue.py"
    result = subprocess.run(
        [sys.executable, str(script), "--output", str(PLAN_OUTPUT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        logger.error("Dispatch plan generation failed:\n%s", result.stderr)
        raise RuntimeError(f"run_overnight_queue.py failed: {result.stderr}")

    return json.loads(PLAN_OUTPUT.read_text(encoding="utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to bridge config YAML",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create/update cron jobs (default: dry-run)",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=None,
        help="Use an existing dispatch plan instead of generating one",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    config = BridgeConfig.from_yaml(args.config)
    logger.info("Bridge config loaded (schedule_mode=%s)", config.schedule_mode)
    logger.info("Canonical model resolved from %s: %s", DEFAULT_AGENTS_PATH, config.default_model)

    # Generate or load the dispatch plan
    if args.plan and args.plan.exists():
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        logger.info("Loaded existing plan from %s", args.plan)
    else:
        logger.info("Generating dispatch plan...")
        plan = generate_plan()

    selected_count = len(plan.get("selectedJobs", []))
    blocked_count = plan.get("blockedJobCount", 0)
    logger.info(
        "Dispatch plan: %d selected, %d blocked",
        selected_count,
        blocked_count,
    )

    if selected_count == 0:
        logger.info("No jobs to sync")
        return 0

    # Convert to cron specs
    specs = dispatch_plan_to_cron_specs(plan, config)
    logger.info("Generated %d cron job specs", len(specs))

    # Sync to OpenClaw
    dry_run = not args.apply
    if dry_run:
        logger.info("DRY-RUN mode — use --apply to create cron jobs")
    else:
        ensure_auth_store_exists()

    results = sync_to_gateway_cli(specs, config, dry_run=dry_run)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"BijMantra → OpenClaw Cron Bridge {'(DRY-RUN)' if dry_run else ''}")
    print(f"{'=' * 60}")
    print(f"Schedule mode: {config.schedule_mode}")
    print(f"Timezone:      {config.timezone}")
    print(f"Agent:         {config.agent_id}")
    print(f"Model:         {config.default_model}")
    print(f"Jobs synced:   {len(results['jobs'])}")
    for job in results["jobs"]:
        status = job.get("gateway", job["action"])
        print(f"  • {job['label']}: {status}")
    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
