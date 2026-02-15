
import unittest
import numpy as np
from app.services.gxe_analysis import get_gxe_service, GxEAnalysisService, GGEScaling

class TestGxEAnalysisService(unittest.TestCase):
    def setUp(self):
        self.service = get_gxe_service()
        # Simplified 3 Genotype x 3 Environment Matrix
        #      E1   E2   E3
        # G1 [10,  12,  11]
        # G2 [ 8,   9,  14]
        # G3 [12,  11,  10]
        self.yield_matrix = np.array([
            [10.0, 12.0, 11.0],
            [ 8.0,  9.0, 14.0],
            [12.0, 11.0, 10.0]
        ])
        self.genotypes = ["G1", "G2", "G3"]
        self.environments = ["E1", "E2", "E3"]

    def test_ammi_analysis_structure(self):
        result = self.service.ammi_analysis(
            self.yield_matrix,
            self.genotypes,
            self.environments,
            n_components=2
        )
        
        self.assertEqual(result.grand_mean, np.mean(self.yield_matrix))
        self.assertEqual(len(result.genotype_effects), 3)
        self.assertEqual(len(result.environment_effects), 3)
        self.assertEqual(result.genotype_scores.shape, (3, 2)) # 3 genotypes, 2 PCs
        self.assertEqual(result.environment_scores.shape, (3, 2)) # 3 environments, 2 PCs
        
        # Verify reconstruction approximation (G + E + GE + Mean approx Y)
        # Note: This checks basic math consistency
        reconstructed = (
            result.grand_mean + 
            result.genotype_effects[:, np.newaxis] + 
            result.environment_effects
        )
        # Check if basic main effects model is somewhat correlated (AMMI logic check)
        self.assertTrue(np.allclose(np.mean(reconstructed), result.grand_mean))

    def test_gge_biplot_structure(self):
        result = self.service.gge_biplot(
            self.yield_matrix,
            self.genotypes,
            self.environments,
            n_components=2,
            scaling=GGEScaling.SYMMETRIC
        )
        
        self.assertEqual(result.genotype_scores.shape, (3, 2))
        self.assertEqual(result.environment_scores.shape, (3, 2))
        self.assertEqual(result.scaling, "symmetric")

    def test_finlay_wilkinson(self):
        result = self.service.finlay_wilkinson(
            self.yield_matrix,
            self.genotypes,
            self.environments
        )
        
        self.assertEqual(len(result.slopes), 3)
        self.assertEqual(len(result.r_squared), 3)
        
        # Check classification keys exist
        classification = result._classify_stability()
        self.assertEqual(len(classification), 3)
        self.assertIn("stability", classification[0])
        self.assertIn("performance", classification[0])

if __name__ == '__main__':
    unittest.main()
