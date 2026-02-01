/**
 * BrAPI Client
 * HTTP client for communicating with the backend API
 *
 * ## Error Handling (preview-1)
 * Uses ApiError from api-errors.ts for typed error handling.
 * - ApiError.type: Enum of error types (UNAUTHORIZED, NOT_FOUND, etc.)
 * - ApiError.getUserMessage(): User-friendly error message
 * - ApiError.isAuthError(): Check if auth-related
 * - ApiError.isRetryable: Whether request can be retried
 *
 * ## Logging
 * Uses logger from logger.ts for centralized logging.
 * Set VITE_LOG_LEVEL in .env to control verbosity (DEBUG, INFO, WARN, ERROR)
 *
 * ## Query Building
 * Current methods use URLSearchParams directly for simplicity.
 * For complex filtering needs, see api-helpers.ts QueryBuilder (v1.1 adoption).
 */

import {
  ApiError,
  ApiErrorType,
  createApiErrorFromResponse,
  createApiErrorFromNetworkError,
} from "./api-errors";
import { logger } from "./logger";
import { ApiClientCore } from "./api/core/client";
import { AuthService } from "./api/core/auth";
import { GlobalSearchService } from "./api/search/global-search";
import { LicensingService } from "./api/legal/licensing";
import {
  ProgramService,
  LocationService,
  TrialService,
  StudyService,
  SeasonService,
  PeopleService,
  ListService,
} from "./api/brapi/core";
import {
  GermplasmService,
  SeedLotService,
  CrossService,
} from "./api/brapi/germplasm";
import { FieldScannerService } from "./api/phenotyping/field-scanner";
import { AuditLogService } from "./api/system/audit-log";
import { ReferencesService } from "./api/brapi/genotyping/references";
import {
  ObservationService,
  EventsService,
  ScalesService,
  ImagesService,
  OntologiesService,
} from "./api/brapi/phenotyping";
import { SampleService, PlatesService } from "./api/brapi/genotyping";
import {
  VaultService,
  AccessionService,
  ViabilityService,
  RegenerationService,
  ExchangeService,
  QualityControlService,
  InventoryService,
  TraceabilityService,
  DispatchService,
  ProcessingService,
  WarehouseService,
} from "./api/seed-bank";
import { DUSService } from "./api/commercial/dus-testing";
import {
  VisionService,
  DiseaseService,
  CropHealthService,
  YieldPredictionService,
  ChatService,
} from "./api/ai";
import {
  NotificationService,
  ProfileService,
  TeamManagementService,
  DataDictionaryService,
  OfflineSyncService,
  SystemSettingsService,
  BackupService,
  WorkflowService,
  LanguageService,
} from "./api/system";
import {
  DataValidationService,
  AnalyticsService,

  ReportsService,
  GDDService,
  DataVisualizationService,
  StatisticsService,
} from "./api/analytics";
import {
  GermplasmCollectionService,
  GermplasmSearchService,
  ProgenyService,
  ParentSelectionService,
  GeneticGainService,
  GeneticDiversityService,
  PedigreeAnalysisService,
  PerformanceRankingService,
  SelectionDecisionsService,
  GenomicSelectionService,
  GermplasmComparisonService,
  BreedingPipelineService,
  CrossingProjectsService,
  VarietyComparisonService,
  QTLMappingService,
  GxEAnalysisService,
  NurseryManagementService,
  SeedlingBatchService,
  DiseaseResistanceService,
  AbioticStressService,
  SpeedBreedingService,
  DoubledHaploidService,
  MolecularBreedingService,
  PopulationGeneticsService,
  StabilityAnalysisService,
  YieldPredictorService,
} from "./api/breeding";
import { BreedingValueService } from "./api/breeding/breeding-value";
import { PhenotypeComparisonService } from "./api/breeding/phenotype-comparison";
import { GermplasmAttributesService } from "./api/brapi/attributes";
import { SeedRequestService } from "./api/seed-bank/requests";
import { WorkspacePreferencesService } from "./api/system/workspace";
import { CrossingPlannerService } from "./api/breeding/crossing-planner";
import { GenotypingService } from "./api/brapi/genotyping";
import { SampleTrackingService } from "./api/genotyping";
import {
  CollaborationService,
  CollaborationHubService,
  DataSyncService,
} from "./api/collaboration";
import {
  YieldMapService,
  SpatialService,
  TrialNetworkService,
  HarvestService,
  FieldBookService,
  FieldMapService,
  TrialPlanningService,
  FieldLayoutService,
  TrialSummaryService,
  PhenomicSelectionService,
  FieldPlanningService,
  HarvestPlannerService,
} from "./api/phenotyping";
import {
  WeatherService,
  ClimateService,
  CropCalendarService,
  FieldEnvironmentService,
  PhenologyService,
} from "./api/agronomy";
import { SensorService } from "./api/iot/sensors";
import {
  LabelService,
  QuickEntryService,
  PlotHistoryService,
} from "./api/operations";
export * from "./api/core/types";
export type { Field, Plot } from "./api/phenotyping/field-map";
export type { HarvestRecord } from "./api/phenotyping/harvest";
import { BrAPIResponse, BrAPIListResponse } from "./api/core/types";

// Re-export types for backward compatibility and ease of use
export * from "./api/phenotyping/field-layout";
export * from "./api/phenotyping/trial-summary";
export * from "./api/phenotyping/trial-planning";
export * from "./api/breeding/germplasm-comparison";
export * from "./api/breeding/gxe-analysis";
export * from "./api/breeding/genomic-selection";
export * from "./api/breeding/performance-ranking";
export * from "./api/breeding/genetic-gain";
export * from "./api/breeding/pedigree-analysis";
export * from "./api/breeding/qtl-mapping";
export * from "./api/breeding/selection-decisions";
import { SelectionIndexService } from "./api/breeding/selection-index";
import { TrialDesignService } from "./api/phenotyping/trial-design";
import { SecurityService } from "./api/system/security";
import { GenotypingResultsService } from "./api/genotyping/genotyping-results";
import { GenomicMapService } from "./api/genotyping/genomic-maps";

class APIClient extends ApiClientCore {
  // BrAPI Services
  programService: ProgramService;
  locationService: LocationService;
  trialService: TrialService;
  studyService: StudyService;
  seasonService: SeasonService;
  germplasmService: GermplasmService;
  observationService: ObservationService;
  seedLotService: SeedLotService;
  peopleService: PeopleService;
  listService: ListService;
  crossService: CrossService;
  sampleService: SampleService;
  
  // Seed Bank Services
  vaultService: VaultService;
  accessionService: AccessionService;
  viabilityService: ViabilityService;
  regenerationService: RegenerationService;
  exchangeService: ExchangeService;
  qualityControlService: QualityControlService;
  inventoryService: InventoryService;
  traceabilityService: TraceabilityService;
  dispatchService: DispatchService;
  processingService: ProcessingService;
  warehouseService: WarehouseService;
  
  // commercial
  dusService: DUSService;

  // System Services
  notificationService: NotificationService;
  profileService: ProfileService;
  teamManagementService: TeamManagementService;
  dataDictionaryService: DataDictionaryService;
  offlineSyncService: OfflineSyncService;
  systemSettingsService: SystemSettingsService;
  backupService: BackupService;
  workflowService: WorkflowService;
  languageService: LanguageService;

  // AI Services
  visionService: VisionService;
  diseaseService: DiseaseService;
  cropHealthService: CropHealthService;
  yieldPredictionService: YieldPredictionService;
  chatService: ChatService;

  // Phenotyping Extension
  eventsService: EventsService;
  scalesService: ScalesService;
  imagesService: ImagesService;

  // Genotyping Extension
  platesService: PlatesService;

  // Analytics Services
  dataValidationService: DataValidationService;
  dataQualityService: DataValidationService; // Alias for backward compatibility
  analyticsService: AnalyticsService;
  dataVisualizationService: DataVisualizationService;
  reportsService: ReportsService;
  gddService: GDDService;
  statisticsService: StatisticsService;

  // Collaboration Services
  collaborationService: CollaborationService;
  collaborationHubService: CollaborationHubService;
  dataSyncService: DataSyncService;

  // Phenotyping Services
  yieldMapService: YieldMapService;
  spatialService: SpatialService;
  trialNetworkService: TrialNetworkService;
  harvestService: HarvestService;
  fieldBookService: FieldBookService;
  fieldMapService: FieldMapService;
  trialPlanningService: TrialPlanningService;
  fieldLayoutService: FieldLayoutService;
  trialSummaryService: TrialSummaryService;
  phenomicSelectionService: PhenomicSelectionService;
  fieldPlanningService: FieldPlanningService;

  // Breeding Services
  germplasmCollectionService: GermplasmCollectionService;
  germplasmSearchService: GermplasmSearchService;
  progenyService: ProgenyService;
  parentSelectionService: ParentSelectionService;
  geneticGainService: GeneticGainService;
  geneticDiversityService: GeneticDiversityService;
  pedigreeAnalysisService: PedigreeAnalysisService;
  performanceRankingService: PerformanceRankingService;
  selectionDecisionsService: SelectionDecisionsService;
  qtlMappingService: QTLMappingService;
  genomicSelectionService: GenomicSelectionService;
  germplasmComparisonService: GermplasmComparisonService;
  breedingPipelineService: BreedingPipelineService;
  crossingProjectsService: CrossingProjectsService;
  varietyComparisonService: VarietyComparisonService;
  gxeAnalysisService: GxEAnalysisService;
  molecularBreedingService: MolecularBreedingService;
  populationGeneticsService: PopulationGeneticsService;
  stabilityAnalysisService: StabilityAnalysisService;
  yieldPredictorService: YieldPredictorService;
  speedBreedingService: SpeedBreedingService;
  doubledHaploidService: DoubledHaploidService;

  crossingPlannerService: CrossingPlannerService;

  nurseryManagementService: NurseryManagementService;
  seedlingBatchService: SeedlingBatchService;
  diseaseResistanceService: DiseaseResistanceService;
  abioticStressService: AbioticStressService;

  // Genotyping Services
  genotypingService: GenotypingService;
  sampleTrackingService: SampleTrackingService;
  genotypingResultsService: GenotypingResultsService;
  genomicMapService: GenomicMapService;

  // Phenotyping Services

  harvestPlannerService: HarvestPlannerService;

  // Phase 4 Services
  breedingValueService: BreedingValueService;
  phenotypeComparisonService: PhenotypeComparisonService;
  germplasmAttributesService: GermplasmAttributesService;
  seedRequestService: SeedRequestService;
  workspacePreferencesService: WorkspacePreferencesService;

  // Core Services (Extracted)
  authService: AuthService;
  globalSearchService: GlobalSearchService;
  licensingService: LicensingService;

  public selectionIndexService: SelectionIndexService;
  public trialDesignService: TrialDesignService;
  public securityService: SecurityService;
  public fieldScannerService: FieldScannerService;
  public auditLogService: AuditLogService;
  public referencesService: ReferencesService;
  public ontologiesService: OntologiesService;
  
  // Phase 9: Agronomy & IoT
  public weatherService: WeatherService;
  public climateService: ClimateService;
  public cropCalendarService: CropCalendarService;
  public fieldEnvironmentService: FieldEnvironmentService;
  public phenologyService: PhenologyService;
  public sensorService: SensorService;
  
  // Phase 9: Operations
  public labelService: LabelService;
  public quickEntryService: QuickEntryService;
  public plotHistoryService: PlotHistoryService;

  constructor(config: { baseURL: string; token?: string }) {
    super(config.baseURL);
    this.authService = new AuthService(this);
    this.globalSearchService = new GlobalSearchService(this);
    this.licensingService = new LicensingService(this);
    this.programService = new ProgramService(this);
    this.locationService = new LocationService(this);
    this.trialService = new TrialService(this);
    this.studyService = new StudyService(this);
    this.seasonService = new SeasonService(this);
    this.germplasmService = new GermplasmService(this);
    this.observationService = new ObservationService(this);
    this.ontologiesService = new OntologiesService(this); // Initialized OntologiesService
    this.seedLotService = new SeedLotService(this);
    this.peopleService = new PeopleService(this);
    this.listService = new ListService(this);
    this.crossService = new CrossService(this);
    this.sampleService = new SampleService(this);

    this.vaultService = new VaultService(this);
    this.accessionService = new AccessionService(this);
    this.viabilityService = new ViabilityService(this);
    this.regenerationService = new RegenerationService(this);
    this.exchangeService = new ExchangeService(this);
    this.qualityControlService = new QualityControlService(this);
    this.inventoryService = new InventoryService(this);
    this.traceabilityService = new TraceabilityService(this);
    this.dispatchService = new DispatchService(this);
    this.processingService = new ProcessingService(this);
    this.warehouseService = new WarehouseService(this);
    this.dusService = new DUSService(this);
    
    
    this.visionService = new VisionService(this);
    this.diseaseService = new DiseaseService(this);
    this.cropHealthService = new CropHealthService(this);
    this.yieldPredictionService = new YieldPredictionService(this);
    this.chatService = new ChatService(this);
    
    this.eventsService = new EventsService(this);
    this.scalesService = new ScalesService(this);
    this.imagesService = new ImagesService(this);
    this.platesService = new PlatesService(this);
    
    this.notificationService = new NotificationService(this);
    this.profileService = new ProfileService(this);
    this.teamManagementService = new TeamManagementService(this);
    this.dataDictionaryService = new DataDictionaryService(this);
    this.offlineSyncService = new OfflineSyncService(this);
    this.systemSettingsService = new SystemSettingsService(this);
    this.backupService = new BackupService(this);
    this.workflowService = new WorkflowService(this);
    this.languageService = new LanguageService(this);
    
    this.dataValidationService = new DataValidationService(this);
    this.dataQualityService = this.dataValidationService;
    this.analyticsService = new AnalyticsService(this);
    this.reportsService = new ReportsService(this);
    this.gddService = new GDDService(this);
    this.dataVisualizationService = new DataVisualizationService(this);
    this.statisticsService = new StatisticsService(this);
    
    this.collaborationService = new CollaborationService(this);
    this.collaborationHubService = new CollaborationHubService(this);
    this.dataSyncService = new DataSyncService(this);
    
    this.yieldMapService = new YieldMapService(this);
    this.spatialService = new SpatialService(this);
    this.trialNetworkService = new TrialNetworkService(this);
    this.harvestService = new HarvestService(this);
    this.fieldBookService = new FieldBookService(this);
    this.fieldMapService = new FieldMapService(this);
    this.trialPlanningService = new TrialPlanningService(this);
    this.fieldLayoutService = new FieldLayoutService(this);
    this.trialSummaryService = new TrialSummaryService(this);
    this.phenomicSelectionService = new PhenomicSelectionService(this);
    this.fieldPlanningService = new FieldPlanningService(this);

    this.germplasmCollectionService = new GermplasmCollectionService(this);
    this.germplasmSearchService = new GermplasmSearchService(this);
    this.progenyService = new ProgenyService(this);
    this.parentSelectionService = new ParentSelectionService(this);
    this.geneticGainService = new GeneticGainService(this);
    this.geneticDiversityService = new GeneticDiversityService(this);
    this.pedigreeAnalysisService = new PedigreeAnalysisService(this);
    this.performanceRankingService = new PerformanceRankingService(this);
    this.selectionDecisionsService = new SelectionDecisionsService(this);
    this.crossingPlannerService = new CrossingPlannerService(this);
    this.qtlMappingService = new QTLMappingService(this);
    this.genomicSelectionService = new GenomicSelectionService(this);
    this.germplasmComparisonService = new GermplasmComparisonService(this);
    this.breedingPipelineService = new BreedingPipelineService(this);
    this.crossingProjectsService = new CrossingProjectsService(this);
    this.varietyComparisonService = new VarietyComparisonService(this);
    this.gxeAnalysisService = new GxEAnalysisService(this);
    this.molecularBreedingService = new MolecularBreedingService(this);
    this.speedBreedingService = new SpeedBreedingService(this);
    this.doubledHaploidService = new DoubledHaploidService(this);


    this.nurseryManagementService = new NurseryManagementService(this);
    this.seedlingBatchService = new SeedlingBatchService(this);
    this.diseaseResistanceService = new DiseaseResistanceService(this);
    this.abioticStressService = new AbioticStressService(this);
    this.populationGeneticsService = new PopulationGeneticsService(this);
    this.stabilityAnalysisService = new StabilityAnalysisService(this);
    this.yieldPredictorService = new YieldPredictorService(this);
    
    this.breedingValueService = new BreedingValueService(this);
    this.phenotypeComparisonService = new PhenotypeComparisonService(this);
    this.germplasmAttributesService = new GermplasmAttributesService(this);
    this.seedRequestService = new SeedRequestService(this);
    this.workspacePreferencesService = new WorkspacePreferencesService(this);
    this.harvestPlannerService = new HarvestPlannerService(this);
    this.genotypingService = new GenotypingService(this);
    this.sampleTrackingService = new SampleTrackingService(this);
    this.genotypingResultsService = new GenotypingResultsService(this);
    this.genomicMapService = new GenomicMapService(this);
    
    this.selectionIndexService = new SelectionIndexService(this);
    this.trialDesignService = new TrialDesignService(this);
    this.securityService = new SecurityService(this);
    this.fieldScannerService = new FieldScannerService(this);
    this.auditLogService = new AuditLogService(this);

    this.referencesService = new ReferencesService(this);
    
    // Phase 9 Init
    this.weatherService = new WeatherService(this);
    this.climateService = new ClimateService(this);
    this.cropCalendarService = new CropCalendarService(this);
    this.fieldEnvironmentService = new FieldEnvironmentService(this);
    this.phenologyService = new PhenologyService(this);
    this.sensorService = new SensorService(this);
    
    this.labelService = new LabelService(this);
    this.quickEntryService = new QuickEntryService(this);
    this.plotHistoryService = new PlotHistoryService(this);
  }




  async updateSeason(
    seasonDbId: string,
    data: { seasonName?: string; year?: number },
  ) {
    return this.seasonService.updateSeason(seasonDbId, data);
  }

  async deleteSeason(seasonDbId: string) {
    return this.seasonService.deleteSeason(seasonDbId);
  }

  async deleteLocation(locationDbId: string) {
    return this.locationService.deleteLocation(locationDbId);
  }





}

export const apiClient = new APIClient({
  baseURL: import.meta.env.VITE_API_URL || ''
});

// ============ Service Exports ============
export * from "./api/breeding/nursery-management";
export * from "./api/breeding/seedling-batch";
export * from "./api/breeding/disease-resistance";
export * from "./api/breeding/abiotic-stress";
export * from "./api/analytics/analytics";
export * from "./api/analytics/visualization";
export * from "./api/phenotyping/harvest-planner";
export * from "./api/breeding/variety-comparison";
export * from "./api/genotyping/sample-tracking";
export * from "./api/seed-bank/warehouse";
export * from "./api/breeding/crossing-projects";
export * from "./api/breeding/pedigree-analysis";
export * from "./api/breeding/molecular";

// ============ Type Exports ============
export * from "./api/breeding/types";
export * from "./api/seed-bank/types";
