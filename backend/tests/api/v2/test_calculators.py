import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# Mark as integration test
pytestmark = pytest.mark.asyncio

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

async def test_fertilizer_calculator(client: AsyncClient):
    response = await client.post(
        "/api/v2/calculators/fertilizer",
        json={
            "crop": "wheat",
            "area": 1.0,
            "target_yield": 4.0,
            "soil_n": 0.0,
            "soil_p": 0.0,
            "soil_k": 0.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["urea"] > 0
    assert data["dap"] > 0
    assert data["mop"] > 0
    assert data["total_cost"] > 0

    # Test with soil supply covering needs
    response = await client.post(
        "/api/v2/calculators/fertilizer",
        json={
            "crop": "wheat",
            "area": 1.0,
            "target_yield": 4.0,
            "soil_n": 1000.0, # High N
            "soil_p": 1000.0, # High P
            "soil_k": 1000.0  # High K
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["urea"] == 0
    assert data["dap"] == 0
    assert data["mop"] == 0

async def test_trait_calculator(client: AsyncClient):
    # Harvest Index
    response = await client.post(
        "/api/v2/calculators/traits",
        json={
            "formula_id": "harvest-index",
            "inputs": [50.0, 100.0]
        }
    )
    assert response.status_code == 200
    assert response.json()["result"] == 50.0
    assert response.json()["unit"] == "%"

    # Invalid formula
    response = await client.post(
        "/api/v2/calculators/traits",
        json={
            "formula_id": "invalid-id",
            "inputs": [1.0]
        }
    )
    assert response.status_code == 400

async def test_yield_interpolation(client: AsyncClient):
    # Valid points
    points = [
        {"x": 0, "y": 0, "value": 1},
        {"x": 10, "y": 0, "value": 2},
        {"x": 0, "y": 10, "value": 3},
        {"x": 10, "y": 10, "value": 4}
    ]
    response = await client.post(
        "/api/v2/calculators/yield/interpolation",
        json={"points": points, "resolution": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert "grid_z" in data
    assert len(data["grid_z"]) == 10

    # Too few points
    response = await client.post(
        "/api/v2/calculators/yield/interpolation",
        json={"points": [{"x":0,"y":0,"value":0}]}
    )
    assert response.status_code == 422

async def test_growth_prediction(client: AsyncClient):
    from datetime import date, timedelta
    planting_date = (date.today() - timedelta(days=50)).isoformat()

    response = await client.post(
        "/api/v2/calculators/growth",
        json={
            "crop": "corn",
            "planting_date": planting_date,
            "current_gdd": 500.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "current_stage" in data
    assert data["progress"] > 0

async def test_allocation_calculator(client: AsyncClient):
    response = await client.post(
        "/api/v2/calculators/allocation",
        json={
            "total_budget": 1000.0,
            "categories": [
                {"name": "Fixed", "amount": 200.0},
                {"name": "Variable A", "weight": 1.0},
                {"name": "Variable B", "weight": 3.0}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    allocs = {item["name"]: item for item in data["allocations"]}

    assert allocs["Fixed"]["amount"] == 200.0
    # Remaining 800 divided by 1:3 ratio -> 200:600
    assert allocs["Variable A"]["amount"] == 200.0
    assert allocs["Variable B"]["amount"] == 600.0

async def test_cost_calculator(client: AsyncClient):
    # Simple ROI
    response = await client.post(
        "/api/v2/calculators/cost/roi",
        json={
            "total_cost": 1000.0,
            "expected_revenue": 1500.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["roi_percent"] == 50.0 # (500/1000)*100
    assert data["benefit_cost_ratio"] == 1.5

    # With NPV
    response = await client.post(
        "/api/v2/calculators/cost/roi",
        json={
            "total_cost": 1000.0,
            "expected_revenue": 1500.0,
            "initial_investment": 1000.0,
            "cash_flows": [500.0, 500.0, 500.0],
            "discount_rate": 0.1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["net_present_value"] is not None
