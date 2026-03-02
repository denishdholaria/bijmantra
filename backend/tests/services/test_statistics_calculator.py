import pytest
import unittest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.statistics_calculator import TrialStatistics, ObservationData

class TestTrialStatisticsHeritability(unittest.TestCase):
    def test_calculate_heritability_happy_path(self):
        # Setup: Create 2 genotypes with 2 replicates each to ensure r_bar = 2
        data = [
            ObservationData(value=10.0, germplasm_id="G1"),
            ObservationData(value=12.0, germplasm_id="G1"),
            ObservationData(value=11.0, germplasm_id="G2"),
            ObservationData(value=13.0, germplasm_id="G2")
        ]
        stats = TrialStatistics(data)

        # Test case: Valid ms_genotype > ms_error
        ms_genotype = 100.0
        ms_error = 20.0
        # Expected: 1 - (20 / 100) = 0.8
        expected = 0.8
        result = stats.calculate_heritability(ms_genotype, ms_error)
        self.assertEqual(result, expected)

    def test_calculate_heritability_zero_case(self):
        data = [
            ObservationData(value=10.0, germplasm_id="G1"),
            ObservationData(value=12.0, germplasm_id="G1")
        ]
        stats = TrialStatistics(data)

        # Test case: ms_genotype == ms_error
        ms_genotype = 50.0
        ms_error = 50.0
        # Expected: 0.0
        result = stats.calculate_heritability(ms_genotype, ms_error)
        self.assertEqual(result, 0.0)

    def test_calculate_heritability_negative_vg(self):
        data = [
            ObservationData(value=10.0, germplasm_id="G1"),
            ObservationData(value=12.0, germplasm_id="G1")
        ]
        stats = TrialStatistics(data)

        # Test case: ms_error > ms_genotype
        ms_genotype = 40.0
        ms_error = 50.0
        # Expected: 0.0 (clamped)
        result = stats.calculate_heritability(ms_genotype, ms_error)
        self.assertEqual(result, 0.0)

    def test_calculate_heritability_none_inputs(self):
        data = [
            ObservationData(value=10.0, germplasm_id="G1"),
            ObservationData(value=12.0, germplasm_id="G1")
        ]
        stats = TrialStatistics(data)

        self.assertIsNone(stats.calculate_heritability(None, 50.0))
        self.assertIsNone(stats.calculate_heritability(50.0, None))
        self.assertIsNone(stats.calculate_heritability(None, None))

    def test_calculate_heritability_zero_replicates(self):
        # If no replicates, r_bar is 0
        data = [] # empty list
        stats = TrialStatistics(data)

        # r_bar should be 0
        self.assertEqual(stats.r_bar, 0)

        # Should return None
        result = stats.calculate_heritability(100.0, 20.0)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()

class TestTrialStatisticsAnova:
    def test_calculate_anova_balanced_design(self):
        # Balanced design: 3 genotypes, 3 replicates each
        data = [
            # Genotype 1: 10, 12, 11 (mean=11)
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=12, germplasm_id="G1"),
            ObservationData(value=11, germplasm_id="G1"),
            # Genotype 2: 20, 22, 21 (mean=21)
            ObservationData(value=20, germplasm_id="G2"),
            ObservationData(value=22, germplasm_id="G2"),
            ObservationData(value=21, germplasm_id="G2"),
        ]

        # Manual check
        # Mean G1=11, G2=21
        # Grand Mean = 16
        # SSTr = 3*(11-16)^2 + 3*(21-16)^2 = 3*25 + 3*25 = 150
        # SSE = (10-11)^2 + (12-11)^2 + (11-11)^2 + (20-21)^2 + (22-21)^2 + (21-21)^2
        #     = 1 + 1 + 0 + 1 + 1 + 0 = 4
        # df_tr = 2 - 1 = 1
        # df_error = 6 - 2 = 4
        # MS_Tr = 150 / 1 = 150
        # MS_E = 4 / 4 = 1
        # F = 150 / 1 = 150

        stats = TrialStatistics(data)
        anova = stats.calculate_anova()

        assert anova["ms_genotype"] == pytest.approx(150.0)
        assert anova["ms_error"] == pytest.approx(1.0)
        assert anova["f_value"] == pytest.approx(150.0)
        assert anova["df_genotype"] == 1
        assert anova["df_error"] == 4

    def test_calculate_anova_unbalanced_design(self):
        # Unbalanced design: G1 (3 reps), G2 (2 reps)
        data = [
            # Genotype 1: 10, 12, 11 (mean=11)
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=12, germplasm_id="G1"),
            ObservationData(value=11, germplasm_id="G1"),
            # Genotype 2: 20, 22 (mean=21)
            ObservationData(value=20, germplasm_id="G2"),
            ObservationData(value=22, germplasm_id="G2"),
        ]

        # Manual Check
        # Mean G1=11, G2=21
        # n = 5
        # Grand Mean = (10+12+11+20+22)/5 = 75/5 = 15

        # SSTr = 3*(11-15)^2 + 2*(21-15)^2
        #      = 3*(-4)^2 + 2*(6)^2
        #      = 3*16 + 2*36 = 48 + 72 = 120

        # SSE = (10-11)^2 + (12-11)^2 + (11-11)^2 + (20-21)^2 + (22-21)^2
        #     = 1 + 1 + 0 + 1 + 1 = 4

        # df_tr = 2 - 1 = 1
        # df_error = 5 - 2 = 3

        # MS_Tr = 120 / 1 = 120
        # MS_E = 4 / 3 = 1.3333...

        # F = 120 / 1.3333 = 90

        stats = TrialStatistics(data)
        anova = stats.calculate_anova()

        assert anova["ms_genotype"] == pytest.approx(120.0)
        assert anova["ms_error"] == pytest.approx(4/3)
        assert anova["f_value"] == pytest.approx(90.0)
        assert anova["df_genotype"] == 1
        assert anova["df_error"] == 3

    def test_calculate_anova_insufficient_genotypes(self):
        # Only 1 genotype
        data = [
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=12, germplasm_id="G1"),
        ]
        stats = TrialStatistics(data)
        anova = stats.calculate_anova()

        assert anova["ms_genotype"] is None
        assert anova["ms_error"] is None
        assert anova["f_value"] is None

    def test_calculate_anova_insufficient_data(self):
        # n <= n_genotypes (e.g., 1 rep per genotype)
        data = [
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=20, germplasm_id="G2"),
        ]
        # n=2, n_genotypes=2. 2 <= 2 is True.

        stats = TrialStatistics(data)
        anova = stats.calculate_anova()

        assert anova["ms_genotype"] is None
        assert anova["ms_error"] is None
        assert anova["f_value"] is None

    def test_calculate_anova_zero_variance(self):
        # All values identical
        data = [
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=10, germplasm_id="G2"),
            ObservationData(value=10, germplasm_id="G2"),
        ]

        stats = TrialStatistics(data)
        anova = stats.calculate_anova()

        # SSTr = 0, SSE = 0
        assert anova["ms_genotype"] == 0.0
        assert anova["ms_error"] == 0.0
        # F value logic: if ms_error > 0 check
        # Code: f_value = ms_tr / ms_error if ms_error > 0 else None
        assert anova["f_value"] is None

    def test_calculate_anova_zero_error_variance(self):
        # Genotypes differ, but no error variance (perfect prediction)
        data = [
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=20, germplasm_id="G2"),
            ObservationData(value=20, germplasm_id="G2"),
        ]

        # Mean G1=10, G2=20. Grand Mean=15.
        # SSTr = 2*(10-15)^2 + 2*(20-15)^2 = 2*25 + 2*25 = 100
        # SSE = 0
        # MS_Tr = 100/1 = 100
        # MS_E = 0

        stats = TrialStatistics(data)
        anova = stats.calculate_anova()

        assert anova["ms_genotype"] == pytest.approx(100.0)
        assert anova["ms_error"] == 0.0
        assert anova["f_value"] is None

    def test_calculate_anova_missing_values(self):
        # Data with None values should be filtered out
        data = [
            ObservationData(value=10, germplasm_id="G1"),
            ObservationData(value=None, germplasm_id="G1"),
            ObservationData(value=12, germplasm_id="G1"),
            ObservationData(value=20, germplasm_id="G2"),
            ObservationData(value=22, germplasm_id="G2"),
        ]

        # Effective data same as unbalanced design test case G1: 10,12; G2: 20,22
        # Mean G1=11, G2=21. Grand Mean=16.
        # SSTr = 2*(11-16)^2 + 2*(21-16)^2 = 2*25 + 2*25 = 100
        # SSE = (10-11)^2 + (12-11)^2 + (20-21)^2 + (22-21)^2 = 1+1+1+1 = 4
        # df_tr = 1
        # df_error = 4 - 2 = 2
        # MS_Tr = 100
        # MS_E = 4/2 = 2
        # F = 50

        stats = TrialStatistics(data)
        anova = stats.calculate_anova()

        assert anova["ms_genotype"] == pytest.approx(100.0)
        assert anova["ms_error"] == pytest.approx(2.0)
        assert anova["f_value"] == pytest.approx(50.0)
