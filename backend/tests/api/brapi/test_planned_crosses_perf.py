import pytest
import time
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Program
from app.models.germplasm import CrossingProject, Germplasm


pytestmark = pytest.mark.performance

@pytest.mark.asyncio
async def test_create_planned_crosses_performance(
    authenticated_client: AsyncClient, async_db_session: AsyncSession
):
    """
    Benchmark creating multiple planned crosses to detect N+1 issues.
    """
    # 1. Setup Data
    # Create Program
    program = Program(
        organization_id=1,
        program_db_id=f"prog-{uuid.uuid4().hex[:8]}",
        program_name="Test Program",
        objective="Testing",
    )
    async_db_session.add(program)
    await async_db_session.flush()

    # Create Crossing Project
    project_db_id = f"proj-{uuid.uuid4().hex[:8]}"
    project = CrossingProject(
        organization_id=1,
        program_id=program.id,
        crossing_project_db_id=project_db_id,
        crossing_project_name="Test Project",
    )
    async_db_session.add(project)

    # Create Germplasm (Parents)
    parents = []
    for i in range(50):
        germplasm = Germplasm(
            organization_id=1,
            germplasm_db_id=f"germ-{uuid.uuid4().hex[:8]}",
            germplasm_name=f"Parent {i}",
        )
        async_db_session.add(germplasm)
        parents.append(germplasm)

    await async_db_session.commit()

    # Reload parents to get their db_ids (although we set them manually)
    # Actually we need the germplasm_db_id for the payload

    # 2. Prepare Payload
    crosses_payload = []
    num_crosses = 100
    for i in range(num_crosses):
        parent1 = parents[i % len(parents)]
        parent2 = parents[(i + 1) % len(parents)]

        crosses_payload.append({
            "plannedCrossName": f"Cross {i}",
            "crossingProjectDbId": project_db_id,
            "crossType": "BIPARENTAL",
            "parent1": {
                "germplasmDbId": parent1.germplasm_db_id,
                "parentType": "FEMALE"
            },
            "parent2": {
                "germplasmDbId": parent2.germplasm_db_id,
                "parentType": "MALE"
            }
        })

    # 3. Benchmark
    start_time = time.time()
    response = await authenticated_client.post("/brapi/v2/plannedcrosses", json=crosses_payload)
    end_time = time.time()

    duration = end_time - start_time
    print(f"\nTime to create {num_crosses} planned crosses: {duration:.4f} seconds")

    assert response.status_code == 201, response.text
    result = response.json()["result"]["data"]
    assert len(result) == num_crosses
