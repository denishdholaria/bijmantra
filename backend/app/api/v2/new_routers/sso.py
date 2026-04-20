"""
SSO Router
Handles OIDC and SAML authentication flows.
"""

import json
import logging
import os
import secrets
import time

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.security import create_access_token
from app.modules.core.services.infra.saml_oidc_auth_provider import AuthError, SSOConfig, get_auth_provider


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sso", tags=["Single Sign-On"])
STATE_TTL_SECONDS = 600
_state_store: dict[str, dict[str, str | float]] = {}


def _cleanup_expired_states() -> None:
    now = time.time()
    expired_states = [key for key, value in _state_store.items() if value["expires_at"] < now]
    for key in expired_states:
        _state_store.pop(key, None)


def _create_oauth_state(provider_id: str, redirect_to: str | None) -> str:
    _cleanup_expired_states()
    state = secrets.token_urlsafe(32)
    _state_store[state] = {
        "provider_id": provider_id,
        "redirect_to": redirect_to or "/",
        "expires_at": time.time() + STATE_TTL_SECONDS,
    }
    return state


def _consume_oauth_state(provider_id: str, state: str) -> str:
    _cleanup_expired_states()
    state_data = _state_store.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if state_data.get("provider_id") != provider_id:
        raise HTTPException(status_code=400, detail="OAuth state does not match provider")

    return str(state_data.get("redirect_to") or "/")

# -----------------------------------------------------------------------------
# Configuration Store (Mock/Env based)
# -----------------------------------------------------------------------------
# In a real app, this might come from a database table 'SSOProviders'

def get_sso_config(provider_id: str) -> SSOConfig:
    # Example: Load from env var SSO_PROVIDERS_JSON or hardcoded for dev
    # format: [{"provider_id": "google", "type": "oidc", ...}]
    sso_json = os.getenv("SSO_PROVIDERS_JSON")
    if sso_json:
        try:
            configs = json.loads(sso_json)
            for cfg in configs:
                if cfg.get("provider_id") == provider_id:
                    return SSOConfig(**cfg)
        except Exception as e:
            logger.error(f"Failed to parse SSO_PROVIDERS_JSON: {e}")

    # Fallback/Demo configurations
    if provider_id == "demo-oidc":
        return SSOConfig(
            provider_id="demo-oidc",
            type="oidc",
            name="Demo OIDC",
            client_id=os.getenv("OIDC_CLIENT_ID", "demo-client"),
            client_secret=os.getenv("OIDC_CLIENT_SECRET", "demo-secret"),
            discovery_url=os.getenv("OIDC_DISCOVERY_URL", "https://accounts.google.com/.well-known/openid-configuration")
        )
    elif provider_id == "demo-saml":
        return SSOConfig(
            provider_id="demo-saml",
            type="saml",
            name="Demo SAML",
            sp_entity_id="http://localhost:8000/saml/metadata",
            idp_sso_url=os.getenv("SAML_IDP_URL", "https://idp.example.com/sso")
        )

    raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/login/{provider_id}")
async def sso_login(
    request: Request,
    provider_id: str,
    redirect_to: str | None = None
):
    """Initiate SSO login flow."""
    config = get_sso_config(provider_id)
    provider = get_auth_provider(config)

    # Persist state server-side to bind callback to this login initiation.
    state = _create_oauth_state(provider_id=provider_id, redirect_to=redirect_to)

    # Construct callback URL based on request host
    # e.g. https://api.bijmantra.org/api/v2/sso/callback/{provider_id}
    # But for OIDC/SAML strictness, this usually needs to be pre-registered.
    # We'll assume a standard path pattern.
    base_url = str(request.base_url).rstrip("/")
    # Note: If behind proxy, ensure X-Forwarded-Proto is handled (FastAPI does this with trusted proxies)

    if config.type == "saml":
        callback_uri = f"{base_url}/api/v2/sso/saml/callback/{provider_id}"
    else:
        callback_uri = f"{base_url}/api/v2/sso/callback/{provider_id}"

    try:
        login_url = await provider.get_login_url(state=state, redirect_uri=callback_uri)
        return RedirectResponse(login_url)
    except Exception as e:
        logger.error(f"SSO Login Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback/{provider_id}")
async def sso_oidc_callback(
    request: Request,
    provider_id: str,
    code: str,
    state: str
):
    """Handle OIDC Callback."""
    config = get_sso_config(provider_id)
    if config.type != "oidc":
         raise HTTPException(status_code=400, detail="Invalid provider type for this endpoint")

    provider = get_auth_provider(config)
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/v2/sso/callback/{provider_id}"

    try:
        redirect_to = _consume_oauth_state(provider_id=provider_id, state=state)
        auth_user = await provider.validate_callback(code=code, state=state, redirect_uri=redirect_uri)

        # Create App Session
        # Map auth_user to internal User model if needed, or just issue token with claims
        access_token = create_access_token(
            data={"sub": auth_user.email, "provider": provider_id, "name": auth_user.name}
        )

        # Redirect to frontend with token
        # Security Note: Passing token in URL fragment is standard for implicit flow,
        # but for code flow we usually set a cookie or return HTML with postMessage.
        # Here we redirect to a frontend handler route.
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        target_url = f"{frontend_url}/auth/callback?token={access_token}&redirect_to={redirect_to}"

        return RedirectResponse(target_url)

    except AuthError as e:
        logger.error(f"SSO Auth Error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"SSO Callback Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/saml/callback/{provider_id}")
async def sso_saml_callback(
    request: Request,
    provider_id: str,
    SAMLResponse: str = Form(...),
    RelayState: str = Form(None)
):
    """Handle SAML Callback (POST)."""
    config = get_sso_config(provider_id)
    if config.type != "saml":
         raise HTTPException(status_code=400, detail="Invalid provider type for this endpoint")

    provider = get_auth_provider(config)
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/api/v2/sso/saml/callback/{provider_id}"

    try:
        redirect_to = _consume_oauth_state(provider_id=provider_id, state=RelayState or "")
        auth_user = await provider.validate_callback(
            code=None,
            state=RelayState,
            redirect_uri=redirect_uri,
            SAMLResponse=SAMLResponse
        )

        access_token = create_access_token(
            data={"sub": auth_user.email, "provider": provider_id, "name": auth_user.name}
        )

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        target_url = f"{frontend_url}/auth/callback?token={access_token}&redirect_to={redirect_to}"

        return RedirectResponse(target_url, status_code=303) # 303 See Other for POST -> GET redirect

    except AuthError as e:
        logger.error(f"SAML Auth Error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"SAML Callback Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
