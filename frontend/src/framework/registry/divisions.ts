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
          { id: 'germplasm-comparison', name: 'Compare Germplasm', route: '/germplasm-comparison', isAbsolute: true },
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
          { id: 'pedigree-3d', name: '3D Pedigree', route: '/pedigree-3d', isAbsolute: true },
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
          { id: 'selection-index-calculator', name: 'Index Calculator', route: '/selection-index-calculator', isAbsolute: true },
          { id: 'selection-decision', name: 'Selection Decision', route: '/selection-decision', isAbsolute: true },
          { id: 'parent-selection', name: 'Parent Selection', route: '/parent-selection', isAbsolute: true },
          { id: 'cross-prediction', name: 'Cross Prediction', route: '/cross-prediction', isAbsolute: true },
          { id: 'performance-ranking', name: 'Rankings', route: '/performance-ranking', isAbsolute: true },
          { id: 'genetic-gain', name: 'Genetic Gain', route: '/geneticgain', isAbsolute: true },
          { id: 'genetic-gain-tracker', name: 'Gain Tracker', route: '/genetic-gain-tracker', isAbsolute: true },
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
          { id: 'breeding-value-calculator', name: 'BLUP Calculator', route: '/breeding-value-calculator', isAbsolute: true },
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
          { id: 'harvest-management', name: 'Harvest Mgmt', route: '/harvest-management', isAbsolute: true },
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
          { id: 'wasm-genomics', name: 'Genomics Benchmark', route: '/wasm-genomics', isAbsolute: true },
          { id: 'wasm-gblup', name: 'Genomic BLUP', route: '/wasm-gblup', isAbsolute: true },
          { id: 'wasm-popgen', name: 'Population Genetics', route: '/wasm-popgen', isAbsolute: true },
          { id: 'plant-vision', name: 'Plant Vision', route: '/plant-vision', isAbsolute: true },
          { id: 'vision-strategy', name: 'Vision Strategy', route: '/plant-vision/strategy', isAbsolute: true },
          { id: 'disease-atlas', name: 'Disease Atlas', route: '/disease-atlas', isAbsolute: true },
          { id: 'crop-health', name: 'Crop Health', route: '/crop-health', isAbsolute: true },
          { id: 'yield-predictor', name: 'Yield Predictor', route: '/yield-predictor', isAbsolute: true },
          { id: 'yieldmap', name: 'Yield Map', route: '/yieldmap', isAbsolute: true },
        ],
      },
      // Subgroup: Analysis Tools (NEW - Dec 10, 2025)
      {
        id: 'analysis-tools',
        name: 'Analysis Tools',
        route: '/disease-resistance',
        icon: 'Beaker',
        isAbsolute: true,
        items: [
          { id: 'disease-resistance', name: 'Disease Resistance', route: '/disease-resistance', isAbsolute: true },
          { id: 'abiotic-stress', name: 'Abiotic Stress', route: '/abiotic-stress', isAbsolute: true },
          { id: 'bioinformatics', name: 'Bioinformatics', route: '/bioinformatics', isAbsolute: true },
          { id: 'crop-calendar', name: 'Crop Calendar', route: '/crop-calendar', isAbsolute: true },
          { id: 'spatial-analysis', name: 'Spatial Analysis', route: '/spatial-analysis', isAbsolute: true },
          { id: 'pedigree-analysis', name: 'Pedigree Analysis', route: '/pedigree-analysis', isAbsolute: true },
          { id: 'phenotype-analysis', name: 'Phenotype Analysis', route: '/phenotype-analysis', isAbsolute: true },
        ],
      },
    ],
  },

  // Division 2: Seed Bank (Active)
  // Genetic resources preservation and germplasm conservation module
  {
    id: 'seed-bank',
    name: 'Seed Bank',
    description: 'Genetic resources preservation and germplasm conservation',
    icon: 'Warehouse',
    route: '/seed-bank',
    component: lazy(() => import('@/divisions/seed-bank')),
    requiredPermissions: ['read:seed_bank'],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'overview',
        name: 'Overview',
        route: '/seed-bank',
        icon: 'LayoutDashboard',
        isAbsolute: true,
        items: [
          { id: 'dashboard', name: 'Dashboard', route: '/seed-bank', isAbsolute: true },
          { id: 'vault', name: 'Vault Management', route: '/seed-bank/vault', isAbsolute: true },
          { id: 'monitoring', name: 'Vault Monitoring', route: '/seed-bank/monitoring', isAbsolute: true },
          { id: 'offline', name: 'Offline Data Entry', route: '/seed-bank/offline', isAbsolute: true },
        ],
      },
      {
        id: 'accessions',
        name: 'Accessions',
        route: '/seed-bank/accessions',
        icon: 'Sprout',
        isAbsolute: true,
        items: [
          { id: 'all', name: 'All Accessions', route: '/seed-bank/accessions', isAbsolute: true },
          { id: 'register', name: 'Register New', route: '/seed-bank/accessions/new', isAbsolute: true },
        ],
      },
      {
        id: 'conservation',
        name: 'Conservation',
        route: '/seed-bank/conservation',
        icon: 'Shield',
        isAbsolute: true,
        items: [
          { id: 'status', name: 'Conservation Status', route: '/seed-bank/conservation', isAbsolute: true },
          { id: 'viability', name: 'Viability Testing', route: '/seed-bank/viability', isAbsolute: true },
          { id: 'regeneration', name: 'Regeneration Planning', route: '/seed-bank/regeneration', isAbsolute: true },
        ],
      },
      {
        id: 'exchange',
        name: 'Exchange',
        route: '/seed-bank/exchange',
        icon: 'ArrowLeftRight',
        isAbsolute: true,
        items: [
          { id: 'germplasm-exchange', name: 'Germplasm Exchange', route: '/seed-bank/exchange', isAbsolute: true },
          { id: 'mcpd', name: 'MCPD Exchange', route: '/seed-bank/mcpd', isAbsolute: true },
          { id: 'mta', name: 'MTA Management', route: '/seed-bank/mta', isAbsolute: true },
        ],
      },
      {
        id: 'integration',
        name: 'Global Integration',
        route: '/seed-bank/grin-search',
        icon: 'Globe',
        isAbsolute: true,
        items: [
          { id: 'grin-search', name: 'GRIN/Genesys Search', route: '/seed-bank/grin-search', isAbsolute: true },
          { id: 'taxonomy', name: 'Taxonomy Validator', route: '/seed-bank/taxonomy', isAbsolute: true },
        ],
      },
    ],
  },



  // Division 5: Sensor Networks (Active)
  {
    id: 'sensor-networks',
    name: 'Sensor Networks',
    description: 'IoT integration and environmental monitoring',
    icon: 'Radio',
    route: '/sensor-networks',
    component: lazy(() => import('@/divisions/sensor-networks')),
    requiredPermissions: ['read:sensor_networks'],
    status: 'active',
    version: '1.0.0',
    sections: [
      { id: 'dashboard', name: 'Dashboard', route: '/sensor-networks', icon: 'LayoutDashboard', isAbsolute: true },
      { id: 'devices', name: 'Devices', route: '/sensor-networks/devices', icon: 'Radio', isAbsolute: true },
      { id: 'live', name: 'Live Data', route: '/sensor-networks/live', icon: 'Activity', isAbsolute: true },
      { id: 'alerts', name: 'Alerts', route: '/sensor-networks/alerts', icon: 'Bell', isAbsolute: true },
    ],
  },

  // Division 6: Seed Commerce (Merged: Seed Operations + Commercial)
  // Complete seed industry operations: Lab, Processing, Inventory, Dispatch, DUS, Licensing
  {
    id: 'seed-commerce',
    name: 'Seed Commerce',
    description: 'Lab testing, processing, inventory, dispatch, DUS testing & licensing',
    icon: 'Building2',
    route: '/seed-operations',
    component: lazy(() => import('@/divisions/seed-operations')),
    requiredPermissions: ['read:seed_operations'],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'lab-testing',
        name: 'Lab Testing',
        route: '/seed-operations/samples',
        icon: 'FlaskConical',
        isAbsolute: true,
        items: [
          { id: 'samples', name: 'Samples', route: '/seed-operations/samples', isAbsolute: true },
          { id: 'testing', name: 'Tests', route: '/seed-operations/testing', isAbsolute: true },
          { id: 'certificates', name: 'Certificates', route: '/seed-operations/certificates', isAbsolute: true },
        ],
      },
      {
        id: 'processing',
        name: 'Processing',
        route: '/seed-operations/quality-gate',
        icon: 'Shield',
        isAbsolute: true,
        items: [
          { id: 'quality-gate', name: 'Quality Gate', route: '/seed-operations/quality-gate', isAbsolute: true },
          { id: 'batches', name: 'Batches', route: '/seed-operations/batches', isAbsolute: true },
          { id: 'stages', name: 'Stages', route: '/seed-operations/stages', isAbsolute: true },
        ],
      },
      {
        id: 'inventory',
        name: 'Inventory',
        route: '/seed-operations/lots',
        icon: 'Package',
        isAbsolute: true,
        items: [
          { id: 'lots', name: 'Seed Lots', route: '/seed-operations/lots', isAbsolute: true },
          { id: 'warehouse', name: 'Warehouse', route: '/seed-operations/warehouse', isAbsolute: true },
          { id: 'alerts', name: 'Alerts', route: '/seed-operations/alerts', isAbsolute: true },
        ],
      },
      {
        id: 'dispatch',
        name: 'Dispatch',
        route: '/seed-operations/dispatch',
        icon: 'Truck',
        isAbsolute: true,
        items: [
          { id: 'create-dispatch', name: 'Create Dispatch', route: '/seed-operations/dispatch', isAbsolute: true },
          { id: 'history', name: 'History', route: '/seed-operations/dispatch-history', isAbsolute: true },
          { id: 'firms', name: 'Firms', route: '/seed-operations/firms', isAbsolute: true },
        ],
      },
      {
        id: 'traceability',
        name: 'Traceability',
        route: '/seed-operations/track',
        icon: 'QrCode',
        isAbsolute: true,
        items: [
          { id: 'track', name: 'Track Lot', route: '/seed-operations/track', isAbsolute: true },
          { id: 'lineage', name: 'Lineage', route: '/seed-operations/lineage', isAbsolute: true },
          { id: 'barcode', name: 'Barcode Scanner', route: '/barcode', isAbsolute: true },
        ],
      },
      {
        id: 'dus-testing',
        name: 'DUS Testing',
        route: '/commercial/dus-trials',
        icon: 'ClipboardCheck',
        isAbsolute: true,
        items: [
          { id: 'commercial-dashboard', name: 'Commercial Dashboard', route: '/commercial', isAbsolute: true },
          { id: 'dus-trials', name: 'DUS Trials', route: '/commercial/dus-trials', isAbsolute: true },
          { id: 'dus-crops', name: 'Crop Templates', route: '/commercial/dus-crops', isAbsolute: true },
        ],
      },
      {
        id: 'licensing',
        name: 'Licensing',
        route: '/seed-operations/varieties',
        icon: 'FileCheck',
        isAbsolute: true,
        items: [
          { id: 'varieties', name: 'Varieties', route: '/seed-operations/varieties', isAbsolute: true },
          { id: 'agreements', name: 'Agreements', route: '/seed-operations/agreements', isAbsolute: true },
        ],
      },
    ],
  },

  // Division 7: Space Research (Active)
  {
    id: 'space-research',
    name: 'Space Research',
    description: 'Interplanetary agriculture and space agency collaborations',
    icon: 'Rocket',
    route: '/space-research',
    component: lazy(() => import('@/divisions/space-research')),
    requiredPermissions: ['read:space_research'],
    status: 'active',
    version: '1.0.0',
    sections: [
      { id: 'dashboard', name: 'Dashboard', route: '/space-research', icon: 'Rocket', isAbsolute: true },
      { id: 'crops', name: 'Space Crops', route: '/space-research/crops', icon: 'Leaf', isAbsolute: true },
      { id: 'radiation', name: 'Radiation', route: '/space-research/radiation', icon: 'Shield', isAbsolute: true },
      { id: 'life-support', name: 'Life Support', route: '/space-research/life-support', icon: 'Users', isAbsolute: true },
    ],
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
    description: 'System configuration, integrations, and administration',
    icon: 'Settings',
    route: '/settings',
    component: lazy(() => import('@/divisions/integrations')),
    requiredPermissions: ['manage:settings'],
    status: 'active',
    version: '1.0.0',
    sections: [
      {
        id: 'general',
        name: 'General',
        route: '/settings',
        icon: 'Settings',
        isAbsolute: true,
        items: [
          { id: 'settings', name: 'Settings', route: '/settings', icon: 'Settings', isAbsolute: true },
          { id: 'profile', name: 'Profile', route: '/profile', icon: 'User', isAbsolute: true },
        ],
      },
      {
        id: 'team',
        name: 'Team & Users',
        route: '/users',
        icon: 'Users',
        isAbsolute: true,
        items: [
          { id: 'users', name: 'Users', route: '/users', icon: 'Users', isAbsolute: true },
          { id: 'people', name: 'People', route: '/people', icon: 'Users', isAbsolute: true },
          { id: 'team-management', name: 'Team', route: '/team-management', icon: 'Users', isAbsolute: true },
          { id: 'collaboration', name: 'Collaboration', route: '/collaboration', icon: 'Users', isAbsolute: true },
        ],
      },
      {
        id: 'integrations',
        name: 'Integrations',
        route: '/integrations',
        icon: 'Plug',
        isAbsolute: true,
        items: [
          { id: 'integration-hub', name: 'Integration Hub', route: '/integrations', icon: 'Plug', isAbsolute: true },
          { id: 'api-explorer', name: 'API Explorer', route: '/serverinfo', icon: 'Code', isAbsolute: true },
        ],
      },
      {
        id: 'system',
        name: 'System',
        route: '/system-health',
        icon: 'Activity',
        isAbsolute: true,
        items: [
          { id: 'system-health', name: 'System Health', route: '/system-health', icon: 'Activity', isAbsolute: true },
          { id: 'auditlog', name: 'Audit Log', route: '/auditlog', icon: 'Shield', isAbsolute: true },
          { id: 'workflows', name: 'Workflows', route: '/workflows', icon: 'RefreshCw', isAbsolute: true },
          { id: 'offline', name: 'Offline Mode', route: '/offline', icon: 'WifiOff', isAbsolute: true },
          { id: 'mobile-app', name: 'Mobile App', route: '/mobile-app', icon: 'Smartphone', isAbsolute: true },
          { id: 'barcode', name: 'Barcode Scanner', route: '/barcode', icon: 'QrCode', isAbsolute: true },
        ],
      },
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
    version: '0.6.0',
    sections: [
      { id: 'help', name: 'Help Center', route: '/help', icon: 'HelpCircle', isAbsolute: true },
      { id: 'training', name: 'Training Hub', route: '/knowledge/training', icon: 'GraduationCap', isAbsolute: true },
      { id: 'devguru', name: 'DevGuru (PhD Mentor)', route: '/devguru', icon: 'GraduationCap', isAbsolute: true },
      { id: 'forums', name: 'Community Forums', route: '/knowledge/forums', icon: 'MessageSquare', isAbsolute: true },
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
