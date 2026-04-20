
import pytest
import numpy as np
import cv2
from app.modules.core.services.infra.image_leaf_area_calculator import LeafAreaCalculator

class TestLeafAreaCalculator:

    def setup_method(self):
        self.calculator = LeafAreaCalculator()

    def test_calculate_leaf_area_synthetic(self):
        """
        Test with a synthetic image: a green square on a black background.
        Square size: 100x100 pixels. Area should be 10000.
        """
        # Create a black image
        width, height = 400, 400
        image = np.zeros((height, width, 3), dtype=np.uint8)

        # Draw a green square (BGR: 0, 255, 0)
        # Top-left corner (150, 150), Bottom-right (250, 250) -> 100x100
        cv2.rectangle(image, (150, 150), (250, 250), (0, 255, 0), -1)

        # Encode to bytes (simulate reading from file)
        _, img_encoded = cv2.imencode('.png', image)
        img_bytes = img_encoded.tobytes()

        result = self.calculator.calculate_leaf_area(img_bytes)

        # Area might be slightly off due to compression/decompression or contour approximation
        # But for a perfect square drawn on black, it should be very close.
        expected_area = 100 * 100 # 10000

        # Allow 1% tolerance
        assert abs(result["total_area_pixels"] - expected_area) < (expected_area * 0.01)
        assert result["leaf_count"] == 1
        assert abs(result["average_area_pixels"] - expected_area) < (expected_area * 0.01)

    def test_calculate_leaf_area_multiple_leaves(self):
        """
        Test with two distinct green squares.
        """
        width, height = 500, 500
        image = np.zeros((height, width, 3), dtype=np.uint8)

        # Square 1: 50x50 = 2500 pixels
        cv2.rectangle(image, (50, 50), (100, 100), (0, 255, 0), -1)

        # Square 2: 60x60 = 3600 pixels
        cv2.rectangle(image, (300, 300), (360, 360), (0, 255, 0), -1)

        _, img_encoded = cv2.imencode('.png', image)
        img_bytes = img_encoded.tobytes()

        result = self.calculator.calculate_leaf_area(img_bytes)

        expected_total = 2500 + 3600

        assert result["leaf_count"] == 2
        assert abs(result["total_area_pixels"] - expected_total) < (expected_total * 0.02)

        # Check individual contour areas
        areas = sorted(result["contour_areas"])
        assert len(areas) == 2
        assert abs(areas[0] - 2500) < (2500 * 0.02)
        assert abs(areas[1] - 3600) < (3600 * 0.02)

    def test_invalid_image_data(self):
        """Test with empty or invalid bytes."""
        with pytest.raises(ValueError, match="Empty image data provided"):
            self.calculator.calculate_leaf_area(b"")

        with pytest.raises(ValueError, match="Failed to process image"):
            self.calculator.calculate_leaf_area(b"not an image")

    def test_no_leaves(self):
        """Test with an image containing no green."""
        width, height = 100, 100
        image = np.zeros((height, width, 3), dtype=np.uint8)
        # Make it all blue
        image[:] = (255, 0, 0)

        _, img_encoded = cv2.imencode('.png', image)
        img_bytes = img_encoded.tobytes()

        result = self.calculator.calculate_leaf_area(img_bytes)

        assert result["total_area_pixels"] == 0
        assert result["leaf_count"] == 0
        assert result["average_area_pixels"] == 0.0
