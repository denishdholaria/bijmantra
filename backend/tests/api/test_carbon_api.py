"""
Integration Tests for Carbon Monitoring API

Tests carbon stock CRUD operations and dashboard endpoints with real database.

Test Strategy:
    - Use async test client for FastAPI
    - Use test database with fixtures
    - Test authentication and authorization
    - Test query parameters and filtering
    - Test response structure and validation
    - Clean up test data after each test
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.models.climate import CarbonStock, CarbonMeasurementType


@pytest.fixture
def test_carbon_stock(db_session: Session, test_user) -> CarbonStock:
    """Create test carbon stock record"""
    carbon_stock = CarbonStock(
        organization_id=test_user.organization_id,
        location_id=1,
        measurement_date=date.today(),
        soil_carbon_stock=50.0,
        vegetation_carbon_stock=10.0,
        total_carbon_stock=60.0,
        measurement_depth_cm=30,
        measurement_type=CarbonMeasurementType.FIELD_MEASURED,
        confidence_level=0.9
    )
    
    db_session.add(carbon_stock)
    db_session.commit()
    db_session.refresh(carbon_stock)
    
    yield carbon_stock
    
    # Cleanup
    db_session.delete(carbon_stock)
    db_session.commit()


class TestCarbonStockCRUD:
    """Test carbon stock CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_carbon_stock(self, authenticated_client):
        """Test creating a new carbon stock record"""
        payload = {
            "location_id": 1,
            "measurement_date": date.today().isoformat(),
            "soil_carbon_stock": 45.5,
            "vegetation_carbon_stock": 8.2,
            "measurement_depth_cm": 30,
            "measurement_type": "field_measured",
            "confidence_level": 0.85
        }
        
        response = await authenticated_client.post(
            "/api/v2/carbon/stocks",
            json=payload
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["location_id"] == 1
        assert data["soil_carbon_stock"] == 45.5
        assert data["vegetation_carbon_stock"] == 8.2
        assert data["total_carbon_stock"] == 53.7  # 45.5 + 8.2
        assert data["measurement_depth_cm"] == 30
        assert data["confidence_level"] == 0.85
    
    @pytest.mark.asyncio
    async def test_get_carbon_stocks(self, authenticated_client, test_carbon_stock):
        """Test retrieving carbon stocks"""
        response = await authenticated_client.get("/api/v2/carbon/stocks")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Find our test stock
        test_stock = next((s for s in data if s["id"] == test_carbon_stock.id), None)
        assert test_stock is not None
        assert test_stock["total_carbon_stock"] == 60.0
    
    @pytest.mark.asyncio
    async def test_get_carbon_stock_by_id(self, authenticated_client, test_carbon_stock):
        """Test retrieving a specific carbon stock by ID"""
        response = await authenticated_client.get(
            f"/api/v2/carbon/stocks/{test_carbon_stock.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_carbon_stock.id
        assert data["soil_carbon_stock"] == 50.0
        assert data["vegetation_carbon_stock"] == 10.0
        assert data["total_carbon_stock"] == 60.0
    
    @pytest.mark.asyncio
    async def test_update_carbon_stock(self, authenticated_client, test_carbon_stock):
        """Test updating a carbon stock record"""
        payload = {
            "soil_carbon_stock": 55.0,
            "vegetation_carbon_stock": 12.0,
            "confidence_level": 0.95
        }
        
        response = await authenticated_client.put(
            f"/api/v2/carbon/stocks/{test_carbon_stock.id}",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["soil_carbon_stock"] == 55.0
        assert data["vegetation_carbon_stock"] == 12.0
        assert data["total_carbon_stock"] == 67.0  # 55.0 + 12.0
        assert data["confidence_level"] == 0.95
    
    @pytest.mark.asyncio
    async def test_delete_carbon_stock(self, authenticated_client, test_carbon_stock):
        """Test deleting a carbon stock record"""
        response = await authenticated_client.delete(
            f"/api/v2/carbon/stocks/{test_carbon_stock.id}"
        )
        
        assert response.status_code == 204
        
        # Verify deletion
        response = await authenticated_client.get(
            f"/api/v2/carbon/stocks/{test_carbon_stock.id}"
        )
        
        assert response.status_code == 404


class TestCarbonStockFiltering:
    """Test carbon stock query filtering"""
    
    @pytest.mark.asyncio
    async def test_filter_by_location(self, authenticated_client):
        """Test filtering carbon stocks by location"""
        response = await authenticated_client.get(
            "/api/v2/carbon/stocks?location_id=1"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All results should be for location 1
        for stock in data:
            assert stock["location_id"] == 1
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, authenticated_client):
        """Test filtering carbon stocks by date range"""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        
        response = await authenticated_client.get(
            f"/api/v2/carbon/stocks?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All results should be within date range
        for stock in data:
            stock_date = date.fromisoformat(stock["measurement_date"])
            assert date.fromisoformat(start_date) <= stock_date <= date.fromisoformat(end_date)
    
    @pytest.mark.asyncio
    async def test_filter_by_measurement_type(self, authenticated_client):
        """Test filtering carbon stocks by measurement type"""
        response = await authenticated_client.get(
            "/api/v2/carbon/stocks?measurement_type=field_measured"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All results should be field measured
        for stock in data:
            assert stock["measurement_type"] == "field_measured"


class TestCarbonDashboard:
    """Test carbon dashboard aggregations"""
    
    @pytest.mark.asyncio
    async def test_carbon_dashboard(self, authenticated_client):
        """Test carbon dashboard endpoint"""
        response = await authenticated_client.get("/api/v2/carbon/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check dashboard structure
        assert "total_carbon_stock" in data
        assert "average_carbon_stock" in data
        assert "locations_count" in data
        assert "measurements_count" in data
        assert "recent_measurements" in data
        
        # Check data types
        assert isinstance(data["total_carbon_stock"], (int, float))
        assert isinstance(data["average_carbon_stock"], (int, float))
        assert isinstance(data["locations_count"], int)
        assert isinstance(data["measurements_count"], int)
        assert isinstance(data["recent_measurements"], list)


class TestCarbonTimeSeries:
    """Test carbon time series queries"""
    
    @pytest.mark.asyncio
    async def test_carbon_time_series(self, authenticated_client):
        """Test carbon time series endpoint"""
        start_date = (date.today() - timedelta(days=365)).isoformat()
        end_date = date.today().isoformat()
        
        response = await authenticated_client.get(
            f"/api/v2/carbon/time-series?location_id=1&start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # Check time series structure
        if len(data) > 0:
            point = data[0]
            assert "date" in point
            assert "soil_carbon" in point
            assert "vegetation_carbon" in point
            assert "total_carbon" in point
            assert "measurement_type" in point
            assert "confidence" in point


class TestCarbonValidation:
    """Test carbon stock validation"""
    
    @pytest.mark.asyncio
    async def test_create_without_carbon_values(self, authenticated_client):
        """Test that creating stock without carbon values fails"""
        payload = {
            "location_id": 1,
            "measurement_date": date.today().isoformat(),
            "measurement_depth_cm": 30,
            "measurement_type": "field_measured"
        }
        
        response = await authenticated_client.post(
            "/api/v2/carbon/stocks",
            json=payload
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_with_negative_carbon(self, authenticated_client):
        """Test that negative carbon values are rejected"""
        payload = {
            "location_id": 1,
            "measurement_date": date.today().isoformat(),
            "soil_carbon_stock": -10.0,
            "measurement_depth_cm": 30,
            "measurement_type": "field_measured"
        }
        
        response = await authenticated_client.post(
            "/api/v2/carbon/stocks",
            json=payload
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_with_invalid_confidence(self, authenticated_client):
        """Test that confidence outside 0-1 range is rejected"""
        payload = {
            "location_id": 1,
            "measurement_date": date.today().isoformat(),
            "soil_carbon_stock": 50.0,
            "measurement_depth_cm": 30,
            "measurement_type": "field_measured",
            "confidence_level": 1.5  # Invalid: > 1.0
        }
        
        response = await authenticated_client.post(
            "/api/v2/carbon/stocks",
            json=payload
        )
        
        assert response.status_code == 422  # Validation error


class TestCarbonAuthentication:
    """Test carbon API authentication"""
    
    @pytest.mark.asyncio
    async def test_create_without_auth(self):
        """Test that creating stock without auth fails"""
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        payload = {
            "location_id": 1,
            "measurement_date": date.today().isoformat(),
            "soil_carbon_stock": 50.0,
            "measurement_depth_cm": 30,
            "measurement_type": "field_measured"
        }
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v2/carbon/stocks",
                json=payload
            )
        
            assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.asyncio
    async def test_get_without_auth(self):
        """Test that getting stocks without auth fails"""
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v2/carbon/stocks")
        
            assert response.status_code == 401  # Unauthorized

