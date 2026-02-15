"""
Dimensionality Reduction Service

Provides standalone dimensionality reduction algorithms (PCA, UMAP, t-SNE)
and distance matrix calculations for population structure analysis and
genomic diversity visualization.

Algorithms:
- PCA: Principal Component Analysis (linear) via scikit-learn
- UMAP: Uniform Manifold Approximation and Projection (nonlinear)
- t-SNE: t-Distributed Stochastic Neighbor Embedding (nonlinear)

Distance Metrics:
- Euclidean: Standard geometric distance
- Modified Rogers: Genetic distance based on allele frequency differences
- Nei's Standard: Genetic distance assuming drift/mutation equilibrium
"""

import numpy as np
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

# Try importing optional dependencies for extensive scientific stack
try:
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler, RobustScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ReductionResult:
    """Standardized result container for dimensionality reduction"""
    projection: List[List[float]]  # n_samples x n_components
    components: Optional[List[List[float]]] = None  # loadings (PCA only)
    variance_explained: Optional[List[float]] = None  # (PCA only)
    n_components: int = 2
    method: str = "custom"


class DimensionalityReductionService:
    """
    Service for dimensionality reduction and distance matrix calculations.
    
    Handles genotype matrices (0/1/2) and phenotype matrices.
    Automatically handles missing values (imputation) and scaling.
    """

    def __init__(self):
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not found. PCA/t-SNE will fail.")
        if not UMAP_AVAILABLE:
            logger.warning("umap-learn not found. UMAP will fail.")

    def _prepare_data(self, data: np.ndarray, impute: bool = True, scale: bool = True) -> np.ndarray:
        """
        Preprocess data: impute NaNs and scale.
        
        Args:
            data: Input matrix (n_samples x n_features)
            impute: Whether to replace NaNs with column means
            scale: Whether to apply RobustScaler
        """
        X = np.array(data, dtype=float)
        
        # 1. Imputation (Mean)
        if impute and np.isnan(X).any():
            col_mean = np.nanmean(X, axis=0)
            inds = np.where(np.isnan(X))
            X[inds] = np.take(col_mean, inds[1])
        
        # 2. Scaling
        if scale and SKLEARN_AVAILABLE:
            # RobustScaler is better for biological data with outliers
            X = RobustScaler().fit_transform(X)
            
        return X

    def run_pca(
        self, 
        data: Union[List[List[float]], np.ndarray], 
        n_components: int = 10,
        scale: bool = True
    ) -> Dict[str, Any]:
        """
        Run Principal Component Analysis (PCA).
        
        Linear dimensionality reduction using Singular Value Decomposition.
        
        Args:
            data: Input matrix (n_samples x n_features)
            n_components: Number of components to return (default 10)
            scale: Whether to center and scale data (default True)
            
        Returns:
            Dictionary with scores, loadings, and variance stats
        """
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not installed"}

        X = self._prepare_data(data, scale=scale)
        n_samples, n_features = X.shape
        
        # Limit components to min(n_samples, n_features)
        actual_n = min(n_components, n_samples, n_features)
        
        try:
            pca = PCA(n_components=actual_n, svd_solver='randomized', iterated_power=6, random_state=42)
            scores = pca.fit_transform(X)
            
            return {
                "method": "PCA",
                "n_components": actual_n,
                "scores": scores.tolist(),  # The coordinates (n_samples x n)
                "loadings": pca.components_.tolist(),  # The eigenvectors (n x n_features)
                "variance_explained": pca.explained_variance_ratio_.tolist(),
                "cumulative_variance": np.cumsum(pca.explained_variance_ratio_).tolist(),
                "eigenvalues": pca.explained_variance_.tolist()
            }
        except Exception as e:
            logger.error(f"PCA failed: {str(e)}")
            return {"error": f"PCA computation failed: {str(e)}"}

    def run_umap(
        self,
        data: Union[List[List[float]], np.ndarray],
        n_components: int = 2,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        metric: str = "euclidean",
        scale: bool = True
    ) -> Dict[str, Any]:
        """
        Run Uniform Manifold Approximation and Projection (UMAP).
        
        Non-linear dimensionality reduction preserving local and global structure.
        Excellent for visualizing population clusters.
        
        Args:
            data: Input matrix
            n_components: Target dimensions (usually 2)
            n_neighbors: Balance local vs global structure (default 15)
            min_dist: Minimum distance between points in embedding (default 0.1)
            metric: Distance metric ('euclidean', 'manhattan', 'cosine', etc.)
            
        Returns:
            Dictionary with embedding coordinates
        """
        if not UMAP_AVAILABLE:
            return {"error": "umap-learn not installed"}

        X = self._prepare_data(data, scale=scale)
        
        try:
            reducer = umap.UMAP(
                n_components=n_components,
                n_neighbors=n_neighbors,
                min_dist=min_dist,
                metric=metric,
                random_state=42,
                n_jobs=1  # Prevent threading issues in async context
            )
            embedding = reducer.fit_transform(X)
            
            return {
                "method": "UMAP",
                "n_components": n_components,
                "embedding": embedding.tolist(),
                "parameters": {
                    "n_neighbors": n_neighbors,
                    "min_dist": min_dist,
                    "metric": metric
                }
            }
        except Exception as e:
            logger.error(f"UMAP failed: {str(e)}")
            return {"error": f"UMAP computation failed: {str(e)}"}

    def run_tsne(
        self,
        data: Union[List[List[float]], np.ndarray],
        n_components: int = 2,
        perplexity: float = 30.0,
        learning_rate: float = 200.0,
        scale: bool = True
    ) -> Dict[str, Any]:
        """
        Run t-SNE (t-Distributed Stochastic Neighbor Embedding).
        
        Classic non-linear visualizer. Often slower than UMAP but widely used.
        
        Args:
            data: Input matrix
            n_components: Target dimensions (usually 2)
            perplexity: Balance local/global aspects (5-50)
            learning_rate: Learning rate (10-1000)
            
        Returns:
            Dictionary with embedding coordinates
        """
        if not SKLEARN_AVAILABLE:
            return {"error": "scikit-learn not installed"}

        X = self._prepare_data(data, scale=scale)
        original_n = X.shape[0]
        
        # Perplexity must be < n_samples - 1
        adj_perplexity = min(perplexity, max(1.0, original_n - 2.0))
        
        try:
            tsne = TSNE(
                n_components=n_components,
                perplexity=adj_perplexity,
                learning_rate=learning_rate,
                init='pca', 
                random_state=42,
                n_jobs=1
            )
            embedding = tsne.fit_transform(X)
            
            return {
                "method": "t-SNE",
                "n_components": n_components,
                "embedding": embedding.tolist(),
                "parameters": {
                    "perplexity": adj_perplexity,
                    "learning_rate": learning_rate
                }
            }
        except Exception as e:
            logger.error(f"t-SNE failed: {str(e)}")
            return {"error": f"t-SNE computation failed: {str(e)}"}

    # =========================================================================
    # Distance Matrices (Sprint 2 B2.2)
    # =========================================================================

    def compute_distance_matrix(
        self,
        genotypes: Union[List[List[int]], np.ndarray],
        method: str = "modified_rogers",
        ploidy: int = 2
    ) -> Dict[str, Any]:
        """
        Compute genetic distance matrix between individuals.
        
        Supported Methods:
        - euclidean: Standard Euclidean distance
        - modified_rogers: Rogers' distance (Wright 1978 modified) - Default for clustering
        - nei: Nei's standard genetic distance (1972)
        - identity_by_state: 1 - IBS similarity
        
        Args:
            genotypes: Genotype matrix (n_inds x n_markers), values 0..ploidy
            method: Distance calculation method
            ploidy: Ploidy level (default 2)
            
        Returns:
            Dictionary with distance matrix and method metadata
        """
        G = np.array(genotypes, dtype=float)
        n, m = G.shape
        
        if n < 2:
            return {"error": "Need at least 2 individuals"}

        dist_matrix = np.zeros((n, n))
        
        try:
            if method == "euclidean":
                # Efficient Euclidean distance using dot products
                # d(x,y)^2 = x.x + y.y - 2x.y
                G_sq = np.sum(G**2, axis=1)
                dist_sq = G_sq[:, None] + G_sq[None, :] - 2 * np.dot(G, G.T)
                # Numerical stability: replace negative zeros
                dist_sq[dist_sq < 0] = 0
                dist_matrix = np.sqrt(dist_sq)
                
                # Normalize by number of markers for comparability ? 
                # Usually standard Euclidean isn't normalized by M, but Mean Euclidean is.
                # Let's keep raw standard Euclidean for consistency with scipy.spatial.distance.
                
            elif method == "modified_rogers":
                # Modified Rogers' Distance (W)
                # d_ij = (1 / sqrt(2m)) * sqrt( sum( (p_ix - p_iy)^2 ) ) across loci
                # Here we strictly use genotype calls as pseudo-frequencies p = 0/1/2 -> 0.0/0.5/1.0
                
                # Normalize genotypes to frequency [0, 1]
                freqs = G / ploidy
                
                # Vectorized calculation
                # sum((x-y)^2) = x^2 + y^2 - 2xy
                F_sq = np.sum(freqs**2, axis=1)
                diff_sq = F_sq[:, None] + F_sq[None, :] - 2 * np.dot(freqs, freqs.T)
                diff_sq[diff_sq < 0] = 0
                
                # d = sqrt(diff_sq / (2 * m)) for Modified Rogers (common variant)
                # Reitan (2002) definition: d = sqrt( sum( (x-y)^2 ) / (2m) )
                dist_matrix = np.sqrt(diff_sq / (2 * m))
                
            elif method == "identity_by_state":
                # IBS distance = 1 - (IBS similarity)
                # IBS similarity = (number of shared alleles) / (2 * m)
                # For diploid:
                # 0 vs 0 -> 2 shared
                # 2 vs 2 -> 2 shared
                # 0 vs 2 -> 0 shared
                # 1 vs 1 -> 2 shared ? No, 1 is het.
                # Standard IBS: |x - y| counts allele differences
                
                # City-Block (Manhattan) distance on raw genotypes
                # dist = sum(|x - y|)
                # Similarity = 1 - dist / (ploidy * m)
                
                # Use sklearn pairwise_distances if available, else numpy broadcast
                if SKLEARN_AVAILABLE:
                    from sklearn.metrics.pairwise import manhattan_distances
                    manhattan = manhattan_distances(G)
                else:
                    manhattan = np.sum(np.abs(G[:, None] - G[None, :]), axis=2)
                    
                dist_matrix = manhattan / (ploidy * m)
                
            elif method == "nei":
                # Nei's standard genetic distance usually requires population frequencies.
                # For individuals, we treat them as populations of size 1 (noisy but possible).
                # D = -ln( Jxy / sqrt(Jx * Jy) )
                # Jxy = sum(p_ix * p_iy)
                
                freqs = G / ploidy
                # Jxy = dot product of frequencies normalized by m
                Jxy = np.dot(freqs, freqs.T) / m
                
                # Diagonals Jx
                Jx = np.diag(Jxy)
                
                # D_ij = -ln( Jxy / sqrt(Jx * Jy) )
                denom = np.sqrt(Jx[:, None] * Jx[None, :])
                
                # Handle zeros in log with epsilon
                ratio = Jxy / (denom + 1e-10)
                # Clip for numerical safety
                ratio = np.clip(ratio, 1e-10, 1.0)
                
                dist_matrix = -np.log(ratio)
                
            else:
                return {"error": f"Unknown distance method: {method}"}

            return {
                "matrix": dist_matrix.tolist(),
                "method": method,
                "n_samples": n,
                "n_markers": m
            }
            
        except Exception as e:
            logger.error(f"Distance calculation failed: {str(e)}")
            return {"error": f"Distance calculation failed: {str(e)}"}

# Global instance
dimensionality_reduction = DimensionalityReductionService()
