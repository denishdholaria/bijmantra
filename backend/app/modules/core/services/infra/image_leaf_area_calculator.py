import cv2
import numpy as np


class LeafAreaCalculator:
    """
    Service for calculating leaf area from images using computer vision.
    Focuses on robust segmentation using Excess Green (ExG) index and Otsu's thresholding.
    Designed for isolation and minimal dependencies.
    """

    def calculate_leaf_area(self, image_data: bytes) -> dict:
        """
        Calculate leaf area metrics from raw image bytes.

        Args:
            image_data: Raw bytes of the image (JPEG/PNG).

        Returns:
            Dictionary containing:
                - total_area_pixels (int): Total area of detected leaves in pixels.
                - leaf_count (int): Number of distinct leaves detected.
                - average_area_pixels (float): Average area per leaf.
                - contour_areas (list[float]): List of individual leaf areas.
        """
        if not image_data:
            raise ValueError("Empty image data provided")

        try:
            image = self._decode_image(image_data)
            exg = self._calculate_exg(image)
            mask = self._segment_leaf(exg)
            contours = self._find_contours(mask)

            areas = [cv2.contourArea(c) for c in contours]
            total_area = sum(areas)
            count = len(areas)
            average_area = total_area / count if count > 0 else 0.0

            return {
                "total_area_pixels": int(total_area),
                "leaf_count": count,
                "average_area_pixels": float(average_area),
                "contour_areas": [float(a) for a in areas]
            }

        except Exception as e:
            # Re-raise with context or handle specific errors
            raise ValueError(f"Failed to process image: {str(e)}") from e

    def _decode_image(self, image_bytes: bytes) -> np.ndarray:
        """Decodes image bytes into a numpy array (BGR)."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image bytes")
        return image

    def _calculate_exg(self, image: np.ndarray) -> np.ndarray:
        """
        Calculates Excess Green (ExG) index.
        ExG = 2*G - R - B
        Expected input is BGR (default for OpenCV).
        """
        # Convert to float for calculation to avoid overflow/underflow
        img_float = image.astype(np.float32) / 255.0

        # Split channels (OpenCV uses BGR)
        b, g, r = cv2.split(img_float)

        # Calculate ExG: 2*G - R - B
        # Normalize: r = R/(R+G+B), g = G/(R+G+B), b = B/(R+G+B)
        # But standard ExG formula often uses direct intensities or normalized ones.
        # Let's use the normalized approach for robustness against lighting.

        sum_channels = r + g + b
        # Avoid division by zero
        sum_channels[sum_channels == 0] = 0.00001

        r_norm = r / sum_channels
        g_norm = g / sum_channels
        b_norm = b / sum_channels

        exg = 2 * g_norm - r_norm - b_norm

        # Normalize result to 0-255 for thresholding
        exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX)
        return exg_norm.astype(np.uint8)

    def _segment_leaf(self, exg: np.ndarray) -> np.ndarray:
        """Applies Otsu's thresholding to the ExG image."""
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(exg, (5, 5), 0)

        # Otsu's thresholding
        _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel, iterations=2)

        return mask_clean

    def _find_contours(self, mask: np.ndarray) -> list:
        """Finds external contours in the binary mask."""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Filter small noise contours if necessary (e.g., area < 10 pixels)
        valid_contours = [c for c in contours if cv2.contourArea(c) > 50]
        return valid_contours
