import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from app.modules.mars.optimizer import MarsOptimizer
from app.modules.mars.schemas import MarsEnvironmentProfileBase
from app.models.mars import MarsFailureMode
from app.models.germplasm import Germplasm
from app.models.core import Organization

def test_optimizer_logic():
    profile = MarsEnvironmentProfileBase(
        pressure_kpa=4.0,
        co2_ppm=400,
        o2_ppm=200000,
        radiation_msv=1.0,
        gravity_factor=0.38,
        photoperiod_hours=24,
        temperature_profile={"average": 20},
        humidity_profile={"average": 50}
    )
    result = MarsOptimizer.simulate_trial(profile, 1)
    assert result["failure_mode"] == MarsFailureMode.ATMOSPHERIC_COLLAPSE
    assert result["survival_score"] == 0.0

    profile.pressure_kpa = 20.0
    result = MarsOptimizer.simulate_trial(profile, 1)
    assert result["survival_score"] > 0.0
    assert result["failure_mode"] == MarsFailureMode.UNKNOWN

@pytest.mark.skip(reason="Requires full DB setup with Spatialite")
@pytest.mark.asyncio
async def test_create_environment_api(authenticated_client: AsyncClient):
    payload = {
        "pressure_kpa": 10.0,
        "co2_ppm": 400.0,
        "o2_ppm": 200000.0,
        "radiation_msv": 1.0,
        "gravity_factor": 0.38,
        "photoperiod_hours": 24.5,
        "temperature_profile": {"average": -60},
        "humidity_profile": {"average": 10}
    }
    response = await authenticated_client.post("/api/v2/mars/environments", json=payload)
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["pressure_kpa"] == 10.0
    assert "id" in data

@pytest.mark.skip(reason="Requires full DB setup with Spatialite")
@pytest.mark.asyncio
async def test_simulate_trial_api(authenticated_client: AsyncClient, db_session: Session):
    # 1. Create Environment
    env_payload = {
        "pressure_kpa": 4.0, # Failure
        "co2_ppm": 400.0,
        "o2_ppm": 200000.0,
        "radiation_msv": 1.0,
        "gravity_factor": 0.38,
        "photoperiod_hours": 24.5,
        "temperature_profile": {"average": -60},
        "humidity_profile": {"average": 10}
    }
    env_resp = await authenticated_client.post("/api/v2/mars/environments", json=env_payload)
    assert env_resp.status_code == 200
    env_id = env_resp.json()["id"]

    # 2. Create Germplasm (using sync session from fixture)
    # We need to ensure the org ID matches test user.
    # test_user fixture creates org "Test Organization".
    org = db_session.query(Organization).filter_by(name="Test Organization").first()
    assert org is not None

    germplasm = Germplasm(
        organization_id=org.id,
        germplasm_name="Test Wheat",
        germplasm_db_id="TEST-MARS-1",
        breeding_method_db_id="BM-1"
    )
    db_session.add(germplasm)
    db_session.commit()
    db_session.refresh(germplasm)

    # 3. Simulate
    sim_payload = {
        "environment_profile_id": env_id,
        "germplasm_id": germplasm.id,
        "generation": 1
    }
    response = await authenticated_client.post("/api/v2/mars/simulate", json=sim_payload)

    if response.status_code != 200:
        # If failure is due to missing germplasm (DB isolation), we might get 500 or 404/422.
        # But we will check.
        print(f"Response: {response.text}")

    # Note: If this fails due to DB splitting (Async vs Sync setup in tests),
    # we might need to skip or mock. But let's try.
    assert response.status_code == 200
    data = response.json()
    assert data["failure_mode"] == "ATMOSPHERIC_COLLAPSE"
