import pytest
from app.services.pedigree_service import PedigreeService
from app.models.germplasm import Germplasm, Cross
from app.models.core import Organization
from sqlalchemy import select

@pytest.mark.asyncio
async def test_inbreeding_calculation_repro(async_db_session):
    # Setup
    db = async_db_session

    # Create Org
    org = Organization(name="Genetics Org")
    db.add(org)
    await db.flush()

    # Create Founder Parents
    p1 = Germplasm(
        germplasm_db_id="P1",
        germplasm_name="Parent1",
        organization_id=org.id,
        breeding_method_db_id="unknown"
    )
    p2 = Germplasm(
        germplasm_db_id="P2",
        germplasm_name="Parent2",
        organization_id=org.id,
        breeding_method_db_id="unknown"
    )
    db.add_all([p1, p2])
    await db.flush()

    # Create F1 (Child of P1 x P2)
    cross_f1 = Cross(
        cross_db_id="C_F1",
        cross_name="P1xP2",
        organization_id=org.id,
        parent1_db_id=p1.id,
        parent2_db_id=p2.id
    )
    db.add(cross_f1)
    await db.flush()

    f1 = Germplasm(
        germplasm_db_id="F1",
        germplasm_name="Filial1",
        organization_id=org.id,
        cross_id=cross_f1.id,
        breeding_method_db_id="biparental"
    )
    db.add(f1)
    await db.flush()

    # Create Inbred Child (Self of F1: F1 x F1)
    # Inbreeding of Child = 0.5 * (1 + F_F1) = 0.5 * (1 + 0) = 0.5.

    cross_self = Cross(
        cross_db_id="C_Self",
        cross_name="F1xF1",
        organization_id=org.id,
        parent1_db_id=f1.id,
        parent2_db_id=f1.id
    )
    db.add(cross_self)
    await db.flush()

    child = Germplasm(
        germplasm_db_id="Child",
        germplasm_name="InbredChild",
        organization_id=org.id,
        cross_id=cross_self.id,
        breeding_method_db_id="self"
    )
    db.add(child)
    await db.commit()

    # Test Service
    service = PedigreeService(db)

    # Get Child
    data = await service.get_individual("Child", organization_id=org.id)

    # This assertion confirms the calculation is correct for a selfed individual
    assert data["inbreeding"] == 0.5
