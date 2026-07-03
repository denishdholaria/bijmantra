from fastapi.testclient import TestClient

from app.api.bijmantra.security import sso
from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_sso_router_is_registered_on_app() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v2/sso/login/{provider_id}" in paths
    assert "/api/v2/sso/callback/{provider_id}" in paths


def test_legacy_sso_routes_fail_closed_by_default(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LEGACY_SSO_ENABLED", False, raising=False)

    login_response = client.get("/api/v2/sso/login/demo-oidc", follow_redirects=False)
    oidc_callback_response = client.get(
        "/api/v2/sso/callback/demo-oidc?code=sample-code&state=sample-state",
        follow_redirects=False,
    )
    saml_callback_response = client.post(
        "/api/v2/sso/saml/callback/demo-saml",
        data={"SAMLResponse": "sample-response", "RelayState": "sample-state"},
        follow_redirects=False,
    )

    assert login_response.status_code == 503
    assert oidc_callback_response.status_code == 503
    assert saml_callback_response.status_code == 503


def test_legacy_sso_cannot_be_enabled_in_production(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LEGACY_SSO_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)

    response = client.get("/api/v2/sso/login/demo-oidc", follow_redirects=False)

    assert response.status_code == 503


def test_oauth_state_is_one_time_and_provider_bound() -> None:
    sso._state_store.clear()

    state = sso._create_oauth_state(provider_id="demo-oidc", redirect_to="/dashboard")
    redirect_to = sso._consume_oauth_state(provider_id="demo-oidc", state=state)

    assert redirect_to == "/dashboard"
    assert state not in sso._state_store


def test_oauth_state_rejects_provider_mismatch() -> None:
    sso._state_store.clear()

    state = sso._create_oauth_state(provider_id="demo-oidc", redirect_to="/")

    try:
        sso._consume_oauth_state(provider_id="demo-saml", state=state)
        assert False, "expected HTTPException for provider mismatch"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
