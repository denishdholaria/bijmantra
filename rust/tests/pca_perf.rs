use bijmantra_compute::calculate_pca_impl;
use std::time::Instant;

#[test]
fn test_pca_performance() {
    let n_samples = 200;
    let n_markers = 2000;
    let mut genotypes = Vec::with_capacity(n_samples * n_markers);

    // Deterministic random generation for reproducibility
    let mut seed: i64 = 123456789;
    for _ in 0..(n_samples * n_markers) {
        seed = (1103515245 * seed + 12345) & 0x7fffffff;
        let val = seed % 3; // 0, 1, 2
        genotypes.push(val as i32);
    }

    println!(
        "Running PCA performance benchmark with {} samples and {} markers...",
        n_samples, n_markers
    );

    // Warmup & Correctness Check
    let result = calculate_pca_impl(&genotypes, n_samples, n_markers);
    assert_eq!(result.pc1.len(), n_samples);
    assert_eq!(result.pc2.len(), n_samples);
    assert_eq!(result.pc3.len(), n_samples);
    assert_eq!(result.variance_explained.len(), 3);

    let iterations = 20;
    let start = Instant::now();
    for _ in 0..iterations {
        calculate_pca_impl(&genotypes, n_samples, n_markers);
    }
    let duration = start.elapsed();

    println!("Total time for {} iterations: {:?}", iterations, duration);
    println!(
        "Average time per iteration: {:?}",
        duration / iterations as u32
    );
}
