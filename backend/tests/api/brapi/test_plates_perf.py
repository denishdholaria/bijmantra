import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Program, Trial, Study
from app.models.genotyping import Plate
import uuid

@pytest.mark.asyncio
async def test_update_plates_performance(
    authenticated_client: AsyncClient,
    async_db_session: AsyncSession
):
    """
    Test updating plates to verify performance and correctness (no N+1/MissingGreenlet).
    """
    # 1. Setup dependencies
    # Create Program
    program = Program(
        organization_id=1,
        program_db_id=f"prog-{uuid.uuid4().hex[:8]}",
        program_name="Test Program",
        objective="Testing"
    )
    async_db_session.add(program)
    await async_db_session.flush()

    # Create Trial
    trial = Trial(
        organization_id=1,
        program_id=program.id,
        trial_db_id=f"trial-{uuid.uuid4().hex[:8]}",
        trial_name="Test Trial",
        active=True
    )
    async_db_session.add(trial)
    await async_db_session.flush()

    # Create Study
    study = Study(
        organization_id=1,
        trial_id=trial.id,
        study_db_id=f"study-{uuid.uuid4().hex[:8]}",
        study_name="Test Study",
        active=True
    )
    async_db_session.add(study)
    await async_db_session.commit()

    # 2. Create Plates via API
    plate1_data = {
        "plateName": "Plate 1",
        "plateBarcode": "BC001",
        "plateFormat": "PLATE_96",
        "sampleType": "DNA",
        "studyDbId": study.study_db_id,
        "trialDbId": trial.trial_db_id,
        "programDbId": program.program_db_id
    }
    plate2_data = {
        "plateName": "Plate 2",
        "plateBarcode": "BC002",
        "plateFormat": "PLATE_96",
        "sampleType": "DNA",
        "studyDbId": study.study_db_id,
        "trialDbId": trial.trial_db_id,
        "programDbId": program.program_db_id
    }

    response = await authenticated_client.post("/brapi/v2/plates", json=[plate1_data, plate2_data])
    assert response.status_code == 200
    created_plates = response.json()["result"]["data"]
    assert len(created_plates) == 2

    plate1_id = created_plates[0]["plateDbId"]
    plate2_id = created_plates[1]["plateDbId"]

    # Manually associate the plates with the study/trial/program in the DB
    # because the create_plates API currently ignores them (based on code analysis).
    # We need them associated to trigger the lazy loading issue in update_plates.
    # Note: If create_plates is fixed to handle relationships, this manual step isn't needed.
    # But currently create_plates only sets fields, not relationships.
    # Wait, create_plates sets fields. Plate model has study_id, trial_id, program_id.
    # But create_plates does NOT look up studyDbId etc to set IDs.
    # So we must update them manually in DB to simulate a real scenario where they are linked.

    from sqlalchemy import select, update

    # We need to find the plate IDs (int) or update by plate_db_id
    stmt = update(Plate).where(Plate.plate_db_id.in_([plate1_id, plate2_id])).values(
        study_id=study.id,
        trial_id=trial.id,
        program_id=program.id
    )
    await async_db_session.execute(stmt)
    await async_db_session.commit()

    # 3. Update Plates via API
    # This should trigger the N+1 or MissingGreenlet if not optimized
    update_data = [
        {
            "plateDbId": plate1_id,
            "plateName": "Plate 1 Updated",
            "additionalInfo": {"updated": True}
        },
        {
            "plateDbId": plate2_id,
            "plateName": "Plate 2 Updated",
            "additionalInfo": {"updated": True}
        }
    ]

    response = await authenticated_client.put("/brapi/v2/plates", json=update_data)

    # Assert success
    assert response.status_code == 200
    updated_plates = response.json()["result"]["data"]
    assert len(updated_plates) == 2
    assert updated_plates[0]["plateName"] == "Plate 1 Updated"

    # Check that studyDbId is returned correctly (meaning relationship was loaded)
    # Since we manually linked them, they should be present.
    # If lazy loading failed, this might have crashed or returned None depending on error handling (but here likely crash).
    assert updated_plates[0]["studyDbId"] == study.study_db_id
