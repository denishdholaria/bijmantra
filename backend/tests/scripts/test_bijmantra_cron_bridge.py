from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _load_private_ops_module import load_private_ops_module


cron_bridge = load_private_ops_module(
    "krabi_test_bijmantra_cron_bridge",
    "ops-private/claw-runtime/scripts/bijmantra_cron_bridge.py",
)


def test_bridge_config_uses_agents_yaml_as_canonical_model(tmp_path, monkeypatch):
    config_path = tmp_path / "bridge-config.yaml"
    config_path.write_text(
        "bridge:\n"
        '  agent_id: "bijmantra-dev"\n'
        '  schedule_mode: "continuous"\n',
        encoding="utf-8",
    )
    agents_path = tmp_path / "agents.yaml"
    agents_path.write_text(
        "version: 1\n"
        "agents:\n"
        "  bijmantra-dev:\n"
        '    model: "google/gemini-2.5-pro"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(cron_bridge, "DEFAULT_AGENTS_PATH", agents_path)

    config = cron_bridge.BridgeConfig.from_yaml(config_path)

    assert config.default_model == "google/gemini-2.5-pro"


def test_load_agent_model_requires_explicit_model(tmp_path):
    agents_path = tmp_path / "agents.yaml"
    agents_path.write_text(
        "version: 1\n"
        "agents:\n"
        "  bijmantra-dev:\n"
        '    thinking: "medium"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing a model"):
        cron_bridge.load_agent_model(agents_path, "bijmantra-dev")


def test_load_agent_model_resolves_anchor_without_pyyaml(tmp_path, monkeypatch):
    agents_path = tmp_path / "agents.yaml"
    agents_path.write_text(
        "version: 1\n"
        "x-bijmantra-default-model: &bijmantra_default_model google/gemini-2.5-pro\n"
        "agents:\n"
        "  bijmantra-dev:\n"
        "    model: *bijmantra_default_model\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cron_bridge, "HAS_YAML", False)

    assert cron_bridge.load_agent_model(agents_path, "bijmantra-dev") == "google/gemini-2.5-pro"


def test_load_agent_model_rejects_unknown_anchor_without_pyyaml(tmp_path, monkeypatch):
    agents_path = tmp_path / "agents.yaml"
    agents_path.write_text(
        "version: 1\n"
        "agents:\n"
        "  bijmantra-dev:\n"
        "    model: *missing_model\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(cron_bridge, "HAS_YAML", False)

    with pytest.raises(ValueError, match="was not defined"):
        cron_bridge.load_agent_model(agents_path, "bijmantra-dev")


def test_ensure_auth_store_exists_raises_helpful_error(tmp_path):
    auth_store_path = tmp_path / "auth-profiles.json"

    with pytest.raises(RuntimeError, match="openclaw channels add"):
        cron_bridge.ensure_auth_store_exists(auth_store_path)


def test_build_agent_prompt_omits_branch_for_same_control_plane_jobs():
    config = cron_bridge.BridgeConfig(default_model="google/gemini-2.5-pro")

    prompt = cron_bridge.build_agent_prompt(
        {
            "jobId": "overnight-lane-platform-runtime-token1234",
            "title": "Platform Runtime",
            "priority": "p2",
            "executionMode": "same-control-plane",
            "goal": "Use the current checkout safely.",
            "lane": {
                "objective": "Keep the runtime branchless.",
                "inputs": ["board"],
            },
            "successCriteria": ["No branch is created."],
            "verificationCommands": ["pytest -q"],
        },
        config,
    )

    assert "**Workspace:** current checkout (no branch creation)" in prompt
    assert "**Branch:**" not in prompt
    assert "Do NOT create or switch branches" in prompt
    assert "Do NOT commit or merge" in prompt


def test_job_to_cron_spec_omits_branch_metadata_for_same_control_plane_jobs():
    config = cron_bridge.BridgeConfig(default_model="google/gemini-2.5-pro")

    spec = cron_bridge.job_to_cron_spec(
        {
            "jobId": "overnight-lane-platform-runtime-token1234",
            "title": "Platform Runtime",
            "priority": "p2",
            "executionMode": "same-control-plane",
            "primaryAgent": "OmShriMaatreNamaha",
            "lane": {"objective": "Keep the runtime branchless.", "inputs": []},
            "goal": "Use the current checkout safely.",
            "successCriteria": [],
            "verificationCommands": [],
        },
        config,
    )

    assert spec.session_target == "isolated"
    assert spec.metadata["executionMode"] == "same-control-plane"
    assert "branch" not in spec.metadata


def test_sync_to_gateway_cli_replaces_duplicates_and_submits_agent_messages(tmp_path, monkeypatch):
    runtime_home = tmp_path / "runtime-home"
    cron_sync_state = runtime_home / "cron-sync-state.json"
    monkeypatch.setattr(cron_bridge, "RUNTIME_HOME", runtime_home)
    monkeypatch.setattr(cron_bridge, "CRON_SYNC_STATE", cron_sync_state)

    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[-3:] == ["cron", "list", "--json"]:
            return SimpleNamespace(
                returncode=0,
                stdout='{"jobs":[{"id":"old-job-1","name":"bijmantra:overnight-lane-platform-runtime-token1234"}]}',
                stderr="",
            )
        if command[-3:] == ["cron", "rm", "old-job-1"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if "cron" in command and "add" in command:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(command)

    monkeypatch.setattr(cron_bridge.subprocess, "run", fake_run)

    results = cron_bridge.sync_to_gateway_cli(
        [
            cron_bridge.CronJobSpec(
                label="bijmantra:overnight-lane-platform-runtime-token1234",
                schedule_expr="*/30 * * * *",
                timezone="Asia/Kolkata",
                session_target="main",
                prompt="Run safely in the current checkout.",
                model="google/gemini-2.5-pro",
                timeout_seconds=600,
                metadata={"executionMode": "same-control-plane"},
            )
        ],
        cron_bridge.BridgeConfig(agent_id="bijmantra-dev", default_model="google/gemini-2.5-pro"),
        dry_run=False,
    )

    assert results["jobs"][0]["replacedJobIds"] == ["old-job-1"]
    add_call = next(command for command in calls if "add" in command)
    assert "--agent" in add_call
    assert "bijmantra-dev" in add_call
    assert "--message" in add_call
    assert "--system-event" not in add_call
    assert "--no-deliver" in add_call
