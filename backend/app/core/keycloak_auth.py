"""Keycloak token verification and local identity resolution."""

from __future__ import annotations

import json
import logging
from time import monotonic
from typing import Any

import jwt
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.http_tracing import create_traced_async_client
from app.models.core import AuthIdentity, User


logger = logging.getLogger(__name__)

_KEYCLOAK_PROVIDER = "keycloak"
_SUPPORTED_ALGORITHMS = ["RS256"]
_JWKS_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


class KeycloakTokenError(Exception):
    """Raised when a Keycloak token cannot be cryptographically verified."""


def is_configured_keycloak_issuer_token(token: str) -> bool:
    """Return true when an untrusted token advertises the configured Keycloak issuer."""
    try:
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            },
        )
    except jwt.InvalidTokenError:
        return False

    return payload.get("iss") == settings.KEYCLOAK_ISSUER


async def _load_jwks(jwks_url: str) -> dict[str, Any]:
    cached = _JWKS_CACHE.get(jwks_url)
    now = monotonic()
    if cached and cached[0] > now:
        return cached[1]

    async with create_traced_async_client(timeout=5.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        jwks = response.json()

    if not isinstance(jwks, dict) or not isinstance(jwks.get("keys"), list):
        raise KeycloakTokenError("invalid jwks document")

    _JWKS_CACHE[jwks_url] = (now + settings.KEYCLOAK_JWKS_CACHE_SECONDS, jwks)
    return jwks


def _select_jwk(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    for jwk in jwks.get("keys", []):
        if isinstance(jwk, dict) and jwk.get("kid") == kid:
            return jwk
    return None


async def verify_keycloak_token(token: str) -> dict[str, Any]:
    """Verify a Keycloak RS256 access token against issuer, audience, and JWKS."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise KeycloakTokenError("invalid token header") from exc

    algorithm = header.get("alg")
    if algorithm not in _SUPPORTED_ALGORITHMS:
        raise KeycloakTokenError("unsupported token algorithm")

    kid = header.get("kid")
    if not kid:
        raise KeycloakTokenError("missing token kid")

    jwks = await _load_jwks(settings.KEYCLOAK_JWKS_URL)
    jwk = _select_jwk(jwks, kid)
    if jwk is None:
        raise KeycloakTokenError("unknown token kid")

    try:
        signing_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
        return jwt.decode(
            token,
            signing_key,
            algorithms=_SUPPORTED_ALGORITHMS,
            audience=settings.KEYCLOAK_AUDIENCE,
            issuer=settings.KEYCLOAK_ISSUER,
            options={"require": ["exp", "iss", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise KeycloakTokenError("expired token") from exc
    except jwt.InvalidIssuerError as exc:
        raise KeycloakTokenError("invalid token issuer") from exc
    except jwt.InvalidAudienceError as exc:
        raise KeycloakTokenError("invalid token audience") from exc
    except jwt.InvalidTokenError as exc:
        raise KeycloakTokenError("invalid token") from exc


async def resolve_keycloak_user(db: AsyncSession, claims: dict[str, Any]) -> User | None:
    """Resolve verified Keycloak claims to an existing local BijMantra user."""
    issuer = claims.get("iss")
    subject = claims.get("sub")
    if not isinstance(issuer, str) or not isinstance(subject, str):
        return None

    result = await db.execute(
        select(AuthIdentity)
        .where(
            AuthIdentity.provider == _KEYCLOAK_PROVIDER,
            AuthIdentity.issuer == issuer,
            AuthIdentity.subject == subject,
        )
        .options(selectinload(AuthIdentity.user))
    )
    identity = result.scalar_one_or_none()
    if identity is None or identity.user is None:
        return None

    if identity.organization_id != identity.user.organization_id:
        logger.error(
            "Keycloak identity organization mismatch",
            extra={
                "provider": identity.provider,
                "issuer": issuer,
                "subject": subject,
                "identity_organization_id": identity.organization_id,
                "user_organization_id": identity.user.organization_id,
            },
        )
        return None

    return identity.user
