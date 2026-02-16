/**
 * Future Workspaces Registry
 * 
 * Strategic placeholders for BijMantra's expansion roadmap.
 * These workspaces represent planned capabilities that will attract
 * global talent while clearly marking them as future development.
 * 
 * @see docs/gupt/1-future.md for full roadmap
 * 
 * IMPORTANT: All future workspaces are marked with status: 'planned'
 * and will display "Coming Soon" badges in the UI.
 */

import type { WorkspaceId } from '@/types/workspace';

/**
 * Future workspace identifiers
 * These extend the core WorkspaceId type for planning purposes
 */
export type FutureWorkspaceId = 
  | 'crop-intelligence'      // Tier 1: Crop management & advisories
  | 'soil-nutrients'         // Tier 1: Soil & nutrient intelligence
  | 'crop-protection'        // Tier 1: Pest, disease & stress management
  | 'water-irrigation'       // Tier 1: Water & irrigation intelligence
  | 'market-economics'       // Tier 1: Market & economic intelligence
  | 'sustainability'         // Tier 2: Carbon & sustainability tracking
  | 'farm-operations'        // Tier 2: Farm workflow management
  | 'robotics-automation'    // Tier 2: Agricultural robotics
  | 'post-harvest'           // Tier 2: Supply chain & traceability
  | 'livestock'              // Tier 2: Animal husbandry
  | 'aquaculture';           // Tier 3: Fisheries & aquaculture

/**
 * Development tier classification
 */
export type DevelopmentTier = 'tier-1' | 'tier-2' | 'tier-3' | 'tier-4';

/**
 * Future workspace definition
 */
export interface FutureWorkspace {
  /** Unique identifier */
  id: FutureWorkspaceId;
  
  /** Display name */
  name: string;
  
  /** Short description */
  description: string;
  
  /** Detailed description for hover/modal */
  longDescription: string;
  
  /** Lucide icon name */
  icon: string;
  
  /** Tailwind gradient classes */
  color: string;
  
  /** Background color for cards */
  bgColor: string;
  
  /** Development tier (priority) */
  tier: DevelopmentTier;
  
  /** Estimated timeline */
  timeline: string;
  
  /** Key capabilities (for talent attraction) */
  capabilities: string[];
  
  /** Technologies involved */
  technologies: string[];
  
  /** Target user personas */
  targetUsers: string[];
  
  /** Cross-domain integrations */
  crossDomainIntegrations: string[];
  
  /** Estimated page count when complete */
  estimatedPages: number;
  
  /** Skills needed (for talent attraction) */
  skillsNeeded: string[];
  
  /** Research areas (for academic collaboration) */
  researchAreas: string[];
  
  /** Status - always 'planned' for future workspaces */
  status: 'planned';
}

/**
 * Future workspaces registry
 * Ordered by development tier priority
 */
export const futureWorkspaces: FutureWorkspace[] = [
  // ============================================================================
  // TIER 1: High-Impact Modules (Near-Term) — 2026-2027
  // ============================================================================
  
  {
    id: 'crop-intelligence',
    name: 'Crop Intelligence',
    description: 'Crop selection, calendars, yield prediction',
    longDescription: 'Comprehensive crop management intelligence combining soil, weather, market, and historical data to optimize crop selection, provide growth-stage aware calendars, and deliver accurate yield predictions.',
    icon: 'Wheat',
    color: 'from-lime-500 to-green-600',
    bgColor: 'bg-lime-50 dark:bg-lime-950/30',
    tier: 'tier-1',
    timeline: 'Q2-Q3 2026',
    capabilities: [
      'Crop Selection Optimization',
      'Dynamic Crop Calendars',
      'Phenological Tracking',
      'Yield Forecasting',
      'Crop Suitability Maps',
      'Intercropping Advisor',
      'Variety Recommendation Engine',
    ],
    technologies: [
      'Machine Learning (Yield Prediction)',
      'GIS & Spatial Analysis',
      'Time Series Forecasting',
      'Growing Degree Day Models',
      'Satellite Imagery Integration',
    ],
    targetUsers: ['Agronomists', 'Farm Managers', 'Extension Officers', 'Crop Consultants'],
    crossDomainIntegrations: ['Environment', 'Breeding', 'Economics', 'Soil'],
    estimatedPages: 30,
    skillsNeeded: [
      'Agronomy & Crop Science',
      'Machine Learning / Data Science',
      'GIS & Remote Sensing',
      'Full-Stack Development (React/Python)',
    ],
    researchAreas: [
      'Crop Modeling',
      'Phenology Prediction',
      'G×E Interaction Analysis',
      'Climate-Smart Agriculture',
    ],
    status: 'planned',
  },
  
  {
    id: 'soil-nutrients',
    name: 'Soil & Nutrients',
    description: 'Precision nutrient management & soil health',
    longDescription: 'Transform soil data into actionable recommendations with 4R Nutrient Stewardship, precision fertilizer prescriptions, soil health monitoring, and carbon sequestration tracking.',
    icon: 'Mountain',
    color: 'from-amber-600 to-orange-700',
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
    tier: 'tier-1',
    timeline: 'Q3-Q4 2026',
    capabilities: [
      '4R Nutrient Stewardship Engine',
      'Soil Test Interpretation',
      'Variable Rate Prescription Maps',
      'Nutrient Budget Calculator',
      'Soil Health Scorecard',
      'Carbon Sequestration Estimator',
      'Soil Biology Assessment',
    ],
    technologies: [
      'Precision Agriculture Protocols',
      'ISOBUS Integration',
      'Soil Spectroscopy',
      'Machine Learning (Nutrient Prediction)',
      'GIS & Zone Management',
    ],
    targetUsers: ['Soil Scientists', 'Agronomists', 'Precision Ag Specialists', 'Farm Managers'],
    crossDomainIntegrations: ['Environment', 'Crop Intelligence', 'Economics', 'Sensors'],
    estimatedPages: 25,
    skillsNeeded: [
      'Soil Science & Chemistry',
      'Precision Agriculture',
      'Data Science / ML',
      'GIS Development',
      'IoT Integration',
    ],
    researchAreas: [
      'Soil Carbon Dynamics',
      'Nutrient Use Efficiency',
      'Soil Microbiome',
      'Regenerative Agriculture',
    ],
    status: 'planned',
  },
  
  {
    id: 'crop-protection',
    name: 'Crop Protection',
    description: 'Pest, disease & stress intelligence',
    longDescription: 'Early detection and prediction of pest/disease outbreaks with integrated pest management decision support, spray timing optimization, and resistance management strategies.',
    icon: 'Shield',
    color: 'from-red-500 to-rose-600',
    bgColor: 'bg-red-50 dark:bg-red-950/30',
    tier: 'tier-1',
    timeline: 'Q4 2026 - Q1 2027',
    capabilities: [
      'Disease Prediction Models',
      'Pest Degree Day Calculator',
      'AI Image-Based Diagnosis',
      'IPM Decision Support',
      'Resistance Gene Tracker',
      'Spray Window Calculator',
      'Biological Control Database',
    ],
    technologies: [
      'Computer Vision (Disease Detection)',
      'Weather-Based Disease Models',
      'Degree Day Calculations',
      'Mobile Image Capture',
      'Edge AI Inference',
    ],
    targetUsers: ['Plant Pathologists', 'Entomologists', 'IPM Specialists', 'Crop Scouts'],
    crossDomainIntegrations: ['Environment', 'Genomics', 'Crop Intelligence', 'AI Vision'],
    estimatedPages: 35,
    skillsNeeded: [
      'Plant Pathology',
      'Entomology',
      'Computer Vision / Deep Learning',
      'Epidemiological Modeling',
      'Mobile Development',
    ],
    researchAreas: [
      'Disease Epidemiology',
      'Resistance Durability',
      'Biological Control',
      'Climate-Pest Interactions',
    ],
    status: 'planned',
  },
  
  {
    id: 'water-irrigation',
    name: 'Water & Irrigation',
    description: 'Smart irrigation & water management',
    longDescription: 'Intelligent irrigation scheduling based on crop water demand, evapotranspiration monitoring, water use efficiency optimization, and drought stress prediction.',
    icon: 'Droplets',
    color: 'from-cyan-500 to-blue-600',
    bgColor: 'bg-cyan-50 dark:bg-cyan-950/30',
    tier: 'tier-1',
    timeline: 'Q1-Q2 2027',
    capabilities: [
      'ET Calculator (Penman-Monteith)',
      'Irrigation Scheduler',
      'Soil Moisture Integration',
      'Deficit Irrigation Planner',
      'Water Footprint Calculator',
      'Aquifer Monitoring',
      'Drought Stress Prediction',
    ],
    technologies: [
      'Evapotranspiration Models',
      'Soil Moisture Sensors',
      'Weather API Integration',
      'IoT & LoRaWAN',
      'Hydraulic Modeling',
    ],
    targetUsers: ['Irrigation Engineers', 'Water Managers', 'Farm Managers', 'Hydrologists'],
    crossDomainIntegrations: ['Environment', 'Sensors', 'Crop Intelligence', 'Soil'],
    estimatedPages: 22,
    skillsNeeded: [
      'Hydrology & Water Resources',
      'Irrigation Engineering',
      'IoT & Sensor Integration',
      'Time Series Analysis',
      'Full-Stack Development',
    ],
    researchAreas: [
      'Crop Water Productivity',
      'Deficit Irrigation Strategies',
      'Climate Adaptation',
      'Groundwater Management',
    ],
    status: 'planned',
  },
  
  {
    id: 'market-economics',
    name: 'Market & Economics',
    description: 'Price forecasting & farm profitability',
    longDescription: 'Market price forecasting, farm profitability analysis, input cost optimization, and supply chain visibility to maximize farm economic outcomes.',
    icon: 'TrendingUp',
    color: 'from-emerald-500 to-teal-600',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
    tier: 'tier-1',
    timeline: 'Q2-Q3 2027',
    capabilities: [
      'Price Dashboard & Forecasting',
      'Profitability Calculator',
      'Input Cost Tracker',
      'Market Linkage Platform',
      'Contract Management',
      'Subsidy & Scheme Tracker',
      'Break-Even Analysis',
    ],
    technologies: [
      'Time Series Forecasting',
      'Market Data APIs',
      'Economic Modeling',
      'Dashboard Visualization',
      'Mobile Notifications',
    ],
    targetUsers: ['Farm Managers', 'Agricultural Economists', 'Traders', 'Policy Analysts'],
    crossDomainIntegrations: ['All Modules', 'Crop Intelligence', 'Post-Harvest'],
    estimatedPages: 28,
    skillsNeeded: [
      'Agricultural Economics',
      'Data Science / Econometrics',
      'Market Analysis',
      'Full-Stack Development',
      'API Integration',
    ],
    researchAreas: [
      'Price Volatility Modeling',
      'Supply Chain Economics',
      'Policy Impact Analysis',
      'Risk Management',
    ],
    status: 'planned',
  },
  
  // ============================================================================
  // TIER 2: Strategic Expansion (Mid-Term) — 2027-2028
  // ============================================================================
  
  {
    id: 'sustainability',
    name: 'Sustainability',
    description: 'Carbon tracking & ESG compliance',
    longDescription: 'Carbon footprint calculation, regenerative agriculture practice monitoring, ESG reporting, and sustainability certification support for enterprise compliance.',
    icon: 'Leaf',
    color: 'from-green-600 to-emerald-700',
    bgColor: 'bg-green-50 dark:bg-green-950/30',
    tier: 'tier-2',
    timeline: '2027-2028',
    capabilities: [
      'Carbon Calculator (Scope 1, 2, 3)',
      'Carbon Sequestration Estimator',
      'Regenerative Practice Tracker',
      'Certification Manager',
      'ESG Dashboard',
      'Biodiversity Index',
      'Water Quality Tracker',
    ],
    technologies: [
      'GHG Accounting Standards',
      'Blockchain (Carbon Credits)',
      'Satellite Monitoring',
      'Certification APIs',
      'Reporting Frameworks',
    ],
    targetUsers: ['Sustainability Officers', 'ESG Analysts', 'Certification Auditors', 'Farm Managers'],
    crossDomainIntegrations: ['Soil', 'Crop Intelligence', 'Farm Operations', 'Economics'],
    estimatedPages: 22,
    skillsNeeded: [
      'Environmental Science',
      'Carbon Accounting',
      'Sustainability Reporting',
      'Blockchain Development',
      'Data Visualization',
    ],
    researchAreas: [
      'Carbon Sequestration',
      'Regenerative Agriculture',
      'Ecosystem Services',
      'Life Cycle Assessment',
    ],
    status: 'planned',
  },
  
  {
    id: 'farm-operations',
    name: 'Farm Operations',
    description: 'Workflow management & task execution',
    longDescription: 'Convert intelligence into executable tasks with labor and machinery planning, activity logging for traceability, and compliance documentation.',
    icon: 'ClipboardList',
    color: 'from-slate-500 to-gray-600',
    bgColor: 'bg-slate-50 dark:bg-slate-950/30',
    tier: 'tier-2',
    timeline: '2027-2028',
    capabilities: [
      'AI-Generated Task Lists',
      'Integrated Farm Calendar',
      'Labor Management',
      'Equipment Tracker',
      'Input Inventory',
      'Mobile Activity Logger',
      'Compliance Reporter',
    ],
    technologies: [
      'Task Scheduling Algorithms',
      'Mobile-First PWA',
      'Offline Sync',
      'Calendar Integration',
      'Barcode/QR Scanning',
    ],
    targetUsers: ['Farm Managers', 'Field Supervisors', 'Labor Coordinators', 'Compliance Officers'],
    crossDomainIntegrations: ['All Advisory Modules', 'Environment', 'Economics'],
    estimatedPages: 28,
    skillsNeeded: [
      'Operations Research',
      'Mobile Development',
      'UX Design',
      'Workflow Automation',
      'Full-Stack Development',
    ],
    researchAreas: [
      'Farm Management Systems',
      'Labor Optimization',
      'Traceability Standards',
      'Compliance Automation',
    ],
    status: 'planned',
  },
  
  {
    id: 'robotics-automation',
    name: 'Robotics & Automation',
    description: 'Drones, autonomous equipment & precision application',
    longDescription: 'Drone and UAV mission planning, autonomous equipment coordination, robotic operation monitoring, and precision application management.',
    icon: 'Bot',
    color: 'from-violet-500 to-purple-600',
    bgColor: 'bg-violet-50 dark:bg-violet-950/30',
    tier: 'tier-2',
    timeline: '2028',
    capabilities: [
      'Drone Mission Planner',
      'Imagery Processing Pipeline',
      'Equipment Telemetry Dashboard',
      'Prescription Map Generator',
      'Autonomous Task Coordinator',
      'Spray Drift Calculator',
      'Fleet Management',
    ],
    technologies: [
      'MAVLink / DJI SDK',
      'NDVI/NDRE Processing',
      'ISOBUS Integration',
      'Real-Time Telemetry',
      'Edge Computing',
    ],
    targetUsers: ['Precision Ag Specialists', 'Drone Operators', 'Equipment Managers', 'Agronomists'],
    crossDomainIntegrations: ['Field Operations', 'Sensors', 'Crop Intelligence', 'Crop Protection'],
    estimatedPages: 18,
    skillsNeeded: [
      'Robotics & Automation',
      'Drone/UAV Operations',
      'Computer Vision',
      'GIS & Remote Sensing',
      'Embedded Systems',
    ],
    researchAreas: [
      'Autonomous Agriculture',
      'Swarm Robotics',
      'Precision Application',
      'Computer Vision for Agriculture',
    ],
    status: 'planned',
  },
  
  {
    id: 'post-harvest',
    name: 'Post-Harvest & Supply Chain',
    description: 'Storage, cold chain & traceability',
    longDescription: 'Post-harvest handling optimization, cold chain management, quality preservation, and full traceability through the supply chain.',
    icon: 'Package',
    color: 'from-orange-500 to-amber-600',
    bgColor: 'bg-orange-50 dark:bg-orange-950/30',
    tier: 'tier-2',
    timeline: '2028',
    capabilities: [
      'Harvest Timing Advisor',
      'Storage Condition Monitor',
      'Cold Chain Tracker',
      'Quality Degradation Model',
      'Loss Calculator',
      'Blockchain Traceability',
      'Consumer QR Codes',
    ],
    technologies: [
      'IoT Monitoring',
      'Blockchain',
      'Quality Prediction Models',
      'Mobile Scanning',
      'API Integration',
    ],
    targetUsers: ['Post-Harvest Specialists', 'Supply Chain Managers', 'Quality Controllers', 'Logistics'],
    crossDomainIntegrations: ['Seed Commerce', 'Market Economics', 'Quality', 'Sensors'],
    estimatedPages: 28,
    skillsNeeded: [
      'Food Science',
      'Supply Chain Management',
      'Blockchain Development',
      'IoT Integration',
      'Quality Assurance',
    ],
    researchAreas: [
      'Post-Harvest Loss Reduction',
      'Cold Chain Optimization',
      'Traceability Standards',
      'Quality Prediction',
    ],
    status: 'planned',
  },
  
  {
    id: 'livestock',
    name: 'Livestock & Animal Husbandry',
    description: 'Animal breeding, health & production',
    longDescription: 'Comprehensive livestock management including breeding and genetics, animal health monitoring, feed optimization, and production tracking.',
    icon: 'Beef',
    color: 'from-rose-500 to-pink-600',
    bgColor: 'bg-rose-50 dark:bg-rose-950/30',
    tier: 'tier-2',
    timeline: '2028-2029',
    capabilities: [
      'Animal Registry',
      'Breeding Management',
      'Genomic Selection (EBV/GEBV)',
      'Health Records',
      'Feed Management',
      'Production Tracking',
      'Herd Analytics',
    ],
    technologies: [
      'ICAR Standards',
      'RFID/BLE Tracking',
      'Genomic Analysis',
      'Sensor Integration',
      'Mobile Data Collection',
    ],
    targetUsers: ['Animal Breeders', 'Veterinarians', 'Dairy/Livestock Managers', 'Nutritionists'],
    crossDomainIntegrations: ['Environment', 'Feed/Nutrition', 'Economics', 'Health'],
    estimatedPages: 40,
    skillsNeeded: [
      'Animal Science',
      'Veterinary Medicine',
      'Quantitative Genetics',
      'IoT & Sensor Integration',
      'Full-Stack Development',
    ],
    researchAreas: [
      'Animal Genomics',
      'Precision Livestock Farming',
      'Animal Welfare',
      'Feed Efficiency',
    ],
    status: 'planned',
  },
  
  // ============================================================================
  // TIER 3: Advanced Research (Long-Term) — 2029+
  // ============================================================================
  
  {
    id: 'aquaculture',
    name: 'Aquaculture & Fisheries',
    description: 'Fish production & water quality management',
    longDescription: 'Fish and shellfish production management, water quality monitoring, feed optimization, and disease management for aquaculture operations.',
    icon: 'Fish',
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    tier: 'tier-3',
    timeline: '2029+',
    capabilities: [
      'Pond/Tank Management',
      'Water Quality Dashboard',
      'Feed Calculator',
      'Growth Tracker',
      'Disease Surveillance',
      'Harvest Planner',
      'Broodstock Management',
    ],
    technologies: [
      'Water Quality Sensors',
      'Growth Modeling',
      'Disease Prediction',
      'IoT Integration',
      'Mobile Monitoring',
    ],
    targetUsers: ['Aquaculture Managers', 'Fisheries Scientists', 'Hatchery Operators', 'Feed Specialists'],
    crossDomainIntegrations: ['Water Quality', 'Environment', 'Economics', 'Health'],
    estimatedPages: 28,
    skillsNeeded: [
      'Aquaculture Science',
      'Fisheries Biology',
      'Water Quality Management',
      'IoT & Sensor Integration',
      'Full-Stack Development',
    ],
    researchAreas: [
      'Sustainable Aquaculture',
      'Fish Genetics',
      'Disease Management',
      'Feed Optimization',
    ],
    status: 'planned',
  },
];

/**
 * Get future workspaces by tier
 */
export function getFutureWorkspacesByTier(tier: DevelopmentTier): FutureWorkspace[] {
  return futureWorkspaces.filter(w => w.tier === tier);
}

/**
 * Get all future workspace IDs
 */
export function getFutureWorkspaceIds(): FutureWorkspaceId[] {
  return futureWorkspaces.map(w => w.id);
}

/**
 * Get a specific future workspace by ID
 */
export function getFutureWorkspace(id: FutureWorkspaceId): FutureWorkspace | undefined {
  return futureWorkspaces.find(w => w.id === id);
}

/**
 * Tier display names and descriptions
 */
export const tierInfo: Record<DevelopmentTier, { name: string; description: string; timeline: string }> = {
  'tier-1': {
    name: 'Foundation Modules',
    description: 'High-impact modules for core agricultural intelligence',
    timeline: '2026-2027',
  },
  'tier-2': {
    name: 'Strategic Expansion',
    description: 'Enterprise features and cross-domain integration',
    timeline: '2027-2028',
  },
  'tier-3': {
    name: 'Advanced Research',
    description: 'Specialized domains and emerging technologies',
    timeline: '2029+',
  },
  'tier-4': {
    name: 'Future Technologies',
    description: 'Quantum computing, digital twins, and beyond',
    timeline: '2030+',
  },
};

/**
 * Total statistics for future development
 */
export const futureStats = {
  totalWorkspaces: futureWorkspaces.length,
  totalEstimatedPages: futureWorkspaces.reduce((sum, w) => sum + w.estimatedPages, 0),
  tier1Count: getFutureWorkspacesByTier('tier-1').length,
  tier2Count: getFutureWorkspacesByTier('tier-2').length,
  tier3Count: getFutureWorkspacesByTier('tier-3').length,
};
