/**
 * Future Divisions Registry
 * 
 * Placeholder divisions for the MAHASARTHI navigation system.
 * These appear in the browser with "Coming Soon" badges to showcase
 * BijMantra's expansion roadmap and attract contributors.
 * 
 * @see docs/gupt/1-future.md for full roadmap
 */

import type { Division } from './types';
import type { ComponentType, LazyExoticComponent } from 'react';

/**
 * Future division status type
 */
export type FutureDivisionStatus = 'planned' | 'in-development' | 'alpha';

/**
 * Extended division type for future modules
 */
export interface FutureDivision extends Omit<Division, 'component' | 'status'> {
  /** Status is always planned/in-development for future divisions */
  status: FutureDivisionStatus;
  
  /** Development tier */
  tier: 'tier-1' | 'tier-2' | 'tier-3' | 'tier-4';
  
  /** Estimated timeline */
  timeline: string;
  
  /** Key capabilities preview */
  capabilities: string[];
  
  /** Skills needed for contribution */
  skillsNeeded: string[];
  
  /** 
   * Placeholder component - set to null here, actual component assigned in App.tsx
   * This avoids circular dependency with FuturePlaceholder.tsx
   */
  component: LazyExoticComponent<ComponentType<unknown>> | null;
}

/**
 * Future divisions registry
 * These will appear in MAHASARTHI browser with "Coming Soon" badges
 */
export const futureDivisions: FutureDivision[] = [
  // ============================================================================
  // TIER 1: Foundation Modules (2026-2027)
  // ============================================================================
  
  {
    id: 'crop-intelligence',
    name: 'Crop Intelligence',
    description: 'Crop selection, calendars, yield prediction, and variety recommendations',
    icon: 'Wheat',
    route: '/crop-intelligence',
    component: null,
    requiredPermissions: ['read:crop_intelligence'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-1',
    timeline: 'Q2-Q3 2026',
    capabilities: [
      'Crop Selection Optimization',
      'Dynamic Crop Calendars',
      'Yield Forecasting',
      'Variety Recommendation',
    ],
    skillsNeeded: ['Agronomy', 'Machine Learning', 'GIS'],
    sections: [
      {
        id: 'crop-selection',
        name: 'Crop Selection',
        route: '/crop-intelligence/selection',
        icon: 'Target',
        isAbsolute: true,
        items: [
          { id: 'optimizer', name: 'Selection Optimizer', route: '/crop-intelligence/selection', isAbsolute: true },
          { id: 'suitability', name: 'Suitability Maps', route: '/crop-intelligence/suitability', isAbsolute: true },
          { id: 'rotation', name: 'Rotation Planner', route: '/crop-intelligence/rotation', isAbsolute: true },
        ],
      },
      {
        id: 'calendars',
        name: 'Crop Calendars',
        route: '/crop-intelligence/calendars',
        icon: 'Calendar',
        isAbsolute: true,
        items: [
          { id: 'dynamic-calendar', name: 'Dynamic Calendar', route: '/crop-intelligence/calendars', isAbsolute: true },
          { id: 'phenology', name: 'Phenology Tracker', route: '/crop-intelligence/phenology', isAbsolute: true },
          { id: 'gdd', name: 'GDD Calculator', route: '/crop-intelligence/gdd', isAbsolute: true },
        ],
      },
      {
        id: 'yield',
        name: 'Yield Prediction',
        route: '/crop-intelligence/yield',
        icon: 'TrendingUp',
        isAbsolute: true,
        items: [
          { id: 'forecaster', name: 'Yield Forecaster', route: '/crop-intelligence/yield', isAbsolute: true },
          { id: 'factors', name: 'Yield Factors', route: '/crop-intelligence/factors', isAbsolute: true },
          { id: 'historical', name: 'Historical Analysis', route: '/crop-intelligence/historical', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'soil-nutrients',
    name: 'Soil & Nutrients',
    description: 'Precision nutrient management, soil health, and fertilizer optimization',
    icon: 'Mountain',
    route: '/soil-nutrients',
    component: null,
    requiredPermissions: ['read:soil_nutrients'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-1',
    timeline: 'Q3-Q4 2026',
    capabilities: [
      '4R Nutrient Stewardship',
      'Soil Test Interpretation',
      'Variable Rate Prescriptions',
      'Carbon Tracking',
    ],
    skillsNeeded: ['Soil Science', 'Precision Ag', 'Data Science'],
    sections: [
      {
        id: 'nutrient-management',
        name: 'Nutrient Management',
        route: '/soil-nutrients/nutrients',
        icon: 'Beaker',
        isAbsolute: true,
        items: [
          { id: 'dashboard', name: 'Dashboard', route: '/soil-nutrients', isAbsolute: true },
          { id: 'soil-tests', name: 'Soil Tests', route: '/soil-nutrients/soil-tests', isAbsolute: true },
          { id: '4r-engine', name: '4R Stewardship', route: '/soil-nutrients/4r', isAbsolute: true },
          { id: 'prescriptions', name: 'VR Prescriptions', route: '/soil-nutrients/prescriptions', isAbsolute: true },
        ],
      },
      {
        id: 'soil-health',
        name: 'Soil Health',
        route: '/soil-nutrients/health',
        icon: 'Heart',
        isAbsolute: true,
        items: [
          { id: 'scorecard', name: 'Health Scorecard', route: '/soil-nutrients/soil-health', isAbsolute: true },
          { id: 'biology', name: 'Soil Biology', route: '/soil-nutrients/biology', isAbsolute: true },
          { id: 'carbon', name: 'Carbon Tracker', route: '/soil-nutrients/carbon', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'crop-protection',
    name: 'Crop Protection',
    description: 'Pest & disease prediction, IPM decision support, and resistance management',
    icon: 'Shield',
    route: '/crop-protection',
    component: null,
    requiredPermissions: ['read:crop_protection'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-1',
    timeline: 'Q4 2026 - Q1 2027',
    capabilities: [
      'Disease Prediction Models',
      'AI Image Diagnosis',
      'IPM Decision Support',
      'Resistance Tracking',
    ],
    skillsNeeded: ['Plant Pathology', 'Entomology', 'Computer Vision'],
    sections: [
      {
        id: 'disease',
        name: 'Disease Management',
        route: '/crop-protection/disease',
        icon: 'Bug',
        isAbsolute: true,
        items: [
          { id: 'predictor', name: 'Disease Predictor', route: '/crop-protection/disease', isAbsolute: true },
          { id: 'diagnosis', name: 'AI Diagnosis', route: '/crop-protection/diagnosis', isAbsolute: true },
          { id: 'resistance', name: 'Resistance Tracker', route: '/crop-protection/resistance', isAbsolute: true },
        ],
      },
      {
        id: 'pest',
        name: 'Pest Management',
        route: '/crop-protection/pest',
        icon: 'Bug',
        isAbsolute: true,
        items: [
          { id: 'degree-days', name: 'Degree Day Calculator', route: '/crop-protection/degree-days', isAbsolute: true },
          { id: 'scouting', name: 'Scouting Guide', route: '/crop-protection/scouting', isAbsolute: true },
          { id: 'biocontrol', name: 'Biocontrol Database', route: '/crop-protection/biocontrol', isAbsolute: true },
        ],
      },
      {
        id: 'ipm',
        name: 'IPM',
        route: '/crop-protection/ipm',
        icon: 'Target',
        isAbsolute: true,
        items: [
          { id: 'decision-support', name: 'Decision Support', route: '/crop-protection/ipm', isAbsolute: true },
          { id: 'spray-window', name: 'Spray Window', route: '/crop-protection/spray', isAbsolute: true },
          { id: 'thresholds', name: 'Economic Thresholds', route: '/crop-protection/thresholds', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'water-irrigation',
    name: 'Water & Irrigation',
    description: 'Smart irrigation scheduling, ET monitoring, and water use efficiency',
    icon: 'Droplets',
    route: '/water-irrigation',
    component: null,
    requiredPermissions: ['read:water_irrigation'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-1',
    timeline: 'Q1-Q2 2027',
    capabilities: [
      'ET Calculator',
      'Irrigation Scheduler',
      'Soil Moisture Integration',
      'Drought Prediction',
    ],
    skillsNeeded: ['Hydrology', 'Irrigation Engineering', 'IoT'],
    sections: [
      {
        id: 'irrigation',
        name: 'Irrigation',
        route: '/water-irrigation/schedules',
        icon: 'Droplets',
        isAbsolute: true,
        items: [
          { id: 'scheduler', name: 'Irrigation Schedules', route: '/water-irrigation/schedules', isAbsolute: true },
          { id: 'water-balance', name: 'Water Balance', route: '/water-irrigation/balance', isAbsolute: true },
          { id: 'et-calculator', name: 'ET Calculator', route: '/water-irrigation/et', isAbsolute: true },
          { id: 'deficit', name: 'Deficit Irrigation', route: '/water-irrigation/deficit', isAbsolute: true },
        ],
      },
      {
        id: 'monitoring',
        name: 'Monitoring',
        route: '/water-irrigation/monitoring',
        icon: 'Activity',
        isAbsolute: true,
        items: [
          { id: 'soil-moisture', name: 'Soil Moisture', route: '/water-irrigation/moisture', isAbsolute: true },
          { id: 'aquifer', name: 'Aquifer Monitor', route: '/water-irrigation/aquifer', isAbsolute: true },
          { id: 'footprint', name: 'Water Footprint', route: '/water-irrigation/footprint', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'market-economics',
    name: 'Market & Economics',
    description: 'Price forecasting, profitability analysis, and market intelligence',
    icon: 'TrendingUp',
    route: '/market-economics',
    component: null,
    requiredPermissions: ['read:market_economics'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-1',
    timeline: 'Q2-Q3 2027',
    capabilities: [
      'Price Forecasting',
      'Profitability Calculator',
      'Market Linkage',
      'Contract Management',
    ],
    skillsNeeded: ['Agricultural Economics', 'Data Science', 'Market Analysis'],
    sections: [
      {
        id: 'prices',
        name: 'Prices',
        route: '/market-economics/prices',
        icon: 'DollarSign',
        isAbsolute: true,
        items: [
          { id: 'dashboard', name: 'Price Dashboard', route: '/market-economics/prices', isAbsolute: true },
          { id: 'forecast', name: 'Price Forecast', route: '/market-economics/forecast', isAbsolute: true },
          { id: 'alerts', name: 'Price Alerts', route: '/market-economics/alerts', isAbsolute: true },
        ],
      },
      {
        id: 'profitability',
        name: 'Profitability',
        route: '/market-economics/profitability',
        icon: 'Calculator',
        isAbsolute: true,
        items: [
          { id: 'calculator', name: 'Profit Calculator', route: '/market-economics/calculator', isAbsolute: true },
          { id: 'breakeven', name: 'Break-Even Analysis', route: '/market-economics/breakeven', isAbsolute: true },
          { id: 'costs', name: 'Input Costs', route: '/market-economics/costs', isAbsolute: true },
        ],
      },
    ],
  },
  
  // ============================================================================
  // TIER 2: Strategic Expansion (2027-2028)
  // ============================================================================
  
  {
    id: 'sustainability',
    name: 'Sustainability',
    description: 'Carbon tracking, ESG compliance, and regenerative agriculture',
    icon: 'Leaf',
    route: '/sustainability',
    component: null,
    requiredPermissions: ['read:sustainability'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-2',
    timeline: '2027-2028',
    capabilities: [
      'Carbon Calculator',
      'ESG Dashboard',
      'Certification Manager',
      'Biodiversity Index',
    ],
    skillsNeeded: ['Environmental Science', 'Carbon Accounting', 'Sustainability'],
    sections: [
      {
        id: 'carbon',
        name: 'Carbon',
        route: '/sustainability/carbon',
        icon: 'Leaf',
        isAbsolute: true,
        items: [
          { id: 'calculator', name: 'Carbon Calculator', route: '/sustainability/carbon', isAbsolute: true },
          { id: 'sequestration', name: 'Sequestration', route: '/sustainability/sequestration', isAbsolute: true },
          { id: 'credits', name: 'Carbon Credits', route: '/sustainability/credits', isAbsolute: true },
        ],
      },
      {
        id: 'compliance',
        name: 'Compliance',
        route: '/sustainability/compliance',
        icon: 'FileCheck',
        isAbsolute: true,
        items: [
          { id: 'esg', name: 'ESG Dashboard', route: '/sustainability/esg', isAbsolute: true },
          { id: 'certifications', name: 'Certifications', route: '/sustainability/certifications', isAbsolute: true },
          { id: 'reports', name: 'Sustainability Reports', route: '/sustainability/reports', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'farm-operations',
    name: 'Farm Operations',
    description: 'Workflow management, task execution, and compliance documentation',
    icon: 'ClipboardList',
    route: '/farm-operations',
    component: null,
    requiredPermissions: ['read:farm_operations'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-2',
    timeline: '2027-2028',
    capabilities: [
      'AI Task Lists',
      'Farm Calendar',
      'Labor Management',
      'Compliance Reporter',
    ],
    skillsNeeded: ['Operations Research', 'Mobile Development', 'UX Design'],
    sections: [
      {
        id: 'tasks',
        name: 'Tasks',
        route: '/farm-operations/tasks',
        icon: 'CheckSquare',
        isAbsolute: true,
        items: [
          { id: 'task-list', name: 'Task List', route: '/farm-operations/tasks', isAbsolute: true },
          { id: 'calendar', name: 'Farm Calendar', route: '/farm-operations/calendar', isAbsolute: true },
          { id: 'activity-log', name: 'Activity Log', route: '/farm-operations/log', isAbsolute: true },
        ],
      },
      {
        id: 'resources',
        name: 'Resources',
        route: '/farm-operations/resources',
        icon: 'Users',
        isAbsolute: true,
        items: [
          { id: 'labor', name: 'Labor Management', route: '/farm-operations/labor', isAbsolute: true },
          { id: 'equipment', name: 'Equipment Tracker', route: '/farm-operations/equipment', isAbsolute: true },
          { id: 'inventory', name: 'Input Inventory', route: '/farm-operations/inventory', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'robotics-automation',
    name: 'Robotics & Automation',
    description: 'Drone operations, autonomous equipment, and precision application',
    icon: 'Bot',
    route: '/robotics',
    component: null,
    requiredPermissions: ['read:robotics'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-2',
    timeline: '2028',
    capabilities: [
      'Drone Mission Planner',
      'Imagery Processing',
      'Fleet Management',
      'Prescription Maps',
    ],
    skillsNeeded: ['Robotics', 'Computer Vision', 'GIS', 'Embedded Systems'],
    sections: [
      {
        id: 'drones',
        name: 'Drones',
        route: '/robotics/drones',
        icon: 'Plane',
        isAbsolute: true,
        items: [
          { id: 'missions', name: 'Mission Planner', route: '/robotics/missions', isAbsolute: true },
          { id: 'imagery', name: 'Imagery Processing', route: '/robotics/imagery', isAbsolute: true },
          { id: 'fleet', name: 'Fleet Management', route: '/robotics/fleet', isAbsolute: true },
        ],
      },
      {
        id: 'precision',
        name: 'Precision Application',
        route: '/robotics/precision',
        icon: 'Target',
        isAbsolute: true,
        items: [
          { id: 'prescriptions', name: 'Prescription Maps', route: '/robotics/prescriptions', isAbsolute: true },
          { id: 'telemetry', name: 'Equipment Telemetry', route: '/robotics/telemetry', isAbsolute: true },
          { id: 'spray-drift', name: 'Spray Drift Calculator', route: '/robotics/spray-drift', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'post-harvest',
    name: 'Post-Harvest & Supply Chain',
    description: 'Storage optimization, cold chain tracking, and traceability',
    icon: 'Package',
    route: '/post-harvest',
    component: null,
    requiredPermissions: ['read:post_harvest'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-2',
    timeline: '2028',
    capabilities: [
      'Harvest Timing Advisor',
      'Cold Chain Tracker',
      'Quality Prediction',
      'Blockchain Traceability',
    ],
    skillsNeeded: ['Food Science', 'Supply Chain', 'Blockchain', 'IoT'],
    sections: [
      {
        id: 'storage',
        name: 'Storage',
        route: '/post-harvest/storage',
        icon: 'Warehouse',
        isAbsolute: true,
        items: [
          { id: 'conditions', name: 'Storage Conditions', route: '/post-harvest/conditions', isAbsolute: true },
          { id: 'cold-chain', name: 'Cold Chain', route: '/post-harvest/cold-chain', isAbsolute: true },
          { id: 'quality', name: 'Quality Prediction', route: '/post-harvest/quality', isAbsolute: true },
        ],
      },
      {
        id: 'traceability',
        name: 'Traceability',
        route: '/post-harvest/traceability',
        icon: 'QrCode',
        isAbsolute: true,
        items: [
          { id: 'blockchain', name: 'Blockchain Records', route: '/post-harvest/blockchain', isAbsolute: true },
          { id: 'qr-codes', name: 'Consumer QR Codes', route: '/post-harvest/qr', isAbsolute: true },
          { id: 'loss-calculator', name: 'Loss Calculator', route: '/post-harvest/loss', isAbsolute: true },
        ],
      },
    ],
  },
  
  {
    id: 'livestock',
    name: 'Livestock & Animal Husbandry',
    description: 'Animal breeding, health monitoring, and production tracking',
    icon: 'Beef',
    route: '/livestock',
    component: null,
    requiredPermissions: ['read:livestock'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-2',
    timeline: '2028-2029',
    capabilities: [
      'Animal Registry',
      'Genomic Selection (EBV)',
      'Health Records',
      'Feed Management',
    ],
    skillsNeeded: ['Animal Science', 'Veterinary', 'Quantitative Genetics', 'IoT'],
    sections: [
      {
        id: 'breeding',
        name: 'Breeding',
        route: '/livestock/breeding',
        icon: 'Dna',
        isAbsolute: true,
        items: [
          { id: 'registry', name: 'Animal Registry', route: '/livestock/registry', isAbsolute: true },
          { id: 'mating', name: 'Mating Plans', route: '/livestock/mating', isAbsolute: true },
          { id: 'ebv', name: 'EBV Calculator', route: '/livestock/ebv', isAbsolute: true },
        ],
      },
      {
        id: 'health',
        name: 'Health',
        route: '/livestock/health',
        icon: 'Heart',
        isAbsolute: true,
        items: [
          { id: 'records', name: 'Health Records', route: '/livestock/health', isAbsolute: true },
          { id: 'vaccination', name: 'Vaccination', route: '/livestock/vaccination', isAbsolute: true },
          { id: 'monitoring', name: 'Health Monitoring', route: '/livestock/monitoring', isAbsolute: true },
        ],
      },
      {
        id: 'production',
        name: 'Production',
        route: '/livestock/production',
        icon: 'BarChart3',
        isAbsolute: true,
        items: [
          { id: 'tracking', name: 'Production Tracking', route: '/livestock/production', isAbsolute: true },
          { id: 'feed', name: 'Feed Management', route: '/livestock/feed', isAbsolute: true },
          { id: 'analytics', name: 'Herd Analytics', route: '/livestock/analytics', isAbsolute: true },
        ],
      },
    ],
  },
  
  // ============================================================================
  // TIER 3: Advanced Research (2029+)
  // ============================================================================
  
  {
    id: 'aquaculture',
    name: 'Aquaculture & Fisheries',
    description: 'Fish production, water quality management, and disease surveillance',
    icon: 'Fish',
    route: '/aquaculture',
    component: null,
    requiredPermissions: ['read:aquaculture'],
    status: 'planned',
    version: '0.0.0',
    tier: 'tier-3',
    timeline: '2029+',
    capabilities: [
      'Pond/Tank Management',
      'Water Quality Dashboard',
      'Growth Tracking',
      'Disease Surveillance',
    ],
    skillsNeeded: ['Aquaculture Science', 'Fisheries Biology', 'Water Quality', 'IoT'],
    sections: [
      {
        id: 'production',
        name: 'Production',
        route: '/aquaculture/production',
        icon: 'Fish',
        isAbsolute: true,
        items: [
          { id: 'ponds', name: 'Pond Management', route: '/aquaculture/ponds', isAbsolute: true },
          { id: 'growth', name: 'Growth Tracker', route: '/aquaculture/growth', isAbsolute: true },
          { id: 'harvest', name: 'Harvest Planner', route: '/aquaculture/harvest', isAbsolute: true },
        ],
      },
      {
        id: 'water-quality',
        name: 'Water Quality',
        route: '/aquaculture/water',
        icon: 'Droplets',
        isAbsolute: true,
        items: [
          { id: 'dashboard', name: 'Quality Dashboard', route: '/aquaculture/water', isAbsolute: true },
          { id: 'sensors', name: 'Sensor Integration', route: '/aquaculture/sensors', isAbsolute: true },
          { id: 'alerts', name: 'Quality Alerts', route: '/aquaculture/alerts', isAbsolute: true },
        ],
      },
    ],
  },
];

/**
 * Get future divisions by tier
 */
export function getFutureDivisionsByTier(tier: FutureDivision['tier']): FutureDivision[] {
  return futureDivisions.filter(d => d.tier === tier);
}

/**
 * Get all future division IDs
 */
export function getFutureDivisionIds(): string[] {
  return futureDivisions.map(d => d.id);
}

/**
 * Check if a division ID is a future division
 */
export function isFutureDivision(id: string): boolean {
  return futureDivisions.some(d => d.id === id);
}

/**
 * Get a specific future division by ID
 */
export function getFutureDivision(id: string): FutureDivision | undefined {
  return futureDivisions.find(d => d.id === id);
}
