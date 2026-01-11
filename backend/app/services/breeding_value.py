"""
Breeding Value Estimation Service
BLUP, GBLUP, and genomic prediction methods
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
import math


class BreedingValueService:
    """Service for breeding value estimation and genomic prediction"""
    
    def __init__(self):
        # In-memory storage
        self.analyses: Dict[str, Dict] = {}
        self.breeding_values: Dict[str, List[Dict]] = {}
    
    def estimate_blup(
        self,
        phenotypes: List[Dict[str, Any]],
        pedigree: Optional[List[Dict[str, str]]] = None,
        fixed_effects: Optional[List[str]] = None,
        trait: str = "value",
        heritability: float = 0.3,
    ) -> Dict:
        """
        Estimate breeding values using BLUP (Best Linear Unbiased Prediction)
        Simplified implementation using Henderson's mixed model equations
        """
        n = len(phenotypes)
        if n < 3:
            return {"error": "Need at least 3 observations"}
        
        # Extract values
        ids = [p.get("id", f"IND-{i}") for i, p in enumerate(phenotypes)]
        values = [p[trait] for p in phenotypes]
        
        # Calculate overall mean
        overall_mean = sum(values) / n
        
        # Calculate variance components
        variance = sum((v - overall_mean) ** 2 for v in values) / (n - 1)
        genetic_variance = heritability * variance
        residual_variance = (1 - heritability) * variance
        
        # Simplified BLUP: EBV = h² × (phenotype - mean)
        # This is a simplified version; full BLUP requires matrix operations
        lambda_val = residual_variance / genetic_variance if genetic_variance > 0 else 1
        
        breeding_values = []
        for i, (ind_id, value) in enumerate(zip(ids, values)):
            deviation = value - overall_mean
            ebv = heritability * deviation
            reliability = heritability / (1 + lambda_val)  # Simplified reliability
            
            breeding_values.append({
                "individual_id": ind_id,
                "phenotype": value,
                "deviation": round(deviation, 4),
                "ebv": round(ebv, 4),
                "reliability": round(reliability, 4),
            })
        
        # Sort by EBV
        breeding_values.sort(key=lambda x: x["ebv"], reverse=True)
        
        # Add rank
        for i, bv in enumerate(breeding_values):
            bv["rank"] = i + 1
        
        # Store analysis
        analysis_id = str(uuid4())
        analysis = {
            "analysis_id": analysis_id,
            "method": "BLUP",
            "trait": trait,
            "n_individuals": n,
            "heritability": heritability,
            "overall_mean": round(overall_mean, 4),
            "genetic_variance": round(genetic_variance, 4),
            "residual_variance": round(residual_variance, 4),
            "breeding_values": breeding_values,
            "top_10": breeding_values[:10],
            "created_at": datetime.now().isoformat(),
        }
        
        self.analyses[analysis_id] = analysis
        
        return analysis
    
    def estimate_gblup(
        self,
        phenotypes: List[Dict[str, Any]],
        markers: List[Dict[str, Any]],
        trait: str = "value",
        heritability: float = 0.3,
    ) -> Dict:
        """
        Estimate genomic breeding values using GBLUP
        Uses genomic relationship matrix (G-matrix)
        """
        n = len(phenotypes)
        if n < 3:
            return {"error": "Need at least 3 observations"}
        
        if len(markers) != n:
            return {"error": "Number of marker records must match phenotypes"}
        
        # Extract values
        ids = [p.get("id", f"IND-{i}") for i, p in enumerate(phenotypes)]
        values = [p[trait] for p in phenotypes]
        
        # Calculate overall mean
        overall_mean = sum(values) / n
        
        # Calculate G-matrix (simplified - using marker similarity)
        # In practice, this would use VanRaden's method
        g_matrix = self._calculate_g_matrix(markers)
        
        # Calculate variance components
        variance = sum((v - overall_mean) ** 2 for v in values) / (n - 1)
        genetic_variance = heritability * variance
        residual_variance = (1 - heritability) * variance
        
        # Simplified GBLUP: GEBV = h² × G × (phenotype - mean) / diag(G)
        breeding_values = []
        for i, (ind_id, value) in enumerate(zip(ids, values)):
            deviation = value - overall_mean
            
            # Weight by genomic relationship
            g_weight = g_matrix[i][i] if g_matrix else 1
            gebv = heritability * deviation * g_weight
            
            # Reliability based on genomic information
            reliability = heritability * g_weight
            
            breeding_values.append({
                "individual_id": ind_id,
                "phenotype": value,
                "deviation": round(deviation, 4),
                "gebv": round(gebv, 4),
                "reliability": round(min(reliability, 0.99), 4),
                "g_diagonal": round(g_weight, 4),
            })
        
        # Sort by GEBV
        breeding_values.sort(key=lambda x: x["gebv"], reverse=True)
        
        for i, bv in enumerate(breeding_values):
            bv["rank"] = i + 1
        
        analysis_id = str(uuid4())
        analysis = {
            "analysis_id": analysis_id,
            "method": "GBLUP",
            "trait": trait,
            "n_individuals": n,
            "n_markers": len(markers[0].get("genotypes", [])) if markers else 0,
            "heritability": heritability,
            "overall_mean": round(overall_mean, 4),
            "genetic_variance": round(genetic_variance, 4),
            "residual_variance": round(residual_variance, 4),
            "breeding_values": breeding_values,
            "top_10": breeding_values[:10],
            "created_at": datetime.now().isoformat(),
        }
        
        self.analyses[analysis_id] = analysis
        
        return analysis
    
    def _calculate_g_matrix(self, markers: List[Dict[str, Any]]) -> List[List[float]]:
        """Calculate genomic relationship matrix (simplified)"""
        n = len(markers)
        g_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i, n):
                # Calculate similarity based on shared alleles
                geno_i = markers[i].get("genotypes", [])
                geno_j = markers[j].get("genotypes", [])
                
                if geno_i and geno_j and len(geno_i) == len(geno_j):
                    matches = sum(1 for a, b in zip(geno_i, geno_j) if a == b)
                    similarity = matches / len(geno_i)
                else:
                    similarity = 1.0 if i == j else 0.5
                
                g_matrix[i][j] = similarity
                g_matrix[j][i] = similarity
        
        return g_matrix
    
    def predict_cross(
        self,
        parent1_ebv: float,
        parent2_ebv: float,
        trait_mean: float,
        heritability: float = 0.3,
    ) -> Dict:
        """
        Predict offspring performance from cross
        """
        # Mid-parent value
        mid_parent = (parent1_ebv + parent2_ebv) / 2
        
        # Predicted offspring EBV
        offspring_ebv = mid_parent
        
        # Predicted phenotype
        predicted_phenotype = trait_mean + offspring_ebv
        
        # Mendelian sampling variance
        mendelian_variance = 0.5 * heritability * (1 - heritability)
        
        return {
            "parent1_ebv": parent1_ebv,
            "parent2_ebv": parent2_ebv,
            "mid_parent_value": round(mid_parent, 4),
            "offspring_ebv": round(offspring_ebv, 4),
            "predicted_phenotype": round(predicted_phenotype, 4),
            "mendelian_sampling_sd": round(math.sqrt(mendelian_variance), 4),
            "prediction_range": {
                "low": round(predicted_phenotype - 2 * math.sqrt(mendelian_variance), 4),
                "high": round(predicted_phenotype + 2 * math.sqrt(mendelian_variance), 4),
            },
        }
    
    def calculate_accuracy(
        self,
        predicted: List[float],
        observed: List[float],
    ) -> Dict:
        """Calculate prediction accuracy"""
        n = len(predicted)
        if n != len(observed) or n < 3:
            return {"error": "Need matching lists with at least 3 values"}
        
        # Correlation
        mean_pred = sum(predicted) / n
        mean_obs = sum(observed) / n
        
        numerator = sum((p - mean_pred) * (o - mean_obs) for p, o in zip(predicted, observed))
        denom_pred = math.sqrt(sum((p - mean_pred) ** 2 for p in predicted))
        denom_obs = math.sqrt(sum((o - mean_obs) ** 2 for o in observed))
        
        correlation = numerator / (denom_pred * denom_obs) if denom_pred * denom_obs > 0 else 0
        
        # Mean squared error
        mse = sum((p - o) ** 2 for p, o in zip(predicted, observed)) / n
        rmse = math.sqrt(mse)
        
        # Bias
        bias = sum(p - o for p, o in zip(predicted, observed)) / n
        
        return {
            "n": n,
            "correlation": round(correlation, 4),
            "r_squared": round(correlation ** 2, 4),
            "mse": round(mse, 4),
            "rmse": round(rmse, 4),
            "bias": round(bias, 4),
        }
    
    def rank_candidates(
        self,
        breeding_values: List[Dict[str, Any]],
        selection_intensity: float = 0.1,
        ebv_key: str = "ebv",
    ) -> Dict:
        """Rank and select breeding candidates"""
        n = len(breeding_values)
        n_select = max(1, int(n * selection_intensity))
        
        # Sort by EBV
        sorted_bv = sorted(breeding_values, key=lambda x: x.get(ebv_key, 0), reverse=True)
        
        selected = sorted_bv[:n_select]
        
        # Calculate selection differential
        all_ebvs = [bv.get(ebv_key, 0) for bv in breeding_values]
        selected_ebvs = [bv.get(ebv_key, 0) for bv in selected]
        
        mean_all = sum(all_ebvs) / n if n > 0 else 0
        mean_selected = sum(selected_ebvs) / len(selected) if selected else 0
        
        return {
            "total_candidates": n,
            "n_selected": n_select,
            "selection_intensity": selection_intensity,
            "mean_ebv_all": round(mean_all, 4),
            "mean_ebv_selected": round(mean_selected, 4),
            "selection_differential": round(mean_selected - mean_all, 4),
            "selected": selected,
        }
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis results"""
        return self.analyses.get(analysis_id)
    
    def list_analyses(self) -> List[Dict]:
        """List all analyses"""
        return [
            {
                "analysis_id": a["analysis_id"],
                "method": a["method"],
                "trait": a["trait"],
                "n_individuals": a["n_individuals"],
                "created_at": a["created_at"],
            }
            for a in self.analyses.values()
        ]
    
    def get_methods(self) -> List[Dict]:
        """Get available breeding value estimation methods"""
        return [
            {
                "code": "blup",
                "name": "BLUP",
                "description": "Best Linear Unbiased Prediction using pedigree",
                "requires": ["phenotypes", "pedigree (optional)"],
            },
            {
                "code": "gblup",
                "name": "GBLUP",
                "description": "Genomic BLUP using marker data",
                "requires": ["phenotypes", "markers"],
            },
            {
                "code": "ssblup",
                "name": "ssGBLUP",
                "description": "Single-step GBLUP (pedigree + genomic)",
                "requires": ["phenotypes", "pedigree", "markers"],
                "status": "planned",
            },
        ]


# Singleton instance
breeding_value_service = BreedingValueService()
