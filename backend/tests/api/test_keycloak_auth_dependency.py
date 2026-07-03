"""API dependency tests for Keycloak-backed authentication."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.core import AuthIdentity, Organization, User
from tests.conftest import AsyncTestingSessionLocal


ISSUER = "http://localhost:8084/realms/bijmantra"


async def _override_get_db():
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _verified_claims(subject: str):
    async def _claims(token: str) -> dict:
        assert token == "keycloak-access-token"
        return {
            "iss": ISSUER,
            "sub": subject,
            "email": "admin@bijmantra.org",
        }

    return _claims


async def _create_keycloak_user(
    *,
    active: bool = True,
    subject: str = "keycloak-subject-123",
    org_name: str = "Keycloak Test Org",
) -> None:
    async with AsyncTestingSessionLocal() as session:
        org = Organization(name=org_name)
        session.add(org)
        await session.flush()
        user = User(
            organization_id=org.id,
            email=f"{subject}@example.com",
            hashed_password="external-keycloak",
            full_name="Keycloak Admin",
            is_active=active,
            is_superuser=True,
        )
        session.add(user)
        await session.flush()
        session.add(
            AuthIdentity(
                organization_id=org.id,
                user_id=user.id,
                provider="keycloak",
                issuer=ISSUER,
                subject=subject,
                email_at_login="admin@bijmantra.org",
            )
        )
        await session.commit()


async def _verified_claims_for_admin(token: str) -> dict:
    assert token == "keycloak-access-token"
    return {
        "iss": ISSUER,
        "sub": "keycloak-subject-123",
        "email": "admin@bijmantra.org",
    }


@pytest.mark.asyncio
async def test_api_auth_me_accepts_mapped_keycloak_token(setup_db, monkeypatch):
    await _create_keycloak_user(subject="keycloak-subject-123", org_name="Keycloak Test Org A")
    monkeypatch.setattr(settings, "KEYCLOAK_ENABLED", True)
    monkeypatch.setattr(deps, "verify_keycloak_token", _verified_claims_for_admin)

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer keycloak-access-token"},
    ) as client:
        response = await client.get("/api/auth/me")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["email"] == "keycloak-subject-123@example.com"


@pytest.mark.asyncio
async def test_api_auth_me_rejects_unmapped_keycloak_subject(setup_db, monkeypatch):
    monkeypatch.setattr(settings, "KEYCLOAK_ENABLED", True)
    monkeypatch.setattr(deps, "verify_keycloak_token", _verified_claims("unmapped-subject"))

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer keycloak-access-token"},
    ) as client:
        response = await client.get("/api/auth/me")

    app.dependency_overrides.clear()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_auth_me_rejects_inactive_keycloak_user(setup_db, monkeypatch):
    await _create_keycloak_user(
        active=False,
        subject="inactive-keycloak-subject",
        org_name="Keycloak Test Org B",
    )
    monkeypatch.setattr(settings, "KEYCLOAK_ENABLED", True)
    monkeypatch.setattr(
        deps, "verify_keycloak_token", _verified_claims("inactive-keycloak-subject")
    )

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer keycloak-access-token"},
    ) as client:
        response = await client.get("/api/auth/me")

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"
