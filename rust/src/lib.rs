mod utils;
mod genomics;
mod statistics;
mod matrix;
mod population;

// Fortran FFI layer (for native builds, not WASM)
#[cfg(not(target_arch = "wasm32"))]
pub mod fortran_ffi;

// Python bindings (only when python feature is enabled)
#[cfg(feature = "python")]
mod python_bindings;

use wasm_bindgen::prelude::*;

// Initialize panic hook for better error messages
#[wasm_bindgen(start)]
pub fn start() {
    utils::set_panic_hook();
}

// Re-export all public functions
pub use genomics::*;
pub use statistics::*;
pub use matrix::*;
pub use population::*;

/// Get library version
#[wasm_bindgen]
pub fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// Check if WASM module is loaded
#[wasm_bindgen]
pub fn is_wasm_ready() -> bool {
    true
}

// Python module definition
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn bijmantra_compute(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(python_bindings::blup, m)?)?;
    m.add_function(wrap_pyfunction!(python_bindings::gblup, m)?)?;
    m.add_function(wrap_pyfunction!(python_bindings::compute_grm, m)?)?;
    Ok(())
}
