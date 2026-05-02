denish@Mac bijmantraorg % cd rust && cargo update

    Updating crates.io index
     Locking 24 packages to latest compatible versions
    Updating cc v1.2.58 -> v1.2.60
      Adding getrandom v0.3.4
    Updating js-sys v0.3.93 -> v0.3.95
    Updating libc v0.2.183 -> v0.2.185
    Updating pyo3 v0.28.2 -> v0.28.3
    Updating pyo3-build-config v0.28.2 -> v0.28.3
    Updating pyo3-ffi v0.28.2 -> v0.28.3
    Updating pyo3-macros v0.28.2 -> v0.28.3
    Updating pyo3-macros-backend v0.28.2 -> v0.28.3
      Adding r-efi v5.3.0
      Adding rand v0.9.4 (available: v0.10.1)
      Adding rand_chacha v0.9.0
      Adding rand_core v0.9.5
      Adding wasip2 v1.0.2+wasi-0.2.9
    Updating wasm-bindgen v0.2.116 -> v0.2.118
    Updating wasm-bindgen-futures v0.4.66 -> v0.4.68
    Updating wasm-bindgen-macro v0.2.116 -> v0.2.118
    Updating wasm-bindgen-macro-support v0.2.116 -> v0.2.118
    Updating wasm-bindgen-shared v0.2.116 -> v0.2.118
    Updating wasm-bindgen-test v0.3.66 -> v0.3.68
    Updating wasm-bindgen-test-macro v0.3.66 -> v0.3.68
    Updating wasm-bindgen-test-shared v0.2.116 -> v0.2.118
    Updating web-sys v0.3.93 -> v0.3.95
      Adding wit-bindgen v0.51.0
note: pass`--verbose` to see 1 unchanged dependencies behind latest
denish@Mac rust % cargo build
  Downloaded wasm-bindgen-shared v0.2.118
  Downloaded cc v1.2.60
  Downloaded wasm-bindgen-macro v0.2.118
  Downloaded wasm-bindgen-macro-support v0.2.118
  Downloaded js-sys v0.3.95
  Downloaded wasm-bindgen v0.2.118
  Downloaded rand v0.9.4
  Downloaded web-sys v0.3.95
  Downloaded libc v0.2.185
  Downloaded 9 crates (1.8MiB) in 3.51s
   Compiling cfg-if v1.0.4
   Compiling libc v0.2.185
   Compiling unicode-ident v1.0.24
   Compiling wasm-bindgen-shared v0.2.118
   Compiling libm v0.2.16
   Compiling zerocopy v0.8.48
   Compiling wasm-bindgen v0.2.118
   Compiling once_cell v1.21.4
   Compiling getrandom v0.3.4
   Compiling proc-macro2 v1.0.106
   Compiling bytemuck v1.25.0
   Compiling rawpointer v0.2.1
   Compiling serde_core v1.0.228
   Compiling matrixmultiply v0.3.10
   Compiling safe_arch v0.7.4
   Compiling wide v0.7.33
   Compiling quote v1.0.45
   Compiling syn v2.0.117
   Compiling cc v1.2.60
   Compiling typenum v1.19.0
   Compiling zmij v1.0.21
   Compiling memchr v2.8.0
   Compiling itoa v1.0.18
   Compiling bijmantra-genomics v1.0.0-beta.1 (/Users/denish/Documents/bpro/bijmantraorg/rust)
   Compiling serde_json v1.0.149
   Compiling num-traits v0.2.19
   Compiling num-integer v0.1.46
   Compiling num-complex v0.4.6
   Compiling approx v0.5.1
   Compiling num-rational v0.4.2
   Compiling simba v0.9.1
   Compiling ndarray v0.17.2
   Compiling wasm-bindgen-macro-support v0.2.118
   Compiling getrandom v0.2.17
   Compiling rand_core v0.6.4
   Compiling rand_core v0.9.5
   Compiling serde_derive v1.0.228
   Compiling ppv-lite86 v0.2.21
   Compiling rand_chacha v0.3.1
   Compiling rand_chacha v0.9.0
   Compiling rand v0.8.5
   Compiling rand v0.9.4
   Compiling wasm-bindgen-macro v0.2.118
   Compiling rand_distr v0.4.3
   Compiling serde v1.0.228
   Compiling nalgebra v0.33.3
   Compiling js-sys v0.3.95
   Compiling console_error_panic_hook v0.1.7
   Compiling serde-wasm-bindgen v0.6.5
   Compiling web-sys v0.3.95
   Compiling statrs v0.18.0
warning: use of deprecated function `rand::thread_rng`: Renamed to `rng`
   --> src/matrix.rs:238:25
    |
238 |     let mut rng = rand::thread_rng();
    |                         ^^^^^^^^^^
    |
    = note: `#[warn(deprecated)]` on by default

warning: use of deprecated function `rand::thread_rng`: Renamed to `rng`
   --> src/population.rs:363:25
    |
363 |     let mut rng = rand::thread_rng();
    |                         ^^^^^^^^^^

warning: use of deprecated function `rand::thread_rng`: Renamed to `rng`
   --> src/population.rs:512:25
    |
512 |     let mut rng = rand::thread_rng();
    |                         ^^^^^^^^^^

warning: use of deprecated method `rand::Rng::gen`: Renamed to `random` to avoid conflict with the new `gen` keyword in Rust 2024.
   --> src/matrix.rs:245:50
    |
245 |         let mut v: Vec`<f64>` = (0..n).map(|_| rng.gen::`<f64>`() - 0.5).collect();
    |                                                  ^^^

warning: use of deprecated method `rand::Rng::gen`: Renamed to `random` to avoid conflict with the new `gen` keyword in Rust 2024.
   --> src/population.rs:371:58
    |
371 |         let mut v: Vec`<f64>` = (0..n_samples).map(|_| rng.gen::`<f64>`() - 0.5).collect();
    |                                                          ^^^

warning: use of deprecated method `rand::Rng::gen`: Renamed to `random` to avoid conflict with the new `gen` keyword in Rust 2024.
   --> src/population.rs:515:56
    |
515 |     let mut u: Vec`<f64>` = (0..n_genotypes).map(|_| rng.gen::`<f64>`() - 0.5).collect();
    |                                                        ^^^

warning: use of deprecated method `rand::Rng::gen`: Renamed to `random` to avoid conflict with the new `gen` keyword in Rust 2024.
   --> src/population.rs:517:22
    |
517 |         .map(|_| rng.gen::`<f64>`() - 0.5)
    |                      ^^^

warning: `bijmantra-genomics` (lib) generated 7 warnings
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 18.98s
denish@Mac rust %
