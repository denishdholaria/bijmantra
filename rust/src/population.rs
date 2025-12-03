//! Population genetics functions
//! Diversity metrics, population structure, and genetic distance

use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};

/// Diversity metrics result
#[derive(Serialize, Deserialize)]
pub struct DiversityMetrics {
    pub shannon_index: f64,
    pub simpson_index: f64,
    pub nei_diversity: f64,
    pub observed_heterozygosity: f64,
    pub expected_heterozygosity: f64,
    pub inbreeding_coefficient: f64,
    pub effective_alleles: f64,
}

/// Calculate genetic diversity metrics
#[wasm_bindgen]
pub fn calculate_diversity(genotypes: &[i32], n_samples: usize, n_markers: usize) -> JsValue {
    let mut total_ho = 0.0;
    let mut total_he = 0.0;
    let mut total_shannon = 0.0;
    let mut total_simpson = 0.0;
    let mut total_nei = 0.0;
    let mut valid_markers = 0;

    for j in 0..n_markers {
        let mut n_aa = 0;
        let mut n_ab = 0;
        let mut n_bb = 0;

        for i in 0..n_samples {
            match genotypes[i * n_markers + j] {
                0 => n_aa += 1,
                1 => n_ab += 1,
                2 => n_bb += 1,
                _ => {}
            }
        }

        let n = (n_aa + n_ab + n_bb) as f64;
        if n < 2.0 { continue; }

        // Allele frequencies
        let p = (2.0 * n_aa as f64 + n_ab as f64) / (2.0 * n);
        let q = 1.0 - p;

        if p <= 0.0 || p >= 1.0 { continue; }

        // Observed heterozygosity
        let ho = n_ab as f64 / n;
        total_ho += ho;

        // Expected heterozygosity (Nei's gene diversity)
        let he = 2.0 * p * q;
        total_he += he;

        // Shannon index: -Σ(p * ln(p))
        let shannon = -(p * p.ln() + q * q.ln());
        total_shannon += shannon;

        // Simpson index: 1 - Σ(p²)
        let simpson = 1.0 - (p * p + q * q);
        total_simpson += simpson;

        // Nei's diversity
        total_nei += he * n / (n - 1.0);

        valid_markers += 1;
    }

    if valid_markers == 0 {
        return serde_wasm_bindgen::to_value(&DiversityMetrics {
            shannon_index: 0.0,
            simpson_index: 0.0,
            nei_diversity: 0.0,
            observed_heterozygosity: 0.0,
            expected_heterozygosity: 0.0,
            inbreeding_coefficient: 0.0,
            effective_alleles: 1.0,
        }).unwrap();
    }

    let n_markers_f = valid_markers as f64;
    let ho = total_ho / n_markers_f;
    let he = total_he / n_markers_f;
    
    // Inbreeding coefficient: F = 1 - Ho/He
    let f = if he > 0.0 { 1.0 - ho / he } else { 0.0 };

    // Effective number of alleles: Ne = 1 / (1 - He)
    let ne = if he < 1.0 { 1.0 / (1.0 - he) } else { 2.0 };

    let result = DiversityMetrics {
        shannon_index: total_shannon / n_markers_f,
        simpson_index: total_simpson / n_markers_f,
        nei_diversity: total_nei / n_markers_f,
        observed_heterozygosity: ho,
        expected_heterozygosity: he,
        inbreeding_coefficient: f.max(-1.0).min(1.0),
        effective_alleles: ne,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Fst (fixation index) result
#[derive(Serialize, Deserialize)]
pub struct FstResult {
    pub fst: f64,
    pub fis: f64,
    pub fit: f64,
    pub per_marker_fst: Vec<f64>,
}

/// Calculate Fst between populations
#[wasm_bindgen]
pub fn calculate_fst(
    genotypes: &[i32],
    population_ids: &[i32],
    n_samples: usize,
    n_markers: usize,
) -> JsValue {
    // Find unique populations
    let mut pops: Vec<i32> = population_ids.iter().cloned().collect();
    pops.sort();
    pops.dedup();
    let n_pops = pops.len();

    if n_pops < 2 {
        return serde_wasm_bindgen::to_value(&FstResult {
            fst: 0.0,
            fis: 0.0,
            fit: 0.0,
            per_marker_fst: vec![],
        }).unwrap();
    }

    let mut per_marker_fst = Vec::with_capacity(n_markers);
    let mut total_hs = 0.0;
    let mut total_ht = 0.0;
    let mut valid_markers = 0;

    for j in 0..n_markers {
        // Calculate allele frequencies per population
        let mut pop_freqs = vec![0.0; n_pops];
        let mut pop_counts = vec![0usize; n_pops];
        let mut pop_het = vec![0.0; n_pops];

        for i in 0..n_samples {
            let geno = genotypes[i * n_markers + j];
            if geno < 0 { continue; }

            let pop_idx = pops.iter().position(|&p| p == population_ids[i]).unwrap();
            pop_freqs[pop_idx] += geno as f64;
            pop_counts[pop_idx] += 1;
            if geno == 1 {
                pop_het[pop_idx] += 1.0;
            }
        }

        // Convert to frequencies
        let mut valid_pops = 0;
        for k in 0..n_pops {
            if pop_counts[k] > 0 {
                pop_freqs[k] /= 2.0 * pop_counts[k] as f64;
                pop_het[k] /= pop_counts[k] as f64;
                valid_pops += 1;
            }
        }

        if valid_pops < 2 { continue; }

        // Calculate Hs (within-population heterozygosity)
        let mut hs = 0.0;
        let mut total_n = 0;
        for k in 0..n_pops {
            if pop_counts[k] > 0 {
                let p = pop_freqs[k];
                hs += 2.0 * p * (1.0 - p) * pop_counts[k] as f64;
                total_n += pop_counts[k];
            }
        }
        hs /= total_n as f64;

        // Calculate Ht (total heterozygosity)
        let mut p_total = 0.0;
        for k in 0..n_pops {
            if pop_counts[k] > 0 {
                p_total += pop_freqs[k] * pop_counts[k] as f64;
            }
        }
        p_total /= total_n as f64;
        let ht = 2.0 * p_total * (1.0 - p_total);

        // Fst for this marker
        let fst_marker = if ht > 0.0 { (ht - hs) / ht } else { 0.0 };
        per_marker_fst.push(fst_marker.max(0.0).min(1.0));

        total_hs += hs;
        total_ht += ht;
        valid_markers += 1;
    }

    let fst = if total_ht > 0.0 {
        ((total_ht - total_hs) / total_ht).max(0.0).min(1.0)
    } else {
        0.0
    };

    let result = FstResult {
        fst,
        fis: 0.0, // Would need individual-level calculation
        fit: fst, // Simplified
        per_marker_fst,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// Genetic distance result
#[derive(Serialize, Deserialize)]
pub struct GeneticDistanceResult {
    pub distance_matrix: Vec<f64>,
    pub n_samples: usize,
    pub method: String,
}

/// Calculate pairwise genetic distances (Nei's distance)
#[wasm_bindgen]
pub fn calculate_genetic_distance(
    genotypes: &[i32],
    n_samples: usize,
    n_markers: usize,
) -> JsValue {
    let mut distances = vec![0.0; n_samples * n_samples];

    for i in 0..n_samples {
        for j in (i + 1)..n_samples {
            let mut shared = 0.0;
            let mut total = 0.0;

            for k in 0..n_markers {
                let g1 = genotypes[i * n_markers + k];
                let g2 = genotypes[j * n_markers + k];

                if g1 >= 0 && g2 >= 0 {
                    // Modified Rogers distance
                    let diff = (g1 - g2).abs() as f64;
                    shared += 1.0 - diff / 2.0;
                    total += 1.0;
                }
            }

            let dist = if total > 0.0 {
                1.0 - shared / total
            } else {
                1.0
            };

            distances[i * n_samples + j] = dist;
            distances[j * n_samples + i] = dist;
        }
    }

    let result = GeneticDistanceResult {
        distance_matrix: distances,
        n_samples,
        method: "Modified Rogers".to_string(),
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// PCA result
#[derive(Serialize, Deserialize)]
pub struct PCAResult {
    pub pc1: Vec<f64>,
    pub pc2: Vec<f64>,
    pub pc3: Vec<f64>,
    pub variance_explained: Vec<f64>,
}

/// Perform PCA on genotype matrix
#[wasm_bindgen]
pub fn calculate_pca(genotypes: &[i32], n_samples: usize, n_markers: usize) -> JsValue {
    // Center and scale genotypes
    let mut centered = vec![0.0; n_samples * n_markers];
    
    for j in 0..n_markers {
        let mut sum = 0.0;
        let mut sum2 = 0.0;
        let mut count = 0;

        for i in 0..n_samples {
            let geno = genotypes[i * n_markers + j];
            if geno >= 0 {
                sum += geno as f64;
                sum2 += (geno as f64).powi(2);
                count += 1;
            }
        }

        let mean = if count > 0 { sum / count as f64 } else { 0.0 };
        let std = if count > 1 {
            ((sum2 - sum * sum / count as f64) / (count - 1) as f64).sqrt()
        } else {
            1.0
        };

        for i in 0..n_samples {
            let idx = i * n_markers + j;
            let geno = genotypes[idx];
            centered[idx] = if geno >= 0 && std > 0.0 {
                (geno as f64 - mean) / std
            } else {
                0.0
            };
        }
    }

    // Calculate covariance matrix (samples x samples)
    let mut cov = vec![0.0; n_samples * n_samples];
    for i in 0..n_samples {
        for j in i..n_samples {
            let mut sum = 0.0;
            for k in 0..n_markers {
                sum += centered[i * n_markers + k] * centered[j * n_markers + k];
            }
            let c = sum / n_markers as f64;
            cov[i * n_samples + j] = c;
            cov[j * n_samples + i] = c;
        }
    }

    // Power iteration for top 3 PCs
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let mut pcs = vec![vec![0.0; n_samples]; 3];
    let mut variances = vec![0.0; 3];
    let mut deflated = cov.clone();

    for pc in 0..3 {
        // Initialize random vector
        let mut v: Vec<f64> = (0..n_samples).map(|_| rng.gen::<f64>() - 0.5).collect();
        let mut norm: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
        for x in &mut v {
            *x /= norm;
        }

        // Power iteration
        for _ in 0..50 {
            let mut av = vec![0.0; n_samples];
            for i in 0..n_samples {
                for j in 0..n_samples {
                    av[i] += deflated[i * n_samples + j] * v[j];
                }
            }

            norm = av.iter().map(|x| x * x).sum::<f64>().sqrt();
            if norm < 1e-10 { break; }
            
            for i in 0..n_samples {
                v[i] = av[i] / norm;
            }
        }

        // Store PC
        pcs[pc] = v.clone();
        variances[pc] = norm;

        // Deflate
        for i in 0..n_samples {
            for j in 0..n_samples {
                deflated[i * n_samples + j] -= norm * v[i] * v[j];
            }
        }
    }

    // Calculate variance explained
    let total_var: f64 = variances.iter().sum();
    let var_explained: Vec<f64> = variances.iter()
        .map(|v| if total_var > 0.0 { v / total_var * 100.0 } else { 0.0 })
        .collect();

    let result = PCAResult {
        pc1: pcs[0].clone(),
        pc2: pcs[1].clone(),
        pc3: pcs[2].clone(),
        variance_explained: var_explained,
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}

/// AMMI (Additive Main effects and Multiplicative Interaction) result
#[derive(Serialize, Deserialize)]
pub struct AMMIResult {
    pub genotype_means: Vec<f64>,
    pub environment_means: Vec<f64>,
    pub grand_mean: f64,
    pub ipca1_genotype: Vec<f64>,
    pub ipca1_environment: Vec<f64>,
    pub ipca1_variance: f64,
}

/// Calculate AMMI analysis for G×E interaction
#[wasm_bindgen]
pub fn calculate_ammi(
    phenotypes: &[f64],  // n_genotypes * n_environments
    n_genotypes: usize,
    n_environments: usize,
) -> JsValue {
    // Calculate means
    let mut geno_means = vec![0.0; n_genotypes];
    let mut env_means = vec![0.0; n_environments];
    let mut grand_sum = 0.0;
    let mut count = 0;

    for g in 0..n_genotypes {
        let mut sum = 0.0;
        let mut n = 0;
        for e in 0..n_environments {
            let val = phenotypes[g * n_environments + e];
            if !val.is_nan() {
                sum += val;
                n += 1;
            }
        }
        geno_means[g] = if n > 0 { sum / n as f64 } else { 0.0 };
    }

    for e in 0..n_environments {
        let mut sum = 0.0;
        let mut n = 0;
        for g in 0..n_genotypes {
            let val = phenotypes[g * n_environments + e];
            if !val.is_nan() {
                sum += val;
                n += 1;
            }
        }
        env_means[e] = if n > 0 { sum / n as f64 } else { 0.0 };
    }

    for &p in phenotypes {
        if !p.is_nan() {
            grand_sum += p;
            count += 1;
        }
    }
    let grand_mean = if count > 0 { grand_sum / count as f64 } else { 0.0 };

    // Calculate interaction matrix
    let mut interaction = vec![0.0; n_genotypes * n_environments];
    for g in 0..n_genotypes {
        for e in 0..n_environments {
            let val = phenotypes[g * n_environments + e];
            if !val.is_nan() {
                interaction[g * n_environments + e] = val - geno_means[g] - env_means[e] + grand_mean;
            }
        }
    }

    // Simple SVD approximation for first IPCA
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    // Initialize vectors
    let mut u: Vec<f64> = (0..n_genotypes).map(|_| rng.gen::<f64>() - 0.5).collect();
    let mut v: Vec<f64> = (0..n_environments).map(|_| rng.gen::<f64>() - 0.5).collect();

    // Power iteration
    for _ in 0..50 {
        // v = I' * u
        for e in 0..n_environments {
            v[e] = 0.0;
            for g in 0..n_genotypes {
                v[e] += interaction[g * n_environments + e] * u[g];
            }
        }
        let norm_v: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm_v > 0.0 {
            for x in &mut v { *x /= norm_v; }
        }

        // u = I * v
        for g in 0..n_genotypes {
            u[g] = 0.0;
            for e in 0..n_environments {
                u[g] += interaction[g * n_environments + e] * v[e];
            }
        }
        let norm_u: f64 = u.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm_u > 0.0 {
            for x in &mut u { *x /= norm_u; }
        }
    }

    // Calculate singular value
    let mut sv = 0.0;
    for g in 0..n_genotypes {
        for e in 0..n_environments {
            sv += interaction[g * n_environments + e] * u[g] * v[e];
        }
    }

    let result = AMMIResult {
        genotype_means: geno_means,
        environment_means: env_means,
        grand_mean,
        ipca1_genotype: u,
        ipca1_environment: v,
        ipca1_variance: sv.abs(),
    };

    serde_wasm_bindgen::to_value(&result).unwrap()
}
