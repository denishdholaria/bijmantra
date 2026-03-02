//! Statistical functions for breeding value estimation
//! BLUP, GBLUP, and genomic prediction

use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

/// BLUP result
#[derive(Serialize, Deserialize)]
pub struct BLUPResult {
    pub breeding_values: Vec<f64>,
    pub reliability: Vec<f64>,
    pub mean: f64,
    pub variance: f64,
    pub heritability: f64,
}

/// Simple BLUP estimation using Henderson's mixed model equations
/// y = Xb + Zu + e
#[wasm_bindgen]
pub fn estimate_blup(
    phenotypes: &[f64],
    relationship_matrix: &[f64],
    n_individuals: usize,
    heritability: f64,
) -> JsValue {
    let result = calculate_blup(phenotypes, relationship_matrix, n_individuals, heritability);
    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Internal BLUP calculation logic
pub(crate) fn calculate_blup(
    phenotypes: &[f64],
    relationship_matrix: &[f64],
    n_individuals: usize,
    heritability: f64,
) -> BLUPResult {
    // Calculate variance ratio
    // Guard against division by zero if heritability is 0
    let lambda = if heritability > 0.0 {
        (1.0 - heritability) / heritability
    } else {
        1e6 // Large value implies minimal genetic contribution
    };

    // Calculate phenotype statistics
    let mut sum = 0.0;
    let mut sum2 = 0.0;
    let mut count = 0;

    for &p in phenotypes {
        if !p.is_nan() {
            sum += p;
            sum2 += p * p;
            count += 1;
        }
    }

    let mean = if count > 0 { sum / count as f64 } else { 0.0 };
    let variance = if count > 1 {
        (sum2 - sum * sum / count as f64) / (count - 1) as f64
    } else {
        1.0
    };

    // Build mixed model equations: (Z'Z + λA⁻¹)u = Z'(y - μ)
    // Simplified: use relationship matrix directly

    let mut breeding_values = vec![0.0; n_individuals];
    let mut reliability = vec![0.0; n_individuals];

    // Simple estimation: weighted average of own performance and relatives
    for i in 0..n_individuals {
        let mut weighted_sum = 0.0;
        let mut weight_sum = 0.0;

        for j in 0..n_individuals {
            if !phenotypes[j].is_nan() {
                let rel = relationship_matrix[i * n_individuals + j];
                let weight = rel * rel; // Weight by relationship squared
                weighted_sum += weight * (phenotypes[j] - mean);
                weight_sum += weight;
            }
        }

        if weight_sum > 0.0 {
            breeding_values[i] = weighted_sum / weight_sum * heritability;
            reliability[i] = (weight_sum / (weight_sum + lambda)).min(0.99);
        }
    }

    BLUPResult {
        breeding_values,
        reliability,
        mean,
        variance,
        heritability,
    }
}

#[cfg(test)]
mod tests_gblup {
    use super::*;

    #[test]
    fn test_gblup_simple() {
        let phenotypes = vec![10.0, 12.0, 11.0];
        let n = 3;
        // Simple identity GRM (independent individuals)
        let grm = vec![1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0];
        let heritability = 0.5;

        let result = estimate_gblup_impl(&phenotypes, &grm, n, heritability);

        assert_eq!(result.gebv.len(), n);
        assert_eq!(result.reliability.len(), n);
        assert_eq!(result.accuracy.len(), n);

        // With identity GRM and h2=0.5, lambda = 1.
        // Mean = 11.0.
        // Check if values are reasonable (not NaN)
        for val in result.gebv {
            assert!(!val.is_nan());
        }
        assert!((result.mean - 11.0).abs() < 1e-6);
    }

    #[test]
    fn test_gblup_nan_handling() {
        let phenotypes = vec![10.0, f64::NAN, 12.0];
        let n = 3;
        let grm = vec![1.0, 0.1, 0.2, 0.1, 1.0, 0.3, 0.2, 0.3, 1.0];
        let heritability = 0.3;

        let result = estimate_gblup_impl(&phenotypes, &grm, n, heritability);

        assert_eq!(result.gebv.len(), n);
        assert!(!result.mean.is_nan());
        // Mean should be (10+12)/2 = 11.0
        assert!((result.mean - 11.0).abs() < 1e-6);

        // GEBV for the missing individual should be estimated (via relatives)
        assert!(!result.gebv[1].is_nan());
    }

    #[test]
    fn test_gblup_zero_variance() {
        let phenotypes = vec![10.0, 10.0, 10.0];
        let n = 3;
        let grm = vec![1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0];
        let heritability = 0.5;

        let result = estimate_gblup_impl(&phenotypes, &grm, n, heritability);

        assert_eq!(result.mean, 10.0);
        // Variance should be 0 (or very small)
        assert!((result.genetic_variance).abs() < 1e-6);

        // GEBVs should be 0 because deviations from mean are 0
        for val in result.gebv {
            assert!(val.abs() < 1e-6);
        }
    }
}

/// Genomic BLUP (GBLUP) result
#[derive(Serialize, Deserialize)]
pub struct GBLUPResult {
    pub gebv: Vec<f64>, // Genomic Estimated Breeding Values
    pub reliability: Vec<f64>,
    pub accuracy: Vec<f64>,
    pub mean: f64,
    pub genetic_variance: f64,
    pub residual_variance: f64,
}

/// Estimate GEBV using GBLUP (internal implementation)
pub fn estimate_gblup_impl(
    phenotypes: &[f64],
    grm: &[f64],
    n_individuals: usize,
    heritability: f64,
) -> GBLUPResult {
    let lambda = (1.0 - heritability) / heritability;

    // Calculate mean
    let mut sum = 0.0;
    let mut count = 0;
    for &p in phenotypes {
        if !p.is_nan() {
            sum += p;
            count += 1;
        }
    }
    let mean = if count > 0 { sum / count as f64 } else { 0.0 };

    // Calculate variance
    let mut var_sum = 0.0;
    for &p in phenotypes {
        if !p.is_nan() {
            var_sum += (p - mean).powi(2);
        }
    }
    let total_variance = if count > 1 {
        var_sum / (count - 1) as f64
    } else {
        1.0
    };
    let genetic_variance = total_variance * heritability;
    let residual_variance = total_variance * (1.0 - heritability);

    // Build coefficient matrix: G + λI
    let mut coef = vec![0.0; n_individuals * n_individuals];
    for i in 0..n_individuals {
        for j in 0..n_individuals {
            coef[i * n_individuals + j] = grm[i * n_individuals + j];
            if i == j {
                coef[i * n_individuals + j] += lambda;
            }
        }
    }

    // Right-hand side: y - μ
    let rhs: Vec<f64> = phenotypes
        .iter()
        .map(|&p| if p.is_nan() { 0.0 } else { p - mean })
        .collect();

    // Solve using Gauss-Seidel iteration
    let mut gebv = vec![0.0; n_individuals];
    for _ in 0..100 {
        for i in 0..n_individuals {
            let mut sum = rhs[i];
            for j in 0..n_individuals {
                if i != j {
                    sum -= coef[i * n_individuals + j] * gebv[j];
                }
            }
            if coef[i * n_individuals + i].abs() > 1e-10 {
                gebv[i] = sum / coef[i * n_individuals + i];
            }
        }
    }

    // Calculate reliability and accuracy
    let mut reliability = vec![0.0; n_individuals];
    let mut accuracy = vec![0.0; n_individuals];

    for i in 0..n_individuals {
        let diag = grm[i * n_individuals + i];
        let pev = lambda / (diag + lambda); // Prediction error variance (simplified)
        reliability[i] = (1.0 - pev).clamp(0.0, 0.99);
        accuracy[i] = reliability[i].sqrt();
    }

    GBLUPResult {
        gebv,
        reliability,
        accuracy,
        mean,
        genetic_variance,
        residual_variance,
    }
}

/// Estimate GEBV using GBLUP
#[wasm_bindgen]
pub fn estimate_gblup(
    phenotypes: &[f64],
    grm: &[f64],
    n_individuals: usize,
    heritability: f64,
) -> JsValue {
    let result = estimate_gblup_impl(phenotypes, grm, n_individuals, heritability);
    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Selection index result
#[derive(Serialize, Deserialize)]
pub struct SelectionIndexResult {
    pub index_values: Vec<f64>,
    pub rankings: Vec<usize>,
    pub selection_differential: f64,
    pub expected_response: f64,
}

/// Calculate selection index
#[wasm_bindgen]
pub fn calculate_selection_index(
    trait_values: &[f64],     // n_individuals * n_traits
    economic_weights: &[f64], // n_traits
    n_individuals: usize,
    n_traits: usize,
) -> JsValue {
    let mut index_values = vec![0.0; n_individuals];

    // Calculate index: I = Σ(w_i * x_i)
    for i in 0..n_individuals {
        let mut idx = 0.0;
        for t in 0..n_traits {
            let val = trait_values[i * n_traits + t];
            if !val.is_nan() {
                idx += economic_weights[t] * val;
            }
        }
        index_values[i] = idx;
    }

    // Rank individuals
    let mut rankings: Vec<usize> = (0..n_individuals).collect();
    rankings.sort_by(|&a, &b| {
        index_values[b]
            .partial_cmp(&index_values[a])
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    // Calculate selection differential (top 10%)
    let n_selected = (n_individuals as f64 * 0.1).ceil() as usize;
    let mean_all: f64 = index_values.iter().sum::<f64>() / n_individuals as f64;
    let mean_selected: f64 = rankings
        .iter()
        .take(n_selected)
        .map(|&i| index_values[i])
        .sum::<f64>()
        / n_selected as f64;

    let selection_differential = mean_selected - mean_all;

    // Expected response (assuming h² = 0.3)
    let expected_response = selection_differential * 0.3;

    let result = SelectionIndexResult {
        index_values,
        rankings,
        selection_differential,
        expected_response,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Genetic correlation result
#[derive(Serialize, Deserialize)]
pub struct GeneticCorrelationResult {
    pub correlation_matrix: Vec<f64>,
    pub n_traits: usize,
    pub trait_means: Vec<f64>,
    pub trait_variances: Vec<f64>,
}

/// Calculate genetic correlations between traits
#[wasm_bindgen]
pub fn calculate_genetic_correlations(
    trait_values: &[f64],
    n_individuals: usize,
    n_traits: usize,
) -> JsValue {
    // Calculate means
    let mut means = vec![0.0; n_traits];
    let mut counts = vec![0usize; n_traits];

    for i in 0..n_individuals {
        for t in 0..n_traits {
            let val = trait_values[i * n_traits + t];
            if !val.is_nan() {
                means[t] += val;
                counts[t] += 1;
            }
        }
    }

    for t in 0..n_traits {
        if counts[t] > 0 {
            means[t] /= counts[t] as f64;
        }
    }

    // Calculate variances and covariances
    let mut variances = vec![0.0; n_traits];
    let mut covariances = vec![0.0; n_traits * n_traits];

    for i in 0..n_individuals {
        for t1 in 0..n_traits {
            let v1 = trait_values[i * n_traits + t1];
            if v1.is_nan() {
                continue;
            }

            let d1 = v1 - means[t1];
            variances[t1] += d1 * d1;

            for t2 in t1..n_traits {
                let v2 = trait_values[i * n_traits + t2];
                if v2.is_nan() {
                    continue;
                }

                let d2 = v2 - means[t2];
                covariances[t1 * n_traits + t2] += d1 * d2;
                if t1 != t2 {
                    covariances[t2 * n_traits + t1] += d1 * d2;
                }
            }
        }
    }

    // Normalize
    for t in 0..n_traits {
        if counts[t] > 1 {
            variances[t] /= (counts[t] - 1) as f64;
        }
    }

    // Calculate correlations
    let mut correlations = vec![0.0; n_traits * n_traits];
    for t1 in 0..n_traits {
        correlations[t1 * n_traits + t1] = 1.0;
        for t2 in (t1 + 1)..n_traits {
            let denom = (variances[t1] * variances[t2]).sqrt();
            let corr = if denom > 0.0 {
                covariances[t1 * n_traits + t2] / denom / counts[t1].min(counts[t2]) as f64
            } else {
                0.0
            };
            correlations[t1 * n_traits + t2] = corr.clamp(-1.0, 1.0);
            correlations[t2 * n_traits + t1] = corr.clamp(-1.0, 1.0);
        }
    }

    let result = GeneticCorrelationResult {
        correlation_matrix: correlations,
        n_traits,
        trait_means: means,
        trait_variances: variances,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Heritability estimation result
#[derive(Serialize, Deserialize)]
pub struct HeritabilityResult {
    pub heritability: f64,
    pub genetic_variance: f64,
    pub environmental_variance: f64,
    pub phenotypic_variance: f64,
    pub standard_error: f64,
}

/// Estimate heritability using variance components
#[wasm_bindgen]
pub fn estimate_heritability(phenotypes: &[f64], grm: &[f64], n_individuals: usize) -> JsValue {
    // Calculate phenotypic variance
    let mut sum = 0.0;
    let mut sum2 = 0.0;
    let mut count = 0;

    for &p in phenotypes {
        if !p.is_nan() {
            sum += p;
            sum2 += p * p;
            count += 1;
        }
    }

    let mean = if count > 0 { sum / count as f64 } else { 0.0 };
    let phenotypic_variance = if count > 1 {
        (sum2 - sum * sum / count as f64) / (count - 1) as f64
    } else {
        1.0
    };

    // Estimate genetic variance using GRM
    // Simplified: use correlation between phenotypes and GRM
    let mut cov_sum = 0.0;
    let mut grm_var = 0.0;
    let mut pair_count = 0;

    for i in 0..n_individuals {
        if phenotypes[i].is_nan() {
            continue;
        }
        for j in (i + 1)..n_individuals {
            if phenotypes[j].is_nan() {
                continue;
            }

            let pheno_cov = (phenotypes[i] - mean) * (phenotypes[j] - mean);
            let grm_val = grm[i * n_individuals + j];

            cov_sum += pheno_cov * grm_val;
            grm_var += grm_val * grm_val;
            pair_count += 1;
        }
    }

    let genetic_variance = if grm_var > 0.0 && pair_count > 0 {
        (cov_sum / grm_var).max(0.0).min(phenotypic_variance)
    } else {
        phenotypic_variance * 0.3 // Default assumption
    };

    let environmental_variance = phenotypic_variance - genetic_variance;
    let heritability = genetic_variance / phenotypic_variance;

    // Standard error approximation
    let se = (2.0 * (1.0 - heritability).powi(2) / count as f64).sqrt();

    let result = HeritabilityResult {
        heritability: heritability.clamp(0.0, 1.0),
        genetic_variance,
        environmental_variance: environmental_variance.max(0.0),
        phenotypic_variance,
        standard_error: se,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

#[cfg(test)]
mod tests_blup {
    use super::*;

    #[test]
    fn test_blup_basic() {
        let phenotypes = vec![100.0, 105.0, 98.0, 102.0];
        let relationship_matrix = vec![
            1.0, 0.5, 0.25, 0.1, 0.5, 1.0, 0.3, 0.2, 0.25, 0.3, 1.0, 0.15, 0.1, 0.2, 0.15, 1.0,
        ];
        let n_individuals = 4;
        let heritability = 0.3;

        let result = calculate_blup(
            &phenotypes,
            &relationship_matrix,
            n_individuals,
            heritability,
        );

        assert_eq!(result.breeding_values.len(), n_individuals);
        assert_eq!(result.reliability.len(), n_individuals);

        // Basic sanity checks
        assert!((result.mean - 101.25).abs() < 1e-6);
        assert!(result.variance > 0.0);

        // Check reliability is within bounds
        for &r in &result.reliability {
            assert!((0.0..=1.0).contains(&r));
        }
    }

    #[test]
    fn test_blup_nan_phenotypes() {
        let phenotypes = vec![100.0, f64::NAN, 98.0, 102.0];
        let relationship_matrix = vec![
            1.0, 0.5, 0.25, 0.1, 0.5, 1.0, 0.3, 0.2, 0.25, 0.3, 1.0, 0.15, 0.1, 0.2, 0.15, 1.0,
        ];
        let n_individuals = 4;
        let heritability = 0.3;

        let result = calculate_blup(
            &phenotypes,
            &relationship_matrix,
            n_individuals,
            heritability,
        );

        // Mean should exclude NaN
        // Sum = 100 + 98 + 102 = 300, Count = 3, Mean = 100
        assert!((result.mean - 100.0).abs() < 1e-6);

        // Breeding value for NaN individual (index 1) should still be calculated based on relatives
        assert!(!result.breeding_values[1].is_nan());
    }

    #[test]
    fn test_blup_zero_heritability() {
        let phenotypes = vec![10.0, 12.0];
        let relationship_matrix = vec![1.0, 0.0, 0.0, 1.0];
        let n_individuals = 2;
        let heritability = 0.0;

        let result = calculate_blup(
            &phenotypes,
            &relationship_matrix,
            n_individuals,
            heritability,
        );

        // With h2=0, breeding values should be 0
        for &bv in &result.breeding_values {
            assert_eq!(bv, 0.0);
        }

        // Lambda should be large (guarded)
        // Reliability should be small (near 0)
        for &r in &result.reliability {
            assert!(r < 0.01);
        }
    }

    #[test]
    fn test_blup_high_heritability() {
        let phenotypes = vec![10.0, 12.0];
        let relationship_matrix = vec![1.0, 0.0, 0.0, 1.0];
        let n_individuals = 2;
        let heritability = 0.99; // Avoid 1.0 to avoid potential division issues if code wasn't robust

        let result = calculate_blup(
            &phenotypes,
            &relationship_matrix,
            n_individuals,
            heritability,
        );

        // High heritability -> high reliability
        for &r in &result.reliability {
            assert!(r > 0.9);
        }
    }

    #[test]
    fn test_blup_single_individual() {
        let phenotypes = vec![10.0];
        let relationship_matrix = vec![1.0];
        let n_individuals = 1;
        let heritability = 0.5;

        let result = calculate_blup(
            &phenotypes,
            &relationship_matrix,
            n_individuals,
            heritability,
        );

        assert_eq!(result.mean, 10.0);
        assert_eq!(result.variance, 1.0); // Default when count <= 1

        // With only one individual, deviation is 0 (10 - 10), so BV should be 0
        assert_eq!(result.breeding_values[0], 0.0);
    }
}
