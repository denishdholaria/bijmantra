/**
 * Parashakti Framework - Division Registry
 * 
 * Public API for the division registry system.
 */

export * from './types';
export * from './capabilities';
export * from './divisions';
export { useDivisionRegistry } from './useDivisionRegistry';
export * from './moduleRegistry';

// Navigation truth consolidation - single source of truth
export * from './navigation-source';
export * from './navigation-derived';
export * from './capability-navigation';

// Future modules (planned development)
export * from './futureWorkspaces';
export * from './futureDivisions';
