"""
Statistics Service
Statistical analysis and summaries for breeding data
"""
from typing import Optional
import math
import random


class StatisticsService:
    """Service for statistical analysis of breeding data."""
    
    def __init__(self):
        # Demo trait data
        self._traits = [
            {"id": "yield", "name": "Yield", "unit": "t/ha"},
            {"id": "plant_height", "name": "Plant Height", "unit": "cm"},
            {"id": "days_to_maturity", "name": "Days to Maturity", "unit": "days"},
            {"id": "protein_content", "name": "Protein Content", "unit": "%"},
            {"id": "disease_score", "name": "Disease Score", "unit": "1-9"},
            {"id": "tgw", "name": "1000 Grain Weight", "unit": "g"},
            {"id": "tiller_count", "name": "Tiller Count", "unit": "count"},
            {"id": "grain_length", "name": "Grain Length", "unit": "mm"},
        ]
        
        # Demo trials
        self._trials = [
            {"id": "trial-2024", "name": "Trial 2024", "year": 2024, "genotypes": 45, "reps": 3},
            {"id": "trial-2023", "name": "Trial 2023", "year": 2023, "genotypes": 40, "reps": 3},
            {"id": "trial-2022", "name": "Trial 2022", "year": 2022, "genotypes": 35, "reps": 3},
        ]
    
    def get_trials(self) -> list:
        """Get available trials for analysis."""
        return self._trials
    
    def get_traits(self) -> list:
        """Get available traits."""
        return self._traits
    
    def get_summary_stats(
        self,
        trial_id: Optional[str] = None,
        trait_ids: Optional[list] = None,
    ) -> dict:
        """Get descriptive statistics for traits."""
        # Demo data generation based on trial
        trial = next((t for t in self._trials if t["id"] == trial_id), self._trials[0]) if trial_id else self._trials[0]
        n_base = trial["genotypes"] * trial["reps"]
        
        # Generate realistic stats for each trait
        trait_stats = {
            "yield": {"mean": 4.85, "std": 0.72, "min": 3.2, "max": 6.8},
            "plant_height": {"mean": 98.5, "std": 12.3, "min": 72, "max": 125},
            "days_to_maturity": {"mean": 118, "std": 8.5, "min": 98, "max": 135},
            "protein_content": {"mean": 12.3, "std": 1.4, "min": 9.5, "max": 15.2},
            "disease_score": {"mean": 6.8, "std": 1.9, "min": 2, "max": 9},
            "tgw": {"mean": 42.5, "std": 4.2, "min": 32, "max": 52},
            "tiller_count": {"mean": 12.5, "std": 2.8, "min": 6, "max": 20},
            "grain_length": {"mean": 7.2, "std": 0.8, "min": 5.5, "max": 9.0},
        }
        
        traits_to_use = trait_ids if trait_ids else [t["id"] for t in self._traits]
        
        stats = []
        for trait in self._traits:
            if trait["id"] not in traits_to_use:
                continue
            
            base = trait_stats.get(trait["id"], {"mean": 50, "std": 10, "min": 20, "max": 80})
            n = n_base - random.randint(0, 10)  # Some missing data
            cv = (base["std"] / base["mean"]) * 100 if base["mean"] > 0 else 0
            
            stats.append({
                "trait_id": trait["id"],
                "trait_name": trait["name"],
                "unit": trait["unit"],
                "n": n,
                "mean": round(base["mean"], 2),
                "std": round(base["std"], 2),
                "min": base["min"],
                "max": base["max"],
                "cv": round(cv, 1),
                "se": round(base["std"] / math.sqrt(n), 3),
                "variance": round(base["std"] ** 2, 2),
            })
        
        return {
            "trial_id": trial["id"],
            "trial_name": trial["name"],
            "stats": stats,
            "total_traits": len(stats),
        }
    
    def get_correlations(
        self,
        trial_id: Optional[str] = None,
        trait_ids: Optional[list] = None,
    ) -> dict:
        """Get correlation matrix between traits."""
        # Predefined correlations (realistic for breeding data)
        correlation_matrix = {
            ("yield", "plant_height"): 0.45,
            ("yield", "days_to_maturity"): 0.32,
            ("yield", "protein_content"): -0.28,
            ("yield", "disease_score"): 0.52,
            ("yield", "tgw"): 0.38,
            ("yield", "tiller_count"): 0.55,
            ("plant_height", "days_to_maturity"): 0.38,
            ("plant_height", "tgw"): 0.22,
            ("protein_content", "tgw"): 0.15,
            ("protein_content", "grain_length"): -0.12,
            ("disease_score", "yield"): 0.52,
            ("tgw", "grain_length"): 0.68,
            ("tiller_count", "plant_height"): -0.25,
        }
        
        traits_to_use = trait_ids if trait_ids else [t["id"] for t in self._traits[:6]]
        
        correlations = []
        for (t1, t2), r in correlation_matrix.items():
            if t1 in traits_to_use and t2 in traits_to_use:
                trait1 = next((t for t in self._traits if t["id"] == t1), None)
                trait2 = next((t for t in self._traits if t["id"] == t2), None)
                if trait1 and trait2:
                    # Determine strength
                    abs_r = abs(r)
                    if abs_r >= 0.7:
                        strength = "strong"
                    elif abs_r >= 0.4:
                        strength = "moderate"
                    elif abs_r >= 0.2:
                        strength = "weak"
                    else:
                        strength = "negligible"
                    
                    correlations.append({
                        "trait1_id": t1,
                        "trait1_name": trait1["name"],
                        "trait2_id": t2,
                        "trait2_name": trait2["name"],
                        "r": r,
                        "r_squared": round(r ** 2, 3),
                        "direction": "positive" if r > 0 else "negative",
                        "strength": strength,
                        "p_value": 0.001 if abs_r >= 0.3 else 0.05,  # Simplified
                        "significant": abs_r >= 0.2,
                    })
        
        return {
            "trial_id": trial_id,
            "correlations": correlations,
            "total": len(correlations),
        }
    
    def get_distribution(
        self,
        trial_id: Optional[str] = None,
        trait_id: str = "yield",
        bins: int = 10,
    ) -> dict:
        """Get distribution data for a trait."""
        trait = next((t for t in self._traits if t["id"] == trait_id), self._traits[0])
        
        # Generate realistic distribution data
        trait_params = {
            "yield": {"mean": 4.85, "std": 0.72, "min": 3.2, "max": 6.8},
            "plant_height": {"mean": 98.5, "std": 12.3, "min": 72, "max": 125},
            "days_to_maturity": {"mean": 118, "std": 8.5, "min": 98, "max": 135},
            "protein_content": {"mean": 12.3, "std": 1.4, "min": 9.5, "max": 15.2},
        }
        
        params = trait_params.get(trait_id, {"mean": 50, "std": 10, "min": 20, "max": 80})
        
        # Generate histogram bins
        bin_width = (params["max"] - params["min"]) / bins
        histogram = []
        total_count = 0
        
        for i in range(bins):
            bin_start = params["min"] + i * bin_width
            bin_end = bin_start + bin_width
            bin_center = (bin_start + bin_end) / 2
            
            # Normal distribution approximation
            z = (bin_center - params["mean"]) / params["std"]
            density = math.exp(-0.5 * z ** 2) / (params["std"] * math.sqrt(2 * math.pi))
            count = int(density * 150 * bin_width)  # Scale to ~150 observations
            total_count += count
            
            histogram.append({
                "bin_start": round(bin_start, 2),
                "bin_end": round(bin_end, 2),
                "bin_center": round(bin_center, 2),
                "count": count,
                "frequency": 0,  # Will calculate after
            })
        
        # Calculate frequencies
        for bin_data in histogram:
            bin_data["frequency"] = round(bin_data["count"] / total_count, 3) if total_count > 0 else 0
        
        # Quartiles
        q1 = params["mean"] - 0.675 * params["std"]
        q3 = params["mean"] + 0.675 * params["std"]
        iqr = q3 - q1
        
        return {
            "trait_id": trait_id,
            "trait_name": trait["name"],
            "unit": trait["unit"],
            "histogram": histogram,
            "summary": {
                "mean": params["mean"],
                "std": params["std"],
                "min": params["min"],
                "max": params["max"],
                "median": params["mean"],  # Approximation for normal
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2),
                "skewness": round(random.uniform(-0.3, 0.3), 2),
                "kurtosis": round(random.uniform(-0.5, 0.5), 2),
            },
            "n": total_count,
        }
    
    def get_overview(self, trial_id: Optional[str] = None) -> dict:
        """Get overview statistics."""
        trial = next((t for t in self._trials if t["id"] == trial_id), self._trials[0]) if trial_id else self._trials[0]
        
        return {
            "trial_id": trial["id"],
            "trial_name": trial["name"],
            "traits_analyzed": len(self._traits),
            "total_observations": trial["genotypes"] * trial["reps"] * len(self._traits),
            "genotypes": trial["genotypes"],
            "replications": trial["reps"],
            "locations": 1,
            "missing_data_pct": round(random.uniform(2, 8), 1),
            "data_quality_score": round(random.uniform(85, 98), 1),
        }
    
    def calculate_anova(
        self,
        trial_id: Optional[str] = None,
        trait_id: str = "yield",
    ) -> dict:
        """Calculate ANOVA for a trait."""
        trial = next((t for t in self._trials if t["id"] == trial_id), self._trials[0]) if trial_id else self._trials[0]
        trait = next((t for t in self._traits if t["id"] == trait_id), self._traits[0])
        
        # Simplified ANOVA results
        g = trial["genotypes"]
        r = trial["reps"]
        
        # Generate realistic ANOVA values
        ms_genotype = round(random.uniform(0.5, 2.0), 3)
        ms_rep = round(random.uniform(0.1, 0.5), 3)
        ms_error = round(random.uniform(0.05, 0.2), 3)
        
        f_genotype = round(ms_genotype / ms_error, 2)
        f_rep = round(ms_rep / ms_error, 2)
        
        return {
            "trait_id": trait_id,
            "trait_name": trait["name"],
            "sources": [
                {
                    "source": "Genotype",
                    "df": g - 1,
                    "ss": round(ms_genotype * (g - 1), 3),
                    "ms": ms_genotype,
                    "f_value": f_genotype,
                    "p_value": 0.001 if f_genotype > 3 else 0.05,
                    "significant": f_genotype > 2,
                },
                {
                    "source": "Replication",
                    "df": r - 1,
                    "ss": round(ms_rep * (r - 1), 3),
                    "ms": ms_rep,
                    "f_value": f_rep,
                    "p_value": 0.05 if f_rep > 2 else 0.1,
                    "significant": f_rep > 3,
                },
                {
                    "source": "Error",
                    "df": (g - 1) * (r - 1),
                    "ss": round(ms_error * (g - 1) * (r - 1), 3),
                    "ms": ms_error,
                    "f_value": None,
                    "p_value": None,
                    "significant": None,
                },
            ],
            "total_df": g * r - 1,
            "cv_percent": round((math.sqrt(ms_error) / 4.85) * 100, 1),  # Assuming yield mean
            "heritability": round(1 - (ms_error / ms_genotype), 2) if ms_genotype > ms_error else 0,
            "lsd_5pct": round(2.0 * math.sqrt(2 * ms_error / r), 3),
        }


# Singleton instance
statistics_service = StatisticsService()
