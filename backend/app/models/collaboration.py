"""
Collaboration and Reporting Models
Database models for reports, collaboration hub, and data sync
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, Enum as SQLEnum, JSON, Float
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


# ============================================
# ENUMS
# ============================================

class ReportFormat(str, enum.Enum):
    PDF = "PDF"
    EXCEL = "Excel"
    CSV = "CSV"
    POWERPOINT = "PowerPoint"
    JSON = "JSON"


class ReportCategory(str, enum.Enum):
    TRIALS = "trials"
    GERMPLASM = "germplasm"
    BREEDING = "breeding"
    PHENOTYPING = "phenotyping"
    GENOMICS = "genomics"
    INVENTORY = "inventory"
    QUALITY = "quality"


class ScheduleFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ScheduleStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class MemberStatus(str, enum.Enum):
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"


class WorkspaceType(str, enum.Enum):
    TRIAL = "trial"
    STUDY = "study"
    CROSSING_PROJECT = "crossing_project"
    ANALYSIS = "analysis"
    REPORT = "report"


class CollabActivityType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    COMMENTED = "commented"
    SHARED = "shared"
    COMPLETED = "completed"
    ASSIGNED = "assigned"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SyncStatus(str, enum.Enum):
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"


class SyncAction(str, enum.Enum):
    UPLOAD = "upload"
    DOWNLOAD = "download"
    FULL_SYNC = "full_sync"


class SyncEntityType(str, enum.Enum):
    OBSERVATION = "observation"
    GERMPLASM = "germplasm"
    TRIAL = "trial"
    STUDY = "study"
    CROSS = "cross"
    IMAGE = "image"
    SAMPLE = "sample"


class ConversationType(str, enum.Enum):
    DIRECT = "direct"
    GROUP = "group"
    TEAM = "team"


# ============================================
# REPORT MODELS
# ============================================

class ReportTemplate(BaseModel):
    """Report template definitions"""
    __tablename__ = "report_templates"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(SQLEnum(ReportCategory, values_callable=lambda x: [e.value for e in x]), nullable=False)
    formats = Column(JSON, default=list)  # List of supported formats
    parameters = Column(JSON, default=list)  # Parameter definitions
    template_content = Column(Text)  # Template markup/config
    last_generated = Column(DateTime)
    generation_count = Column(Integer, default=0)
    is_system = Column(Boolean, default=False)  # System vs user-created
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organization = relationship("Organization", backref="report_templates")
    schedules = relationship("ReportSchedule", back_populates="template", cascade="all, delete-orphan")
    generated_reports = relationship("GeneratedReport", back_populates="template", cascade="all, delete-orphan")


class ReportSchedule(BaseModel):
    """Scheduled report configurations"""
    __tablename__ = "report_schedules"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    schedule = Column(SQLEnum(ScheduleFrequency, values_callable=lambda x: [e.value for e in x]), nullable=False)
    schedule_time = Column(String(10))  # HH:MM format
    schedule_day = Column(Integer)  # Day of week (0-6) or day of month (1-31)
    next_run = Column(DateTime)
    last_run = Column(DateTime)
    recipients = Column(JSON, default=list)  # List of email addresses
    parameters = Column(JSON, default=dict)  # Report parameters
    status = Column(SQLEnum(ScheduleStatus, values_callable=lambda x: [e.value for e in x]), default=ScheduleStatus.ACTIVE)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    organization = relationship("Organization", backref="report_schedules")
    template = relationship("ReportTemplate", back_populates="schedules")
    created_by = relationship("User", backref="report_schedules")


class GeneratedReport(BaseModel):
    """Generated report records"""
    __tablename__ = "generated_reports"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey("report_schedules.id"), index=True)  # Null if manual
    name = Column(String(255), nullable=False)
    format = Column(SQLEnum(ReportFormat, values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(SQLEnum(ReportStatus, values_callable=lambda x: [e.value for e in x]), default=ReportStatus.PENDING)
    size_bytes = Column(Integer, default=0)
    file_path = Column(String(500))  # Storage path
    download_url = Column(String(500))
    parameters = Column(JSON, default=dict)  # Parameters used
    error_message = Column(Text)
    generated_by_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    
    # Relationships
    organization = relationship("Organization", backref="generated_reports")
    template = relationship("ReportTemplate", back_populates="generated_reports")
    schedule = relationship("ReportSchedule", backref="generated_reports")
    generated_by = relationship("User", backref="generated_reports")


# ============================================
# COLLABORATION MODELS
# ============================================

class CollaborationWorkspace(BaseModel):
    """Shared workspaces for team collaboration"""
    __tablename__ = "collaboration_workspaces"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(WorkspaceType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entity_id = Column(String(100))  # ID of linked entity (trial, study, etc.)
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organization = relationship("Organization", backref="collaboration_workspaces")
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_workspaces")
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    activities = relationship("CollaborationActivity", back_populates="workspace", cascade="all, delete-orphan")
    tasks = relationship("CollaborationTask", back_populates="workspace", cascade="all, delete-orphan")
    comments = relationship("CollaborationComment", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(BaseModel):
    """Workspace membership"""
    __tablename__ = "workspace_members"
    
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(SQLEnum(MemberRole, values_callable=lambda x: [e.value for e in x]), default=MemberRole.VIEWER)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    workspace = relationship("CollaborationWorkspace", back_populates="members")
    user = relationship("User", backref="workspace_memberships")


class UserPresence(BaseModel):
    """User online presence tracking"""
    __tablename__ = "user_presence"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    status = Column(SQLEnum(MemberStatus, values_callable=lambda x: [e.value for e in x]), default=MemberStatus.OFFLINE)
    current_workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id"))
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", backref="presence")
    current_workspace = relationship("CollaborationWorkspace", backref="active_users")


class CollaborationActivity(BaseModel):
    """Activity feed entries"""
    __tablename__ = "collaboration_activities"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(SQLEnum(CollabActivityType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    entity_name = Column(String(255))
    description = Column(Text)
    extra_data = Column("metadata", JSON, default=dict)  # Map to 'metadata' column in DB
    
    # Relationships
    organization = relationship("Organization", backref="collaboration_activities")
    workspace = relationship("CollaborationWorkspace", back_populates="activities")
    user = relationship("User", backref="collaboration_activities")


class CollaborationTask(BaseModel):
    """Tasks within workspaces"""
    __tablename__ = "collaboration_tasks"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id"), index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    assignee_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(TaskStatus, values_callable=lambda x: [e.value for e in x]), default=TaskStatus.TODO)
    priority = Column(SQLEnum(TaskPriority, values_callable=lambda x: [e.value for e in x]), default=TaskPriority.MEDIUM)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    organization = relationship("Organization", backref="collaboration_tasks")
    workspace = relationship("CollaborationWorkspace", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], backref="assigned_tasks")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_tasks")


class CollaborationComment(BaseModel):
    """Comments on entities"""
    __tablename__ = "collaboration_comments"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("collaboration_comments.id"))  # For replies
    
    # Relationships
    organization = relationship("Organization", backref="collaboration_comments")
    workspace = relationship("CollaborationWorkspace", back_populates="comments")
    user = relationship("User", backref="collaboration_comments")
    parent = relationship("CollaborationComment", remote_side="CollaborationComment.id", backref="replies")


# ============================================
# CHAT & MESSAGING MODELS
# ============================================

class Conversation(BaseModel):
    """Chat conversations (Direct or Group/Team)"""
    __tablename__ = "conversations"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255))  # Optional for direct messages
    type = Column(SQLEnum(ConversationType, values_callable=lambda x: [e.value for e in x]), default=ConversationType.DIRECT)
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id"), index=True)  # Optional, for team/workspace chats
    last_message_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", backref="conversations")
    workspace = relationship("CollaborationWorkspace", backref="conversations")
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="desc(Message.created_at)")


class ConversationParticipant(BaseModel):
    """Users in a conversation"""
    __tablename__ = "conversation_participants"

    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    last_read_at = Column(DateTime)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", backref="conversation_participations")


class Message(BaseModel):
    """Chat messages"""
    __tablename__ = "messages"

    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    is_system = Column(Boolean, default=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", backref="sent_messages")


# ============================================
# DATA SYNC MODELS
# ============================================

class SyncItem(BaseModel):
    """Items pending synchronization"""
    __tablename__ = "sync_items"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(SQLEnum(SyncEntityType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    entity_id = Column(String(100), nullable=False)
    name = Column(String(255))
    status = Column(SQLEnum(SyncStatus, values_callable=lambda x: [e.value for e in x]), default=SyncStatus.PENDING)
    size_bytes = Column(Integer, default=0)
    local_data = Column(JSON)  # Local version of data
    server_data = Column(JSON)  # Server version (for conflicts)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    last_modified = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization", backref="sync_items")
    user = relationship("User", backref="sync_items")


class SyncHistory(BaseModel):
    """Synchronization history log"""
    __tablename__ = "sync_history"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(SQLEnum(SyncAction, values_callable=lambda x: [e.value for e in x]), nullable=False)
    description = Column(Text)
    items_count = Column(Integer, default=0)
    bytes_transferred = Column(Integer, default=0)
    status = Column(String(20))  # success, error, partial
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Relationships
    organization = relationship("Organization", backref="sync_history")
    user = relationship("User", backref="sync_history")


class OfflineDataCache(BaseModel):
    """Offline data cache metadata"""
    __tablename__ = "offline_data_cache"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # trials, studies, germplasm, etc.
    item_count = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    last_updated = Column(DateTime)
    last_full_sync = Column(DateTime)
    
    # Relationships
    organization = relationship("Organization", backref="offline_data_cache")
    user = relationship("User", backref="offline_data_cache")


class SyncSettings(BaseModel):
    """User sync settings"""
    __tablename__ = "sync_settings"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    auto_sync = Column(Boolean, default=True)
    sync_on_wifi_only = Column(Boolean, default=True)
    background_sync = Column(Boolean, default=True)
    sync_images = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=15)
    max_offline_days = Column(Integer, default=30)
    conflict_resolution = Column(String(20), default="server_wins")  # server_wins, client_wins, manual
    
    # Relationships
    user = relationship("User", backref="sync_settings")


class SharedItem(BaseModel):
    """Items shared between users/teams"""
    __tablename__ = "shared_items"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    item_type = Column(String(50), nullable=False) # trial, study, germplasm, report
    item_id = Column(String(100), nullable=False)
    
    shared_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    permission = Column(String(20), default="view") # view, edit, admin
    shared_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization")
    shared_by = relationship("User", foreign_keys=[shared_by_id])
    shared_with = relationship("User", foreign_keys=[shared_with_id])
