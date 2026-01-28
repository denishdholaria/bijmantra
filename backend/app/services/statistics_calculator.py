
import math
import statistics
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class ObservationData:
    value: float
    germplasm_id: str
    replicate: Optional[str] = None

class TrialStatistics:
    def __init__(self, data: List[ObservationData]):
        self.data = [d for d in data if d.value is not None]
        self.n = len(self.data)
        self.values = [d.value for d in self.data]
        self.germplasms = set(d.germplasm_id for d in self.data)
        self.n_genotypes = len(self.germplasms)

        # Calculate replicates per germplasm
        self.rep_counts = {}
        for d in self.data:
            self.rep_counts[d.germplasm_id] = self.rep_counts.get(d.germplasm_id, 0) + 1

        self.r_bar = statistics.mean(self.rep_counts.values()) if self.rep_counts else 0

    def calculate_basic_stats(self) -> Dict[str, float]:
        if not self.values:
            return {
                "mean": None, "min": None, "max": None,
                "variance": None, "std_dev": None, "cv": None, "count": 0
            }

        mean = statistics.mean(self.values)
        variance = statistics.variance(self.values) if self.n > 1 else 0.0
        std_dev = math.sqrt(variance)

        return {
            "mean": mean,
            "min": min(self.values),
            "max": max(self.values),
            "variance": variance,
            "std_dev": std_dev,
            "cv": (std_dev / mean * 100) if mean != 0 else 0.0,
            "count": self.n
        }

    def calculate_anova(self) -> Dict[str, Any]:
        """
        Performs a one-way ANOVA (CRD) where the factor is Genotype.
        Returns dictionary with MS_Tr (Genotype Mean Square) and MS_E (Error Mean Square).
        """
        if self.n_genotypes < 2 or self.n <= self.n_genotypes:
             return {"ms_genotype": None, "ms_error": None, "f_value": None, "p_value": None}

        # Correction Factor
        grand_total = sum(self.values)
        cf = (grand_total ** 2) / self.n

        # Total Sum of Squares
        tss = sum(v ** 2 for v in self.values) - cf

        # Genotype Sum of Squares (Treatment SS)
        # SSTr = sum(Ti^2 / ni) - CF
        sstr = 0.0
        for gid in self.germplasms:
            # Sum of values for this germplasm
            g_values = [d.value for d in self.data if d.germplasm_id == gid]
            ti = sum(g_values)
            ni = len(g_values)
            sstr += (ti ** 2) / ni
        sstr -= cf

        # Error Sum of Squares
        sse = tss - sstr

        # Degrees of Freedom
        df_tr = self.n_genotypes - 1
        df_error = self.n - self.n_genotypes

        # Mean Squares
        ms_tr = sstr / df_tr if df_tr > 0 else 0
        ms_error = sse / df_error if df_error > 0 else 0

        f_value = ms_tr / ms_error if ms_error > 0 else None

        return {
            "ms_genotype": ms_tr,
            "ms_error": ms_error,
            "f_value": f_value,
            "df_genotype": df_tr,
            "df_error": df_error,
            "ss_genotype": sstr,
            "ss_error": sse
        }

    def calculate_heritability(self, ms_genotype: float, ms_error: float) -> Optional[float]:
        """
        Broad-sense Heritability (H2) = Vg / (Vg + Ve/r)
        Vg = (MS_G - MS_E) / r
        Ve = MS_E
        """
        if ms_genotype is None or ms_error is None or self.r_bar == 0:
            return None

        # If MS_E > MS_G, Vg would be negative, which is impossible. H2 is effectively 0.
        if ms_error >= ms_genotype:
            return 0.0

        vg = (ms_genotype - ms_error) / self.r_bar
        ve = ms_error

        # H2 = Vg / (Vg + Ve/r) -> simplified: (MS_G - MS_E)/r / ((MS_G - MS_E)/r + MS_E/r)
        # = (MS_G - MS_E) / MS_G ? No.
        # Phenotypic Variance Vp = Vg + Ve/r (on a mean basis)
        # H2 = Vg / Vp
        # Vp = (MS_G - MS_E)/r + MS_E/r = MS_G / r
        # So H2 = ((MS_G - MS_E)/r) / (MS_G/r) = (MS_G - MS_E) / MS_G = 1 - (MS_E / MS_G)

        h2 = 1 - (ms_error / ms_genotype)
        return max(0.0, min(1.0, h2))

    def calculate_lsd(self, ms_error: float, alpha: float = 0.05) -> Optional[float]:
        """
        LSD = t_crit * sqrt(2 * MSE / r)
        """
        if ms_error is None or self.r_bar == 0:
            return None

        df_error = self.n - self.n_genotypes
        if df_error < 1:
            return None

        # Approximation of t-critical value
        # For large degrees of freedom, t approaches z (1.96 for 5%, 2.576 for 1%)
        # Simple lookup for common small DFs? Or just use z-score approximation for now as scipy is missing.
        # Using a simple approximation function:
        t_crit = self._approximate_t_critical(df_error, alpha)

        lsd = t_crit * math.sqrt(2 * ms_error / self.r_bar)
        return lsd

    def _approximate_t_critical(self, df: int, alpha: float) -> float:
        """
        Very rough approximation of t-critical value.
        """
        if alpha == 0.05:
            if df > 120: return 1.960
            if df >= 60: return 2.000
            if df >= 40: return 2.021
            if df >= 30: return 2.042
            if df >= 20: return 2.086
            if df >= 10: return 2.228
            return 2.571 # df=5
        elif alpha == 0.01:
            if df > 120: return 2.576
            if df >= 60: return 2.660
            if df >= 30: return 2.750
            if df >= 10: return 3.169
            return 4.032 # df=5
        return 2.0 # Default fallback

    def calculate_genetic_gain(self, h2: float, phenotypic_std_dev: float, selection_intensity: float = 1.755) -> Optional[float]:
        """
        Expected Genetic Gain: delta_G = i * h2 * sigma_p
        i = selection intensity (1.755 corresponds to selecting top 10% in large pop)
        """
        if h2 is None or phenotypic_std_dev is None:
            return None
        return selection_intensity * h2 * phenotypic_std_dev
