mod utils;
mod genomics;
mod statistics;
mod matrix;
mod population;

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
