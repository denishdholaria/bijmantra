"""
Tests for CropOntologySyncWorker
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.genomics.compute.analytics.crop_ontology_sync_worker import CropOntologySyncWorker
from app.models.phenotyping import ObservationVariable

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client

@pytest.fixture(autouse=True)
async def create_tables(async_db_session: AsyncSession):
    """Ensure ObservationVariable table exists for tests"""
    # Create tables using the async engine associated with the session
    # We use run_sync to execute synchronous metadata.create_all
    # Access the engine from the session
    engine = async_db_session.bind
    async with engine.begin() as conn:
        await conn.run_sync(ObservationVariable.metadata.create_all)
    yield

@pytest.mark.asyncio
async def test_fetch_variables_success(mock_httpx_client):
    """Test successful fetching of variables"""
    worker = CropOntologySyncWorker()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "data": [
                {
                    "observationVariableDbId": "CO_320:0000001",
                    "observationVariableName": "Plant Height"
                }
            ]
        }
    }

    # Setup context manager mock
    mock_instance = mock_httpx_client.return_value
    mock_instance.__aenter__.return_value.get.return_value = mock_response

    variables = await worker.fetch_variables("CO_320")

    assert len(variables) == 1
    assert variables[0]["observationVariableDbId"] == "CO_320:0000001"

@pytest.mark.asyncio
async def test_sync_ontology_creates_new(async_db_session: AsyncSession):
    """Test syncing creates new variables"""
    worker = CropOntologySyncWorker()

    # Mock fetch_variables to avoid external call
    async def mock_fetch(ontology_id):
        return [
            {
                "observationVariableDbId": "CO_320:0000001",
                "observationVariableName": "Plant Height",
                "crop": "Rice",
                "trait": {"traitDbId": "T001", "traitName": "Height"},
                "method": {"methodDbId": "M001", "methodName": "Measuring"},
                "scale": {"scaleDbId": "S001", "scaleName": "cm"},
                "ontologyDbId": "CO_320",
                "ontologyName": "Rice"
            }
        ]

    worker.fetch_variables = mock_fetch

    # Use a dummy organization ID
    org_id = 1

    # We need to ensure there are no existing vars
    stmt = select(ObservationVariable).where(ObservationVariable.observation_variable_db_id == "CO_320:0000001")
    result = await async_db_session.execute(stmt)
    assert result.scalar_one_or_none() is None

    result = await worker.sync_ontology("CO_320", org_id, async_db_session)

    assert result["created"] == 1
    assert result["updated"] == 0

    # Verify DB
    stmt = select(ObservationVariable).where(ObservationVariable.observation_variable_db_id == "CO_320:0000001")
    db_result = await async_db_session.execute(stmt)
    var = db_result.scalar_one_or_none()

    assert var is not None
    assert var.observation_variable_name == "Plant Height"
    assert var.organization_id == org_id
    assert var.trait_name == "Height"

@pytest.mark.asyncio
async def test_sync_ontology_updates_existing(async_db_session: AsyncSession):
    """Test syncing updates existing variables"""
    org_id = 1

    # Create existing variable
    existing_var = ObservationVariable(
        organization_id=org_id,
        observation_variable_db_id="CO_320:0000002",
        observation_variable_name="Old Name",
        trait_name="Old Trait"
    )
    async_db_session.add(existing_var)
    await async_db_session.commit()

    worker = CropOntologySyncWorker()

    async def mock_fetch(ontology_id):
        return [
            {
                "observationVariableDbId": "CO_320:0000002",
                "observationVariableName": "New Name", # Changed
                "crop": "Rice",
                "trait": {"traitDbId": "T002", "traitName": "New Trait"}, # Changed
                "method": {},
                "scale": {},
                "ontologyDbId": "CO_320"
            }
        ]

    worker.fetch_variables = mock_fetch

    result = await worker.sync_ontology("CO_320", org_id, async_db_session)

    assert result["created"] == 0
    assert result["updated"] == 1

    # Verify DB update
    # Need to refresh or re-query
    stmt = select(ObservationVariable).where(ObservationVariable.observation_variable_db_id == "CO_320:0000002")
    db_result = await async_db_session.execute(stmt)
    var = db_result.scalar_one_or_none()

    assert var.observation_variable_name == "New Name"
    assert var.trait_name == "New Trait"

@pytest.mark.asyncio
async def test_sync_ontology_api_error(async_db_session: AsyncSession):
    """Test syncing handles API error gracefully"""
    worker = CropOntologySyncWorker()

    # Mock fetch_variables to raise exception
    async def mock_fetch_error(ontology_id):
        raise Exception("API Error")

    worker.fetch_variables = mock_fetch_error

    result = await worker.sync_ontology("CO_320", 1, async_db_session)

    assert result["errors"] == 1
    assert result["created"] == 0
