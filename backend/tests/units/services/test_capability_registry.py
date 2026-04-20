from types import SimpleNamespace

from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.schemas.functions import get_all_function_names, get_function_manifest


DISPATCH_PREFIXES = (
    "search_",
    "get_",
    "compare_",
    "calculate_",
    "analyze_",
    "recommend_",
    "predict_",
    "check_",
    "export_",
    "propose_",
)
EXACT_DISPATCH_NAMES = {"get_statistics", "navigate_to", "cross_domain_query"}


def _is_executor_dispatchable(function_name: str) -> bool:
    return function_name in EXACT_DISPATCH_NAMES or function_name.startswith(DISPATCH_PREFIXES)


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


def test_unsupported_drift_functions_are_not_advertised_in_registry():
    registry = CapabilityRegistry.from_agent_setting(None)
    function_names = get_all_function_names()

    assert "calculate_gdd" not in function_names
    assert "generate_trial_report" not in function_names
    assert registry.can_execute("calculate_gdd") is False
    assert registry.can_execute("generate_trial_report") is False


def test_internal_helper_functions_are_not_advertised_in_registry():
    registry = CapabilityRegistry.from_agent_setting(None)
    function_names = get_all_function_names()

    for helper_name in (
        "get_statistics",
        "predict_harvest_timing",
        "recommend_varieties_by_gdd",
        "analyze_planting_windows",
        "get_gdd_insights",
    ):
        assert helper_name not in function_names
        assert registry.can_execute(helper_name) is False


def test_internal_helper_functions_are_not_exposed_in_function_manifest():
    manifest = get_function_manifest()
    tool_names = {
        tool["name"]
        for category in manifest
        for tool in category["tools"]
    }

    for helper_name in (
        "get_statistics",
        "predict_harvest_timing",
        "recommend_varieties_by_gdd",
        "analyze_planting_windows",
        "get_gdd_insights",
    ):
        assert helper_name not in tool_names


def test_all_advertised_functions_have_executor_dispatch_route():
    function_names = get_all_function_names()
    uncovered = [name for name in function_names if not _is_executor_dispatchable(name)]

    assert uncovered == []