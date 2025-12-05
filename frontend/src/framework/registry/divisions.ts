/**
 * Parashakti Framework - Division Definitions
 * 
 * Central registry of all divisions in the Bijmantra platform.
 * Divisions are lazy-loaded to optimize initial bundle size.
 */

import { lazy } from 'react';
import { Division } from './types';

/**
 * All registered divisions
 * 
 * Order matters for navigation display.
 * Status determines visibility and behavior.
 */
export const divisions: Division[] = [
  // Division 1: Plant Sciences (Active)
  {
    id: 'plant-sciences',
    name: 'Plant Sciences',
    description: 'Breeding operations, genomics, molecular biology, and crop sciences',
    icon: 'Seedling',
    route: '/plant-sciences',
    component: lazy(() => import('@/divisions/plant-sciences')),
    requiredPermissions: ['read:plant_sciences'],
    status: 'active',
    version: '1.0.0',
    sections: [
      { id: 'breeding', name: 'Breeding Operations', route: '/breeding', icon: 'FlaskConical' },
      { id: 'genomics', name: 'Genetics & Genomics', route: '/genomics', icon: 'Dna' },
      { id: 'molecular', name: 'Molecular Biology', route: '/molecular', icon: 'Microscope' },
      { id: 'crop-sciences', name: 'Crop Sciences', route: '/crop-sciences', icon: 'Wheat' },
      { id: 'soil', name: 'Soil & Environment', route: '/soil', icon: 'Mountain' },
    ],
  },

  // Division 2: Seed Bank (Planned)
  {
    id: 'seed-bank',
    name: 'Seed Bank',
    description: 'Genetic resources preservation and germplasm conservation',
    icon: 'Warehouse',
    route: '/seed-bank',
    component: lazy(() => import('@/divisions/seed-bank')),
    requiredPermissions: ['read:seed_bank'],
    featureFlag: 'SEED_BANK_ENABLED',
    status: 'planned',
    version: '0.1.0',
    sections: [
      { id: 'vault', name: 'Seed Vault', route: '/vault', icon: 'Lock' },
      { id: 'accessions', name: 'Accessions', route: '/accessions', icon: 'Database' },
      { id: 'conservation', name: 'Conservation', route: '/conservation', icon: 'Shield' },
    ],
  },

  // Division 3: Earth Systems (Beta)
  {
    id: 'earth-systems',
    name: 'Earth Systems',
    description: 'Climate patterns, weather intelligence, and GIS platform',
    icon: 'Globe',
    route: '/earth-systems',
    component: lazy(() => import('@/divisions/earth-systems')),
    requiredPermissions: ['read:earth_systems'],
    featureFlag: 'EARTH_SYSTEMS_ENABLED',
    status: 'beta',
    version: '0.5.0',
    sections: [
      { id: 'climate', name: 'Climate Patterns', route: '/climate', icon: 'CloudSun' },
      { id: 'weather', name: 'Weather Intelligence', route: '/weather', icon: 'Thermometer' },
      { id: 'gis', name: 'GIS Platform', route: '/gis', icon: 'Map' },
    ],
  },

  // Division 4: Sun-Earth Systems (Visionary)
  {
    id: 'sun-earth-systems',
    name: 'Sun-Earth Systems',
    description: 'Solar radiation, magnetic field monitoring, and space weather',
    icon: 'Sun',
    route: '/sun-earth-systems',
    component: lazy(() => import('@/divisions/sun-earth-systems')),
    requiredPermissions: ['read:sun_earth_systems'],
    featureFlag: 'SUN_EARTH_SYSTEMS_ENABLED',
    status: 'visionary',
    version: '0.0.1',
  },

  // Division 5: Sensor Networks (Conceptual)
  {
    id: 'sensor-networks',
    name: 'Sensor Networks',
    description: 'IoT integration and environmental monitoring',
    icon: 'Radio',
    route: '/sensor-networks',
    component: lazy(() => import('@/divisions/sensor-networks')),
    requiredPermissions: ['read:sensor_networks'],
    featureFlag: 'SENSOR_NETWORKS_ENABLED',
    status: 'planned',
    version: '0.0.1',
  },

  // Division 6: Commercial (Planned)
  {
    id: 'commercial',
    name: 'Commercial',
    description: 'Traceability, licensing, and ERP integration',
    icon: 'Building2',
    route: '/commercial',
    component: lazy(() => import('@/divisions/commercial')),
    requiredPermissions: ['read:commercial'],
    featureFlag: 'COMMERCIAL_ENABLED',
    status: 'planned',
    version: '0.2.0',
    sections: [
      { id: 'traceability', name: 'Traceability', route: '/traceability', icon: 'ScanLine' },
      { id: 'licensing', name: 'Licensing', route: '/licensing', icon: 'FileCheck' },
      { id: 'erp', name: 'ERP Integration', route: '/erp', icon: 'Link' },
    ],
  },

  // Division 7: Space Research (Visionary)
  {
    id: 'space-research',
    name: 'Space Research',
    description: 'Interplanetary agriculture and space agency collaborations',
    icon: 'Rocket',
    route: '/space-research',
    component: lazy(() => import('@/divisions/space-research')),
    requiredPermissions: ['read:space_research'],
    featureFlag: 'SPACE_RESEARCH_ENABLED',
    status: 'visionary',
    version: '0.0.1',
  },

  // Division 8: Integration Hub (Planned)
  {
    id: 'integrations',
    name: 'Integrations',
    description: 'Third-party API connections and external services',
    icon: 'Plug',
    route: '/integrations',
    component: lazy(() => import('@/divisions/integrations')),
    requiredPermissions: ['manage:integrations'],
    status: 'planned',
    version: '0.3.0',
  },

  // Division 9: Knowledge (Partial)
  {
    id: 'knowledge',
    name: 'Knowledge',
    description: 'Documentation, training, and community resources',
    icon: 'BookOpen',
    route: '/knowledge',
    component: lazy(() => import('@/divisions/knowledge')),
    requiredPermissions: ['read:knowledge'],
    status: 'active',
    version: '0.5.0',
    sections: [
      { id: 'docs', name: 'Documentation', route: '/docs', icon: 'FileText' },
      { id: 'training', name: 'Training Hub', route: '/training', icon: 'GraduationCap' },
      { id: 'community', name: 'Community', route: '/community', icon: 'Users' },
    ],
  },
];

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
    
    // Show beta/planned if feature flag is enabled
    if (d.featureFlag && enabledFlags.has(d.featureFlag)) return true;
    
    // Hide visionary by default
    if (d.status === 'visionary') return false;
    
    // Show planned/beta without feature flags
    return !d.featureFlag;
  });
}
