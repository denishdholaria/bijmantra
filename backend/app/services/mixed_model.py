"""
Mixed Model Service

Provides formula-driven Mixed Model Equations (MME) solver for phenotypic analysis.
Supports complex experimental designs (RCBD, Alpha-Lattice, Row-Column) via
R-style formula syntax:

    Yield ~ Genotype + Rep + (1|Block)

Solver uses Henderson's Mixed Model Equations to estimate:
- BLUEs (Best Linear Unbiased Estimates) for fixed effects
- BLUPs (Best Linear Unbiased Predictions) for random effects
- Variance Components (Vg, Ve) via Restricted Maximum Likelihood (REML)
"""

import numpy as np
import pandas as pd
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from scipy import linalg

# Try importing patsy for robust formula parsing
try:
    import patsy
    PATSY_AVAILABLE = True
except ImportError:
    PATSY_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MixedModelResult:
    """Result from mixed model analysis"""
    formula: str
    fixed_effects: pd.DataFrame  # BLUEs, SE, p-values
    random_effects: pd.DataFrame  # BLUPs, SE
    variance_components: Dict[str, float]  # Vg, Ve, h2
    model_fit: Dict[str, float]  # AIC, BIC, LogLik
    residuals: List[float]
    fitted_values: List[float]
    converged: bool
    iterations: int


class MixedModelService:
    """
    Service for formula-driven mixed model analysis.
    
    Orchestrates:
    1. Formula Parsing -> Design Matrices (X, Z)
    2. Variance Component Estimation (REML)
    3. MME Solution (BLUEs, BLUPs)
    """

    def __init__(self):
        if not PATSY_AVAILABLE:
            logger.warning("Patsy not found. Falling back to custom formula parser (limited syntax).")

    def _parse_formula_custom(self, formula: str, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Custom lightweight parser for R-style formulas.
        Supports: y ~ x1 + x2 + (1|z1) + (1|z2)
        Limitations: No interactions (: or *), no functions (log(x)), no intricate nesting /
        
        Returns:
            y (outcome), X (fixed), Z (random) as DataFrames
        """
        # 1. Split into LHS and RHS
        if "~" not in formula:
            raise ValueError(f"Invalid formula: {formula} (missing '~')")

        lhs, rhs = formula.split("~", 1)
        response_var = lhs.strip()

        # 2. Process RHS terms
        # Split by '+' but respect parentheses
        # Simple regex split by + might break (1|group) if it had + inside, but standard syntax usually doesn't for simple random intercepts
        terms = [t.strip() for t in rhs.split("+")]

        fixed_terms = []
        random_terms = []

        for term in terms:
            # Check for random effect syntax (1|group)
            random_match = re.match(r"\(\s*1\s*\|\s*(\w+)\s*\)", term)
            if random_match:
                random_terms.append(random_match.group(1))
            else:
                fixed_terms.append(term)

        # 3. Build Matrices

        # y (Outcome)
        if response_var not in data.columns:
            raise KeyError(f"Response variable '{response_var}' not found in data")
        y = data[[response_var]]

        # X (Fixed Effects) - One-Hot Encoding for categorical
        # Constant intercept is implicit in most mixed models, usually added as first col
        # mimic patsy: Intercept + fixed_terms

        # Start with Intercept
        X = pd.DataFrame({"Intercept": np.ones(len(data))}, index=data.index)

        for term in fixed_terms:
            if term == "1": continue # Intercept already added
            if term == "0":
                X.drop(columns=["Intercept"], inplace=True)
                continue

            if term not in data.columns:
                 raise KeyError(f"Fixed effect '{term}' not found in data")

            # If numeric, add as is
            if pd.api.types.is_numeric_dtype(data[term]):
                X[term] = data[term]
            else:
                # If categorical, get dummies (drop_first=True to avoid collinearity with intercept?)
                # Statsmodels/R usually uses treatment contrasts (drop first level)
                dummies = pd.get_dummies(data[term], prefix=term, drop_first=True)
                # Ensure boolean/int dummies are float
                dummies = dummies.astype(float)
                X = pd.concat([X, dummies], axis=1)

        # Z (Random Effects) - One-Hot Encoding (NO drop_first, we want incidence for all levels)
        Z = pd.DataFrame(index=data.index)

        for term in random_terms:
            if term not in data.columns:
                 raise KeyError(f"Random effect '{term}' not found in data")

            # Get dummies for all levels
            dummies = pd.get_dummies(data[term], prefix=term) # , sparse=True?
            dummies = dummies.astype(float)
            Z = pd.concat([Z, dummies], axis=1)

        if Z.empty:
            # If no random effects, maybe just regular OLS?
            # But MME solver expects Z. Create dummy Z of zeros?
            # Or raise error that this is a fixed model?
            pass

        return y, X, Z

    def _parse_formula_patsy(self, formula: str, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Parse formula using Patsy (robust).
        Handles complex syntax like C(Genotype), interactions, etc.
        """
        # Split formula into fixed and random parts manually since patsy doesn't support (1|group) syntax directly
        # lme4/pymmer do this by custom parsing too.

        # We start with the lightweight split again to separate random parts
        if "~" not in formula:
            raise ValueError(f"Invalid formula: {formula}")

        lhs, rhs = formula.split("~", 1)

        # Extract random terms (1|group)
        # Regex to find (expr | group)
        random_pattern = r"\(([^\|]+)\|([^\)]+)\)"
        random_matches = re.findall(random_pattern, rhs)

        # Remove random terms from RHS to get fixed formula
        fixed_rhs = re.sub(random_pattern, "", rhs)
        # Clean up dangling pluses
        fixed_rhs = re.sub(r"\+\s*\+", "+", fixed_rhs).strip().strip("+")
        if not fixed_rhs: fixed_rhs = "1"

        fixed_formula = f"{lhs} ~ {fixed_rhs}"

        # Build Fixed X matrix
        y, X = patsy.dmatrices(fixed_formula, data, return_type='dataframe')

        # Build Random Z matrix
        # For simple random intercepts (1|Group), Z is just dummy matrix of Group
        # For random slopes (Slope|Group), Z is X_slope * Dummy_Group (row-wise interaction)

        Z_parts = []
        for expr, group in random_matches:
            expr = expr.strip()
            group = group.strip()

            # Simple Random Intercept: expr is "1"
            if expr == "1":
                # Z is incidence matrix of group
                # patsy can do this: "0 + C(group)" (0 removes intercept so we get all levels)
                # But need to make sure we treat it as categorical
                if group in data.columns:
                    # Cast to categorical string to ensure discrete levels
                    # But patsy syntax C() handles this
                    z_part = patsy.dmatrix(f"0 + C({group})", data, return_type='dataframe')
                    # Rename info to be pretty
                    z_part.columns = [c.replace("C(", "").replace(")", "").replace("[", "").replace("]", ".") for c in z_part.columns]
                    Z_parts.append(z_part)
                else:
                    raise KeyError(f"Grouping variable '{group}' not found")
            else:
                # Random Slope (e.g. Days|Subject)
                logger.warning(f"Random slopes ({expr}|{group}) not strictly supported in this version. Treating as intercept.")
                # Fallback to intercept logic for now or implement row-wise product
                z_part = patsy.dmatrix(f"0 + C({group})", data, return_type='dataframe')
                Z_parts.append(z_part)

        if Z_parts:
            Z = pd.concat(Z_parts, axis=1)
        else:
            Z = pd.DataFrame(index=data.index)

        return pd.DataFrame(y), X, Z

    def parse_formula(self, formula: str, data: Union[pd.DataFrame, List[Dict]]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Main entry point for formula parsing.
        """
        df = pd.DataFrame(data) if isinstance(data, list) else data

        if PATSY_AVAILABLE:
            return self._parse_formula_patsy(formula, df)
        else:
            return self._parse_formula_custom(formula, df)

    def solve_mme(
        self,
        y: pd.DataFrame,
        X: pd.DataFrame,
        Z: pd.DataFrame,
        weights: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Solve Henderson's Mixed Model Equations (MME).
        
        y = Xβ + Zu + ε
        
        MME:
        [ X'X   X'Z     ] [ β̂ ]   [ X'y ]
        [ Z'X   Z'Z+λI  ] [ û ] = [ Z'y ]
        
        where λ = σ²e / σ²u  (ratio of residual variance to random effect variance)
        """

        # Import compute engine for REML estimation
        # We need variance components to define λ
        # Cyclic import check?
        from app.services.compute_engine import compute_engine

        # 1. Estimate Variance Components using REML
        # Using Identity matrix (I) for relationship matrix A for now (assuming unrelated levels unless pedigree provided)
        # In this Sprint 3, we focus on designs (Blocks/Reps), where levels are independent.
        # Sprint 6 adds Pedigree A-matrix support.

        n_levels_random = Z.shape[1]
        A = np.eye(n_levels_random)

        y_np = y.values.flatten()
        X_np = X.values
        Z_np = Z.values

        reml_res = compute_engine.estimate_variance_components(
            phenotypes=y_np,
            fixed_effects=X_np,
            random_effects=Z_np,
            relationship_matrix=A,
            method="ai-reml" # Asymptotic Information REML
        )

        var_a = reml_res.var_additive # Random effect variance (Vg)
        var_e = reml_res.var_residual # Residual variance (Ve)

        # 2. Solve MME with estimated variances
        blup_res = compute_engine.compute_blup(
            phenotypes=y_np,
            fixed_effects=X_np,
            random_effects=Z_np,
            relationship_matrix_inv=np.linalg.inv(A), # I inverse is I
            var_additive=var_a,
            var_residual=var_e
        )

        # 3. Format Results

        # Fixed Effects (BLUEs)
        blues = pd.DataFrame({
            "term": X.columns,
            "estimate": blup_res.fixed_effects,
            # SE/p-values would come from inverse of LHS (C matrix) diagonals
            # Ideally compute_engine should return C_inverse or SEs.
            # For now, placeholder or basic calc if engine doesn't expose SE
        })

        # Random Effects (BLUPs)
        blups = pd.DataFrame({
            "term": Z.columns,
            "estimate": blup_res.breeding_values
        })

        # Residuals
        # ε = y - Xβ - Zu
        fitted = X_np @ blup_res.fixed_effects + Z_np @ blup_res.breeding_values
        residuals = y_np - fitted

        return {
            "fixed_effects": blues,
            "random_effects": blups,
            "variance_components": {
                "var_random": var_a,
                "var_residual": var_e,
                "heritability": reml_res.heritability
            },
            "fitted": fitted.tolist(),
            "residuals": residuals.tolist(),
            "converged": reml_res.converged,
            "iterations": reml_res.iterations
        }

    def analyze_rcbd(
        self,
        data: List[Dict],
        trait: str,
        genotype_col: str = "genotype",
        block_col: str = "block"
    ) -> Dict[str, Any]:
        """
        Preset for Randomized Complete Block Design.
        Formula: Trait ~ Genotype + (1|Block)
        
        Note: Genotype is usually Fixed for BLUEs (Trial evaluation)
              but Random for BLUPs/Selection (Breeding value estimation).
              This method assumes Genotype is FIXED (BLUEs) as per standard RCBD ANOVA logic,
              with Block as Random.
              
        Wait, for breeding, we often want Genotype as Random (BLUPs).
        Let's offer both or default to Fixed? 
        Standard "analyze trial" usually implies BLUEs for variety release.
        "Breeding Value" implies BLUPs.
        
        Let's stick to standard mixed model convention:
        y ~ Genotype (Fixed) + (1|Block) (Random)
        """
        formula = f"{trait} ~ {genotype_col} + (1|{block_col})"
        y, X, Z = self.parse_formula(formula, data)
        return self.solve_mme(y, X, Z)

    def analyze_alpha_lattice(
        self,
        data: List[Dict],
        trait: str,
        genotype_col: str = "genotype",
        rep_col: str = "rep",
        block_col: str = "block"
    ) -> Dict[str, Any]:
        """
        Preset for Alpha-Lattice Design.
        Formula: Trait ~ Genotype + Rep + (1|Rep:Block)
        
        Assuming Block is nested within Rep.
        Since our parser logic relies on column names, creating a nested column is safer.
        """
        df = pd.DataFrame(data)
        # Create nested block ID "Rep1_Blk1" ensuring uniqueness
        df["_nested_block"] = df[rep_col].astype(str) + "_" + df[block_col].astype(str)

        formula = f"{trait} ~ {genotype_col} + {rep_col} + (1|_nested_block)"
        y, X, Z = self.parse_formula(formula, df)
        return self.solve_mme(y, X, Z)

# Global Instance
mixed_model_service = MixedModelService()
