fn main() {
    // Only link for native builds, not WASM
    let target_arch = std::env::var("CARGO_CFG_TARGET_ARCH").unwrap_or_default();
    if target_arch != "wasm32" {
        // Compile the mock Fortran (C) code
        cc::Build::new()
            .file("mock_fortran.c")
            .compile("bijmantra_compute_c");

        // Ensure rebuild if the C file changes
        println!("cargo:rerun-if-changed=mock_fortran.c");
    }
}
