"""
ML Bounding Box Extractor

Service for extracting plot bounding boxes from field images.
Supports multiple strategies:
- Grid-based extraction (for regular plot layouts)
- Contour-based extraction (for irregular plots)
- ML-based extraction (using detection models)
"""

import logging
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from app.modules.phenotyping.services.vision.model_service import vision_model_service

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    x: int
    y: int
    w: int
    h: int
    label: str | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "label": self.label,
            "confidence": self.confidence,
        }


class MLBoundingBoxExtractor:
    """
    Extracts plot bounding boxes from images using various strategies.
    """

    def extract_grid(
        self,
        image_shape: tuple[int, int],
        rows: int,
        cols: int,
        margin: int = 0,
    ) -> list[BoundingBox]:
        """
        Extract bounding boxes based on a regular grid layout.

        Args:
            image_shape: (height, width)
            rows: Number of rows
            cols: Number of columns
            margin: Margin in pixels to shrink each box

        Returns:
            List of BoundingBox objects
        """
        height, width = image_shape
        plot_height = height // rows
        plot_width = width // cols

        boxes = []
        for r in range(rows):
            for c in range(cols):
                y1 = r * plot_height + margin
                x1 = c * plot_width + margin

                # Calculate width and height after margin
                w = plot_width - 2 * margin
                h = plot_height - 2 * margin

                # Boundary checks
                if w <= 0 or h <= 0:
                    continue

                # Ensure we don't go out of bounds
                if y1 + h > height:
                    h = height - y1
                if x1 + w > width:
                    w = width - x1

                boxes.append(BoundingBox(
                    x=x1,
                    y=y1,
                    w=w,
                    h=h,
                    label=f"R{r+1}C{c+1}"
                ))

        return boxes

    def extract_contours(
        self,
        image: np.ndarray,
        min_area: int = 100,
        threshold_method: str = "otsu",
    ) -> list[BoundingBox]:
        """
        Extract bounding boxes using contour detection.

        Args:
            image: Input image (BGR or Grayscale)
            min_area: Minimum area to consider a valid plot
            threshold_method: 'otsu' or 'simple'

        Returns:
            List of BoundingBox objects
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        if threshold_method == "otsu":
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                boxes.append(BoundingBox(
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    label="contour_plot"
                ))

        # Sort by position (top-left to bottom-right)
        boxes.sort(key=lambda b: (b.y, b.x))
        return boxes

    def extract_ml(
        self,
        image: np.ndarray,
        model_id: str,
    ) -> list[BoundingBox]:
        """
        Extract bounding boxes using a machine learning model.

        Args:
            image: Input image
            model_id: ID of the registered model in VisionModelService

        Returns:
            List of BoundingBox objects
        """
        result = vision_model_service.predict(model_id, image)

        if "error" in result:
            logger.error(f"ML extraction failed: {result['error']}")
            return []

        boxes = []
        if result.get("task") == "detection":
            detections = result.get("detections", [])
            for d in detections:
                bbox = d.get("bbox", [])
                if len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    w = x2 - x1
                    h = y2 - y1
                    boxes.append(BoundingBox(
                        x=x1,
                        y=y1,
                        w=w,
                        h=h,
                        label=d.get("class"),
                        confidence=d.get("confidence")
                    ))

        return boxes

    def extract_plots(
        self,
        image: np.ndarray,
        strategy: str = "grid",
        **kwargs
    ) -> list[BoundingBox]:
        """
        Main entry point for plot extraction.

        Args:
            image: Input image
            strategy: 'grid', 'contours', or 'ml'
            **kwargs: Arguments passed to specific extraction methods

        Returns:
            List of BoundingBox objects
        """
        if strategy == "grid":
            rows = kwargs.get("rows", 1)
            cols = kwargs.get("cols", 1)
            margin = kwargs.get("margin", 0)
            return self.extract_grid(image.shape[:2], rows, cols, margin)

        elif strategy == "contours":
            min_area = kwargs.get("min_area", 100)
            threshold_method = kwargs.get("threshold_method", "otsu")
            return self.extract_contours(image, min_area, threshold_method)

        elif strategy == "ml":
            model_id = kwargs.get("model_id")
            if not model_id:
                raise ValueError("model_id is required for ML strategy")
            return self.extract_ml(image, model_id)

        else:
            raise ValueError(f"Unknown strategy: {strategy}")


ml_bounding_box_extractor = MLBoundingBoxExtractor()
