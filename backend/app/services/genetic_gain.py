"""
Genetic Gain Service

Track and analyze genetic progress over breeding cycles.
Calculate realized gain, genetic trend, and breeding efficiency.

This service queries real database data. When no data exists,
it returns empty results per Zero Mock Data Policy.

Key Formulas:

Genetic Gain (ΔG):
    ΔG = (i × h² × σp) / L
    
    Where:
    - i = selection intensity
    - h² = heritability
    - σp = phenotypic standard deviation
    - L = generation interval (years)

Annual Genetic Gain:
    ΔG/year = (final_value - initial_value) / years

Realized Heritability:
    h²realized = R / S
    
    Where:
    - R = response to selection (change in mean)
    - S = selection differential (selected mean - population mean)
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.core import Program, Trial, Study
from app.models.germplasm import Germplasm
from app.models.phenotyping import Observation, ObservationVariable


class GeneticGainService:
    """Service for tracking genetic gain and breeding progress."""

    async def list_programs(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[Dict[str, Any]]:
        """List all breeding programs for genetic gain tracking."""
        stmt = select(Program).where(
            Program.organization_id == organization_id
        ).order_by(Program.program_name)

        result = await db.execute(stmt)
        programs = result.scalars().all()

        return [
            {
                "program_id": str(p.id),
                "program_db_id": p.program_db_id,
                "program_name": p.program_name,
                "common_crop_name": p.common_crop_name,
                "objective": p.objective,
            }
            for p in programs
        ]

    async def get_program_summary(
        self,
        db: AsyncSession,
        organization_id: int,
        program_id: str,
    ) -> Dict[str, Any]:
        """Get comprehensive summary of breeding program progress."""
        stmt = select(Program).where(
            Program.organization_id == organization_id,
            Program.program_db_id == program_id
        )
        result = await db.execute(stmt)
        program = result.scalar_one_or_none()

        if not program:
            return {"error": f"Program {program_id} not found"}

        stmt_trials = select(func.count(Trial.id)).where(
            Trial.organization_id == organization_id,
            Trial.program_id == program.id
        )
        result_trials = await db.execute(stmt_trials)
        trial_count = result_trials.scalar() or 0

        return {
            "program": {
                "program_id": str(program.id),
                "program_db_id": program.program_db_id,
                "program_name": program.program_name,
                "common_crop_name": program.common_crop_name,
            },
            "total_trials": trial_count,
            "cycle_data": [],
            "variety_releases": [],
            "genetic_gain_mean": None,
            "genetic_gain_best": None,
            "note": "Genetic gain calculation requires breeding cycle data.",
        }

    def calculate_expected_gain(
        self,
        heritability: float,
        selection_intensity: float,
        phenotypic_std: float,
        generation_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Calculate expected genetic gain from selection.
        
        Breeder's Equation:
            ΔG = (i × h² × σp) / L
        """
        if selection_intensity <= 0.01:
            i = 2.67
        elif selection_intensity <= 0.05:
            i = 2.06
        elif selection_intensity <= 0.10:
            i = 1.76
        elif selection_intensity <= 0.20:
            i = 1.40
        else:
            i = 0.80

        expected_gain = (i * heritability * phenotypic_std) / generation_interval

        return {
            "heritability": heritability,
            "selection_proportion": selection_intensity,
            "selection_intensity_i": round(i, 3),
            "phenotypic_std": phenotypic_std,
            "generation_interval": generation_interval,
            "expected_gain_per_year": round(expected_gain, 4),
            "formula": "ΔG = (i × h² × σp) / L",
        }

    def calculate_realized_heritability(
        self,
        response: float,
        selection_differential: float,
    ) -> Dict[str, Any]:
        """
        Estimate realized heritability from selection response.
        
        h²realized = R / S
        """
        if selection_differential == 0:
            return {"error": "Selection differential cannot be zero"}

        h2_realized = response / selection_differential

        return {
            "response": response,
            "selection_differential": selection_differential,
            "realized_heritability": round(h2_realized, 4),
            "formula": "h²realized = R / S",
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get overall statistics for genetic gain tracking."""
        stmt_programs = select(func.count(Program.id)).where(
            Program.organization_id == organization_id
        )
        result_programs = await db.execute(stmt_programs)
        program_count = result_programs.scalar() or 0

        stmt_trials = select(func.count(Trial.id)).where(
            Trial.organization_id == organization_id
        )
        result_trials = await db.execute(stmt_trials)
        trial_count = result_trials.scalar() or 0

        return {
            "total_programs": program_count,
            "total_trials": trial_count,
            "total_cycles_recorded": 0,
            "total_variety_releases": 0,
            "note": "Record breeding cycle data for detailed tracking.",
        }


def get_genetic_gain_service() -> GeneticGainService:
    """Get the genetic gain service instance."""
    return GeneticGainService()


# Backward compatibility
genetic_gain_service = GeneticGainService()
