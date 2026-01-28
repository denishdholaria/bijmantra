//! Statistical functions for breeding value estimation
//! BLUP, GBLUP, and genomic prediction

use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};

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
    // Calculate variance ratio
    let lambda = (1.0 - heritability) / heritability;

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

    let result = BLUPResult {
        breeding_values,
        reliability,
        mean,
        variance,
        heritability,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Genomic BLUP (GBLUP) result
#[derive(Serialize, Deserialize)]
pub struct GBLUPResult {
    pub gebv: Vec<f64>,           // Genomic Estimated Breeding Values
    pub reliability: Vec<f64>,
    pub accuracy: Vec<f64>,
    pub mean: f64,
    pub genetic_variance: f64,
    pub residual_variance: f64,
}

/// Estimate GEBV using GBLUP
#[wasm_bindgen]
pub fn estimate_gblup(
    phenotypes: &[f64],
    grm: &[f64],
    n_individuals: usize,
    heritability: f64,
) -> JsValue {
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
    let total_variance = if count > 1 { var_sum / (count - 1) as f64 } else { 1.0 };
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
    let mut rhs: Vec<f64> = phenotypes.iter()
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
        reliability[i] = (1.0 - pev).max(0.0).min(0.99);
        accuracy[i] = reliability[i].sqrt();
    }

    let result = GBLUPResult {
        gebv,
        reliability,
        accuracy,
        mean,
        genetic_variance,
        residual_variance,
    };

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
    trait_values: &[f64],      // n_individuals * n_traits
    economic_weights: &[f64],  // n_traits
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
        index_values[b].partial_cmp(&index_values[a]).unwrap_or(std::cmp::Ordering::Equal)
    });

    // Calculate selection differential (top 10%)
    let n_selected = (n_individuals as f64 * 0.1).ceil() as usize;
    let mean_all: f64 = index_values.iter().sum::<f64>() / n_individuals as f64;
    let mean_selected: f64 = rankings.iter()
        .take(n_selected)
        .map(|&i| index_values[i])
        .sum::<f64>() / n_selected as f64;
    
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
            if v1.is_nan() { continue; }
            
            let d1 = v1 - means[t1];
            variances[t1] += d1 * d1;

            for t2 in t1..n_traits {
                let v2 = trait_values[i * n_traits + t2];
                if v2.is_nan() { continue; }
                
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
            correlations[t1 * n_traits + t2] = corr.max(-1.0).min(1.0);
            correlations[t2 * n_traits + t1] = corr.max(-1.0).min(1.0);
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
pub fn estimate_heritability(
    phenotypes: &[f64],
    grm: &[f64],
    n_individuals: usize,
) -> JsValue {
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
        if phenotypes[i].is_nan() { continue; }
        for j in (i + 1)..n_individuals {
            if phenotypes[j].is_nan() { continue; }
            
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
        heritability: heritability.max(0.0).min(1.0),
        genetic_variance,
        environmental_variance: environmental_variance.max(0.0),
        phenotypic_variance,
        standard_error: se,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}
