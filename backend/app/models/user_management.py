"""
User Management Models
Notifications, Profiles, Preferences, Teams, Team Members, Invitations
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class NotificationType(str, enum.Enum):
    """Notification type enum"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


class NotificationCategory(str, enum.Enum):
    """Notification category enum"""
    TRIALS = "trials"
    INVENTORY = "inventory"
    WEATHER = "weather"
    SYNC = "sync"
    IMPORT = "import"
    TEAM = "team"
    RELEASES = "releases"
    ALERTS = "alerts"
    SYSTEM = "system"


class MemberStatus(str, enum.Enum):
    """Team member status enum"""
    ACTIVE = "active"
    PENDING = "pending"
    INACTIVE = "inactive"


class InviteStatus(str, enum.Enum):
    """Invitation status enum"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Notification(BaseModel):
    """User notification model"""
    
    __tablename__ = "notifications"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    notification_type = Column(String(20), nullable=False, default="info")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="system")
    
    read = Column(Boolean, default=False, nullable=False, index=True)
    action_url = Column(String(500))
    
    # Extra data
    extra_data = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")


class NotificationPreference(BaseModel):
    """User notification preferences per category"""
    
    __tablename__ = "notification_preferences"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    category = Column(String(100), nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
    
    # Unique constraint on user + category
    __table_args__ = (
        {'extend_existing': True}
    )


class QuietHours(BaseModel):
    """User quiet hours settings"""
    
    __tablename__ = "quiet_hours"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    enabled = Column(Boolean, default=False, nullable=False)
    start_time = Column(String(10), default="22:00")  # HH:MM format
    end_time = Column(String(10), default="07:00")    # HH:MM format
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")


class UserProfile(BaseModel):
    """Extended user profile information"""
    
    __tablename__ = "user_profiles"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Profile fields
    phone = Column(String(50))
    bio = Column(Text)
    location = Column(String(255))
    timezone = Column(String(100), default="UTC")
    avatar_url = Column(String(500))
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")


class UserPreference(BaseModel):
    """User application preferences"""
    
    __tablename__ = "user_preferences"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Appearance
    theme = Column(String(20), default="system")  # light, dark, system
    language = Column(String(10), default="en")
    density = Column(String(20), default="comfortable")  # compact, comfortable, spacious
    color_scheme = Column(String(50), default="standard")
    
    # Accessibility
    field_mode = Column(Boolean, default=False)
    high_contrast = Column(Boolean, default=False)
    large_text = Column(Boolean, default=False)
    haptic_feedback = Column(Boolean, default=True)
    
    # Notifications
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    
    # Defaults
    default_program_id = Column(Integer, ForeignKey("programs.id"))
    default_location_id = Column(Integer, ForeignKey("locations.id"))
    
    # UI State
    sidebar_collapsed = Column(Boolean, default=False)
    
    # Workspace Preferences (Gateway-Workspace Architecture)
    default_workspace = Column(String(20))  # breeding, seed-ops, research, genebank, admin
    recent_workspaces = Column(JSON, default=list)  # List of recent workspace IDs
    show_gateway_on_login = Column(Boolean, default=True)
    last_workspace = Column(String(20))  # Last active workspace
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")


class UserSession(BaseModel):
    """User session tracking"""
    
    __tablename__ = "user_sessions"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    device = Column(String(255))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    location = Column(String(255))
    
    last_active = Column(DateTime)
    expires_at = Column(DateTime)
    is_current = Column(Boolean, default=False)
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")


class Team(BaseModel):
    """Team model for organizing users"""
    
    __tablename__ = "teams"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    lead_id = Column(Integer, ForeignKey("users.id"))
    
    # Extra data
    extra_data = Column(JSON)
    
    # Relationships
    organization = relationship("Organization")
    lead = relationship("User", foreign_keys=[lead_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class Role(BaseModel):
    """Role model for permissions"""
    
    __tablename__ = "roles"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    role_id = Column(String(50), nullable=False, index=True)  # admin, breeder, technician, viewer
    name = Column(String(100), nullable=False)
    description = Column(Text)
    permissions = Column(JSON)  # List of permission strings
    color = Column(String(20))  # For UI display
    is_system = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted
    
    # Relationships
    organization = relationship("Organization")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(BaseModel):
    """Association table for User-Role many-to-many relationship"""
    
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    granted_at = Column(DateTime, server_default="now()")
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    
    __table_args__ = (
        {'extend_existing': True}
    )


class TeamMember(BaseModel):
    """Team membership model"""
    
    __tablename__ = "team_members"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    role = Column(String(50), default="viewer")  # admin, breeder, technician, viewer
    status = Column(String(20), default="active")  # active, pending, inactive
    joined_at = Column(DateTime)
    last_active = Column(DateTime)
    
    # Relationships
    organization = relationship("Organization")
    team = relationship("Team", back_populates="members")
    user = relationship("User")


class TeamInvitation(BaseModel):
    """Team invitation model"""
    
    __tablename__ = "team_invitations"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), default="viewer")
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    invited_by_id = Column(Integer, ForeignKey("users.id"))
    sent_at = Column(DateTime)
    expires_at = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, accepted, expired, cancelled
    
    # Token for accepting invitation
    token = Column(String(255), unique=True, index=True)
    
    # Relationships
    organization = relationship("Organization")
    team = relationship("Team")
    invited_by = relationship("User")


class ActivityLog(BaseModel):
    """User activity log for audit trail"""
    
    __tablename__ = "activity_logs"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    action = Column(String(100), nullable=False, index=True)  # login, logout, create, update, delete
    entity_type = Column(String(100))  # trial, germplasm, observation, etc.
    entity_id = Column(String(255))
    details = Column(Text)
    
    # Request metadata
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
