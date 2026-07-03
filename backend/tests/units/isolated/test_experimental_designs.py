"""
Isolated Unit Tests for Trial Design Service

Tests for:
- Randomized Complete Block Design (RCBD)
- Alpha-Lattice Design
- Augmented Design
- Split-Plot Design
- Completely Randomized Design (CRD)
- Field Map Generation
- Reproducibility
- Input Validation

Executed via:
  python backend/tests/units/isolated/test_experimental_designs.py

Verification History:
- Verified locally: 2025-02-14
"""

import unittest
import sys
import os
import math

# Add backend to path so we can import app modules
# Assuming running from repo root
sys.path.insert(0, os.path.abspath("backend"))

from app.modules.breeding.services.trial_design_service import TrialDesignService, TrialDesign, PlotAssignment

class TestTrialDesignService(unittest.TestCase):
    def setUp(self):
        self.service = TrialDesignService(seed=42)
        self.genotypes = [f"G{i}" for i in range(1, 11)]  # 10 genotypes

    def test_rcbd(self):
        """Test Randomized Complete Block Design"""
        n_blocks = 3
        design = self.service.rcbd(self.genotypes, n_blocks)

        self.assertEqual(design.design_type, "RCBD")
        self.assertEqual(design.n_blocks, n_blocks)
        self.assertEqual(design.n_genotypes, 10)
        self.assertEqual(design.n_plots, 30)

        # Verify each block has all genotypes
        for b in range(1, n_blocks + 1):
            block_plots = [p for p in design.plots if p.block == b]
            block_genos = [p.genotype for p in block_plots]
            self.assertEqual(len(block_genos), 10)
            self.assertEqual(set(block_genos), set(self.genotypes))

    def test_alpha_lattice(self):
        """Test Alpha-Lattice Design"""
        n_blocks = 2
        block_size = 5
        design = self.service.alpha_lattice(self.genotypes, n_blocks, block_size)

        self.assertEqual(design.design_type, "Alpha-Lattice")
        self.assertEqual(design.n_blocks, n_blocks)
        # 10 genotypes, block size 5 -> 2 incomplete blocks per replicate. Perfect fit.

        # Verify incomplete blocks
        for b in range(1, n_blocks + 1):
            block_plots = [p for p in design.plots if p.block == b]
            self.assertEqual(len(block_plots), 10)

            # Check incomplete blocks structure (rows represent incomplete blocks here)
            # The implementation: row = (rep - 1) * n_iblocks + iblock + 1
            # n_iblocks = 10 / 5 = 2
            # rep 1: rows 1, 2
            # rep 2: rows 3, 4
            rows = set(p.row for p in block_plots)
            self.assertEqual(len(rows), 2)

    def test_alpha_lattice_with_checks(self):
        """Test Alpha-Lattice Design with Checks (Padding)"""
        # 11 genotypes, block size 4 -> need padding to 12 (3 blocks of 4)
        genotypes = [f"G{i}" for i in range(1, 12)]
        design = self.service.alpha_lattice(genotypes, n_blocks=2, block_size=4)

        self.assertEqual(len(design.plots), 24) # 12 * 2

        # Verify checks exist
        checks = [p for p in design.plots if p.is_check]
        self.assertTrue(len(checks) > 0)
        self.assertTrue(all(c.genotype.startswith("CHECK_") for c in checks))

    def test_augmented(self):
        """Test Augmented Design"""
        test_genos = [f"T{i}" for i in range(1, 21)] # 20 test
        check_genos = ["C1", "C2"] # 2 checks
        n_blocks = 4
        checks_per_block = 1 # Each check appears once per block

        design = self.service.augmented_design(test_genos, check_genos, n_blocks, checks_per_block=checks_per_block)

        self.assertEqual(design.design_type, "Augmented")

        # Verify checks in every block
        for b in range(1, n_blocks + 1):
            block_plots = [p for p in design.plots if p.block == b]
            block_genos = [p.genotype for p in block_plots]
            self.assertIn("C1", block_genos)
            self.assertIn("C2", block_genos)

        # Verify test genotypes appear exactly once across the whole experiment
        all_genos = [p.genotype for p in design.plots if not p.is_check]
        self.assertEqual(len(all_genos), 20)
        self.assertEqual(set(all_genos), set(test_genos))

    def test_split_plot(self):
        """Test Split-Plot Design"""
        main = ["M1", "M2"]
        sub = ["S1", "S2", "S3"]
        n_blocks = 3
        design = self.service.split_plot(main, sub, n_blocks)

        self.assertEqual(design.design_type, "Split-Plot")
        total_plots = len(main) * len(sub) * n_blocks # 2 * 3 * 3 = 18
        self.assertEqual(design.n_plots, 18)

        # Check genotype format "Main:Sub"
        for p in design.plots:
            self.assertIn(":", p.genotype)
            m, s = p.genotype.split(":")
            self.assertIn(m, main)
            self.assertIn(s, sub)

    def test_crd(self):
        """Test Completely Randomized Design"""
        n_reps = 4
        design = self.service.crd(self.genotypes, n_reps)

        self.assertEqual(design.design_type, "CRD")
        self.assertEqual(design.n_plots, 10 * 4)

        # Verify genotype counts
        from collections import Counter
        counts = Counter(p.genotype for p in design.plots)
        for g in self.genotypes:
            self.assertEqual(counts[g], 4)

    def test_field_map(self):
        """Test Field Map Generation"""
        design = self.service.rcbd(self.genotypes, n_blocks=2, field_rows=2)
        # 20 plots total. field_rows=2 -> 10 plots per row?
        # Code: plots_per_row = math.ceil(20 / 2) = 10.

        field_map = self.service.generate_field_map(design, plot_width=2.0, plot_length=5.0, alley_width=0.5)

        self.assertIn("plots", field_map)
        self.assertEqual(len(field_map["plots"]), 20)

        first_plot = field_map["plots"][0]
        self.assertIn("x_meters", first_plot)
        self.assertIn("y_meters", first_plot)
        self.assertEqual(first_plot["width_meters"], 2.0)

        # Verify dimensions
        self.assertIn("field_dimensions", field_map)
        dims = field_map["field_dimensions"]
        self.assertIn("total_width_meters", dims)
        self.assertIn("total_length_meters", dims)

    def test_reproducibility(self):
        """Test Reproducibility with Seed"""
        seed = 12345
        service1 = TrialDesignService(seed=seed)
        design1 = service1.rcbd(self.genotypes, n_blocks=3)

        service2 = TrialDesignService(seed=seed)
        design2 = service2.rcbd(self.genotypes, n_blocks=3)

        self.assertEqual(len(design1.plots), len(design2.plots))
        for p1, p2 in zip(design1.plots, design2.plots):
            self.assertEqual(p1.genotype, p2.genotype)
            self.assertEqual(p1.row, p2.row)
            self.assertEqual(p1.column, p2.column)

    def test_invalid_inputs(self):
        """Test Invalid Inputs (0 blocks, etc.)"""
        # The service doesn't validate blocks > 0 explicitly, leading to ZeroDivisionError
        # or logical errors. We document this behavior here.

        # RCBD with 0 blocks raises ZeroDivisionError due to field_rows defaulting to 0
        with self.assertRaises(ZeroDivisionError):
            self.service.rcbd(self.genotypes, n_blocks=0)

        # CRD with 0 reps is valid and should return 0 plots
        design_crd = self.service.crd(self.genotypes, n_reps=0)
        self.assertEqual(design_crd.n_plots, 0)

if __name__ == "__main__":
    unittest.main()
