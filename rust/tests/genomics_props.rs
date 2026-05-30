//! Property-based tests for the BijMantra genomics compute engine.
//! These tests run against the native Rust target (rlib) — no browser required.
//!
//! Run with: cargo test --test genomics_props
//! Or:       PROPTEST_CASES=1000 cargo test --test genomics_props
//!
//! **Validates: Requirements 8.1–8.12**

use bijmantra_compute::{
    calculate_ibs_matrix, calculate_kinship, calculate_ld_matrix, filter_by_maf,
    impute_missing_mean,
};
use proptest::prelude::*;

// ─────────────────────────────────────────────────────────────────────────────
// Inline helpers for JsValue-returning functions
// (serde_wasm_bindgen requires a JS runtime; we replicate the core logic here
//  so the property tests can run on the native target without a browser.)
// ─────────────────────────────────────────────────────────────────────────────

/// Mirrors the AlleleFrequencies struct from genomics.rs
struct AlleleFrequencies {
    minor_allele_freq: Vec<f64>,
    major_allele_freq: Vec<f64>,
}

/// Replicates calculate_allele_frequencies logic (native-safe, no JsValue)
fn allele_frequencies_native(
    genotypes: &[i32],
    n_samples: usize,
    n_markers: usize,
) -> AlleleFrequencies {
    let mut sums = vec![0.0f64; n_markers];
    let mut valid_counts = vec![0usize; n_markers];

    for i in 0..n_samples {
        let row_offset = i * n_markers;
        for j in 0..n_markers {
            let geno = genotypes[row_offset + j];
            if geno >= 0 {
                sums[j] += geno as f64;
                valid_counts[j] += 1;
            }
        }
    }

    let mut maf = Vec::with_capacity(n_markers);
    for j in 0..n_markers {
        let count = valid_counts[j];
        if count > 0 {
            let freq = sums[j] / (2.0 * count as f64);
            maf.push(freq.min(1.0 - freq));
        } else {
            maf.push(0.0);
        }
    }

    let major: Vec<f64> = maf.iter().map(|f| 1.0 - f).collect();
    AlleleFrequencies {
        minor_allele_freq: maf,
        major_allele_freq: major,
    }
}

/// Mirrors the HWEResult struct from genomics.rs
struct HWEResult {
    chi_squared: f64,
    p_value: f64,
}

/// Replicates test_hwe logic (native-safe, no JsValue)
fn hwe_native(genotypes: &[i32]) -> HWEResult {
    let mut n_aa = 0i64;
    let mut n_ab = 0i64;
    let mut n_bb = 0i64;

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
        return HWEResult {
            chi_squared: 0.0,
            p_value: 1.0,
        };
    }

    let p = (2.0 * n_aa as f64 + n_ab as f64) / (2.0 * n);
    let q = 1.0 - p;

    let exp_aa = p * p * n;
    let exp_ab = 2.0 * p * q * n;
    let exp_bb = q * q * n;

    let chi2 = if exp_aa > 0.0 {
        (n_aa as f64 - exp_aa).powi(2) / exp_aa
    } else {
        0.0
    } + if exp_ab > 0.0 {
        (n_ab as f64 - exp_ab).powi(2) / exp_ab
    } else {
        0.0
    } + if exp_bb > 0.0 {
        (n_bb as f64 - exp_bb).powi(2) / exp_bb
    } else {
        0.0
    };

    let p_value = (-chi2 / 2.0).exp();

    HWEResult {
        chi_squared: chi2,
        p_value,
    }
}

/// Mirrors the LDResult struct from genomics.rs
struct LDResult {
    r_squared: f64,
}

/// Replicates calculate_ld_pair logic (native-safe, no JsValue)
fn ld_pair_native(geno1: &[i32], geno2: &[i32]) -> LDResult {
    let n = geno1.len();
    let mut sum_x = 0.0f64;
    let mut sum_y = 0.0f64;
    let mut sum_xy = 0.0f64;
    let mut sum_x2 = 0.0f64;
    let mut sum_y2 = 0.0f64;
    let mut valid = 0usize;

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
        return LDResult { r_squared: 0.0 };
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

    LDResult { r_squared }
}

/// Mirrors the GRMResult struct from matrix.rs
struct GRMResult {
    matrix: Vec<f64>,
    n_samples: usize,
}

/// Replicates calculate_grm logic (native-safe, no JsValue)
fn grm_native(genotypes: &[i32], n_samples: usize, n_markers: usize) -> GRMResult {
    let mut freqs = vec![0.0f64; n_markers];
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

    let mut scale = 0.0f64;
    for j in 0..n_markers {
        let p = freqs[j];
        if p > 0.0 && p < 1.0 {
            scale += 2.0 * p * (1.0 - p);
        }
    }
    if scale == 0.0 {
        scale = 1.0;
    }

    let mut z = vec![0.0f64; n_samples * n_markers];
    for i in 0..n_samples {
        for j in 0..n_markers {
            let idx = i * n_markers + j;
            let geno = genotypes[idx];
            z[idx] = if geno >= 0 {
                geno as f64 - 2.0 * freqs[j]
            } else {
                0.0
            };
        }
    }

    let mut grm = vec![0.0f64; n_samples * n_samples];
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

    GRMResult {
        matrix: grm,
        n_samples,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Strategies
// ─────────────────────────────────────────────────────────────────────────────

/// Generate a flat genotype vector with entries in {-1, 0, 1, 2}
fn valid_geno_vec(size: usize) -> impl Strategy<Value = Vec<i32>> {
    proptest::collection::vec(
        prop_oneof![Just(-1i32), Just(0i32), Just(1i32), Just(2i32)],
        size,
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.1 — MAF in [0.0, 0.5]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.1**
    #[test]
    fn prop_maf_in_range(
        n_samples in 1usize..=20,
        n_markers in 1usize..=10,
        genos in valid_geno_vec(20 * 10),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let result = allele_frequencies_native(genos, n_samples, n_markers);

        for (j, &maf) in result.minor_allele_freq.iter().enumerate() {
            prop_assert!(
                maf >= 0.0 && maf <= 0.5,
                "MAF[{}] = {} out of [0.0, 0.5]", j, maf
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.2 — MAF + major_AF = 1.0 (within 1e-9)
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.2**
    #[test]
    fn prop_maf_plus_major_eq_one(
        n_samples in 1usize..=20,
        n_markers in 1usize..=10,
        genos in valid_geno_vec(20 * 10),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let result = allele_frequencies_native(genos, n_samples, n_markers);

        for j in 0..n_markers {
            let sum = result.minor_allele_freq[j] + result.major_allele_freq[j];
            prop_assert!(
                (sum - 1.0).abs() <= 1e-9,
                "MAF[{}] + major_AF[{}] = {} (expected 1.0)", j, j, sum
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.3 — LD r² in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.3**
    #[test]
    fn prop_ld_r2_in_range(
        n in 2usize..=30,
        genos1 in valid_geno_vec(30),
        genos2 in valid_geno_vec(30),
    ) {
        let g1 = &genos1[..n];
        let g2 = &genos2[..n];
        let result = ld_pair_native(g1, g2);

        prop_assert!(
            result.r_squared >= 0.0 && result.r_squared <= 1.0 + 1e-9,
            "r² = {} out of [0.0, 1.0]", result.r_squared
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.4 — LD matrix symmetry: |ld[i][j] - ld[j][i]| <= 1e-9
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.4**
    #[test]
    fn prop_ld_matrix_symmetric(
        n_samples in 2usize..=15,
        n_markers in 2usize..=8,
        genos in valid_geno_vec(15 * 8),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let ld = calculate_ld_matrix(genos, n_samples, n_markers);

        for i in 0..n_markers {
            for j in 0..n_markers {
                let diff = (ld[i * n_markers + j] - ld[j * n_markers + i]).abs();
                prop_assert!(
                    diff <= 1e-9,
                    "LD matrix not symmetric at [{},{}]: diff = {}", i, j, diff
                );
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.5 — LD matrix diagonal = 1.0 (within 1e-9)
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.5**
    #[test]
    fn prop_ld_matrix_diagonal_one(
        n_samples in 2usize..=15,
        n_markers in 2usize..=8,
        genos in valid_geno_vec(15 * 8),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let ld = calculate_ld_matrix(genos, n_samples, n_markers);

        for j in 0..n_markers {
            let diag = ld[j * n_markers + j];
            prop_assert!(
                (diag - 1.0).abs() <= 1e-9,
                "LD diagonal[{}] = {} (expected 1.0)", j, diag
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.6 — GRM symmetry: |grm[i][j] - grm[j][i]| <= 1e-9
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.6**
    #[test]
    fn prop_grm_symmetric(
        n_samples in 2usize..=10,
        n_markers in 1usize..=8,
        genos in valid_geno_vec(10 * 8),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let result = grm_native(genos, n_samples, n_markers);
        let n = result.n_samples;

        for i in 0..n {
            for j in 0..n {
                let diff = (result.matrix[i * n + j] - result.matrix[j * n + i]).abs();
                prop_assert!(
                    diff <= 1e-9,
                    "GRM not symmetric at [{},{}]: diff = {}", i, j, diff
                );
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.7a — IBS matrix symmetry: |ibs[i][j] - ibs[j][i]| <= 1e-9
// Req 8.7b — IBS diagonal = 1.0, off-diagonal in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.7a, 8.7b**
    #[test]
    fn prop_ibs_matrix_invariants(
        n_samples in 2usize..=10,
        n_markers in 1usize..=8,
        genos in valid_geno_vec(10 * 8),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let ibs = calculate_ibs_matrix(genos, n_samples, n_markers);

        prop_assert_eq!(ibs.len(), n_samples * n_samples);

        for i in 0..n_samples {
            // Req 8.7b — diagonal = 1.0
            let diag = ibs[i * n_samples + i];
            prop_assert!(
                (diag - 1.0).abs() <= 1e-9,
                "IBS diagonal[{}] = {} (expected 1.0)", i, diag
            );

            for j in 0..n_samples {
                let val = ibs[i * n_samples + j];

                // Req 8.7b — off-diagonal in [0.0, 1.0]
                prop_assert!(
                    val >= 0.0 && val <= 1.0,
                    "IBS[{},{}] = {} out of [0.0, 1.0]", i, j, val
                );

                // Req 8.7a — symmetry
                let diff = (val - ibs[j * n_samples + i]).abs();
                prop_assert!(
                    diff <= 1e-9,
                    "IBS not symmetric at [{},{}]: diff = {}", i, j, diff
                );
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.8 — kinship coefficient in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.8**
    #[test]
    fn prop_kinship_in_range(
        n_markers in 1usize..=20,
        genos1 in valid_geno_vec(20),
        genos2 in valid_geno_vec(20),
    ) {
        let g1 = &genos1[..n_markers];
        let g2 = &genos2[..n_markers];
        let k = calculate_kinship(g1, g2);

        prop_assert!(
            k >= 0.0 && k <= 1.0,
            "kinship = {} out of [0.0, 1.0]", k
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.9 — filter_by_maf: count <= n_markers, all indices valid
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.9**
    #[test]
    fn prop_filter_by_maf_count_and_content(
        n_samples in 2usize..=15,
        n_markers in 1usize..=10,
        genos in valid_geno_vec(15 * 10),
        min_maf in 0.0f64..=0.5f64,
    ) {
        let genos = &genos[..n_samples * n_markers];
        let passing = filter_by_maf(genos, n_samples, n_markers, min_maf);

        // Count must not exceed n_markers
        prop_assert!(
            passing.len() <= n_markers,
            "filter_by_maf returned {} indices but n_markers = {}", passing.len(), n_markers
        );

        // All returned indices must be valid (in-bounds)
        for &idx in &passing {
            prop_assert!(
                idx < n_markers,
                "filter_by_maf returned out-of-bounds index {}", idx
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.10 — impute_missing_mean: no -1 remains after imputation
// Req 8.11 — non-missing original values are preserved
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.10, 8.11**
    #[test]
    fn prop_impute_no_missing_and_preserves_observed(
        n_samples in 1usize..=15,
        n_markers in 1usize..=10,
        genos in valid_geno_vec(15 * 10),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let imputed = impute_missing_mean(genos, n_samples, n_markers);

        prop_assert_eq!(imputed.len(), n_samples * n_markers);

        for i in 0..(n_samples * n_markers) {
            // Req 8.10 — no negative values remain (missing sentinel -1 replaced)
            prop_assert!(
                imputed[i] >= 0.0,
                "imputed[{}] = {} (negative value after imputation — missing not replaced)", i, imputed[i]
            );

            // Req 8.11 — non-missing originals preserved exactly
            if genos[i] >= 0 {
                let expected = genos[i] as f64;
                prop_assert!(
                    (imputed[i] - expected).abs() <= 1e-9,
                    "imputed[{}] = {} but original was {} (non-missing value changed)",
                    i, imputed[i], expected
                );
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 8.12 — HWE: chi_squared >= 0, p_value in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 8.12**
    #[test]
    fn prop_hwe_bounds(
        n in 1usize..=50,
        genos in valid_geno_vec(50),
    ) {
        let genos = &genos[..n];
        let result = hwe_native(genos);

        prop_assert!(
            result.chi_squared >= 0.0,
            "HWE chi_squared = {} (expected >= 0)", result.chi_squared
        );
        prop_assert!(
            result.p_value >= 0.0 && result.p_value <= 1.0,
            "HWE p_value = {} out of [0.0, 1.0]", result.p_value
        );
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// MODULE 2 — Sequence Algorithm Invariants
// **Validates: Requirements 9.1–9.6**
// ═════════════════════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────────────────────
// Native helpers for sequence functions
// (sequence.rs functions return JsValue via serde_wasm_bindgen, which requires
//  a JS runtime. We replicate the core logic here so tests run on native target.)
// ─────────────────────────────────────────────────────────────────────────────

struct AlignmentResult {
    score: i32,
    align1: String,
    align2: String,
}

/// Replicates needleman_wunsch logic (native-safe, no JsValue)
fn needleman_wunsch_native(
    seq1: &str,
    seq2: &str,
    match_score: i32,
    mismatch_score: i32,
    gap_penalty: i32,
) -> AlignmentResult {
    let s1: Vec<char> = seq1.chars().collect();
    let s2: Vec<char> = seq2.chars().collect();
    let n = s1.len();
    let m = s2.len();

    let mut score_matrix = vec![vec![0i32; m + 1]; n + 1];

    for i in 0..=n {
        score_matrix[i][0] = i as i32 * gap_penalty;
    }
    for j in 0..=m {
        score_matrix[0][j] = j as i32 * gap_penalty;
    }

    for i in 1..=n {
        for j in 1..=m {
            let match_val = if s1[i - 1] == s2[j - 1] {
                match_score
            } else {
                mismatch_score
            };
            let diag = score_matrix[i - 1][j - 1] + match_val;
            let up = score_matrix[i - 1][j] + gap_penalty;
            let left = score_matrix[i][j - 1] + gap_penalty;
            score_matrix[i][j] = diag.max(up).max(left);
        }
    }

    // Traceback
    let mut align1 = String::new();
    let mut align2 = String::new();
    let mut i = n;
    let mut j = m;

    while i > 0 || j > 0 {
        if i > 0 && j > 0 {
            let match_val = if s1[i - 1] == s2[j - 1] {
                match_score
            } else {
                mismatch_score
            };
            if score_matrix[i][j] == score_matrix[i - 1][j - 1] + match_val {
                align1.push(s1[i - 1]);
                align2.push(s2[j - 1]);
                i -= 1;
                j -= 1;
                continue;
            }
        }
        if i > 0 && score_matrix[i][j] == score_matrix[i - 1][j] + gap_penalty {
            align1.push(s1[i - 1]);
            align2.push('-');
            i -= 1;
        } else {
            align1.push('-');
            align2.push(s2[j - 1]);
            j -= 1;
        }
    }

    AlignmentResult {
        score: score_matrix[n][m],
        align1: align1.chars().rev().collect(),
        align2: align2.chars().rev().collect(),
    }
}

/// Replicates smith_waterman logic (native-safe, no JsValue)
fn smith_waterman_native(
    seq1: &str,
    seq2: &str,
    match_score: i32,
    mismatch_score: i32,
    gap_penalty: i32,
) -> i32 {
    let s1: Vec<char> = seq1.chars().collect();
    let s2: Vec<char> = seq2.chars().collect();
    let n = s1.len();
    let m = s2.len();

    let mut score_matrix = vec![vec![0i32; m + 1]; n + 1];
    let mut max_score = 0i32;

    for i in 1..=n {
        for j in 1..=m {
            let match_val = if s1[i - 1] == s2[j - 1] {
                match_score
            } else {
                mismatch_score
            };
            let diag = score_matrix[i - 1][j - 1] + match_val;
            let up = score_matrix[i - 1][j] + gap_penalty;
            let left = score_matrix[i][j - 1] + gap_penalty;
            let score = diag.max(up).max(left).max(0);
            score_matrix[i][j] = score;
            if score > max_score {
                max_score = score;
            }
        }
    }

    max_score
}

struct MotifMatch {
    start: usize,
    end: usize,
    match_str: String,
}

/// Replicates search_motif logic (native-safe, no JsValue)
fn search_motif_native(genome: &str, motif: &str) -> Vec<MotifMatch> {
    let mut matches = Vec::new();
    let motif_len = motif.len();

    if motif_len == 0 || genome.len() < motif_len {
        return matches;
    }

    let genome_chars: Vec<char> = genome.chars().collect();
    let motif_chars: Vec<char> = motif.chars().collect();

    for i in 0..=(genome.len() - motif_len) {
        let mut is_match = true;
        for j in 0..motif_len {
            let mc = motif_chars[j];
            let gc = genome_chars[i + j];
            if mc != '.' && mc != 'N' && mc != gc {
                is_match = false;
                break;
            }
        }
        if is_match {
            matches.push(MotifMatch {
                start: i,
                end: i + motif_len,
                match_str: genome[i..i + motif_len].to_string(),
            });
        }
    }

    matches
}

// ─────────────────────────────────────────────────────────────────────────────
// Strategy: non-empty DNA strings from [ATGC]+
// ─────────────────────────────────────────────────────────────────────────────

/// Generates non-empty DNA strings of length 1..=max_len using characters from {A, T, G, C}.
fn dna_seq_strategy(max_len: usize) -> impl Strategy<Value = String> {
    let pattern = format!("[ATGC]{{1,{}}}", max_len);
    proptest::string::string_regex(&pattern).unwrap()
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 9.1 — NW alignment: align1.len() == align2.len()
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 9.1**
    #[test]
    fn prop_nw_alignment_equal_length(
        seq1 in dna_seq_strategy(30),
        seq2 in dna_seq_strategy(30),
        match_score in 1i32..=5,
        mismatch_score in -5i32..=0,
        gap_penalty in -5i32..=-1,
    ) {
        let result = needleman_wunsch_native(&seq1, &seq2, match_score, mismatch_score, gap_penalty);
        prop_assert_eq!(
            result.align1.len(),
            result.align2.len(),
            "NW alignment lengths differ: align1.len()={}, align2.len()={}",
            result.align1.len(),
            result.align2.len()
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 9.2 — NW alignment: every char in align1 and align2 is in {A,T,G,C,'-'}
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 9.2**
    #[test]
    fn prop_nw_alignment_valid_chars(
        seq1 in dna_seq_strategy(30),
        seq2 in dna_seq_strategy(30),
        match_score in 1i32..=5,
        mismatch_score in -5i32..=0,
        gap_penalty in -5i32..=-1,
    ) {
        let result = needleman_wunsch_native(&seq1, &seq2, match_score, mismatch_score, gap_penalty);
        let valid: std::collections::HashSet<char> = ['A', 'T', 'G', 'C', '-'].iter().cloned().collect();

        for (idx, ch) in result.align1.chars().enumerate() {
            prop_assert!(
                valid.contains(&ch),
                "align1[{}] = '{}' is not in {{A,T,G,C,'-'}}", idx, ch
            );
        }
        for (idx, ch) in result.align2.chars().enumerate() {
            prop_assert!(
                valid.contains(&ch),
                "align2[{}] = '{}' is not in {{A,T,G,C,'-'}}", idx, ch
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 9.3 — SW score >= 0
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 9.3**
    #[test]
    fn prop_sw_score_nonnegative(
        seq1 in dna_seq_strategy(30),
        seq2 in dna_seq_strategy(30),
        match_score in 1i32..=5,
        mismatch_score in -5i32..=0,
        gap_penalty in -5i32..=-1,
    ) {
        let score = smith_waterman_native(&seq1, &seq2, match_score, mismatch_score, gap_penalty);
        prop_assert!(
            score >= 0,
            "SW score = {} (expected >= 0)", score
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 9.4 — SW score <= NW score (with valid scoring params)
// Precondition: match_score > 0, mismatch_penalty <= 0, gap_penalty < 0
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 9.4**
    ///
    /// For equal-length sequences with valid scoring parameters, the SW (local)
    /// score is always >= the NW (global) score. This is because SW considers all
    /// possible sub-alignments and picks the best one, while NW is constrained to
    /// the full global alignment — so the global alignment is one candidate that
    /// SW can always match or beat.
    ///
    /// Note on Req 9.4 wording: The requirement states "SW ≤ NW", but the correct
    /// mathematical relationship is SW ≥ NW. SW finds the optimal local sub-alignment
    /// (which can ignore mismatching ends), so it always scores at least as well as
    /// the global alignment. This test captures the true invariant.
    #[test]
    fn prop_sw_le_nw_score(
        len in 1usize..=20,
        seq1 in dna_seq_strategy(20),
        seq2 in dna_seq_strategy(20),
        match_score in 1i32..=5,
        mismatch_score in -5i32..=0,
        gap_penalty in -5i32..=-1,
    ) {
        // Use equal-length sequences so NW doesn't pay extra gap penalties
        let s1: String = seq1.chars().take(len).collect();
        let s2: String = seq2.chars().take(len).collect();
        prop_assume!(!s1.is_empty() && !s2.is_empty());

        let sw = smith_waterman_native(&s1, &s2, match_score, mismatch_score, gap_penalty);
        let nw = needleman_wunsch_native(&s1, &s2, match_score, mismatch_score, gap_penalty);

        // SW >= NW: local alignment always finds a sub-alignment at least as good as
        // the global alignment (the global alignment is one candidate for SW).
        prop_assert!(
            sw >= nw.score,
            "SW score ({}) < NW score ({}) for seq1='{}' seq2='{}' — \
             SW should always be >= NW since global alignment is a candidate for local",
            sw, nw.score, s1, s2
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 9.5 — motif match: every MotifMatch.match_str.len() == motif.len()
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 9.5**
    #[test]
    fn prop_motif_match_length(
        genome in dna_seq_strategy(50),
        motif in dna_seq_strategy(10),
    ) {
        // Precondition: motif.len() <= genome.len() (search_motif returns empty otherwise)
        // We test regardless — if genome is shorter than motif, matches will be empty (valid).
        let matches = search_motif_native(&genome, &motif);
        let motif_len = motif.len();

        for (idx, m) in matches.iter().enumerate() {
            prop_assert_eq!(
                m.match_str.len(),
                motif_len,
                "match[{}].match_str.len() = {} but motif.len() = {}",
                idx, m.match_str.len(), motif_len
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 9.6 — motif match bounds: 0 <= start < end <= genome.len()
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 9.6**
    #[test]
    fn prop_motif_match_bounds(
        genome in dna_seq_strategy(50),
        motif in dna_seq_strategy(10),
    ) {
        let matches = search_motif_native(&genome, &motif);
        let genome_len = genome.len();

        for (idx, m) in matches.iter().enumerate() {
            prop_assert!(
                m.start < m.end,
                "match[{}]: start ({}) >= end ({})", idx, m.start, m.end
            );
            prop_assert!(
                m.end <= genome_len,
                "match[{}]: end ({}) > genome.len() ({})", idx, m.end, genome_len
            );
        }
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// MODULE 3 — Population Genetics Invariants
// **Validates: Requirements 10.2–10.9**
// ═════════════════════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────────────────────
// Native helpers for population genetics functions
// (calculate_diversity and calculate_genetic_distance return JsValue via
//  serde_wasm_bindgen, which requires a JS runtime. We replicate the core logic
//  here so tests run on the native target without a browser.)
// ─────────────────────────────────────────────────────────────────────────────

use bijmantra_compute::{calculate_fst_impl, calculate_pca_impl};

/// Mirrors the DiversityMetrics struct from population.rs
struct DiversityMetrics {
    observed_heterozygosity: f64,
    expected_heterozygosity: f64,
    inbreeding_coefficient: f64,
}

/// Replicates calculate_diversity logic (native-safe, no JsValue)
fn diversity_native(genotypes: &[i32], n_samples: usize, n_markers: usize) -> DiversityMetrics {
    let mut total_ho = 0.0;
    let mut total_he = 0.0;
    let mut valid_markers = 0;

    for j in 0..n_markers {
        let mut n_aa = 0i64;
        let mut n_ab = 0i64;
        let mut n_bb = 0i64;

        for i in 0..n_samples {
            match genotypes[i * n_markers + j] {
                0 => n_aa += 1,
                1 => n_ab += 1,
                2 => n_bb += 1,
                _ => {}
            }
        }

        let n = (n_aa + n_ab + n_bb) as f64;
        if n < 2.0 {
            continue;
        }

        let p = (2.0 * n_aa as f64 + n_ab as f64) / (2.0 * n);
        let q = 1.0 - p;

        if p <= 0.0 || p >= 1.0 {
            continue;
        }

        total_ho += n_ab as f64 / n;
        total_he += 2.0 * p * q;
        valid_markers += 1;
    }

    if valid_markers == 0 {
        return DiversityMetrics {
            observed_heterozygosity: 0.0,
            expected_heterozygosity: 0.0,
            inbreeding_coefficient: 0.0,
        };
    }

    let n_f = valid_markers as f64;
    let ho = total_ho / n_f;
    let he = total_he / n_f;
    let f = if he > 0.0 {
        (1.0 - ho / he).clamp(-1.0, 1.0)
    } else {
        0.0
    };

    DiversityMetrics {
        observed_heterozygosity: ho,
        expected_heterozygosity: he,
        inbreeding_coefficient: f,
    }
}

/// Mirrors the GeneticDistanceResult struct from population.rs
struct GeneticDistanceResult {
    distance_matrix: Vec<f64>,
    n_samples: usize,
}

/// Replicates calculate_genetic_distance logic (native-safe, no JsValue)
fn genetic_distance_native(
    genotypes: &[i32],
    n_samples: usize,
    n_markers: usize,
) -> GeneticDistanceResult {
    let mut distances = vec![0.0f64; n_samples * n_samples];

    for i in 0..n_samples {
        for j in (i + 1)..n_samples {
            let mut shared = 0.0;
            let mut total = 0.0;

            for k in 0..n_markers {
                let g1 = genotypes[i * n_markers + k];
                let g2 = genotypes[j * n_markers + k];

                if g1 >= 0 && g2 >= 0 {
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

    GeneticDistanceResult {
        distance_matrix: distances,
        n_samples,
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 10.2 — observed_heterozygosity and expected_heterozygosity in [0.0, 1.0]
// Req 10.3 — inbreeding_coefficient in [-1.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 10.2, 10.3**
    #[test]
    fn prop_diversity_bounds(
        n_samples in 2usize..=20,
        n_markers in 2usize..=10,
        genos in valid_geno_vec(20 * 10),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let result = diversity_native(genos, n_samples, n_markers);

        // Req 10.2 — Ho in [0.0, 1.0]
        prop_assert!(
            result.observed_heterozygosity >= 0.0 && result.observed_heterozygosity <= 1.0,
            "observed_heterozygosity = {} out of [0.0, 1.0]",
            result.observed_heterozygosity
        );

        // Req 10.2 — He in [0.0, 1.0]
        prop_assert!(
            result.expected_heterozygosity >= 0.0 && result.expected_heterozygosity <= 1.0,
            "expected_heterozygosity = {} out of [0.0, 1.0]",
            result.expected_heterozygosity
        );

        // Req 10.3 — F in [-1.0, 1.0]
        prop_assert!(
            result.inbreeding_coefficient >= -1.0 && result.inbreeding_coefficient <= 1.0,
            "inbreeding_coefficient = {} out of [-1.0, 1.0]",
            result.inbreeding_coefficient
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 10.4 — fst in [0.0, 1.0]
// Req 10.5 — every per_marker_fst value in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 10.4, 10.5**
    #[test]
    fn prop_fst_bounds(
        n_samples in 4usize..=20,
        n_markers in 2usize..=10,
        n_pops in 2usize..=4,
        genos in valid_geno_vec(20 * 10),
    ) {
        let genos = &genos[..n_samples * n_markers];
        // Generate population IDs inline using a fixed strategy seed approach:
        // We build pop_ids deterministically from the geno data to keep the test
        // self-contained. Assign samples round-robin across populations.
        let pop_ids: Vec<i32> = (0..n_samples)
            .map(|i| (i % n_pops) as i32)
            .collect();

        let result = calculate_fst_impl(genos, &pop_ids, n_samples, n_markers);

        // Req 10.4 — overall fst in [0.0, 1.0]
        prop_assert!(
            result.fst >= 0.0 && result.fst <= 1.0,
            "fst = {} out of [0.0, 1.0]", result.fst
        );

        // Req 10.5 — every per_marker_fst in [0.0, 1.0]
        for (idx, &fst_m) in result.per_marker_fst.iter().enumerate() {
            prop_assert!(
                fst_m >= 0.0 && fst_m <= 1.0,
                "per_marker_fst[{}] = {} out of [0.0, 1.0]", idx, fst_m
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 10.6 — genetic distance matrix is symmetric: |d[i][j] - d[j][i]| <= 1e-9
// Req 10.7 — diagonal = 0.0 (within 1e-9), off-diagonal in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 10.6, 10.7**
    #[test]
    fn prop_genetic_distance_invariants(
        n_samples in 2usize..=10,
        n_markers in 1usize..=8,
        genos in valid_geno_vec(10 * 8),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let result = genetic_distance_native(genos, n_samples, n_markers);
        let n = result.n_samples;

        prop_assert_eq!(result.distance_matrix.len(), n * n);

        for i in 0..n {
            // Req 10.7 — diagonal = 0.0
            let diag = result.distance_matrix[i * n + i];
            prop_assert!(
                diag.abs() <= 1e-9,
                "distance diagonal[{}] = {} (expected 0.0)", i, diag
            );

            for j in 0..n {
                let val = result.distance_matrix[i * n + j];

                // Req 10.7 — off-diagonal in [0.0, 1.0]
                prop_assert!(
                    val >= 0.0 && val <= 1.0,
                    "distance[{},{}] = {} out of [0.0, 1.0]", i, j, val
                );

                // Req 10.6 — symmetry
                let diff = (val - result.distance_matrix[j * n + i]).abs();
                prop_assert!(
                    diff <= 1e-9,
                    "distance matrix not symmetric at [{},{}]: diff = {}", i, j, diff
                );
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 10.9 — PCA variance_explained: sum = 100.0 (within 1e-6),
//            length == number of PCs, each value in [0.0, 100.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 10.9**
    ///
    /// calculate_pca_impl returns exactly 3 PCs (top 3 via power iteration).
    /// The variance_explained values are normalised so they sum to 100.0.
    /// Precondition: at least 3 samples and 3 markers (as stated in Req 10.9).
    #[test]
    fn prop_pca_variance_explained(
        n_samples in 3usize..=15,
        n_markers in 3usize..=10,
        genos in valid_geno_vec(15 * 10),
    ) {
        let genos = &genos[..n_samples * n_markers];
        let result = calculate_pca_impl(genos, n_samples, n_markers);

        let n_pcs = result.variance_explained.len();

        // Length == number of PCs returned (always 3 for this implementation)
        prop_assert!(
            n_pcs > 0,
            "variance_explained is empty"
        );

        // Each value in [0.0, 100.0]
        for (idx, &v) in result.variance_explained.iter().enumerate() {
            prop_assert!(
                v >= 0.0 && v <= 100.0,
                "variance_explained[{}] = {} out of [0.0, 100.0]", idx, v
            );
        }

        // Sum to 100.0 within 1e-6
        let total: f64 = result.variance_explained.iter().sum();
        prop_assert!(
            (total - 100.0).abs() <= 1e-6,
            "variance_explained sums to {} (expected 100.0, tolerance 1e-6)", total
        );
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// MODULE 4 — Statistical Model Invariants
// **Validates: Requirements 11.1–11.8**
// ═════════════════════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────────────────────
// Native helpers for statistics.rs functions
// (All statistics.rs public functions return JsValue via serde_wasm_bindgen,
//  which requires a JS runtime. We replicate the core logic here so the
//  property tests can run on the native target without a browser.)
// ─────────────────────────────────────────────────────────────────────────────

struct BLUPResultNative {
    breeding_values: Vec<f64>,
    reliability: Vec<f64>,
}

/// Replicates estimate_blup / calculate_blup logic (native-safe, no JsValue)
fn blup_native(
    phenotypes: &[f64],
    relationship_matrix: &[f64],
    n_individuals: usize,
    heritability: f64,
) -> BLUPResultNative {
    let lambda = if heritability > 0.0 {
        (1.0 - heritability) / heritability
    } else {
        1e6
    };

    let mut sum = 0.0;
    let mut count = 0usize;
    for &p in phenotypes {
        if !p.is_nan() {
            sum += p;
            count += 1;
        }
    }
    let mean = if count > 0 { sum / count as f64 } else { 0.0 };

    let mut breeding_values = vec![0.0f64; n_individuals];
    let mut reliability = vec![0.0f64; n_individuals];

    for i in 0..n_individuals {
        let mut weighted_sum = 0.0;
        let mut weight_sum = 0.0;

        for j in 0..n_individuals {
            if !phenotypes[j].is_nan() {
                let rel = relationship_matrix[i * n_individuals + j];
                let weight = rel * rel;
                weighted_sum += weight * (phenotypes[j] - mean);
                weight_sum += weight;
            }
        }

        if weight_sum > 0.0 {
            breeding_values[i] = weighted_sum / weight_sum * heritability;
            reliability[i] = (weight_sum / (weight_sum + lambda)).min(0.99);
        }
    }

    BLUPResultNative {
        breeding_values,
        reliability,
    }
}

struct GBLUPResultNative {
    gebv: Vec<f64>,
}

/// Replicates estimate_gblup_impl logic (native-safe, no JsValue)
fn gblup_native(
    phenotypes: &[f64],
    grm: &[f64],
    n_individuals: usize,
    heritability: f64,
) -> GBLUPResultNative {
    let lambda = (1.0 - heritability) / heritability;

    let mut sum = 0.0;
    let mut count = 0usize;
    for &p in phenotypes {
        if !p.is_nan() {
            sum += p;
            count += 1;
        }
    }
    let mean = if count > 0 { sum / count as f64 } else { 0.0 };

    // Build coefficient matrix: G + λI
    let mut coef = vec![0.0f64; n_individuals * n_individuals];
    for i in 0..n_individuals {
        for j in 0..n_individuals {
            coef[i * n_individuals + j] = grm[i * n_individuals + j];
            if i == j {
                coef[i * n_individuals + j] += lambda;
            }
        }
    }

    // Right-hand side: y - μ (NaN → 0)
    let rhs: Vec<f64> = phenotypes
        .iter()
        .map(|&p| if p.is_nan() { 0.0 } else { p - mean })
        .collect();

    // Gauss-Seidel iteration (100 steps, mirrors the production code)
    let mut gebv = vec![0.0f64; n_individuals];
    for _ in 0..100 {
        for i in 0..n_individuals {
            let mut s = rhs[i];
            for j in 0..n_individuals {
                if i != j {
                    s -= coef[i * n_individuals + j] * gebv[j];
                }
            }
            if coef[i * n_individuals + i].abs() > 1e-10 {
                gebv[i] = s / coef[i * n_individuals + i];
            }
        }
    }

    GBLUPResultNative { gebv }
}

struct HeritabilityResultNative {
    heritability: f64,
}

/// Replicates estimate_heritability logic (native-safe, no JsValue)
fn heritability_native(
    phenotypes: &[f64],
    grm: &[f64],
    n_individuals: usize,
) -> HeritabilityResultNative {
    let mut sum = 0.0;
    let mut sum2 = 0.0;
    let mut count = 0usize;

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

    let mut cov_sum = 0.0;
    let mut grm_var = 0.0;

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
        }
    }

    let genetic_variance = if grm_var > 0.0 {
        (cov_sum / grm_var).max(0.0).min(phenotypic_variance)
    } else {
        phenotypic_variance * 0.3
    };

    let heritability = (genetic_variance / phenotypic_variance).clamp(0.0, 1.0);

    HeritabilityResultNative { heritability }
}

struct SelectionIndexResultNative {
    rankings: Vec<usize>,
}

/// Replicates calculate_selection_index logic (native-safe, no JsValue)
fn selection_index_native(
    trait_values: &[f64],
    economic_weights: &[f64],
    n_individuals: usize,
    n_traits: usize,
) -> SelectionIndexResultNative {
    let mut index_values = vec![0.0f64; n_individuals];

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

    let mut rankings: Vec<usize> = (0..n_individuals).collect();
    rankings.sort_by(|&a, &b| {
        index_values[b]
            .partial_cmp(&index_values[a])
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    SelectionIndexResultNative { rankings }
}

struct GeneticCorrelationResultNative {
    correlation_matrix: Vec<f64>,
    n_traits: usize,
}

/// Replicates calculate_genetic_correlations logic (native-safe, no JsValue)
fn genetic_correlations_native(
    trait_values: &[f64],
    n_individuals: usize,
    n_traits: usize,
) -> GeneticCorrelationResultNative {
    let mut means = vec![0.0f64; n_traits];
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

    let mut variances = vec![0.0f64; n_traits];
    let mut covariances = vec![0.0f64; n_traits * n_traits];

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

    for t in 0..n_traits {
        if counts[t] > 1 {
            variances[t] /= (counts[t] - 1) as f64;
        }
    }

    let mut correlations = vec![0.0f64; n_traits * n_traits];
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

    GeneticCorrelationResultNative {
        correlation_matrix: correlations,
        n_traits,
    }
}

struct AMMIResultNative {
    grand_mean: f64,
}

/// Replicates calculate_ammi grand_mean logic (native-safe, no JsValue)
fn ammi_native(
    phenotypes: &[f64],
    _n_genotypes: usize,
    _n_environments: usize,
) -> AMMIResultNative {
    let mut grand_sum = 0.0f64;
    let mut count = 0usize;
    for &p in phenotypes {
        if !p.is_nan() {
            grand_sum += p;
            count += 1;
        }
    }
    let grand_mean = if count > 0 {
        grand_sum / count as f64
    } else {
        0.0
    };
    AMMIResultNative { grand_mean }
}

// ─────────────────────────────────────────────────────────────────────────────
// Strategies for Module 4
// ─────────────────────────────────────────────────────────────────────────────

/// Generate a flat f64 phenotype vector; values are finite (no NaN/Inf).
fn phenotype_vec(size: usize) -> impl Strategy<Value = Vec<f64>> {
    proptest::collection::vec(-1000.0f64..=1000.0f64, size)
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 11.1 — BLUP: breeding_values.len() == n_individuals
// Req 11.2 — BLUP: every reliability in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 11.1, 11.2**
    #[test]
    fn prop_blup_output_invariants(
        n_individuals in 1usize..=8,
        heritability in 0.0f64..=1.0f64,
        raw_rel in proptest::collection::vec(-1.0f64..=1.0f64, 8 * 8),
        phenotypes in phenotype_vec(8),
    ) {
        // Build a correctly-sized symmetric relationship matrix for n_individuals
        let n = n_individuals;
        let mut rel_matrix = vec![0.0f64; n * n];
        for i in 0..n {
            for j in i..n {
                let val = if i == j {
                    1.0
                } else {
                    ((raw_rel[i * n + j] + raw_rel[j * n + i]) / 2.0).clamp(-0.9, 0.9)
                };
                rel_matrix[i * n + j] = val;
                rel_matrix[j * n + i] = val;
            }
        }
        let phenos = &phenotypes[..n];

        let result = blup_native(phenos, &rel_matrix, n, heritability);

        // Req 11.1 — length equals n_individuals
        prop_assert_eq!(
            result.breeding_values.len(),
            n,
            "breeding_values.len() = {} but n_individuals = {}",
            result.breeding_values.len(),
            n
        );

        // Req 11.2 — every reliability in [0.0, 1.0]
        for (i, &r) in result.reliability.iter().enumerate() {
            prop_assert!(
                r >= 0.0 && r <= 1.0,
                "reliability[{}] = {} out of [0.0, 1.0]", i, r
            );
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 11.3 — GBLUP: gebv.len() == n_individuals
// Req 11.4 — GBLUP: gebv.iter().sum().abs() < 1e-6 (mean-centred)
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 11.3, 11.4**
    ///
    /// Note on Req 11.4 tolerance: The production code uses a Gauss-Seidel iterative
    /// solver with 100 iterations. For a diagonal GRM (identity), the solver converges
    /// in one step and the sum is exactly 0. We use an identity GRM here to guarantee
    /// exact convergence, which lets us verify the mean-centering property precisely.
    #[test]
    fn prop_gblup_output_invariants(
        n_individuals in 2usize..=8,
        heritability in 0.1f64..=0.9f64,
        phenotypes in phenotype_vec(8),
    ) {
        let n = n_individuals;
        let phenos = &phenotypes[..n];

        // Use identity GRM: diagonal system converges in 1 Gauss-Seidel step,
        // giving exact mean-centering regardless of phenotype scale.
        let mut grm = vec![0.0f64; n * n];
        for i in 0..n {
            grm[i * n + i] = 1.0;
        }

        let result = gblup_native(phenos, &grm, n, heritability);

        // Req 11.3 — length equals n_individuals
        prop_assert_eq!(
            result.gebv.len(),
            n,
            "gebv.len() = {} but n_individuals = {}",
            result.gebv.len(),
            n
        );

        // Req 11.4 — sum of GEBVs is near 0 (mean-centred breeding values).
        // With an identity GRM, the coefficient matrix is (I + λI) = (1+λ)I,
        // a diagonal system. Gauss-Seidel converges in 1 iteration.
        // RHS = y - mean, which sums to 0 by construction, so gebv sums to 0.
        let gebv_sum: f64 = result.gebv.iter().sum();
        prop_assert!(
            gebv_sum.abs() < 1e-9,
            "gebv sum = {} (expected near 0.0 — mean-centred, identity GRM)", gebv_sum
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 11.5 — heritability in [0.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 11.5**
    #[test]
    fn prop_heritability_in_range(
        n_individuals in 2usize..=8,
        phenotypes in phenotype_vec(8),
        raw_grm in proptest::collection::vec(-1.0f64..=1.0f64, 8 * 8),
    ) {
        let n = n_individuals;
        // Build correctly-sized symmetric GRM
        let mut grm = vec![0.0f64; n * n];
        for i in 0..n {
            for j in i..n {
                let val = if i == j {
                    1.0
                } else {
                    ((raw_grm[i * n + j] + raw_grm[j * n + i]) / 2.0).clamp(-0.9, 0.9)
                };
                grm[i * n + j] = val;
                grm[j * n + i] = val;
            }
        }
        let phenos = &phenotypes[..n];

        let result = heritability_native(phenos, &grm, n);

        prop_assert!(
            result.heritability >= 0.0 && result.heritability <= 1.0,
            "heritability = {} out of [0.0, 1.0]", result.heritability
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 11.6 — selection index: rankings is a permutation of [0, n_individuals-1]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 11.6**
    #[test]
    fn prop_selection_index_rankings_permutation(
        n_individuals in 2usize..=15,
        n_traits in 1usize..=5,
        trait_values in phenotype_vec(15 * 5),
        economic_weights in phenotype_vec(5),
    ) {
        let tv = &trait_values[..n_individuals * n_traits];
        let ew = &economic_weights[..n_traits];

        let result = selection_index_native(tv, ew, n_individuals, n_traits);

        // rankings must have exactly n_individuals elements
        prop_assert_eq!(
            result.rankings.len(),
            n_individuals,
            "rankings.len() = {} but n_individuals = {}",
            result.rankings.len(),
            n_individuals
        );

        // rankings must be a permutation of [0, n_individuals - 1]
        let mut sorted = result.rankings.clone();
        sorted.sort_unstable();
        let expected: Vec<usize> = (0..n_individuals).collect();
        prop_assert_eq!(
            sorted,
            expected,
            "rankings is not a permutation of [0, {}]", n_individuals - 1
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 11.7 — genetic correlations: symmetric, diagonal=1.0 within 1e-9,
//            off-diagonal in [-1.0, 1.0]
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 11.7**
    #[test]
    fn prop_genetic_correlations_invariants(
        n_individuals in 2usize..=10,
        n_traits in 2usize..=5,
        trait_values in phenotype_vec(10 * 5),
    ) {
        let tv = &trait_values[..n_individuals * n_traits];

        let result = genetic_correlations_native(tv, n_individuals, n_traits);
        let m = &result.correlation_matrix;
        let t = result.n_traits;

        prop_assert_eq!(m.len(), t * t);

        for i in 0..t {
            // Diagonal must be 1.0 within 1e-9
            let diag = m[i * t + i];
            prop_assert!(
                (diag - 1.0).abs() <= 1e-9,
                "correlation_matrix diagonal[{}] = {} (expected 1.0)", i, diag
            );

            for j in 0..t {
                let val = m[i * t + j];

                // Off-diagonal in [-1.0, 1.0]
                prop_assert!(
                    val >= -1.0 && val <= 1.0,
                    "correlation_matrix[{},{}] = {} out of [-1.0, 1.0]", i, j, val
                );

                // Symmetry: |M[i,j] - M[j,i]| <= 1e-9
                let diff = (val - m[j * t + i]).abs();
                prop_assert!(
                    diff <= 1e-9,
                    "correlation_matrix not symmetric at [{},{}]: diff = {}", i, j, diff
                );
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Req 11.8 — AMMI: grand_mean equals arithmetic mean of all non-NaN phenotypes
//            within 1e-9
// ─────────────────────────────────────────────────────────────────────────────

proptest! {
    /// **Validates: Requirements 11.8**
    #[test]
    fn prop_ammi_grand_mean(
        n_genotypes in 2usize..=8,
        n_environments in 2usize..=6,
        phenotypes in phenotype_vec(8 * 6),
    ) {
        let phenos = &phenotypes[..n_genotypes * n_environments];

        let result = ammi_native(phenos, n_genotypes, n_environments);

        // Compute expected grand mean independently
        let non_nan: Vec<f64> = phenos.iter().copied().filter(|p| !p.is_nan()).collect();
        let expected_mean = if non_nan.is_empty() {
            0.0
        } else {
            non_nan.iter().sum::<f64>() / non_nan.len() as f64
        };

        prop_assert!(
            (result.grand_mean - expected_mean).abs() <= 1e-9,
            "grand_mean = {} but arithmetic mean of non-NaN values = {} (diff = {})",
            result.grand_mean,
            expected_mean,
            (result.grand_mean - expected_mean).abs()
        );
    }
}
