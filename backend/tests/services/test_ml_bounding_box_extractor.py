import cv2
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from app.services.ml_bounding_box_extractor import ml_bounding_box_extractor

class TestMLBoundingBoxExtractor:

    def test_extract_grid(self):
        # 100x100 image, 2 rows, 2 cols -> 50x50 plots
        shape = (100, 100)
        rows = 2
        cols = 2
        margin = 0

        boxes = ml_bounding_box_extractor.extract_grid(shape, rows, cols, margin)

        assert len(boxes) == 4
        # R1C1
        assert boxes[0].x == 0
        assert boxes[0].y == 0
        assert boxes[0].w == 50
        assert boxes[0].h == 50

        # Check margin
        margin = 5
        boxes_m = ml_bounding_box_extractor.extract_grid(shape, rows, cols, margin)
        assert len(boxes_m) == 4
        assert boxes_m[0].x == 5
        assert boxes_m[0].y == 5
        assert boxes_m[0].w == 40
        assert boxes_m[0].h == 40

    def test_extract_contours(self):
        # Create a synthetic image with two white squares on black background
        image = np.zeros((100, 100), dtype=np.uint8)
        # Square 1: (10, 10) to (30, 30), size 20x20
        cv2.rectangle(image, (10, 10), (30, 30), 255, -1)
        # Square 2: (60, 60) to (80, 80), size 20x20
        cv2.rectangle(image, (60, 60), (80, 80), 255, -1)

        boxes = ml_bounding_box_extractor.extract_contours(image, min_area=50)

        assert len(boxes) == 2
        # Check first box (sorted by y, x)
        assert abs(boxes[0].x - 10) <= 1
        assert abs(boxes[0].y - 10) <= 1
        assert abs(boxes[0].w - 21) <= 2  # cv2 boundingRect logic
        assert abs(boxes[0].h - 21) <= 2

    @patch("app.services.ml_bounding_box_extractor.vision_model_service")
    def test_extract_ml(self, mock_vision_service):
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        model_id = "test-model"

        # Mock response
        mock_vision_service.predict.return_value = {
            "task": "detection",
            "detections": [
                {
                    "class": "plot",
                    "confidence": 0.95,
                    "bbox": [10, 10, 50, 50]
                }
            ]
        }

        boxes = ml_bounding_box_extractor.extract_ml(image, model_id)

        assert len(boxes) == 1
        assert boxes[0].x == 10
        assert boxes[0].y == 10
        assert boxes[0].w == 40
        assert boxes[0].h == 40
        assert boxes[0].label == "plot"
        assert boxes[0].confidence == 0.95

    def test_extract_plots_dispatch(self):
        image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Test grid strategy dispatch
        boxes = ml_bounding_box_extractor.extract_plots(image, strategy="grid", rows=2, cols=2)
        assert len(boxes) == 4

        # Test unknown strategy
        with pytest.raises(ValueError, match="Unknown strategy"):
            ml_bounding_box_extractor.extract_plots(image, strategy="invalid")

        # Test missing model_id for ml
        with pytest.raises(ValueError, match="model_id is required"):
            ml_bounding_box_extractor.extract_plots(image, strategy="ml")
