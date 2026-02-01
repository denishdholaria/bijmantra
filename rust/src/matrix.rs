//! Matrix operations for genomic computations
//! Genomic Relationship Matrix (GRM) and kinship calculations

use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};
use ndarray::{Array2, Axis};

/// Genomic Relationship Matrix result
#[derive(Serialize, Deserialize)]
pub struct GRMResult {
    pub matrix: Vec<f64>,
    pub n_samples: usize,
    pub n_markers_used: usize,
    pub mean_diagonal: f64,
    pub mean_off_diagonal: f64,
}

/// Calculate Genomic Relationship Matrix (VanRaden Method 1)
/// G = ZZ' / (2 * sum(p * (1-p)))
#[wasm_bindgen]
pub fn calculate_grm(genotypes: &[i32], n_samples: usize, n_markers: usize) -> JsValue {
    // Calculate allele frequencies
    let mut freqs = vec![0.0; n_markers];
    let mut counts = vec![0usize; n_markers];

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
            freqs[j] = sum / (2.0 * count as f64);
        }
        counts[j] = count;
    }

    // Calculate scaling factor: 2 * sum(p * (1-p))
    let mut scale = 0.0;
    let mut markers_used = 0;
    for j in 0..n_markers {
        let p = freqs[j];
        if p > 0.0 && p < 1.0 {
            scale += 2.0 * p * (1.0 - p);
            markers_used += 1;
        }
    }

    if scale == 0.0 {
        scale = 1.0;
    }

    // Center genotypes: Z = X - 2p
    let mut z = vec![0.0; n_samples * n_markers];
    for i in 0..n_samples {
        for j in 0..n_markers {
            let idx = i * n_markers + j;
            let geno = genotypes[idx];
            if geno >= 0 {
                z[idx] = geno as f64 - 2.0 * freqs[j];
            } else {
                z[idx] = 0.0; // Missing values centered at 0
            }
        }
    }

    // Calculate G = ZZ' / scale
    let mut grm = vec![0.0; n_samples * n_samples];
    for i in 0..n_samples {
        for j in i..n_samples {
            let mut sum = 0.0;
            for k in 0..n_markers {
                sum += z[i * n_markers + k] * z[j * n_markers + k];
            }
            let g_ij = sum / scale;
            grm[i * n_samples + j] = g_ij;
            grm[j * n_samples + i] = g_ij;
        }
    }

    // Calculate statistics
    let mut diag_sum = 0.0;
    let mut off_diag_sum = 0.0;
    let mut off_diag_count = 0;

    for i in 0..n_samples {
        diag_sum += grm[i * n_samples + i];
        for j in (i + 1)..n_samples {
            off_diag_sum += grm[i * n_samples + j];
            off_diag_count += 1;
        }
    }

    let result = GRMResult {
        matrix: grm,
        n_samples,
        n_markers_used: markers_used,
        mean_diagonal: diag_sum / n_samples as f64,
        mean_off_diagonal: if off_diag_count > 0 { off_diag_sum / off_diag_count as f64 } else { 0.0 },
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Calculate pedigree-based relationship matrix (A-matrix)
#[wasm_bindgen]
pub fn calculate_a_matrix(sire_ids: &[i32], dam_ids: &[i32]) -> Vec<f64> {
    let n = sire_ids.len();
    let mut a = vec![0.0; n * n];

    // Initialize diagonal
    for i in 0..n {
        a[i * n + i] = 1.0;
    }

    // Calculate relationships
    for i in 0..n {
        let sire = sire_ids[i];
        let dam = dam_ids[i];

        // Self relationship (inbreeding)
        if sire >= 0 && dam >= 0 {
            let s = sire as usize;
            let d = dam as usize;
            if s < n && d < n {
                a[i * n + i] = 1.0 + 0.5 * a[s * n + d];
            }
        }

        // Relationships with others
        for j in (i + 1)..n {
            let mut rel = 0.0;
            
            if sire >= 0 && (sire as usize) < n {
                rel += 0.5 * a[(sire as usize) * n + j];
            }
            if dam >= 0 && (dam as usize) < n {
                rel += 0.5 * a[(dam as usize) * n + j];
            }

            a[i * n + j] = rel;
            a[j * n + i] = rel;
        }
    }

    a
}

/// Calculate kinship coefficient between two individuals
#[wasm_bindgen]
pub fn calculate_kinship(geno1: &[i32], geno2: &[i32]) -> f64 {
    let n = geno1.len();
    let mut ibs_sum = 0.0;
    let mut valid = 0;

    for i in 0..n {
        if geno1[i] >= 0 && geno2[i] >= 0 {
            // IBS (Identity By State) calculation
            let ibs = match (geno1[i], geno2[i]) {
                (0, 0) | (2, 2) => 2.0,
                (0, 1) | (1, 0) | (1, 2) | (2, 1) | (1, 1) => 1.0,
                (0, 2) | (2, 0) => 0.0,
                _ => 0.0,
            };
            ibs_sum += ibs;
            valid += 1;
        }
    }

    if valid > 0 {
        ibs_sum / (2.0 * valid as f64)
    } else {
        0.0
    }
}

/// Calculate IBS (Identity By State) matrix
#[wasm_bindgen]
pub fn calculate_ibs_matrix(genotypes: &[i32], n_samples: usize, n_markers: usize) -> Vec<f64> {
    let mut ibs = vec![0.0; n_samples * n_samples];

    for i in 0..n_samples {
        ibs[i * n_samples + i] = 1.0; // Self-comparison

        for j in (i + 1)..n_samples {
            let mut sum = 0.0;
            let mut count = 0;

            for k in 0..n_markers {
                let g1 = genotypes[i * n_markers + k];
                let g2 = genotypes[j * n_markers + k];

                if g1 >= 0 && g2 >= 0 {
                    let ibs_val = match (g1, g2) {
                        (0, 0) | (2, 2) => 2.0,
                        (0, 1) | (1, 0) | (1, 2) | (2, 1) | (1, 1) => 1.0,
                        _ => 0.0,
                    };
                    sum += ibs_val;
                    count += 1;
                }
            }

            let ibs_ij = if count > 0 { sum / (2.0 * count as f64) } else { 0.0 };
            ibs[i * n_samples + j] = ibs_ij;
            ibs[j * n_samples + i] = ibs_ij;
        }
    }

    ibs
}

/// Eigenvalue decomposition result
#[derive(Serialize, Deserialize)]
pub struct EigenResult {
    pub eigenvalues: Vec<f64>,
    pub explained_variance: Vec<f64>,
    pub cumulative_variance: Vec<f64>,
}

/// Calculate eigenvalues of a symmetric matrix (power iteration method)
/// Returns top k eigenvalues
#[wasm_bindgen]
pub fn calculate_eigenvalues(matrix: &[f64], n: usize, k: usize) -> JsValue {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let mut eigenvalues = Vec::with_capacity(k);
    let mut deflated = matrix.to_vec();
    
    for _ in 0..k.min(n) {
        // Initialize random vector
        let mut v: Vec<f64> = (0..n).map(|_| rng.gen::<f64>() - 0.5).collect();
        let mut norm: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
        for x in &mut v {
            *x /= norm;
        }

        // Power iteration
        for _ in 0..100 {
            // Matrix-vector multiplication
            let mut av = vec![0.0; n];
            for i in 0..n {
                for j in 0..n {
                    av[i] += deflated[i * n + j] * v[j];
                }
            }

            // Normalize
            norm = av.iter().map(|x| x * x).sum::<f64>().sqrt();
            if norm < 1e-10 {
                break;
            }
            for i in 0..n {
                v[i] = av[i] / norm;
            }
        }

        // Eigenvalue = v' * A * v
        let mut av = vec![0.0; n];
        for i in 0..n {
            for j in 0..n {
                av[i] += deflated[i * n + j] * v[j];
            }
        }
        let eigenvalue: f64 = v.iter().zip(av.iter()).map(|(a, b)| a * b).sum();
        eigenvalues.push(eigenvalue.abs());

        // Deflate matrix: A = A - λ * v * v'
        for i in 0..n {
            for j in 0..n {
                deflated[i * n + j] -= eigenvalue * v[i] * v[j];
            }
        }
    }

    // Calculate explained variance
    let total: f64 = eigenvalues.iter().sum();
    let explained: Vec<f64> = eigenvalues.iter().map(|e| e / total * 100.0).collect();
    let mut cumulative = Vec::with_capacity(k);
    let mut cum = 0.0;
    for e in &explained {
        cum += e;
        cumulative.push(cum);
    }

    let result = EigenResult {
        eigenvalues,
        explained_variance: explained,
        cumulative_variance: cumulative,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}
