import pytest
from app.modules.breeding.services.experimental_design_service import get_experimental_design_generator
from app.schemas.trial_design import TrialDesignOutput, PlotAssignment


class TestExperimentalDesignGenerator:
    def test_rcbd_generation(self):
        generator = get_experimental_design_generator()
        genotypes = ["G1", "G2", "G3", "G4"]
        n_blocks = 3

        design = generator.generate_rcbd(genotypes, n_blocks, seed=42)

        assert design.design_type == "RCBD"
        assert design.n_genotypes == 4
        assert design.n_blocks == 3
        assert design.n_plots == 12
        assert len(design.plots) == 12

        # Verify each block has all genotypes
        for block_idx in range(1, n_blocks + 1):
            block_plots = [p for p in design.plots if p.block == block_idx]
            assert len(block_plots) == 4
            block_genos = {p.genotype for p in block_plots}
            assert block_genos == set(genotypes)

    def test_rcbd_reproducibility(self):
        generator = get_experimental_design_generator()
        genotypes = ["G1", "G2", "G3"]

        design1 = generator.generate_rcbd(genotypes, n_blocks=2, seed=123)
        design2 = generator.generate_rcbd(genotypes, n_blocks=2, seed=123)
        design3 = generator.generate_rcbd(genotypes, n_blocks=2, seed=999)

        # Check plot assignments are identical for same seed
        assert [p.genotype for p in design1.plots] == [p.genotype for p in design2.plots]
        # Check different for different seed (highly likely)
        assert [p.genotype for p in design1.plots] != [p.genotype for p in design3.plots]

    def test_alpha_lattice_perfect_fit(self):
        generator = get_experimental_design_generator()
        # 9 genotypes, block size 3 -> perfect fit (3 blocks per rep)
        genotypes = [f"G{i}" for i in range(1, 10)]
        n_reps = 2
        block_size = 3

        design = generator.generate_alpha_lattice(genotypes, n_reps, block_size, seed=42)

        assert design.design_type == "Alpha-Lattice"
        assert design.n_plots == 9 * 2

        # Check structure
        # Each rep should have 3 incomplete blocks
        # Each incomplete block should have 3 plots

        for rep in range(1, n_reps + 1):
            rep_plots = [p for p in design.plots if p.replicate == rep]
            assert len(rep_plots) == 9

            # Check incomplete blocks
            ib_ids = {p.incomplete_block for p in rep_plots}
            assert len(ib_ids) == 3

            for ib_id in ib_ids:
                ib_plots = [p for p in rep_plots if p.incomplete_block == ib_id]
                assert len(ib_plots) == 3

    def test_alpha_lattice_padding(self):
        generator = get_experimental_design_generator()
        # 10 genotypes, block size 3. Needs 12 slots per rep (4 blocks of 3). 2 padding.
        genotypes = [f"G{i}" for i in range(1, 11)]
        n_reps = 2
        block_size = 3

        design = generator.generate_alpha_lattice(genotypes, n_reps, block_size, seed=42)

        assert design.n_plots == 12 * 2

        # Check filler existence
        fillers = [p for p in design.plots if p.genotype.startswith("FILLER")]
        assert len(fillers) == 2 * 2  # 2 per rep * 2 reps

        for filler in fillers:
            assert filler.is_check is True

    def test_validation_errors(self):
        generator = get_experimental_design_generator()

        with pytest.raises(ValueError):
            generator.generate_rcbd(["G1"], n_blocks=2)  # Too few genotypes

        with pytest.raises(ValueError):
            generator.generate_rcbd(["G1", "G2"], n_blocks=1)  # Too few blocks

        with pytest.raises(ValueError):
            generator.generate_alpha_lattice(
                ["G1", "G2"], n_blocks=2, block_size=5
            )  # Block size > genotypes
