import pytest

from app.core.rls import clear_tenant_context, set_tenant_context


class RecordingSession:
    def __init__(self):
        self.execute_calls = []

    async def execute(self, statement, params=None):
        self.execute_calls.append((statement, params or {}))


def _config_values(session: RecordingSession) -> dict[str, str]:
    return {
        params["key"]: params["value"]
        for _statement, params in session.execute_calls
        if "key" in params
    }


@pytest.mark.asyncio
async def test_set_tenant_context_sets_user_context_for_user_owned_rls_policies():
    session = RecordingSession()

    await set_tenant_context(session, organization_id=456, user_id=123)

    config_values = _config_values(session)
    assert config_values["app.current_organization_id"] == "456"
    assert config_values["app.current_user_id"] == "123"


@pytest.mark.asyncio
async def test_set_tenant_context_defaults_user_context_to_restricted_value():
    session = RecordingSession()

    await set_tenant_context(session, organization_id=456)

    config_values = _config_values(session)
    assert config_values["app.current_organization_id"] == "456"
    assert config_values["app.current_user_id"] == "-1"


@pytest.mark.asyncio
async def test_clear_tenant_context_resets_organization_and_user_contexts():
    session = RecordingSession()

    await clear_tenant_context(session)

    statements = [str(statement) for statement, _params in session.execute_calls]
    assert "RESET app.current_organization_id" in statements
    assert "RESET app.current_user_id" in statements
