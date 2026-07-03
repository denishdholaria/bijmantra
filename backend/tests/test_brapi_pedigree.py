
import pytest
from app.models.germplasm import Germplasm, Cross, CrossingProject
from app.models.core import Organization
from sqlalchemy import select

@pytest.mark.asyncio
async def test_pedigree_traversal(async_db_session, authenticated_client):
    # Setup data
    # Create Organization
    org = Organization(name="Pedigree Test Org")
    async_db_session.add(org)
    await async_db_session.commit()
    await async_db_session.refresh(org)

    # Create Parents
    parent1 = Germplasm(
        organization_id=org.id,
        germplasm_db_id="P1_ID",
        germplasm_name="Parent1",
        pedigree="Unknown"
    )
    parent2 = Germplasm(
        organization_id=org.id,
        germplasm_db_id="P2_ID",
        germplasm_name="Parent2",
        pedigree="Unknown"
    )
    async_db_session.add(parent1)
    async_db_session.add(parent2)
    await async_db_session.commit()
    await async_db_session.refresh(parent1)
    await async_db_session.refresh(parent2)

    # Create Crossing Project
    project = CrossingProject(
        organization_id=org.id,
        crossing_project_db_id="CP1_ID",
        crossing_project_name="Project1"
    )
    async_db_session.add(project)
    await async_db_session.commit()
    await async_db_session.refresh(project)

    # Create Cross
    cross = Cross(
        organization_id=org.id,
        cross_db_id="C1_ID",
        cross_name="P1xP2",
        crossing_project_id=project.id,
        parent1_db_id=parent1.id,
        parent1_type="FEMALE",
        parent2_db_id=parent2.id,
        parent2_type="MALE",
        crossing_year=2023
    )
    async_db_session.add(cross)
    await async_db_session.commit()
    await async_db_session.refresh(cross)

    # Create Child
    child = Germplasm(
        organization_id=org.id,
        germplasm_db_id="Child1_ID",
        germplasm_name="Child1",
        cross_id=cross.id
    )
    async_db_session.add(child)

    # Create Sibling
    sibling = Germplasm(
        organization_id=org.id,
        germplasm_db_id="Sibling1_ID",
        germplasm_name="Sibling1",
        cross_id=cross.id
    )
    async_db_session.add(sibling)
    await async_db_session.commit()

    # Call API
    response = await authenticated_client.get("/brapi/v2/germplasm/Child1_ID/pedigree?includeSiblings=true")

    assert response.status_code == 200
    data = response.json()["result"]

    # Check parents
    parents = data.get("parents", [])
    assert len(parents) == 2

    # Check siblings
    siblings = data.get("siblings", [])
    assert len(siblings) == 1

    # Check crossing info
    assert data.get("crossingProjectDbId") == "CP1_ID"
    assert data.get("crossingYear") == 2023
