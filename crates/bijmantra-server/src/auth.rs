use std::sync::{Arc, RwLock};
use std::time::{Duration, Instant};

use jsonwebtoken::jwk::JwkSet;
use jsonwebtoken::{
    Algorithm, DecodingKey, Validation, dangerous::insecure_decode, decode, decode_header,
};
use serde::Deserialize;

const DEFAULT_KEYCLOAK_ISSUER: &str = "http://localhost:8084/realms/bijmantra";
const DEFAULT_KEYCLOAK_AUDIENCE: &str = "bijmantra-api";
const DEFAULT_KEYCLOAK_JWKS_URL: &str =
    "http://localhost:8084/realms/bijmantra/protocol/openid-connect/certs";
const DEFAULT_KEYCLOAK_JWKS_CACHE_SECONDS: u64 = 300;

#[derive(Debug, Clone)]
pub struct AuthConfig {
    local_hs256_secret: Option<String>,
    keycloak: Option<KeycloakConfig>,
    jwks_cache: Arc<RwLock<Option<CachedJwks>>>,
    http_client: reqwest::Client,
}

#[derive(Debug, Clone)]
struct KeycloakConfig {
    issuer: String,
    audience: String,
    jwks_url: String,
    jwks_cache_seconds: u64,
}

#[derive(Debug, Clone)]
struct CachedJwks {
    expires_at: Instant,
    jwks: JwkSet,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AuthPrincipal {
    Local {
        user_id: i64,
        organization_id: i64,
        is_superuser: bool,
    },
    Keycloak {
        issuer: String,
        subject: String,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AuthError {
    Invalid,
    Unavailable,
    ProviderUnavailable,
}

#[derive(Debug, Deserialize)]
struct LocalAccessClaims {
    sub: String,
    organization_id: i64,
    #[serde(default)]
    is_superuser: bool,
    #[serde(rename = "exp")]
    _exp: i64,
}

#[derive(Debug, Deserialize)]
struct UntrustedIssuerClaims {
    iss: Option<String>,
}

#[derive(Debug, Deserialize)]
struct KeycloakClaims {
    sub: String,
    iss: String,
    #[serde(rename = "aud")]
    _aud: serde_json::Value,
    #[serde(rename = "exp")]
    _exp: i64,
}

impl AuthConfig {
    pub fn from_env() -> Self {
        let local_hs256_secret = std::env::var("SECRET_KEY")
            .ok()
            .map(|secret| secret.trim().to_string())
            .filter(|secret| !secret.is_empty());

        let keycloak = env_flag("KEYCLOAK_ENABLED").then(|| KeycloakConfig {
            issuer: env_or_default("KEYCLOAK_ISSUER", DEFAULT_KEYCLOAK_ISSUER),
            audience: env_or_default("KEYCLOAK_AUDIENCE", DEFAULT_KEYCLOAK_AUDIENCE),
            jwks_url: env_or_default("KEYCLOAK_JWKS_URL", DEFAULT_KEYCLOAK_JWKS_URL),
            jwks_cache_seconds: std::env::var("KEYCLOAK_JWKS_CACHE_SECONDS")
                .ok()
                .and_then(|value| value.parse().ok())
                .unwrap_or(DEFAULT_KEYCLOAK_JWKS_CACHE_SECONDS),
        });

        Self::new(local_hs256_secret, keycloak)
    }

    pub fn local_hs256(secret: impl Into<String>) -> Self {
        let secret = secret.into().trim().to_string();
        Self::new((!secret.is_empty()).then_some(secret), None)
    }

    pub fn keycloak_rs256(
        issuer: impl Into<String>,
        audience: impl Into<String>,
        jwks_url: impl Into<String>,
    ) -> Self {
        Self::new(
            None,
            Some(KeycloakConfig {
                issuer: issuer.into().trim().to_string(),
                audience: audience.into().trim().to_string(),
                jwks_url: jwks_url.into().trim().to_string(),
                jwks_cache_seconds: DEFAULT_KEYCLOAK_JWKS_CACHE_SECONDS,
            }),
        )
    }

    #[cfg(test)]
    fn keycloak_with_jwks(
        issuer: impl Into<String>,
        audience: impl Into<String>,
        jwks: JwkSet,
    ) -> Self {
        let auth = Self::keycloak_rs256(issuer, audience, "memory://keycloak-jwks");
        auth.cache_jwks(jwks, DEFAULT_KEYCLOAK_JWKS_CACHE_SECONDS);
        auth
    }

    fn new(local_hs256_secret: Option<String>, keycloak: Option<KeycloakConfig>) -> Self {
        Self {
            local_hs256_secret,
            keycloak,
            jwks_cache: Arc::new(RwLock::new(None)),
            http_client: reqwest::Client::new(),
        }
    }

    pub async fn verify_token(&self, token: &str) -> Result<AuthPrincipal, AuthError> {
        if self.is_configured_keycloak_issuer_token(token) {
            return self.verify_keycloak_token(token).await;
        }

        match self.verify_local_token(token) {
            Err(AuthError::Unavailable) if self.keycloak.is_some() => Err(AuthError::Invalid),
            result => result,
        }
    }

    pub fn verify_local_token(&self, token: &str) -> Result<AuthPrincipal, AuthError> {
        let Some(secret) = &self.local_hs256_secret else {
            return Err(AuthError::Unavailable);
        };

        let claims = decode::<LocalAccessClaims>(
            token,
            &DecodingKey::from_secret(secret.as_bytes()),
            &Validation::new(Algorithm::HS256),
        )
        .map_err(|_| AuthError::Invalid)?
        .claims;

        let user_id = claims.sub.parse::<i64>().map_err(|_| AuthError::Invalid)?;

        Ok(AuthPrincipal::Local {
            user_id,
            organization_id: claims.organization_id,
            is_superuser: claims.is_superuser,
        })
    }

    fn is_configured_keycloak_issuer_token(&self, token: &str) -> bool {
        let Some(keycloak) = &self.keycloak else {
            return false;
        };

        insecure_decode::<UntrustedIssuerClaims>(token)
            .map(|data| data.claims.iss.as_deref() == Some(keycloak.issuer.as_str()))
            .unwrap_or(false)
    }

    async fn verify_keycloak_token(&self, token: &str) -> Result<AuthPrincipal, AuthError> {
        let Some(keycloak) = &self.keycloak else {
            return Err(AuthError::Unavailable);
        };

        let header = decode_header(token).map_err(|_| AuthError::Invalid)?;
        if header.alg != Algorithm::RS256 {
            return Err(AuthError::Invalid);
        }

        let kid = header.kid.as_deref().ok_or(AuthError::Invalid)?;
        let jwks = self.load_keycloak_jwks(keycloak).await?;
        let jwk = jwks.find(kid).ok_or(AuthError::Invalid)?;
        let key = DecodingKey::from_jwk(jwk).map_err(|_| AuthError::Invalid)?;

        let mut validation = Validation::new(Algorithm::RS256);
        validation.set_audience(&[keycloak.audience.as_str()]);
        validation.set_issuer(&[keycloak.issuer.as_str()]);
        validation.set_required_spec_claims(&["exp", "iss", "sub", "aud"]);

        let claims = decode::<KeycloakClaims>(token, &key, &validation)
            .map_err(|_| AuthError::Invalid)?
            .claims;

        Ok(AuthPrincipal::Keycloak {
            issuer: claims.iss,
            subject: claims.sub,
        })
    }

    async fn load_keycloak_jwks(&self, keycloak: &KeycloakConfig) -> Result<JwkSet, AuthError> {
        if let Some(jwks) = self.cached_jwks()? {
            return Ok(jwks);
        }

        let jwks = self
            .http_client
            .get(&keycloak.jwks_url)
            .send()
            .await
            .map_err(|_| AuthError::ProviderUnavailable)?
            .error_for_status()
            .map_err(|_| AuthError::ProviderUnavailable)?
            .json::<JwkSet>()
            .await
            .map_err(|_| AuthError::ProviderUnavailable)?;

        self.cache_jwks(jwks.clone(), keycloak.jwks_cache_seconds);
        Ok(jwks)
    }

    fn cached_jwks(&self) -> Result<Option<JwkSet>, AuthError> {
        let cache = self
            .jwks_cache
            .read()
            .map_err(|_| AuthError::ProviderUnavailable)?;
        Ok(cache
            .as_ref()
            .filter(|cached| cached.expires_at > Instant::now())
            .map(|cached| cached.jwks.clone()))
    }

    fn cache_jwks(&self, jwks: JwkSet, cache_seconds: u64) {
        if let Ok(mut cache) = self.jwks_cache.write() {
            *cache = Some(CachedJwks {
                expires_at: Instant::now() + Duration::from_secs(cache_seconds),
                jwks,
            });
        }
    }
}

fn env_flag(name: &str) -> bool {
    std::env::var(name)
        .map(|value| {
            matches!(
                value.trim().to_ascii_lowercase().as_str(),
                "1" | "true" | "yes" | "on"
            )
        })
        .unwrap_or(false)
}

fn env_or_default(name: &str, default: &str) -> String {
    std::env::var(name)
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| default.to_string())
}

#[cfg(test)]
mod tests {
    use jsonwebtoken::{EncodingKey, Header, encode};
    use serde::Serialize;
    use serde_json::json;

    use super::*;

    const KEYCLOAK_ISSUER: &str = "http://localhost:8084/realms/bijmantra";
    const KEYCLOAK_AUDIENCE: &str = "bijmantra-api";
    const KEYCLOAK_SUBJECT: &str = "00000000-0000-4000-8000-000000000042";
    const KEYCLOAK_TOKEN: &str = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImJpai10ZXN0LWtleSJ9.eyJzdWIiOiIwMDAwMDAwMC0wMDAwLTQwMDAtODAwMC0wMDAwMDAwMDAwNDIiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwODQvcmVhbG1zL2Jpam1hbnRyYSIsImF1ZCI6ImJpam1hbnRyYS1hcGkiLCJleHAiOjQxMDI0NDQ4MDB9.AmpxfCs96U6zQkQCF6GMea0QQu-SBpC9AmjA40IlbseNOV27OZaeBkRbYRfXOFsBpL-Tij3dFI4QYf3934vZEBp8KRW0xim5A2NIyhO7YQkA4UjluYHSqfA_QDqDUKIm-RGau6JRC2iKlZa6spJphIeHaD7pIgJdTMjim1nWyMTUse1zUzakZ44CZHgf_LCFoAZlr5AEzIRo8PKy6Sxqn76SwD_XHR3KWMtiwoWTOQR7eI3oK6zoYPxfXo3F8krWH-qWtTZbMdnXu4b80j4jvpqkQ7XY63T_3CGOZnTgH0uExQ_ch6frffIL-4JTU5cesbsizE1r_pcoDx3SepUOWQ";

    #[derive(Debug, Serialize)]
    struct TestClaims<'a> {
        sub: &'a str,
        organization_id: i64,
        is_superuser: bool,
        exp: i64,
    }

    fn token(secret: &str, exp: i64) -> String {
        token_with_sub(secret, "42", exp)
    }

    fn token_with_sub(secret: &str, sub: &str, exp: i64) -> String {
        encode(
            &Header::new(Algorithm::HS256),
            &TestClaims {
                sub,
                organization_id: 7,
                is_superuser: false,
                exp,
            },
            &EncodingKey::from_secret(secret.as_bytes()),
        )
        .unwrap()
    }

    fn keycloak_jwks() -> JwkSet {
        serde_json::from_value(json!({
            "keys": [{
                "kty": "RSA",
                "n": "n2SjVzUo7vXgOg5DrseHYy75SZjQIxgSxygYoDCXL3WhvwKaKpEQGBiP_N-swfg_Z6AoSegTSWRNBm497BvctZ9rpOwpJ-do4nifoKL295YBjaY0-pWKSgr-lE3DgnBrLC6bJwR8EjZtrjfQGFzzvQjpXxAB5fRqJUqccr_Tj42FTXx3vjEWgrHApAVAfbxTKV2a1A2txHEfi11ApAti1O0UHidj8BwUrefKiFL6v_dSNySe7LQa_txa0G1_vQuxc0jr3dqeSrURHY-m3uzTMke2sE382_Djj7-7FccbxbC8Is_4Zi2izqv10Iuqoc67xA9YMR8nKA92FuJEl5MO7w",
                "e": "AQAB",
                "kid": "bij-test-key",
                "alg": "RS256",
                "use": "sig"
            }]
        }))
        .unwrap()
    }

    #[test]
    fn verifies_fastapi_local_claims() {
        let auth = AuthConfig::local_hs256("secret");
        let principal = auth
            .verify_local_token(&token("secret", 4_102_444_800))
            .unwrap();

        assert_eq!(
            principal,
            AuthPrincipal::Local {
                user_id: 42,
                organization_id: 7,
                is_superuser: false,
            }
        );
    }

    #[test]
    fn rejects_invalid_secret() {
        let auth = AuthConfig::local_hs256("secret");

        assert_eq!(
            auth.verify_local_token(&token("other-secret", 4_102_444_800)),
            Err(AuthError::Invalid)
        );
    }

    #[test]
    fn rejects_expired_token() {
        let auth = AuthConfig::local_hs256("secret");

        assert_eq!(
            auth.verify_local_token(&token("secret", 1)),
            Err(AuthError::Invalid)
        );
    }

    #[test]
    fn rejects_local_tokens_with_malformed_subject() {
        let auth = AuthConfig::local_hs256("secret");

        assert_eq!(
            auth.verify_local_token(&token_with_sub("secret", "not-a-user-id", 4_102_444_800)),
            Err(AuthError::Invalid)
        );
    }

    #[test]
    fn reports_unavailable_without_secret() {
        let auth = AuthConfig::local_hs256("");

        assert_eq!(
            auth.verify_local_token("token"),
            Err(AuthError::Unavailable)
        );
    }

    #[tokio::test]
    async fn verifies_keycloak_rs256_claims_from_cached_jwks() {
        let auth =
            AuthConfig::keycloak_with_jwks(KEYCLOAK_ISSUER, KEYCLOAK_AUDIENCE, keycloak_jwks());

        let principal = auth.verify_token(KEYCLOAK_TOKEN).await.unwrap();

        assert_eq!(
            principal,
            AuthPrincipal::Keycloak {
                issuer: KEYCLOAK_ISSUER.to_string(),
                subject: KEYCLOAK_SUBJECT.to_string(),
            }
        );
    }

    #[tokio::test]
    async fn rejects_keycloak_tokens_with_wrong_audience() {
        let auth = AuthConfig::keycloak_with_jwks(KEYCLOAK_ISSUER, "other-api", keycloak_jwks());

        assert_eq!(
            auth.verify_token(KEYCLOAK_TOKEN).await,
            Err(AuthError::Invalid)
        );
    }

    #[test]
    fn keycloak_jwks_cache_returns_only_unexpired_keys() {
        let auth =
            AuthConfig::keycloak_with_jwks(KEYCLOAK_ISSUER, KEYCLOAK_AUDIENCE, keycloak_jwks());

        assert!(auth.cached_jwks().unwrap().is_some());

        auth.cache_jwks(keycloak_jwks(), 0);

        assert!(auth.cached_jwks().unwrap().is_none());
    }
}
