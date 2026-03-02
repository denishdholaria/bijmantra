import pytest
from backend.app.services.environmental_physics import EnvironmentalPhysicsService

# Mock SoilProfile for testing
class MockSoilProfile:
    def __init__(self, theta_sat, theta_res, alpha, n_param):
        self.theta_sat = theta_sat
        self.theta_res = theta_res
        self.alpha = alpha
        self.n_param = n_param

@pytest.fixture
def service():
    return EnvironmentalPhysicsService()

@pytest.mark.asyncio
async def test_calculate_gdd_standard(service):
    """Test GDD calculation where temperatures are above base."""
    # Tmax=30, Tmin=20, Tbase=10
    # Mean = (30 + 20) / 2 = 25
    # GDD = 25 - 10 = 15
    gdd = await service.calculate_gdd(30.0, 20.0, t_base=10.0)
    assert gdd == 15.0

@pytest.mark.asyncio
async def test_calculate_gdd_min_clamped(service):
    """Test GDD calculation where minimum temperature is below base."""
    # Tmax=20, Tmin=5, Tbase=10
    # Tmin clamped to 10
    # Mean = (20 + 10) / 2 = 15
    # GDD = 15 - 10 = 5
    gdd = await service.calculate_gdd(20.0, 5.0, t_base=10.0)
    assert gdd == 5.0

@pytest.mark.asyncio
async def test_calculate_gdd_both_clamped(service):
    """Test GDD calculation where both temperatures are below base."""
    # Tmax=8, Tmin=5, Tbase=10
    # Both clamped to 10
    # Mean = 10
    # GDD = 10 - 10 = 0
    gdd = await service.calculate_gdd(8.0, 5.0, t_base=10.0)
    assert gdd == 0.0

@pytest.mark.asyncio
async def test_calculate_gdd_wheat(service):
    """Test GDD calculation with a different base temperature (0.0)."""
    # Tmax=10, Tmin=5, Tbase=0
    # Mean = 7.5
    # GDD = 7.5 - 0 = 7.5
    gdd = await service.calculate_gdd(10.0, 5.0, t_base=0.0)
    assert gdd == 7.5

@pytest.mark.asyncio
async def test_calculate_ptu(service):
    """Test PTU calculation."""
    # GDD=10, DayLength=12
    # PTU = 10 * 12 = 120
    ptu = await service.calculate_ptu(10.0, 12.0)
    assert ptu == 120.0

@pytest.mark.asyncio
async def test_calculate_soil_moisture_saturation(service):
    """Test soil moisture at saturation (matric potential >= 0)."""
    profile = MockSoilProfile(theta_sat=0.5, theta_res=0.1, alpha=0.01, n_param=2.0)
    theta = await service.calculate_soil_moisture(profile, 0.0)
    assert theta == 0.5

    theta_pos = await service.calculate_soil_moisture(profile, 10.0)
    assert theta_pos == 0.5

@pytest.mark.asyncio
async def test_calculate_soil_moisture_dry(service):
    """Test soil moisture for unsaturated conditions."""
    profile = MockSoilProfile(theta_sat=0.5, theta_res=0.1, alpha=0.01, n_param=2.0)
    # h = 100
    # alpha * h = 1
    # (1 + 1^2) = 2
    # m = 1 - 1/2 = 0.5
    # denominator = 2^0.5 = 1.41421356
    # range = 0.4
    # theta = 0.1 + (0.4 / 1.41421356) = 0.1 + 0.28284271 = 0.38284271

    theta = await service.calculate_soil_moisture(profile, -100.0)
    assert abs(theta - 0.38284271) < 1e-6
