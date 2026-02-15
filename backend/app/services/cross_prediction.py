"""
Cross Prediction Service
Predict progeny performance from parental crosses

Features:
- Predict mean progeny performance
- Estimate genetic variance in progeny
- Calculate usefulness criterion
- Rank potential crosses
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.compute_engine import compute_engine
from app.models.biometrics import CrossPredictionResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@dataclass
class CrossPrediction:
    """Prediction for a single cross"""
    parent1_id: str
    parent2_id: str
    predicted_mean: float
    predicted_variance: float
    usefulness: float  # Mean + k * SD
    superior_progeny_prob: float  # P(progeny > threshold)
    inbreeding_coefficient: float
    genetic_distance: float


@dataclass
class CrossRanking:
    """Ranked list of crosses"""
    crosses: List[CrossPrediction]
    selection_intensity: float
    threshold: float
    method: str


class CrossPredictionService:
    """
    Service for predicting cross performance
    
    Methods:
    - Mid-parent value prediction
    - GBLUP-based prediction with GRM
    - Usefulness criterion (Schnell & Utz, 1975)
    - Optimal contribution selection
    """
    
    def __init__(self):
        self.compute = compute_engine
    
    def predict_cross_mean(
        self,
        parent1_gebv: float,
        parent2_gebv: float
    ) -> float:
        """
        Predict mean progeny performance (mid-parent value)
        
        For additive traits: E(progeny) = (GEBV1 + GEBV2) / 2
        """
        return (parent1_gebv + parent2_gebv) / 2
    
    def predict_cross_variance(
        self,
        parent1_genotypes: np.ndarray,
        parent2_genotypes: np.ndarray,
        marker_effects: np.ndarray
    ) -> float:
        """
        Predict genetic variance among progeny
        
        Var(progeny) = sum of (a_i^2 * p_i * (1-p_i))
        where a_i = marker effect, p_i = probability of inheriting allele
        """
        # For each marker, variance depends on parental heterozygosity
        n_markers = len(marker_effects)
        variance = 0.0
        
        for i in range(n_markers):
            g1, g2 = parent1_genotypes[i], parent2_genotypes[i]
            a = marker_effects[i]
            
            # Segregation variance depends on parental genotypes
            # Both homozygous same: no variance
            # Both homozygous different: all progeny heterozygous, no variance
            # One heterozygous: 0.25 variance
            # Both heterozygous: 0.5 variance
            
            if g1 == 1 and g2 == 1:  # Both het
                seg_var = 0.5
            elif g1 == 1 or g2 == 1:  # One het
                seg_var = 0.25
            else:
                seg_var = 0.0
            
            variance += (a ** 2) * seg_var
        
        return variance
    
    def calculate_usefulness(
        self,
        predicted_mean: float,
        predicted_variance: float,
        selection_intensity: float = 2.06  # Top 5%
    ) -> float:
        """
        Calculate usefulness criterion (Schnell & Utz, 1975)
        
        U = μ + i * σ
        
        where:
        - μ = predicted mean
        - i = selection intensity
        - σ = predicted standard deviation
        """
        predicted_sd = np.sqrt(predicted_variance) if predicted_variance > 0 else 0
        return predicted_mean + selection_intensity * predicted_sd
    
    def calculate_superior_progeny_probability(
        self,
        predicted_mean: float,
        predicted_variance: float,
        threshold: float
    ) -> float:
        """
        Calculate probability of progeny exceeding threshold
        
        P(progeny > threshold) = 1 - Φ((threshold - μ) / σ)
        """
        from scipy import stats
        
        if predicted_variance <= 0:
            return 1.0 if predicted_mean > threshold else 0.0
        
        predicted_sd = np.sqrt(predicted_variance)
        z = (threshold - predicted_mean) / predicted_sd
        return 1 - stats.norm.cdf(z)
    
    def calculate_inbreeding(
        self,
        parent1_genotypes: np.ndarray,
        parent2_genotypes: np.ndarray,
        grm: Optional[np.ndarray] = None,
        parent1_idx: Optional[int] = None,
        parent2_idx: Optional[int] = None
    ) -> float:
        """
        Calculate expected inbreeding coefficient of progeny
        
        F = 0.5 * (1 + f_12)
        where f_12 is the relationship between parents
        """
        if grm is not None and parent1_idx is not None and parent2_idx is not None:
            # Use GRM relationship
            relationship = grm[parent1_idx, parent2_idx]
            return 0.5 * (1 + relationship)
        
        # Estimate from genotype similarity
        n_markers = len(parent1_genotypes)
        ibs = np.sum(parent1_genotypes == parent2_genotypes) / n_markers
        return 0.5 * ibs
    
    def calculate_genetic_distance(
        self,
        parent1_genotypes: np.ndarray,
        parent2_genotypes: np.ndarray
    ) -> float:
        """
        Calculate genetic distance between parents
        
        Uses modified Rogers' distance
        """
        n_markers = len(parent1_genotypes)
        diff = np.abs(parent1_genotypes - parent2_genotypes)
        return np.sqrt(np.sum(diff ** 2) / (2 * n_markers))
    
    def predict_single_cross(
        self,
        parent1_id: str,
        parent2_id: str,
        parent1_gebv: float,
        parent2_gebv: float,
        parent1_genotypes: np.ndarray,
        parent2_genotypes: np.ndarray,
        marker_effects: Optional[np.ndarray] = None,
        selection_intensity: float = 2.06,
        threshold: Optional[float] = None
    ) -> CrossPrediction:
        """
        Predict performance of a single cross
        """
        # Predicted mean
        pred_mean = self.predict_cross_mean(parent1_gebv, parent2_gebv)
        
        # Predicted variance (if marker effects available)
        if marker_effects is not None:
            pred_var = self.predict_cross_variance(
                parent1_genotypes, parent2_genotypes, marker_effects
            )
        else:
            # Estimate from parental heterozygosity
            het1 = np.mean(parent1_genotypes == 1)
            het2 = np.mean(parent2_genotypes == 1)
            pred_var = 0.25 * (het1 + het2) * np.var([parent1_gebv, parent2_gebv])
        
        # Usefulness
        usefulness = self.calculate_usefulness(pred_mean, pred_var, selection_intensity)
        
        # Superior progeny probability
        if threshold is None:
            threshold = pred_mean  # Default: probability of exceeding mean
        sup_prob = self.calculate_superior_progeny_probability(pred_mean, pred_var, threshold)
        
        # Inbreeding
        inbreeding = self.calculate_inbreeding(parent1_genotypes, parent2_genotypes)
        
        # Genetic distance
        gen_dist = self.calculate_genetic_distance(parent1_genotypes, parent2_genotypes)
        
        return CrossPrediction(
            parent1_id=parent1_id,
            parent2_id=parent2_id,
            predicted_mean=pred_mean,
            predicted_variance=pred_var,
            usefulness=usefulness,
            superior_progeny_prob=sup_prob,
            inbreeding_coefficient=inbreeding,
            genetic_distance=gen_dist
        )
    
    def rank_crosses(
        self,
        parents: List[Dict[str, Any]],
        genotypes: np.ndarray,
        gebvs: np.ndarray,
        marker_effects: Optional[np.ndarray] = None,
        selection_intensity: float = 2.06,
        threshold: Optional[float] = None,
        max_inbreeding: float = 0.25,
        min_genetic_distance: float = 0.1,
        top_n: int = 20,
        rank_by: str = "usefulness"
    ) -> CrossRanking:
        """
        Rank all possible crosses
        
        Parameters:
            parents: List of parent info dicts with 'id' key
            genotypes: Genotype matrix (n_parents x n_markers)
            gebvs: GEBV vector (n_parents)
            marker_effects: Optional marker effect estimates
            selection_intensity: For usefulness calculation
            threshold: For superior progeny probability
            max_inbreeding: Maximum allowed inbreeding
            min_genetic_distance: Minimum genetic distance
            top_n: Number of top crosses to return
            rank_by: "usefulness", "mean", "variance", "superior_prob"
        
        Returns:
            CrossRanking with sorted crosses
        """
        n_parents = len(parents)
        crosses = []
        
        # Generate all pairwise crosses
        for i in range(n_parents):
            for j in range(i + 1, n_parents):
                prediction = self.predict_single_cross(
                    parent1_id=parents[i]['id'],
                    parent2_id=parents[j]['id'],
                    parent1_gebv=gebvs[i],
                    parent2_gebv=gebvs[j],
                    parent1_genotypes=genotypes[i],
                    parent2_genotypes=genotypes[j],
                    marker_effects=marker_effects,
                    selection_intensity=selection_intensity,
                    threshold=threshold
                )
                
                # Apply filters
                if prediction.inbreeding_coefficient > max_inbreeding:
                    continue
                if prediction.genetic_distance < min_genetic_distance:
                    continue
                
                crosses.append(prediction)
        
        # Sort by criterion
        if rank_by == "usefulness":
            crosses.sort(key=lambda x: x.usefulness, reverse=True)
        elif rank_by == "mean":
            crosses.sort(key=lambda x: x.predicted_mean, reverse=True)
        elif rank_by == "variance":
            crosses.sort(key=lambda x: x.predicted_variance, reverse=True)
        elif rank_by == "superior_prob":
            crosses.sort(key=lambda x: x.superior_progeny_prob, reverse=True)
        
        return CrossRanking(
            crosses=crosses[:top_n],
            selection_intensity=selection_intensity,
            threshold=threshold or 0.0,
            method=rank_by
        )

    async def save_prediction(
        self,
        db: AsyncSession,
        organization_id: int,
        prediction: CrossPrediction,
        model_id: Optional[int] = None,
        trait_name: Optional[str] = None
    ) -> CrossPredictionResult:
        """
        Save a cross prediction to the database.
        """
        db_result = CrossPredictionResult(
            organization_id=organization_id,
            parent1_id=int(prediction.parent1_id),
            parent2_id=int(prediction.parent2_id),
            predicted_mean=prediction.predicted_mean,
            predicted_variance=prediction.predicted_variance,
            usefulness_criterion=prediction.usefulness,
            superiority_prob=prediction.superior_progeny_prob,
            genetic_distance=prediction.genetic_distance,
            inbreeding_coeff=prediction.inbreeding_coefficient,
            model_id=model_id,
            trait_name=trait_name
        )
        
        db.add(db_result)
        await db.commit()
        await db.refresh(db_result)
        return db_result


# Global service instance
cross_prediction_service = CrossPredictionService()
