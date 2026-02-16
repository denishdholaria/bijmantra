
import pytest
import numpy as np
from app.services.simulation import genetic_algorithm, SimulatedGenotype, GeneticAlgorithmService

@pytest.fixture
def service():
    return genetic_algorithm

class TestGeneticAlgorithm:
    def test_phase_from_dosage(self, service):
        """Test conversion of dosage to phased genome"""
        # Dosage: 0, 1, 2
        dosage = [0, 1, 2]
        genome = service.phase_from_dosage(dosage)
        
        assert genome.shape == (2, 3)
        # Locus 0 (val 0) -> [0, 0]
        assert np.all(genome[:, 0] == 0)
        
        # Locus 1 (val 1) -> [0, 1] or [1, 0]
        assert np.sum(genome[:, 1]) == 1
        
        # Locus 2 (val 2) -> [1, 1]
        assert np.all(genome[:, 2] == 1)

    def test_mendelian_segregation(self, service):
        """Test 1:2:1 ratio for heterozygote cross (1 x 1)"""
        # Create F1 parents (Heterozygous at 1 locus)
        # 1 -> [0, 1]
        p1_genome = np.array([[0], [1]])
        p2_genome = np.array([[0], [1]])
        
        p1 = SimulatedGenotype("P1", ("?", "?"), p1_genome, 0)
        p2 = SimulatedGenotype("P2", ("?", "?"), p2_genome, 0)
        
        # Generate large no. of offspring
        n = 1000
        offspring = service.cross(p1, p2, n_progeny=n)
        
        # Check genotypes
        dosages = [np.sum(ind.genome) for ind in offspring]
        counts = {0: 0, 1: 0, 2: 0}
        for d in dosages: counts[d] += 1
        
        # Expected: 250, 500, 250
        # Allow some stochastic error (check percentages)
        assert 0.20 < counts[0] / n < 0.30
        assert 0.45 < counts[1] / n < 0.55
        assert 0.20 < counts[2] / n < 0.30

    def test_recombination_linkage(self, service):
        """Test linkage: recombination_rate = 0.0 vs 0.5"""
        # Parent: Heterozygous at 2 loci, in coupling phase?
        # Let's define phased genome manually
        # Chr 0: [0, 0]
        # Chr 1: [1, 1]
        # Dosage is [1, 1] for both loci.
        
        genome = np.array([[0, 0], [1, 1]])
        parent = SimulatedGenotype("P1", ("?", "?"), genome, 0)
        
        # Case A: Complete Linkage (r=0)
        # Gametes should be [0, 0] or [1, 1]. Never [0, 1] or [1, 0].
        gametes_linked = []
        for _ in range(100):
            g = service._create_gamete(genome, recombination_rate=0.0)
            gametes_linked.append(g)
            
        for g in gametes_linked:
            # g is (2,) 1D array
            # Check if loci are same
            assert g[0] == g[1], "Recombination occurred despite r=0"
            
        # Case B: Unlinked (r=0.5)
        # Should see recombinants [0, 1] or [1, 0]
        recombinants = 0
        for _ in range(200):
            g = service._create_gamete(genome, recombination_rate=0.5)
            # Check if alleles differ (since parent was [0,0] and [1,1] at the two loci? No, Wait)
            # Parent Genome: [[0, 0], [1, 1]]
            # If gamete picks chr0 for locus 0 -> gets 0.
            # If gamete picks chr0 for locus 1 -> gets 0. (Parental)
            # If gamete picks chr1 for locus 1 -> gets 1. (Recombinant)
            
            # So if g[0] != g[1], it means valid recombinant?
            # Yes, because at locus 0, alleles are 0 (chr0) and 1 (chr1). No wait.
            # Genome is [[0, 0], [1, 1]].
            # Locus 0: Alleles are 0, 1. (Index 0 is 0, Index 1 is 1).
            # Locus 1: Alleles are 0, 1.
            # So if we pick Chr0 at Loc0 -> allele 0.
            # If we pick Chr0 at Loc1 -> allele 0.
            # g = [0, 0] (Parental)
            
            # If we pick Chr1 at Loc0 -> allele 1.
            # If we pick Chr1 at Loc1 -> allele 1.
            # g = [1, 1] (Parental)
            
            # Recombinants: [0, 1] or [1, 0].
            # In these cases, g[0] != g[1].
            
            if g[0] != g[1]:
                recombinants += 1
                
        # Expect approx 50% recombinants
        assert 0.40 < recombinants / 200 < 0.60

    def test_selection_response(self, service):
        """Test if selection increases mean phenotype"""
        # Create population of 100 random individuals at 1 locus
        pop = []
        for i in range(100):
            # Random dosage 0, 1, 2
            d = np.random.randint(0, 3, size=1)
            g = service.phase_from_dosage(d)
            ind = SimulatedGenotype(f"Ind_{i}", ("?", "?"), g, 0)
            pop.append(ind)
            
        # Effect of allele 1 = +1.0
        effects = np.array([1.0])
        service.calculate_breeding_values(pop, effects)
        
        # Calculate initial mean BV
        mean_initial = np.mean([ind.breeding_value for ind in pop])
        
        # Select top 10
        selected = service.select(pop, n_select=10, criterion="breeding_value")
        mean_selected = np.mean([ind.breeding_value for ind in selected])
        
        # Selected mean should be higher (unless all same)
        # With random int(0,3), we should have variation
        assert mean_selected >= mean_initial
        # Check size
        assert len(selected) == 10

