//! NVIDIA NIM client for native (non-WASM) Rust contexts.
//!
//! Calls the BijMantra backend NIM proxy — **never** calls NIM directly from
//! Rust so the NVIDIA API key is never embedded in a binary or WASM module.
//!
//! # Feature gate
//! This module is only compiled when the `native-http` feature is enabled and
//! the target is not `wasm32`. It is intentionally absent from the WASM build.
//!
//! # Usage
//! ```no_run
//! use bijmantra_compute::nim_client::{NimProxyClient, NimMessage};
//!
//! #[tokio::main]
//! async fn main() -> anyhow::Result<()> {
//!     let client = NimProxyClient::from_env();
//!     let messages = vec![NimMessage::user("What is genomic selection?")];
//!     let response = client.chat(&messages).await?;
//!     println!("{}", response.content);
//!     Ok(())
//! }
//! ```

use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::env;
use std::time::Instant;

/// Default backend proxy URL for the NIM chat endpoint.
const DEFAULT_PROXY_URL: &str = "http://localhost:8000/api/v2/nim/chat";

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

/// A single chat message (mirrors the backend schema).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NimMessage {
    pub role: String,
    pub content: String,
}

impl NimMessage {
    pub fn system(content: impl Into<String>) -> Self {
        Self { role: "system".into(), content: content.into() }
    }

    pub fn user(content: impl Into<String>) -> Self {
        Self { role: "user".into(), content: content.into() }
    }

    pub fn assistant(content: impl Into<String>) -> Self {
        Self { role: "assistant".into(), content: content.into() }
    }
}

/// Request body for the backend NIM proxy.
#[derive(Debug, Serialize)]
struct NimProxyRequest<'a> {
    messages: &'a [NimMessage],
    #[serde(skip_serializing_if = "Option::is_none")]
    model: Option<&'a str>,
    max_tokens: u32,
    temperature: f32,
}

/// Response from the backend NIM proxy.
#[derive(Debug, Deserialize)]
pub struct NimProxyResponse {
    pub content: String,
    pub model: Option<String>,
    pub input_tokens: Option<u64>,
    pub output_tokens: Option<u64>,
    pub total_tokens: Option<u64>,
    pub latency_ms: f64,
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

/// Async client that calls the BijMantra backend NIM proxy.
///
/// The proxy handles authentication with NVIDIA — this client only needs a
/// valid BijMantra session token (or can be called without auth in dev mode).
pub struct NimProxyClient {
    http: Client,
    proxy_url: String,
    /// Optional Bearer token for the BijMantra backend.
    auth_token: Option<String>,
    /// Override model name (falls back to server default).
    model: Option<String>,
    max_tokens: u32,
    temperature: f32,
}

impl NimProxyClient {
    /// Construct from environment variables:
    /// - `BIJMANTRA_NIM_PROXY_URL` (default: `http://localhost:8000/api/v2/nim/chat`)
    /// - `BIJMANTRA_AUTH_TOKEN`    (optional Bearer token)
    /// - `NIM_MODEL`               (optional model override)
    pub fn from_env() -> Self {
        Self {
            http: Client::builder()
                .timeout(std::time::Duration::from_secs(60))
                .build()
                .expect("failed to build reqwest client"),
            proxy_url: env::var("BIJMANTRA_NIM_PROXY_URL")
                .unwrap_or_else(|_| DEFAULT_PROXY_URL.to_string()),
            auth_token: env::var("BIJMANTRA_AUTH_TOKEN").ok(),
            model: env::var("NIM_MODEL").ok(),
            max_tokens: 1024,
            temperature: 0.7,
        }
    }

    pub fn with_max_tokens(mut self, max_tokens: u32) -> Self {
        self.max_tokens = max_tokens;
        self
    }

    pub fn with_temperature(mut self, temperature: f32) -> Self {
        self.temperature = temperature;
        self
    }

    /// Send a blocking (non-streaming) chat request to the BijMantra NIM proxy.
    pub async fn chat(&self, messages: &[NimMessage]) -> Result<NimProxyResponse, reqwest::Error> {
        let body = NimProxyRequest {
            messages,
            model: self.model.as_deref(),
            max_tokens: self.max_tokens,
            temperature: self.temperature,
        };

        let t0 = Instant::now();
        let mut req = self.http.post(&self.proxy_url).json(&body);
        if let Some(token) = &self.auth_token {
            req = req.bearer_auth(token);
        }

        let response = req.send().await?.error_for_status()?;
        let mut parsed: NimProxyResponse = response.json().await?;
        // Patch latency with client-side measurement if backend didn't include it
        if parsed.latency_ms == 0.0 {
            parsed.latency_ms = t0.elapsed().as_secs_f64() * 1000.0;
        }
        Ok(parsed)
    }
}

// ---------------------------------------------------------------------------
// Smoke-test helpers (used by the integration test binary below)
// ---------------------------------------------------------------------------

/// Run a quick connectivity check against the NIM proxy.
/// Returns `Ok(true)` if the proxy responds, `Ok(false)` on auth/config error.
pub async fn smoke_test() -> Result<bool, reqwest::Error> {
    let client = NimProxyClient::from_env();
    let messages = vec![NimMessage::user(
        "In one word, name a staple crop grown in South Asia.",
    )];
    match client.chat(&messages).await {
        Ok(resp) => {
            println!("[NIM Rust smoke] OK  model={:?}  content={}", resp.model, resp.content.trim());
            Ok(true)
        }
        Err(e) => {
            eprintln!("[NIM Rust smoke] FAIL: {e}");
            Err(e)
        }
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    /// Unit test: verify message constructors produce the correct role strings.
    #[test]
    fn test_message_roles() {
        let system = NimMessage::system("sys");
        let user = NimMessage::user("hi");
        let assistant = NimMessage::assistant("hello");
        assert_eq!(system.role, "system");
        assert_eq!(user.role, "user");
        assert_eq!(assistant.role, "assistant");
    }

    /// Unit test: NimProxyClient::from_env falls back to the default proxy URL
    /// when BIJMANTRA_NIM_PROXY_URL is not set.
    #[test]
    fn test_default_proxy_url() {
        // Temporarily unset to verify fallback
        let saved = std::env::var("BIJMANTRA_NIM_PROXY_URL").ok();
        std::env::remove_var("BIJMANTRA_NIM_PROXY_URL");
        let client = NimProxyClient::from_env();
        assert_eq!(client.proxy_url, DEFAULT_PROXY_URL);
        if let Some(v) = saved {
            std::env::set_var("BIJMANTRA_NIM_PROXY_URL", v);
        }
    }

    /// Integration test: only runs when BIJMANTRA_NIM_PROXY_URL (or backend) is
    /// reachable. Skipped automatically in offline/sandbox environments.
    #[tokio::test]
    async fn test_smoke_integration() {
        // Skip if proxy is not configured or unreachable
        let proxy_url = std::env::var("BIJMANTRA_NIM_PROXY_URL")
            .unwrap_or_else(|_| DEFAULT_PROXY_URL.to_string());
        let check = reqwest::get(&proxy_url).await;
        if check.is_err() {
            eprintln!("[NIM Rust test] Proxy unreachable — skipping integration test");
            return;
        }
        let result = smoke_test().await;
        assert!(result.is_ok(), "NIM smoke test returned an HTTP error");
    }
}
