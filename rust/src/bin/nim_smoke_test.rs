//! Rust NIM smoke test binary.
//!
//! Build and run:
//!   cargo build --features native-http --bin nim_smoke_test
//!   BIJMANTRA_NIM_PROXY_URL=http://localhost:8000/api/v2/nim/chat \
//!     cargo run --features native-http --bin nim_smoke_test
//!
//! The binary calls the BijMantra backend proxy (which holds NVIDIA_API_KEY).
//! Set BIJMANTRA_AUTH_TOKEN if the backend requires authentication.

#[cfg(not(all(not(target_arch = "wasm32"), feature = "native-http")))]
fn main() {
    eprintln!(
        "This binary requires the `native-http` feature and a non-WASM target.\n\
         Build with: cargo build --features native-http --bin nim_smoke_test"
    );
    std::process::exit(1);
}

#[cfg(all(not(target_arch = "wasm32"), feature = "native-http"))]
#[tokio::main]
async fn main() {
    use bijmantra_compute::nim_client::smoke_test;

    println!("=== NVIDIA NIM Rust Smoke Test ===");
    println!("Proxy: {}", std::env::var("BIJMANTRA_NIM_PROXY_URL")
        .unwrap_or_else(|_| "http://localhost:8000/api/v2/nim/chat".to_string()));

    match smoke_test().await {
        Ok(true) => {
            println!("✓ Smoke test passed.");
            std::process::exit(0);
        }
        Ok(false) => {
            eprintln!("✗ Smoke test returned unexpected result.");
            std::process::exit(1);
        }
        Err(e) => {
            eprintln!("✗ Smoke test failed: {e}");
            std::process::exit(1);
        }
    }
}
