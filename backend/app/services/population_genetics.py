"""
Population Genetics Service

Provides population structure analysis, PCA, Fst calculations,
Hardy-Weinberg equilibrium tests, and migration rate estimation.
"""

from typing import Optional
import math
import random


# Demo populations with genetic data
DEMO_POPULATIONS = [
    {
        "id": "pop1",
        "name": "Elite Lines 2024",
        "description": "Advanced breeding lines from 2024 cycle",
        "size": 120,
        "region": "South Asia",
        "crop": "Rice",
        "admixture": [0.70, 0.20, 0.10],
    },
    {
        "id": "pop2",
        "name": "Core Collection",
        "description": "Representative germplasm collection",
        "size": 95,
        "region": "East Asia",
        "crop": "Rice",
        "admixture": [0.15, 0.75, 0.10],
    },
    {
        "id": "pop3",
        "name": "Landrace Collection",
        "description": "Traditional varieties from diverse regions",
        "size": 78,
        "region": "Africa",
        "crop": "Rice",
        "admixture": [0.10, 0.15, 0.75],
    },
    {
        "id": "pop4",
        "name": "Breeding Population",
        "description": "Active breeding population",
        "size": 85,
        "region": "Europe",
        "crop": "Rice",
        "admixture": [0.40, 0.35, 0.25],
    },
    {
        "id": "pop5",
        "name": "Introgression Lines",
        "description": "Lines with wild species introgressions",
        "size": 62,
        "region": "Americas",
        "crop": "Rice",
        "admixture": [0.30, 0.25, 0.45],
    },
]

# Pairwise Fst values
FST_MATRIX = {
    ("pop1", "pop2"): 0.082,
    ("pop1", "pop3"): 0.145,
    ("pop1", "pop4"): 0.048,
    ("pop1", "pop5"): 0.095,
    ("pop2", "pop3"): 0.168,
    ("pop2", "pop4"): 0.095,
    ("pop2", "pop5"): 0.112,
    ("pop3", "pop4"): 0.152,
    ("pop3", "pop5"): 0.138,
    ("pop4", "pop5"): 0.065,
}

# Hardy-Weinberg test results per population
HW_RESULTS = {
    "pop1": {"chi_square": 3.45, "p_value": 0.178, "in_equilibrium": True, "loci_tested": 50, "loci_deviated": 3},
    "pop2": {"chi_square": 8.92, "p_value": 0.012, "in_equilibrium": False, "loci_tested": 50, "loci_deviated": 8},
    "pop3": {"chi_square": 2.18, "p_value": 0.336, "in_equilibrium": True, "loci_tested": 50, "loci_deviated": 2},
    "pop4": {"chi_square": 5.67, "p_value": 0.059, "in_equilibrium": True, "loci_tested": 50, "loci_deviated": 5},
    "pop5": {"chi_square": 12.34, "p_value": 0.002, "in_equilibrium": False, "loci_tested": 50, "loci_deviated": 11},
}

# Population statistics
POP_STATISTICS = {
    "pop1": {"he": 0.72, "ho": 0.68, "fis": 0.055, "allelic_richness": 4.8, "private_alleles": 12},
    "pop2": {"he": 0.68, "ho": 0.62, "fis": 0.088, "allelic_richness": 4.2, "private_alleles": 8},
    "pop3": {"he": 0.82, "ho": 0.78, "fis": 0.049, "allelic_richness": 6.5, "private_alleles": 25},
    "pop4": {"he": 0.65, "ho": 0.60, "fis": 0.077, "allelic_richness": 3.8, "private_alleles": 5},
    "pop5": {"he": 0.75, "ho": 0.70, "fis": 0.067, "allelic_richness": 5.2, "private_alleles": 18},
}


class PopulationGeneticsService:
    """Service for population genetics analysis."""
    
    def __init__(self):
        self.populations = DEMO_POPULATIONS.copy()
    
    def list_populations(
        self,
        crop: Optional[str] = None,
        region: Optional[str] = None,
    ) -> list[dict]:
        """List available populations."""
        filtered = self.populations.copy()
        
        if crop:
            filtered = [p for p in filtered if p["crop"].lower() == crop.lower()]
        if region:
            filtered = [p for p in filtered if region.lower() in p["region"].lower()]
        
        # Add statistics to each population
        for pop in filtered:
            stats = POP_STATISTICS.get(pop["id"], {})
            pop["statistics"] = stats
        
        return filtered
    
    def get_population(self, population_id: str) -> Optional[dict]:
        """Get a single population by ID."""
        for pop in self.populations:
            if pop["id"] == population_id:
                pop["statistics"] = POP_STATISTICS.get(pop["id"], {})
                return pop
        return None
    
    def get_structure_analysis(self, k: int = 3, population_ids: Optional[list[str]] = None) -> dict:
        """Get STRUCTURE/ADMIXTURE analysis results."""
        populations = self.populations
        if population_ids:
            populations = [p for p in populations if p["id"] in population_ids]
        
        # Calculate delta K for different K values
        delta_k_values = []
        for k_val in range(2, 11):
            if k_val == 3:
                delta_k = 245.8
            elif k_val == 4:
                delta_k = 85.2
            elif k_val == 5:
                delta_k = 42.1
            else:
                delta_k = random.uniform(5, 35)
            delta_k_values.append({"k": k_val, "delta_k": round(delta_k, 1)})
        
        # Get admixture proportions
        admixture_data = []
        for pop in populations:
            proportions = pop.get("admixture", [0.33, 0.33, 0.34])[:k]
            # Normalize to sum to 1
            total = sum(proportions)
            proportions = [p / total for p in proportions]
            
            admixture_data.append({
                "population_id": pop["id"],
                "population_name": pop["name"],
                "sample_size": pop["size"],
                "region": pop["region"],
                "proportions": [
                    {"cluster": i + 1, "proportion": round(p, 3)}
                    for i, p in enumerate(proportions)
                ],
            })
        
        return {
            "k": k,
            "optimal_k": 3,
            "delta_k_analysis": delta_k_values,
            "populations": admixture_data,
            "parameters": {
                "burn_in": 10000,
                "mcmc_iterations": 50000,
                "model": "admixture",
            },
        }
    
    def get_pca_results(self, population_ids: Optional[list[str]] = None) -> dict:
        """Get PCA results for population structure visualization."""
        # Define cluster centers for each population
        centers = {
            "pop1": (-2.5, 1.2),
            "pop2": (2.8, 1.8),
            "pop3": (0.2, -3.5),
            "pop4": (-0.5, 0.8),
            "pop5": (0.8, -0.5),
        }
        
        populations = self.populations
        if population_ids:
            populations = [p for p in populations if p["id"] in population_ids]
        
        samples = []
        for pop in populations:
            center = centers.get(pop["id"], (0, 0))
            spread = 0.8
            
            # Generate sample points
            for i in range(min(pop["size"], 30)):  # Limit samples for performance
                pc1 = center[0] + (random.random() - 0.5) * spread * 2
                pc2 = center[1] + (random.random() - 0.5) * spread * 2
                pc3 = (random.random() - 0.5) * spread
                
                samples.append({
                    "sample_id": f"{pop['name'][:2].upper()}{i + 1:03d}",
                    "population_id": pop["id"],
                    "population_name": pop["name"],
                    "pc1": round(pc1, 3),
                    "pc2": round(pc2, 3),
                    "pc3": round(pc3, 3),
                })
        
        return {
            "samples": samples,
            "variance_explained": [
                {"pc": "PC1", "variance": 32.5, "cumulative": 32.5},
                {"pc": "PC2", "variance": 18.2, "cumulative": 50.7},
                {"pc": "PC3", "variance": 12.8, "cumulative": 63.5},
                {"pc": "PC4", "variance": 8.5, "cumulative": 72.0},
                {"pc": "PC5", "variance": 5.2, "cumulative": 77.2},
            ],
            "total_samples": len(samples),
            "total_populations": len(populations),
        }
    
    def get_fst_analysis(self, population_ids: Optional[list[str]] = None) -> dict:
        """Get pairwise Fst analysis."""
        pairwise_fst = []
        
        for (pop1_id, pop2_id), fst in FST_MATRIX.items():
            if population_ids:
                if pop1_id not in population_ids or pop2_id not in population_ids:
                    continue
            
            pop1 = self.get_population(pop1_id)
            pop2 = self.get_population(pop2_id)
            
            # Calculate Nm (number of migrants) from Fst
            # Nm = (1 - Fst) / (4 * Fst)
            nm = (1 - fst) / (4 * fst) if fst > 0 else float('inf')
            
            pairwise_fst.append({
                "population1_id": pop1_id,
                "population1_name": pop1["name"] if pop1 else "Unknown",
                "population2_id": pop2_id,
                "population2_name": pop2["name"] if pop2 else "Unknown",
                "fst": fst,
                "nm": round(nm, 2),
                "differentiation": self._interpret_fst(fst),
                "p_value": 0.001,  # Simulated
            })
        
        # Calculate global Fst
        all_fst = list(FST_MATRIX.values())
        global_fst = sum(all_fst) / len(all_fst)
        
        # Calculate mean statistics
        all_stats = list(POP_STATISTICS.values())
        mean_he = sum(s["he"] for s in all_stats) / len(all_stats)
        mean_ho = sum(s["ho"] for s in all_stats) / len(all_stats)
        mean_fis = sum(s["fis"] for s in all_stats) / len(all_stats)
        
        return {
            "pairwise": pairwise_fst,
            "global_statistics": {
                "global_fst": round(global_fst, 3),
                "mean_he": round(mean_he, 3),
                "mean_ho": round(mean_ho, 3),
                "mean_fis": round(mean_fis, 3),
            },
            "interpretation": {
                "fst_ranges": [
                    {"range": "0-0.05", "level": "Little", "description": "Little genetic differentiation"},
                    {"range": "0.05-0.15", "level": "Moderate", "description": "Moderate differentiation"},
                    {"range": "0.15-0.25", "level": "Great", "description": "Great differentiation"},
                    {"range": ">0.25", "level": "Very great", "description": "Very great differentiation"},
                ],
            },
        }
    
    def get_hardy_weinberg_test(self, population_id: str) -> Optional[dict]:
        """Get Hardy-Weinberg equilibrium test results for a population."""
        if population_id not in HW_RESULTS:
            return None
        
        pop = self.get_population(population_id)
        hw = HW_RESULTS[population_id]
        
        return {
            "population_id": population_id,
            "population_name": pop["name"] if pop else "Unknown",
            "chi_square": hw["chi_square"],
            "p_value": hw["p_value"],
            "in_equilibrium": hw["in_equilibrium"],
            "loci_tested": hw["loci_tested"],
            "loci_deviated": hw["loci_deviated"],
            "deviation_percent": round(hw["loci_deviated"] / hw["loci_tested"] * 100, 1),
            "interpretation": self._interpret_hw(hw["in_equilibrium"], hw["p_value"]),
        }
    
    def get_migration_rates(self, population_ids: Optional[list[str]] = None) -> dict:
        """Calculate migration rates between populations."""
        migrations = []
        
        for (pop1_id, pop2_id), fst in FST_MATRIX.items():
            if population_ids:
                if pop1_id not in population_ids or pop2_id not in population_ids:
                    continue
            
            pop1 = self.get_population(pop1_id)
            pop2 = self.get_population(pop2_id)
            
            # Calculate Nm from Fst
            nm = (1 - fst) / (4 * fst) if fst > 0 else float('inf')
            
            migrations.append({
                "from_population_id": pop1_id,
                "from_population_name": pop1["name"] if pop1 else "Unknown",
                "to_population_id": pop2_id,
                "to_population_name": pop2["name"] if pop2 else "Unknown",
                "nm": round(nm, 2),
                "gene_flow": self._interpret_gene_flow(nm),
            })
        
        return {
            "migrations": migrations,
            "interpretation": {
                "nm_threshold": 1.0,
                "description": "Nm > 1 indicates sufficient gene flow to prevent genetic differentiation by drift",
            },
        }
    
    def get_population_statistics(self, population_id: str) -> Optional[dict]:
        """Get detailed statistics for a population."""
        pop = self.get_population(population_id)
        if not pop:
            return None
        
        stats = POP_STATISTICS.get(population_id, {})
        hw = HW_RESULTS.get(population_id, {})
        
        return {
            "population_id": population_id,
            "population_name": pop["name"],
            "sample_size": pop["size"],
            "region": pop["region"],
            "diversity_metrics": {
                "expected_heterozygosity": stats.get("he", 0),
                "observed_heterozygosity": stats.get("ho", 0),
                "inbreeding_coefficient": stats.get("fis", 0),
                "allelic_richness": stats.get("allelic_richness", 0),
                "private_alleles": stats.get("private_alleles", 0),
            },
            "hardy_weinberg": {
                "chi_square": hw.get("chi_square", 0),
                "p_value": hw.get("p_value", 1),
                "in_equilibrium": hw.get("in_equilibrium", True),
            },
            "recommendations": self._generate_recommendations(stats, hw),
        }
    
    def get_summary_statistics(self) -> dict:
        """Get summary statistics across all populations."""
        total_samples = sum(p["size"] for p in self.populations)
        all_stats = list(POP_STATISTICS.values())
        
        return {
            "total_populations": len(self.populations),
            "total_samples": total_samples,
            "mean_expected_heterozygosity": round(sum(s["he"] for s in all_stats) / len(all_stats), 3),
            "mean_observed_heterozygosity": round(sum(s["ho"] for s in all_stats) / len(all_stats), 3),
            "mean_inbreeding_coefficient": round(sum(s["fis"] for s in all_stats) / len(all_stats), 3),
            "mean_allelic_richness": round(sum(s["allelic_richness"] for s in all_stats) / len(all_stats), 2),
            "total_private_alleles": sum(s["private_alleles"] for s in all_stats),
            "global_fst": round(sum(FST_MATRIX.values()) / len(FST_MATRIX), 3),
            "most_diverse_population": "Landrace Collection",
            "least_diverse_population": "Breeding Population",
        }
    
    def _interpret_fst(self, fst: float) -> str:
        """Interpret Fst value."""
        if fst < 0.05:
            return "Little"
        elif fst < 0.15:
            return "Moderate"
        elif fst < 0.25:
            return "Great"
        else:
            return "Very great"
    
    def _interpret_gene_flow(self, nm: float) -> str:
        """Interpret gene flow based on Nm."""
        if nm > 4:
            return "High"
        elif nm > 1:
            return "Moderate"
        else:
            return "Low"
    
    def _interpret_hw(self, in_equilibrium: bool, p_value: float) -> str:
        """Interpret Hardy-Weinberg test results."""
        if in_equilibrium:
            return f"Population is in Hardy-Weinberg equilibrium (p = {p_value:.3f}). Random mating assumed."
        else:
            return f"Population deviates from Hardy-Weinberg equilibrium (p = {p_value:.3f}). Check for selection, non-random mating, or population structure."
    
    def _generate_recommendations(self, stats: dict, hw: dict) -> list[str]:
        """Generate recommendations based on population statistics."""
        recommendations = []
        
        # Inbreeding check
        fis = stats.get("fis", 0)
        if fis > 0.1:
            recommendations.append("High inbreeding detected. Consider introducing new genetic material.")
        elif fis > 0.05:
            recommendations.append("Monitor inbreeding levels to prevent inbreeding depression.")
        
        # Heterozygosity check
        he = stats.get("he", 0)
        ho = stats.get("ho", 0)
        if ho < he * 0.85:
            recommendations.append("Observed heterozygosity is lower than expected. Check for population substructure or inbreeding.")
        
        # Hardy-Weinberg check
        if not hw.get("in_equilibrium", True):
            recommendations.append("Population deviates from Hardy-Weinberg equilibrium. Investigate potential causes (selection, migration, non-random mating).")
        
        # Allelic richness
        ar = stats.get("allelic_richness", 0)
        if ar < 4.0:
            recommendations.append("Low allelic richness. Consider introgression from diverse sources.")
        
        # Private alleles
        pa = stats.get("private_alleles", 0)
        if pa > 15:
            recommendations.append(f"Population has {pa} private alleles. Consider conservation priority.")
        
        return recommendations


# Singleton instance
_service = None


def get_population_genetics_service() -> PopulationGeneticsService:
    """Get the population genetics service singleton."""
    global _service
    if _service is None:
        _service = PopulationGeneticsService()
    return _service
