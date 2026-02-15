"""
Genetic Algorithm Service for Breeding Simulation

This service simulates the biological processes of plant breeding:
- Gamete formation (Meiosis with recombination)
- Crossing (Fertilization)
- Selection (Truncation selection)
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimulatedGenotype:
    """Represents a single individual in the simulation"""
    id: str
    parents: Tuple[str, str] # (Mom, Dad)
    genome: np.ndarray # Shape (ploidy, n_markers), values 0 or 1 (alleles)
    generation: int
    breeding_value: Optional[float] = None
    phenotype: Optional[float] = None

    def to_dict(self):
        return {
            "id": self.id,
            "parents": self.parents,
            "generation": self.generation,
            "breeding_value": self.breeding_value,
            "phenotype": self.phenotype,
            # Genome usually too large to dump fully, maybe summary?
            # "genome_summary": ... 
        }

class GeneticAlgorithmService:
    """
    Simulates breeding processes.
    """

    def __init__(self):
        pass

    def phase_from_dosage(self, dosage: Union[List[int], np.ndarray]) -> np.ndarray:
        """
        Convert unphased dosage (0, 1, 2) into phased haplotypes (2, M).
        
        Since phase is unknown, we assign alleles randomly for heterozygotes (1).
        - 0 -> (0, 0)
        - 2 -> (1, 1)
        - 1 -> (0, 1) or (1, 0) with equal prob
        
        Args:
            dosage: Vector of allele counts (M,)
            
        Returns:
            Phased genome (2, M)
        """
        dosage = np.array(dosage, dtype=int)
        M = len(dosage)
        genome = np.zeros((2, M), dtype=int)
        
        # Homozygote Ref (0) -> Both 0 (already init)
        
        # Homozygote Alt (2) -> Both 1
        hom_alt_idx = (dosage == 2)
        genome[:, hom_alt_idx] = 1
        
        # Heterozygote (1) -> Random Assignment
        het_idx = np.where(dosage == 1)[0]
        n_het = len(het_idx)
        
        if n_het > 0:
            # Randomly choose which chromosome gets the '1' allele
            # 0 -> (1, 0), 1 -> (0, 1)
            choices = np.random.randint(0, 2, size=n_het)
            
            # For choice 0: chr0=1, chr1=0
            # For choice 1: chr0=0, chr1=1
            
            # Assign 1s
            # Array fancy indexing: genome[row, col]
            genome[choices, het_idx] = 1
            # The other chromosome stays 0 (is initialized to 0)
            
        return genome


    def _create_gamete(self, genome: np.ndarray, recombination_rate: float = 0.5) -> np.ndarray:
        """
        Simulate meiosis for a diploid genome to produce a haploid gamete.
        
        Args:
            genome: Shape (2, n_markers). Row 0 = Chr A, Row 1 = Chr B.
            recombination_rate: Probability of crossover between adjacent markers.
                                If 0.5, markers are unlinked (independent assortment).
                                If < 0.5, markers are linked.
                                Realistically, this should be a vector of map distances.
                                For basic sim, we use uniform rate or independent (0.5).
        
        Returns:
            gamete: Shape (1, n_markers) - a haploid set.
        """
        n_markers = genome.shape[1]
        
        # 1. Choose starting chromosome for first marker (0 or 1)
        current_chrom = np.random.randint(0, 2)
        
        # 2. Determine crossovers
        # Generate random floats for each interval
        # If rand < r, switch chromosome
        # We need n_markers decisions (first one is random start, rest depend on r)
        
        # Vectorized approach:
        # Generate crossover points
        crossovers = np.random.random(n_markers) < recombination_rate
        # For the first marker, it's 50/50 (independent start)
        crossovers[0] = np.random.random() < 0.5 
        
        # Cumulative sum % 2 determines current chromosome state
        # 0 -> 0 -> 0 (stay)
        # 0 -> 1 -> 1 (switch)
        # 1 -> 1 -> 0 (switch back)
        chrom_indices = np.cumsum(crossovers) % 2
        chrom_indices = chrom_indices.astype(int)
        
        # Select alleles
        # genome is (2, M). We want genome[chrom_indices[i], i] for each i
        gamete = genome[chrom_indices, np.arange(n_markers)]
        
        return gamete

    def cross(
        self,
        parent_a: SimulatedGenotype,
        parent_b: SimulatedGenotype,
        n_progeny: int = 1,
        recombination_rate: float = 0.5,
        generation_name: Optional[str] = None
    ) -> List[SimulatedGenotype]:
        """
        Perform a cross between two parents.
        
        Args:
            parent_a, parent_b: Parent genotypes
            n_progeny: Number of offspring to generate
            recombination_rate: Proxy for linkage (default 0.5 = unlinked)
            
        Returns:
            List of new SimulatedGenotype objects
        """
        offspring = []
        gen_num = max(parent_a.generation, parent_b.generation) + 1
        
        for i in range(n_progeny):
            # Form gametes
            gamete_a = self._create_gamete(parent_a.genome, recombination_rate)
            gamete_b = self._create_gamete(parent_b.genome, recombination_rate)
            
            # Fuse to form zygote (2, M)
            new_genome = np.vstack([gamete_a, gamete_b])
            
            # ID generation
            new_id = f"F{gen_num}_{parent_a.id}x{parent_b.id}_{i+1}"
            
            child = SimulatedGenotype(
                id=new_id,
                parents=(parent_a.id, parent_b.id),
                genome=new_genome,
                generation=gen_num
            )
            offspring.append(child)
            
        return offspring

    def calculate_breeding_values(
        self,
        population: List[SimulatedGenotype],
        marker_effects: np.ndarray
    ) -> List[SimulatedGenotype]:
        """
        Calculate True Breeding Value (TBV) = Sum(Genotype * Effect)
        
        Args:
            population: List of genotypes
            marker_effects: Vector of effects (M,)
            
        Returns:
            Population with .breeding_value updated
        """
        for ind in population:
            # Genome (2, M). Sum alleles at each locus -> (M,) 0/1/2
            dosage = np.sum(ind.genome, axis=0)
            tbv = np.dot(dosage, marker_effects)
            ind.breeding_value = float(tbv)
            
        return population

    def select(
        self,
        population: List[SimulatedGenotype],
        n_select: int,
        criterion: str = "breeding_value" # or "phenotype"
    ) -> List[SimulatedGenotype]:
        """
        Perform truncation selection.
        """
        # Sort desc
        if criterion == "breeding_value":
            ranked = sorted(population, key=lambda x: x.breeding_value or -np.inf, reverse=True)
        elif criterion == "phenotype":
             ranked = sorted(population, key=lambda x: x.phenotype or -np.inf, reverse=True)
        else:
             raise ValueError(f"Unknown selection criterion: {criterion}")
             
        return ranked[:n_select]

    def simulate_phenotypes(
        self,
        population: List[SimulatedGenotype],
        h2: float = 0.5
    ) -> List[SimulatedGenotype]:
        """
        Simulate phenotypes: P = G + E
        Var(E) determined by H2.
        Var(P) = Var(G) / H2
        Var(E) = Var(P) - Var(G) = Var(G)*(1/H2 - 1)
        """
        # Calculate Genetic Variance of *current* population
        bvs = [ind.breeding_value for ind in population]
        # Needs BVs to be calculated first
        if any(b is None for b in bvs):
            raise ValueError("Breeding values must be calculated before phenotypes")
            
        var_g = np.var(bvs)
        
        if var_g == 0:
            var_e = 1.0 # arbitrary if no variation
        else:
            var_e = var_g * (1/h2 - 1)
            
        # Add environmental noise
        sigma_e = np.sqrt(var_e)
        
        for ind in population:
            env_effect = np.random.normal(0, sigma_e)
            ind.phenotype = ind.breeding_value + env_effect
            
        return population

# Global instance
genetic_algorithm = GeneticAlgorithmService()
