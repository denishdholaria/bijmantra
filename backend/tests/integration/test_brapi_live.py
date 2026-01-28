"""
Live integration tests against the official BrAPI Test Server.

These tests verify our BrAPI client works correctly against a real BrAPI v2.1 server.
Server: https://test-server.brapi.org/brapi/v2/

Note: These tests require internet connectivity and may be slower than unit tests.
Mark with @pytest.mark.integration to allow selective running.
"""
import pytest
import httpx
from typing import Any

BRAPI_TEST_SERVER = "https://test-server.brapi.org/brapi/v2"


@pytest.fixture
def brapi_client():
    """Create an httpx client for BrAPI requests."""
    return httpx.AsyncClient(timeout=30.0)


async def brapi_get(client: httpx.AsyncClient, endpoint: str) -> dict[str, Any]:
    """Helper to make BrAPI GET requests and return parsed response."""
    url = f"{BRAPI_TEST_SERVER}/{endpoint}"
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPIServerInfo:
    """Test BrAPI Core - Server Info endpoints."""

    async def test_serverinfo_returns_valid_response(self, brapi_client):
        """Verify /serverinfo returns expected BrAPI structure."""
        data = await brapi_get(brapi_client, "serverinfo")
        
        assert "result" in data
        assert "calls" in data["result"]
        assert "serverName" in data["result"]
        assert len(data["result"]["calls"]) > 0
        
        # Verify server identifies as BrAPI v2
        calls = data["result"]["calls"]
        versions = set()
        for call in calls:
            versions.update(call.get("versions", []))
        assert "2.1" in versions or "2.0" in versions

    async def test_commoncropnames_returns_crops(self, brapi_client):
        """Verify /commoncropnames returns crop list."""
        data = await brapi_get(brapi_client, "commoncropnames")
        
        assert "result" in data
        assert "data" in data["result"]
        # Test server should have demo crops
        assert len(data["result"]["data"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPIPrograms:
    """Test BrAPI Core - Programs endpoints."""

    async def test_programs_list(self, brapi_client):
        """Verify /programs returns program list."""
        data = await brapi_get(brapi_client, "programs")
        
        assert "result" in data
        assert "data" in data["result"]
        programs = data["result"]["data"]
        assert len(programs) > 0
        
        # Verify program structure
        program = programs[0]
        assert "programDbId" in program
        assert "programName" in program

    async def test_programs_pagination(self, brapi_client):
        """Verify pagination works on /programs."""
        data = await brapi_get(brapi_client, "programs?pageSize=2&page=0")
        
        assert "metadata" in data
        assert "pagination" in data["metadata"]
        pagination = data["metadata"]["pagination"]
        assert pagination["pageSize"] == 2
        assert pagination["currentPage"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPIGermplasm:
    """Test BrAPI Germplasm endpoints."""

    async def test_germplasm_list(self, brapi_client):
        """Verify /germplasm returns germplasm list."""
        data = await brapi_get(brapi_client, "germplasm?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]
        germplasm = data["result"]["data"]
        assert len(germplasm) > 0
        
        # Verify germplasm structure
        g = germplasm[0]
        assert "germplasmDbId" in g
        assert "germplasmName" in g

    async def test_germplasm_by_id(self, brapi_client):
        """Verify /germplasm/{id} returns single germplasm."""
        # First get a valid ID
        list_data = await brapi_get(brapi_client, "germplasm?pageSize=1")
        germplasm_id = list_data["result"]["data"][0]["germplasmDbId"]
        
        # Then fetch by ID
        data = await brapi_get(brapi_client, f"germplasm/{germplasm_id}")
        
        assert "result" in data
        assert data["result"]["germplasmDbId"] == germplasm_id


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPIStudies:
    """Test BrAPI Core - Studies endpoints."""

    async def test_studies_list(self, brapi_client):
        """Verify /studies returns study list."""
        data = await brapi_get(brapi_client, "studies?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]
        studies = data["result"]["data"]
        assert len(studies) > 0
        
        # Verify study structure
        study = studies[0]
        assert "studyDbId" in study
        assert "studyName" in study

    async def test_study_by_id(self, brapi_client):
        """Verify /studies/{id} returns single study."""
        # First get a valid ID
        list_data = await brapi_get(brapi_client, "studies?pageSize=1")
        study_id = list_data["result"]["data"][0]["studyDbId"]
        
        # Then fetch by ID
        data = await brapi_get(brapi_client, f"studies/{study_id}")
        
        assert "result" in data
        assert data["result"]["studyDbId"] == study_id


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPITrials:
    """Test BrAPI Core - Trials endpoints."""

    async def test_trials_list(self, brapi_client):
        """Verify /trials returns trial list."""
        data = await brapi_get(brapi_client, "trials?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]
        trials = data["result"]["data"]
        assert len(trials) > 0
        
        # Verify trial structure
        trial = trials[0]
        assert "trialDbId" in trial
        assert "trialName" in trial


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPILocations:
    """Test BrAPI Core - Locations endpoints."""

    async def test_locations_list(self, brapi_client):
        """Verify /locations returns location list."""
        data = await brapi_get(brapi_client, "locations?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]
        locations = data["result"]["data"]
        assert len(locations) > 0
        
        # Verify location structure
        loc = locations[0]
        assert "locationDbId" in loc
        assert "locationName" in loc


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPIPhenotyping:
    """Test BrAPI Phenotyping endpoints."""

    async def test_observations_list(self, brapi_client):
        """Verify /observations returns observation list."""
        data = await brapi_get(brapi_client, "observations?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]

    async def test_variables_list(self, brapi_client):
        """Verify /variables returns observation variables."""
        data = await brapi_get(brapi_client, "variables?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]
        variables = data["result"]["data"]
        assert len(variables) > 0
        
        # Verify variable structure
        var = variables[0]
        assert "observationVariableDbId" in var
        assert "observationVariableName" in var

    async def test_traits_list(self, brapi_client):
        """Verify /traits returns trait list."""
        data = await brapi_get(brapi_client, "traits?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPIGenotyping:
    """Test BrAPI Genotyping endpoints."""

    async def test_samples_list(self, brapi_client):
        """Verify /samples returns sample list."""
        data = await brapi_get(brapi_client, "samples?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]

    async def test_variants_list(self, brapi_client):
        """Verify /variants returns variant list."""
        data = await brapi_get(brapi_client, "variants?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]

    async def test_maps_list(self, brapi_client):
        """Verify /maps returns genome map list."""
        data = await brapi_get(brapi_client, "maps")
        
        assert "result" in data
        assert "data" in data["result"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPISeedlots:
    """Test BrAPI Germplasm - Seedlots endpoints."""

    async def test_seedlots_list(self, brapi_client):
        """Verify /seedlots returns seedlot list."""
        data = await brapi_get(brapi_client, "seedlots?pageSize=5")
        
        assert "result" in data
        assert "data" in data["result"]
        seedlots = data["result"]["data"]
        
        if len(seedlots) > 0:
            # Verify seedlot structure
            sl = seedlots[0]
            assert "seedLotDbId" in sl
            assert "seedLotName" in sl


@pytest.mark.asyncio
@pytest.mark.integration
class TestBrAPIBreedingMethods:
    """Test BrAPI Germplasm - Breeding Methods endpoints."""

    async def test_breedingmethods_list(self, brapi_client):
        """Verify /breedingmethods returns method list."""
        data = await brapi_get(brapi_client, "breedingmethods")
        
        assert "result" in data
        assert "data" in data["result"]
        methods = data["result"]["data"]
        assert len(methods) > 0
        
        # Verify method structure
        method = methods[0]
        assert "breedingMethodDbId" in method
        assert "breedingMethodName" in method
