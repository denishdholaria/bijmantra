/**
 * Parashakti Framework
 * 
 * The foundational framework for Bijmantra platform.
 * Provides division registry, feature flags, authentication,
 * and shared services.
 */

// Division Registry
export * from './registry';

// Feature Flags
export * from './features';

// Shell Components
export * from './shell';

// Re-export commonly used types
export type { Division, DivisionSection, DivisionStatus } from './registry/types';
export type { FeatureFlag } from './features/types';
