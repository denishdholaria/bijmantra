import numpy as np

from app.services.compute_engine import ComputeBackend, ComputeEngine


def test_gblup_matches_precomputed_grm_path() -> None:
    engine = ComputeEngine(ComputeBackend.NUMPY)
    genotypes = np.array(
        [
            [0, 1, 2, 1, 0],
            [1, 1, 2, 0, 1],
            [2, 0, 1, 1, 2],
            [0, 2, 1, 2, 0],
        ],
        dtype=np.float64,
    )
    phenotypes = np.array([10.0, 11.5, 13.0, 9.5], dtype=np.float64)
    heritability = 0.4

    grm = engine.compute_grm(genotypes, method="vanraden1").matrix + np.eye(len(phenotypes)) * 0.001

    direct = engine.compute_gblup(genotypes, phenotypes, heritability)
    from_grm = engine.compute_gblup_from_grm(phenotypes, grm, heritability)

    np.testing.assert_allclose(direct.fixed_effects, from_grm.fixed_effects, atol=1e-8)
    np.testing.assert_allclose(direct.breeding_values, from_grm.breeding_values, atol=1e-8)
    np.testing.assert_allclose(direct.reliability, from_grm.reliability, atol=1e-8)
    np.testing.assert_allclose(direct.accuracy, from_grm.accuracy, atol=1e-8)
    assert direct.genetic_variance == from_grm.genetic_variance
    assert direct.error_variance == from_grm.error_variance
    assert direct.converged is from_grm.converged