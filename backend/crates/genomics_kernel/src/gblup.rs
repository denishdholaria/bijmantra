#[cfg(not(target_arch = "wasm32"))]
use rayon::prelude::*;
#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

const MAX_GENOTYPE: u8 = 2;
const PLOIDY: f32 = 2.0;

/// Computes the genomic relationship (G) matrix using G = ZZ' / (2 * Σ p(1-p)).
///
/// `markers` must be a row-major flat slice of diploid genotype calls with
/// length `n_individuals * n_markers`, where each individual occupies a
/// contiguous block of `n_markers`. Valid genotype values are 0, 1, 2; values
/// greater than 2 are treated as missing and excluded from allele frequency
/// estimation and the centered Z matrix (i.e., they contribute 0.0). When the
/// scaling denominator is 0 (all fixed or missing markers), a zero matrix is
/// returned. Invalid input lengths or overflow return an empty Vec.
#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn calculate_g_matrix(markers: &[u8], n_markers: usize, n_individuals: usize) -> Vec<f32> {
    if n_markers == 0 || n_individuals == 0 {
        return Vec::new();
    }

    let expected_len = match n_markers.checked_mul(n_individuals) {
        Some(len) => len,
        None => return Vec::new(),
    };
    if markers.len() != expected_len {
        return Vec::new();
    }

    let g_len = match n_individuals.checked_mul(n_individuals) {
        Some(len) => len,
        None => return Vec::new(),
    };

    let mut freqs = vec![0.0_f32; n_markers];
    let mut counts = vec![0_u32; n_markers];

    for marker_idx in 0..n_markers {
        let mut sum = 0.0_f32;
        let mut count = 0_u32;
        for ind_idx in 0..n_individuals {
            let value = markers[ind_idx * n_markers + marker_idx];
            if value <= MAX_GENOTYPE {
                sum += value as f32;
                count += 1;
            }
        }
        if count > 0 {
            freqs[marker_idx] = sum / (PLOIDY * count as f32);
        }
        counts[marker_idx] = count;
    }

    let mut scale = 0.0_f32;
    for marker_idx in 0..n_markers {
        let p = freqs[marker_idx];
        if counts[marker_idx] > 0 && p > 0.0 && p < 1.0 {
            scale += PLOIDY * p * (1.0 - p);
        }
    }
    if scale == 0.0 {
        return vec![0.0_f32; g_len];
    }

    let mut z = vec![0.0_f32; expected_len];
    for ind_idx in 0..n_individuals {
        for marker_idx in 0..n_markers {
            let idx = ind_idx * n_markers + marker_idx;
            let geno = markers[idx];
            if geno <= MAX_GENOTYPE {
                z[idx] = geno as f32 - PLOIDY * freqs[marker_idx];
            }
        }
    }

    let mut g = vec![0.0_f32; g_len];
    #[cfg(not(target_arch = "wasm32"))]
    {
        g.par_chunks_mut(n_individuals)
            .enumerate()
            .for_each(|(i, row)| {
                for j in 0..n_individuals {
                    let mut sum = 0.0_f32;
                    let row_offset = i * n_markers;
                    let col_offset = j * n_markers;
                    for k in 0..n_markers {
                        sum += z[row_offset + k] * z[col_offset + k];
                    }
                    row[j] = sum / scale;
                }
            });
    }
    #[cfg(target_arch = "wasm32")]
    {
        for (i, row) in g.chunks_mut(n_individuals).enumerate() {
            for j in 0..n_individuals {
                let mut sum = 0.0_f32;
                let row_offset = i * n_markers;
                let col_offset = j * n_markers;
                for k in 0..n_markers {
                    sum += z[row_offset + k] * z[col_offset + k];
                }
                row[j] = sum / scale;
            }
        }
    }

    g
}
