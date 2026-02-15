
import pytest
import numpy as np
import pandas as pd
from app.services.mixed_model import mixed_model_service, MixedModelService
from app.services.phenotype_analysis import PhenotypeAnalysisService, get_phenotype_service

@pytest.fixture
def mock_rcbd_data():
    """Balanced RCBD Data"""
    # 2 Genotypes, 2 Blocks
    return [
        {"genotype": "G1", "block": "B1", "yield": 10.0},
        {"genotype": "G1", "block": "B2", "yield": 12.0},
        {"genotype": "G2", "block": "B1", "yield": 14.0},
        {"genotype": "G2", "block": "B2", "yield": 16.0},
    ]

@pytest.fixture
def mock_multi_env_data():
    """Balanced Multi-Environment Data"""
    # 2 Genotypes, 2 Environments, 2 Reps (8 obs)
    data = []
    # Genotype means: G1=10, G2=20 (diff=10)
    # Env means: E1=15, E2=15 (diff=0)
    # GxE: G1 in E1=8 (low), G1 in E2=12 (high) -> means 10
    #      G2 in E1=22 (high), G2 in E2=18 (low) -> means 20
    # Interaction: specific adaptability
    
    # E1
    data.append({"genotype": "G1", "env": "E1", "rep": 1, "value": 8.0}) # G1E1 = 8
    data.append({"genotype": "G1", "env": "E1", "rep": 2, "value": 8.0})
    data.append({"genotype": "G2", "env": "E1", "rep": 1, "value": 22.0}) # G2E1 = 22
    data.append({"genotype": "G2", "env": "E1", "rep": 2, "value": 22.0})
    
    # E2
    data.append({"genotype": "G1", "env": "E2", "rep": 1, "value": 12.0}) # G1E2 = 12
    data.append({"genotype": "G1", "env": "E2", "rep": 2, "value": 12.0})
    data.append({"genotype": "G2", "env": "E2", "rep": 1, "value": 18.0}) # G2E2 = 18
    data.append({"genotype": "G2", "env": "E2", "rep": 2, "value": 18.0})
    
    return data

class TestMixedModelService:
    def test_custom_formula_parsing(self, mock_rcbd_data):
        """Test custom formula parser without patsy"""
        # Force fallback if patsy exists (by mocking or calling private method)
        df = pd.DataFrame(mock_rcbd_data)
        
        # Formula: yield ~ genotype + (1|block)
        y, X, Z = mixed_model_service._parse_formula_custom("yield ~ genotype + (1|block)", df)
        
        # Check y
        assert y.shape == (4, 1)
        assert y.iloc[0, 0] == 10.0
        
        # Check X (Fixed: Intercept + Genotype)
        # G1 is reference (alphabetical)?
        # 1 + G2
        assert "Intercept" in X.columns
        assert "genotype_G2" in X.columns or "genotype_G1" in X.columns
        assert X.shape == (4, 2)
        
        # Check Z (Random: Block)
        # Block has B1, B2
        assert "block_B1" in Z.columns
        assert "block_B2" in Z.columns
        assert Z.shape == (4, 2)

    def test_solve_mme_sanity(self, mock_rcbd_data):
        """Test MME solver runs and returns reasonable shapes"""
        # This is an integration test invoking `compute_engine` 
        # which might not have fortran compiled, so it uses numpy fallback.
        
        # We need to ensure compute_engine uses numpy fallback correctly
        # The solver requires inverting matrices.
        
        df = pd.DataFrame(mock_rcbd_data)
        y, X, Z = mixed_model_service.parse_formula("yield ~ genotype + (1|block)", df)
        
        try:
            result = mixed_model_service.solve_mme(y, X, Z)
            
            assert "fixed_effects" in result
            assert "random_effects" in result
            assert "variance_components" in result
            
            # Check convergence
            # Numpy fallback usually iterates or returns 1-step if just BLUP
            # result["converged"] might be boolean
            
            # Check fixed effects size
            assert len(result["fixed_effects"]) == 2 # Intercept + G2
            
            # Check random effects size
            assert len(result["random_effects"]) == 2 # B1, B2
            
        except ImportError:
            pytest.skip("Compute engine dependencies missing")
        except Exception as e:
            pytest.fail(f"MME Solver failed: {e}")

class TestPhenotypeAnalysisMultiEnv:
    def test_heritability_multi_env(self, mock_multi_env_data):
        service = get_phenotype_service()
        
        # Run analysis
        res = service.estimate_heritability_multi_env(
            mock_multi_env_data, 
            trait="yield", 
            genotype_col="genotype", 
            env_col="env"
        )
        
        # Check structure
        assert res.trait == "yield"
        assert res.vg >= 0
        assert res.ve >= 0
        
        # Calculation verification
        # Grand Mean = (8*2 + 22*2 + 12*2 + 18*2) / 8 = (16+44+24+36)/8 = 120/8 = 15
        
        # Geno Means: G1=(8+8+12+12)/4=10, G2=(22+22+18+18)/4=20
        # SS_G = r*e * sum((g - mean)^2) = 2*2 * [ (10-15)^2 + (20-15)^2 ]
        #      = 4 * [25 + 25] = 200
        # MS_G = 200 / (2-1) = 200
        
        # Env Means: E1=(8+22)/2=15, E2=(12+18)/2=15
        # SS_E = r*g * [ (15-15)^2 + ... ] = 0
        # MS_E = 0
        
        # GxE Means:
        # G1E1=8, G1E2=12. MeanG1=10, MeanE1=15, Grand=15
        # InteractionTerm = CellMean - RowMean - ColMean + Grand
        # G1E1: 8 - 10 - 15 + 15 = -2
        # G1E2: 12 - 10 - 15 + 15 = +2
        # G2E1: 22 - 20 - 15 + 15 = +2
        # G2E2: 18 - 20 - 15 + 15 = -2
        # SS_GE = r * sum(terms^2) = 2 * (4 + 4 + 4 + 4) = 32
        # MS_GE = 32 / ((2-1)*(2-1)) = 32
        
        # Residual (Rep Variance)
        # All reps are identical in mock data (e.g., Rep1=8, Rep2=8)
        # So SS_Error should be 0
        # MS_Error = 0
        
        # Variance Components
        # Ve = MS_Error = 0
        # Vge = (MS_GE - MS_Error) / r = (32 - 0) / 2 = 16
        # Vg = (MS_G - MS_GE) / (r * e) = (200 - 32) / 4 = 168 / 4 = 42
        
        # Verify
        assert abs(res.ve) < 1e-5
        assert abs(res.vg - 42.0) < 1e-5
        # vge isn't directly exposed in result object as separate field unless we check
        # But we check H2
        
        # H2 = Vg / (Vg + Vge/e + Ve/re)
        # H2 = 42 / (42 + 16/2 + 0) = 42 / (42 + 8) = 42 / 50 = 0.84
        
        assert abs(res.h2_broad - 0.84) < 1e-4

