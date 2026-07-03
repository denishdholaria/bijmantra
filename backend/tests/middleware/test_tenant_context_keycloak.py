"""Tenant-context extraction for Keycloak-authenticated requests."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from app.core.config import settings
from app.middleware import tenant_context
from app.middleware.tenant_context import TenantContextMiddleware
from app.models.core import AuthIdentity, Organization, User
from tests.conftest import AsyncTestingSessionLocal


ISSUER = "http://localhost:8084/realms/bijmantra"


def _request_with_token(token: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v2/programs",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
        }
    )


def _verified_claims(subject: str = "tenant-context-subject"):
    async def _claims(token: str) -> dict:
        assert token == "keycloak-access-token"
        return {
            "iss": ISSUER,
            "sub": subject,
            "email": "admin@bijmantra.org",
        }

    return _claims


async def _create_keycloak_user() -> tuple[int, int]:
    async with AsyncTestingSessionLocal() as session:
        org = Organization(name="Keycloak Tenant Context Org")
        session.add(org)
        await session.flush()
        user = User(
            organization_id=org.id,
            email="tenant-context@example.com",
            hashed_password="external-keycloak",
            full_name="Tenant Context Admin",
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()
        session.add(
            AuthIdentity(
                organization_id=org.id,
                user_id=user.id,
                provider="keycloak",
                issuer=ISSUER,
                subject="tenant-context-subject",
                email_at_login="admin@bijmantra.org",
            )
        )
        await session.commit()
        return org.id, user.id


@pytest.mark.asyncio
async def test_tenant_context_resolves_org_from_keycloak_identity(setup_db, monkeypatch):
    org_id, user_id = await _create_keycloak_user()
    monkeypatch.setattr(settings, "KEYCLOAK_ENABLED", True)
    monkeypatch.setattr(tenant_context, "AsyncSessionLocal", AsyncTestingSessionLocal)
    monkeypatch.setattr(tenant_context, "verify_keycloak_token", _verified_claims())

    middleware = TenantContextMiddleware(app=lambda scope, receive, send: None)
    tenant_info = await middleware._extract_tenant_info(
        _request_with_token("keycloak-access-token")
    )

    assert tenant_info == {
        "organization_id": org_id,
        "is_superuser": False,
        "user_id": user_id,
    }


@pytest.mark.asyncio
async def test_tenant_context_returns_empty_for_unmapped_keycloak_subject(setup_db, monkeypatch):
    monkeypatch.setattr(settings, "KEYCLOAK_ENABLED", True)
    monkeypatch.setattr(tenant_context, "AsyncSessionLocal", AsyncTestingSessionLocal)
    monkeypatch.setattr(
        tenant_context,
        "verify_keycloak_token",
        _verified_claims("unmapped-tenant-context-subject"),
    )

    middleware = TenantContextMiddleware(app=lambda scope, receive, send: None)
    tenant_info = await middleware._extract_tenant_info(
        _request_with_token("keycloak-access-token")
    )

    assert tenant_info == {}
