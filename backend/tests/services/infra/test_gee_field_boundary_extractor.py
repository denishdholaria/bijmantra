"""
Tests for GEE Field Boundary Extractor using unittest.
"""

import sys
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure app is in path
sys.path.append('backend')

from app.services.infra.gee_field_boundary_extractor import GEEFieldBoundaryExtractor

class TestGEEFieldBoundaryExtractor(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Create mock GEE service
        self.mock_gee_service_patcher = patch('app.services.infra.gee_field_boundary_extractor.get_gee_service')
        self.mock_get_gee_service = self.mock_gee_service_patcher.start()
        self.mock_gee_service = AsyncMock()
        self.mock_gee_service.authenticate.return_value = True
        self.mock_get_gee_service.return_value = self.mock_gee_service

        # Create mock ee module
        self.mock_ee = MagicMock()

        # Setup chain for ImageCollection
        collection = MagicMock()
        collection.filterBounds.return_value = collection
        collection.filterDate.return_value = collection
        collection.filter.return_value = collection
        collection.sort.return_value = collection
        # collection.size().getInfo() is called via asyncio.to_thread
        collection.size.return_value.getInfo.return_value = 1

        image = MagicMock()
        collection.first.return_value = image
        image.clip.return_value = image
        image.select.return_value = image

        # Metadata calls via asyncio.to_thread
        image.id.return_value.getInfo.return_value = "S2/TestImage"
        image.date.return_value.format.return_value.getInfo.return_value = "2023-01-01"

        self.mock_ee.ImageCollection.return_value = collection

        snic = MagicMock()
        self.mock_ee.Algorithms.Image.Segmentation.SNIC.return_value = snic
        snic.select.return_value = snic

        vectors = MagicMock()
        snic.reduceToVectors.return_value = vectors
        # vectors.getInfo() is called via asyncio.to_thread
        vectors.getInfo.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"count": 150, "cluster_id": 1},
                    "geometry": {"type": "Polygon", "coordinates": []}
                }
            ]
        }

    def tearDown(self):
        self.mock_gee_service_patcher.stop()

    async def test_extract_boundaries_success(self):
        extractor = GEEFieldBoundaryExtractor()

        with patch.dict(sys.modules, {'ee': self.mock_ee}):
            result = await extractor.extract_boundaries(
                latitude=10.0,
                longitude=20.0,
                date=datetime(2023, 1, 1)
            )

        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'FeatureCollection')
        self.assertEqual(len(result['features']), 1)

        props = result['features'][0]['properties']
        self.assertEqual(props['image_id'], "S2/TestImage")
        self.assertEqual(props['acquisition_date'], "2023-01-01")
        self.assertEqual(props['area_ha'], 1.5)

    async def test_extract_boundaries_auth_fail(self):
        self.mock_gee_service.authenticate.return_value = False
        extractor = GEEFieldBoundaryExtractor()

        result = await extractor.extract_boundaries(
            latitude=10.0,
            longitude=20.0,
            date=datetime(2023, 1, 1)
        )

        self.assertIsNone(result)

    async def test_extract_boundaries_no_images(self):
        self.mock_ee.ImageCollection.return_value \
            .filterBounds.return_value \
            .filterDate.return_value \
            .filter.return_value \
            .sort.return_value \
            .size.return_value.getInfo.return_value = 0

        extractor = GEEFieldBoundaryExtractor()

        with patch.dict(sys.modules, {'ee': self.mock_ee}):
            result = await extractor.extract_boundaries(
                latitude=10.0,
                longitude=20.0,
                date=datetime(2023, 1, 1)
            )

        self.assertIsNone(result)

    async def test_extract_boundaries_exception(self):
        self.mock_ee.Algorithms.Image.Segmentation.SNIC.side_effect = Exception("GEE Error")

        extractor = GEEFieldBoundaryExtractor()

        with patch.dict(sys.modules, {'ee': self.mock_ee}):
            result = await extractor.extract_boundaries(
                latitude=10.0,
                longitude=20.0,
                date=datetime(2023, 1, 1)
            )

        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
