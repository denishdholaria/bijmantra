from app.api.v2.new_routers import sso
from app.main import app


def test_sso_router_is_registered_on_app() -> None:
    paths = {route.path for route in app.routes}
    assert "/api/v2/sso/login/{provider_id}" in paths
    assert "/api/v2/sso/callback/{provider_id}" in paths


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
