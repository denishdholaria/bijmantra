"""
DevGuru Database Models

Models for PhD research project tracking and mentoring.
Phases 1-5: Foundation, BrAPI Integration, Literature, Writing, Collaboration
"""

from sqlalchemy import Column, String, Integer, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base


class ResearchPhase(str, Enum):
    """PhD research phases"""
    COURSEWORK = "coursework"
    LITERATURE_REVIEW = "literature_review"
    PROPOSAL = "proposal"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    WRITING = "writing"
    DEFENSE = "defense"


class MilestoneStatus(str, Enum):
    """Milestone completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    AT_RISK = "at_risk"


class ReadStatus(str, Enum):
    """Paper read status"""
    UNREAD = "unread"
    READING = "reading"
    READ = "read"


class ChapterType(str, Enum):
    """Thesis chapter types"""
    INTRODUCTION = "introduction"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"


class ChapterStatus(str, Enum):
    """Chapter writing status"""
    NOT_STARTED = "not_started"
    DRAFTING = "drafting"
    REVIEW = "review"
    REVISION = "revision"
    COMPLETE = "complete"


class CommitteeRole(str, Enum):
    """Committee member roles"""
    SUPERVISOR = "supervisor"
    CO_SUPERVISOR = "co_supervisor"
    COMMITTEE = "committee"
    EXTERNAL = "external"


class MeetingType(str, Enum):
    """Meeting types"""
    PROGRESS = "progress"
    PROPOSAL = "proposal"
    DEFENSE = "defense"
    INFORMAL = "informal"


class MeetingStatus(str, Enum):
    """Meeting status"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FeedbackType(str, Enum):
    """Feedback types"""
    SUGGESTION = "suggestion"
    CORRECTION = "correction"
    QUESTION = "question"
    PRAISE = "praise"


class FeedbackPriority(str, Enum):
    """Feedback priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackStatus(str, Enum):
    """Feedback status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ADDRESSED = "addressed"
    DISMISSED = "dismissed"


class LinkType(str, Enum):
    """Paper-experiment link types"""
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    EXTENDS = "extends"
    METHODOLOGY = "methodology"


# ============================================
# PHASE 1: FOUNDATION
# ============================================

class ResearchProject(Base):
    """A PhD research project"""
    __tablename__ = "research_projects"

    id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    student_name = Column(String(200), nullable=False)
    supervisor = Column(String(200), nullable=True)
    start_date = Column(Date, nullable=False)
    expected_end_date = Column(Date, nullable=False)
    current_phase = Column(String(50), default=ResearchPhase.COURSEWORK.value)
    research_area = Column(String(200), nullable=True)
    objectives = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    milestones = relationship("ResearchMilestone", back_populates="project", cascade="all, delete-orphan")
    papers = relationship("ResearchPaper", back_populates="project", cascade="all, delete-orphan")
    chapters = relationship("ThesisChapter", back_populates="project", cascade="all, delete-orphan")
    committee_members = relationship("CommitteeMember", back_populates="project", cascade="all, delete-orphan")
    meetings = relationship("CommitteeMeeting", back_populates="project", cascade="all, delete-orphan")
    feedback_items = relationship("FeedbackItem", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "title": self.title,
            "student_name": self.student_name,
            "supervisor": self.supervisor,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "expected_end_date": self.expected_end_date.isoformat() if self.expected_end_date else None,
            "current_phase": self.current_phase,
            "research_area": self.research_area,
            "objectives": json.loads(self.objectives) if self.objectives else [],
            "milestones": [m.to_dict() for m in self.milestones],
            "notes": self.notes,
            "progress_percentage": self.calculate_progress(),
            "program_id": self.program_id
        }

    def calculate_progress(self) -> int:
        if not self.milestones:
            return 0
        completed = sum(1 for m in self.milestones if m.status == MilestoneStatus.COMPLETED.value)
        return int((completed / len(self.milestones)) * 100)


class ResearchMilestone(Base):
    """A milestone within a research project"""
    __tablename__ = "research_milestones"

    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    phase = Column(String(50), nullable=False)
    target_date = Column(Date, nullable=False)
    completed_date = Column(Date, nullable=True)
    status = Column(String(50), default=MilestoneStatus.NOT_STARTED.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("ResearchProject", back_populates="milestones")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "phase": self.phase,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "status": self.status,
            "notes": self.notes
        }


# ============================================
# PHASE 3: LITERATURE INTEGRATION
# ============================================

class ResearchPaper(Base):
    """A research paper linked to a project"""
    __tablename__ = "research_papers"

    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(Text)  # JSON array
    journal = Column(String(300))
    year = Column(Integer)
    doi = Column(String(200))
    url = Column(String(500))
    abstract = Column(Text)
    notes = Column(Text)
    tags = Column(Text)  # JSON array
    relevance_score = Column(Integer)  # 1-5
    read_status = Column(String(50), default=ReadStatus.UNREAD.value)
    citation_key = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("ResearchProject", back_populates="papers")
    experiment_links = relationship("PaperExperimentLink", back_populates="paper", cascade="all, delete-orphan")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "title": self.title,
            "authors": json.loads(self.authors) if self.authors else [],
            "journal": self.journal,
            "year": self.year,
            "doi": self.doi,
            "url": self.url,
            "abstract": self.abstract,
            "notes": self.notes,
            "tags": json.loads(self.tags) if self.tags else [],
            "relevance_score": self.relevance_score,
            "read_status": self.read_status,
            "citation_key": self.citation_key
        }


class PaperExperimentLink(Base):
    """Link between a paper and an experiment (trial/study)"""
    __tablename__ = "paper_experiment_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey("research_papers.id", ondelete="CASCADE"), nullable=False)
    trial_id = Column(Integer, ForeignKey("trials.id", ondelete="CASCADE"), nullable=True)
    study_id = Column(Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=True)
    link_type = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    paper = relationship("ResearchPaper", back_populates="experiment_links")

    def to_dict(self):
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "trial_id": self.trial_id,
            "study_id": self.study_id,
            "link_type": self.link_type,
            "notes": self.notes
        }


# ============================================
# PHASE 4: WRITING ASSISTANT
# ============================================

class ThesisChapter(Base):
    """A thesis chapter"""
    __tablename__ = "thesis_chapters"

    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    chapter_type = Column(String(50))
    target_word_count = Column(Integer, default=5000)
    current_word_count = Column(Integer, default=0)
    status = Column(String(50), default=ChapterStatus.NOT_STARTED.value)
    outline = Column(Text)  # JSON structure
    notes = Column(Text)
    target_date = Column(Date)
    completed_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("ResearchProject", back_populates="chapters")
    writing_sessions = relationship("WritingSession", back_populates="chapter", cascade="all, delete-orphan")
    feedback_items = relationship("FeedbackItem", back_populates="chapter")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "chapter_number": self.chapter_number,
            "title": self.title,
            "chapter_type": self.chapter_type,
            "target_word_count": self.target_word_count,
            "current_word_count": self.current_word_count,
            "progress_percentage": int((self.current_word_count / self.target_word_count) * 100) if self.target_word_count > 0 else 0,
            "status": self.status,
            "outline": json.loads(self.outline) if self.outline else None,
            "notes": self.notes,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None
        }


class WritingSession(Base):
    """A writing session for a chapter"""
    __tablename__ = "writing_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(String(50), ForeignKey("thesis_chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    session_date = Column(Date, nullable=False)
    words_written = Column(Integer, default=0)
    duration_minutes = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    chapter = relationship("ThesisChapter", back_populates="writing_sessions")

    def to_dict(self):
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "session_date": self.session_date.isoformat() if self.session_date else None,
            "words_written": self.words_written,
            "duration_minutes": self.duration_minutes,
            "notes": self.notes
        }


# ============================================
# PHASE 5: COLLABORATION
# ============================================

class CommitteeMember(Base):
    """A committee member"""
    __tablename__ = "committee_members"

    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255))
    role = Column(String(50))
    institution = Column(String(300))
    expertise = Column(String(300))
    notes = Column(Text)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("ResearchProject", back_populates="committee_members")
    feedback_items = relationship("FeedbackItem", back_populates="from_member")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "institution": self.institution,
            "expertise": self.expertise,
            "notes": self.notes,
            "is_primary": self.is_primary
        }


class CommitteeMeeting(Base):
    """A committee meeting"""
    __tablename__ = "committee_meetings"

    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    meeting_type = Column(String(50))
    scheduled_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    location = Column(String(300))
    agenda = Column(Text)
    minutes = Column(Text)
    action_items = Column(Text)  # JSON array
    status = Column(String(50), default=MeetingStatus.SCHEDULED.value)
    attendees = Column(Text)  # JSON array of committee_member IDs
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("ResearchProject", back_populates="meetings")
    feedback_items = relationship("FeedbackItem", back_populates="meeting")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "title": self.title,
            "meeting_type": self.meeting_type,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "agenda": self.agenda,
            "minutes": self.minutes,
            "action_items": json.loads(self.action_items) if self.action_items else [],
            "status": self.status,
            "attendees": json.loads(self.attendees) if self.attendees else []
        }


class FeedbackItem(Base):
    """Feedback from committee members"""
    __tablename__ = "feedback_items"

    id = Column(String(50), primary_key=True)
    project_id = Column(String(50), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(String(50), ForeignKey("thesis_chapters.id", ondelete="SET NULL"), nullable=True)
    meeting_id = Column(String(50), ForeignKey("committee_meetings.id", ondelete="SET NULL"), nullable=True)
    from_member_id = Column(String(50), ForeignKey("committee_members.id", ondelete="SET NULL"), nullable=True)
    feedback_type = Column(String(50))
    priority = Column(String(50), default=FeedbackPriority.MEDIUM.value)
    content = Column(Text, nullable=False)
    response = Column(Text)
    status = Column(String(50), default=FeedbackStatus.PENDING.value)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("ResearchProject", back_populates="feedback_items")
    chapter = relationship("ThesisChapter", back_populates="feedback_items")
    meeting = relationship("CommitteeMeeting", back_populates="feedback_items")
    from_member = relationship("CommitteeMember", back_populates="feedback_items")

    def to_dict(self):
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "meeting_id": self.meeting_id,
            "from_member_id": self.from_member_id,
            "from_member_name": self.from_member.name if self.from_member else None,
            "feedback_type": self.feedback_type,
            "priority": self.priority,
            "content": self.content,
            "response": self.response,
            "status": self.status
        }
