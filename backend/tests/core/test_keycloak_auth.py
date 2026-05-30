"""Keycloak JWT verification tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app.core import keycloak_auth


ISSUER = "http://localhost:8084/realms/bijmantra"
AUDIENCE = "bijmantra-api"


def _key_pair() -> tuple[object, dict]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": "test-key", "use": "sig", "alg": "RS256"})
    return private_key, jwk


def _token(private_key: object, **claim_overrides: object) -> str:
    claims = {
        "iss": ISSUER,
        "sub": "keycloak-subject-123",
        "aud": AUDIENCE,
        "email": "admin@bijmantra.org",
        "exp": datetime.now(UTC) + timedelta(minutes=10),
        "iat": datetime.now(UTC),
    }
    claims.update(claim_overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-key"})


async def _mock_jwks(jwks_url: str) -> dict:
    assert jwks_url.endswith("/certs")
    return {"keys": [_mock_jwks.jwk]}


@pytest.mark.asyncio
async def test_verify_keycloak_token_accepts_valid_rs256_token(monkeypatch):
    private_key, jwk = _key_pair()
    _mock_jwks.jwk = jwk
    monkeypatch.setattr(keycloak_auth.settings, "KEYCLOAK_ISSUER", ISSUER)
    monkeypatch.setattr(keycloak_auth.settings, "KEYCLOAK_AUDIENCE", AUDIENCE)
    monkeypatch.setattr(
        keycloak_auth.settings,
        "KEYCLOAK_JWKS_URL",
        f"{ISSUER}/protocol/openid-connect/certs",
    )
    monkeypatch.setattr(keycloak_auth, "_load_jwks", _mock_jwks)

    claims = await keycloak_auth.verify_keycloak_token(_token(private_key))

    assert claims["sub"] == "keycloak-subject-123"
    assert claims["email"] == "admin@bijmantra.org"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("claim_overrides", "match"),
    [
        ({"iss": "http://localhost:8084/realms/other"}, "issuer"),
        ({"aud": "wrong-api"}, "audience"),
        ({"exp": datetime.now(UTC) - timedelta(minutes=1)}, "expired"),
    ],
)
async def test_verify_keycloak_token_rejects_invalid_required_claims(
    monkeypatch,
    claim_overrides,
    match,
):
    private_key, jwk = _key_pair()
    _mock_jwks.jwk = jwk
    monkeypatch.setattr(keycloak_auth.settings, "KEYCLOAK_ISSUER", ISSUER)
    monkeypatch.setattr(keycloak_auth.settings, "KEYCLOAK_AUDIENCE", AUDIENCE)
    monkeypatch.setattr(
        keycloak_auth.settings,
        "KEYCLOAK_JWKS_URL",
        f"{ISSUER}/protocol/openid-connect/certs",
    )
    monkeypatch.setattr(keycloak_auth, "_load_jwks", _mock_jwks)

    with pytest.raises(keycloak_auth.KeycloakTokenError, match=match):
        await keycloak_auth.verify_keycloak_token(_token(private_key, **claim_overrides))


@pytest.mark.asyncio
async def test_verify_keycloak_token_rejects_token_without_kid(monkeypatch):
    private_key, jwk = _key_pair()
    _mock_jwks.jwk = jwk
    monkeypatch.setattr(keycloak_auth.settings, "KEYCLOAK_ISSUER", ISSUER)
    monkeypatch.setattr(keycloak_auth.settings, "KEYCLOAK_AUDIENCE", AUDIENCE)
    monkeypatch.setattr(
        keycloak_auth.settings,
        "KEYCLOAK_JWKS_URL",
        f"{ISSUER}/protocol/openid-connect/certs",
    )
    monkeypatch.setattr(keycloak_auth, "_load_jwks", _mock_jwks)

    token = jwt.encode(
        {
            "iss": ISSUER,
            "sub": "keycloak-subject-123",
            "aud": AUDIENCE,
            "exp": datetime.now(UTC) + timedelta(minutes=10),
        },
        private_key,
        algorithm="RS256",
    )

    with pytest.raises(keycloak_auth.KeycloakTokenError, match="kid"):
        await keycloak_auth.verify_keycloak_token(token)
