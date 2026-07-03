import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.api import auth as auth_api
from app.core.config import settings
from app.main import app
from app.core.database import get_db
from app.models.core import User, Organization
from app.core.security import decode_access_token, get_password_hash
from tests.conftest import AsyncTestingSessionLocal

@pytest.fixture
async def unauthenticated_client() -> AsyncClient:
    """
    Creates an unauthenticated client.
    Overrides get_db to use the async session connected to the SAME test database.
    """
    # Override dependency to use our async session factory
    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_login_success(
    unauthenticated_client: AsyncClient,
    async_db_session: AsyncSession
):
    """
    Test successful login.
    """
    # 1. Create Organization
    org = Organization(name="Auth Test Org")
    async_db_session.add(org)
    await async_db_session.flush()

    # 2. Create User with hashed password
    password = "StrongPassword123!"
    hashed_password = get_password_hash(password)
    user = User(
        email="auth_success@example.com",
        hashed_password=hashed_password,
        organization_id=org.id,
        is_active=True
    )
    async_db_session.add(user)
    await async_db_session.commit()

    # 3. Login
    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={
            "username": "auth_success@example.com",
            "password": password
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "auth_success@example.com"
    decoded_token = decode_access_token(data["access_token"])
    assert decoded_token is not None
    assert decoded_token["sub"] == str(user.id)
    assert decoded_token["organization_id"] == org.id
    assert decoded_token["is_superuser"] is False


@pytest.mark.asyncio
async def test_login_demo_credentials_mark_user_as_demo(
    unauthenticated_client: AsyncClient,
    async_db_session: AsyncSession,
):
    org = Organization(name=settings.DEMO_ORG_NAME)
    async_db_session.add(org)
    await async_db_session.flush()

    password = "StrongPassword123!"
    user = User(
        email=settings.DEMO_USER_EMAIL,
        hashed_password=get_password_hash(password),
        organization_id=org.id,
        is_active=True,
    )
    async_db_session.add(user)
    await async_db_session.commit()

    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={"username": settings.DEMO_USER_EMAIL, "password": password},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == settings.DEMO_USER_EMAIL
    assert data["user"]["organization_name"] == settings.DEMO_ORG_NAME
    assert data["user"]["is_demo"] is True


@pytest.mark.asyncio
async def test_login_wrong_password(
    unauthenticated_client: AsyncClient,
    async_db_session: AsyncSession
):
    """
    Test login with wrong password.
    """
    # 1. Create Organization
    org = Organization(name="Auth Fail Org")
    async_db_session.add(org)
    await async_db_session.flush()

    # 2. Create User
    password = "StrongPassword123!"
    hashed_password = get_password_hash(password)
    user = User(
        email="auth_fail@example.com",
        hashed_password=hashed_password,
        organization_id=org.id,
        is_active=True
    )
    async_db_session.add(user)
    await async_db_session.commit()

    # 3. Login with wrong password
    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={
            "username": "auth_fail@example.com",
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_normalizes_email_input(
    unauthenticated_client: AsyncClient,
    async_db_session: AsyncSession,
):
    org = Organization(name="Auth Normalized Org")
    async_db_session.add(org)
    await async_db_session.flush()

    password = "StrongPassword123!"
    user = User(
        email="auth_normalized@example.com",
        hashed_password=get_password_hash(password),
        organization_id=org.id,
        is_active=True,
    )
    async_db_session.add(user)
    await async_db_session.commit()

    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={
            "username": " Auth_Normalized@Example.Com ",
            "password": password,
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "auth_normalized@example.com"


@pytest.mark.asyncio
async def test_login_non_existent_user(
    unauthenticated_client: AsyncClient
):
    """
    Test login with non-existent user.
    """
    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={
            "username": "non_existent@example.com",
            "password": "AnyPassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_login_inactive_user(
    unauthenticated_client: AsyncClient,
    async_db_session: AsyncSession
):
    """
    Test login with inactive user.
    """
    # 1. Create Organization
    org = Organization(name="Auth Inactive Org")
    async_db_session.add(org)
    await async_db_session.flush()

    # 2. Create Inactive User
    password = "StrongPassword123!"
    hashed_password = get_password_hash(password)
    user = User(
        email="auth_inactive@example.com",
        hashed_password=hashed_password,
        organization_id=org.id,
        is_active=False
    )
    async_db_session.add(user)
    await async_db_session.commit()

    # 3. Login
    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={
            "username": "auth_inactive@example.com",
            "password": password
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"


@pytest.mark.asyncio
async def test_local_password_login_disabled_in_production_before_rate_limit(
    unauthenticated_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(
        settings,
        "ALLOW_LOCAL_PASSWORD_LOGIN_IN_PRODUCTION",
        False,
        raising=False,
    )
    rate_limit_check = AsyncMock()
    monkeypatch.setattr(auth_api.rate_limiter, "check", rate_limit_check)

    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={
            "username": "admin@bijmantra.org",
            "password": "Admin123!",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == (
        "Local password login is disabled in production. "
        "Use the configured identity provider."
    )
    rate_limit_check.assert_not_called()


@pytest.mark.asyncio
async def test_local_password_login_production_break_glass_flag_allows_login(
    unauthenticated_client: AsyncClient,
    async_db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(
        settings,
        "ALLOW_LOCAL_PASSWORD_LOGIN_IN_PRODUCTION",
        True,
        raising=False,
    )

    org = Organization(name="Auth Break Glass Org")
    async_db_session.add(org)
    await async_db_session.flush()

    password = "StrongPassword123!"
    user = User(
        email="auth_break_glass@example.com",
        hashed_password=get_password_hash(password),
        organization_id=org.id,
        is_active=True,
        is_superuser=True,
    )
    async_db_session.add(user)
    await async_db_session.commit()

    response = await unauthenticated_client.post(
        "/api/auth/login",
        data={
            "username": "auth_break_glass@example.com",
            "password": password,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["email"] == "auth_break_glass@example.com"
    assert data["user"]["is_superuser"] is True
    assert "access_token" in data
