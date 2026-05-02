import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.main import app
from app.core.database import get_db
from app.models.core import User, Organization
from app.core.security import get_password_hash
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
