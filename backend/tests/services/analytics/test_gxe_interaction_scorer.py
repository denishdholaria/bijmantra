import numpy as np
import pytest

# Adjust path if necessary, but this should work if backend is in PYTHONPATH
from app.services.analytics.gxe_interaction_scorer import GxEInteractionScorer, GxEScores

@pytest.fixture
def scorer():
    return GxEInteractionScorer()

@pytest.fixture
def sample_data():
    """
    Sample data: 3 Genotypes, 3 Environments.

    Data:
    Env1 Env2 Env3
    G1: 10   12   11
    G2: 8    15   12
    G3: 12   10   14

    Means:
    G1: 11
    G2: 11.66
    G3: 12

    Env1: 10
    Env2: 12.33
    Env3: 12.33

    Grand Mean: 11.55
    """
    yield_matrix = np.array([
        [10.0, 12.0, 11.0],
        [8.0, 15.0, 12.0],
        [12.0, 10.0, 14.0]
    ])
    genotype_names = ["G1", "G2", "G3"]
    environment_names = ["E1", "E2", "E3"]
    return yield_matrix, genotype_names, environment_names

def test_calculate_interaction_matrix(scorer, sample_data):
    yield_matrix, _, _ = sample_data
    interaction = scorer.calculate_interaction_matrix(yield_matrix)

    assert interaction.shape == yield_matrix.shape

    # Manual check for G1, E1
    # Y_11 = 10
    # Y_1. = 11
    # Y_.1 = 10
    # Y_.. = 11.555... (104/9)

    grand_mean = np.mean(yield_matrix) # 11.555
    g1_mean = np.mean(yield_matrix[0, :]) # 11
    e1_mean = np.mean(yield_matrix[:, 0]) # 10

    expected_g1e1 = 10 - g1_mean - e1_mean + grand_mean
    assert np.isclose(interaction[0, 0], expected_g1e1)

    # Sum of interactions across rows and columns should be approx 0
    assert np.allclose(np.sum(interaction, axis=0), 0)
    assert np.allclose(np.sum(interaction, axis=1), 0)

def test_calculate_wricke_ecovalence(scorer, sample_data):
    yield_matrix, g_names, _ = sample_data
    wricke = scorer.calculate_wricke_ecovalence(yield_matrix, g_names)

    assert len(wricke) == 3
    assert all(g in wricke for g in g_names)

    interaction = scorer.calculate_interaction_matrix(yield_matrix)
    expected_wricke_g1 = np.sum(interaction[0, :]**2)

    assert np.isclose(wricke["G1"], expected_wricke_g1)
    # Wricke should be non-negative
    assert all(val >= 0 for val in wricke.values())

def test_calculate_shukla_stability(scorer, sample_data):
    yield_matrix, g_names, _ = sample_data
    shukla = scorer.calculate_shukla_stability(yield_matrix, g_names)

    # Check dimensions requirement (p=3, q=3 is valid)
    assert len(shukla) == 3

    # Basic property check
    # Sum of Shukla variances relates to total interaction SS
    # Not directly sum(sigma) = SS, but related.
    pass

def test_calculate_shukla_insufficient_dimensions(scorer):
    # Case p=2 < 3
    yield_matrix = np.array([[10, 12], [8, 14]])
    g_names = ["G1", "G2"]

    shukla = scorer.calculate_shukla_stability(yield_matrix, g_names)
    assert all(val == 0.0 for val in shukla.values())

def test_calculate_lin_binns_superiority(scorer, sample_data):
    yield_matrix, g_names, _ = sample_data
    pi = scorer.calculate_lin_binns_superiority(yield_matrix, g_names)

    # Max yields:
    # E1: 12 (G3)
    # E2: 15 (G2)
    # E3: 14 (G3)

    # G1 Distances:
    # (10-12)^2 + (12-15)^2 + (11-14)^2
    # 4 + 9 + 9 = 22
    # Pi = 22 / (2 * 3) = 22/6 = 3.666

    assert np.isclose(pi["G1"], 22.0 / 6.0)

    # G3 should have low Pi because it has max in 2 envs
    # G3: (12-12)^2 + (10-15)^2 + (14-14)^2
    # 0 + 25 + 0 = 25
    # Pi = 25/6 = 4.166

    assert np.isclose(pi["G3"], 25.0 / 6.0)

def test_calculate_kang_rank_sum(scorer, sample_data):
    yield_matrix, g_names, _ = sample_data
    # Mean Yields: G3(12) > G2(11.66) > G1(11)
    # Ranks Yield: G3=1, G2=2, G1=3

    # Stability (Shukla):
    # Need to calc or assume based on Wricke (since p,q constant)
    # Wricke ~ Interaction^2
    # G1 is most stable (visually less variation from mean pattern?)
    # Let's trust the calc.

    kang = scorer.calculate_kang_rank_sum(yield_matrix, g_names)

    # Check we get a result
    assert len(kang) == 3

    # Check customizable weights
    kang_weighted = scorer.calculate_kang_rank_sum(yield_matrix, g_names, weight_yield=2, weight_stability=1)
    assert kang_weighted != kang # Should be different unless ranks identical

def test_calculate_all_scores(scorer, sample_data):
    yield_matrix, g_names, e_names = sample_data
    scores = scorer.calculate_all_scores(yield_matrix, g_names, e_names)

    assert isinstance(scores, GxEScores)
    assert scores.wricke_ecovalence
    assert scores.shukla_stability
    assert scores.lin_binns_superiority
    assert scores.kang_rank_sum
    assert scores.interaction_matrix.shape == yield_matrix.shape

def test_empty_matrix(scorer):
    empty = np.zeros((0, 0))
    assert scorer.calculate_interaction_matrix(empty).size == 0
    assert scorer.calculate_wricke_ecovalence(empty, []) == {}
