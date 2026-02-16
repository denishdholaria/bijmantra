"""
SNP Clustering Service (Theta-R Transform)

Implements Illumina-style Theta-R polar coordinate transform
for genotype cluster calling from biallelic SNP intensity data.

Methods:
- theta_r_transform: Convert (X, Y) intensities to (Theta, R)
- cluster_snp: Assign genotype clusters (AA, AB, BB)
- call_genotypes: Batch genotype calling from intensity matrix
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy.cluster.vq import kmeans2
import logging

logger = logging.getLogger(__name__)


class SNPClusteringService:
    """
    Theta-R transform and genotype cluster calling for biallelic SNPs.

    In Illumina genotyping, raw intensities (X, Y) for allele A and B
    are transformed to polar coordinates:
      Theta = (2/pi) * arctan(Y / X)   -> allelic ratio [0, 1]
      R = X + Y                         -> total signal intensity
    
    Genotype clusters:
      AA: Theta near 0
      AB: Theta near 0.5
      BB: Theta near 1
    """

    def theta_r_transform(
        self, x: np.ndarray, y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform (X, Y) allele intensities to (Theta, R).

        Args:
            x: Allele A intensities (n_samples,)
            y: Allele B intensities (n_samples,)

        Returns:
            (theta, r) tuple of arrays
        """
        r = x + y

        # Avoid division by zero
        denom = x.copy().astype(float)
        denom[denom == 0] = 1e-10

        theta = (2.0 / np.pi) * np.arctan(y / denom)

        # Clamp to [0, 1]
        theta = np.clip(theta, 0, 1)

        return theta, r

    def cluster_snp(
        self,
        theta: np.ndarray,
        r: np.ndarray,
        n_clusters: int = 3,
        min_r: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Cluster a single SNP's samples into genotype groups.

        Args:
            theta: Allelic ratio values (n_samples,)
            r: Total intensity (n_samples,)
            n_clusters: Expected number of clusters (2 or 3)
            min_r: Minimum R threshold (below = no-call)

        Returns:
            Dict with cluster assignments and statistics
        """
        n = len(theta)

        # Filter low-quality samples
        valid = r >= min_r
        n_valid = np.sum(valid)

        if n_valid < n_clusters:
            return {
                "calls": np.full(n, -1, dtype=int).tolist(),
                "n_valid": int(n_valid),
                "error": "Insufficient valid samples for clustering",
            }

        # K-means on theta values for valid samples
        theta_valid = theta[valid].reshape(-1, 1)

        try:
            centroids, labels = kmeans2(theta_valid, n_clusters, minit="++")
        except Exception as e:
            return {
                "calls": np.full(n, -1, dtype=int).tolist(),
                "n_valid": int(n_valid),
                "error": f"Clustering failed: {str(e)}",
            }

        # Sort centroids to assign: lowest = AA (0), middle = AB (1), highest = BB (2)
        centroid_order = np.argsort(centroids.ravel())
        label_map = {old: new for new, old in enumerate(centroid_order)}

        # Map labels
        mapped_labels = np.array([label_map[l] for l in labels])

        # Build full call array
        calls = np.full(n, -1, dtype=int)  # -1 = no call
        calls[valid] = mapped_labels

        # Cluster statistics
        cluster_stats = {}
        genotype_names = {0: "AA", 1: "AB", 2: "BB"}

        for cluster_id in range(n_clusters):
            mask = mapped_labels == cluster_id
            if np.any(mask):
                cluster_theta = theta_valid[mask].ravel()
                cluster_stats[genotype_names.get(cluster_id, f"C{cluster_id}")] = {
                    "count": int(np.sum(mask)),
                    "mean_theta": float(np.mean(cluster_theta)),
                    "std_theta": float(np.std(cluster_theta)),
                }

        # Call rate
        call_rate = int(np.sum(calls >= 0)) / n if n > 0 else 0.0

        return {
            "calls": calls.tolist(),
            "genotypes": [genotype_names.get(c, "NC") if c >= 0 else "NC" for c in calls],
            "cluster_stats": cluster_stats,
            "call_rate": float(call_rate),
            "n_valid": int(n_valid),
            "centroids": {
                genotype_names.get(i, f"C{i}"): float(centroids[centroid_order[i]].item())
                for i in range(n_clusters)
            },
        }

    def call_genotypes(
        self,
        x_matrix: np.ndarray,
        y_matrix: np.ndarray,
        snp_names: Optional[List[str]] = None,
        min_r: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Batch genotype calling for multiple SNPs.

        Args:
            x_matrix: (n_snps, n_samples) allele A intensities
            y_matrix: (n_snps, n_samples) allele B intensities
            snp_names: Optional SNP identifiers
            min_r: Minimum R threshold

        Returns:
            Dict with genotype calls matrix and per-SNP stats
        """
        n_snps, n_samples = x_matrix.shape

        if snp_names is None:
            snp_names = [f"SNP_{i+1}" for i in range(n_snps)]

        all_calls = []
        all_stats = {}

        for i in range(n_snps):
            theta, r = self.theta_r_transform(x_matrix[i], y_matrix[i])
            result = self.cluster_snp(theta, r, min_r=min_r)
            all_calls.append(result["calls"])
            all_stats[snp_names[i]] = {
                "call_rate": result["call_rate"],
                "cluster_stats": result.get("cluster_stats", {}),
            }

        genotype_matrix = np.array(all_calls)

        # Summary
        call_rates = [all_stats[s]["call_rate"] for s in snp_names]

        return {
            "genotype_matrix": genotype_matrix.tolist(),
            "snp_names": snp_names,
            "n_snps": n_snps,
            "n_samples": n_samples,
            "per_snp_stats": all_stats,
            "mean_call_rate": float(np.mean(call_rates)),
        }


# Singleton
snp_clustering_service = SNPClusteringService()
