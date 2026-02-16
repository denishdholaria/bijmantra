"""
Trial Design Service for Plant Breeding
Experimental design generation and randomization

Features:
- Randomized Complete Block Design (RCBD)
- Alpha-lattice design
- Augmented design
- Split-plot design
- Randomization and layout generation
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import random
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlotAssignment:
    """Single plot assignment"""
    plot_id: int
    row: int
    column: int
    block: int
    genotype: str
    is_check: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plot_id": self.plot_id,
            "row": self.row,
            "column": self.column,
            "block": self.block,
            "genotype": self.genotype,
            "is_check": self.is_check,
        }


@dataclass
class TrialDesign:
    """Complete trial design"""
    design_type: str
    n_genotypes: int
    n_blocks: int
    n_plots: int
    plots: List[PlotAssignment]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_type": self.design_type,
            "n_genotypes": self.n_genotypes,
            "n_blocks": self.n_blocks,
            "n_plots": self.n_plots,
            "plots": [p.to_dict() for p in self.plots],
        }


class TrialDesignService:
    """
    Trial design generation for plant breeding experiments
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def set_seed(self, seed: int):
        """Set random seed for reproducibility"""
        self.rng = random.Random(seed)

    def rcbd(
        self,
        genotypes: List[str],
        n_blocks: int,
        field_rows: Optional[int] = None
    ) -> TrialDesign:
        """
        Generate Randomized Complete Block Design
        
        Each block contains all genotypes in random order.
        
        Args:
            genotypes: List of genotype names
            n_blocks: Number of blocks (replicates)
            field_rows: Number of field rows (for layout)
            
        Returns:
            TrialDesign with plot assignments
        """
        n_geno = len(genotypes)
        n_plots = n_geno * n_blocks

        if field_rows is None:
            field_rows = n_blocks

        plots_per_row = math.ceil(n_plots / field_rows)

        plots = []
        plot_id = 1

        for block in range(1, n_blocks + 1):
            # Randomize genotypes within block
            block_genos = genotypes.copy()
            self.rng.shuffle(block_genos)

            for i, geno in enumerate(block_genos):
                # Calculate row and column
                overall_idx = (block - 1) * n_geno + i
                row = overall_idx // plots_per_row + 1
                col = overall_idx % plots_per_row + 1

                plots.append(PlotAssignment(
                    plot_id=plot_id,
                    row=row,
                    column=col,
                    block=block,
                    genotype=geno,
                ))
                plot_id += 1

        return TrialDesign(
            design_type="RCBD",
            n_genotypes=n_geno,
            n_blocks=n_blocks,
            n_plots=n_plots,
            plots=plots,
        )

    def alpha_lattice(
        self,
        genotypes: List[str],
        n_blocks: int,
        block_size: int
    ) -> TrialDesign:
        """
        Generate Alpha-Lattice (Resolvable Incomplete Block) Design
        
        For large numbers of genotypes where complete blocks are impractical.
        
        Args:
            genotypes: List of genotype names
            n_blocks: Number of super-blocks (replicates)
            block_size: Number of plots per incomplete block
            
        Returns:
            TrialDesign with plot assignments
        """
        n_geno = len(genotypes)

        # Number of incomplete blocks per replicate
        n_iblocks = math.ceil(n_geno / block_size)

        # Pad genotypes if needed
        padded_genos = genotypes.copy()
        while len(padded_genos) % block_size != 0:
            padded_genos.append(f"CHECK_{len(padded_genos) - n_geno + 1}")

        n_plots = len(padded_genos) * n_blocks
        plots = []
        plot_id = 1

        for rep in range(1, n_blocks + 1):
            # Randomize genotypes for this replicate
            rep_genos = padded_genos.copy()
            self.rng.shuffle(rep_genos)

            # Assign to incomplete blocks
            for iblock in range(n_iblocks):
                start_idx = iblock * block_size
                end_idx = min(start_idx + block_size, len(rep_genos))
                block_genos = rep_genos[start_idx:end_idx]

                # Randomize within incomplete block
                self.rng.shuffle(block_genos)

                for i, geno in enumerate(block_genos):
                    is_check = geno.startswith("CHECK_")

                    plots.append(PlotAssignment(
                        plot_id=plot_id,
                        row=(rep - 1) * n_iblocks + iblock + 1,
                        column=i + 1,
                        block=rep,
                        genotype=geno,
                        is_check=is_check,
                    ))
                    plot_id += 1

        return TrialDesign(
            design_type="Alpha-Lattice",
            n_genotypes=n_geno,
            n_blocks=n_blocks,
            n_plots=n_plots,
            plots=plots,
        )

    def augmented_design(
        self,
        test_genotypes: List[str],
        check_genotypes: List[str],
        n_blocks: int,
        checks_per_block: int = 1
    ) -> TrialDesign:
        """
        Generate Augmented Design (Modified Augmented Design)
        
        Checks are replicated in each block, test genotypes are unreplicated.
        Useful for early generation testing with many lines.
        
        Args:
            test_genotypes: Unreplicated test entries
            check_genotypes: Replicated check varieties
            n_blocks: Number of blocks
            checks_per_block: Number of check plots per block
            
        Returns:
            TrialDesign with plot assignments
        """
        n_test = len(test_genotypes)
        n_checks = len(check_genotypes)

        # Distribute test genotypes across blocks
        tests_per_block = math.ceil(n_test / n_blocks)

        plots = []
        plot_id = 1
        test_idx = 0

        for block in range(1, n_blocks + 1):
            block_entries = []

            # Add checks to this block
            for _ in range(checks_per_block):
                for check in check_genotypes:
                    block_entries.append((check, True))

            # Add test genotypes to this block
            for _ in range(tests_per_block):
                if test_idx < n_test:
                    block_entries.append((test_genotypes[test_idx], False))
                    test_idx += 1

            # Randomize within block
            self.rng.shuffle(block_entries)

            for i, (geno, is_check) in enumerate(block_entries):
                plots.append(PlotAssignment(
                    plot_id=plot_id,
                    row=block,
                    column=i + 1,
                    block=block,
                    genotype=geno,
                    is_check=is_check,
                ))
                plot_id += 1

        return TrialDesign(
            design_type="Augmented",
            n_genotypes=n_test + n_checks,
            n_blocks=n_blocks,
            n_plots=len(plots),
            plots=plots,
        )

    def split_plot(
        self,
        main_treatments: List[str],
        sub_treatments: List[str],
        n_blocks: int
    ) -> TrialDesign:
        """
        Generate Split-Plot Design
        
        Main plots contain main treatments, split into subplots for sub-treatments.
        
        Args:
            main_treatments: Main plot treatments (e.g., irrigation levels)
            sub_treatments: Subplot treatments (e.g., genotypes)
            n_blocks: Number of blocks
            
        Returns:
            TrialDesign with plot assignments
        """
        n_main = len(main_treatments)
        n_sub = len(sub_treatments)
        n_plots = n_main * n_sub * n_blocks

        plots = []
        plot_id = 1

        for block in range(1, n_blocks + 1):
            # Randomize main plots within block
            main_order = main_treatments.copy()
            self.rng.shuffle(main_order)

            for main_idx, main_trt in enumerate(main_order):
                # Randomize subplots within main plot
                sub_order = sub_treatments.copy()
                self.rng.shuffle(sub_order)

                for sub_idx, sub_trt in enumerate(sub_order):
                    plots.append(PlotAssignment(
                        plot_id=plot_id,
                        row=(block - 1) * n_main + main_idx + 1,
                        column=sub_idx + 1,
                        block=block,
                        genotype=f"{main_trt}:{sub_trt}",
                    ))
                    plot_id += 1

        return TrialDesign(
            design_type="Split-Plot",
            n_genotypes=n_main * n_sub,
            n_blocks=n_blocks,
            n_plots=n_plots,
            plots=plots,
        )

    def crd(
        self,
        genotypes: List[str],
        n_reps: int
    ) -> TrialDesign:
        """
        Generate Completely Randomized Design
        
        All plots randomized without blocking.
        
        Args:
            genotypes: List of genotype names
            n_reps: Number of replications per genotype
            
        Returns:
            TrialDesign with plot assignments
        """
        n_geno = len(genotypes)
        n_plots = n_geno * n_reps

        # Create all plot assignments
        all_genos = genotypes * n_reps
        self.rng.shuffle(all_genos)

        # Calculate grid dimensions
        n_cols = math.ceil(math.sqrt(n_plots))

        plots = []
        for i, geno in enumerate(all_genos):
            plots.append(PlotAssignment(
                plot_id=i + 1,
                row=i // n_cols + 1,
                column=i % n_cols + 1,
                block=1,  # No blocking in CRD
                genotype=geno,
            ))

        return TrialDesign(
            design_type="CRD",
            n_genotypes=n_geno,
            n_blocks=1,
            n_plots=n_plots,
            plots=plots,
        )

    def generate_field_map(
        self,
        design: TrialDesign,
        plot_width: float = 1.5,
        plot_length: float = 5.0,
        alley_width: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate field map with coordinates
        
        Args:
            design: TrialDesign object
            plot_width: Plot width in meters
            plot_length: Plot length in meters
            alley_width: Alley width between blocks
            
        Returns:
            Field map with coordinates
        """
        max_row = max(p.row for p in design.plots)
        max_col = max(p.column for p in design.plots)

        field_map = []
        for plot in design.plots:
            x = (plot.column - 1) * (plot_width + alley_width)
            y = (plot.row - 1) * (plot_length + alley_width)

            field_map.append({
                **plot.to_dict(),
                "x_meters": round(x, 2),
                "y_meters": round(y, 2),
                "width_meters": plot_width,
                "length_meters": plot_length,
            })

        return {
            "design_type": design.design_type,
            "field_dimensions": {
                "rows": max_row,
                "columns": max_col,
                "total_width_meters": round(max_col * (plot_width + alley_width), 2),
                "total_length_meters": round(max_row * (plot_length + alley_width), 2),
            },
            "plot_dimensions": {
                "width_meters": plot_width,
                "length_meters": plot_length,
                "alley_width_meters": alley_width,
            },
            "plots": field_map,
        }


# Singleton
_trial_design_service: Optional[TrialDesignService] = None


def get_trial_design_service() -> TrialDesignService:
    """Get or create trial design service singleton"""
    global _trial_design_service
    if _trial_design_service is None:
        _trial_design_service = TrialDesignService()
    return _trial_design_service
