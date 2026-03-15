/**
 * Parashakti Framework - Division Registry Hook
 * 
 * React hook for accessing division registry with feature flag awareness.
 */

import { useMemo } from 'react';
import { divisions, getDivision, getNavigableDivisions } from './divisions';
import { Division } from './types';
import { useFeatureFlags } from '../features/useFeatureFlags';

/**
 * Hook to access the division registry
 */
export function useDivisionRegistry() {
  const { enabledFlags, isEnabled } = useFeatureFlags();
  
  // Get navigable divisions based on feature flags
  const navigableDivisions = useMemo(() => {
    return getNavigableDivisions(enabledFlags);
  }, [enabledFlags]);
  
  // Get active divisions (status = 'active')
  const activeDivisions = useMemo(() => {
    return navigableDivisions.filter(d => d.status === 'active');
  }, [navigableDivisions]);
  
  // Check if a specific division is accessible
  const isDivisionAccessible = (divisionId: string): boolean => {
    const division = getDivision(divisionId);
    if (!division) return false;
    
    // Check feature flag if required
    if (division.featureFlag && !isEnabled(division.featureFlag)) {
      return false;
    }
    
    return true;
  };
  
  // Get division by ID (with access check)
  const getDivisionIfAccessible = (divisionId: string): Division | undefined => {
    if (!isDivisionAccessible(divisionId)) return undefined;
    return getDivision(divisionId);
  };
  
  return {
    // All registered divisions
    allDivisions: divisions,
    
    // Divisions shown in navigation
    navigableDivisions,
    
    // Only active status divisions
    activeDivisions,
    
    // Utility functions
    getDivision: getDivisionIfAccessible,
    isDivisionAccessible,
    
    // Feature flag check
    isEnabled,
  };
}
