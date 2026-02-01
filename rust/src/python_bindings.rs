//! Python bindings for Bijmantra Compute
//!
//! Exposes Rust/Fortran functionality to Python via PyO3.

use pyo3::prelude::*;
use pyo3::Py;
use numpy::{IntoPyArray, PyReadonlyArray1};
use crate::fortran_ffi;

#[pyfunction]
pub fn blup(
    _py: Python<'_>,
    phenotypes: PyReadonlyArray1<f64>,
    fixed_effects: PyReadonlyArray1<f64>,
    random_effects: PyReadonlyArray1<f64>,
    a_inverse: PyReadonlyArray1<f64>,
    var_additive: f64,
    var_residual: f64,
    n: usize,
    p: usize,
    q: usize,
) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
    let phenotypes = phenotypes.as_slice()?;
    let fixed_effects = fixed_effects.as_slice()?;
    let random_effects = random_effects.as_slice()?;
    let a_inverse = a_inverse.as_slice()?;

    let result = fortran_ffi::blup(
        phenotypes,
        fixed_effects,
        random_effects,
        a_inverse,
        var_additive,
        var_residual,
        n,
        p,
        q,
    ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let beta = result.beta.into_pyarray(_py).to_owned();
    let u = result.breeding_values.into_pyarray(_py).to_owned();

    Ok((beta.into(), u.into()))
}

#[pyfunction]
pub fn gblup(
    _py: Python<'_>,
    genotypes: PyReadonlyArray1<f64>,
    phenotypes: PyReadonlyArray1<f64>,
    heritability: f64,
    n: usize,
    m: usize,
) -> PyResult<Py<PyAny>> {
    let genotypes = genotypes.as_slice()?;
    let phenotypes = phenotypes.as_slice()?;

    let gebv_vec = fortran_ffi::gblup(
        genotypes,
        phenotypes,
        heritability,
        n,
        m,
    ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(gebv_vec.into_pyarray(_py).to_owned().into())
}

#[pyfunction]
pub fn compute_grm(
    _py: Python<'_>,
    genotypes: PyReadonlyArray1<f64>,
    method: &str,
    n: usize,
    m: usize,
) -> PyResult<Py<PyAny>> {
    let genotypes = genotypes.as_slice()?;

    let method_enum = match method {
        "vanraden1" => fortran_ffi::GrmMethod::VanRaden1,
        "vanraden2" => fortran_ffi::GrmMethod::VanRaden2,
        _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid method")),
    };

    let grm_vec = fortran_ffi::compute_grm(
        genotypes,
        method_enum,
        n,
        m,
    ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok(grm_vec.into_pyarray(_py).to_owned().into())
}

#[pyfunction]
pub fn reml_estimate(
    _py: Python<'_>,
    phenotypes: PyReadonlyArray1<f64>,
    fixed_effects: PyReadonlyArray1<f64>,
    random_effects: PyReadonlyArray1<f64>,
    relationship_matrix: PyReadonlyArray1<f64>,
    var_additive_init: f64,
    var_residual_init: f64,
    method: &str,
    max_iter: usize,
    tolerance: f64,
    n: usize,
    p: usize,
    q: usize,
) -> PyResult<(f64, f64, f64, bool, i32, f64)> {
    let phenotypes = phenotypes.as_slice()?;
    let fixed_effects = fixed_effects.as_slice()?;
    let random_effects = random_effects.as_slice()?;
    let relationship_matrix = relationship_matrix.as_slice()?;

    let method_enum = match method {
        "ai-reml" => fortran_ffi::RemlMethod::AiReml,
        "em-reml" => fortran_ffi::RemlMethod::EmReml,
        _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid method")),
    };

    let result = fortran_ffi::reml_estimate(
        phenotypes,
        fixed_effects,
        random_effects,
        relationship_matrix,
        var_additive_init,
        var_residual_init,
        method_enum,
        max_iter,
        tolerance,
        n,
        p,
        q,
    ).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    Ok((
        result.var_additive,
        result.var_residual,
        result.heritability,
        result.converged,
        result.iterations,
        result.log_likelihood,
    ))
}
