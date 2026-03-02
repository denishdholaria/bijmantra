import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
from datetime import datetime, timedelta

# Ensure backend is in sys.path so we can import app
sys.path.append(os.path.abspath("backend"))

# Mock 'ee' module before importing the service to avoid ImportError if it's imported at module level
# (Though in this service it's imported inside methods, but good practice if it changes)
mock_ee = MagicMock()
sys.modules["ee"] = mock_ee

from app.services.gee_integration_service import GEEIntegrationService, get_gee_service

class TestGEEIntegrationService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Reset the singleton if needed, though we test instances mostly
        # But get_gee_service uses a global variable
        mock_ee.reset_mock()
        mock_ee.Initialize.side_effect = None

    async def test_authenticate_success(self):
        """Test successful authentication with environment variables."""
        service = GEEIntegrationService()

        with patch.dict(os.environ, {
            'GEE_SERVICE_ACCOUNT_EMAIL': 'test@example.com',
            'GEE_PRIVATE_KEY_PATH': '/path/to/key.json'
        }):
            # We need to ensure 'ee' is mocked and available
            with patch.dict(sys.modules, {'ee': mock_ee}):
                # Reset mock to clear previous calls
                mock_ee.reset_mock()

                result = await service.authenticate()

                self.assertTrue(result)
                self.assertTrue(service._authenticated)
                mock_ee.Initialize.assert_called_once()
                # Check credentials creation
                mock_ee.ServiceAccountCredentials.assert_called_with(
                    email='test@example.com',
                    key_file='/path/to/key.json'
                )

    async def test_authenticate_already_authenticated(self):
        """Test that authenticate returns True immediately if already authenticated."""
        service = GEEIntegrationService()
        service._authenticated = True

        result = await service.authenticate()
        self.assertTrue(result)
        # Should not call os.getenv or ee.Initialize
        # (We can't easily check os.getenv calls unless we mock it,
        # but we can check if it tried to re-initialize if we mock ee)
        mock_ee.Initialize.assert_not_called()

    async def test_authenticate_missing_creds(self):
        """Test authentication fails when credentials are missing."""
        service = GEEIntegrationService()

        with patch.dict(os.environ, {}, clear=True):
            # We need to ensure 'ee' is mocked
            with patch.dict(sys.modules, {'ee': mock_ee}):
                mock_ee.reset_mock()

                result = await service.authenticate()

                self.assertFalse(result)
                self.assertFalse(service._authenticated)
                mock_ee.Initialize.assert_not_called()

    async def test_authenticate_import_error(self):
        """Test authentication fails when ee module cannot be imported."""
        service = GEEIntegrationService()

        # Remove 'ee' from sys.modules to simulate ImportError
        with patch.dict(sys.modules):
            if 'ee' in sys.modules:
                del sys.modules['ee']

            # Also ensure it's not importable from environment (it isn't)
            result = await service.authenticate()

            self.assertFalse(result)
            self.assertFalse(service._authenticated)

    async def test_authenticate_exception(self):
        """Test authentication fails when ee.Initialize raises an exception."""
        service = GEEIntegrationService()

        with patch.dict(os.environ, {
            'GEE_SERVICE_ACCOUNT_EMAIL': 'test@example.com',
            'GEE_PRIVATE_KEY_PATH': '/path/to/key.json'
        }):
            with patch.dict(sys.modules, {'ee': mock_ee}):
                mock_ee.reset_mock()
                mock_ee.Initialize.side_effect = Exception("Auth failed")

                result = await service.authenticate()

                self.assertFalse(result)
                self.assertFalse(service._authenticated)

    async def test_get_soil_carbon_estimate_success(self):
        """Test successful retrieval of soil carbon estimate."""
        service = GEEIntegrationService()
        service._authenticated = True
        service._ee = mock_ee # Inject the mock directly

        # Mock chain for ee calls
        # collection.filterBounds().filterDate().filter().sort()
        mock_collection = MagicMock()
        mock_filtered = MagicMock()
        mock_sorted = MagicMock()

        mock_ee.ImageCollection.return_value = mock_collection
        mock_collection.filterBounds.return_value = mock_collection
        mock_collection.filterDate.return_value = mock_collection
        mock_collection.filter.return_value = mock_collection
        mock_collection.sort.return_value = mock_sorted

        # collection.size().getInfo() returns > 0
        mock_sorted.size.return_value.getInfo.return_value = 1

        # collection.first() returns image
        mock_image = MagicMock()
        mock_sorted.first.return_value = mock_image

        # image.select()... operations
        # The code does complex band math. We just mock the result of reduceRegion().getInfo()
        mock_image.normalizedDifference.return_value = MagicMock()

        # Mock reduceRegion().getInfo() return value
        # values = {'NDVI': 0.5, 'SAVI': 0.3, 'BSI': 0.1, 'Brightness': 1000}
        mock_reduce_region = MagicMock()
        mock_reduce_region.getInfo.return_value = {
            'NDVI': 0.5,
            'SAVI': 0.3,
            'BSI': 0.1,
            'Brightness': 1000
        }

        # The code creates 'indices' image via ee.Image.cat
        mock_indices = MagicMock()
        mock_ee.Image.cat.return_value = mock_indices
        mock_indices.reduceRegion.return_value = mock_reduce_region

        # Mock image.getInfo() for metadata
        mock_image.getInfo.return_value = {
            'id': 'test_image_id',
            'properties': {
                'CLOUDY_PIXEL_PERCENTAGE': 5.0,
                'system:time_start': '2023-01-01'
            }
        }

        # Run test
        result = await service.get_soil_carbon_estimate(
            latitude=10.0,
            longitude=20.0,
            date=datetime(2023, 1, 1)
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['image_id'], 'test_image_id')
        self.assertEqual(result['cloud_cover'], 5.0)
        # Check SOC calculation
        # 1.5 + 2.0*0.5 + 1.5*0.3 - 1.0*0.1 + 0.001*1000
        # 1.5 + 1.0 + 0.45 - 0.1 + 1.0 = 3.85
        self.assertAlmostEqual(result['soc_estimate'], 3.85, places=2)

    async def test_get_soil_carbon_estimate_no_images(self):
        """Test soil carbon estimate when no images are found."""
        service = GEEIntegrationService()
        service._authenticated = True
        service._ee = mock_ee

        mock_collection = MagicMock()
        mock_sorted = MagicMock()

        mock_ee.ImageCollection.return_value = mock_collection
        mock_collection.filterBounds.return_value = mock_collection
        mock_collection.filterDate.return_value = mock_collection
        mock_collection.filter.return_value = mock_collection
        mock_collection.sort.return_value = mock_sorted

        # collection.size().getInfo() returns 0
        mock_sorted.size.return_value.getInfo.return_value = 0

        result = await service.get_soil_carbon_estimate(
            latitude=10.0,
            longitude=20.0,
            date=datetime(2023, 1, 1)
        )

        self.assertIsNone(result)

    async def test_get_soil_carbon_estimate_no_auth(self):
        """Test soil carbon estimate returns None when authentication fails."""
        service = GEEIntegrationService()
        # Mock authenticate to return False
        with patch.object(service, 'authenticate', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = False

            result = await service.get_soil_carbon_estimate(
                latitude=10.0,
                longitude=20.0,
                date=datetime(2023, 1, 1)
            )

            self.assertIsNone(result)

    async def test_get_ndvi_time_series_success(self):
        """Test successful retrieval of NDVI time series."""
        service = GEEIntegrationService()
        service._authenticated = True
        service._ee = mock_ee

        mock_collection = MagicMock()
        mock_ee.ImageCollection.return_value = mock_collection
        mock_collection.filterBounds.return_value = mock_collection
        mock_collection.filterDate.return_value = mock_collection
        mock_collection.filter.return_value = mock_collection

        # collection.map(...) returns collection
        mock_mapped_collection = MagicMock()
        mock_collection.map.return_value = mock_mapped_collection

        # Second map (extract_values) and getInfo()
        mock_features = MagicMock()
        mock_mapped_collection.map.return_value = mock_features

        # Mock getInfo() return value
        mock_features.getInfo.return_value = {
            'features': [
                {
                    'properties': {
                        'date': '2023-01-01',
                        'ndvi': 0.6,
                        'evi': 0.4,
                        'cloud_cover': 10.0,
                        'image_id': 'img1'
                    }
                },
                {
                    'properties': {
                        'date': '2023-01-05',
                        'ndvi': 0.7,
                        'evi': 0.5,
                        'cloud_cover': 5.0,
                        'image_id': 'img2'
                    }
                }
            ]
        }

        result = await service.get_ndvi_time_series(
            latitude=10.0,
            longitude=20.0,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31)
        )

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['date'], '2023-01-01')
        self.assertEqual(result[0]['ndvi'], 0.6)
        self.assertEqual(result[1]['date'], '2023-01-05')
        self.assertEqual(result[1]['ndvi'], 0.7)

    async def test_calculate_vegetation_carbon_success(self):
        """Test vegetation carbon calculation with generic crop."""
        service = GEEIntegrationService()
        service._authenticated = True

        # Mock get_ndvi_time_series on the instance
        with patch.object(service, 'get_ndvi_time_series', new_callable=AsyncMock) as mock_get_ndvi:
            mock_get_ndvi.return_value = [
                {'date': '2023-01-01', 'ndvi': 0.8, 'image_id': 'img1'},
                {'date': '2023-01-15', 'ndvi': 0.6, 'image_id': 'img2'} # Closest to 2023-01-10?
            ]

            # Target date 2023-01-10. Closest is 2023-01-15 (5 days diff) vs 2023-01-01 (9 days diff)
            target_date = datetime(2023, 1, 10)

            result = await service.calculate_vegetation_carbon(
                latitude=10.0,
                longitude=20.0,
                date=target_date,
                crop_type='generic'
            )

            self.assertIsNotNone(result)
            self.assertEqual(result['ndvi'], 0.6) # Should pick closest date
            self.assertEqual(result['image_id'], 'img2')

            # Generic model: 1000 * (0.6 - 0.1) / 0.7 = 1000 * 0.5 / 0.7 = 714.28 kg/ha = 0.714 t/ha
            # Carbon = 0.714 * 0.45 = 0.32 t/ha
            self.assertAlmostEqual(result['biomass'], 0.71, places=2)
            self.assertAlmostEqual(result['vegetation_carbon'], 0.32, places=2)

    async def test_calculate_vegetation_carbon_crops(self):
        """Test vegetation carbon calculation with specific crops."""
        service = GEEIntegrationService()
        service._authenticated = True

        with patch.object(service, 'get_ndvi_time_series', new_callable=AsyncMock) as mock_get_ndvi:
            mock_get_ndvi.return_value = [{'date': '2023-01-01', 'ndvi': 0.5, 'image_id': 'img1'}]

            # Maize: 18000 * NDVI^2 = 18000 * 0.25 = 4500 kg/ha = 4.5 t/ha
            # Carbon = 4.5 * 0.45 = 2.025 t/ha
            # Python's round(2.025, 2) -> 2.02 (Banker's rounding to nearest even number)
            result = await service.calculate_vegetation_carbon(
                latitude=10.0,
                longitude=20.0,
                date=datetime(2023, 1, 1),
                crop_type='maize'
            )

            self.assertIsNotNone(result)
            self.assertEqual(result['biomass'], 4.5)
            self.assertEqual(result['vegetation_carbon'], 2.02)

    async def test_get_climate_data_success(self):
        """Test successful retrieval of climate data."""
        service = GEEIntegrationService()
        service._authenticated = True
        service._ee = mock_ee

        mock_collection = MagicMock()
        mock_ee.ImageCollection.return_value = mock_collection
        mock_collection.filterBounds.return_value = mock_collection
        mock_collection.filterDate.return_value = mock_collection

        mock_stats = MagicMock()
        mock_collection.select.return_value.reduce.return_value.reduceRegion.return_value = mock_stats

        mock_stats.getInfo.return_value = {
            'mean_2m_air_temperature_mean': 293.15, # 20 C
            'total_precipitation_mean': 0.05,
            'surface_solar_radiation_downwards_mean': 15000000
        }

        result = await service.get_climate_data(
            latitude=10.0,
            longitude=20.0,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 2)
        )

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['mean_temperature_c'], 20.0, places=1)
        self.assertEqual(result['total_precipitation_m'], 0.05)

if __name__ == '__main__':
    unittest.main()
