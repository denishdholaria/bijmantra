"""
Models package
Import all models here for Alembic to detect them
"""

from app.models.ai_quota import AIUsageDaily
from app.models.audit import AuditLog, Permission, RolePermission
from app.models.barcode import BarcodeScan
from app.models.base import BaseModel
from app.models.biosimulation import CropModel, SimulationRun
from app.models.climate import (
    AdoptionLevel,
    CarbonMeasurement,
    CarbonMeasurementType,
    # Carbon Monitoring
    CarbonStock,
    EmissionCategory,
    EmissionFactor,
    # Emissions
    EmissionSource,
    # Impact Metrics
    ImpactMetric,
    ImpactReport,
    MetricType,
    PolicyAdoption,
    Publication,
    ReleaseStatus,
    SDGGoal,
    SDGIndicator,
    VarietyFootprint,
    VarietyRelease,
)
from app.models.collaboration import (
    CollabActivityType,
    CollaborationActivity,
    CollaborationComment,
    CollaborationTask,
    # Collaboration Models
    CollaborationWorkspace,
    # Chat Models
    Conversation,
    ConversationParticipant,
    ConversationType,
    GeneratedReport,
    MemberRole,
    MemberStatus,
    Message,
    OfflineDataCache,
    ReportCategory,
    # Enums
    ReportFormat,
    ReportSchedule,
    ReportStatus,
    # Report Models
    ReportTemplate,
    ScheduleFrequency,
    ScheduleStatus,
    SyncAction,
    SyncEntityType,
    SyncHistory,
    # Data Sync Models
    SyncItem,
    SyncSettings,
    SyncStatus,
    TaskPriority,
    TaskStatus,
    UserPresence,
    WorkspaceMember,
    WorkspaceType,
)
from app.models.core import (
    List,
    Location,
    Ontology,
    Organization,
    Person,
    Program,
    Season,
    Study,
    Trial,
    User,
)
from app.models.cost_analysis import BudgetCategory, Expense
from app.models.data_management import (
    AlertSeverity,
    AlertType,
    Backup,
    BackupStatus,
    BackupType,
    CollectionStatus,
    # Enums
    CollectionType,
    DiseaseRiskLevel,
    GermplasmCollection,
    GermplasmCollectionMember,
    HealthAlert,
    TrialHealth,
    ValidationIssue,
    ValidationIssueStatus,
    ValidationRule,
    ValidationRun,
    ValidationRunStatus,
    ValidationSeverity,
)
from app.models.devguru import (
    ChapterStatus,
    ChapterType,
    CommitteeMeeting,
    # Phase 5: Collaboration
    CommitteeMember,
    CommitteeRole,
    FeedbackItem,
    FeedbackPriority,
    FeedbackStatus,
    FeedbackType,
    LinkType,
    MeetingStatus,
    MeetingType,
    MilestoneStatus,
    PaperExperimentLink,
    ReadStatus,
    ResearchMilestone,
    # Phase 3: Literature
    ResearchPaper,
    ResearchPhase,
    ResearchProject,
    # Phase 4: Writing
    ThesisChapter,
    WritingSession,
)
from app.models.dispatch import Dispatch, DispatchItem, Firm
from app.models.doubled_haploid import DHBatch, DHProtocol
from app.models.dus import DUSEntry, DUSResult, DUSScore, DUSTrial, DUSTrialStatus
from app.models.environmental import EnvironmentalUnit, SoilProfile
from app.models.field_operations import (
    FieldBookEntry,
    FieldBookObservation,
    FieldBookStudy,
    FieldBookTrait,
    NurseryLocation,
    SeedlingBatch,
)
from app.models.field_scanner import FieldScan
from app.models.future.carbon_sequestration import CarbonSequestration

# from app.models.future.crop_calendar import CropCalendar
from app.models.future.crop_suitability import CropSuitability
from app.models.future.disease_risk_forecast import DiseaseRiskForecast
from app.models.future.fertilizer_recommendation import FertilizerRecommendation
from app.models.future.field import Field
from app.models.future.gdd_log import GrowingDegreeDayLog
from app.models.future.ipm_strategy import IPMStrategy
from app.models.future.irrigation_schedule import IrrigationSchedule, IrrigationStatus
from app.models.future.pest_observation import PestObservation
from app.models.future.soil_health_score import SoilHealthScore
from app.models.future.soil_moisture_reading import SoilMoistureReading
from app.models.future.soil_test import SoilTest
from app.models.future.spray_application import SprayApplication
from app.models.future.water_balance import WaterBalance
from app.models.future.yield_prediction import YieldPrediction
from app.models.genotyping import (
    Call,
    CallSet,
    GenomeMap,
    LinkageGroup,
    MarkerPosition,
    Plate,
    Reference,
    ReferenceSet,
    Variant,
    VariantSet,
    VendorOrder,
    variant_set_call_sets,
)
from app.models.germplasm import (
    BreedingMethod,
    Cross,
    CrossingProject,
    Germplasm,
    GermplasmAttribute,
    PlannedCross,
    Seedlot,
    SeedlotTransaction,
)
from app.models.import_job import ImportJob
from app.models.iot import (
    IoTAggregate,
    IoTAlertEvent,
    IoTAlertRule,
    IoTDevice,
    IoTEnvironmentLink,
    IoTSensor,
    IoTTelemetry,
)
from app.models.label_printing import PrintJob, PrintJobStatus
from app.models.mars import MarsClosedLoopMetric, MarsEnvironmentProfile, MarsTrial
from app.models.phenomic import PhenomicDataset, PhenomicModel
from app.models.phenotyping import (
    Event,
    Image,
    Observation,
    ObservationUnit,
    ObservationVariable,
    Sample,
)
from app.models.proposal import ActionType, Proposal, ProposalStatus
from app.models.qtl import QTL, Gene, GOTerm, gene_go_terms
from app.models.space_research import SpaceCrop, SpaceExperiment
from app.models.speed_breeding import (
    SpeedBreedingBatch,
    SpeedBreedingChamber,
    SpeedBreedingProtocol,
)
from app.models.stress_resistance import (
    AbioticStress,
    Disease,
    PyramidingStrategy,
    ResistanceGene,
    ToleranceGene,
)
from app.models.system_settings import SystemSettings
from app.models.user_management import (
    ActivityLog,
    Notification,
    NotificationPreference,
    QuietHours,
    Role,
    Team,
    TeamInvitation,
    TeamMember,
    UserPreference,
    UserProfile,
    UserRole,
    UserSession,
)
from app.models.veena_core import ReasoningTrace, UserContext, VeenaMemory
from app.models.vision import (
    AnnotationStatus,
    AnnotationTask,
    AnnotationTaskItem,
    AnnotationType,
    VisionAnnotation,
    VisionDeployment,
    VisionModel,
)
from app.models.warehouse import StorageLocation
from app.models.field_scanner import FieldScan
from app.modules.bio_analytics.models import GSModel, MarkerEffect, GEBVPrediction, GWASRun, GWASResult, BioQTL, CandidateGene
from app.models.biosimulation import CropModel, SimulationRun
from app.models.environmental import EnvironmentalUnit, SoilProfile
from app.models.audit import AuditLog, Permission, RolePermission
from app.models.import_job import ImportJob
from app.modules.weather.models import (
    WeatherStation,
    ForecastData,
    HistoricalRecord,
    ClimateZone,
    AlertSubscription
)
from app.modules.crop_calendar.models import (
    ActivityType,
    CropCalendar,
    GrowthStage,
    HarvestWindow,
    ResourceRequirement,
    ScheduleEvent,
)
from app.modules.seed_bank.models import Accession
from app.models.phenology import PhenologyRecord, PhenologyObservation

__all__ = [
    "BaseModel",
    # Core Models
    "Organization",
    "User",
    "ImportJob",
    "Program",
    "Location",
    "Trial",
    "Study",
    "Person",
    "Season",
    "Ontology",
    "List",
    # Germplasm Models
    "Germplasm",
    "GermplasmAttribute",
    "Cross",
    "CrossingProject",
    "PlannedCross",
    "Seedlot",
    "SeedlotTransaction",
    "BreedingMethod",
    "Accession",
    # Phenotyping Models
    "ObservationVariable",
    "ObservationUnit",
    "Observation",
    "Sample",
    "Image",
    "Event",
    # IoT Models
    "IoTDevice",
    "IoTSensor",
    "IoTTelemetry",
    "IoTAlertRule",
    "IoTAlertEvent",
    "IoTAggregate",
    "IoTEnvironmentLink",
    # Genotyping Models
    "ReferenceSet",
    "Reference",
    "GenomeMap",
    "LinkageGroup",
    "MarkerPosition",
    "VariantSet",
    "Variant",
    "CallSet",
    "Call",
    "Plate",
    "VendorOrder",
    "variant_set_call_sets",
    # User Management Models
    "Notification",
    "NotificationPreference",
    "QuietHours",
    "UserProfile",
    "UserPreference",
    "UserSession",
    "Team",
    "Role",
    "UserRole",
    "TeamMember",
    "TeamInvitation",
    "ActivityLog",
    # Stress Resistance Models
    "AbioticStress",
    "ToleranceGene",
    "Disease",
    "ResistanceGene",
    "PyramidingStrategy",
    # Field Operations Models
    "NurseryLocation",
    "SeedlingBatch",
    "FieldBookStudy",
    "FieldBookTrait",
    "FieldBookEntry",
    "FieldBookObservation",
    # Data Management Models
    "GermplasmCollection",
    "GermplasmCollectionMember",
    "ValidationRule",
    "ValidationIssue",
    "ValidationRun",
    "Backup",
    "TrialHealth",
    "HealthAlert",
    # Collaboration & Reporting Models
    "ReportTemplate",
    "ReportSchedule",
    "GeneratedReport",
    "CollaborationWorkspace",
    "WorkspaceMember",
    "UserPresence",
    "CollaborationActivity",
    "CollaborationTask",
    "CollaborationComment",
    # Chat Models
    "Conversation",
    "ConversationParticipant",
    "Message",
    "ConversationType",
    "SyncItem",
    "SyncHistory",
    "OfflineDataCache",
    "SyncSettings",
    # DevGuru Models
    "ResearchProject",
    # System Settings
    "SystemSettings",
    "ResearchMilestone",
    "ResearchPhase",
    "MilestoneStatus",
    # DevGuru Phase 3: Literature
    "ResearchPaper",
    "PaperExperimentLink",
    "ReadStatus",
    "LinkType",
    # DevGuru Phase 4: Writing
    "ThesisChapter",
    "WritingSession",
    "ChapterType",
    "ChapterStatus",
    # DevGuru Phase 5: Collaboration
    "CommitteeMember",
    "CommitteeMeeting",
    "FeedbackItem",
    "CommitteeRole",
    "MeetingType",
    "MeetingStatus",
    "FeedbackType",
    "FeedbackPriority",
    "FeedbackStatus",
    # Future Models - Crop Intelligence
    "GrowingDegreeDayLog",
    "CropCalendar",
    "ActivityType",
    "ScheduleEvent",
    "ResourceRequirement",
    "GrowthStage",
    "HarvestWindow",
    "CropSuitability",
    "YieldPrediction",
    # Future Models - Soil & Nutrients
    "FertilizerRecommendation",
    "SoilTest",
    "SoilHealthScore",
    "CarbonSequestration",
    # Future Models - Water & Irrigation
    "Field",
    "WaterBalance",
    "IrrigationSchedule",
    "IrrigationStatus",
    "SoilMoistureReading",
    # Future Models - Crop Protection
    "DiseaseRiskForecast",
    "SprayApplication",
    "PestObservation",
    "IPMStrategy",
    # Dispatch Models
    "Firm",
    "Dispatch",
    "DispatchItem",
    # DUS Testing Models
    "DUSTrial",
    "DUSEntry",
    "DUSScore",
    "DUSTrialStatus",
    "DUSResult",
    # Doubled Haploid Models
    "DHProtocol",
    "DHBatch",
    # Phenomic Selection Models
    "PhenomicDataset",
    "PhenomicModel",
    # Space Research Models
    "SpaceCrop",
    "SpaceExperiment",
    # Cost Analysis Models
    "BudgetCategory",
    "Expense",
    # Speed Breeding Models
    "SpeedBreedingProtocol",
    "SpeedBreedingBatch",
    "SpeedBreedingChamber",
    # Vision Models
    "AnnotationTask",
    "VisionAnnotation",
    "AnnotationTaskItem",
    "AnnotationType",
    "AnnotationStatus",
    "VisionModel",
    "VisionDeployment",
    # Climate Models - Carbon Monitoring
    "CarbonStock",
    "CarbonMeasurement",
    "CarbonMeasurementType",
    # Climate Models - Emissions
    "EmissionSource",
    "EmissionFactor",
    "VarietyFootprint",
    "EmissionCategory",
    # Climate Models - Impact Metrics
    "ImpactMetric",
    "SDGIndicator",
    "VarietyRelease",
    "PolicyAdoption",
    "Publication",
    "ImpactReport",
    "MetricType",
    "SDGGoal",
    "ReleaseStatus",
    "AdoptionLevel",
    # Safe AI (Scribe)
    "Proposal",
    "ProposalStatus",
    "ActionType",
    # MARS Module
    "MarsEnvironmentProfile",
    "MarsTrial",
    "MarsClosedLoopMetric",
    "AIUsageDaily",
    "PrintJob",
    # Veena Core
    "VeenaMemory",
    "ReasoningTrace",
    "UserContext",
    "BarcodeScan",
    # Warehouse & Field Scanner
    "StorageLocation",
    "FieldScan",
    # Bio-Analytics
    "GSModel",
    "MarkerEffect",
    "GEBVPrediction",
    "GWASRun",
    "GWASResult",
    "BioQTL",
    "CandidateGene",
    # Science Engine Models
    "CropModel",
    "SimulationRun",
    "EnvironmentalUnit",
    "SoilProfile",
    "AuditLog",
    "Permission",
    "RolePermission",
    # Weather Models
    "WeatherStation",
    "ForecastData",
    "HistoricalRecord",
    "ClimateZone",
    "AlertSubscription",
    # QTL & GO
    "Gene",
    "GOTerm",
    "gene_go_terms",
    # Phenology Models
    "PhenologyRecord",
    "PhenologyObservation",
]
