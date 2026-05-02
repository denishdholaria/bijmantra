/**
 * Parashakti Framework - Feature Flags Types
 */

/**
 * All available feature flags
 */
export enum FeatureFlag {
  // Division flags
  SEED_BANK_ENABLED = 'SEED_BANK_ENABLED',
  EARTH_SYSTEMS_ENABLED = 'EARTH_SYSTEMS_ENABLED',
  SUN_EARTH_SYSTEMS_ENABLED = 'SUN_EARTH_SYSTEMS_ENABLED',
  SENSOR_NETWORKS_ENABLED = 'SENSOR_NETWORKS_ENABLED',
  COMMERCIAL_ENABLED = 'COMMERCIAL_ENABLED',
  SPACE_RESEARCH_ENABLED = 'SPACE_RESEARCH_ENABLED',
  
  // Feature flags
  AI_FEATURES_ENABLED = 'AI_FEATURES_ENABLED',
  OFFLINE_SYNC_ENABLED = 'OFFLINE_SYNC_ENABLED',
  WASM_COMPUTE_ENABLED = 'WASM_COMPUTE_ENABLED',
}

/**
 * Feature flag configuration
 */
export interface FeatureFlagConfig {
  // Default values for flags
  defaults: Record<string, boolean>;
  
  // Organization-specific overrides
  orgOverrides?: Record<string, Record<string, boolean>>;
}
