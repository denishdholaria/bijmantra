from types import SimpleNamespace

from app.modules.ai.services.capability_registry import CapabilityRegistry


def test_capability_registry_defaults_to_all_tools_without_agent_setting():
    registry = CapabilityRegistry.from_agent_setting(None)

    assert registry.can_execute("search_germplasm") is True
    assert registry.can_execute("search_trials") is True
    assert len(registry.get_allowed_functions()) > 10


def test_capability_registry_applies_overrides_and_policy_rules():
    agent_setting = SimpleNamespace(
        capability_overrides=["search_germplasm", "search_trials", "invalid_name"],
        tool_policy={"deny": ["search_germplasm"], "allow": ["search_trials", "search_germplasm"]},
    )

    registry = CapabilityRegistry.from_agent_setting(agent_setting)

    assert registry.get_allowed_function_names() == ["search_trials"]
    assert registry.can_execute("search_trials") is True
    assert registry.can_execute("search_germplasm") is False