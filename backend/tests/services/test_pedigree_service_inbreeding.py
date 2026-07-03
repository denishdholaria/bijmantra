import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.breeding.services.pedigree_service import PedigreeService
from app.models.germplasm import Germplasm, Cross
from app.models.core import Organization

@pytest.mark.asyncio
async def test_inbreeding_calculation_full_sibs(async_db_session: AsyncSession):
    """
    Test inbreeding calculation for full sib mating.
    Sire, Dam (unrelated) -> Child1, Child2
    Child1 x Child2 -> Target
    Expected F(Target) = 0.25
    """
    db = async_db_session

    # Create Organization
    org = Organization(name="Pedigree Org")
    db.add(org)
    await db.flush()

    # Create Parents (Founders)
    sire = Germplasm(
        germplasm_db_id="Sire", germplasm_name="Sire", organization_id=org.id,
        breeding_method_db_id="unknown"
    )
    dam = Germplasm(
        germplasm_db_id="Dam", germplasm_name="Dam", organization_id=org.id,
        breeding_method_db_id="unknown"
    )
    db.add_all([sire, dam])
    await db.flush()

    # Create Cross 1 (Sire x Dam)
    cross1 = Cross(
        cross_db_id="C1", cross_name="Sire/Dam", organization_id=org.id,
        parent1_db_id=sire.id, parent2_db_id=dam.id
    )
    db.add(cross1)
    await db.flush()

    # Create Children (Full Sibs)
    child1 = Germplasm(
        germplasm_db_id="Child1", germplasm_name="Child1", organization_id=org.id,
        breeding_method_db_id="unknown", cross_id=cross1.id
    )
    child2 = Germplasm(
        germplasm_db_id="Child2", germplasm_name="Child2", organization_id=org.id,
        breeding_method_db_id="unknown", cross_id=cross1.id
    )
    db.add_all([child1, child2])
    await db.flush()

    # Create Cross 2 (Child1 x Child2)
    cross2 = Cross(
        cross_db_id="C2", cross_name="Child1/Child2", organization_id=org.id,
        parent1_db_id=child1.id, parent2_db_id=child2.id
    )
    db.add(cross2)
    await db.flush()

    # Create Target
    target = Germplasm(
        germplasm_db_id="Target", germplasm_name="Target", organization_id=org.id,
        breeding_method_db_id="unknown", cross_id=cross2.id
    )
    db.add(target)
    await db.commit()

    # Test Calculation
    service = PedigreeService(db)

    # Verify using private method directly
    f_val = await service._calculate_inbreeding(target.id)
    assert abs(f_val - 0.25) < 1e-6

    # Verify using get_individual
    ind = await service.get_individual("Target", org.id)
    assert ind["id"] == "Target"
    assert abs(ind["inbreeding"] - 0.25) < 1e-6


@pytest.mark.asyncio
async def test_inbreeding_calculation_parent_offspring(async_db_session: AsyncSession):
    """
    Test inbreeding calculation for parent-offspring mating.
    Sire, Dam -> Child
    Sire x Child -> Target
    Expected F(Target) = 0.25
    """
    db = async_db_session

    org = Organization(name="Pedigree Org 2")
    db.add(org)
    await db.flush()

    sire = Germplasm(germplasm_db_id="P1", germplasm_name="P1", organization_id=org.id)
    dam = Germplasm(germplasm_db_id="P2", germplasm_name="P2", organization_id=org.id)
    db.add_all([sire, dam])
    await db.flush()

    c1 = Cross(cross_db_id="Cross1", cross_name="P1/P2", organization_id=org.id,
               parent1_db_id=sire.id, parent2_db_id=dam.id)
    db.add(c1)
    await db.flush()

    child = Germplasm(germplasm_db_id="Child", germplasm_name="Child", organization_id=org.id, cross_id=c1.id)
    db.add(child)
    await db.flush()

    c2 = Cross(cross_db_id="Cross2", cross_name="P1/Child", organization_id=org.id,
               parent1_db_id=sire.id, parent2_db_id=child.id)
    db.add(c2)
    await db.flush()

    target = Germplasm(germplasm_db_id="Target2", germplasm_name="Target2", organization_id=org.id, cross_id=c2.id)
    db.add(target)
    await db.commit()

    service = PedigreeService(db)
    f_val = await service._calculate_inbreeding(target.id)
    assert abs(f_val - 0.25) < 1e-6

@pytest.mark.asyncio
async def test_inbreeding_calculation_unrelated(async_db_session: AsyncSession):
    """
    Test inbreeding calculation for unrelated parents.
    P1, P2 -> Target
    Expected F = 0
    """
    db = async_db_session
    org = Organization(name="Pedigree Org 3")
    db.add(org)
    await db.flush()

    p1 = Germplasm(germplasm_db_id="U1", germplasm_name="U1", organization_id=org.id)
    p2 = Germplasm(germplasm_db_id="U2", germplasm_name="U2", organization_id=org.id)
    db.add_all([p1, p2])
    await db.flush()

    c1 = Cross(cross_db_id="CU", cross_name="U1/U2", organization_id=org.id,
               parent1_db_id=p1.id, parent2_db_id=p2.id)
    db.add(c1)
    await db.flush()

    target = Germplasm(germplasm_db_id="TargetU", germplasm_name="TargetU", organization_id=org.id, cross_id=c1.id)
    db.add(target)
    await db.commit()

    service = PedigreeService(db)
    f_val = await service._calculate_inbreeding(target.id)
    assert abs(f_val - 0.0) < 1e-6
