"""
Simulation API

Endpoints for genetic algorithm simulation of breeding processes.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
import numpy as np

from app.api import deps
from app.services.simulation import genetic_algorithm, SimulatedGenotype

router = APIRouter()

@router.post("/cross", response_model=Dict[str, Any])
async def simulate_cross(
    parent_a_dosage: List[int] = Body(..., description="Parent A genotype (0, 1, 2)"),
    parent_b_dosage: List[int] = Body(..., description="Parent B genotype (0, 1, 2)"),
    n_progeny: int = Body(1, ge=1, le=1000),
    recombination_rate: float = Body(0.5, ge=0.0, le=0.5),
    curr_user: Any = Depends(deps.get_current_active_user),
):
    """
    Simulate a cross between two parents.
    Input: Unphased dosage (0, 1, 2).
    Output: Offspring dosage (0, 1, 2).
    """
    if len(parent_a_dosage) != len(parent_b_dosage):
        raise HTTPException(status_code=400, detail="Parent genotypes must have same length")
        
    try:
        # 1. Phase parents (guess)
        genome_a = genetic_algorithm.phase_from_dosage(parent_a_dosage)
        genome_b = genetic_algorithm.phase_from_dosage(parent_b_dosage)
        
        # 2. Create SimulatedGenotype objects
        # ID is arbitrary since stateless
        pa = SimulatedGenotype(id="P1", parents=("Unknown", "Unknown"), genome=genome_a, generation=0)
        pb = SimulatedGenotype(id="P2", parents=("Unknown", "Unknown"), genome=genome_b, generation=0)
        
        # 3. Crossing
        offspring_objs = genetic_algorithm.cross(
            pa, pb, n_progeny=n_progeny, recombination_rate=recombination_rate
        )
        
        # 4. Convert back to Dosage for response
        offspring_dosages = []
        for child in offspring_objs:
            # Sum alleles at each locus
            dosage = np.sum(child.genome, axis=0).tolist()
            offspring_dosages.append(dosage)
            
        return {
            "n_progeny": n_progeny,
            "offspring_dosages": offspring_dosages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

@router.post("/generation", response_model=Dict[str, Any])
async def simulate_generation(
    population_dosages: List[List[int]] = Body(..., description="List of genotypes"),
    n_offspring: int = Body(..., description="Target population size"),
    recombination_rate: float = Body(0.5),
    crossing_scheme: str = Body("random", regex="^(random|selfing)$"),
    curr_user: Any = Depends(deps.get_current_active_user),
):
    """
    Advance a population by one generation.
    - Random: Random mating (panmixia)
    - Selfing: Everyone self-fertilizes
    """
    if not population_dosages:
        raise HTTPException(status_code=400, detail="Population cannot be empty")
        
    try:
        # Convert to SimulatedGenotype objects
        pop_objs = []
        for i, dosage in enumerate(population_dosages):
            genome = genetic_algorithm.phase_from_dosage(dosage)
            pop_objs.append(SimulatedGenotype(id=f"Ind_{i}", parents=("?", "?"), genome=genome, generation=0))
            
        new_pop = []
        n_parents = len(pop_objs)
        
        if crossing_scheme == "selfing":
             # Produce n_offspring total, distributed among parents?
             # Or n_offspring PER parent? Let's assume total target size.
             # If n_offspring < n_parents, we pick random parents or truncate?
             # Let's produce n_offspring total by sampling parents with replacement.
             
             for i in range(n_offspring):
                 parent = pop_objs[np.random.randint(0, n_parents)]
                 # Selfing: Cross parent with itself
                 children = genetic_algorithm.cross(parent, parent, n_progeny=1, recombination_rate=recombination_rate)
                 new_pop.extend(children)
                 
        elif crossing_scheme == "random":
             # Random mating
             for i in range(n_offspring):
                 p1 = pop_objs[np.random.randint(0, n_parents)]
                 p2 = pop_objs[np.random.randint(0, n_parents)]
                 children = genetic_algorithm.cross(p1, p2, n_progeny=1, recombination_rate=recombination_rate)
                 new_pop.extend(children)
        
        # Output dosages
        offspring_dosages = [np.sum(ind.genome, axis=0).tolist() for ind in new_pop]
        
        return {
            "generation": 1,
            "n_offspring": len(offspring_dosages),
            "offspring_dosages": offspring_dosages
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation simulation failed: {str(e)}")
