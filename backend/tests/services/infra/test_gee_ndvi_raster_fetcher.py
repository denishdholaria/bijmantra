import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add backend to path to allow importing app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from app.modules.core.services.infra.gee_ndvi_raster_fetcher import (
    GEENDVIRasterFetcher,
    NDVIRasterRequest,
    NDVIRasterResponse
)

class TestGEENDVIRasterFetcher(unittest.TestCase):

    def setUp(self):
        self.fetcher = GEENDVIRasterFetcher()
        self.mock_ee = MagicMock()

    @patch.dict(os.environ, {
        'GEE_SERVICE_ACCOUNT_EMAIL': 'test@example.com',
        'GEE_PRIVATE_KEY_PATH': '/path/to/key.json'
    })
    def test_authenticate_success(self):
        with patch.dict(sys.modules, {'ee': self.mock_ee}):
            result = self.fetcher.authenticate()
            self.assertTrue(result)
            self.assertTrue(self.fetcher._authenticated)
            self.mock_ee.Initialize.assert_called_once()
            self.assertEqual(self.fetcher._ee, self.mock_ee)

    @patch.dict(os.environ, {}, clear=True)
    def test_authenticate_failure_no_creds(self):
        # Ensure env vars are cleared
        with patch.dict(sys.modules, {'ee': self.mock_ee}):
            result = self.fetcher.authenticate()
            self.assertFalse(result)
            self.assertFalse(self.fetcher._authenticated)

    def test_fetch_raster_url_success(self):
        # Mock authentication
        self.fetcher._authenticated = True
        self.fetcher._ee = self.mock_ee

        # Mock request
        request = NDVIRasterRequest(
            geometry={'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
            start_date='2023-01-01',
            end_date='2023-01-31'
        )

        # Mock EE objects and chain
        mock_geom = MagicMock()
        self.mock_ee.Geometry.return_value = mock_geom

        mock_collection = MagicMock()
        self.mock_ee.ImageCollection.return_value = mock_collection

        # Chained calls for filtering
        mock_filtered = MagicMock()
        mock_collection.filterBounds.return_value = mock_filtered
        mock_filtered.filterDate.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered

        # Check size > 0
        mock_filtered.size.return_value.getInfo.return_value = 1

        # Map and select
        mock_ndvi_collection = MagicMock()
        mock_filtered.map.return_value = mock_ndvi_collection
        mock_ndvi_collection.select.return_value = mock_ndvi_collection

        # Composite and clip
        mock_composite = MagicMock()
        mock_ndvi_collection.median.return_value = mock_composite
        mock_clipped = MagicMock()
        mock_composite.clip.return_value = mock_clipped

        # getDownloadURL
        expected_url = "http://example.com/download.tif"
        mock_clipped.getDownloadURL.return_value = expected_url

        # Execute
        response = self.fetcher.fetch_raster_url(request)

        # Verify
        self.assertIsNotNone(response)
        self.assertEqual(response.url, expected_url)
        self.assertEqual(response.start_date, '2023-01-01')
        self.assertEqual(response.end_date, '2023-01-31')
        self.assertEqual(response.scale, 10)
        self.assertEqual(response.crs, 'EPSG:4326')

        # Verify calls
        self.mock_ee.Geometry.assert_called_with(request.geometry)
        self.mock_ee.ImageCollection.assert_called_with('COPERNICUS/S2_SR_HARMONIZED')
        mock_collection.filterBounds.assert_called_with(mock_geom)
        mock_filtered.filterDate.assert_called_with('2023-01-01', '2023-01-31')
        mock_clipped.getDownloadURL.assert_called()

    def test_fetch_raster_url_empty_collection(self):
        # Mock authentication
        self.fetcher._authenticated = True
        self.fetcher._ee = self.mock_ee

        request = NDVIRasterRequest(
            geometry={'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]},
            start_date='2023-01-01',
            end_date='2023-01-31'
        )

        mock_collection = MagicMock()
        self.mock_ee.ImageCollection.return_value = mock_collection
        mock_collection.filterBounds.return_value = mock_collection
        mock_collection.filterDate.return_value = mock_collection
        mock_collection.filter.return_value = mock_collection

        # Size 0
        mock_collection.size.return_value.getInfo.return_value = 0

        response = self.fetcher.fetch_raster_url(request)
        self.assertIsNone(response)

    def test_fetch_raster_url_auth_failure(self):
        # Mock authenticate to fail
        with patch.object(self.fetcher, 'authenticate', return_value=False):
            request = NDVIRasterRequest(
                geometry={'type': 'Polygon', 'coordinates': []},
                start_date='2023-01-01',
                end_date='2023-01-31'
            )
            response = self.fetcher.fetch_raster_url(request)
            self.assertIsNone(response)

if __name__ == '__main__':
    unittest.main()
