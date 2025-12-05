/**
 * Parashakti Framework - Division Registry Types
 * 
 * Defines the structure for divisions in the Bijmantra platform.
 * Each division is a self-contained feature domain that can be
 * lazy-loaded and enabled/disabled via feature flags.
 */

import { ComponentType, LazyExoticComponent } from 'react';
import { LucideIcon } from 'lucide-react';

/**
 * Division status indicates the maturity level
 */
export type DivisionStatus = 'active' | 'beta' | 'planned' | 'visionary';

/**
 * A section within a division (for sub-navigation)
 */
export interface DivisionSection {
  id: string;
  name: string;
  route: string;
  icon?: string;
  description?: string;
}

/**
 * Division definition - the core unit of the Parashakti framework
 */
export interface Division {
  // Identity
  id: string;
  name: string;
  description: string;
  icon: string;
  
  // Routing
  route: string;
  component: LazyExoticComponent<ComponentType<unknown>> | ComponentType<unknown>;
  
  // Access Control
  requiredPermissions: string[];
  featureFlag?: string;
  
  // Metadata
  status: DivisionStatus;
  version: string;
  
  // Sub-navigation
  sections?: DivisionSection[];
  
  // Dependencies on other divisions
  dependencies?: string[];
}

/**
 * Division registry state
 */
export interface DivisionRegistryState {
  divisions: Division[];
  activeDivisionId: string | null;
  
  // Actions
  getDivision: (id: string) => Division | undefined;
  getActiveDivisions: () => Division[];
  setActiveDivision: (id: string) => void;
  isDivisionEnabled: (id: string) => boolean;
}
