/**
 * Division Service
 * 
 * Business logic for division operations.
 * Metadata lives in divisions.ts, logic lives here.
 */

import type { Division } from '../types';
import { divisions } from '../divisions';

/**
 * Get a division by ID
 */
export function getDivision(id: string): Division | undefined {
  return divisions.find(d => d.id === id);
}

/**
 * Get all divisions with a specific status
 */
export function getDivisionsByStatus(status: Division['status']): Division[] {
  return divisions.filter(d => d.status === status);
}

/**
 * Get divisions that should be shown in navigation
 * (excludes visionary unless explicitly enabled)
 */
export function getNavigableDivisions(enabledFlags: Set<string>): Division[] {
  return divisions.filter(d => {
    // Always show active divisions
    if (d.status === 'active') return true;
    
    // Show preview/planned if feature flag is enabled
    if (d.featureFlag && enabledFlags.has(d.featureFlag)) return true;
    
    // Hide visionary by default
    if (d.status === 'visionary') return false;
    
    // Show planned/preview without feature flags
    return !d.featureFlag;
  });
}
