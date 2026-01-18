/**
 * Workspace Registry
 * 
 * Central registry of all workspaces in the Bijmantra platform.
 * Defines the 5 main pathways: Plant Breeding, Seed Industry, Innovation Lab, Gene Bank, Administration.
 * 
 * @see docs/gupt/archieve/GATEWAY-WORKSPACE.md for full specification
 */

import type { 
  Workspace, 
  WorkspaceId, 
  WorkspaceModule, 
  ModuleId,
  CrossAccessConfig 
} from '@/types/workspace';

/**
 * All registered workspaces
 * Order matters for gateway display
 */
export const workspaces: Workspace[] = [
  // Workspace 1: Plant Breeding (BrAPI-Aligned)
  {
    id: 'breeding',
    name: 'Plant Breeding',
    description: 'Programs, trials, crosses, genomics',
    longDescription: 'Comprehensive plant breeding platform with BrAPI v2.1 compliance. Manage breeding programs, trials, crosses, germplasm, and genomic analysis.',
    icon: 'Wheat',
    color: 'from-green-500 to-emerald-600',
    bgColor: 'bg-green-50 dark:bg-green-950/30',
    landingRoute: '/breeding/dashboard',
    modules: ['core', 'germplasm', 'phenotyping', 'genotyping'],
    targetUsers: ['Breeders', 'Geneticists', 'Research Scientists'],
    pageCount: 83,
    isBrAPIAligned: true,
  },

  // Workspace 2: Seed Industry
  {
    id: 'seed-ops',
    name: 'Seed Industry',
    description: 'Lab, processing, inventory, dispatch',
    longDescription: 'Complete seed industry operations including lab testing, quality processing, inventory management, dispatch logistics, DUS testing, and variety licensing.',
    icon: 'Factory',
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    landingRoute: '/seed-ops/dashboard',
    modules: ['lab-testing', 'processing', 'inventory', 'dispatch', 'traceability', 'dus-testing', 'licensing'],
    targetUsers: ['Seed Companies', 'Quality Labs', 'Dispatch Managers', 'Licensing Officers'],
    pageCount: 22,
    isBrAPIAligned: false,
  },

  // Workspace 3: Innovation Lab
  {
    id: 'research',
    name: 'Innovation Lab',
    description: 'Space, AI, analytics, experimental tools',
    longDescription: 'Cutting-edge tools for innovation and experimentation. Includes space agriculture research, AI-powered plant vision, WASM analytics, and advanced analysis tools.',
    icon: 'Microscope',
    color: 'from-purple-500 to-violet-600',
    bgColor: 'bg-purple-50 dark:bg-purple-950/30',
    landingRoute: '/research/dashboard',
    modules: ['space-research', 'ai-vision', 'analytics', 'analysis-tools'],
    targetUsers: ['Scientists', 'PhD Students', 'Innovators', 'Data Scientists'],
    pageCount: 28,
    isBrAPIAligned: false,
  },

  // Workspace 4: Gene Bank
  {
    id: 'genebank',
    name: 'Gene Bank',
    description: 'Conservation, vaults, exchange',
    longDescription: 'Germplasm conservation and genebank management inspired by Svalbard Global Seed Vault. Manage vaults, accessions, viability testing, regeneration, and germplasm exchange.',
    icon: 'Building2',
    color: 'from-amber-500 to-orange-600',
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
    landingRoute: '/genebank/dashboard',
    modules: ['seed-bank', 'environment', 'sensors'],
    targetUsers: ['Genebank Curators', 'Conservation Officers', 'Exchange Coordinators'],
    pageCount: 34,
    isBrAPIAligned: false,
  },

  // Workspace 5: Administration
  {
    id: 'admin',
    name: 'Administration',
    description: 'Users, settings, system',
    longDescription: 'System administration and configuration. Manage users, teams, integrations, system health, audit logs, workflows, and developer tools.',
    icon: 'Settings',
    color: 'from-slate-500 to-gray-600',
    bgColor: 'bg-slate-50 dark:bg-slate-950/30',
    landingRoute: '/admin/dashboard',
    modules: ['settings', 'users-teams', 'integrations', 'system', 'tools', 'developer'],
    targetUsers: ['IT Admins', 'System Managers', 'Organization Admins'],
    pageCount: 25,
    isBrAPIAligned: false,
  },
];

/**
 * Module definitions with page mappings
 * Maps modules to their pages and cross-workspace access
 */
export const workspaceModules: WorkspaceModule[] = [
  // BrAPI Core Module
  {
    id: 'core',
    name: 'Core',
    description: 'Programs, Trials, Studies, Locations, Seasons, People, Lists, Pedigree',
    icon: 'Database',
    route: '/programs',
    isBrAPI: true,
    workspaces: ['breeding'],
    pages: [
      { id: 'programs', name: 'Programs', route: '/programs' },
      { id: 'program-detail', name: 'Program Detail', route: '/programs/:id' },
      { id: 'trials', name: 'Trials', route: '/trials' },
      { id: 'trial-detail', name: 'Trial Detail', route: '/trials/:id' },
      { id: 'studies', name: 'Studies', route: '/studies' },
      { id: 'study-detail', name: 'Study Detail', route: '/studies/:id' },
      { id: 'locations', name: 'Locations', route: '/locations' },
      { id: 'seasons', name: 'Seasons', route: '/seasons' },
      { id: 'people', name: 'People', route: '/people' },
      { id: 'lists', name: 'Lists', route: '/lists' },
      { id: 'pedigree', name: 'Pedigree Viewer', route: '/pedigree' },
      { id: 'pedigree-3d', name: '3D Pedigree Explorer', route: '/pedigree-3d' },
    ],
  },

  // BrAPI Germplasm Module
  {
    id: 'germplasm',
    name: 'Germplasm',
    description: 'Germplasm CRUD, Attributes, Crosses, Crossing Projects, Seed Lots, Selection',
    icon: 'Sprout',
    route: '/germplasm',
    isBrAPI: true,
    workspaces: ['breeding', 'genebank'],
    pages: [
      { id: 'germplasm', name: 'Germplasm', route: '/germplasm', isCrossAccess: true, crossAccessWorkspaces: ['genebank'] },
      { id: 'germplasm-detail', name: 'Germplasm Detail', route: '/germplasm/:id' },
      { id: 'germplasm-comparison', name: 'Germplasm Comparison', route: '/germplasm-comparison' },
      { id: 'germplasm-search', name: 'Germplasm Search', route: '/germplasm-search' },
      { id: 'germplasm-passport', name: 'Germplasm Passport', route: '/germplasm-passport' },
      { id: 'germplasm-attributes', name: 'Germplasm Attributes', route: '/germplasmattributes' },
      { id: 'attribute-values', name: 'Attribute Values', route: '/attributevalues' },
      { id: 'collections', name: 'Germplasm Collection', route: '/collections' },
      { id: 'crosses', name: 'Crosses', route: '/crosses' },
      { id: 'crossing-projects', name: 'Crossing Projects', route: '/crossingprojects' },
      { id: 'planned-crosses', name: 'Planned Crosses', route: '/plannedcrosses' },
      { id: 'crossing-planner', name: 'Crossing Planner', route: '/crossingplanner' },
      { id: 'progeny', name: 'Progeny', route: '/progeny' },
      { id: 'seed-lots', name: 'Seed Lots', route: '/seedlots', isCrossAccess: true, crossAccessWorkspaces: ['seed-ops'] },
      { id: 'selection-index', name: 'Selection Index', route: '/selectionindex' },
      { id: 'selection-decision', name: 'Selection Decision', route: '/selection-decision' },
      { id: 'parent-selection', name: 'Parent Selection', route: '/parent-selection' },
      { id: 'cross-prediction', name: 'Cross Prediction', route: '/cross-prediction' },
      // Additional breeding pages
      { id: 'genetic-gain-tracker', name: 'Genetic Gain Tracker', route: '/genetic-gain-tracker' },
      { id: 'genetic-gain-calculator', name: 'Genetic Gain Calculator', route: '/genetic-gain-calculator' },
      { id: 'geneticgain', name: 'Genetic Gain', route: '/geneticgain' },
      { id: 'pipeline', name: 'Breeding Pipeline', route: '/pipeline' },
      { id: 'performance-ranking', name: 'Performance Ranking', route: '/performance-ranking' },
      { id: 'breeding-goals', name: 'Breeding Goals', route: '/breeding-goals' },
      { id: 'breeding-history', name: 'Breeding History', route: '/breeding-history' },
      { id: 'comparison', name: 'Comparison', route: '/comparison' },
    ],
  },

  // BrAPI Phenotyping Module
  {
    id: 'phenotyping',
    name: 'Phenotyping',
    description: 'Observations, Traits, Field Ops, Harvest, Nursery, Data Quality',
    icon: 'Microscope',
    route: '/traits',
    isBrAPI: true,
    workspaces: ['breeding'],
    pages: [
      { id: 'traits', name: 'Traits', route: '/traits' },
      { id: 'observations', name: 'Observations', route: '/observations' },
      { id: 'collect-data', name: 'Collect Data', route: '/observations/collect' },
      { id: 'observation-units', name: 'Observation Units', route: '/observationunits' },
      { id: 'events', name: 'Events', route: '/events' },
      { id: 'images', name: 'Images', route: '/images' },
      { id: 'data-quality', name: 'Data Quality', route: '/dataquality' },
      { id: 'ontologies', name: 'Ontologies', route: '/ontologies' },
      { id: 'field-layout', name: 'Field Layout', route: '/fieldlayout' },
      { id: 'field-book', name: 'Field Book', route: '/fieldbook' },
      { id: 'field-map', name: 'Field Map', route: '/field-map' },
      { id: 'field-planning', name: 'Field Planning', route: '/field-planning' },
      { id: 'field-scanner', name: 'Field Scanner', route: '/field-scanner' },
      { id: 'trial-design', name: 'Trial Design', route: '/trialdesign' },
      { id: 'trial-planning', name: 'Trial Planning', route: '/trialplanning' },
      { id: 'season-planning', name: 'Season Planning', route: '/season-planning' },
      { id: 'resource-allocation', name: 'Resource Allocation', route: '/resource-allocation' },
      { id: 'resource-calendar', name: 'Resource Calendar', route: '/resource-calendar' },
      { id: 'harvest', name: 'Harvest', route: '/harvest' },
      { id: 'harvest-management', name: 'Harvest Management', route: '/harvest-management' },
      { id: 'harvest-log', name: 'Harvest Log', route: '/harvest-log' },
      { id: 'nursery', name: 'Nursery Management', route: '/nursery' },
      { id: 'phenology', name: 'Phenology Tracker', route: '/phenology' },
      { id: 'quick-entry', name: 'Quick Entry', route: '/quick-entry' },
      { id: 'labels', name: 'Labels', route: '/labels' },
      // Additional phenotyping pages
      { id: 'trial-comparison', name: 'Trial Comparison', route: '/trial-comparison' },
      { id: 'trial-summary', name: 'Trial Summary', route: '/trial-summary' },
      { id: 'variety-release', name: 'Variety Release', route: '/variety-release' },
      { id: 'varietycomparison', name: 'Variety Comparison', route: '/varietycomparison' },
      { id: 'growth-tracker', name: 'Growth Tracker', route: '/growth-tracker' },
      { id: 'plot-history', name: 'Plot History', route: '/plot-history' },
      { id: 'scanner', name: 'Scanner', route: '/scanner' },
      { id: 'crops', name: 'Crops', route: '/crops' },
      { id: 'protocols', name: 'Protocols', route: '/protocols' },
    ],
  },

  // BrAPI Genotyping Module
  {
    id: 'genotyping',
    name: 'Genotyping',
    description: 'Samples, Variants, Calls, Maps, Molecular, Genomic Analysis',
    icon: 'Dna',
    route: '/samples',
    isBrAPI: true,
    workspaces: ['breeding'],
    pages: [
      { id: 'samples', name: 'Samples', route: '/samples' },
      { id: 'variants', name: 'Variants', route: '/variants' },
      { id: 'variant-sets', name: 'Variant Sets', route: '/variantsets' },
      { id: 'calls', name: 'Calls', route: '/calls' },
      { id: 'call-sets', name: 'Call Sets', route: '/callsets' },
      { id: 'plates', name: 'Plates', route: '/plates' },
      { id: 'allele-matrix', name: 'Allele Matrix', route: '/allelematrix' },
      { id: 'genome-maps', name: 'Genome Maps', route: '/genomemaps' },
      { id: 'marker-positions', name: 'Marker Positions', route: '/markerpositions' },
      { id: 'references', name: 'References', route: '/references' },
      { id: 'vendor-orders', name: 'Vendor Orders', route: '/vendororders' },
      { id: 'genetic-diversity', name: 'Genetic Diversity', route: '/genetic-diversity' },
      { id: 'population-genetics', name: 'Population Genetics', route: '/population-genetics' },
      { id: 'ld-analysis', name: 'LD Analysis', route: '/linkage-disequilibrium' },
      { id: 'haplotype-analysis', name: 'Haplotype Analysis', route: '/haplotype-analysis' },
      { id: 'breeding-values', name: 'Breeding Values', route: '/breeding-values' },
      { id: 'blup-calculator', name: 'BLUP Calculator', route: '/breeding-value-calculator' },
      { id: 'genomic-selection', name: 'Genomic Selection', route: '/genomic-selection' },
      { id: 'genetic-correlation', name: 'Genetic Correlation', route: '/genetic-correlation' },
      { id: 'qtl-mapping', name: 'QTL Mapping', route: '/qtl-mapping' },
      { id: 'mas', name: 'Marker-Assisted Selection', route: '/marker-assisted-selection' },
      { id: 'parentage-analysis', name: 'Parentage Analysis', route: '/parentage-analysis' },
      { id: 'gxe', name: 'G×E Interaction', route: '/gxe-interaction' },
      { id: 'stability-analysis', name: 'Stability Analysis', route: '/stability-analysis' },
      { id: 'trial-network', name: 'Trial Network', route: '/trial-network' },
      { id: 'molecular-breeding', name: 'Molecular Breeding', route: '/molecular-breeding' },
      { id: 'phenomic-selection', name: 'Phenomic Selection', route: '/phenomic-selection' },
      { id: 'speed-breeding', name: 'Speed Breeding', route: '/speed-breeding' },
      // Additional genotyping pages
      { id: 'genetic-map', name: 'Genetic Map', route: '/genetic-map' },
      { id: 'sample-tracking', name: 'Sample Tracking', route: '/sample-tracking' },
      { id: 'selection-index-calculator', name: 'Selection Index Calculator', route: '/selection-index-calculator' },
    ],
  },

  // Seed Bank Module
  {
    id: 'seed-bank',
    name: 'Seed Bank',
    description: 'Vaults, accessions, conservation, exchange',
    icon: 'Building2',
    route: '/seed-bank',
    isBrAPI: false,
    workspaces: ['genebank'],
    pages: [
      { id: 'seed-bank-dashboard', name: 'Seed Bank Dashboard', route: '/seed-bank' },
      { id: 'vault-management', name: 'Vault Management', route: '/seed-bank/vault' },
      { id: 'vault-monitoring', name: 'Vault Monitoring', route: '/seed-bank/monitoring' },
      { id: 'accessions', name: 'Accessions List', route: '/seed-bank/accessions' },
      { id: 'accession-new', name: 'Register New Accession', route: '/seed-bank/accessions/new' },
      { id: 'accession-detail', name: 'Accession Detail', route: '/seed-bank/accessions/:id' },
      { id: 'conservation', name: 'Conservation Status', route: '/seed-bank/conservation' },
      { id: 'viability', name: 'Viability Testing', route: '/seed-bank/viability' },
      { id: 'regeneration', name: 'Regeneration Planning', route: '/seed-bank/regeneration' },
      { id: 'exchange', name: 'Germplasm Exchange', route: '/seed-bank/exchange' },
      { id: 'mcpd', name: 'MCPD Exchange', route: '/seed-bank/mcpd' },
      { id: 'mta', name: 'MTA Management', route: '/seed-bank/mta' },
      { id: 'grin-search', name: 'GRIN/Genesys Search', route: '/seed-bank/grin-search' },
      { id: 'taxonomy', name: 'Taxonomy Validator', route: '/seed-bank/taxonomy' },
      { id: 'offline-entry', name: 'Offline Data Entry', route: '/seed-bank/offline' },
    ],
  },

  // Environment Module
  {
    id: 'environment',
    name: 'Environment',
    description: 'Weather, climate, soil, solar monitoring',
    icon: 'CloudSun',
    route: '/earth-systems',
    isBrAPI: false,
    workspaces: ['genebank', 'breeding'],
    pages: [
      { id: 'earth-dashboard', name: 'Earth Systems Dashboard', route: '/earth-systems' },
      { id: 'weather', name: 'Weather Forecast', route: '/earth-systems/weather' },
      { id: 'climate', name: 'Climate Analysis', route: '/earth-systems/climate' },
      { id: 'gdd', name: 'Growing Degrees', route: '/earth-systems/gdd' },
      { id: 'drought', name: 'Drought Monitor', route: '/earth-systems/drought' },
      { id: 'soil', name: 'Soil Data', route: '/earth-systems/soil' },
      { id: 'inputs', name: 'Input Log', route: '/earth-systems/inputs' },
      { id: 'irrigation', name: 'Irrigation Planner', route: '/earth-systems/irrigation' },
      { id: 'field-map-env', name: 'Field Map', route: '/earth-systems/map' },
      { id: 'solar-dashboard', name: 'Solar Dashboard', route: '/sun-earth-systems' },
      { id: 'photoperiod', name: 'Photoperiod Calculator', route: '/sun-earth-systems/photoperiod' },
      { id: 'uv-index', name: 'UV Index', route: '/sun-earth-systems/uv-index' },
      // Additional environment pages (root-level routes for backward compatibility)
      { id: 'weather-root', name: 'Weather', route: '/weather' },
      { id: 'weather-forecast-root', name: 'Weather Forecast', route: '/weather-forecast' },
      { id: 'soil-root', name: 'Soil', route: '/soil' },
      { id: 'irrigation-root', name: 'Irrigation', route: '/irrigation' },
      { id: 'environment-monitor', name: 'Environment Monitor', route: '/environment-monitor' },
      { id: 'fertilizer', name: 'Fertilizer', route: '/fertilizer' },
      { id: 'pest-monitor', name: 'Pest Monitor', route: '/pest-monitor' },
      { id: 'drones', name: 'Drones', route: '/drones' },
      { id: 'iot-sensors', name: 'IoT Sensors', route: '/iot-sensors' },
    ],
  },

  // Sensors Module
  {
    id: 'sensors',
    name: 'Sensors',
    description: 'IoT devices, telemetry, alerts',
    icon: 'Radio',
    route: '/sensor-networks',
    isBrAPI: false,
    workspaces: ['genebank'],
    pages: [
      { id: 'sensor-dashboard', name: 'Sensor Dashboard', route: '/sensor-networks' },
      { id: 'devices', name: 'Devices', route: '/sensor-networks/devices' },
      { id: 'live-data', name: 'Live Data', route: '/sensor-networks/live' },
      { id: 'sensor-alerts', name: 'Alerts', route: '/sensor-networks/alerts' },
      { id: 'telemetry', name: 'Telemetry', route: '/sensor-networks/telemetry' },
      { id: 'aggregates', name: 'Aggregates', route: '/sensor-networks/aggregates' },
      { id: 'environment-link', name: 'Environment Link', route: '/sensor-networks/environment-link' },
    ],
  },

  // Lab Testing Module (Seed Industry)
  {
    id: 'lab-testing',
    name: 'Lab Testing',
    description: 'Samples, Tests, Certificates',
    icon: 'FlaskConical',
    route: '/seed-operations/samples',
    isBrAPI: false,
    workspaces: ['seed-ops'],
    pages: [
      { id: 'lab-samples', name: 'Lab Samples', route: '/seed-operations/samples' },
      { id: 'lab-tests', name: 'Lab Tests', route: '/seed-operations/testing' },
      { id: 'certificates', name: 'Certificates', route: '/seed-operations/certificates' },
    ],
  },

  // Processing Module (Seed Industry)
  {
    id: 'processing',
    name: 'Processing',
    description: 'Quality Gate, Batches, Stages',
    icon: 'Shield',
    route: '/seed-operations/quality-gate',
    isBrAPI: false,
    workspaces: ['seed-ops'],
    pages: [
      { id: 'quality-gate', name: 'Quality Gate Scanner', route: '/seed-operations/quality-gate' },
      { id: 'batches', name: 'Processing Batches', route: '/seed-operations/batches' },
      { id: 'stages', name: 'Processing Stages', route: '/seed-operations/stages' },
    ],
  },

  // Inventory Module (Seed Industry)
  {
    id: 'inventory',
    name: 'Inventory',
    description: 'Seed Lots, Warehouse, Alerts',
    icon: 'Package',
    route: '/seed-operations/lots',
    isBrAPI: false,
    workspaces: ['seed-ops'],
    pages: [
      { id: 'seed-lots-inv', name: 'Seed Lots', route: '/seed-operations/lots' },
      { id: 'warehouse', name: 'Warehouse Management', route: '/seed-operations/warehouse' },
      { id: 'stock-alerts', name: 'Stock Alerts', route: '/seed-operations/alerts' },
      { id: 'seed-inventory', name: 'Seed Inventory', route: '/inventory' },
    ],
  },

  // Dispatch Module (Seed Industry)
  {
    id: 'dispatch',
    name: 'Dispatch',
    description: 'Create Dispatch, History, Firms',
    icon: 'Truck',
    route: '/seed-operations/dispatch',
    isBrAPI: false,
    workspaces: ['seed-ops'],
    pages: [
      { id: 'create-dispatch', name: 'Create Dispatch', route: '/seed-operations/dispatch' },
      { id: 'dispatch-history', name: 'Dispatch History', route: '/seed-operations/dispatch-history' },
      { id: 'firms', name: 'Firms/Dealers', route: '/seed-operations/firms' },
    ],
  },

  // Traceability Module (Seed Industry)
  {
    id: 'traceability',
    name: 'Traceability',
    description: 'Track Lot, Lineage, Barcode Scanner',
    icon: 'QrCode',
    route: '/seed-operations/track',
    isBrAPI: false,
    workspaces: ['seed-ops', 'genebank'],
    pages: [
      { id: 'track-lot', name: 'Track Lot', route: '/seed-operations/track' },
      { id: 'lineage', name: 'Lineage View', route: '/seed-operations/lineage' },
      { id: 'barcode', name: 'Barcode Scanner', route: '/barcode', isCrossAccess: true, crossAccessWorkspaces: ['genebank'] },
    ],
  },

  // DUS Testing Module (Seed Industry)
  {
    id: 'dus-testing',
    name: 'DUS Testing',
    description: 'Dashboard, DUS Trials, Crop Templates',
    icon: 'ClipboardCheck',
    route: '/commercial',
    isBrAPI: false,
    workspaces: ['seed-ops'],
    pages: [
      { id: 'commercial-dashboard', name: 'Commercial Dashboard', route: '/commercial' },
      { id: 'dus-trials', name: 'DUS Trials', route: '/commercial/dus-trials' },
      { id: 'dus-crops', name: 'Crop Templates', route: '/commercial/dus-crops' },
      { id: 'dus-trial-detail', name: 'DUS Trial Detail', route: '/commercial/dus-trials/:id' },
    ],
  },

  // Licensing Module (Seed Industry)
  {
    id: 'licensing',
    name: 'Licensing',
    description: 'Varieties, Agreements',
    icon: 'FileCheck',
    route: '/seed-operations/varieties',
    isBrAPI: false,
    workspaces: ['seed-ops'],
    pages: [
      { id: 'varieties', name: 'Varieties', route: '/seed-operations/varieties' },
      { id: 'agreements', name: 'License Agreements', route: '/seed-operations/agreements' },
      // Additional seed operations pages
      { id: 'seedrequest', name: 'Seed Request', route: '/seedrequest' },
    ],
  },

  // Space Research Module (Innovation Lab)
  {
    id: 'space-research',
    name: 'Space Research',
    description: 'Space crops, radiation, life support',
    icon: 'Rocket',
    route: '/space-research',
    isBrAPI: false,
    workspaces: ['research'],
    pages: [
      { id: 'space-dashboard', name: 'Space Dashboard', route: '/space-research' },
      { id: 'space-crops', name: 'Space Crops', route: '/space-research/crops' },
      { id: 'radiation', name: 'Radiation Calculator', route: '/space-research/radiation' },
      { id: 'life-support', name: 'Life Support', route: '/space-research/life-support' },
    ],
  },

  // AI Vision Module (Innovation Lab)
  {
    id: 'ai-vision',
    name: 'AI Vision',
    description: 'Plant disease detection, model training',
    icon: 'Eye',
    route: '/ai-vision',
    isBrAPI: false,
    workspaces: ['research'],
    pages: [
      { id: 'vision-dashboard', name: 'Vision Dashboard', route: '/ai-vision' },
      { id: 'datasets', name: 'Datasets', route: '/ai-vision/datasets' },
      { id: 'training', name: 'Training', route: '/ai-vision/training' },
      { id: 'model-registry', name: 'Model Registry', route: '/ai-vision/registry' },
      { id: 'annotate', name: 'Annotate', route: '/ai-vision/annotate/:id' },
    ],
  },

  // Analytics Module (Innovation Lab)
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'WASM tools, yield prediction, simulators',
    icon: 'LineChart',
    route: '/wasm-genomics',
    isBrAPI: false,
    workspaces: ['research'],
    pages: [
      { id: 'wasm-genomics', name: 'WASM Genomics Benchmark', route: '/wasm-genomics' },
      { id: 'wasm-gblup', name: 'WASM GBLUP', route: '/wasm-gblup' },
      { id: 'wasm-popgen', name: 'WASM PopGen', route: '/wasm-popgen' },
      { id: 'wasm-ld', name: 'WASM LD Analysis', route: '/wasm-ld' },
      { id: 'wasm-selection', name: 'WASM Selection Index', route: '/wasm-selection' },
      { id: 'yield-predictor', name: 'Yield Predictor', route: '/yield-predictor' },
      { id: 'yield-map', name: 'Yield Map', route: '/yieldmap' },
      { id: 'breeding-simulator', name: 'Breeding Simulator', route: '/breeding-simulator' },
      { id: 'doubled-haploid', name: 'Doubled Haploid', route: '/doubled-haploid' },
      // Additional analytics pages
      { id: 'analytics', name: 'Analytics', route: '/analytics' },
      { id: 'visualization', name: 'Visualization', route: '/visualization' },
      { id: 'experiment-designer', name: 'Experiment Designer', route: '/experiment-designer' },
      { id: 'cost-analysis', name: 'Cost Analysis', route: '/cost-analysis' },
      { id: 'market-analysis', name: 'Market Analysis', route: '/market-analysis' },
      { id: 'publications', name: 'Publications', route: '/publications' },
      { id: 'chrome-ai', name: 'Chrome AI', route: '/chrome-ai' },
    ],
  },

  // Analysis Tools Module (Innovation Lab)
  {
    id: 'analysis-tools',
    name: 'Analysis Tools',
    description: 'Disease resistance, stress, bioinformatics',
    icon: 'Beaker',
    route: '/disease-resistance',
    isBrAPI: false,
    workspaces: ['research'],
    pages: [
      { id: 'disease-resistance', name: 'Disease Resistance', route: '/disease-resistance' },
      { id: 'abiotic-stress', name: 'Abiotic Stress', route: '/abiotic-stress' },
      { id: 'bioinformatics', name: 'Bioinformatics', route: '/bioinformatics' },
      { id: 'crop-calendar', name: 'Crop Calendar', route: '/crop-calendar', isCrossAccess: true, crossAccessWorkspaces: ['breeding', 'genebank'] },
      { id: 'spatial-analysis', name: 'Spatial Analysis', route: '/spatial-analysis' },
      { id: 'pedigree-analysis', name: 'Pedigree Analysis', route: '/pedigree-analysis' },
      { id: 'phenotype-analysis', name: 'Phenotype Analysis', route: '/phenotype-analysis' },
      { id: 'statistics', name: 'Statistics', route: '/statistics', isCrossAccess: true, crossAccessWorkspaces: ['breeding'] },
      { id: 'plant-vision', name: 'Plant Vision', route: '/plant-vision' },
      { id: 'disease-atlas', name: 'Disease Atlas', route: '/disease-atlas' },
      // Additional analysis tools pages
      { id: 'plant-vision-strategy', name: 'Plant Vision Strategy', route: '/plant-vision/strategy' },
    ],
  },

  // Settings Module (Administration)
  {
    id: 'settings',
    name: 'Settings',
    description: 'Profile, preferences, language',
    icon: 'Settings',
    route: '/settings',
    isBrAPI: false,
    workspaces: ['admin'],
    pages: [
      { id: 'settings-page', name: 'Settings', route: '/settings' },
      { id: 'profile', name: 'Profile', route: '/profile' },
      { id: 'languages', name: 'Language Settings', route: '/languages' },
    ],
  },

  // Users & Teams Module (Administration)
  {
    id: 'users-teams',
    name: 'Users & Teams',
    description: 'User management, teams, collaboration',
    icon: 'Users',
    route: '/users',
    isBrAPI: false,
    workspaces: ['admin'],
    pages: [
      { id: 'users', name: 'Users', route: '/users' },
      { id: 'people-admin', name: 'People Directory', route: '/people' },
      { id: 'team-management', name: 'Team Management', route: '/team-management' },
      { id: 'collaboration', name: 'Collaboration Hub', route: '/collaboration' },
    ],
  },

  // Integrations Module (Administration)
  {
    id: 'integrations',
    name: 'Integrations',
    description: 'External APIs, webhooks',
    icon: 'Plug',
    route: '/integrations',
    isBrAPI: false,
    workspaces: ['admin'],
    pages: [
      { id: 'integration-hub', name: 'Integration Hub', route: '/integrations' },
      { id: 'api-explorer', name: 'API Explorer', route: '/serverinfo' },
    ],
  },

  // System Module (Administration)
  {
    id: 'system',
    name: 'System',
    description: 'Health, audit, workflows, backup',
    icon: 'Activity',
    route: '/system-health',
    isBrAPI: false,
    workspaces: ['admin'],
    pages: [
      { id: 'system-health', name: 'System Health', route: '/system-health' },
      { id: 'audit-log', name: 'Audit Log', route: '/auditlog' },
      { id: 'security', name: 'Security Dashboard', route: '/security' },
      { id: 'workflows', name: 'Workflows', route: '/workflows' },
      { id: 'offline-mode', name: 'Offline Mode', route: '/offline' },
      { id: 'backup', name: 'Backup/Restore', route: '/backup' },
      { id: 'data-sync', name: 'Data Sync', route: '/data-sync' },
      { id: 'data-validation', name: 'Data Validation', route: '/data-validation' },
    ],
  },

  // Tools Module (Administration)
  {
    id: 'tools',
    name: 'Tools',
    description: 'Import/export, reports, calculator',
    icon: 'Wrench',
    route: '/import-export',
    isBrAPI: false,
    workspaces: ['admin'],
    pages: [
      { id: 'import-export', name: 'Import/Export', route: '/import-export' },
      { id: 'batch-operations', name: 'Batch Operations', route: '/batch-operations' },
      { id: 'reports', name: 'Reports', route: '/reports', isCrossAccess: true, crossAccessWorkspaces: ['breeding', 'seed-ops', 'research', 'genebank'] },
      { id: 'advanced-reports', name: 'Advanced Reports', route: '/advanced-reports' },
      { id: 'calculator', name: 'Calculator', route: '/calculator' },
    ],
  },

  // Developer Module (Administration)
  {
    id: 'developer',
    name: 'Developer',
    description: 'Dev progress, API explorer, data dictionary',
    icon: 'Code',
    route: '/dev-progress',
    isBrAPI: false,
    workspaces: ['admin'],
    pages: [
      { id: 'dev-progress', name: 'Dev Progress', route: '/dev-progress' },
      { id: 'data-dictionary', name: 'Data Dictionary', route: '/data-dictionary' },
      { id: 'system-settings', name: 'System Settings', route: '/system-settings' },
      // Additional developer pages
      { id: 'api-explorer', name: 'API Explorer', route: '/api-explorer' },
      { id: 'export-templates', name: 'Export Templates', route: '/export-templates' },
      { id: 'ai-assistant', name: 'AI Assistant', route: '/ai-assistant' },
      { id: 'ai-settings', name: 'AI Settings', route: '/ai-settings' },
      { id: 'mobile-app', name: 'Mobile App', route: '/mobile-app' },
      { id: 'blockchain', name: 'Blockchain', route: '/blockchain' },
      { id: 'compliance', name: 'Compliance', route: '/compliance' },
      { id: 'stakeholders', name: 'Stakeholders', route: '/stakeholders' },
      { id: 'training-admin', name: 'Training', route: '/training' },
      { id: 'genebank-admin', name: 'Genebank', route: '/genebank' },
    ],
  },

  // Global Module (Always accessible)
  {
    id: 'global',
    name: 'Global',
    description: 'Dashboard, search, notifications, help',
    icon: 'Globe',
    route: '/dashboard',
    isBrAPI: false,
    workspaces: ['breeding', 'seed-ops', 'research', 'genebank', 'admin'],
    pages: [
      // Core global pages
      { id: 'dashboard', name: 'Dashboard', route: '/dashboard' },
      { id: 'gateway', name: 'Workspace Gateway', route: '/gateway' },
      { id: 'insights', name: 'AI Insights', route: '/insights' },
      { id: 'apex-analytics', name: 'Apex Analytics', route: '/apex-analytics' },
      { id: 'search', name: 'Global Search', route: '/search' },
      { id: 'notifications', name: 'Notifications', route: '/notifications' },
      { id: 'notification-center', name: 'Notification Center', route: '/notification-center' },
      { id: 'activity', name: 'Activity Feed', route: '/activity' },
      // Help & Knowledge
      { id: 'help', name: 'Help Center', route: '/help' },
      { id: 'training', name: 'Training Hub', route: '/knowledge/training' },
      { id: 'forums', name: 'Community Forums', route: '/knowledge/forums' },
      { id: 'glossary', name: 'Glossary', route: '/glossary' },
      { id: 'faq', name: 'FAQ', route: '/faq' },
      { id: 'quick-guide', name: 'Quick Guide', route: '/quick-guide' },
      { id: 'tips', name: 'Tips', route: '/tips' },
      { id: 'keyboard-shortcuts', name: 'Keyboard Shortcuts', route: '/keyboard-shortcuts' },
      // Info pages
      { id: 'about', name: 'About', route: '/about' },
      { id: 'vision', name: 'Vision', route: '/vision' },
      { id: 'changelog', name: 'Changelog', route: '/changelog' },
      { id: 'whats-new', name: "What's New", route: '/whats-new' },
      { id: 'contact', name: 'Contact', route: '/contact' },
      { id: 'feedback', name: 'Feedback', route: '/feedback' },
      { id: 'terms', name: 'Terms of Service', route: '/terms' },
      { id: 'privacy', name: 'Privacy Policy', route: '/privacy' },
      // Auth
      { id: 'login', name: 'Login', route: '/login' },
      // Crop health (global utility)
      { id: 'crop-health', name: 'Crop Health', route: '/crop-health' },
    ],
  },
];

/**
 * Cross-access configuration for pages that appear in multiple workspaces
 */
export const crossAccessPages: CrossAccessConfig[] = [
  { route: '/germplasm', primaryWorkspace: 'breeding', additionalWorkspaces: ['genebank'] },
  { route: '/seedlots', primaryWorkspace: 'breeding', additionalWorkspaces: ['seed-ops'] },
  { route: '/barcode', primaryWorkspace: 'seed-ops', additionalWorkspaces: ['genebank'] },
  { route: '/reports', primaryWorkspace: 'admin', additionalWorkspaces: ['breeding', 'seed-ops', 'research', 'genebank'] },
  { route: '/statistics', primaryWorkspace: 'research', additionalWorkspaces: ['breeding'] },
  { route: '/crop-calendar', primaryWorkspace: 'research', additionalWorkspaces: ['breeding', 'genebank'] },
];

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get a workspace by ID
 */
export function getWorkspace(id: WorkspaceId): Workspace | undefined {
  return workspaces.find(w => w.id === id);
}

/**
 * Get all workspaces
 */
export function getAllWorkspaces(): Workspace[] {
  return workspaces;
}

/**
 * Get modules for a specific workspace
 */
export function getWorkspaceModules(workspaceId: WorkspaceId): WorkspaceModule[] {
  return workspaceModules.filter(m => m.workspaces.includes(workspaceId));
}

/**
 * Get a module by ID
 */
export function getModule(moduleId: ModuleId): WorkspaceModule | undefined {
  return workspaceModules.find(m => m.id === moduleId);
}

/**
 * Check if a route is accessible from a workspace
 */
export function isRouteInWorkspace(route: string, workspaceId: WorkspaceId): boolean {
  // Check direct module pages
  const modules = getWorkspaceModules(workspaceId);
  for (const module of modules) {
    if (module.pages.some(p => p.route === route || route.startsWith(p.route.replace(':id', '')))) {
      return true;
    }
  }
  
  // Check cross-access pages
  const crossAccess = crossAccessPages.find(c => c.route === route);
  if (crossAccess) {
    return crossAccess.primaryWorkspace === workspaceId || 
           crossAccess.additionalWorkspaces.includes(workspaceId);
  }
  
  // Global pages are always accessible
  const globalModule = workspaceModules.find(m => m.id === 'global');
  if (globalModule?.pages.some(p => p.route === route)) {
    return true;
  }
  
  return false;
}

/**
 * Get the primary workspace for a route
 */
export function getPrimaryWorkspaceForRoute(route: string): WorkspaceId | null {
  // Check cross-access first
  const crossAccess = crossAccessPages.find(c => c.route === route);
  if (crossAccess) {
    return crossAccess.primaryWorkspace;
  }
  
  // Find first workspace that contains this route
  for (const workspace of workspaces) {
    const modules = getWorkspaceModules(workspace.id);
    for (const module of modules) {
      if (module.pages.some(p => p.route === route || route.startsWith(p.route.replace(':id', '')))) {
        return workspace.id;
      }
    }
  }
  
  return null;
}

/**
 * Get all routes for a workspace
 */
export function getWorkspaceRoutes(workspaceId: WorkspaceId): string[] {
  const modules = getWorkspaceModules(workspaceId);
  const routes: string[] = [];
  
  for (const module of modules) {
    for (const page of module.pages) {
      routes.push(page.route);
    }
  }
  
  // Add cross-access routes
  for (const crossAccess of crossAccessPages) {
    if (crossAccess.additionalWorkspaces.includes(workspaceId) && !routes.includes(crossAccess.route)) {
      routes.push(crossAccess.route);
    }
  }
  
  return routes;
}

/**
 * Get workspace statistics
 */
export function getWorkspaceStats(workspaceId: WorkspaceId): { pageCount: number; moduleCount: number } {
  const modules = getWorkspaceModules(workspaceId);
  const pageCount = modules.reduce((sum, m) => sum + m.pages.length, 0);
  return { pageCount, moduleCount: modules.length };
}
