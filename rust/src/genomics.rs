//! Genomic data processing functions
//! High-performance genotype matrix operations and LD calculations

use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};
use ndarray::{Array1, Array2, Axis};

/// Genotype encoding: 0 = AA, 1 = AB, 2 = BB, -1 = missing
#[wasm_bindgen]
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum GenotypeEncoding {
    Additive,    // 0, 1, 2
    Dominant,    // 0, 1, 1
    Recessive,   // 0, 0, 1
}

/// Result of allele frequency calculation
#[derive(Serialize, Deserialize)]
pub struct AlleleFrequencies {
    pub minor_allele_freq: Vec<f64>,
    pub major_allele_freq: Vec<f64>,
    pub heterozygosity: Vec<f64>,
    pub missing_rate: Vec<f64>,
}

/// Calculate allele frequencies from genotype matrix
#[wasm_bindgen]
pub fn calculate_allele_frequencies(genotypes: &[i32], n_samples: usize, n_markers: usize) -> JsValue {
    let mut maf = Vec::with_capacity(n_markers);
    let mut het = Vec::with_capacity(n_markers);
    let mut missing = Vec::with_capacity(n_markers);

    for j in 0..n_markers {
        let mut sum = 0.0;
        let mut het_count = 0;
        let mut valid_count = 0;
        let mut missing_count = 0;

        for i in 0..n_samples {
            let idx = i * n_markers + j;
            let geno = genotypes[idx];
            
            if geno >= 0 {
                sum += geno as f64;
                if geno == 1 {
                    het_count += 1;
                }
                valid_count += 1;
            } else {
                missing_count += 1;
            }
        }

        if valid_count > 0 {
            let freq = sum / (2.0 * valid_count as f64);
            maf.push(freq.min(1.0 - freq));
            het.push(het_count as f64 / valid_count as f64);
        } else {
            maf.push(0.0);
            het.push(0.0);
        }
        missing.push(missing_count as f64 / n_samples as f64);
    }

    let result = AlleleFrequencies {
        minor_allele_freq: maf.clone(),
        major_allele_freq: maf.iter().map(|f| 1.0 - f).collect(),
        heterozygosity: het,
        missing_rate: missing,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// LD (Linkage Disequilibrium) result
#[derive(Serialize, Deserialize)]
pub struct LDResult {
    pub r_squared: f64,
    pub d_prime: f64,
    pub p_value: f64,
}

/// Calculate LD (r²) between two markers
#[wasm_bindgen]
pub fn calculate_ld_pair(geno1: &[i32], geno2: &[i32]) -> JsValue {
    let n = geno1.len();
    let mut sum_x = 0.0;
    let mut sum_y = 0.0;
    let mut sum_xy = 0.0;
    let mut sum_x2 = 0.0;
    let mut sum_y2 = 0.0;
    let mut valid = 0;

    for i in 0..n {
        if geno1[i] >= 0 && geno2[i] >= 0 {
            let x = geno1[i] as f64;
            let y = geno2[i] as f64;
            sum_x += x;
            sum_y += y;
            sum_xy += x * y;
            sum_x2 += x * x;
            sum_y2 += y * y;
            valid += 1;
        }
    }

    if valid < 2 {
        return serde_wasm_bindgen::to_value(&LDResult {
            r_squared: 0.0,
            d_prime: 0.0,
            p_value: 1.0,
        }).unwrap();
    }

    let n_f = valid as f64;
    let mean_x = sum_x / n_f;
    let mean_y = sum_y / n_f;
    
    let var_x = sum_x2 / n_f - mean_x * mean_x;
    let var_y = sum_y2 / n_f - mean_y * mean_y;
    let cov_xy = sum_xy / n_f - mean_x * mean_y;

    let r_squared = if var_x > 0.0 && var_y > 0.0 {
        (cov_xy * cov_xy) / (var_x * var_y)
    } else {
        0.0
    };

    // Simplified D' calculation
    let d_prime = if var_x > 0.0 && var_y > 0.0 {
        cov_xy.abs() / (var_x * var_y).sqrt()
    } else {
        0.0
    };

    let result = LDResult {
        r_squared,
        d_prime: d_prime.min(1.0),
        p_value: 0.0, // Would need chi-square calculation
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Calculate LD matrix for all marker pairs
#[wasm_bindgen]
pub fn calculate_ld_matrix(genotypes: &[i32], n_samples: usize, n_markers: usize) -> Vec<f64> {
    let mut ld_matrix = vec![0.0; n_markers * n_markers];
    
    // Pre-calculate means and variances
    let mut means = vec![0.0; n_markers];
    let mut vars = vec![0.0; n_markers];
    let mut counts = vec![0usize; n_markers];

    for j in 0..n_markers {
        let mut sum = 0.0;
        let mut sum2 = 0.0;
        let mut count = 0;

        for i in 0..n_samples {
            let geno = genotypes[i * n_markers + j];
            if geno >= 0 {
                let g = geno as f64;
                sum += g;
                sum2 += g * g;
                count += 1;
            }
        }

        if count > 0 {
            means[j] = sum / count as f64;
            vars[j] = sum2 / count as f64 - means[j] * means[j];
        }
        counts[j] = count;
    }

    // Calculate pairwise LD
    for j1 in 0..n_markers {
        ld_matrix[j1 * n_markers + j1] = 1.0; // Diagonal
        
        for j2 in (j1 + 1)..n_markers {
            let mut cov = 0.0;
            let mut valid = 0;

            for i in 0..n_samples {
                let g1 = genotypes[i * n_markers + j1];
                let g2 = genotypes[i * n_markers + j2];
                
                if g1 >= 0 && g2 >= 0 {
                    cov += (g1 as f64 - means[j1]) * (g2 as f64 - means[j2]);
                    valid += 1;
                }
            }

            let r2 = if valid > 0 && vars[j1] > 0.0 && vars[j2] > 0.0 {
                let cov_norm = cov / valid as f64;
                (cov_norm * cov_norm) / (vars[j1] * vars[j2])
            } else {
                0.0
            };

            ld_matrix[j1 * n_markers + j2] = r2;
            ld_matrix[j2 * n_markers + j1] = r2;
        }
    }

    ld_matrix
}

/// Hardy-Weinberg equilibrium test result
#[derive(Serialize, Deserialize)]
pub struct HWEResult {
    pub chi_squared: f64,
    pub p_value: f64,
    pub observed_het: f64,
    pub expected_het: f64,
    pub in_equilibrium: bool,
}

/// Test Hardy-Weinberg equilibrium for a marker
#[wasm_bindgen]
pub fn test_hwe(genotypes: &[i32]) -> JsValue {
    let mut n_aa = 0;
    let mut n_ab = 0;
    let mut n_bb = 0;

    for &g in genotypes {
        match g {
            0 => n_aa += 1,
            1 => n_ab += 1,
            2 => n_bb += 1,
            _ => {}
        }
    }

    let n = (n_aa + n_ab + n_bb) as f64;
    if n < 1.0 {
        return serde_wasm_bindgen::to_value(&HWEResult {
            chi_squared: 0.0,
            p_value: 1.0,
            observed_het: 0.0,
            expected_het: 0.0,
            in_equilibrium: true,
        }).unwrap();
    }

    let p = (2.0 * n_aa as f64 + n_ab as f64) / (2.0 * n);
    let q = 1.0 - p;

    let exp_aa = p * p * n;
    let exp_ab = 2.0 * p * q * n;
    let exp_bb = q * q * n;

    let chi2 = if exp_aa > 0.0 { (n_aa as f64 - exp_aa).powi(2) / exp_aa } else { 0.0 }
             + if exp_ab > 0.0 { (n_ab as f64 - exp_ab).powi(2) / exp_ab } else { 0.0 }
             + if exp_bb > 0.0 { (n_bb as f64 - exp_bb).powi(2) / exp_bb } else { 0.0 };

    // Approximate p-value using chi-square with 1 df
    let p_value = (-chi2 / 2.0).exp();

    let result = HWEResult {
        chi_squared: chi2,
        p_value,
        observed_het: n_ab as f64 / n,
        expected_het: 2.0 * p * q,
        in_equilibrium: p_value > 0.05,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Filter markers by MAF threshold
#[wasm_bindgen]
pub fn filter_by_maf(genotypes: &[i32], n_samples: usize, n_markers: usize, min_maf: f64) -> Vec<usize> {
    let mut passing_indices = Vec::new();

    for j in 0..n_markers {
        let mut sum = 0.0;
        let mut count = 0;

        for i in 0..n_samples {
            let geno = genotypes[i * n_markers + j];
            if geno >= 0 {
                sum += geno as f64;
                count += 1;
            }
        }

        if count > 0 {
            let freq = sum / (2.0 * count as f64);
            let maf = freq.min(1.0 - freq);
            if maf >= min_maf {
                passing_indices.push(j);
            }
        }
    }

    passing_indices
}

/// Impute missing genotypes using mean imputation
#[wasm_bindgen]
pub fn impute_missing_mean(genotypes: &[i32], n_samples: usize, n_markers: usize) -> Vec<f64> {
    let mut imputed = vec![0.0; n_samples * n_markers];

    for j in 0..n_markers {
        let mut sum = 0.0;
        let mut count = 0;

        // Calculate mean for this marker
        for i in 0..n_samples {
            let geno = genotypes[i * n_markers + j];
            if geno >= 0 {
                sum += geno as f64;
                count += 1;
            }
        }

        let mean = if count > 0 { sum / count as f64 } else { 1.0 };

        // Impute missing values
        for i in 0..n_samples {
            let idx = i * n_markers + j;
            let geno = genotypes[idx];
            imputed[idx] = if geno >= 0 { geno as f64 } else { mean };
        }
    }

    imputed
}
