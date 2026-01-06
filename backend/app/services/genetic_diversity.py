"""
Genetic Diversity Analysis Service

Provides population genetics analysis including diversity metrics,
genetic distances, and population structure analysis.
"""

from typing import Optional
import math
import random


# Demo populations
DEMO_POPULATIONS = [
    {
        "id": "pop1",
        "name": "Elite Lines 2024",
        "description": "Advanced breeding lines from 2024 cycle",
        "size": 48,
        "crop": "Rice",
        "program_id": "prog-001",
    },
    {
        "id": "pop2",
        "name": "Core Collection",
        "description": "Representative germplasm collection",
        "size": 200,
        "crop": "Rice",
        "program_id": "prog-001",
    },
    {
        "id": "pop3",
        "name": "Breeding Population",
        "description": "Active breeding population",
        "size": 96,
        "crop": "Rice",
        "program_id": "prog-001",
    },
    {
        "id": "pop4",
        "name": "Landrace Collection",
        "description": "Traditional varieties from diverse regions",
        "size": 150,
        "crop": "Rice",
        "program_id": "prog-001",
    },
]

# Pre-computed diversity metrics for demo
DIVERSITY_METRICS = {
    "pop1": {
        "shannon_index": 2.85,
        "simpson_index": 0.92,
        "evenness": 0.78,
        "allelic_richness": 4.2,
        "expected_heterozygosity": 0.68,
        "observed_heterozygosity": 0.62,
        "inbreeding_coefficient": 0.088,
        "effective_alleles": 3.8,
        "polymorphic_loci_percent": 85.5,
    },
    "pop2": {
        "shannon_index": 3.45,
        "simpson_index": 0.96,
        "evenness": 0.85,
        "allelic_richness": 6.8,
        "expected_heterozygosity": 0.82,
        "observed_heterozygosity": 0.75,
        "inbreeding_coefficient": 0.085,
        "effective_alleles": 5.2,
        "polymorphic_loci_percent": 95.2,
    },
    "pop3": {
        "shannon_index": 2.12,
        "simpson_index": 0.78,
        "evenness": 0.65,
        "allelic_richness": 3.1,
        "expected_heterozygosity": 0.52,
        "observed_heterozygosity": 0.48,
        "inbreeding_coefficient": 0.077,
        "effective_alleles": 2.8,
        "polymorphic_loci_percent": 72.3,
    },
    "pop4": {
        "shannon_index": 3.65,
        "simpson_index": 0.97,
        "evenness": 0.88,
        "allelic_richness": 7.5,
        "expected_heterozygosity": 0.85,
        "observed_heterozygosity": 0.80,
        "inbreeding_coefficient": 0.059,
        "effective_alleles": 5.8,
        "polymorphic_loci_percent": 97.8,
    },
}

# Genetic distance matrix (Nei's distance)
DISTANCE_MATRIX = {
    ("pop1", "pop2"): {"nei_distance": 0.35, "fst": 0.08},
    ("pop1", "pop3"): {"nei_distance": 0.22, "fst": 0.05},
    ("pop1", "pop4"): {"nei_distance": 0.42, "fst": 0.11},
    ("pop2", "pop3"): {"nei_distance": 0.42, "fst": 0.12},
    ("pop2", "pop4"): {"nei_distance": 0.18, "fst": 0.04},
    ("pop3", "pop4"): {"nei_distance": 0.48, "fst": 0.14},
}

# AMOVA results
AMOVA_RESULTS = {
    "among_populations": 8.0,
    "among_individuals": 12.0,
    "within_individuals": 80.0,
    "phi_st": 0.08,
    "phi_is": 0.13,
    "phi_it": 0.20,
}

# Admixture proportions for K=3
ADMIXTURE_PROPORTIONS = {
    "pop1": [0.70, 0.20, 0.10],
    "pop2": [0.20, 0.60, 0.20],
    "pop3": [0.45, 0.35, 0.20],
    "pop4": [0.15, 0.55, 0.30],
}


class GeneticDiversityService:
    """Service for genetic diversity analysis."""
    
    def __init__(self):
        self.populations = DEMO_POPULATIONS.copy()
    
    def list_populations(
        self,
        crop: Optional[str] = None,
        program_id: Optional[str] = None,
    ) -> list[dict]:
        """List available populations."""
        filtered = self.populations.copy()
        
        if crop:
            filtered = [p for p in filtered if p["crop"].lower() == crop.lower()]
        if program_id:
            filtered = [p for p in filtered if p["program_id"] == program_id]
        
        return filtered
    
    def get_population(self, population_id: str) -> Optional[dict]:
        """Get a single population by ID."""
        for pop in self.populations:
            if pop["id"] == population_id:
                return pop
        return None
    
    def get_diversity_metrics(self, population_id: str) -> Optional[dict]:
        """Get diversity metrics for a population."""
        if population_id not in DIVERSITY_METRICS:
            return None
        
        metrics = DIVERSITY_METRICS[population_id]
        pop = self.get_population(population_id)
        
        return {
            "population_id": population_id,
            "population_name": pop["name"] if pop else "Unknown",
            "sample_size": pop["size"] if pop else 0,
            "metrics": [
                {
                    "name": "Shannon Index (H)",
                    "value": metrics["shannon_index"],
                    "interpretation": self._interpret_shannon(metrics["shannon_index"]),
                    "range": [0, 4],
                },
                {
                    "name": "Simpson Index (D)",
                    "value": metrics["simpson_index"],
                    "interpretation": self._interpret_simpson(metrics["simpson_index"]),
                    "range": [0, 1],
                },
                {
                    "name": "Evenness (E)",
                    "value": metrics["evenness"],
                    "interpretation": self._interpret_evenness(metrics["evenness"]),
                    "range": [0, 1],
                },
                {
                    "name": "Allelic Richness",
                    "value": metrics["allelic_richness"],
                    "interpretation": self._interpret_allelic_richness(metrics["allelic_richness"]),
                    "range": [1, 10],
                },
                {
                    "name": "Expected Heterozygosity (He)",
                    "value": metrics["expected_heterozygosity"],
                    "interpretation": self._interpret_heterozygosity(metrics["expected_heterozygosity"]),
                    "range": [0, 1],
                },
                {
                    "name": "Observed Heterozygosity (Ho)",
                    "value": metrics["observed_heterozygosity"],
                    "interpretation": self._interpret_heterozygosity(metrics["observed_heterozygosity"]),
                    "range": [0, 1],
                },
                {
                    "name": "Inbreeding Coefficient (F)",
                    "value": metrics["inbreeding_coefficient"],
                    "interpretation": self._interpret_inbreeding(metrics["inbreeding_coefficient"]),
                    "range": [0, 1],
                },
                {
                    "name": "Effective Alleles (Ne)",
                    "value": metrics["effective_alleles"],
                    "interpretation": "Number of equally frequent alleles",
                    "range": [1, 10],
                },
                {
                    "name": "Polymorphic Loci (%)",
                    "value": metrics["polymorphic_loci_percent"],
                    "interpretation": self._interpret_polymorphism(metrics["polymorphic_loci_percent"]),
                    "range": [0, 100],
                },
            ],
            "recommendations": self._generate_recommendations(metrics),
        }
    
    def get_genetic_distances(
        self,
        population_ids: Optional[list[str]] = None,
    ) -> list[dict]:
        """Get pairwise genetic distances between populations."""
        distances = []
        
        for (pop1_id, pop2_id), values in DISTANCE_MATRIX.items():
            if population_ids and (pop1_id not in population_ids or pop2_id not in population_ids):
                continue
            
            pop1 = self.get_population(pop1_id)
            pop2 = self.get_population(pop2_id)
            
            distances.append({
                "population1_id": pop1_id,
                "population1_name": pop1["name"] if pop1 else "Unknown",
                "population2_id": pop2_id,
                "population2_name": pop2["name"] if pop2 else "Unknown",
                "nei_distance": values["nei_distance"],
                "fst": values["fst"],
                "differentiation": self._interpret_fst(values["fst"]),
            })
        
        return distances
    
    def get_amova_results(self) -> dict:
        """Get AMOVA (Analysis of Molecular Variance) results."""
        return {
            "variance_components": {
                "among_populations": AMOVA_RESULTS["among_populations"],
                "among_individuals": AMOVA_RESULTS["among_individuals"],
                "within_individuals": AMOVA_RESULTS["within_individuals"],
            },
            "fixation_indices": {
                "phi_st": AMOVA_RESULTS["phi_st"],
                "phi_is": AMOVA_RESULTS["phi_is"],
                "phi_it": AMOVA_RESULTS["phi_it"],
            },
            "interpretation": {
                "phi_st": "Differentiation among populations",
                "phi_is": "Inbreeding within populations",
                "phi_it": "Overall inbreeding",
            },
        }
    
    def get_admixture_proportions(self, k: int = 3) -> dict:
        """Get admixture proportions for population structure analysis."""
        proportions = []
        
        for pop in self.populations:
            pop_id = pop["id"]
            if pop_id in ADMIXTURE_PROPORTIONS:
                props = ADMIXTURE_PROPORTIONS[pop_id]
                proportions.append({
                    "population_id": pop_id,
                    "population_name": pop["name"],
                    "proportions": [
                        {"cluster": i + 1, "proportion": p}
                        for i, p in enumerate(props[:k])
                    ],
                })
        
        return {
            "k": k,
            "optimal_k": 3,
            "delta_k": 245.8,
            "populations": proportions,
        }
    
    def get_pca_data(self, population_ids: Optional[list[str]] = None) -> dict:
        """Generate PCA data for visualization."""
        # Define cluster centers for each population
        centers = {
            "pop1": (2.0, 1.0),
            "pop2": (-1.0, -0.5),
            "pop3": (0.5, -1.5),
            "pop4": (-1.5, 1.0),
        }
        spreads = {
            "pop1": 0.8,
            "pop2": 1.5,
            "pop3": 1.0,
            "pop4": 1.2,
        }
        
        points = []
        for pop in self.populations:
            if population_ids and pop["id"] not in population_ids:
                continue
            
            pop_id = pop["id"]
            center = centers.get(pop_id, (0, 0))
            spread = spreads.get(pop_id, 1.0)
            
            # Generate points around center
            for i in range(min(pop["size"], 50)):  # Limit to 50 points per pop
                x = center[0] + (random.random() - 0.5) * spread * 2
                y = center[1] + (random.random() - 0.5) * spread * 2
                points.append({
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "label": f"{pop['name'].split()[0]}_{i + 1}",
                    "group": pop["name"],
                    "population_id": pop_id,
                })
        
        return {
            "points": points,
            "variance_explained": {
                "pc1": 45.2,
                "pc2": 18.7,
                "pc3": 12.3,
            },
            "total_variance_explained": 76.2,
        }
    
    def get_summary_statistics(self) -> dict:
        """Get summary statistics across all populations."""
        total_samples = sum(p["size"] for p in self.populations)
        avg_he = sum(DIVERSITY_METRICS[p["id"]]["expected_heterozygosity"] for p in self.populations) / len(self.populations)
        avg_ho = sum(DIVERSITY_METRICS[p["id"]]["observed_heterozygosity"] for p in self.populations) / len(self.populations)
        
        return {
            "total_populations": len(self.populations),
            "total_samples": total_samples,
            "average_expected_heterozygosity": round(avg_he, 3),
            "average_observed_heterozygosity": round(avg_ho, 3),
            "average_fst": round(sum(v["fst"] for v in DISTANCE_MATRIX.values()) / len(DISTANCE_MATRIX), 3),
            "most_diverse_population": "Landrace Collection",
            "least_diverse_population": "Breeding Population",
        }
    
    # Helper methods for interpretation
    def _interpret_shannon(self, value: float) -> str:
        if value >= 3.0:
            return "Very high diversity"
        elif value >= 2.5:
            return "High diversity"
        elif value >= 2.0:
            return "Moderate diversity"
        else:
            return "Low diversity"
    
    def _interpret_simpson(self, value: float) -> str:
        if value >= 0.9:
            return "Extremely diverse"
        elif value >= 0.8:
            return "Very diverse"
        elif value >= 0.6:
            return "Moderately diverse"
        else:
            return "Low diversity"
    
    def _interpret_evenness(self, value: float) -> str:
        if value >= 0.8:
            return "Excellent balance"
        elif value >= 0.6:
            return "Well balanced"
        elif value >= 0.4:
            return "Some imbalance"
        else:
            return "Highly uneven"
    
    def _interpret_allelic_richness(self, value: float) -> str:
        if value >= 6.0:
            return "High richness"
        elif value >= 4.0:
            return "Good richness"
        elif value >= 2.0:
            return "Moderate richness"
        else:
            return "Low richness"
    
    def _interpret_heterozygosity(self, value: float) -> str:
        if value >= 0.7:
            return "High"
        elif value >= 0.5:
            return "Moderate"
        elif value >= 0.3:
            return "Low"
        else:
            return "Very low"
    
    def _interpret_inbreeding(self, value: float) -> str:
        if value >= 0.25:
            return "High inbreeding"
        elif value >= 0.125:
            return "Moderate inbreeding"
        elif value >= 0.05:
            return "Low inbreeding"
        else:
            return "Minimal inbreeding"
    
    def _interpret_polymorphism(self, value: float) -> str:
        if value >= 90:
            return "Highly polymorphic"
        elif value >= 70:
            return "Moderately polymorphic"
        elif value >= 50:
            return "Low polymorphism"
        else:
            return "Very low polymorphism"
    
    def _interpret_fst(self, value: float) -> str:
        if value < 0.05:
            return "Low"
        elif value < 0.15:
            return "Moderate"
        elif value < 0.25:
            return "High"
        else:
            return "Very high"
    
    def _generate_recommendations(self, metrics: dict) -> list[str]:
        """Generate recommendations based on diversity metrics."""
        recommendations = []
        
        # Inbreeding check
        f = metrics["inbreeding_coefficient"]
        if f > 0.1:
            recommendations.append("High inbreeding detected. Consider introducing new genetic material.")
        elif f > 0.05:
            recommendations.append("Monitor inbreeding coefficient to prevent inbreeding depression.")
        
        # Heterozygosity check
        he = metrics["expected_heterozygosity"]
        ho = metrics["observed_heterozygosity"]
        if ho < he * 0.8:
            recommendations.append("Observed heterozygosity is lower than expected. Check for population substructure.")
        
        # Allelic richness
        ar = metrics["allelic_richness"]
        if ar < 3.0:
            recommendations.append("Low allelic richness. Consider introgression from diverse sources.")
        
        # Polymorphism
        poly = metrics["polymorphic_loci_percent"]
        if poly < 80:
            recommendations.append("Consider increasing marker density for better diversity assessment.")
        
        # General recommendations
        recommendations.append("Maintain effective population size (Ne) above 50 to avoid genetic drift.")
        recommendations.append("Use molecular markers to identify unique alleles for conservation.")
        
        return recommendations


# Singleton instance
_service = None

def get_genetic_diversity_service() -> GeneticDiversityService:
    """Get the genetic diversity service singleton."""
    global _service
    if _service is None:
        _service = GeneticDiversityService()
    return _service
