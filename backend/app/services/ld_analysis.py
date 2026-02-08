import math
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.ld import LDPair, LDDecayPoint
from app.services.genotyping import genotyping_service

class LDAnalysisService:
    def calculate_r2(self, g1: List[int], g2: List[int]) -> float:
        """Calculate r^2 ignoring missing values (-1)."""
        n = len(g1)
        if n != len(g2) or n == 0:
            return 0.0

        # Filter valid pairs
        valid_indices = [i for i in range(n) if g1[i] != -1 and g2[i] != -1]
        n_valid = len(valid_indices)

        if n_valid < 2:
            return 0.0

        x = [g1[i] for i in valid_indices]
        y = [g2[i] for i in valid_indices]

        mean1 = sum(x) / n_valid
        mean2 = sum(y) / n_valid

        var1 = sum((v - mean1) ** 2 for v in x)
        var2 = sum((v - mean2) ** 2 for v in y)

        if var1 == 0 or var2 == 0:
            return 0.0

        cov = sum((x[i] - mean1) * (y[i] - mean2) for i in range(n_valid))
        r2 = (cov ** 2) / (var1 * var2)
        return r2

    def calculate_pairwise_ld(
        self,
        genotypes: List[List[int]],
        positions: List[int],
        marker_names: List[str],
        window_size: int = 100
    ) -> Tuple[List[LDPair], List[List[float]]]:
        """
        Calculate pairwise LD for a region.
        Returns list of significant pairs and the full matrix.
        """
        n_markers = len(genotypes)
        pairs = []
        matrix = [[0.0] * n_markers for _ in range(n_markers)]

        for i in range(n_markers):
            matrix[i][i] = 1.0
            end_j = min(n_markers, i + window_size + 1)
            for j in range(i + 1, end_j):
                r2 = self.calculate_r2(genotypes[i], genotypes[j])
                matrix[i][j] = r2
                matrix[j][i] = r2

                dist = abs(positions[i] - positions[j])
                pairs.append(LDPair(
                    marker1=marker_names[i],
                    marker2=marker_names[j],
                    distance=dist,
                    r2=r2,
                    d_prime=math.sqrt(r2) # Approximate/Placeholder for D'
                ))

        # Sort pairs by r2 descending
        pairs.sort(key=lambda x: x.r2, reverse=True)
        return pairs, matrix

    def calculate_decay(
        self,
        genotypes: List[List[int]],
        positions: List[int],
        max_dist: int = 100000,
        bin_size: int = 1000
    ) -> List[LDDecayPoint]:
        """
        Calculate LD decay.
        """
        n_markers = len(genotypes)
        bins = {} # bin_start -> [sum_r2, count]

        for i in range(n_markers):
            # Limit inner loop to avoid O(N^2) on large sets if needed, but for decay we usually check pairs within max_dist
            # Optimization: since positions are likely sorted, we can break early
            for j in range(i + 1, n_markers):
                dist = abs(positions[i] - positions[j])
                if dist > max_dist:
                    continue # Assuming sorted

                r2 = self.calculate_r2(genotypes[i], genotypes[j])

                bin_idx = (dist // bin_size) * bin_size
                if bin_idx not in bins:
                    bins[bin_idx] = [0.0, 0]

                bins[bin_idx][0] += r2
                bins[bin_idx][1] += 1

        decay_points = []
        for bin_start in sorted(bins.keys()):
            total_r2, count = bins[bin_start]
            decay_points.append(LDDecayPoint(
                distance=bin_start,
                mean_r2=total_r2 / count if count > 0 else 0,
                pair_count=count
            ))

        return decay_points

    async def get_genotype_matrix(self, db: AsyncSession, variant_set_id: str) -> Tuple[List[List[int]], List[str], List[int], int]:
        """
        Fetch genotype data and convert to matrix.
        Returns: (genotypes (markers x samples), marker_names, positions, sample_count)
        """
        # Fetch variants
        variants, _ = await genotyping_service.list_variants(db, variant_set_db_id=variant_set_id, page_size=1000)

        if not variants:
            return [], [], [], 0

        # Sort by position
        variants.sort(key=lambda v: v.start or 0)

        marker_names = [v.variant_name for v in variants]
        positions = [v.start or 0 for v in variants]
        variant_ids = [v.variant_db_id for v in variants]

        # Fetch calls
        calls, _ = await genotyping_service.list_calls(db, variant_set_db_id=variant_set_id, page_size=10000)

        if not calls:
            return [[-1] * 1 for _ in range(len(variants))], marker_names, positions, 0

        # Get samples
        call_sets = await genotyping_service.list_call_sets(db, variant_set_db_id=variant_set_id, page_size=1000)
        sample_ids = [cs['callSetDbId'] for cs in call_sets['data']]
        sample_index = {sid: i for i, sid in enumerate(sample_ids)}
        n_samples = len(sample_ids)
        n_markers = len(variants)

        # Initialize matrix (Markers x Samples)
        matrix = [[-1] * n_samples for _ in range(n_markers)]

        variant_index = {vid: i for i, vid in enumerate(variant_ids)}

        for call in calls:
            v_idx = variant_index.get(call.variant.variant_db_id)
            # Access relationship via object or ID depending on how list_calls returns
            # list_calls returns objects with joined relationships
            s_id = call.call_set.call_set_db_id if call.call_set else None

            if s_id and s_id in sample_index:
                s_idx = sample_index[s_id]

                if v_idx is not None:
                    gt = call.genotype_value
                    val = -1
                    if gt == "0/0": val = 0
                    elif gt == "0/1" or gt == "1/0": val = 1
                    elif gt == "1/1": val = 2

                    matrix[v_idx][s_idx] = val

        return matrix, marker_names, positions, n_samples

ld_service = LDAnalysisService()
