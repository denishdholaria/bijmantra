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

__all__ = [
    "BaseModel",
    # Core Models
    "Organization",
    "User",
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
]
