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
  // Comprehensive breeding platform with all major modules
  {
    id: 'plant-sciences',
    name: 'Plant Sciences',
    description: 'Breeding, genomics, phenotyping, and field operations',
    icon: 'Seedling',
    route: '/programs',
    component: lazy(() => import('@/divisions/plant-sciences')),
    requiredPermissions: ['read:plant_sciences'],
    status: 'active',
    version: '1.0.0',
    sections: [
      // Subgroup: Core Breeding
      {
        id: 'breeding',
        name: 'Breeding',
        route: '/programs',
        icon: 'Wheat',
        isAbsolute: true,
        items: [
          { id: 'programs', name: 'Programs', route: '/programs', isAbsolute: true },
          { id: 'trials', name: 'Trials', route: '/trials', isAbsolute: true },
          { id: 'studies', name: 'Studies', route: '/studies', isAbsolute: true },
          { id: 'germplasm', name: 'Germplasm', route: '/germplasm', isAbsolute: true },
          { id: 'pipeline', name: 'Pipeline', route: '/pipeline', isAbsolute: true },
          { id: 'locations', name: 'Locations', route: '/locations', isAbsolute: true },
          { id: 'seasons', name: 'Seasons', route: '/seasons', isAbsolute: true },
        ],
      },
      // Subgroup: Crossing
      {
        id: 'crossing',
        name: 'Crossing',
        route: '/crosses',
        icon: 'GitMerge',
        isAbsolute: true,
        items: [
          { id: 'crosses', name: 'Crosses', route: '/crosses', isAbsolute: true },
          { id: 'crossing-projects', name: 'Crossing Projects', route: '/crossingprojects', isAbsolute: true },
          { id: 'planned-crosses', name: 'Planned Crosses', route: '/plannedcrosses', isAbsolute: true },
          { id: 'progeny', name: 'Progeny', route: '/progeny', isAbsolute: true },
          { id: 'pedigree', name: 'Pedigree', route: '/pedigree', isAbsolute: true },
        ],
      },
      // Subgroup: Selection & Prediction
      {
        id: 'selection',
        name: 'Selection',
        route: '/selectionindex',
        icon: 'Target',
        isAbsolute: true,
        items: [
          { id: 'selection-index', name: 'Selection Index', route: '/selectionindex', isAbsolute: true },
          { id: 'selection-decision', name: 'Selection Decision', route: '/selection-decision', isAbsolute: true },
          { id: 'parent-selection', name: 'Parent Selection', route: '/parent-selection', isAbsolute: true },
          { id: 'cross-prediction', name: 'Cross Prediction', route: '/cross-prediction', isAbsolute: true },
          { id: 'performance-ranking', name: 'Rankings', route: '/performance-ranking', isAbsolute: true },
          { id: 'genetic-gain', name: 'Genetic Gain', route: '/geneticgain', isAbsolute: true },
          { id: 'genetic-gain-calculator', name: 'Gain Calculator', route: '/genetic-gain-calculator', isAbsolute: true },
        ],
      },
      // Subgroup: Phenotyping
      {
        id: 'phenotyping',
        name: 'Phenotyping',
        route: '/traits',
        icon: 'Microscope',
        isAbsolute: true,
        items: [
          { id: 'traits', name: 'Traits', route: '/traits', isAbsolute: true },
          { id: 'observations', name: 'Observations', route: '/observations', isAbsolute: true },
          { id: 'collect-data', name: 'Collect Data', route: '/observations/collect', isAbsolute: true },
          { id: 'observation-units', name: 'Observation Units', route: '/observationunits', isAbsolute: true },
          { id: 'events', name: 'Events', route: '/events', isAbsolute: true },
          { id: 'images', name: 'Images', route: '/images', isAbsolute: true },
          { id: 'data-quality', name: 'Data Quality', route: '/dataquality', isAbsolute: true },
        ],
      },
      // Subgroup: Genotyping
      {
        id: 'genotyping',
        name: 'Genotyping',
        route: '/samples',
        icon: 'TestTube2',
        isAbsolute: true,
        items: [
          { id: 'samples', name: 'Samples', route: '/samples', isAbsolute: true },
          { id: 'variants', name: 'Variants', route: '/variants', isAbsolute: true },
          { id: 'allele-matrix', name: 'Allele Matrix', route: '/allelematrix', isAbsolute: true },
          { id: 'plates', name: 'Plates', route: '/plates', isAbsolute: true },
          { id: 'genome-maps', name: 'Genome Maps', route: '/genomemaps', isAbsolute: true },
        ],
      },
      // Subgroup: Genomics & Analysis
      {
        id: 'genomics',
        name: 'Genomics',
        route: '/genetic-diversity',
        icon: 'Dna',
        isAbsolute: true,
        items: [
          { id: 'genetic-diversity', name: 'Genetic Diversity', route: '/genetic-diversity', isAbsolute: true },
          { id: 'population-genetics', name: 'Population Genetics', route: '/population-genetics', isAbsolute: true },
          { id: 'linkage-disequilibrium', name: 'LD Analysis', route: '/linkage-disequilibrium', isAbsolute: true },
          { id: 'haplotype-analysis', name: 'Haplotypes', route: '/haplotype-analysis', isAbsolute: true },
          { id: 'breeding-values', name: 'Breeding Values', route: '/breeding-values', isAbsolute: true },
          { id: 'genomic-selection', name: 'Genomic Selection', route: '/genomic-selection', isAbsolute: true },
          { id: 'genetic-correlation', name: 'Correlations', route: '/genetic-correlation', isAbsolute: true },
          { id: 'qtl-mapping', name: 'QTL Mapping', route: '/qtl-mapping', isAbsolute: true },
          { id: 'mas', name: 'Marker-Assisted Selection', route: '/marker-assisted-selection', isAbsolute: true },
          { id: 'parentage-analysis', name: 'Parentage', route: '/parentage-analysis', isAbsolute: true },
          { id: 'gxe', name: 'G×E Interaction', route: '/gxe-interaction', isAbsolute: true },
          { id: 'stability-analysis', name: 'Stability', route: '/stability-analysis', isAbsolute: true },
          { id: 'trial-network', name: 'Trial Network', route: '/trial-network', isAbsolute: true },
          { id: 'molecular-breeding', name: 'Molecular Breeding', route: '/molecular-breeding', isAbsolute: true },
          { id: 'phenomic-selection', name: 'Phenomics', route: '/phenomic-selection', isAbsolute: true },
          { id: 'speed-breeding', name: 'Speed Breeding', route: '/speed-breeding', isAbsolute: true },
          { id: 'doubled-haploid', name: 'Doubled Haploid', route: '/doubled-haploid', isAbsolute: true },
        ],
      },
      // Subgroup: Field Operations
      {
        id: 'field',
        name: 'Field Ops',
        route: '/fieldlayout',
        icon: 'Map',
        isAbsolute: true,
        items: [
          { id: 'field-layout', name: 'Field Layout', route: '/fieldlayout', isAbsolute: true },
          { id: 'fieldbook', name: 'Field Book', route: '/fieldbook', isAbsolute: true },
          { id: 'field-map', name: 'Field Map', route: '/field-map', isAbsolute: true },
          { id: 'field-planning', name: 'Field Planning', route: '/field-planning', isAbsolute: true },
          { id: 'field-scanner', name: 'Field Scanner', route: '/field-scanner', isAbsolute: true },
          { id: 'trial-design', name: 'Trial Design', route: '/trialdesign', isAbsolute: true },
          { id: 'trial-planning', name: 'Trial Planning', route: '/trialplanning', isAbsolute: true },
          { id: 'season-planning', name: 'Season Planning', route: '/season-planning', isAbsolute: true },
          { id: 'resource-allocation', name: 'Resources', route: '/resource-allocation', isAbsolute: true },
          { id: 'resource-calendar', name: 'Calendar', route: '/resource-calendar', isAbsolute: true },
          { id: 'harvest', name: 'Harvest', route: '/harvest', isAbsolute: true },
          { id: 'nursery', name: 'Nursery', route: '/nursery', isAbsolute: true },
        ],
      },
      // Subgroup: Analysis & Visualization
      {
        id: 'analysis',
        name: 'Analysis',
        route: '/statistics',
        icon: 'BarChart3',
        isAbsolute: true,
        items: [
          { id: 'statistics', name: 'Statistics', route: '/statistics', isAbsolute: true },
          { id: 'visualization', name: 'Visualization', route: '/visualization', isAbsolute: true },
          { id: 'trial-comparison', name: 'Trial Comparison', route: '/trial-comparison', isAbsolute: true },
          { id: 'trial-summary', name: 'Trial Summary', route: '/trial-summary', isAbsolute: true },
          { id: 'breeding-simulator', name: 'Breeding Simulator', route: '/breeding-simulator', isAbsolute: true },
        ],
      },
      // Subgroup: AI & Compute
      {
        id: 'ai-compute',
        name: 'AI & Compute',
        route: '/wasm-genomics',
        icon: 'Cpu',
        isAbsolute: true,
        items: [
          { id: 'wasm-genomics', name: 'WASM Genomics', route: '/wasm-genomics', isAbsolute: true },
          { id: 'wasm-gblup', name: 'WASM GBLUP', route: '/wasm-gblup', isAbsolute: true },
          { id: 'wasm-popgen', name: 'WASM PopGen', route: '/wasm-popgen', isAbsolute: true },
          { id: 'plant-vision', name: 'Plant Vision', route: '/plant-vision', isAbsolute: true },
          { id: 'disease-atlas', name: 'Disease Atlas', route: '/disease-atlas', isAbsolute: true },
          { id: 'crop-health', name: 'Crop Health', route: '/crop-health', isAbsolute: true },
          { id: 'yield-predictor', name: 'Yield Predictor', route: '/yield-predictor', isAbsolute: true },
          { id: 'yieldmap', name: 'Yield Map', route: '/yieldmap', isAbsolute: true },
        ],
      },
    ],
  },

  // Division 2: Seed Bank (Active)
  {
    id: 'seed-bank',
    name: 'Seed Bank',
    description: 'Genetic resources preservation and germplasm conservation',
    icon: 'Warehouse',
    route: '/seedlots',
    component: lazy(() => import('@/divisions/seed-bank')),
    requiredPermissions: ['read:seed_bank'],
    status: 'active',
    version: '0.5.0',
    sections: [
      { id: 'seedlots', name: 'Seed Lots', route: '/seedlots', icon: 'Package', isAbsolute: true },
      { id: 'inventory', name: 'Inventory', route: '/inventory', icon: 'Archive', isAbsolute: true },
    ],
  },

  // Division 3: Earth Systems (Beta)
  {
    id: 'earth-systems',
    name: 'Earth Systems',
    description: 'Climate patterns, weather intelligence, and GIS platform',
    icon: 'Globe',
    route: '/weather',
    component: lazy(() => import('@/divisions/earth-systems')),
    requiredPermissions: ['read:earth_systems'],
    status: 'beta',
    version: '0.5.0',
    sections: [
      { id: 'weather', name: 'Weather', route: '/weather', icon: 'Thermometer', isAbsolute: true },
      { id: 'forecast', name: 'Forecast', route: '/weather-forecast', icon: 'CloudSun', isAbsolute: true },
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

  // Division 5: Sensor Networks (Planned)
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

  // Division 8: Tools & Utilities
  {
    id: 'tools',
    name: 'Tools',
    description: 'Utilities, reports, and productivity tools',
    icon: 'Wrench',
    route: '/quick-entry',
    component: lazy(() => import('@/divisions/integrations')),
    requiredPermissions: ['read:tools'],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'utilities',
        name: 'Utilities',
        route: '/quick-entry',
        icon: 'Zap',
        isAbsolute: true,
        items: [
          { id: 'quick-entry', name: 'Quick Entry', route: '/quick-entry', isAbsolute: true },
          { id: 'scanner', name: 'Barcode Scanner', route: '/scanner', isAbsolute: true },
          { id: 'labels', name: 'Labels', route: '/labels', isAbsolute: true },
          { id: 'calculator', name: 'Calculator', route: '/calculator', isAbsolute: true },
        ],
      },
      {
        id: 'data-ops',
        name: 'Data Ops',
        route: '/import-export',
        icon: 'Upload',
        isAbsolute: true,
        items: [
          { id: 'import-export', name: 'Import/Export', route: '/import-export', isAbsolute: true },
          { id: 'batch-operations', name: 'Batch Operations', route: '/batch-operations', isAbsolute: true },
          { id: 'data-sync', name: 'Data Sync', route: '/data-sync', isAbsolute: true },
          { id: 'backup', name: 'Backup', route: '/backup', isAbsolute: true },
        ],
      },
      {
        id: 'reports',
        name: 'Reports',
        route: '/reports',
        icon: 'FileText',
        isAbsolute: true,
        items: [
          { id: 'reports', name: 'Reports', route: '/reports', isAbsolute: true },
          { id: 'advanced-reports', name: 'Advanced Reports', route: '/advanced-reports', isAbsolute: true },
        ],
      },
      {
        id: 'ai',
        name: 'AI Assistant',
        route: '/ai-assistant',
        icon: 'MessageSquare',
        isAbsolute: true,
        items: [
          { id: 'ai-assistant', name: 'AI Assistant', route: '/ai-assistant', isAbsolute: true },
          { id: 'ai-settings', name: 'AI Settings', route: '/ai-settings', isAbsolute: true },
        ],
      },
    ],
  },

  // Division 9: Settings & Admin
  {
    id: 'settings',
    name: 'Settings',
    description: 'System configuration and administration',
    icon: 'Settings',
    route: '/settings',
    component: lazy(() => import('@/divisions/integrations')),
    requiredPermissions: ['manage:settings'],
    status: 'active',
    version: '1.0.0',
    sections: [
      { id: 'settings', name: 'Settings', route: '/settings', icon: 'Settings', isAbsolute: true },
      { id: 'users', name: 'Users', route: '/users', icon: 'Users', isAbsolute: true },
      { id: 'people', name: 'People', route: '/people', icon: 'Users', isAbsolute: true },
      { id: 'team-management', name: 'Team', route: '/team-management', icon: 'Users', isAbsolute: true },
      { id: 'collaboration', name: 'Collaboration', route: '/collaboration', icon: 'Users', isAbsolute: true },
      { id: 'workflows', name: 'Workflows', route: '/workflows', icon: 'RefreshCw', isAbsolute: true },
      { id: 'auditlog', name: 'Audit Log', route: '/auditlog', icon: 'Shield', isAbsolute: true },
      { id: 'system-health', name: 'System Health', route: '/system-health', icon: 'Activity', isAbsolute: true },
      { id: 'offline', name: 'Offline Mode', route: '/offline', icon: 'WifiOff', isAbsolute: true },
      { id: 'serverinfo', name: 'API Explorer', route: '/serverinfo', icon: 'Code', isAbsolute: true },
    ],
  },

  // Division 10: Knowledge (Active)
  {
    id: 'knowledge',
    name: 'Knowledge',
    description: 'Documentation, training, and community resources',
    icon: 'BookOpen',
    route: '/help',
    component: lazy(() => import('@/divisions/knowledge')),
    requiredPermissions: ['read:knowledge'],
    status: 'active',
    version: '0.5.0',
    sections: [
      { id: 'help', name: 'Help Center', route: '/help', icon: 'HelpCircle', isAbsolute: true },
      { id: 'glossary', name: 'Glossary', route: '/glossary', icon: 'Book', isAbsolute: true },
      { id: 'about', name: 'About', route: '/about', icon: 'Info', isAbsolute: true },
      { id: 'vision', name: 'Our Vision', route: '/vision', icon: 'Telescope', isAbsolute: true },
    ],
  },

  // Division 11: Dashboard & Home
  {
    id: 'home',
    name: 'Home',
    description: 'Dashboard, insights, and overview',
    icon: 'Home',
    route: '/dashboard',
    component: lazy(() => import('@/divisions/knowledge')),
    requiredPermissions: ['read:dashboard'],
    status: 'active',
    version: '1.0.0',
    sections: [
      { id: 'dashboard', name: 'Dashboard', route: '/dashboard', icon: 'BarChart3', isAbsolute: true },
      { id: 'insights', name: 'AI Insights', route: '/insights', icon: 'Brain', isAbsolute: true },
      { id: 'apex-analytics', name: 'Analytics', route: '/apex-analytics', icon: 'LineChart', isAbsolute: true },
      { id: 'search', name: 'Search', route: '/search', icon: 'Search', isAbsolute: true },
      { id: 'notifications', name: 'Notifications', route: '/notifications', icon: 'Bell', isAbsolute: true },
      { id: 'activity', name: 'Activity', route: '/activity', icon: 'Activity', isAbsolute: true },
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
