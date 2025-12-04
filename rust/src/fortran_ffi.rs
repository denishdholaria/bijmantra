//! Fortran FFI Layer
//! 
//! Safe Rust wrappers around Fortran compute kernels.
//! Provides memory-safe orchestration of high-performance numerical computations.
//!
//! Architecture Decision:
//! "Wrap Fortran in Rust: call Fortran shared libs from Rust using the C ABI.
//! That gives you Rust's memory safety around orchestration + the raw speed
//! of Fortran where it matters."

use std::ffi::c_int;
use std::os::raw::c_double;

/// FFI declarations for Fortran compute kernels
#[link(name = "bijmantra_compute_c")]
extern "C" {
    /// Compute BLUP (Best Linear Unbiased Prediction)
    fn compute_blup(
        y: *const c_double,
        x: *const c_double,
        z: *const c_double,
        a_inv: *const c_double,
        var_a: c_double,
        var_e: c_double,
        beta: *mut c_double,
        u: *mut c_double,
        n: c_int,
        p: c_int,
        q: c_int,
    ) -> c_int;

    /// Compute GBLUP (Genomic BLUP)
    fn compute_gblup(
        genotypes: *const c_double,
        phenotypes: *const c_double,
        gebv: *mut c_double,
        n: c_int,
        m: c_int,
        h2: c_double,
    ) -> c_int;

    /// Solve Mixed Model Equations using PCG
    fn solve_mme(
        c: *const c_double,
        rhs: *const c_double,
        solution: *mut c_double,
        dim: c_int,
        tol: c_double,
        max_iter: c_int,
    ) -> c_int;

    /// Compute Genomic Relationship Matrix (VanRaden Method 1)
    fn compute_grm_vanraden1(
        genotypes: *const c_double,
        g: *mut c_double,
        n: c_int,
        m: c_int,
    ) -> c_int;

    /// Compute Genomic Relationship Matrix (VanRaden Method 2)
    fn compute_grm_vanraden2(
        genotypes: *const c_double,
        g: *mut c_double,
        n: c_int,
        m: c_int,
    ) -> c_int;

    /// Compute Dominance Relationship Matrix
    fn compute_dominance_matrix(
        genotypes: *const c_double,
        d: *mut c_double,
        n: c_int,
        m: c_int,
    ) -> c_int;

    /// Compute Epistatic Relationship Matrix
    fn compute_epistatic_matrix(
        g: *const c_double,
        e: *mut c_double,
        n: c_int,
    ) -> c_int;
}

/// Error types for Fortran computations
#[derive(Debug, Clone, PartialEq)]
pub enum ComputeError {
    /// Matrix inversion failed
    MatrixInversionFailed,
    /// Linear system solve failed
    SolveFailure,
    /// Convergence not achieved
    ConvergenceFailure { iterations: i32 },
    /// Invalid input dimensions
    InvalidDimensions,
    /// Memory allocation failed
    AllocationError,
    /// Unknown error
    Unknown(i32),
}

impl std::fmt::Display for ComputeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ComputeError::MatrixInversionFailed => write!(f, "Matrix inversion failed"),
            ComputeError::SolveFailure => write!(f, "Linear system solve failed"),
            ComputeError::ConvergenceFailure { iterations } => {
                write!(f, "Convergence not achieved after {} iterations", iterations)
            }
            ComputeError::InvalidDimensions => write!(f, "Invalid input dimensions"),
            ComputeError::AllocationError => write!(f, "Memory allocation failed"),
            ComputeError::Unknown(code) => write!(f, "Unknown error (code: {})", code),
        }
    }
}

impl std::error::Error for ComputeError {}

/// Result type for Fortran computations
pub type ComputeResult<T> = Result<T, ComputeError>;

/// BLUP computation result
#[derive(Debug, Clone)]
pub struct BlupResult {
    /// Fixed effects estimates
    pub beta: Vec<f64>,
    /// Random effects (breeding values)
    pub breeding_values: Vec<f64>,
}

/// Safe wrapper for BLUP computation
/// 
/// # Arguments
/// * `phenotypes` - Phenotypic observations (n x 1)
/// * `fixed_effects` - Fixed effects design matrix (n x p)
/// * `random_effects` - Random effects design matrix (n x q)
/// * `a_inverse` - Inverse of relationship matrix (q x q)
/// * `var_additive` - Additive genetic variance
/// * `var_residual` - Residual variance
/// 
/// # Returns
/// * `BlupResult` containing fixed effects and breeding values
pub fn blup(
    phenotypes: &[f64],
    fixed_effects: &[f64],
    random_effects: &[f64],
    a_inverse: &[f64],
    var_additive: f64,
    var_residual: f64,
    n: usize,
    p: usize,
    q: usize,
) -> ComputeResult<BlupResult> {
    // Validate dimensions
    if phenotypes.len() != n {
        return Err(ComputeError::InvalidDimensions);
    }
    if fixed_effects.len() != n * p {
        return Err(ComputeError::InvalidDimensions);
    }
    if random_effects.len() != n * q {
        return Err(ComputeError::InvalidDimensions);
    }
    if a_inverse.len() != q * q {
        return Err(ComputeError::InvalidDimensions);
    }

    let mut beta = vec![0.0; p];
    let mut u = vec![0.0; q];

    let status = unsafe {
        compute_blup(
            phenotypes.as_ptr(),
            fixed_effects.as_ptr(),
            random_effects.as_ptr(),
            a_inverse.as_ptr(),
            var_additive,
            var_residual,
            beta.as_mut_ptr(),
            u.as_mut_ptr(),
            n as c_int,
            p as c_int,
            q as c_int,
        )
    };

    match status {
        0 => Ok(BlupResult {
            beta,
            breeding_values: u,
        }),
        -1 => Err(ComputeError::MatrixInversionFailed),
        code => Err(ComputeError::Unknown(code)),
    }
}

/// Safe wrapper for GBLUP computation
/// 
/// # Arguments
/// * `genotypes` - Marker genotype matrix (n x m), coded as 0, 1, 2
/// * `phenotypes` - Phenotypic observations (n x 1)
/// * `heritability` - Heritability estimate (0-1)
/// * `n` - Number of individuals
/// * `m` - Number of markers
/// 
/// # Returns
/// * Vector of Genomic Estimated Breeding Values (GEBVs)
pub fn gblup(
    genotypes: &[f64],
    phenotypes: &[f64],
    heritability: f64,
    n: usize,
    m: usize,
) -> ComputeResult<Vec<f64>> {
    // Validate dimensions
    if genotypes.len() != n * m {
        return Err(ComputeError::InvalidDimensions);
    }
    if phenotypes.len() != n {
        return Err(ComputeError::InvalidDimensions);
    }
    if heritability <= 0.0 || heritability >= 1.0 {
        return Err(ComputeError::InvalidDimensions);
    }

    let mut gebv = vec![0.0; n];

    let status = unsafe {
        compute_gblup(
            genotypes.as_ptr(),
            phenotypes.as_ptr(),
            gebv.as_mut_ptr(),
            n as c_int,
            m as c_int,
            heritability,
        )
    };

    match status {
        0 => Ok(gebv),
        -1 => Err(ComputeError::MatrixInversionFailed),
        -2 => Err(ComputeError::SolveFailure),
        code => Err(ComputeError::Unknown(code)),
    }
}

/// Genomic Relationship Matrix computation methods
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum GrmMethod {
    /// VanRaden Method 1 (2008)
    VanRaden1,
    /// VanRaden Method 2 (2008)
    VanRaden2,
}

/// Safe wrapper for Genomic Relationship Matrix computation
/// 
/// # Arguments
/// * `genotypes` - Marker genotype matrix (n x m), coded as 0, 1, 2
/// * `method` - GRM computation method
/// * `n` - Number of individuals
/// * `m` - Number of markers
/// 
/// # Returns
/// * Genomic relationship matrix (n x n) in row-major order
pub fn compute_grm(
    genotypes: &[f64],
    method: GrmMethod,
    n: usize,
    m: usize,
) -> ComputeResult<Vec<f64>> {
    if genotypes.len() != n * m {
        return Err(ComputeError::InvalidDimensions);
    }

    let mut g = vec![0.0; n * n];

    let status = unsafe {
        match method {
            GrmMethod::VanRaden1 => {
                compute_grm_vanraden1(genotypes.as_ptr(), g.as_mut_ptr(), n as c_int, m as c_int)
            }
            GrmMethod::VanRaden2 => {
                compute_grm_vanraden2(genotypes.as_ptr(), g.as_mut_ptr(), n as c_int, m as c_int)
            }
        }
    };

    match status {
        0 => Ok(g),
        code => Err(ComputeError::Unknown(code)),
    }
}

/// Safe wrapper for Dominance Relationship Matrix computation
pub fn compute_dominance(genotypes: &[f64], n: usize, m: usize) -> ComputeResult<Vec<f64>> {
    if genotypes.len() != n * m {
        return Err(ComputeError::InvalidDimensions);
    }

    let mut d = vec![0.0; n * n];

    let status = unsafe {
        compute_dominance_matrix(genotypes.as_ptr(), d.as_mut_ptr(), n as c_int, m as c_int)
    };

    match status {
        0 => Ok(d),
        code => Err(ComputeError::Unknown(code)),
    }
}

/// Safe wrapper for Epistatic Relationship Matrix computation
pub fn compute_epistatic(grm: &[f64], n: usize) -> ComputeResult<Vec<f64>> {
    if grm.len() != n * n {
        return Err(ComputeError::InvalidDimensions);
    }

    let mut e = vec![0.0; n * n];

    let status =
        unsafe { compute_epistatic_matrix(grm.as_ptr(), e.as_mut_ptr(), n as c_int) };

    match status {
        0 => Ok(e),
        code => Err(ComputeError::Unknown(code)),
    }
}

/// Solve Mixed Model Equations using Preconditioned Conjugate Gradient
/// 
/// # Arguments
/// * `coefficient_matrix` - Coefficient matrix (dim x dim)
/// * `rhs` - Right-hand side vector (dim x 1)
/// * `initial_guess` - Initial solution guess (dim x 1)
/// * `tolerance` - Convergence tolerance
/// * `max_iterations` - Maximum number of iterations
/// 
/// # Returns
/// * Solution vector and number of iterations
pub fn solve_mme_pcg(
    coefficient_matrix: &[f64],
    rhs: &[f64],
    initial_guess: &[f64],
    tolerance: f64,
    max_iterations: usize,
) -> ComputeResult<(Vec<f64>, usize)> {
    let dim = rhs.len();
    
    if coefficient_matrix.len() != dim * dim {
        return Err(ComputeError::InvalidDimensions);
    }
    if initial_guess.len() != dim {
        return Err(ComputeError::InvalidDimensions);
    }

    let mut solution = initial_guess.to_vec();

    let iterations = unsafe {
        solve_mme(
            coefficient_matrix.as_ptr(),
            rhs.as_ptr(),
            solution.as_mut_ptr(),
            dim as c_int,
            tolerance,
            max_iterations as c_int,
        )
    };

    if iterations < 0 {
        if iterations == -1 {
            return Err(ComputeError::SolveFailure);
        }
        return Err(ComputeError::ConvergenceFailure {
            iterations: -iterations,
        });
    }

    Ok((solution, iterations as usize))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_grm_dimensions() {
        let n = 10;
        let m = 100;
        let genotypes: Vec<f64> = (0..n * m).map(|i| (i % 3) as f64).collect();
        
        let result = compute_grm(&genotypes, GrmMethod::VanRaden1, n, m);
        assert!(result.is_ok());
        
        let grm = result.unwrap();
        assert_eq!(grm.len(), n * n);
    }

    #[test]
    fn test_invalid_dimensions() {
        let genotypes = vec![0.0; 50]; // Wrong size
        let result = compute_grm(&genotypes, GrmMethod::VanRaden1, 10, 100);
        assert!(matches!(result, Err(ComputeError::InvalidDimensions)));
    }
}
