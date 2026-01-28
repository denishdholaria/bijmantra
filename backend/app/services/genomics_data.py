"""
Genomics Data Service
Retrieves genotype and phenotype data for analysis.

In a real deployment, this would connect to a VCF file storage,
HDF5 database (like Hail or TileDB), or a relational database.
For this beta version, we simulate data deterministically based on IDs.
"""

import numpy as np
from typing import Tuple, List, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)

class GenomicsDataService:
    """Service to retrieve genomic data"""

    def _get_deterministic_seed(self, input_str: str) -> int:
        """Generate a deterministic seed from input string."""
        return int(hashlib.md5(input_str.encode()).hexdigest(), 16) % (2**32)

    def get_genotypes(self, marker_data_id: str) -> Tuple[np.ndarray, List[str]]:
        """
        Retrieve genotype matrix for a given marker data ID.

        Args:
            marker_data_id: Identifier for the marker dataset

        Returns:
            Tuple of (genotype_matrix, sample_ids)
            Matrix shape is (n_samples, n_markers)
            Values: 0, 1, 2 (or -1 for missing)
        """
        # Simulate data based on ID hash to be deterministic
        seed = self._get_deterministic_seed(marker_data_id)
        rng = np.random.default_rng(seed)

        # Dimensions based on "metadata" encoded in ID if possible, otherwise defaults
        # Simulating: "marker_set_A_100x1000" -> 100 samples, 1000 markers
        n_samples = 100
        n_markers = 1000

        parts = marker_data_id.split('_')
        if len(parts) >= 3 and parts[-1].isdigit() and parts[-2].isdigit():
             n_markers = int(parts[-1])
             n_samples = int(parts[-2])

        # Simulate genotypes with some structure (MAF > 0.05)
        mafs = rng.uniform(0.05, 0.5, n_markers)
        genotypes = np.zeros((n_samples, n_markers), dtype=np.float64)

        for j in range(n_markers):
            p = mafs[j]
            # HWE probabilities: p^2, 2pq, q^2
            probs = [(1-p)**2, 2*p*(1-p), p**2]
            genotypes[:, j] = rng.choice([0, 1, 2], size=n_samples, p=probs)

        sample_ids = [f"SAMPLE_{i+1:04d}" for i in range(n_samples)]

        return genotypes, sample_ids

    def get_phenotypes(self, training_data_id: str, trait: str) -> Tuple[np.ndarray, List[str]]:
        """
        Retrieve phenotype values for a trait.

        Args:
            training_data_id: Identifier for the training population
            trait: Name of the trait

        Returns:
            Tuple of (phenotype_vector, sample_ids)
        """
        seed = self._get_deterministic_seed(training_data_id + trait)
        rng = np.random.default_rng(seed)

        n_samples = 100
        if "dataset" in training_data_id:
             # Just a heuristic for simulation
             n_samples = 100

        # Simulate normal distribution
        mean = 100.0
        std = 15.0
        phenotypes = rng.normal(mean, std, n_samples)

        sample_ids = [f"SAMPLE_{i+1:04d}" for i in range(n_samples)]

        return phenotypes, sample_ids

# Singleton instance
genomics_data_service = GenomicsDataService()
