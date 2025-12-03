use wasm_bindgen::prelude::*;

pub fn set_panic_hook() {
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    pub fn log(s: &str);
    
    #[wasm_bindgen(js_namespace = console)]
    pub fn error(s: &str);
}

#[macro_export]
macro_rules! console_log {
    ($($t:tt)*) => (crate::utils::log(&format_args!($($t)*).to_string()))
}

/// Performance timer for benchmarking
#[wasm_bindgen]
pub struct Timer {
    name: String,
    start: f64,
}

#[wasm_bindgen]
impl Timer {
    #[wasm_bindgen(constructor)]
    pub fn new(name: &str) -> Timer {
        let window = web_sys::window().expect("no global window");
        let performance = window.performance().expect("no performance");
        Timer {
            name: name.to_string(),
            start: performance.now(),
        }
    }

    pub fn elapsed(&self) -> f64 {
        let window = web_sys::window().expect("no global window");
        let performance = window.performance().expect("no performance");
        performance.now() - self.start
    }

    pub fn log_elapsed(&self) {
        log(&format!("{}: {:.2}ms", self.name, self.elapsed()));
    }
}
