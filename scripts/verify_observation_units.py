import asyncio
import uuid
import sys
import os
from unittest.mock import MagicMock

# Mock modules to prevent lifespan startup from hanging
mock_redis = MagicMock()
mock_redis.redis_client.connect.return_value = False
sys.modules['app.core.redis'] = mock_redis

mock_meili = MagicMock()
mock_meili.meilisearch_service.connect.return_value = False
sys.modules['app.core.meilisearch'] = mock_meili

mock_task = MagicMock()
sys.modules['app.services.task_queue'] = mock_task

mock_security = MagicMock()
sys.modules['app.services.redis_security'] = mock_security

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.models.phenotyping import ObservationUnit
from app.models.core import Study, Organization, Program, Trial
from app.models.germplasm import Germplasm

# Disable lifespan
app.router.lifespan_context = None

# Setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

async def init_models():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

async def run_verification():
    print("Initializing test database...")
    await init_models()

    print("Starting AsyncClient...")
    # Using a context manager for AsyncClient triggers the lifespan events.
    async with AsyncClient(transport=None, app=app, base_url="http://test") as ac:
        print("AsyncClient started.")
        print("Seeding data...")
        async with TestingSessionLocal() as session:
            # Create Organization
            org = Organization(name="Test Org")
            session.add(org)
            await session.commit()
            await session.refresh(org)

            # Create Program
            program = Program(
                organization_id=org.id,
                program_name="Test Program",
                program_db_id=f"prog_{uuid.uuid4().hex[:8]}"
            )
            session.add(program)
            await session.commit()
            await session.refresh(program)

            # Create Trial
            trial = Trial(
                organization_id=org.id,
                program_id=program.id,
                trial_name="Test Trial",
                trial_db_id=f"trial_{uuid.uuid4().hex[:8]}"
            )
            session.add(trial)
            await session.commit()
            await session.refresh(trial)

            # Create Study
            study = Study(
                organization_id=org.id,
                trial_id=trial.id,
                study_name="Test Study",
                study_db_id=f"study_{uuid.uuid4().hex[:8]}"
            )
            session.add(study)

            # Create Germplasm
            germplasm = Germplasm(
                organization_id=org.id,
                germplasm_name="Test Germplasm",
                germplasm_db_id=f"germ_{uuid.uuid4().hex[:8]}"
            )
            session.add(germplasm)

            await session.commit()
            await session.refresh(study)
            await session.refresh(germplasm)

            study_id = study.id
            germplasm_id = germplasm.id
            print(f"Seeded: Study ID {study_id}, Germplasm ID {germplasm_id}")

        # 1. Create Observation Unit
        print("\nTesting Create Observation Unit...")
        payload = {
            "observationUnitName": "PLOT-001",
            "studyDbId": str(study_id),
            "germplasmDbId": str(germplasm_id),
            "observationLevel": "plot",
            "positionCoordinateX": "1",
            "positionCoordinateY": "1"
        }
        response = await ac.post("/brapi/v2/observationunits", json=payload)

        print(f"Create Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.json()}")
        assert response.status_code == 200
        data = response.json()["result"]
        unit_db_id = data["observationUnitDbId"]
        assert data["observationUnitName"] == "PLOT-001"
        print(f"Created Unit: {unit_db_id}")

        # 2. Get List
        print("\nTesting List Observation Units...")
        response = await ac.get("/brapi/v2/observationunits")
        print(f"List Response status: {response.status_code}")
        assert response.status_code == 200
        result_data = response.json()["result"]["data"]
        assert len(result_data) >= 1
        print(f"Found {len(result_data)} units")

        # 3. Get Single
        print("\nTesting Get Single Unit...")
        response = await ac.get(f"/brapi/v2/observationunits/{unit_db_id}")
        assert response.status_code == 200
        assert response.json()["result"]["observationUnitName"] == "PLOT-001"
        print("Unit retrieved successfully")

        # 4. Update
        print("\nTesting Update Unit...")
        response = await ac.put(f"/brapi/v2/observationunits/{unit_db_id}", json={
            "observationUnitName": "PLOT-001-UPDATED"
        })
        assert response.status_code == 200
        assert response.json()["result"]["observationUnitName"] == "PLOT-001-UPDATED"
        print("Unit updated successfully")

        print("\nVerification Successful!")

if __name__ == "__main__":
    # Set timeout for asyncio run
    try:
        asyncio.run(asyncio.wait_for(run_verification(), timeout=60))
    except asyncio.TimeoutError:
        print("Timed out!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
