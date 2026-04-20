"""Shared assertions for standardized safe-failure payload contracts."""


def assert_actionable_safe_failure_payload(
    safe_failure: dict | None,
    *,
    error_category: str,
) -> None:
    """Assert standardized safe-failure payload includes actionable non-empty fields."""
    assert safe_failure
    assert safe_failure.get("error_category") == error_category
    assert isinstance(safe_failure.get("searched"), list)
    assert isinstance(safe_failure.get("missing"), list)
    assert isinstance(safe_failure.get("next_steps"), list)
    assert len(safe_failure.get("searched")) > 0
    assert len(safe_failure.get("missing")) > 0
    assert len(safe_failure.get("next_steps")) > 0
    assert all(isinstance(step, str) and step.strip() for step in safe_failure.get("next_steps"))
