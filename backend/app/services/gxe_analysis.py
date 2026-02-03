"""
G×E Interaction Analysis Service
Genotype-by-Environment interaction analysis for plant breeding

Methods:
- AMMI (Additive Main effects and Multiplicative Interaction)
- GGE Biplot
- Finlay-Wilkinson Regression

Uses NumPy/SciPy for calculations (Fortran bindings available for production)
"""

import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GxEMethod(str, Enum):
    """Available G×E analysis methods"""
    AMMI = "ammi"
    GGE = "gge"
    FINLAY_WILKINSON = "finlay_wilkinson"


class GGEScaling(int, Enum):
    """GGE biplot scaling options"""
    SYMMETRIC = 0
    GENOTYPE_FOCUSED = 1
    ENVIRONMENT_FOCUSED = 2


@dataclass
class AMMIResult:
    """AMMI analysis results"""
    grand_mean: float
    genotype_effects: np.ndarray
    environment_effects: np.ndarray
    genotype_scores: np.ndarray  # IPCA scores
    environment_scores: np.ndarray
    eigenvalues: np.ndarray
    variance_explained: np.ndarray
    genotype_names: List[str]
    environment_names: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "grand_mean": float(self.grand_mean),
            "genotype_effects": self.genotype_effects.tolist(),
            "environment_effects": self.environment_effects.tolist(),
            "genotype_scores": self.genotype_scores.tolist(),
            "environment_scores": self.environment_scores.tolist(),
            "eigenvalues": self.eigenvalues.tolist(),
            "variance_explained": self.variance_explained.tolist(),
            "genotype_names": self.genotype_names,
            "environment_names": self.environment_names,
        }


@dataclass
class GGEResult:
    """GGE biplot results"""
    genotype_scores: np.ndarray
    environment_scores: np.ndarray
    eigenvalues: np.ndarray
    variance_explained: np.ndarray
    genotype_names: List[str]
    environment_names: List[str]
    scaling: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "genotype_scores": self.genotype_scores.tolist(),
            "environment_scores": self.environment_scores.tolist(),
            "eigenvalues": self.eigenvalues.tolist(),
            "variance_explained": self.variance_explained.tolist(),
            "genotype_names": self.genotype_names,
            "environment_names": self.environment_names,
            "scaling": self.scaling,
        }


@dataclass 
class FinlayWilkinsonResult:
    """Finlay-Wilkinson regression results"""
    genotype_means: np.ndarray
    slopes: np.ndarray  # Stability parameter (b)
    r_squared: np.ndarray
    environment_index: np.ndarray
    genotype_names: List[str]
    environment_names: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "genotype_means": self.genotype_means.tolist(),
            "slopes": self.slopes.tolist(),
            "r_squared": self.r_squared.tolist(),
            "environment_index": self.environment_index.tolist(),
            "genotype_names": self.genotype_names,
            "environment_names": self.environment_names,
            "stability_classification": self._classify_stability(),
        }
    
    def _classify_stability(self) -> List[Dict[str, Any]]:
        """Classify genotypes by stability"""
        results = []
        mean_yield = np.mean(self.genotype_means)
        
        for i, name in enumerate(self.genotype_names):
            slope = self.slopes[i]
            mean = self.genotype_means[i]
            
            # Classification based on Finlay-Wilkinson interpretation
            if slope < 0.8:
                stability = "stable_low_responsive"
                desc = "Stable, below-average response to environment"
            elif slope > 1.2:
                stability = "unstable_high_responsive" 
                desc = "Unstable, above-average response to environment"
            else:
                stability = "average_responsive"
                desc = "Average response to environment"
            
            if mean > mean_yield:
                performance = "high_yielding"
            else:
                performance = "low_yielding"
            
            results.append({
                "genotype": name,
                "mean": float(mean),
                "slope": float(slope),
                "r_squared": float(self.r_squared[i]),
                "stability": stability,
                "performance": performance,
                "description": desc,
            })
        
        return results


class GxEAnalysisService:
    """
    G×E Interaction Analysis Service
    
    Provides AMMI, GGE biplot, and Finlay-Wilkinson regression
    for analyzing genotype-by-environment interactions.
    """
    
    def ammi_analysis(
        self,
        yield_matrix: np.ndarray,
        genotype_names: List[str],
        environment_names: List[str],
        n_components: int = 2
    ) -> AMMIResult:
        """
        AMMI (Additive Main effects and Multiplicative Interaction) Analysis
        
        Model: Y_ij = μ + G_i + E_j + Σ λ_k α_ik γ_jk + ε_ij
        
        Args:
            yield_matrix: Yield data (genotypes × environments)
            genotype_names: Names of genotypes
            environment_names: Names of environments
            n_components: Number of IPCA components to retain
            
        Returns:
            AMMIResult with effects, scores, and eigenvalues
        """
        g, e = yield_matrix.shape
        n_components = min(n_components, min(g, e) - 1)
        
        # Grand mean
        grand_mean = np.mean(yield_matrix)
        
        # Genotype effects (row means - grand mean)
        genotype_effects = np.mean(yield_matrix, axis=1) - grand_mean
        
        # Environment effects (column means - grand mean)
        environment_effects = np.mean(yield_matrix, axis=0) - grand_mean
        
        # GE interaction matrix
        GE = yield_matrix - grand_mean - genotype_effects[:, np.newaxis] - environment_effects
        
        # SVD of interaction matrix
        U, S, Vt = np.linalg.svd(GE, full_matrices=False)
        
        # IPCA scores (scaled by sqrt of singular values)
        genotype_scores = U[:, :n_components] * np.sqrt(S[:n_components])
        environment_scores = Vt[:n_components, :].T * np.sqrt(S[:n_components])
        
        # Eigenvalues and variance explained
        eigenvalues = S[:n_components] ** 2
        total_ss = np.sum(GE ** 2)
        variance_explained = eigenvalues / total_ss * 100 if total_ss > 0 else eigenvalues * 0
        
        return AMMIResult(
            grand_mean=grand_mean,
            genotype_effects=genotype_effects,
            environment_effects=environment_effects,
            genotype_scores=genotype_scores,
            environment_scores=environment_scores,
            eigenvalues=eigenvalues,
            variance_explained=variance_explained,
            genotype_names=genotype_names,
            environment_names=environment_names,
        )
    
    def gge_biplot(
        self,
        yield_matrix: np.ndarray,
        genotype_names: List[str],
        environment_names: List[str],
        n_components: int = 2,
        scaling: GGEScaling = GGEScaling.SYMMETRIC
    ) -> GGEResult:
        """
        GGE (Genotype + Genotype-by-Environment) Biplot Analysis
        
        Model: Y_ij - μ - E_j = Σ λ_k α_ik γ_jk
        Environment-centered, combines G + GE effects
        
        Args:
            yield_matrix: Yield data (genotypes × environments)
            genotype_names: Names of genotypes
            environment_names: Names of environments
            n_components: Number of PCs to retain
            scaling: Scaling method for biplot
            
        Returns:
            GGEResult with scores and eigenvalues
        """
        g, e = yield_matrix.shape
        n_components = min(n_components, min(g, e) - 1)
        
        # Environment-center the data (remove environment means)
        env_means = np.mean(yield_matrix, axis=0)
        Y_centered = yield_matrix - env_means
        
        # SVD
        U, S, Vt = np.linalg.svd(Y_centered, full_matrices=False)
        
        # Apply scaling
        if scaling == GGEScaling.SYMMETRIC:
            scale_g = np.sqrt(S[:n_components])
            scale_e = np.sqrt(S[:n_components])
        elif scaling == GGEScaling.GENOTYPE_FOCUSED:
            scale_g = S[:n_components]
            scale_e = np.ones(n_components)
        else:  # ENVIRONMENT_FOCUSED
            scale_g = np.ones(n_components)
            scale_e = S[:n_components]
        
        genotype_scores = U[:, :n_components] * scale_g
        environment_scores = Vt[:n_components, :].T * scale_e
        
        # Variance explained
        eigenvalues = S[:n_components] ** 2
        total_ss = np.sum(Y_centered ** 2)
        variance_explained = eigenvalues / total_ss * 100 if total_ss > 0 else eigenvalues * 0
        
        scaling_names = {0: "symmetric", 1: "genotype_focused", 2: "environment_focused"}
        
        return GGEResult(
            genotype_scores=genotype_scores,
            environment_scores=environment_scores,
            eigenvalues=eigenvalues,
            variance_explained=variance_explained,
            genotype_names=genotype_names,
            environment_names=environment_names,
            scaling=scaling_names.get(scaling.value, "symmetric"),
        )
    
    def finlay_wilkinson(
        self,
        yield_matrix: np.ndarray,
        genotype_names: List[str],
        environment_names: List[str]
    ) -> FinlayWilkinsonResult:
        """
        Finlay-Wilkinson Regression Analysis
        
        Model: Y_ij = μ_i + β_i * E_j + ε_ij
        where E_j is the environment index (mean - grand mean)
        
        Interpretation:
        - β ≈ 1: Average stability
        - β < 1: Below-average response (stable in poor environments)
        - β > 1: Above-average response (responsive to good environments)
        
        Args:
            yield_matrix: Yield data (genotypes × environments)
            genotype_names: Names of genotypes
            environment_names: Names of environments
            
        Returns:
            FinlayWilkinsonResult with means, slopes, and R²
        """
        g, e = yield_matrix.shape
        
        # Grand mean and environment index
        grand_mean = np.mean(yield_matrix)
        env_means = np.mean(yield_matrix, axis=0)
        env_index = env_means - grand_mean
        
        # Genotype means
        genotype_means = np.mean(yield_matrix, axis=1)
        
        # Regression for each genotype
        slopes = np.zeros(g)
        r_squared = np.zeros(g)
        
        for i in range(g):
            y = yield_matrix[i, :]
            x = env_index
            
            # Simple linear regression
            x_mean = np.mean(x)
            y_mean = np.mean(y)
            
            ss_xy = np.sum((x - x_mean) * (y - y_mean))
            ss_xx = np.sum((x - x_mean) ** 2)
            ss_yy = np.sum((y - y_mean) ** 2)
            
            if ss_xx > 1e-10:
                slopes[i] = ss_xy / ss_xx
            else:
                slopes[i] = 1.0
            
            if ss_yy > 1e-10 and ss_xx > 1e-10:
                r_squared[i] = (ss_xy ** 2) / (ss_xx * ss_yy)
            else:
                r_squared[i] = 0.0
        
        return FinlayWilkinsonResult(
            genotype_means=genotype_means,
            slopes=slopes,
            r_squared=r_squared,
            environment_index=env_index,
            genotype_names=genotype_names,
            environment_names=environment_names,
        )
    
    def identify_mega_environments(
        self,
        gge_result: GGEResult,
        n_clusters: int = 3
    ) -> Dict[str, Any]:
        """
        Identify mega-environments from GGE biplot
        
        Uses environment scores to cluster similar environments.
        """
        from scipy.cluster.hierarchy import linkage, fcluster
        
        env_scores = gge_result.environment_scores
        
        # Hierarchical clustering
        Z = linkage(env_scores, method='ward')
        clusters = fcluster(Z, n_clusters, criterion='maxclust')
        
        mega_envs = {}
        for i, (name, cluster) in enumerate(zip(gge_result.environment_names, clusters)):
            cluster_name = f"ME{cluster}"
            if cluster_name not in mega_envs:
                mega_envs[cluster_name] = []
            mega_envs[cluster_name].append(name)
        
        return {
            "mega_environments": mega_envs,
            "cluster_assignments": dict(zip(gge_result.environment_names, clusters.tolist())),
        }
    
    def identify_winning_genotypes(
        self,
        gge_result: GGEResult
    ) -> Dict[str, Any]:
        """
        Identify winning genotypes for each environment
        
        Based on GGE biplot: genotype closest to environment vector wins.
        """
        g_scores = gge_result.genotype_scores
        e_scores = gge_result.environment_scores
        
        winners = {}
        for j, env_name in enumerate(gge_result.environment_names):
            env_vec = e_scores[j]
            
            # Project genotypes onto environment vector
            projections = np.dot(g_scores, env_vec) / (np.linalg.norm(env_vec) + 1e-10)
            winner_idx = np.argmax(projections)
            
            winners[env_name] = {
                "winner": gge_result.genotype_names[winner_idx],
                "projection": float(projections[winner_idx]),
                "rankings": [
                    {"genotype": gge_result.genotype_names[i], "score": float(projections[i])}
                    for i in np.argsort(projections)[::-1][:5]
                ]
            }
        
        return winners




    async def get_observation_matrix(
        self,
        db,  # AsyncSession
        study_db_ids: List[str],
        trait_db_id: str
    ) -> Dict[str, Any]:
        """
        Generate Yield Matrix from Database Observations
        
        Args:
            db: Database session
            study_db_ids: List of Study DB IDs to include (Environments)
            trait_db_id: Trait DB ID to analyze (Yield)
            
        Returns:
            Dict containing yield_matrix, genotype_names, environment_names
        """
        from sqlalchemy import select, func, cast, Float
        from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
        from app.models.core import Study
        from app.models.germplasm import Germplasm
        
        # 1. Fetch observations
        stmt = (
            select(
                Germplasm.germplasm_name,
                Study.study_name,
                func.avg(cast(Observation.value, Float)).label("mean_value")
            )
            .join(ObservationUnit, Observation.observation_unit_id == ObservationUnit.id)
            .join(Germplasm, Observation.germplasm_id == Germplasm.id)
            .join(Study, Observation.study_id == Study.id)
            .join(ObservationVariable, Observation.observation_variable_id == ObservationVariable.id) 
            .where(ObservationVariable.observation_variable_db_id == trait_db_id)
            .where(Study.study_db_id.in_(study_db_ids))
            .group_by(Germplasm.germplasm_name, Study.study_name)
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        if not rows:
            return {
                "yield_matrix": [],
                "genotype_names": [],
                "environment_names": [],
                "error": "No observations found for these criteria"
            }
            
        # 2. Pivot Data
        # structured as {(genotype, environment): value}
        data_map = {(r.germplasm_name, r.study_name): r.mean_value for r in rows}
        
        # Get unique sorted lists
        genotypes = sorted(list(set(r.germplasm_name for r in rows)))
        environments = sorted(list(set(r.study_name for r in rows)))
        
        # Build Matrix
        matrix = []
        for g in genotypes:
            row = []
            for e in environments:
                val = data_map.get((g, e))
                if val is None:
                    # Handle missing data - for now, fill with mean of genotype or None?
                    # GXE analysis often requires complete data. 
                    # Simple imputation: Genotype Mean
                    g_vals = [data_map.get((g, env)) for env in environments if data_map.get((g, env)) is not None]
                    val = sum(g_vals) / len(g_vals) if g_vals else 0
                row.append(val)
            matrix.append(row)
            
        return {
            "yield_matrix": matrix,
            "genotype_names": genotypes,
            "environment_names": environments
        }

# Singleton instance
_gxe_service: Optional[GxEAnalysisService] = None


def get_gxe_service() -> GxEAnalysisService:
    """Get or create G×E analysis service singleton"""
    global _gxe_service
    if _gxe_service is None:
        _gxe_service = GxEAnalysisService()
    return _gxe_service
