//! WebAssembly tests for Bijmantra Genomics

#![cfg(target_arch = "wasm32")]

use wasm_bindgen_test::*;
use bijmantra_genomics::*;

wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn test_version() {
    let version = get_version();
    assert!(!version.is_empty());
}

#[wasm_bindgen_test]
fn test_wasm_ready() {
    assert!(is_wasm_ready());
}

#[wasm_bindgen_test]
fn test_allele_frequencies() {
    // 3 samples, 2 markers
    let genotypes = vec![0, 1, 1, 2, 2, 1];
    let result = calculate_allele_frequencies(&genotypes, 3, 2);
    assert!(!result.is_null());
}

#[wasm_bindgen_test]
fn test_ld_calculation() {
    let geno1 = vec![0, 1, 2, 1, 0];
    let geno2 = vec![0, 1, 2, 1, 0];
    let result = calculate_ld_pair(&geno1, &geno2);
    assert!(!result.is_null());
}

#[wasm_bindgen_test]
fn test_grm_calculation() {
    // 4 samples, 3 markers
    let genotypes = vec![
        0, 1, 2,
        1, 1, 1,
        2, 1, 0,
        1, 2, 1,
    ];
    let result = calculate_grm(&genotypes, 4, 3);
    assert!(!result.is_null());
}

#[wasm_bindgen_test]
fn test_hwe() {
    let genotypes = vec![0, 0, 1, 1, 1, 2, 2, 1, 0, 1];
    let result = test_hwe(&genotypes);
    assert!(!result.is_null());
}

#[wasm_bindgen_test]
fn test_diversity() {
    let genotypes = vec![
        0, 1, 2, 1,
        1, 1, 1, 2,
        2, 0, 1, 1,
    ];
    let result = calculate_diversity(&genotypes, 3, 4);
    assert!(!result.is_null());
}

#[wasm_bindgen_test]
fn test_pca() {
    let genotypes = vec![
        0, 1, 2, 1, 0,
        1, 1, 1, 2, 1,
        2, 0, 1, 1, 2,
        1, 2, 0, 1, 1,
    ];
    let result = calculate_pca(&genotypes, 4, 5);
    assert!(!result.is_null());
}

#[wasm_bindgen_test]
fn test_blup() {
    let phenotypes = vec![100.0, 105.0, 98.0, 102.0];
    let grm = vec![
        1.0, 0.5, 0.25, 0.1,
        0.5, 1.0, 0.3, 0.2,
        0.25, 0.3, 1.0, 0.15,
        0.1, 0.2, 0.15, 1.0,
    ];
    let result = estimate_blup(&phenotypes, &grm, 4, 0.3);
    assert!(!result.is_null());
}

#[wasm_bindgen_test]
fn test_selection_index() {
    // 3 individuals, 2 traits
    let traits = vec![
        100.0, 50.0,
        110.0, 45.0,
        95.0, 55.0,
    ];
    let weights = vec![1.0, 0.5];
    let result = calculate_selection_index(&traits, &weights, 3, 2);
    assert!(!result.is_null());
}
