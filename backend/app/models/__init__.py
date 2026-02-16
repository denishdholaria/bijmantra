"""
Models package
Import all models here for Alembic to detect them
"""

from app.models.base import BaseModel
from app.models.core import (
    Organization,
    User,
    Program,
    Location,
    Trial,
    Study,
    Person,
    Season,
    Ontology,
    List
)
from app.models.germplasm import (
    Germplasm,
    GermplasmAttribute,
    Cross,
    CrossingProject,
    PlannedCross,
    Seedlot,
    SeedlotTransaction,
    BreedingMethod
)
from app.modules.seed_bank.models import Accession
from app.models.phenotyping import (
    ObservationVariable,
    ObservationUnit,
    Observation,
    Sample,
    Image,
    Event
)
from app.models.iot import (
    IoTDevice,
    IoTSensor,
    IoTTelemetry,
    IoTAlertRule,
    IoTAlertEvent,
    IoTAggregate,
    IoTEnvironmentLink
)
from app.models.genotyping import (
    ReferenceSet,
    Reference,
    GenomeMap,
    LinkageGroup,
    MarkerPosition,
    VariantSet,
    Variant,
    CallSet,
    Call,
    Plate,
    VendorOrder,
    variant_set_call_sets
)
from app.models.user_management import (
    Notification,
    NotificationPreference,
    QuietHours,
    UserProfile,
    UserPreference,
    UserSession,
    Team,
    Role,
    UserRole,
    TeamMember,
    TeamInvitation,
    ActivityLog
)
from app.models.stress_resistance import (
    AbioticStress,
    ToleranceGene,
    Disease,
    ResistanceGene,
    PyramidingStrategy
)
from app.models.field_operations import (
    NurseryLocation,
    SeedlingBatch,
    FieldBookStudy,
    FieldBookTrait,
    FieldBookEntry,
    FieldBookObservation
)
from app.models.data_management import (
    GermplasmCollection,
    GermplasmCollectionMember,
    ValidationRule,
    ValidationIssue,
    ValidationRun,
    Backup,
    TrialHealth,
    HealthAlert,
    # Enums
    CollectionType,
    CollectionStatus,
    ValidationSeverity,
    ValidationIssueStatus,
    ValidationRunStatus,
    BackupType,
    BackupStatus,
    DiseaseRiskLevel,
    AlertType,
    AlertSeverity
)
from app.models.collaboration import (
    # Report Models
    ReportTemplate,
    ReportSchedule,
    GeneratedReport,
    # Collaboration Models
    CollaborationWorkspace,
    WorkspaceMember,
    UserPresence,
    CollaborationActivity,
    CollaborationTask,
    CollaborationComment,
    # Chat Models
    Conversation,
    ConversationParticipant,
    Message,
    ConversationType,
    # Data Sync Models
    SyncItem,
    SyncHistory,
    OfflineDataCache,
    SyncSettings,
    # Enums
    ReportFormat,
    ReportCategory,
    ScheduleFrequency,
    ReportStatus,
    ScheduleStatus,
    MemberRole,
    MemberStatus,
    WorkspaceType,
    CollabActivityType,
    TaskStatus,
    TaskPriority,
    SyncStatus,
    SyncAction,
    SyncEntityType
)
from app.models.system_settings import SystemSettings
from app.models.devguru import (
    ResearchProject,
    ResearchMilestone,
    ResearchPhase,
    MilestoneStatus,
    # Phase 3: Literature
    ResearchPaper,
    PaperExperimentLink,
    ReadStatus,
    LinkType,
    # Phase 4: Writing
    ThesisChapter,
    WritingSession,
    ChapterType,
    ChapterStatus,
    # Phase 5: Collaboration
    CommitteeMember,
    CommitteeMeeting,
    FeedbackItem,
    CommitteeRole,
    MeetingType,
    MeetingStatus,
    FeedbackType,
    FeedbackPriority,
    FeedbackStatus
)
from app.models.future.gdd_log import GrowingDegreeDayLog
from app.models.future.crop_calendar import CropCalendar
from app.models.future.crop_suitability import CropSuitability
from app.models.future.yield_prediction import YieldPrediction
from app.models.future.fertilizer_recommendation import FertilizerRecommendation
from app.models.future.soil_test import SoilTest
from app.models.future.soil_health_score import SoilHealthScore
from app.models.future.carbon_sequestration import CarbonSequestration
from app.models.future.field import Field
from app.models.future.water_balance import WaterBalance
from app.models.future.irrigation_schedule import IrrigationSchedule, IrrigationStatus
from app.models.future.soil_moisture_reading import SoilMoistureReading
from app.models.future.disease_risk_forecast import DiseaseRiskForecast
from app.models.future.spray_application import SprayApplication
from app.models.future.pest_observation import PestObservation
from app.models.future.ipm_strategy import IPMStrategy
from app.models.dispatch import Firm, Dispatch, DispatchItem
from app.models.dus import DUSTrial, DUSEntry, DUSScore, DUSTrialStatus, DUSResult
from app.models.doubled_haploid import DHProtocol, DHBatch
from app.models.phenomic import PhenomicDataset, PhenomicModel
from app.models.space_research import SpaceCrop, SpaceExperiment
from app.models.cost_analysis import BudgetCategory, Expense
from app.models.speed_breeding import (
    SpeedBreedingProtocol,
    SpeedBreedingBatch,
    SpeedBreedingChamber
)
from app.models.vision import (
    AnnotationTask,
    VisionAnnotation,
    AnnotationTaskItem,
    AnnotationType,
    AnnotationStatus,
    VisionModel,
    VisionDeployment
)
from app.models.climate import (
    # Carbon Monitoring
    CarbonStock,
    CarbonMeasurement,
    CarbonMeasurementType,
    # Emissions
    EmissionSource,
    EmissionFactor,
    VarietyFootprint,
    EmissionCategory,
    # Impact Metrics
    ImpactMetric,
    SDGIndicator,
    VarietyRelease,
    PolicyAdoption,
    Publication,
    ImpactReport,
    MetricType,
    SDGGoal,
    ReleaseStatus,
    AdoptionLevel,
)
from app.models.proposal import (
    Proposal,
    ProposalStatus,
    ActionType
)
from app.models.mars import (
    MarsEnvironmentProfile,
    MarsTrial,
    MarsClosedLoopMetric
)
from app.models.label_printing import PrintJob, PrintJobStatus
from app.models.ai_quota import AIUsageDaily
from app.models.veena_core import VeenaMemory, ReasoningTrace, UserContext
from app.models.barcode import BarcodeScan
from app.models.warehouse import StorageLocation
from app.models.field_scanner import FieldScan
from app.modules.bio_analytics.models import GSModel, MarkerEffect, GEBVPrediction, GWASRun, GWASResult
from app.models.biosimulation import CropModel, SimulationRun
from app.models.environmental import EnvironmentalUnit, SoilProfile
from app.models.audit import AuditLog, Permission, RolePermission
from app.models.import_job import ImportJob

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
    # Science Engine Models
    "CropModel",
    "SimulationRun",
    "EnvironmentalUnit",
    "SoilProfile",
    "AuditLog",
    "Permission",
    "RolePermission",
]
