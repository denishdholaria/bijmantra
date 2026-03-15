/**
 * Centralized Application Configuration
 *
 * ADR-007: All environment variable reads are centralized here.
 * No other file should read `import.meta.env.*` directly.
 *
 * To add a new config value:
 *   1. Add the env var to `.env` / `.env.local`
 *   2. Add it to this file
 *   3. Import from `@/config` in your module
 */

// ────────────────────────────────────────────────────────────
// API & Network
// ────────────────────────────────────────────────────────────

/** Backend API base URL (no trailing slash). */
export const API_URL: string =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000';

/** WebSocket / Socket.IO endpoint. */
export const SOCKET_URL: string =
  import.meta.env.VITE_SOCKET_URL || API_URL;

// ────────────────────────────────────────────────────────────
// Search
// ────────────────────────────────────────────────────────────

/** Meilisearch host URL. */
export const MEILISEARCH_HOST: string =
  import.meta.env.VITE_MEILISEARCH_HOST || 'http://localhost:7700';

/** Meilisearch API key (public, search-only). */
export const MEILISEARCH_API_KEY: string =
  import.meta.env.VITE_MEILISEARCH_API_KEY || '';

// ────────────────────────────────────────────────────────────
// Push Notifications
// ────────────────────────────────────────────────────────────

/** VAPID public key for Web Push subscriptions. */
export const VAPID_PUBLIC_KEY: string =
  import.meta.env.VITE_VAPID_PUBLIC_KEY || '';

// ────────────────────────────────────────────────────────────
// Observability
// ────────────────────────────────────────────────────────────

/** PostHog analytics API key. */
export const POSTHOG_API_KEY: string =
  import.meta.env.VITE_POSTHOG_API_KEY || '';

/** PostHog analytics host. */
export const POSTHOG_HOST: string =
  import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com';

/** Sentry DSN for error reporting. */
export const SENTRY_DSN: string =
  import.meta.env.VITE_SENTRY_DSN || '';

/** Application version string. */
export const APP_VERSION: string =
  import.meta.env.VITE_APP_VERSION || '0.1.0';

/** Minimum log level (DEBUG, INFO, WARN, ERROR). */
export const LOG_LEVEL: string =
  import.meta.env.VITE_LOG_LEVEL || 'INFO';

// ────────────────────────────────────────────────────────────
// Build Mode
// ────────────────────────────────────────────────────────────

/** True in development mode. */
export const IS_DEV: boolean = import.meta.env.DEV;

/** True in production mode. */
export const IS_PROD: boolean = import.meta.env.PROD;

/** Current Vite mode string (e.g. 'development', 'production'). */
export const MODE: string = import.meta.env.MODE;

// ────────────────────────────────────────────────────────────
// Feature Flags
// ────────────────────────────────────────────────────────────

/** Centralized feature-flag environment overrides keyed by FeatureFlag enum names. */
export const FEATURE_FLAG_ENV_OVERRIDES: Record<string, string | undefined> = {
  AI_FEATURES_ENABLED: import.meta.env.VITE_AI_FEATURES_ENABLED,
  OFFLINE_SYNC_ENABLED: import.meta.env.VITE_OFFLINE_SYNC_ENABLED,
  WASM_COMPUTE_ENABLED: import.meta.env.VITE_WASM_COMPUTE_ENABLED,
  EARTH_SYSTEMS_ENABLED: import.meta.env.VITE_EARTH_SYSTEMS_ENABLED,
  SEED_BANK_ENABLED: import.meta.env.VITE_SEED_BANK_ENABLED,
  COMMERCIAL_ENABLED: import.meta.env.VITE_COMMERCIAL_ENABLED,
  SENSOR_NETWORKS_ENABLED: import.meta.env.VITE_SENSOR_NETWORKS_ENABLED,
  SUN_EARTH_SYSTEMS_ENABLED: import.meta.env.VITE_SUN_EARTH_SYSTEMS_ENABLED,
  SPACE_RESEARCH_ENABLED: import.meta.env.VITE_SPACE_RESEARCH_ENABLED,
};
