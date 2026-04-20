import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.breeding.services.pipeline_service import BreedingPipelineService, PIPELINE_STAGES
from app.models.germplasm import Germplasm
from app.models.core import User


pytestmark = pytest.mark.performance

@pytest.mark.asyncio
async def test_stage_summary_performance(async_db_session: AsyncSession, test_user: User):
    """
    Benchmark BreedingPipelineService.get_stage_summary performance
    """
    service = BreedingPipelineService(async_db_session, test_user.organization_id)

    # Seed data
    germplasms = []
    # Create 100 entries for each of the 7 stages = 700 entries
    print("\n[BENCHMARK] Seeding database with 700 entries...")
    for stage in PIPELINE_STAGES:
        for i in range(100):
            entry_id = f"BM-BENCH-{stage['id']}-{i}"
            info = {
                "breeding_pipeline_stage": stage["id"],
                "breeding_pipeline_status": "active",
                "breeding_pipeline_program_id": "PROG-1",
                "breeding_pipeline_year": 2024
            }
            germplasm = Germplasm(
                organization_id=test_user.organization_id,
                germplasm_db_id=entry_id,
                germplasm_name=f"Entry {stage['id']} {i}",
                default_display_name=f"Entry {stage['id']} {i}",
                common_crop_name="Wheat",
                additional_info=info
            )
            germplasms.append(germplasm)

    async_db_session.add_all(germplasms)
    await async_db_session.commit()
    print("[BENCHMARK] Seeding complete.")

    # Measure performance
    start_time = time.perf_counter()
    summary = await service.get_stage_summary()
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"\n[BENCHMARK] get_stage_summary took {duration:.4f} seconds for {len(germplasms)} entries.")

    # Verify structure and data
    assert len(summary) == len(PIPELINE_STAGES)

    for stage_summary in summary:
        stage_id = stage_summary["stage_id"]
        # We added 100 active entries per stage
        assert stage_summary["count"] == 100, f"Stage {stage_id} count mismatch"
        assert len(stage_summary["entries"]) == 5, f"Stage {stage_id} entries mismatch"

        # Verify entries are from correct stage
        for entry in stage_summary["entries"]:
             assert entry["id"].startswith(f"BM-BENCH-{stage_id}"), f"Entry {entry['id']} in wrong stage {stage_id}"

    # Verify order is correct (latest created should be first, i.e. desc ID)
    # Since we inserted sequentially, higher ID means later creation.
    # Germplasm IDs are auto-increment integers usually.
    # Let's check the first entry of the first stage.
    first_stage = summary[0]
    # Check "F1" stage specifically if order matches
    if first_stage["stage_id"] == "F1":
        first_entry = first_stage["entries"][0]
        # It should be the last one inserted for that stage (index 99)
        assert first_entry["name"] == f"Entry F1 99"
