import pytest
import sys
import os

# Ensure backend is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../backend')))

from app.services.analytics.cold_storage_3d_mapper import ColdStorage3DMapper, StorageUnitType, StorageNode

class TestColdStorage3DMapper:

    @pytest.fixture
    def mapper(self):
        config = {
            "warehouse": {"width": 1000, "height": 500, "depth": 1000},
            "rack": {"width": 100, "height": 200, "depth": 50, "shelves": 5},
            "shelf": {"height": 40},
            "box": {"width": 20, "height": 15, "depth": 30},
            "aisle_width": 150,
            "rack_spacing": 20
        }
        return ColdStorage3DMapper(config)

    def test_parse_location_code(self, mapper):
        code = "WH1-R2-S3-B4"
        parsed = mapper.parse_location_code(code)

        assert len(parsed) == 4
        assert parsed[0]['type'] == StorageUnitType.WAREHOUSE
        assert parsed[0]['id'] == 'WH1'
        assert parsed[0]['index'] == 1

        assert parsed[1]['type'] == StorageUnitType.RACK
        assert parsed[1]['id'] == 'R2'
        assert parsed[1]['index'] == 2

        assert parsed[2]['type'] == StorageUnitType.SHELF
        assert parsed[2]['id'] == 'S3'
        assert parsed[2]['index'] == 3

        assert parsed[3]['type'] == StorageUnitType.BOX
        assert parsed[3]['id'] == 'B4'
        assert parsed[3]['index'] == 4

    def test_calculate_coordinates_rack(self, mapper):
        # Test Rack 1
        node = mapper.build_node({'type': StorageUnitType.RACK, 'id': 'R1', 'index': 1})
        assert node.local_coordinates.x == 0

        # Test Rack 2
        # width 100 + spacing 20 = 120
        node = mapper.build_node({'type': StorageUnitType.RACK, 'id': 'R2', 'index': 2})
        assert node.local_coordinates.x == 120

    def test_calculate_coordinates_shelf(self, mapper):
        # Test Shelf 1
        node = mapper.build_node({'type': StorageUnitType.SHELF, 'id': 'S1', 'index': 1})
        assert node.local_coordinates.y == 0

        # Test Shelf 2 (height 40)
        node = mapper.build_node({'type': StorageUnitType.SHELF, 'id': 'S2', 'index': 2})
        assert node.local_coordinates.y == 40

    def test_build_full_hierarchy(self, mapper):
        codes = ["WH1-R1-S1-B1", "WH1-R1-S1-B2", "WH1-R2-S1-B1"]
        root = mapper.build_full_hierarchy(codes)

        assert root.type == StorageUnitType.WAREHOUSE
        assert len(root.children) == 1 # WH1

        wh = root.children[0]
        assert wh.id == "WH1"
        assert len(wh.children) == 2 # R1, R2

        r1 = next(c for c in wh.children if c.id == "R1")
        assert len(r1.children) == 1 # S1

        s1 = r1.children[0]
        assert len(s1.children) == 2 # B1, B2

        r2 = next(c for c in wh.children if c.id == "R2")
        assert len(r2.children) == 1 # S1

    def test_coordinates_nesting(self, mapper):
        # WH1 -> R2 -> S3 -> B4
        # R2 x = 120
        # S3 y = 80
        # B4 x = 60 (3 * 20)

        codes = ["WH1-R2-S3-B4"]
        root = mapper.build_full_hierarchy(codes)

        wh = root.children[0] # WH1
        r2 = wh.children[0] # R2
        s3 = r2.children[0] # S3
        b4 = s3.children[0] # B4

        # Check relative coordinates
        assert r2.local_coordinates.x == 120
        assert s3.local_coordinates.y == 80
        assert b4.local_coordinates.x == 60

        # Check global coordinates (accumulated)
        # WH1 local is 0
        # R2 global x = WH1.x + R2.x = 0 + 120 = 120
        # S3 global y = WH1.y + R2.y + S3.y = 0 + 0 + 80 = 80
        # B4 global x = WH1.x + R2.x + S3.x + B4.x = 0 + 120 + 0 + 60 = 180

        assert b4.global_coordinates.x == 180
        assert b4.global_coordinates.y == 80
