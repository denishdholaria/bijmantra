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
  MCPDService,
  GRINService,
  TaxonomyService,
  MTAService,
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
  AIConfigurationService,
  ChatHealthService,
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
import { MarkerAssistedService } from "./api/breeding/marker-assisted";
import { BreedingValueService } from "./api/breeding/breeding-value";
import { PhenotypeComparisonService } from "./api/breeding/phenotype-comparison";
import { GermplasmAttributesService } from "./api/brapi/attributes";
import { SeedRequestService } from "./api/seed-bank/requests";
import { WorkspacePreferencesService } from "./api/system/workspace";
import { CrossingPlannerService } from "./api/breeding/crossing-planner";
import { GenotypingService } from "./api/brapi/genotyping";
import { SampleTrackingService } from "./api/genotyping";
import { GenomicsPipelineService } from "./api/breeding/genomics-pipeline";
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
  AgronomyService,
} from "./api/agronomy";
import { SensorService } from "./api/iot/sensors";
import {
  LabelService,
  QuickEntryService,
  PlotHistoryService,
} from "./api/operations";
import { MarsService, LunarService, ResearchService } from "./api/space";
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
import { BiosimulationService } from "./api/breeding/biosimulation";
import { EconomicsService } from "./api/analytics/economics";
import { CrossPredictionService } from "./api/breeding/cross-prediction";
import { CalculatorService } from "./api/calculators";
import { API_URL } from '@/config';

class APIClient extends ApiClientCore {
  // ── Private backing fields ──────────────────────────────────────────────────
  // BrAPI Core
  private _programService?: ProgramService;
  private _locationService?: LocationService;
  private _trialService?: TrialService;
  private _studyService?: StudyService;
  private _seasonService?: SeasonService;
  private _germplasmService?: GermplasmService;
  private _observationService?: ObservationService;
  private _seedLotService?: SeedLotService;
  private _peopleService?: PeopleService;
  private _listService?: ListService;
  private _crossService?: CrossService;
  private _sampleService?: SampleService;

  // Seed Bank
  private _vaultService?: VaultService;
  private _accessionService?: AccessionService;
  private _viabilityService?: ViabilityService;
  private _regenerationService?: RegenerationService;
  private _exchangeService?: ExchangeService;
  private _mcpdService?: MCPDService;
  private _grinService?: GRINService;
  private _taxonomyService?: TaxonomyService;
  private _mtaService?: MTAService;
  private _qualityControlService?: QualityControlService;
  private _inventoryService?: InventoryService;
  private _traceabilityService?: TraceabilityService;
  private _dispatchService?: DispatchService;
  private _processingService?: ProcessingService;
  private _warehouseService?: WarehouseService;

  // Commercial
  private _dusService?: DUSService;

  // System
  private _notificationService?: NotificationService;
  private _profileService?: ProfileService;
  private _teamManagementService?: TeamManagementService;
  private _dataDictionaryService?: DataDictionaryService;
  private _offlineSyncService?: OfflineSyncService;
  private _aiConfigurationService?: AIConfigurationService;
  private _chatHealthService?: ChatHealthService;
  private _systemSettingsService?: SystemSettingsService;
  private _backupService?: BackupService;
  private _workflowService?: WorkflowService;
  private _languageService?: LanguageService;

  // AI
  private _visionService?: VisionService;
  private _diseaseService?: DiseaseService;
  private _cropHealthService?: CropHealthService;
  private _yieldPredictionService?: YieldPredictionService;
  private _chatService?: ChatService;

  // Phenotyping Extension
  private _eventsService?: EventsService;
  private _scalesService?: ScalesService;
  private _imagesService?: ImagesService;

  // Genotyping Extension
  private _platesService?: PlatesService;

  // Analytics
  private _dataValidationService?: DataValidationService;
  private _analyticsService?: AnalyticsService;
  private _dataVisualizationService?: DataVisualizationService;
  private _reportsService?: ReportsService;
  private _gddService?: GDDService;
  private _statisticsService?: StatisticsService;

  // Collaboration
  private _collaborationService?: CollaborationService;
  private _collaborationHubService?: CollaborationHubService;
  private _dataSyncService?: DataSyncService;

  // Phenotyping
  private _yieldMapService?: YieldMapService;
  private _spatialService?: SpatialService;
  private _trialNetworkService?: TrialNetworkService;
  private _harvestService?: HarvestService;
  private _fieldBookService?: FieldBookService;
  private _fieldMapService?: FieldMapService;
  private _trialPlanningService?: TrialPlanningService;
  private _fieldLayoutService?: FieldLayoutService;
  private _trialSummaryService?: TrialSummaryService;
  private _phenomicSelectionService?: PhenomicSelectionService;
  private _fieldPlanningService?: FieldPlanningService;
  private _harvestPlannerService?: HarvestPlannerService;

  // Breeding
  private _germplasmCollectionService?: GermplasmCollectionService;
  private _germplasmSearchService?: GermplasmSearchService;
  private _progenyService?: ProgenyService;
  private _parentSelectionService?: ParentSelectionService;
  private _geneticGainService?: GeneticGainService;
  private _geneticDiversityService?: GeneticDiversityService;
  private _pedigreeAnalysisService?: PedigreeAnalysisService;
  private _performanceRankingService?: PerformanceRankingService;
  private _selectionDecisionsService?: SelectionDecisionsService;
  private _qtlMappingService?: QTLMappingService;
  private _genomicSelectionService?: GenomicSelectionService;
  private _germplasmComparisonService?: GermplasmComparisonService;
  private _breedingPipelineService?: BreedingPipelineService;
  private _crossingProjectsService?: CrossingProjectsService;
  private _varietyComparisonService?: VarietyComparisonService;
  private _gxeAnalysisService?: GxEAnalysisService;
  private _molecularBreedingService?: MolecularBreedingService;
  private _markerAssistedService?: MarkerAssistedService;
  private _populationGeneticsService?: PopulationGeneticsService;
  private _stabilityAnalysisService?: StabilityAnalysisService;
  private _yieldPredictorService?: YieldPredictorService;
  private _speedBreedingService?: SpeedBreedingService;
  private _doubledHaploidService?: DoubledHaploidService;
  private _crossingPlannerService?: CrossingPlannerService;
  private _nurseryManagementService?: NurseryManagementService;
  private _seedlingBatchService?: SeedlingBatchService;
  private _diseaseResistanceService?: DiseaseResistanceService;
  private _abioticStressService?: AbioticStressService;
  private _genomicsPipelineService?: GenomicsPipelineService;
  private _breedingValueService?: BreedingValueService;
  private _phenotypeComparisonService?: PhenotypeComparisonService;
  private _selectionIndexService?: SelectionIndexService;
  private _crossPredictionService?: CrossPredictionService;
  private _biosimulationService?: BiosimulationService;

  // Genotyping
  private _genotypingService?: GenotypingService;
  private _sampleTrackingService?: SampleTrackingService;
  private _genotypingResultsService?: GenotypingResultsService;
  private _genomicMapService?: GenomicMapService;

  // Phase 4
  private _germplasmAttributesService?: GermplasmAttributesService;
  private _seedRequestService?: SeedRequestService;
  private _workspacePreferencesService?: WorkspacePreferencesService;

  // Core (Extracted)
  private _authService?: AuthService;
  private _globalSearchService?: GlobalSearchService;
  private _licensingService?: LicensingService;

  // Misc
  private _trialDesignService?: TrialDesignService;
  private _securityService?: SecurityService;
  private _fieldScannerService?: FieldScannerService;
  private _auditLogService?: AuditLogService;
  private _referencesService?: ReferencesService;
  private _ontologiesService?: OntologiesService;

  // Analytics extras
  private _economicsService?: EconomicsService;
  private _calculatorService?: CalculatorService;

  // Agronomy & IoT
  private _weatherService?: WeatherService;
  private _climateService?: ClimateService;
  private _cropCalendarService?: CropCalendarService;
  private _fieldEnvironmentService?: FieldEnvironmentService;
  private _phenologyService?: PhenologyService;
  private _agronomyService?: AgronomyService;
  private _sensorService?: SensorService;

  // Operations
  private _labelService?: LabelService;
  private _quickEntryService?: QuickEntryService;
  private _plotHistoryService?: PlotHistoryService;

  // Space Division
  private _marsService?: MarsService;
  private _lunarService?: LunarService;
  private _researchService?: ResearchService;

  // ── Constructor ─────────────────────────────────────────────────────────────
  constructor(config: { baseURL: string; token?: string }) {
    super(config.baseURL);
  }

  // ── Lazy getters ────────────────────────────────────────────────────────────
  // BrAPI Core
  get programService() { return (this._programService ??= new ProgramService(this)); }
  get locationService() { return (this._locationService ??= new LocationService(this)); }
  get trialService() { return (this._trialService ??= new TrialService(this)); }
  get studyService() { return (this._studyService ??= new StudyService(this)); }
  get seasonService() { return (this._seasonService ??= new SeasonService(this)); }
  get germplasmService() { return (this._germplasmService ??= new GermplasmService(this)); }
  get observationService() { return (this._observationService ??= new ObservationService(this)); }
  get seedLotService() { return (this._seedLotService ??= new SeedLotService(this)); }
  get peopleService() { return (this._peopleService ??= new PeopleService(this)); }
  get listService() { return (this._listService ??= new ListService(this)); }
  get crossService() { return (this._crossService ??= new CrossService(this)); }
  get sampleService() { return (this._sampleService ??= new SampleService(this)); }

  // Seed Bank
  get vaultService() { return (this._vaultService ??= new VaultService(this)); }
  get accessionService() { return (this._accessionService ??= new AccessionService(this)); }
  get viabilityService() { return (this._viabilityService ??= new ViabilityService(this)); }
  get regenerationService() { return (this._regenerationService ??= new RegenerationService(this)); }
  get exchangeService() { return (this._exchangeService ??= new ExchangeService(this)); }
  get mcpdService() { return (this._mcpdService ??= new MCPDService(this)); }
  get grinService() { return (this._grinService ??= new GRINService(this)); }
  get taxonomyService() { return (this._taxonomyService ??= new TaxonomyService(this)); }
  get mtaService() { return (this._mtaService ??= new MTAService(this)); }
  get qualityControlService() { return (this._qualityControlService ??= new QualityControlService(this)); }
  get inventoryService() { return (this._inventoryService ??= new InventoryService(this)); }
  get traceabilityService() { return (this._traceabilityService ??= new TraceabilityService(this)); }
  get dispatchService() { return (this._dispatchService ??= new DispatchService(this)); }
  get processingService() { return (this._processingService ??= new ProcessingService(this)); }
  get warehouseService() { return (this._warehouseService ??= new WarehouseService(this)); }

  // Commercial
  get dusService() { return (this._dusService ??= new DUSService(this)); }

  // System
  get notificationService() { return (this._notificationService ??= new NotificationService(this)); }
  get profileService() { return (this._profileService ??= new ProfileService(this)); }
  get teamManagementService() { return (this._teamManagementService ??= new TeamManagementService(this)); }
  get dataDictionaryService() { return (this._dataDictionaryService ??= new DataDictionaryService(this)); }
  get offlineSyncService() { return (this._offlineSyncService ??= new OfflineSyncService(this)); }
  get aiConfigurationService() { return (this._aiConfigurationService ??= new AIConfigurationService(this)); }
  get chatHealthService() { return (this._chatHealthService ??= new ChatHealthService(this)); }
  get systemSettingsService() { return (this._systemSettingsService ??= new SystemSettingsService(this)); }
  get backupService() { return (this._backupService ??= new BackupService(this)); }
  get workflowService() { return (this._workflowService ??= new WorkflowService(this)); }
  get languageService() { return (this._languageService ??= new LanguageService(this)); }

  // AI
  get visionService() { return (this._visionService ??= new VisionService(this)); }
  get diseaseService() { return (this._diseaseService ??= new DiseaseService(this)); }
  get cropHealthService() { return (this._cropHealthService ??= new CropHealthService(this)); }
  get yieldPredictionService() { return (this._yieldPredictionService ??= new YieldPredictionService(this)); }
  get chatService() { return (this._chatService ??= new ChatService(this)); }

  // Phenotyping Extension
  get eventsService() { return (this._eventsService ??= new EventsService(this)); }
  get scalesService() { return (this._scalesService ??= new ScalesService(this)); }
  get imagesService() { return (this._imagesService ??= new ImagesService(this)); }

  // Genotyping Extension
  get platesService() { return (this._platesService ??= new PlatesService(this)); }

  // Analytics
  get dataValidationService() { return (this._dataValidationService ??= new DataValidationService(this)); }
  get dataQualityService() { return this.dataValidationService; } // Alias for backward compatibility
  get analyticsService() { return (this._analyticsService ??= new AnalyticsService(this)); }
  get dataVisualizationService() { return (this._dataVisualizationService ??= new DataVisualizationService(this)); }
  get reportsService() { return (this._reportsService ??= new ReportsService(this)); }
  get gddService() { return (this._gddService ??= new GDDService(this)); }
  get statisticsService() { return (this._statisticsService ??= new StatisticsService(this)); }

  // Collaboration
  get collaborationService() { return (this._collaborationService ??= new CollaborationService(this)); }
  get collaborationHubService() { return (this._collaborationHubService ??= new CollaborationHubService(this)); }
  get dataSyncService() { return (this._dataSyncService ??= new DataSyncService(this)); }

  // Phenotyping
  get yieldMapService() { return (this._yieldMapService ??= new YieldMapService(this)); }
  get spatialService() { return (this._spatialService ??= new SpatialService(this)); }
  get trialNetworkService() { return (this._trialNetworkService ??= new TrialNetworkService(this)); }
  get harvestService() { return (this._harvestService ??= new HarvestService(this)); }
  get fieldBookService() { return (this._fieldBookService ??= new FieldBookService(this)); }
  get fieldMapService() { return (this._fieldMapService ??= new FieldMapService(this)); }
  get trialPlanningService() { return (this._trialPlanningService ??= new TrialPlanningService(this)); }
  get fieldLayoutService() { return (this._fieldLayoutService ??= new FieldLayoutService(this)); }
  get trialSummaryService() { return (this._trialSummaryService ??= new TrialSummaryService(this)); }
  get phenomicSelectionService() { return (this._phenomicSelectionService ??= new PhenomicSelectionService(this)); }
  get fieldPlanningService() { return (this._fieldPlanningService ??= new FieldPlanningService(this)); }
  get harvestPlannerService() { return (this._harvestPlannerService ??= new HarvestPlannerService(this)); }

  // Breeding
  get germplasmCollectionService() { return (this._germplasmCollectionService ??= new GermplasmCollectionService(this)); }
  get germplasmSearchService() { return (this._germplasmSearchService ??= new GermplasmSearchService(this)); }
  get progenyService() { return (this._progenyService ??= new ProgenyService(this)); }
  get parentSelectionService() { return (this._parentSelectionService ??= new ParentSelectionService(this)); }
  get geneticGainService() { return (this._geneticGainService ??= new GeneticGainService(this)); }
  get geneticDiversityService() { return (this._geneticDiversityService ??= new GeneticDiversityService(this)); }
  get pedigreeAnalysisService() { return (this._pedigreeAnalysisService ??= new PedigreeAnalysisService(this)); }
  get performanceRankingService() { return (this._performanceRankingService ??= new PerformanceRankingService(this)); }
  get selectionDecisionsService() { return (this._selectionDecisionsService ??= new SelectionDecisionsService(this)); }
  get qtlMappingService() { return (this._qtlMappingService ??= new QTLMappingService(this)); }
  get genomicSelectionService() { return (this._genomicSelectionService ??= new GenomicSelectionService(this)); }
  get germplasmComparisonService() { return (this._germplasmComparisonService ??= new GermplasmComparisonService(this)); }
  get breedingPipelineService() { return (this._breedingPipelineService ??= new BreedingPipelineService(this)); }
  get crossingProjectsService() { return (this._crossingProjectsService ??= new CrossingProjectsService(this)); }
  get varietyComparisonService() { return (this._varietyComparisonService ??= new VarietyComparisonService(this)); }
  get gxeAnalysisService() { return (this._gxeAnalysisService ??= new GxEAnalysisService(this)); }
  get molecularBreedingService() { return (this._molecularBreedingService ??= new MolecularBreedingService(this)); }
  get markerAssistedService() { return (this._markerAssistedService ??= new MarkerAssistedService(this)); }
  get populationGeneticsService() { return (this._populationGeneticsService ??= new PopulationGeneticsService(this)); }
  get stabilityAnalysisService() { return (this._stabilityAnalysisService ??= new StabilityAnalysisService(this)); }
  get yieldPredictorService() { return (this._yieldPredictorService ??= new YieldPredictorService(this)); }
  get speedBreedingService() { return (this._speedBreedingService ??= new SpeedBreedingService(this)); }
  get doubledHaploidService() { return (this._doubledHaploidService ??= new DoubledHaploidService(this)); }
  get crossingPlannerService() { return (this._crossingPlannerService ??= new CrossingPlannerService(this)); }
  get nurseryManagementService() { return (this._nurseryManagementService ??= new NurseryManagementService(this)); }
  get seedlingBatchService() { return (this._seedlingBatchService ??= new SeedlingBatchService(this)); }
  get diseaseResistanceService() { return (this._diseaseResistanceService ??= new DiseaseResistanceService(this)); }
  get abioticStressService() { return (this._abioticStressService ??= new AbioticStressService(this)); }
  get genomicsPipelineService() { return (this._genomicsPipelineService ??= new GenomicsPipelineService(this)); }
  get breedingValueService() { return (this._breedingValueService ??= new BreedingValueService(this)); }
  get phenotypeComparisonService() { return (this._phenotypeComparisonService ??= new PhenotypeComparisonService(this)); }
  get selectionIndexService() { return (this._selectionIndexService ??= new SelectionIndexService(this)); }
  get crossPredictionService() { return (this._crossPredictionService ??= new CrossPredictionService(this)); }
  get biosimulationService() { return (this._biosimulationService ??= new BiosimulationService(this)); }

  // Genotyping
  get genotypingService() { return (this._genotypingService ??= new GenotypingService(this)); }
  get sampleTrackingService() { return (this._sampleTrackingService ??= new SampleTrackingService(this)); }
  get genotypingResultsService() { return (this._genotypingResultsService ??= new GenotypingResultsService(this)); }
  get genomicMapService() { return (this._genomicMapService ??= new GenomicMapService(this)); }

  // Phase 4
  get germplasmAttributesService() { return (this._germplasmAttributesService ??= new GermplasmAttributesService(this)); }
  get seedRequestService() { return (this._seedRequestService ??= new SeedRequestService(this)); }
  get workspacePreferencesService() { return (this._workspacePreferencesService ??= new WorkspacePreferencesService(this)); }

  // Core (Extracted)
  get authService() { return (this._authService ??= new AuthService(this)); }
  get globalSearchService() { return (this._globalSearchService ??= new GlobalSearchService(this)); }
  get licensingService() { return (this._licensingService ??= new LicensingService(this)); }

  // Misc
  get trialDesignService() { return (this._trialDesignService ??= new TrialDesignService(this)); }
  get securityService() { return (this._securityService ??= new SecurityService(this)); }
  get fieldScannerService() { return (this._fieldScannerService ??= new FieldScannerService(this)); }
  get auditLogService() { return (this._auditLogService ??= new AuditLogService(this)); }
  get referencesService() { return (this._referencesService ??= new ReferencesService(this)); }
  get ontologiesService() { return (this._ontologiesService ??= new OntologiesService(this)); }

  // Analytics extras
  get economicsService() { return (this._economicsService ??= new EconomicsService(this)); }
  get calculatorService() { return (this._calculatorService ??= new CalculatorService(this)); }

  // Agronomy & IoT
  get weatherService() { return (this._weatherService ??= new WeatherService(this)); }
  get climateService() { return (this._climateService ??= new ClimateService(this)); }
  get cropCalendarService() { return (this._cropCalendarService ??= new CropCalendarService(this)); }
  get fieldEnvironmentService() { return (this._fieldEnvironmentService ??= new FieldEnvironmentService(this)); }
  get phenologyService() { return (this._phenologyService ??= new PhenologyService(this)); }
  get agronomyService() { return (this._agronomyService ??= new AgronomyService(this)); }
  get sensorService() { return (this._sensorService ??= new SensorService(this)); }

  // Operations
  get labelService() { return (this._labelService ??= new LabelService(this)); }
  get quickEntryService() { return (this._quickEntryService ??= new QuickEntryService(this)); }
  get plotHistoryService() { return (this._plotHistoryService ??= new PlotHistoryService(this)); }

  // Space Division
  get marsService() { return (this._marsService ??= new MarsService(this)); }
  get lunarService() { return (this._lunarService ??= new LunarService(this)); }
  get researchService() { return (this._researchService ??= new ResearchService(this)); }
}

export const apiClient = new APIClient({
  baseURL: API_URL
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
