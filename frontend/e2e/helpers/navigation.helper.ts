/**
 * Navigation Helper
 * 
 * Centralized navigation utilities for E2E tests:
 * - Route definitions
 * - Navigation methods
 * - URL validation
 */

import { Page, expect } from '@playwright/test'

// Complete route definitions for all 221 pages
export const ROUTES = {
  // Public routes
  login: '/login',
  
  // Gateway
  gateway: '/gateway',
  
  // Workspace Dashboards
  workspaces: {
    breeding: '/breeding/dashboard',
    seedOps: '/seed-ops/dashboard',
    research: '/research/dashboard',
    genebank: '/genebank/dashboard',
    admin: '/admin/dashboard',
  },
  
  // Core routes
  dashboard: '/dashboard',
  profile: '/profile',
  settings: '/settings',
  search: '/search',
  
  // Breeding Module
  breeding: {
    programs: '/programs',
    programNew: '/programs/new',
    trials: '/trials',
    trialNew: '/trials/new',
    studies: '/studies',
    studyNew: '/studies/new',
    crosses: '/crosses',
    crossNew: '/crosses/new',
    crossingProjects: '/crossingprojects',
    plannedCrosses: '/plannedcrosses',
    crossingPlanner: '/crossingplanner',
    pipeline: '/pipeline',
    goals: '/breeding-goals',
    history: '/breeding-history',
    simulator: '/breeding-simulator',
    values: '/breeding-values',
    valueCalculator: '/breeding-value-calculator',
  },
  
  // Phenotyping Module
  phenotyping: {
    traits: '/traits',
    traitNew: '/traits/new',
    observations: '/observations',
    observationUnits: '/observationunits',
    dataCollect: '/observations/collect',
    fieldLayout: '/fieldlayout',
    fieldBook: '/fieldbook',
    fieldMap: '/fieldmap',
    fieldPlanning: '/fieldplanning',
    phenologyTracker: '/phenology',
    phenotypeAnalysis: '/phenotype-analysis',
    phenotypeComparison: '/comparison',
  },
  
  // Genomics Module
  genomics: {
    samples: '/samples',
    sampleNew: '/samples/new',
    variants: '/variants',
    variantSets: '/variantsets',
    calls: '/calls',
    callSets: '/callsets',
    alleleMatrix: '/allelematrix',
    plates: '/plates',
    references: '/references',
    genomeMaps: '/genomemaps',
    markerPositions: '/markerpositions',
    geneticDiversity: '/genetic-diversity',
    qtlMapping: '/qtl-mapping',
    genomicSelection: '/genomic-selection',
    markerAssistedSelection: '/marker-assisted-selection',
    haplotypeAnalysis: '/haplotype-analysis',
    linkageDisequilibrium: '/linkage-disequilibrium',
    populationGenetics: '/population-genetics',
    parentageAnalysis: '/parentage-analysis',
    geneticCorrelation: '/genetic-correlation',
    molecularBreeding: '/molecular-breeding',
    bioinformatics: '/bioinformatics',
  },
  
  // Germplasm Module
  germplasm: {
    list: '/germplasm',
    new: '/germplasm/new',
    search: '/germplasm-search',
    comparison: '/germplasm-comparison',
    collection: '/collections',
    attributes: '/germplasmattributes',
    attributeValues: '/attributevalues',
    passport: '/germplasm-passport',
    pedigree: '/pedigree',
    pedigree3D: '/pedigree-3d',
    pedigreeAnalysis: '/pedigree-analysis',
    progeny: '/progeny',
  },
  
  // Seed Bank Module
  seedBank: {
    dashboard: '/seed-bank',
    vault: '/seed-bank/vault',
    accessions: '/seed-bank/accessions',
    accessionNew: '/seed-bank/accessions/new',
    conservation: '/seed-bank/conservation',
    viability: '/seed-bank/viability',
    regeneration: '/seed-bank/regeneration',
    exchange: '/seed-bank/exchange',
    mcpd: '/seed-bank/mcpd',
    grinSearch: '/seed-bank/grin-search',
    taxonomy: '/seed-bank/taxonomy',
    mta: '/seed-bank/mta',
    monitoring: '/seed-bank/monitoring',
    offline: '/seed-bank/offline',
    geneBank: '/genebank',
  },
  
  // Seed Operations Module
  seedOperations: {
    dashboard: '/seed-operations',
    samples: '/seed-operations/samples',
    testing: '/seed-operations/testing',
    certificates: '/seed-operations/certificates',
    qualityGate: '/seed-operations/quality-gate',
    batches: '/seed-operations/batches',
    stages: '/seed-operations/stages',
    lots: '/seed-operations/lots',
    warehouse: '/seed-operations/warehouse',
    alerts: '/seed-operations/alerts',
    dispatch: '/seed-operations/dispatch',
    dispatchHistory: '/seed-operations/dispatch-history',
    firms: '/seed-operations/firms',
    track: '/seed-operations/track',
    lineage: '/seed-operations/lineage',
    varieties: '/seed-operations/varieties',
    agreements: '/seed-operations/agreements',
    seedLots: '/seedlots',
    seedLotNew: '/seedlots/new',
    seedInventory: '/inventory',
    seedRequest: '/seedrequest',
  },
  
  // Environment Module
  environment: {
    dashboard: '/earth-systems',
    weather: '/weather',
    weatherForecast: '/earth-systems/weather',
    climate: '/earth-systems/climate',
    soil: '/earth-systems/soil',
    soilAnalysis: '/soil',
    inputs: '/earth-systems/inputs',
    irrigation: '/earth-systems/irrigation',
    irrigationPlanner: '/irrigation-planner',
    gdd: '/earth-systems/gdd',
    drought: '/earth-systems/drought',
    map: '/earth-systems/map',
    environmentMonitor: '/environment-monitor',
  },
  
  // Analysis & Statistics
  analysis: {
    statistics: '/statistics',
    reports: '/reports',
    advancedReports: '/advanced-reports',
    dataVisualization: '/data-visualization',
    analytics: '/analytics-dashboard',
    insights: '/insights-dashboard',
    apex: '/apex-analytics',
    gxeInteraction: '/gxe-interaction',
    stabilityAnalysis: '/stability-analysis',
    geneticGain: '/geneticgain',
    geneticGainTracker: '/genetic-gain-tracker',
    geneticGainCalculator: '/genetic-gain-calculator',
    selectionIndex: '/selectionindex',
    selectionIndexCalculator: '/selection-index-calculator',
    trialDesign: '/trialdesign',
    trialComparison: '/trial-comparison',
    trialNetwork: '/trial-network',
    trialPlanning: '/trialplanning',
    trialSummary: '/trial-summary',
    spatialAnalysis: '/spatial-analysis',
    performanceRanking: '/performance-ranking',
  },
  
  // Commercial Module
  commercial: {
    dashboard: '/commercial',
    dusTrials: '/commercial/dus-trials',
    dusCrops: '/commercial/dus-crops',
    varietyRelease: '/variety-release',
    varietyComparison: '/varietycomparison',
    marketAnalysis: '/market-analysis',
    costAnalysis: '/cost-analysis',
  },
  
  // Knowledge Module
  knowledge: {
    forums: '/knowledge/forums',
    forumNew: '/knowledge/forums/new',
    training: '/knowledge/training',
    trainingHub: '/training-hub',
    protocolLibrary: '/protocol-library',
    glossary: '/glossary',
    faq: '/faq',
    helpCenter: '/help',
    quickGuide: '/quick-guide',
  },
  
  // Admin & Settings
  admin: {
    users: '/users',
    teamManagement: '/team-management',
    systemSettings: '/system-settings',
    systemHealth: '/system-health',
    security: '/security',
    auditLog: '/auditlog',
    backup: '/backup',
    dataQuality: '/dataquality',
    apiExplorer: '/api-explorer',
    serverInfo: '/serverinfo',
    devProgress: '/dev-progress',
  },
  
  // Integrations
  integrations: {
    hub: '/integrations',
    barcode: '/barcode',
    scanner: '/scanner',
    importExport: '/import-export',
    dataSync: '/data-sync',
    iotSensors: '/iot-sensors',
    droneIntegration: '/drone-integration',
    blockchain: '/blockchain-traceability',
  },
  
  // AI & Tools
  ai: {
    veena: '/veena',
    assistant: '/ai-assistant',
    settings: '/ai-settings',
    chromeAI: '/chrome-ai',
    devGuru: '/devguru',
  },
  
  // WASM Compute
  wasm: {
    genomics: '/wasm-genomics',
    gblup: '/wasm-gblup',
    popGen: '/wasm-popgen',
    ldAnalysis: '/wasm-ld-analysis',
    selectionIndex: '/wasm-selection-index',
  },
  
  // Vision & Imaging
  vision: {
    main: '/vision',
    dashboard: '/vision-dashboard',
    datasets: '/vision-datasets',
    training: '/vision-training',
    registry: '/vision-registry',
    annotate: '/vision-annotate',
    plantVision: '/plant-vision',
    fieldScanner: '/field-scanner',
    cropHealth: '/crop-health-dashboard',
  },
  
  // Sensor Networks
  sensors: {
    dashboard: '/sensor-networks',
    devices: '/sensor-networks/devices',
    live: '/sensor-networks/live',
    alerts: '/sensor-networks/alerts',
  },
  
  // Sun-Earth Systems
  sunEarth: {
    dashboard: '/sun-earth-systems',
    solarActivity: '/sun-earth-systems/solar-activity',
    photoperiod: '/sun-earth-systems/photoperiod',
    uvIndex: '/sun-earth-systems/uv-index',
  },
  
  // Space Research
  space: {
    dashboard: '/space-research',
    crops: '/space-research/crops',
    radiation: '/space-research/radiation',
    lifeSupport: '/space-research/life-support',
  },
  
  // Misc Pages
  misc: {
    about: '/about',
    inspiration: '/inspiration',
    whatsNew: '/whats-new',
    changelog: '/changelog',
    feedback: '/feedback',
    tips: '/tips',
    contact: '/contact',
    privacy: '/privacy',
    terms: '/terms',
    keyboardShortcuts: '/keyboard-shortcuts',
    notifications: '/notifications',
    notificationCenter: '/notification-center',
    offlineMode: '/offline-mode',
    mobileApp: '/mobile-app',
  },
  
  // BrAPI Core
  brapi: {
    locations: '/locations',
    locationNew: '/locations/new',
    seasons: '/seasons',
    people: '/people',
    personNew: '/people/new',
    lists: '/lists',
    events: '/events',
    images: '/images',
    ontologies: '/ontologies',
    crops: '/crops',
  },
  
  // Additional Tools
  tools: {
    labelPrinting: '/labels',
    traitCalculator: '/calculator',
    fertilizerCalculator: '/fertilizer',
    harvestPlanner: '/harvest',
    harvestManagement: '/harvest-management',
    harvestLog: '/harvest-log',
    nurseryManagement: '/nursery',
    yieldMap: '/yieldmap',
    yieldPredictor: '/yield-predictor',
    cropCalendar: '/crop-calendar',
    resourceCalendar: '/resource-calendar',
    resourceAllocation: '/resource-allocation',
    seasonPlanning: '/season-planning',
    experimentDesigner: '/experiment-designer',
    workflowAutomation: '/workflow-automation',
    dataExportTemplates: '/data-export-templates',
    dataDictionary: '/data-dictionary',
    dataValidation: '/data-validation',
    batchOperations: '/batch-operations',
    quickEntry: '/quick-entry',
    activityTimeline: '/activity-timeline',
    collaborationHub: '/collaboration-hub',
    stakeholderPortal: '/stakeholder-portal',
    publicationTracker: '/publication-tracker',
    complianceTracker: '/compliance-tracker',
    vendorOrders: '/vendororders',
    parentSelection: '/parent-selection',
    crossPrediction: '/cross-prediction',
    selectionDecision: '/selection-decision',
    plotHistory: '/plot-history',
    sampleTracking: '/sample-tracking',
    pestMonitor: '/pest-monitor',
    growthTracker: '/growth-tracker',
    diseaseAtlas: '/disease-atlas',
    diseaseResistance: '/disease-resistance',
    abioticStress: '/abiotic-stress',
    phenomicSelection: '/phenomic-selection',
    speedBreeding: '/speed-breeding',
    doubledHaploid: '/doubled-haploid',
    geneticMap: '/genetic-map',
    languageSettings: '/language-settings',
  },
} as const

export class NavigationHelper {
  private page: Page
  
  constructor(page: Page) {
    this.page = page
  }
  
  /**
   * Navigate to a route
   */
  async goto(route: string) {
    await this.page.goto(route, { waitUntil: 'domcontentloaded' })
    await this.waitForPageLoad()
  }
  
  /**
   * Wait for page to load
   */
  async waitForPageLoad() {
    // Wait for loading indicators to disappear
    const spinner = this.page.locator('.animate-spin, [data-testid="loading"]').first()
    if (await spinner.isVisible({ timeout: 500 }).catch(() => false)) {
      await spinner.waitFor({ state: 'hidden', timeout: 30000 })
    }
  }
  
  /**
   * Navigate via sidebar
   */
  async navigateViaSidebar(menuPath: string[]) {
    for (const item of menuPath) {
      const menuItem = this.page.locator(`nav a:has-text("${item}"), nav button:has-text("${item}")`).first()
      await menuItem.click()
      await this.page.waitForTimeout(300) // Allow for animations
    }
    await this.waitForPageLoad()
  }
  
  /**
   * Verify current URL
   */
  async verifyUrl(expectedPath: string | RegExp) {
    await expect(this.page).toHaveURL(expectedPath)
  }
  
  /**
   * Go back
   */
  async goBack() {
    await this.page.goBack()
    await this.waitForPageLoad()
  }
  
  /**
   * Go forward
   */
  async goForward() {
    await this.page.goForward()
    await this.waitForPageLoad()
  }
  
  /**
   * Refresh page
   */
  async refresh() {
    await this.page.reload()
    await this.waitForPageLoad()
  }
  
  /**
   * Get all routes as flat array
   */
  static getAllRoutes(): string[] {
    const routes: string[] = []
    
    function extractRoutes(obj: any) {
      for (const value of Object.values(obj)) {
        if (typeof value === 'string') {
          routes.push(value)
        } else if (typeof value === 'object') {
          extractRoutes(value)
        }
      }
    }
    
    extractRoutes(ROUTES)
    return [...new Set(routes)] // Remove duplicates
  }
  
  /**
   * Get protected routes (require auth)
   */
  static getProtectedRoutes(): string[] {
    return this.getAllRoutes().filter(route => route !== '/login')
  }
  
  /**
   * Get public routes
   */
  static getPublicRoutes(): string[] {
    return ['/login']
  }
}
