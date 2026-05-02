#!/usr/bin/env python3
"""Validate active agent-control surfaces for drift and structural damage."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_overnight_queue import load_queue, validate_queue  # noqa: E402


AI_ROOT = ROOT / ".ai"
AGENT_JOBS_ROOT = ROOT / ".agent" / "jobs"
GITHUB_AGENTS_ROOT = ROOT / ".github" / "agents"
GITHUB_HOOKS_ROOT = ROOT / ".github" / "hooks"
GITHUB_INSTRUCTIONS_ROOT = ROOT / ".github" / "instructions"
GITHUB_PROMPTS_ROOT = ROOT / ".github" / "prompts"
GITHUB_SKILLS_ROOT = ROOT / ".github" / "skills"
DEVIL_FLAG_HOOK = GITHUB_HOOKS_ROOT / "devil-file-flags.json"
DEVIL_FLAG_SCANNER = ROOT / "scripts" / "devil_flag_scanner.py"
OPERATOR_GUIDE = GITHUB_AGENTS_ROOT / "2026-03-13-phase1-agent-operator-guide.md"
PROMPT_COOKBOOK = GITHUB_AGENTS_ROOT / "2026-03-13-phase1-agent-prompt-cookbook.md"
PROJECT_MANAGEMENT_TEMPLATE = (
    GITHUB_AGENTS_ROOT / "2026-03-15-om-shri-maatre-daily-project-management-template.md"
)

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

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def fail(message: str) -> None:
    raise SystemExit(message)


def validate_core_paths() -> None:
    required_paths = [
        AI_ROOT / "README.md",
        AI_ROOT / "AGENT_COORDINATION_PROTOCOL.md",
        AGENT_JOBS_ROOT / "README.md",
        AGENT_JOBS_ROOT / "lane-schema.json",
        AGENT_JOBS_ROOT / "overnight-queue.json",
        GITHUB_AGENTS_ROOT,
        GITHUB_HOOKS_ROOT,
        GITHUB_INSTRUCTIONS_ROOT,
        GITHUB_PROMPTS_ROOT,
        GITHUB_SKILLS_ROOT,
        DEVIL_FLAG_HOOK,
        DEVIL_FLAG_SCANNER,
        OPERATOR_GUIDE,
        PROMPT_COOKBOOK,
        PROJECT_MANAGEMENT_TEMPLATE,
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        fail("Missing required control-surface paths:\n" + "\n".join(f"- {path}" for path in missing))


def validate_lane_schema() -> None:
    schema = json.loads((AGENT_JOBS_ROOT / "lane-schema.json").read_text(encoding="utf-8"))
    required = set(schema.get("required", []))
    expected = {
        "objective",
        "inputs",
        "outputs",
        "dependencies",
        "completion_criteria",
    }
    if required != expected:
        fail(
            "Lane schema required keys drifted from the canonical contract:\n"
            f"- expected: {sorted(expected)}\n"
            f"- found: {sorted(required)}"
        )


def validate_overnight_queue() -> None:
    queue = load_queue(AGENT_JOBS_ROOT / "overnight-queue.json")
    validate_queue(queue)


def validate_agent_markdown() -> None:
    agent_files = sorted(GITHUB_AGENTS_ROOT.glob("*.agent.md"))
    if not agent_files:
        fail("No custom agent files found in .github/agents")

    for path in agent_files:
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if match is None:
            fail(f"Missing YAML frontmatter in {path.relative_to(ROOT)}")

        frontmatter = match.group(1)
        if "name:" not in frontmatter:
            fail(f"Missing name field in {path.relative_to(ROOT)}")
        if "description:" not in frontmatter:
            fail(f"Missing description field in {path.relative_to(ROOT)}")


def validate_hook_json() -> None:
    hook_files = sorted(GITHUB_HOOKS_ROOT.glob("*.json"))
    if not hook_files:
        fail("No hook files found in .github/hooks")

    for path in hook_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}")

        hooks = payload.get("hooks")
        if not isinstance(hooks, dict) or not hooks:
            fail(f"Hook file must contain a non-empty hooks object: {path.relative_to(ROOT)}")

        for event_name, entries in hooks.items():
            if event_name not in VALID_HOOK_EVENTS:
                fail(f"Unknown hook event '{event_name}' in {path.relative_to(ROOT)}")
            if not isinstance(entries, list) or not entries:
                fail(f"Hook event '{event_name}' must map to a non-empty list in {path.relative_to(ROOT)}")

            for index, entry in enumerate(entries, start=1):
                if not isinstance(entry, dict):
                    fail(f"Hook entry #{index} for '{event_name}' must be an object in {path.relative_to(ROOT)}")
                if entry.get("type") != "command":
                    fail(f"Hook entry #{index} for '{event_name}' must declare type=command in {path.relative_to(ROOT)}")
                if not any(isinstance(entry.get(field_name), str) and entry.get(field_name).strip() for field_name in ("command", "windows", "linux", "osx")):
                    fail(f"Hook entry #{index} for '{event_name}' must declare a command in {path.relative_to(ROOT)}")
                timeout = entry.get("timeout")
                if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
                    fail(f"Hook entry #{index} for '{event_name}' has invalid timeout in {path.relative_to(ROOT)}")


def validate_instruction_markdown() -> None:
    instruction_files = sorted(GITHUB_INSTRUCTIONS_ROOT.glob("*.instructions.md"))
    if not instruction_files:
        fail("No instruction files found in .github/instructions")

    for path in instruction_files:
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if match is None:
            fail(f"Missing YAML frontmatter in {path.relative_to(ROOT)}")

        frontmatter = match.group(1)
        if "description:" not in frontmatter:
            fail(f"Missing description field in {path.relative_to(ROOT)}")


def validate_prompt_markdown() -> None:
    prompt_files = sorted(GITHUB_PROMPTS_ROOT.glob("*.prompt.md"))
    if not prompt_files:
        fail("No prompt files found in .github/prompts")

    for path in prompt_files:
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if match is None:
            fail(f"Missing YAML frontmatter in {path.relative_to(ROOT)}")

        frontmatter = match.group(1)
        if "description:" not in frontmatter:
            fail(f"Missing description field in {path.relative_to(ROOT)}")


def validate_skill_markdown() -> None:
    skill_files = sorted(GITHUB_SKILLS_ROOT.glob("*/SKILL.md"))
    if not skill_files:
        fail("No skill files found in .github/skills")

    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if match is None:
            fail(f"Missing YAML frontmatter in {path.relative_to(ROOT)}")

        frontmatter = match.group(1)
        if "name:" not in frontmatter:
            fail(f"Missing name field in {path.relative_to(ROOT)}")
        if "description:" not in frontmatter:
            fail(f"Missing description field in {path.relative_to(ROOT)}")

        name_match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", frontmatter, re.MULTILINE)
        if name_match is None:
            fail(f"Skill name must be lowercase hyphenated text in {path.relative_to(ROOT)}")

        expected_name = path.parent.name
        if name_match.group(1) != expected_name:
            fail(
                f"Skill name mismatch in {path.relative_to(ROOT)}: expected '{expected_name}', found '{name_match.group(1)}'"
            )


def validate_active_surface_docs() -> None:
    active_docs = [
        AI_ROOT / "README.md",
        AI_ROOT / "AGENT_COORDINATION_PROTOCOL.md",
        AGENT_JOBS_ROOT / "README.md",
        GITHUB_AGENTS_ROOT / "README.md",
    ]
    for path in active_docs:
        text = path.read_text(encoding="utf-8")
        if "docs-private/" in text:
            fail(f"Active control-surface doc still references docs-private/: {path.relative_to(ROOT)}")


def main() -> int:
    validate_core_paths()
    validate_lane_schema()
    validate_overnight_queue()
    validate_agent_markdown()
    validate_hook_json()
    validate_instruction_markdown()
    validate_prompt_markdown()
    validate_skill_markdown()
    validate_active_surface_docs()
    print("Control surfaces are structurally valid and aligned with the current repo layout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())