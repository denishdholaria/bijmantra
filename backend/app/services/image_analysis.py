
"""
Image Analysis Service

Core engine for phenotyping from images.
Focus: Vegetation Indices, Segmentation, Coverage Metrics.
"""

import numpy as np
import cv2
from typing import Tuple, Dict, Any, List

class ImageAnalysisService:
    
    def calculate_vegetation_indices(self, image_rgb: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate common vegetation indices from RGB image.
        Assumes image is uint8 (0-255).
        Returns float32 indices.
        """
        # Normalize to 0-1 for stability
        img = image_rgb.astype(np.float32) / 255.0
        r, g, b = img[:,:,0], img[:,:,1], img[:,:,2]
        
        # Avoid division by zero
        denom = r + g + b
        denom[denom == 0] = 0.00001
        
        # Normalized coordinates
        r_n = r / denom
        g_n = g / denom
        b_n = b / denom
        
        # Excess Green (ExG) = 2g - r - b
        exg = 2 * g_n - r_n - b_n
        
        # Excess Red (ExR) = 1.4r - g
        exr = 1.4 * r_n - g_n
        
        # Visible Atmospherically Resistant Index (VARI) = (G - R) / (G + R - B)
        vari_denom = g + r - b
        vari_denom[vari_denom == 0] = 0.00001
        vari = (g - r) / vari_denom
        
        return {
            "exg": exg,
            "exr": exr,
            "vari": vari,
            "r_n": r_n,
            "g_n": g_n,
            "b_n": b_n
        }

    def segment_plants(self, image_rgb: np.ndarray, method: str = "exg_otsu") -> np.ndarray:
        """
        Segment plants from background.
        Returns binary mask (0 = background, 255 = plant).
        """
        if method == "exg_otsu":
            indices = self.calculate_vegetation_indices(image_rgb)
            exg = indices["exg"]
            
            # Normalize ExG to 0-255 for Otsu
            exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            
            # Otsu's thresholding
            _, mask = cv2.threshold(exg_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return mask
            
        elif method == "hsv_green":
            hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
            # Define range of green color in HSV
            lower_green = np.array([30, 40, 40])
            upper_green = np.array([90, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)
            return mask
            
        else:
            raise ValueError(f"Unknown segmentation method: {method}")

    def extract_plot_metrics(self, image_rgb: np.ndarray, mask: np.ndarray = None) -> Dict[str, float]:
        """
        Calculate metrics for strict plot region.
        If mask is not provided, computes it using default method.
        """
        if mask is None:
            mask = self.segment_plants(image_rgb)
            
        # Coverage
        total_pixels = mask.size
        plant_pixels = cv2.countNonZero(mask)
        coverage_pct = (plant_pixels / total_pixels) * 100.0
        
        # Indices Stats (only on plant pixels)
        indices = self.calculate_vegetation_indices(image_rgb)
        
        stats = {
            "canopy_coverage_percent": float(coverage_pct),
        }
        
        # Mean index values for plant pixels
        bool_mask = mask > 0
        if plant_pixels > 0:
            stats["mean_exg"] = float(np.mean(indices["exg"][bool_mask]))
            stats["mean_vari"] = float(np.mean(indices["vari"][bool_mask]))
        else:
            stats["mean_exg"] = 0.0
            stats["mean_vari"] = 0.0
            
        return stats

    def crop_plots(self, image_rgb: np.ndarray, grid: Dict[str, Any]) -> List[np.ndarray]:
        """
        Crop image into individual plots based on grid layout.
        grid format: { "rows": 10, "cols": 5, "margin": 10 }
        Returns list of cropped images.
        """
        rows = grid.get("rows", 1)
        cols = grid.get("cols", 1)
        margin = grid.get("margin", 0)
        
        height, width, _ = image_rgb.shape
        
        plot_height = height // rows
        plot_width = width // cols
        
        crops = []
        
        for r in range(rows):
            for c in range(cols):
                y1 = r * plot_height + margin
                y2 = (r + 1) * plot_height - margin
                x1 = c * plot_width + margin
                x2 = (c + 1) * plot_width - margin
                
                # Boundary checks
                if y2 > height: y2 = height
                if x2 > width: x2 = width
                
                if y2 > y1 and x2 > x1:
                    crop = image_rgb[y1:y2, x1:x2]
                    crops.append(crop)
                    
        return crops

image_analysis_service = ImageAnalysisService()
