#include <stdio.h>
#include <stdlib.h>

// Mock implementation of Fortran kernels
// These signatures must match rust/src/fortran_ffi.rs

int compute_blup(
    const double* y,
    const double* x,
    const double* z,
    const double* a_inv,
    double var_a,
    double var_e,
    double* beta,
    double* u,
    int n,
    int p,
    int q
) {
    printf("[Mock Fortran] compute_blup called (n=%d, p=%d, q=%d)\n", n, p, q);
    // Fill results with dummy values
    for(int i=0; i<p; i++) beta[i] = 1.0;
    for(int i=0; i<q; i++) u[i] = 2.0;
    return 0; // Success
}

int compute_gblup(
    const double* genotypes,
    const double* phenotypes,
    double* gebv,
    int n,
    int m,
    double h2
) {
    printf("[Mock Fortran] compute_gblup called (n=%d, m=%d, h2=%f)\n", n, m, h2);
    for(int i=0; i<n; i++) gebv[i] = phenotypes[i] * h2;
    return 0;
}

int solve_mme(
    const double* c,
    const double* rhs,
    double* solution,
    int dim,
    double tol,
    int max_iter
) {
    printf("[Mock Fortran] solve_mme called (dim=%d)\n", dim);
    for(int i=0; i<dim; i++) solution[i] = rhs[i];
    return 1; // 1 iteration
}

int compute_grm_vanraden1(
    const double* genotypes,
    double* g,
    int n,
    int m
) {
    printf("[Mock Fortran] compute_grm_vanraden1 called (n=%d, m=%d)\n", n, m);
    // Identity matrix
    for(int i=0; i<n*n; i++) g[i] = 0.0;
    for(int i=0; i<n; i++) g[i*n + i] = 1.0;
    return 0;
}

int compute_grm_vanraden2(
    const double* genotypes,
    double* g,
    int n,
    int m
) {
    printf("[Mock Fortran] compute_grm_vanraden2 called\n");
    return 0;
}

int compute_dominance_matrix(
    const double* genotypes,
    double* d,
    int n,
    int m
) {
    printf("[Mock Fortran] compute_dominance_matrix called\n");
    return 0;
}

int compute_epistatic_matrix(
    const double* g,
    double* e,
    int n
) {
    printf("[Mock Fortran] compute_epistatic_matrix called\n");
    return 0;
}

int reml_estimate(
    const double* y,
    const double* x,
    const double* z,
    const double* a,
    double var_a_init,
    double var_e_init,
    int method,
    int max_iter,
    double tol,
    double* var_a_out,
    double* var_e_out,
    int* iterations_out,
    int* converged_out,
    double* log_lik_out,
    int n,
    int p,
    int q
) {
    printf("[Mock Fortran] reml_estimate called (n=%d, p=%d, q=%d)\n", n, p, q);
    *var_a_out = var_a_init;
    *var_e_out = var_e_init;
    *iterations_out = 1;
    *converged_out = 1;
    *log_lik_out = -100.0;
    return 0;
}
