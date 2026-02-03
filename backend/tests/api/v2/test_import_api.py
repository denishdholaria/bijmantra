import pytest
from sqlalchemy import select
from app.models.germplasm import Germplasm
from app.models.core import User, Organization
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_import_germplasm_uses_user_org_id(
    authenticated_client: AsyncClient,
    async_db_session: AsyncSession,
    test_user: User
):
    # 1. Use the existing test_user and their organization
    org_id = test_user.organization_id
    assert org_id is not None
    
    # DEBUG: Verify Org exists in Async Session view
    org_in_db = await async_db_session.get(Organization, org_id)
    assert org_in_db is not None, f"Organization {org_id} not found in Async Session!"


    # 4. Import Germplasm
    payload = {
        "data": [
            {
                "germplasmName": "UniqueGermplasm123",
                "accessionNumber": "A123",
                "genus": "Zea",
                "species": "mays",
                "commonCropName": "Maize"
            }
        ]
    }

    # The authenticated_client is already logged in as test_user
    response = await authenticated_client.post("/api/v2/import/germplasm", json=payload)
    assert response.status_code == 200, f"Response: {response.text}"

    # 5. Verify Organization ID
    # We verify against the DB to ensure the Import API used the user's Org ID
    query = select(Germplasm).where(Germplasm.germplasm_name == "UniqueGermplasm123")
    result = await async_db_session.execute(query)
    germplasm = result.scalars().first()

    assert germplasm is not None
    assert germplasm.organization_id == org_id, f"Expected {org_id}, got {germplasm.organization_id}"
