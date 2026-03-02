import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.biosimulation import CropModel
from app.models.core import User, Organization
from app.core.security import create_access_token
from datetime import timedelta
from app.main import app
from app.core.database import get_db
from backend.tests.conftest import AsyncTestingSessionLocal

@pytest.mark.asyncio
async def test_create_crop_model(
    authenticated_client: AsyncClient,
    async_db_session: AsyncSession,
    test_user: User
):
    """
    Test that creating a crop model correctly assigns the organization_id from the current user.
    """
    # Create a new organization
    new_org = Organization(name="Second Org")
    async_db_session.add(new_org)
    await async_db_session.commit()
    await async_db_session.refresh(new_org)

    org_id = new_org.id
    assert org_id != 1 # Ensure it is different from default if possible, or just note it.

    new_user = User(
        email="user2@example.com",
        hashed_password="password",
        organization_id=org_id
    )
    async_db_session.add(new_user)
    await async_db_session.commit()
    await async_db_session.refresh(new_user)

    # Create a client for this new user
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(new_user.id)}, expires_delta=access_token_expires
    )

    # We need to ensure the dependency override for get_db is active.
    # The authenticated_client fixture sets it up, but it clears it after yield!
    # Wait, authenticated_client clears dependency_overrides after yield.
    # Since we are inside the test function, authenticated_client context manager is still active?
    # No, fixtures wrap the test.
    # The fixture:
    # yield client
    # app.dependency_overrides.clear()

    # So the override IS active during the test.
    # So we can just create a new client.

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as client:
        payload = {
            "name": "Test Maize Variety 2",
            "crop_name": "Maize",
            "description": "A test variety",
            "base_temp": 10.0,
            "gdd_flowering": 800.0,
            "gdd_maturity": 1600.0,
            "rue": 1.5
        }

        response = await client.post("/api/v2/biosimulation/models", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == payload["name"]
        assert "id" in data

        # Verify in DB
        result = await async_db_session.execute(
            select(CropModel).where(CropModel.id == data["id"])
        )
        crop_model = result.scalar_one_or_none()

        assert crop_model is not None
        assert crop_model.organization_id == org_id
        assert crop_model.organization_id == new_user.organization_id
