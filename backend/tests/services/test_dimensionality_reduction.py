
import pytest
import numpy as np
import logging
from app.services.dimensionality_reduction import dimensionality_reduction, DimensionalityReductionService

# Setup logger for tests
logger = logging.getLogger(__name__)

# Mock data
@pytest.fixture
def mock_genotypes():
    # Simple 3 individuals x 5 markers
    # Ind 1: 0 0 0 0 0
    # Ind 2: 2 2 2 2 2
    # Ind 3: 1 1 1 1 1 (Heterozygous)
    return [
        [0, 0, 0, 0, 0],
        [2, 2, 2, 2, 2],
        [1, 1, 1, 1, 1]
    ]

@pytest.fixture
def mock_phenotypes():
    # 10 samples, 4 features
    rng = np.random.RandomState(42)
    return rng.rand(10, 4).tolist()

class TestDimensionalityReduction:

    def test_PCA_basic(self, mock_phenotypes):
        """Test basic PCA execution"""
        result = dimensionality_reduction.run_pca(mock_phenotypes, n_components=2)
        
        if "error" in result and "scikit-learn" in result["error"]:
            pytest.skip("scikit-learn not installed")
            
        assert result["method"] == "PCA"
        assert len(result["scores"]) == 10
        assert len(result["scores"][0]) == 2
        assert len(result["variance_explained"]) == 2
        
        # Total variance should be <= 1.0 (though first 2 often < 1)
        assert sum(result["variance_explained"]) <= 1.0 + 1e-9

    def test_PCA_scaling(self):
        """Test scaling effect on PCA"""
        # Data with different scales
        data = [
            [1, 1000],
            [2, 2000],
            [3, 3000],
            [4, 4000]
        ]
        
        # Without scaling, PC1 should be dominated by variable 2
        res_no_scale = dimensionality_reduction.run_pca(data, scale=False)
        if "error" in res_no_scale: pytest.skip("scikit-learn not installed")
        
        # With scaling, contributions should be balanced
        res_scale = dimensionality_reduction.run_pca(data, scale=True)
        
        # Loadings for PC1
        loadings_no_scale = np.abs(res_no_scale["loadings"][0])
        loadings_scale = np.abs(res_scale["loadings"][0])
        
        # In unscaled, var 2 loading should be much larger than var 1
        assert loadings_no_scale[1] > loadings_no_scale[0]
        
        # In scaled, they should be roughly equal (perfect correlation)
        assert np.isclose(loadings_scale[0], loadings_scale[1], atol=0.1)

    def test_UMAP_execution(self, mock_phenotypes):
        """Test UMAP execution (smoke test)"""
        result = dimensionality_reduction.run_umap(mock_phenotypes, n_components=2)
        
        if "error" in result and "umap-learn" in result["error"]:
            logger.warning("Skipping UMAP test: umap-learn not installed")
            return 
            
        assert result["method"] == "UMAP"
        assert len(result["embedding"]) == 10
        assert len(result["embedding"][0]) == 2
    
    def test_distance_euclidean(self):
        """Test Euclidean distance calculation"""
        # Dist(A, B) = sqrt( (0-3)^2 + (4-0)^2 ) = 5
        data = [
            [0, 0],
            [3, 4]
        ]
        res = dimensionality_reduction.compute_distance_matrix(data, method="euclidean")
        matrix = res["matrix"]
        
        assert matrix[0][0] == 0
        assert matrix[1][1] == 0
        assert np.isclose(matrix[0][1], 5.0)
        assert np.isclose(matrix[1][0], 5.0)

    def test_distance_modified_rogers(self, mock_genotypes):
        """Test Modified Rogers Distance"""
        # Ind 1 (all 0) vs Ind 2 (all 2)
        # Freqs: Ind 1 (0.0), Ind 2 (1.0)
        # Diff^2 per locus = (0-1)^2 = 1
        # Sum Diff^2 = 5 loci * 1 = 5
        # d = sqrt(5 / (2 * 5)) = sqrt(0.5) = 0.707...
        
        res = dimensionality_reduction.compute_distance_matrix(mock_genotypes, method="modified_rogers")
        matrix = res["matrix"]
        
        expected = np.sqrt(0.5)
        assert np.isclose(matrix[0][1], expected)
        
        # Ind 1 (0) vs Ind 3 (1 -> 0.5 freq)
        # Diff^2 = (0 - 0.5)^2 = 0.25
        # Sum = 5 * 0.25 = 1.25
        # d = sqrt(1.25 / 10) = sqrt(0.125) = 0.353...
        expected_1_3 = np.sqrt(1.25 / 10)
        assert np.isclose(matrix[0][2], expected_1_3)

    def test_distance_IBS(self, mock_genotypes):
        """Test Identity By State Distance"""
        # IBS Dist = Manhattan / (2 * m)
        # Ind 1 (00000) vs Ind 2 (22222)
        # Diff = |0-2| * 5 = 10
        # Dist = 10 / (2 * 5) = 1.0 (Completely different)
        
        res = dimensionality_reduction.compute_distance_matrix(mock_genotypes, method="identity_by_state")
        matrix = res["matrix"]
        
        assert np.isclose(matrix[0][1], 1.0)
        
        # Ind 1 vs Ind 3 (11111)
        # Diff = |0-1| * 5 = 5
        # Dist = 5 / 10 = 0.5
        assert np.isclose(matrix[0][2], 0.5)

    def test_distance_Nei_edge_case(self):
        """Test Nei distance with identical individuals"""
        data = [[0, 2], [0, 2]] # Identical
        res = dimensionality_reduction.compute_distance_matrix(data, method="nei")
        matrix = res["matrix"]
        
        # Distance should be 0
        assert np.isclose(matrix[0][1], 0.0, atol=1e-7)

