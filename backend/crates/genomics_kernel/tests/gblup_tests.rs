use genomics_kernel::calculate_g_matrix;

#[test]
fn calculate_g_matrix_matches_expected() {
    let n_markers = 2;
    let n_individuals = 2;
    let markers = vec![
        0_u8, 2_u8, // individual 0
        1_u8, 1_u8, // individual 1
    ];

    let result = calculate_g_matrix(&markers, n_markers, n_individuals);
    assert_eq!(result.len(), n_individuals * n_individuals);

    let expected = vec![0.6666667_f32, -0.6666667_f32, -0.6666667_f32, 0.6666667_f32];
    for (value, exp) in result.iter().zip(expected.iter()) {
        assert!((value - exp).abs() < 1e-5);
    }
}

#[test]
fn calculate_g_matrix_empty_inputs() {
    let result = calculate_g_matrix(&[], 0, 0);
    assert!(result.is_empty());
}

#[test]
fn calculate_g_matrix_fixed_markers_returns_zero_matrix() {
    let n_markers = 2;
    let n_individuals = 2;
    let markers = vec![
        0_u8, 0_u8, // individual 0
        0_u8, 0_u8, // individual 1
    ];

    let result = calculate_g_matrix(&markers, n_markers, n_individuals);
    assert_eq!(result, vec![0.0_f32; n_individuals * n_individuals]);
}

#[test]
fn calculate_g_matrix_invalid_length_returns_empty() {
    let markers = vec![0_u8, 1_u8, 2_u8];
    let result = calculate_g_matrix(&markers, 2, 2);
    assert!(result.is_empty());
}

#[test]
fn calculate_g_matrix_ignores_invalid_genotypes() {
    let n_markers = 2;
    let n_individuals = 2;
    let markers = vec![
        0_u8, 2_u8,   // individual 0
        255_u8, 1_u8, // individual 1 (invalid genotype in marker 0)
    ];

    let result = calculate_g_matrix(&markers, n_markers, n_individuals);
    let expected = vec![0.6666667_f32, -0.6666667_f32, -0.6666667_f32, 0.6666667_f32];
    for (value, exp) in result.iter().zip(expected.iter()) {
        assert!((value - exp).abs() < 1e-5);
    }
}
