import pytest
from httpx import AsyncClient


# Tests for NutrientTest
@pytest.mark.asyncio
async def test_create_nutrient_test(client: AsyncClient, normal_user_token_headers):
    data = {
        "field_id": 1,
        "sample_date": "2023-10-01",
        "nitrogen": 10.5,
        "phosphorus": 5.2,
        "potassium": 8.1,
        "ph": 6.5
    }
    response = await client.post("/api/v2/soil/nutrient-tests", json=data, headers=normal_user_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["field_id"] == 1
    assert content["nitrogen"] == 10.5

@pytest.mark.asyncio
async def test_list_nutrient_tests(client: AsyncClient, normal_user_token_headers):
    response = await client.get("/api/v2/soil/nutrient-tests", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Tests for PhysicalProperties
@pytest.mark.asyncio
async def test_create_physical_properties(client: AsyncClient, normal_user_token_headers):
    data = {
        "field_id": 1,
        "date": "2023-10-02",
        "texture_class": "Sandy Loam",
        "bulk_density": 1.2
    }
    response = await client.post("/api/v2/soil/physical-properties", json=data, headers=normal_user_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["texture_class"] == "Sandy Loam"

@pytest.mark.asyncio
async def test_list_physical_properties(client: AsyncClient, normal_user_token_headers):
    response = await client.get("/api/v2/soil/physical-properties", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Tests for MicrobialActivity
@pytest.mark.asyncio
async def test_create_microbial_activity(client: AsyncClient, normal_user_token_headers):
    data = {
        "field_id": 1,
        "date": "2023-10-03",
        "respiration_rate": 25.5
    }
    response = await client.post("/api/v2/soil/microbial-activity", json=data, headers=normal_user_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["respiration_rate"] == 25.5

@pytest.mark.asyncio
async def test_list_microbial_activity(client: AsyncClient, normal_user_token_headers):
    response = await client.get("/api/v2/soil/microbial-activity", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Tests for AmendmentLog
@pytest.mark.asyncio
async def test_create_amendment_log(client: AsyncClient, normal_user_token_headers):
    data = {
        "field_id": 1,
        "date": "2023-10-04",
        "amendment_type": "Compost",
        "amount": 500.0,
        "unit": "kg/ha"
    }
    response = await client.post("/api/v2/soil/amendment-logs", json=data, headers=normal_user_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["amendment_type"] == "Compost"

@pytest.mark.asyncio
async def test_list_amendment_logs(client: AsyncClient, normal_user_token_headers):
    response = await client.get("/api/v2/soil/amendment-logs", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Tests for SoilMap
@pytest.mark.asyncio
async def test_create_soil_map(client: AsyncClient, normal_user_token_headers):
    data = {
        "field_id": 1,
        "date": "2023-10-05",
        "map_type": "pH Map",
        "image_url": "http://example.com/map.png"
    }
    response = await client.post("/api/v2/soil/maps", json=data, headers=normal_user_token_headers)
    assert response.status_code == 201
    content = response.json()
    assert content["map_type"] == "pH Map"

@pytest.mark.asyncio
async def test_list_soil_maps(client: AsyncClient, normal_user_token_headers):
    response = await client.get("/api/v2/soil/maps", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
