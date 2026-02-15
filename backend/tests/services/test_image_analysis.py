
import pytest
import numpy as np
import cv2
from app.services.image_analysis import image_analysis_service

class TestImageAnalysis:
    
    def create_synthetic_plant_image(self):
        """
        Create 100x100 RGB image.
        Background: Brown (Soil) -> R=139, G=69, B=19
        Plant: Green Circle -> R=34, G=139, B=34
        """
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Fill with brown (Soil)
        img[:] = [139, 69, 19] # RGB
        
        # Draw green circle (Plant)
        # Center (50, 50), Radius 20
        # Area = pi * 20^2 approx 1256 pixels
        # Total area = 10000
        # Coverage approx 12.5%
        cv2.circle(img, (50, 50), 20, (34, 139, 34), -1)
        
        return img

    def test_vegetation_indices(self):
        img = self.create_synthetic_plant_image()
        indices = image_analysis_service.calculate_vegetation_indices(img)
        
        assert "exg" in indices
        assert "vari" in indices
        
        # Check center pixel (Plant)
        center_exg = indices["exg"][50, 50]
        # Plant: R=34, G=139, B=34. Normalized approx R=0.16, G=0.67, B=0.16
        # ExG = 2*g - r - b = 1.34 - 0.16 - 0.16 = 1.02 (High positive)
        assert center_exg > 0.5
        
        # Check corner pixel (Soil)
        corner_exg = indices["exg"][0, 0]
        # Soil: R=139, G=69, B=19. Norm R=0.61, G=0.30, B=0.08
        # ExG = 0.60 - 0.61 - 0.08 = -0.09 (Negative)
        assert corner_exg < 0

    def test_segmentation(self):
        img = self.create_synthetic_plant_image()
        mask = image_analysis_service.segment_plants(img, method="exg_otsu")
        
        # Center should be plant (255)
        assert mask[50, 50] == 255
        
        # Corner should be bg (0)
        assert mask[0, 0] == 0
        
        # Check area approximation
        plant_pixels = cv2.countNonZero(mask)
        expected = np.pi * 20**2
        # Allow 5% tolerance for rasterization
        assert abs(plant_pixels - expected) < (0.05 * expected)

    def test_metrics(self):
        img = self.create_synthetic_plant_image()
        stats = image_analysis_service.extract_plot_metrics(img)
        
        assert "canopy_coverage_percent" in stats
        assert "mean_exg" in stats
        
        cov = stats["canopy_coverage_percent"]
        expected_cov = (np.pi * 20**2 / 10000) * 100 # approx 12.56
        assert abs(cov - expected_cov) < 1.0

    def test_crop_plots(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 2x2 grid, no margin
        grid = {"rows": 2, "cols": 2, "margin": 0}
        crops = image_analysis_service.crop_plots(img, grid)
        
        assert len(crops) == 4
        assert crops[0].shape == (50, 50, 3)
        
        # 2x2 grid, margin 5
        grid_margin = {"rows": 2, "cols": 2, "margin": 5}
        crops_m = image_analysis_service.crop_plots(img, grid_margin)
        
        assert len(crops_m) == 4
        # Each plot is 50x50. Margin 5 removes 5 from top/bottom/left/right?
        # y1 = 0*50 + 5 = 5. y2 = 1*50 - 5 = 45. Height = 40.
        assert crops_m[0].shape == (40, 40, 3)
