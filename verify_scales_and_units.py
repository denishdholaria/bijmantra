import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Add backend to path so we can import 'app' directly
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.main import app
from app.api.deps import get_db

async def mock_get_db():
    yield AsyncMock()

app.dependency_overrides[get_db] = mock_get_db

client = TestClient(app)

class MockScale:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def verify_scales():
    print("Verifying Scales Endpoints with Mocks...")

    # Mock data
    mock_scale = MockScale(
        id=1,
        organization_id=1,
        scale_db_id="SCALE-001",
        scale_name="Test Scale",
        scale_pui=None,
        data_type="Numerical",
        decimal_places=2,
        valid_values_min=0,
        valid_values_max=100,
        valid_values_categories=None,
        ontology_db_id="ONT-001",
        ontology_name="Test Ontology",
        ontology_version="1.0",
        external_references=[],
        additional_info={}
    )

    # Use the module path as used by the app
    with patch("app.api.brapi.scales.ScalesService") as MockService:
        # Configure mocks
        MockService.create = AsyncMock(return_value=mock_scale)
        MockService.get_all = AsyncMock(return_value=([mock_scale], 1))
        MockService.get_by_id = AsyncMock(return_value=mock_scale)
        MockService.update = AsyncMock(return_value=mock_scale)
        MockService.delete = AsyncMock(return_value=True)

        @app.middleware("http")
        async def add_test_auth(request, call_next):
            request.state.organization_id = 1
            request.state.is_superuser = True
            response = await call_next(request)
            return response

        # 1. CREATE
        new_scale = {
            "scaleName": "Test Scale",
            "dataType": "Numerical",
            "decimalPlaces": 2,
            "validValues": {
                "min": 0,
                "max": 100
            },
            "ontologyReference": {
                "ontologyDbId": "ONT-001",
                "ontologyName": "Test Ontology",
                "version": "1.0"
            }
        }

        print("Testing CREATE...")
        response = client.post("/brapi/v2/scales", json=[new_scale])
        if response.status_code not in [200, 201]:
            print(f"Create failed: {response.status_code} {response.text}")
        else:
            print("Create: Success")
            assert response.json()["result"]["data"][0]["scaleName"] == "Test Scale"

        # 2. READ LIST
        print("Testing LIST...")
        response = client.get("/brapi/v2/scales")
        if response.status_code == 200:
            print("List: Success")
            assert len(response.json()["result"]["data"]) > 0
        else:
            print(f"List failed: {response.status_code}")

        # 3. READ ONE
        print("Testing READ ONE...")
        response = client.get("/brapi/v2/scales/SCALE-001")
        if response.status_code == 200:
            print("Read One: Success")
            assert response.json()["result"]["scaleDbId"] == "SCALE-001"
        else:
            print(f"Read One failed: {response.status_code}")

        # 4. UPDATE
        print("Testing UPDATE...")
        response = client.put("/brapi/v2/scales/SCALE-001", json={"scaleName": "Updated"})
        if response.status_code == 200:
            print("Update: Success")
        else:
            print(f"Update failed: {response.status_code}")

        # 5. DELETE
        print("Testing DELETE...")
        response = client.delete("/brapi/v2/scales/SCALE-001")
        if response.status_code == 200:
            print("Delete: Success")
        else:
            print(f"Delete failed: {response.status_code}")

if __name__ == "__main__":
    verify_scales()
