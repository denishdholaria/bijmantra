import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import User, Organization
from app.models.user_management import Role, UserRole

@pytest.mark.asyncio
async def test_get_dock_state_role_based(
    authenticated_client: AsyncClient,
    async_db_session: AsyncSession
):
    # 1. Setup Roles
    roles_data = [
        {"role_id": "breeder", "name": "Breeder"},
        {"role_id": "seed_company", "name": "Seed Company"},
        {"role_id": "technician", "name": "Technician"} # Not in DEFAULT_DOCKS
    ]

    # Check if organization exists (created by authenticated_client fixture implicitly via test_user)
    # But we need the ID.
    # The authenticated_client fixture uses a test_user fixture which uses sync session.
    # We can query the user from the async session.

    # Get the user created by authenticated_client
    result = await async_db_session.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one()
    org_id = user.organization_id

    # Create roles
    roles = {}
    for r_data in roles_data:
        role = Role(
            organization_id=org_id,
            role_id=r_data["role_id"],
            name=r_data["name"]
        )
        async_db_session.add(role)
        roles[r_data["role_id"]] = role

    await async_db_session.commit()

    # 2. Assign "breeder" role to the user
    # Need to reload roles to get their IDs
    for role in roles.values():
        await async_db_session.refresh(role)

    user_role = UserRole(
        user_id=user.id,
        role_id=roles["breeder"].id,
        granted_at=datetime.utcnow()
    )
    async_db_session.add(user_role)
    await async_db_session.commit()

    # 3. Call endpoint
    response = await authenticated_client.get(f"/api/v2/dock?user_id={user.id}")
    assert response.status_code == 200
    data = response.json()["data"]

    # 4. Verify "breeder" defaults
    # Breeder dock should have "Breeding Values" (path: /breeding-values)
    pinned_paths = [item["path"] for item in data["pinnedItems"]]
    assert "/breeding-values" in pinned_paths
    assert "/programs" in pinned_paths

    # 5. Change role to "technician" (fallback to default)
    # Remove existing role
    await async_db_session.delete(user_role)
    await async_db_session.commit()

    # Add technician role
    user_role_tech = UserRole(
        user_id=user.id,
        role_id=roles["technician"].id,
        granted_at=datetime.utcnow()
    )
    async_db_session.add(user_role_tech)
    await async_db_session.commit()

    # Call endpoint again
    response = await authenticated_client.get(f"/api/v2/dock?user_id={user.id}")
    assert response.status_code == 200
    data = response.json()["data"]

    # 6. Verify "default" defaults
    # Default dock does NOT have "Breeding Values"
    pinned_paths = [item["path"] for item in data["pinnedItems"]]
    assert "/breeding-values" not in pinned_paths
    assert "/programs" in pinned_paths # Default has programs too
