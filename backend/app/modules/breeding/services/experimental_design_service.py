"""
Experimental Design Generator Service

Provides advanced experimental design generation capabilities focusing on
statistical rigor and reproducibility.

Features:
- Randomized Complete Block Design (RCBD)
- Alpha-Lattice Design (Resolvable Incomplete Block Design)
"""

import math
import random

from app.schemas.trial_design import PlotAssignment, TrialDesignOutput


class ExperimentalDesignGenerator:
    """
    Generator for experimental designs ensuring statistical validity.
    """

    def __init__(self, seed: int | None = None):
        self.seed = seed
        self.rng = random.Random(seed)

    def set_seed(self, seed: int):
        """Set random seed for reproducibility."""
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_rcbd(
        self,
        genotypes: list[str],
        n_blocks: int,
        field_rows: int | None = None,
        seed: int | None = None,
    ) -> TrialDesignOutput:
        """
        Generate Randomized Complete Block Design (RCBD).

        In RCBD, every block contains all treatments (genotypes).
        Blocking allows for removal of field variation.

        Args:
            genotypes: List of genotype identifiers
            n_blocks: Number of blocks (replicates)
            field_rows: Number of physical rows in the field (for layout coordinates)
            seed: Random seed (overrides instance seed if provided)

        Returns:
            TrialDesignOutput with plot assignments
        """
        if seed is not None:
            self.set_seed(seed)

        n_geno = len(genotypes)
        if n_geno < 2:
            raise ValueError("RCBD requires at least 2 genotypes")
        if n_blocks < 2:
            raise ValueError("RCBD requires at least 2 blocks")

        n_plots = n_geno * n_blocks

        # Default field layout: square-ish
        if field_rows is None:
            # Try to make blocks contiguous in rows
            # If we have 3 blocks, maybe 3 rows?
            field_rows = n_blocks

        plots_per_row = math.ceil(n_plots / field_rows)

        plots: list[PlotAssignment] = []
        plot_id = 1

        for block in range(1, n_blocks + 1):
            # Randomize genotypes within block
            block_genos = genotypes.copy()
            self.rng.shuffle(block_genos)

            for i, geno in enumerate(block_genos):
                # Calculate layout coordinates
                # Assuming plots are filled row by row
                overall_idx = plot_id - 1
                row = overall_idx // plots_per_row + 1
                col = overall_idx % plots_per_row + 1

                plots.append(
                    PlotAssignment(
                        plot_id=plot_id,
                        row=row,
                        column=col,
                        block=block,
                        replicate=block,  # In RCBD, block is the replicate
                        genotype=geno,
                        is_check=False,  # Default false, logic could be added to detect checks
                    )
                )
                plot_id += 1

        return TrialDesignOutput(
            design_type="RCBD",
            n_genotypes=n_geno,
            n_blocks=n_blocks,
            n_plots=n_plots,
            plots=plots,
            parameters={"seed": self.seed, "field_rows": field_rows},
        )

    def generate_alpha_lattice(
        self, genotypes: list[str], n_blocks: int, block_size: int, seed: int | None = None
    ) -> TrialDesignOutput:
        """
        Generate Alpha-Lattice Design (Resolvable Incomplete Block Design).

        Suitable for large numbers of genotypes. Each replicate (super-block)
        is divided into smaller incomplete blocks of size k.

        If total genotypes (v) is not a multiple of block_size (k),
        filler "CHECK" entries are added to complete the blocks.

        Args:
            genotypes: List of genotype identifiers
            n_blocks: Number of replicates (super-blocks)
            block_size: Size of incomplete blocks (k)
            seed: Random seed

        Returns:
            TrialDesignOutput with plot assignments
        """
        if seed is not None:
            self.set_seed(seed)

        n_geno = len(genotypes)
        if block_size < 2:
            raise ValueError("Block size must be at least 2")
        if n_geno < block_size:
            raise ValueError("Number of genotypes must be >= block size")

        # Determine number of incomplete blocks per replicate (s)
        # s = ceil(v / k)
        n_incomplete_blocks = math.ceil(n_geno / block_size)

        # Calculate total plots needed per replicate
        plots_per_rep = n_incomplete_blocks * block_size

        # Determine padding needed
        n_pad = plots_per_rep - n_geno

        padded_genos = genotypes.copy()
        if n_pad > 0:
            for i in range(n_pad):
                padded_genos.append(f"FILLER_{i + 1}")

        n_plots = plots_per_rep * n_blocks
        plots: list[PlotAssignment] = []
        plot_id = 1

        for rep in range(1, n_blocks + 1):
            # For each replicate, we randomize the genotypes
            # In a true alpha design, we would ensure specific concurrence.
            # Here we implement a randomized resolvable block design.

            rep_genos = padded_genos.copy()
            self.rng.shuffle(rep_genos)

            # Split into incomplete blocks
            for ib_idx in range(n_incomplete_blocks):
                start = ib_idx * block_size
                end = start + block_size
                block_content = rep_genos[start:end]

                # Assign plots
                for i, geno in enumerate(block_content):
                    # Logical incomplete block ID
                    incomplete_block_id = (rep - 1) * n_incomplete_blocks + ib_idx + 1

                    is_filler = geno.startswith("FILLER_")

                    # Layout: assuming plots flow within incomplete blocks,
                    # and incomplete blocks flow within replicates.
                    # We can map this to a grid if needed, but for now
                    # row/col depends on field shape.
                    # Let's assign logical row/col based on rep/block structure
                    # Row = Replicate, Column = overall index in rep (simplified)

                    # Alternatively, Row = Incomplete Block, Col = Plot in Block
                    row = incomplete_block_id
                    col = i + 1

                    plots.append(
                        PlotAssignment(
                            plot_id=plot_id,
                            row=row,
                            column=col,
                            block=rep,  # Super-block (Replicate)
                            replicate=rep,
                            incomplete_block=incomplete_block_id,
                            genotype=geno,
                            is_check=is_filler,
                        )
                    )
                    plot_id += 1

        return TrialDesignOutput(
            design_type="Alpha-Lattice",
            n_genotypes=n_geno,
            n_blocks=n_blocks,  # This is usually number of replicates
            n_plots=n_plots,
            plots=plots,
            parameters={
                "seed": self.seed,
                "block_size": block_size,
                "incomplete_blocks_per_rep": n_incomplete_blocks,
                "padded_entries": n_pad,
            },
            metadata={"description": "Resolvable Incomplete Block Design", "resolvable": True},
        )


# Factory function
def get_experimental_design_generator() -> ExperimentalDesignGenerator:
    return ExperimentalDesignGenerator()
