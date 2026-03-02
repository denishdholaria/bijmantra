/**
 * Parashakti Framework - Feature Flags Hook
 */

import { useMemo } from 'react';
import { FeatureFlag } from './types';

/**
 * Default feature flag values
 * 
 * In production, these would be loaded from:
 * 1. Environment variables
 * 2. Backend API (per-organization settings)
 * 3. Local storage (for development overrides)
 */
const DEFAULT_FLAGS: Record<string, boolean> = {
  // Active divisions - enabled by default
  [FeatureFlag.AI_FEATURES_ENABLED]: true,
  [FeatureFlag.OFFLINE_SYNC_ENABLED]: true,
  [FeatureFlag.WASM_COMPUTE_ENABLED]: true,
  
  // Beta divisions - enabled for testing
  [FeatureFlag.EARTH_SYSTEMS_ENABLED]: true,
  
  // Planned divisions - disabled by default
  [FeatureFlag.SEED_BANK_ENABLED]: false,
  [FeatureFlag.COMMERCIAL_ENABLED]: false,
  [FeatureFlag.SENSOR_NETWORKS_ENABLED]: false,
  
  // Visionary divisions - disabled
  [FeatureFlag.SUN_EARTH_SYSTEMS_ENABLED]: false,
  [FeatureFlag.SPACE_RESEARCH_ENABLED]: false,
};

/**
 * Load feature flags from environment
 */
function loadFlagsFromEnv(): Record<string, boolean> {
  const flags = { ...DEFAULT_FLAGS };
  
  // Check for environment variable overrides
  // Vite exposes env vars with VITE_ prefix
  Object.keys(FeatureFlag).forEach(key => {
    const envKey = `VITE_${key}`;
    const envValue = import.meta.env[envKey];
    if (envValue !== undefined) {
      flags[key] = envValue === 'true' || envValue === '1';
    }
  });
  
  return flags;
}

/**
 * Load feature flags from localStorage (dev overrides)
 */
function loadFlagsFromStorage(): Record<string, boolean> {
  try {
    const stored = localStorage.getItem('bijmantra_feature_flags');
    if (stored) {
      return JSON.parse(stored);
    }
  } catch {
    // Ignore parse errors
  }
  return {};
}

/**
 * Hook to access feature flags
 */
export function useFeatureFlags() {
  const flags = useMemo(() => {
    const envFlags = loadFlagsFromEnv();
    const storageFlags = loadFlagsFromStorage();
    
    // Storage overrides env (for dev testing)
    return { ...envFlags, ...storageFlags };
  }, []);
  
  const enabledFlags = useMemo(() => {
    return new Set(
      Object.entries(flags)
        .filter(([_, enabled]) => enabled)
        .map(([key]) => key)
    );
  }, [flags]);
  
  const isEnabled = (flag: string): boolean => {
    return flags[flag] ?? false;
  };
  
  const setFlag = (flag: string, enabled: boolean): void => {
    const stored = loadFlagsFromStorage();
    stored[flag] = enabled;
    localStorage.setItem('bijmantra_feature_flags', JSON.stringify(stored));
    // Trigger re-render by reloading (simple approach)
    window.location.reload();
  };
  
  return {
    flags,
    enabledFlags,
    isEnabled,
    setFlag,
  };
}
