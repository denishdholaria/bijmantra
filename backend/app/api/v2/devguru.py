"""
DevGuru - AI PhD Mentor API

API endpoints for the DevGuru PhD mentoring system.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from app.services.devguru_service import get_devguru_service
from app.models.devguru import ResearchPhase, MilestoneStatus
from app.services.ai.engine import get_llm_service

router = APIRouter(prefix="/devguru", tags=["DevGuru PhD Mentor"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class ProjectCreate(BaseModel):
    """Schema for creating a research project"""
    title: str = Field(..., description="Research project title")
    student_name: str = Field(..., description="PhD student name")
    supervisor: str = Field(default="", description="Supervisor name")
    start_date: date = Field(..., description="Project start date")
    expected_end_date: date = Field(..., description="Expected completion date")
    research_area: str = Field(default="", description="Research area/field")
    objectives: List[str] = Field(default=[], description="Research objectives")


class MilestoneUpdate(BaseModel):
    """Schema for updating a milestone"""
    status: Optional[str] = None
    completed_date: Optional[date] = None
    notes: Optional[str] = None


class ChatRequest(BaseModel):
    """Schema for DevGuru chat request"""
    message: str = Field(..., description="User message")
    project_id: Optional[str] = Field(None, description="Active project ID for context")
    conversation_history: Optional[List[dict]] = Field(default=[], description="Previous messages")


class ChatResponse(BaseModel):
    """Schema for DevGuru chat response"""
    message: str
    provider: str
    model: str
    cached: bool = False
    suggestions: Optional[List[dict]] = None
    sources: Optional[List[dict]] = None  # RAG sources
    reasoning: Optional[str] = None  # Scribe Reasoning Trace




class ExplainRequest(BaseModel):
    """Schema for explaining a concept"""
    concept: str = Field(..., description="Concept or method to explain")


class RecommendRequest(BaseModel):
    """Schema for requesting a recommendation"""
    scenario: str = Field(..., description="Research scenario or problem")
    project_id: Optional[str] = Field(None, description="Optional project ID for context")


# ============================================
# PROJECT ENDPOINTS
# ============================================

@router.get("/projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all research projects"""
    service = get_devguru_service(db)
    projects = await service.list_projects()
    return {
        "projects": [p.to_dict() for p in projects],
        "total": len(projects)
    }


@router.get("/projects/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific research project"""
    service = get_devguru_service(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.post("/projects")
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new research project"""
    service = get_devguru_service(db)
    project = await service.create_project(
        title=data.title,
        student_name=data.student_name,
        supervisor=data.supervisor,
        start_date=data.start_date,
        expected_end_date=data.expected_end_date,
        research_area=data.research_area,
        objectives=data.objectives
    )
    return {
        "message": "Project created successfully",
        "project": project.to_dict()
    }


# ============================================
# MILESTONE ENDPOINTS
# ============================================

@router.get("/projects/{project_id}/milestones")
async def get_milestones(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get all milestones for a project"""
    service = get_devguru_service(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "milestones": [m.to_dict() for m in project.milestones],
        "total": len(project.milestones)
    }


@router.put("/projects/{project_id}/milestones/{milestone_id}")
async def update_milestone(project_id: str, milestone_id: str, data: MilestoneUpdate, db: AsyncSession = Depends(get_db)):
    """Update a milestone"""
    service = get_devguru_service(db)
    milestone = await service.update_milestone(
        project_id=project_id,
        milestone_id=milestone_id,
        status=data.status,
        completed_date=data.completed_date,
        notes=data.notes
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return {
        "message": "Milestone updated",
        "milestone": milestone.to_dict()
    }


# ============================================
# ANALYSIS ENDPOINTS
# ============================================

@router.get("/projects/{project_id}/timeline")
async def get_timeline_analysis(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get timeline analysis for a project"""
    service = get_devguru_service(db)
    analysis = await service.get_timeline_analysis(project_id)
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    return analysis


@router.get("/projects/{project_id}/suggestions")
async def get_mentoring_suggestions(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get contextual mentoring suggestions based on current phase"""
    service = get_devguru_service(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    suggestions = service.get_mentoring_suggestions(project)
    return {
        "suggestions": suggestions,
        "total": len(suggestions)
    }


# ============================================
# CHAT ENDPOINT
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def devguru_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat with DevGuru - PhD mentoring mode (Savant RAG enabled)."""
    devguru_service = get_devguru_service(db)

    user_id = current_user.id
    org_id = current_user.organization_id

    # Process with RAG (Savant)
    rag_response = await devguru_service.generate_rag_response(
        project_id=request.project_id,
        query=request.message,
        user_id=user_id,
        organization_id=org_id,
        conversation_history=request.conversation_history
    )

    # Get suggestions if we have a project
    suggestions = None
    if request.project_id:
        project = await devguru_service.get_project(request.project_id)
        if project:
            suggestions = devguru_service.get_mentoring_suggestions(project)

    return ChatResponse(
        message=rag_response["message"],
        provider=rag_response["provider"],
        model="savant-rag",
        cached=False,
        suggestions=suggestions,
        sources=rag_response.get("sources"),
        reasoning=rag_response.get("reasoning")
    )


# ============================================
# REFERENCE DATA
# ============================================

@router.get("/phases")
async def get_research_phases():
    """Get list of research phases"""
    return {
        "phases": [
            {"value": phase.value, "label": phase.value.replace("_", " ").title()}
            for phase in ResearchPhase
        ]
    }


@router.get("/milestone-statuses")
async def get_milestone_statuses():
    """Get list of milestone statuses"""
    return {
        "statuses": [
            {"value": status.value, "label": status.value.replace("_", " ").title()}
            for status in MilestoneStatus
        ]
    }


@router.get("/status")
async def get_devguru_status(db: AsyncSession = Depends(get_db)):
    """Get DevGuru service status"""
    devguru_service = get_devguru_service(db)
    llm_service = get_llm_service()

    llm_status = await llm_service.get_status()
    projects = await devguru_service.list_projects()

    return {
        "devguru": {
            "available": True,
            "projects_count": len(projects)
        },
        "llm": llm_status
    }


# ============================================
# BRAPI INTEGRATION ENDPOINTS (Phase 2)
# ============================================

class LinkProgramRequest(BaseModel):
    """Schema for linking a project to a BrAPI Program"""
    program_id: int = Field(..., description="BrAPI Program ID to link")


@router.post("/projects/{project_id}/link-program")
async def link_project_to_program(project_id: str, request: LinkProgramRequest, db: AsyncSession = Depends(get_db)):
    """Link a research project to a BrAPI Program for experiment tracking"""
    service = get_devguru_service(db)
    project = await service.link_program(project_id, request.program_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project or Program not found")
    return {
        "message": "Project linked to program successfully",
        "project": project.to_dict()
    }


@router.get("/projects/{project_id}/experiments")
async def get_project_experiments(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get all experiments (trials) linked to a research project"""
    service = get_devguru_service(db)
    experiments = await service.get_project_experiments(project_id)
    return {
        "experiments": experiments,
        "total": len(experiments)
    }


@router.get("/experiments/{trial_id}/studies")
async def get_experiment_studies(trial_id: int, db: AsyncSession = Depends(get_db)):
    """Get all studies (sub-experiments) in a trial/experiment"""
    service = get_devguru_service(db)
    studies = await service.get_experiment_studies(trial_id)
    return {
        "studies": studies,
        "total": len(studies)
    }


@router.get("/projects/{project_id}/synthesis")
async def get_project_synthesis(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get AI synthesis of research progress across all experiments"""
    devguru_service = get_devguru_service(db)
    llm_service = get_llm_service()

    # Get synthesis context
    context = await devguru_service.get_synthesis_context(project_id)
    if "error" in context:
        raise HTTPException(status_code=404, detail=context["error"])

    # If no experiments linked, return context without synthesis
    if context["summary"]["total_experiments"] == 0:
        return {
            "context": context,
            "synthesis": None,
            "message": "No experiments linked yet. Link a BrAPI Program to enable synthesis."
        }

    # Generate synthesis using LLM
    synthesis_prompt = devguru_service.get_synthesis_prompt(context)
    messages = [
        {"role": "system", "content": "You are DevGuru, an AI research mentor. Provide concise, actionable synthesis."},
        {"role": "user", "content": synthesis_prompt}
    ]

    response = await llm_service.generate(messages)

    return {
        "context": context,
        "synthesis": {
            "content": response.content,
            "provider": response.provider.value,
            "model": response.model
        }
    }


@router.get("/programs/research")
async def get_research_programs(db: AsyncSession = Depends(get_db)):
    """Get all BrAPI Programs marked as research projects"""
    service = get_devguru_service(db)
    programs = await service.get_research_programs()
    return {
        "programs": [
            {
                "id": p.id,
                "program_db_id": p.program_db_id,
                "program_name": p.program_name,
                "objective": p.objective,
                "research_context": p.research_context,
                "trials_count": len(p.trials) if p.trials else 0
            }
            for p in programs
        ],
        "total": len(programs)
    }


# ============================================
# PHASE 3: LITERATURE ENDPOINTS
# ============================================

class PaperCreate(BaseModel):
    """Schema for adding a paper"""
    title: str = Field(..., description="Paper title")
    authors: Optional[List[str]] = Field(default=[], description="Author names")
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = Field(default=[], description="Tags for categorization")
    relevance_score: Optional[int] = Field(None, ge=1, le=5, description="Relevance 1-5")
    citation_key: Optional[str] = None


class PaperUpdate(BaseModel):
    """Schema for updating a paper"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    relevance_score: Optional[int] = Field(None, ge=1, le=5)
    read_status: Optional[str] = None
    citation_key: Optional[str] = None


class PaperExperimentLinkCreate(BaseModel):
    """Schema for linking paper to experiment"""
    trial_id: Optional[int] = None
    study_id: Optional[int] = None
    link_type: str = Field(default="supports", description="supports, contradicts, extends, methodology")
    notes: Optional[str] = None


@router.get("/projects/{project_id}/papers")
async def list_papers(project_id: str, db: AsyncSession = Depends(get_db)):
    """List all papers for a research project"""
    service = get_devguru_service(db)
    papers = await service.list_papers(project_id)
    return {"papers": papers, "total": len(papers)}


@router.post("/projects/{project_id}/papers")
async def add_paper(project_id: str, data: PaperCreate, db: AsyncSession = Depends(get_db)):
    """Add a paper to a research project"""
    service = get_devguru_service(db)
    paper = await service.add_paper(
        project_id=project_id,
        title=data.title,
        authors=data.authors,
        journal=data.journal,
        year=data.year,
        doi=data.doi,
        url=data.url,
        abstract=data.abstract,
        notes=data.notes,
        tags=data.tags,
        relevance_score=data.relevance_score,
        citation_key=data.citation_key
    )
    return {"message": "Paper added", "paper": paper}


@router.put("/papers/{paper_id}")
async def update_paper(paper_id: str, data: PaperUpdate, db: AsyncSession = Depends(get_db)):
    """Update a paper"""
    service = get_devguru_service(db)
    paper = await service.update_paper(paper_id, **data.model_dump(exclude_none=True))
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"message": "Paper updated", "paper": paper}


@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a paper"""
    service = get_devguru_service(db)
    success = await service.delete_paper(paper_id)
    if not success:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"message": "Paper deleted"}


@router.post("/papers/{paper_id}/link-experiment")
async def link_paper_to_experiment(paper_id: str, data: PaperExperimentLinkCreate, db: AsyncSession = Depends(get_db)):
    """Link a paper to an experiment (trial or study)"""
    service = get_devguru_service(db)
    link = await service.link_paper_to_experiment(
        paper_id=paper_id,
        trial_id=data.trial_id,
        study_id=data.study_id,
        link_type=data.link_type,
        notes=data.notes
    )
    return {"message": "Paper linked to experiment", "link": link}


@router.get("/projects/{project_id}/literature-stats")
async def get_literature_stats(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get literature statistics for a project"""
    service = get_devguru_service(db)
    stats = await service.get_literature_stats(project_id)
    return stats


# ============================================
# PHASE 4: WRITING ENDPOINTS
# ============================================

class ChapterCreate(BaseModel):
    """Schema for creating a chapter"""
    chapter_number: int = Field(..., ge=1)
    title: str
    chapter_type: Optional[str] = None
    target_word_count: int = Field(default=5000, ge=0)
    outline: Optional[List[dict]] = None
    target_date: Optional[date] = None


class ChapterUpdate(BaseModel):
    """Schema for updating a chapter"""
    title: Optional[str] = None
    chapter_type: Optional[str] = None
    target_word_count: Optional[int] = Field(None, ge=0)
    current_word_count: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    outline: Optional[List[dict]] = None
    target_date: Optional[date] = None
    notes: Optional[str] = None


class WritingSessionCreate(BaseModel):
    """Schema for logging a writing session"""
    words_written: int = Field(..., ge=0)
    duration_minutes: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


@router.get("/projects/{project_id}/chapters")
async def list_chapters(project_id: str, db: AsyncSession = Depends(get_db)):
    """List all thesis chapters for a project"""
    service = get_devguru_service(db)
    chapters = await service.list_chapters(project_id)
    return {"chapters": chapters, "total": len(chapters)}


@router.post("/projects/{project_id}/chapters")
async def create_chapter(project_id: str, data: ChapterCreate, db: AsyncSession = Depends(get_db)):
    """Create a thesis chapter"""
    service = get_devguru_service(db)
    chapter = await service.create_chapter(
        project_id=project_id,
        chapter_number=data.chapter_number,
        title=data.title,
        chapter_type=data.chapter_type,
        target_word_count=data.target_word_count,
        outline=data.outline,
        target_date=data.target_date
    )
    return {"message": "Chapter created", "chapter": chapter}


@router.post("/projects/{project_id}/chapters/generate-defaults")
async def generate_default_chapters(project_id: str, db: AsyncSession = Depends(get_db)):
    """Generate default thesis chapters (Introduction, Literature Review, etc.)"""
    service = get_devguru_service(db)
    chapters = await service.generate_default_chapters(project_id)
    return {"message": "Default chapters generated", "chapters": chapters, "total": len(chapters)}


@router.put("/chapters/{chapter_id}")
async def update_chapter(chapter_id: str, data: ChapterUpdate, db: AsyncSession = Depends(get_db)):
    """Update a chapter"""
    service = get_devguru_service(db)
    chapter = await service.update_chapter(chapter_id, **data.model_dump(exclude_none=True))
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return {"message": "Chapter updated", "chapter": chapter}


@router.post("/chapters/{chapter_id}/sessions")
async def log_writing_session(chapter_id: str, data: WritingSessionCreate, db: AsyncSession = Depends(get_db)):
    """Log a writing session for a chapter"""
    service = get_devguru_service(db)
    result = await service.log_writing_session(
        chapter_id=chapter_id,
        words_written=data.words_written,
        duration_minutes=data.duration_minutes,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/projects/{project_id}/writing-stats")
async def get_writing_stats(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get writing statistics for a project"""
    service = get_devguru_service(db)
    stats = await service.get_writing_stats(project_id)
    return stats


# ============================================
# PHASE 5: COLLABORATION ENDPOINTS
# ============================================

class CommitteeMemberCreate(BaseModel):
    """Schema for adding a committee member"""
    name: str
    email: Optional[str] = None
    role: str = Field(default="committee", description="chair, co_chair, committee, external")
    institution: Optional[str] = None
    expertise: Optional[str] = None
    is_primary: bool = False


class CommitteeMemberUpdate(BaseModel):
    """Schema for updating a committee member"""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    institution: Optional[str] = None
    expertise: Optional[str] = None
    is_primary: Optional[bool] = None


class MeetingCreate(BaseModel):
    """Schema for scheduling a meeting"""
    title: str
    scheduled_date: str = Field(..., description="ISO format datetime")
    meeting_type: str = Field(default="progress", description="progress, proposal, defense, other")
    duration_minutes: int = Field(default=60, ge=15)
    location: Optional[str] = None
    agenda: Optional[str] = None
    attendees: Optional[List[str]] = None


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting"""
    title: Optional[str] = None
    scheduled_date: Optional[str] = None
    meeting_type: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=15)
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    action_items: Optional[List[str]] = None
    attendees: Optional[List[str]] = None


class FeedbackCreate(BaseModel):
    """Schema for adding feedback"""
    content: str
    feedback_type: str = Field(default="suggestion", description="suggestion, revision, question, approval")
    priority: str = Field(default="medium", description="low, medium, high, critical")
    chapter_id: Optional[str] = None
    meeting_id: Optional[str] = None
    from_member_id: Optional[str] = None


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback"""
    content: Optional[str] = None
    feedback_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    response: Optional[str] = None


@router.get("/projects/{project_id}/committee")
async def list_committee_members(project_id: str, db: AsyncSession = Depends(get_db)):
    """List all committee members for a project"""
    service = get_devguru_service(db)
    members = await service.list_committee_members(project_id)
    return {"members": members, "total": len(members)}


@router.post("/projects/{project_id}/committee")
async def add_committee_member(project_id: str, data: CommitteeMemberCreate, db: AsyncSession = Depends(get_db)):
    """Add a committee member"""
    service = get_devguru_service(db)
    member = await service.add_committee_member(
        project_id=project_id,
        name=data.name,
        email=data.email,
        role=data.role,
        institution=data.institution,
        expertise=data.expertise,
        is_primary=data.is_primary
    )
    return {"message": "Committee member added", "member": member}


@router.put("/committee/{member_id}")
async def update_committee_member(member_id: str, data: CommitteeMemberUpdate, db: AsyncSession = Depends(get_db)):
    """Update a committee member"""
    service = get_devguru_service(db)
    member = await service.update_committee_member(member_id, **data.model_dump(exclude_none=True))
    if not member:
        raise HTTPException(status_code=404, detail="Committee member not found")
    return {"message": "Committee member updated", "member": member}


@router.get("/projects/{project_id}/meetings")
async def list_meetings(project_id: str, db: AsyncSession = Depends(get_db)):
    """List all meetings for a project"""
    service = get_devguru_service(db)
    meetings = await service.list_meetings(project_id)
    return {"meetings": meetings, "total": len(meetings)}


@router.post("/projects/{project_id}/meetings")
async def schedule_meeting(project_id: str, data: MeetingCreate, db: AsyncSession = Depends(get_db)):
    """Schedule a committee meeting"""
    service = get_devguru_service(db)
    meeting = await service.schedule_meeting(
        project_id=project_id,
        title=data.title,
        scheduled_date=data.scheduled_date,
        meeting_type=data.meeting_type,
        duration_minutes=data.duration_minutes,
        location=data.location,
        agenda=data.agenda,
        attendees=data.attendees
    )
    return {"message": "Meeting scheduled", "meeting": meeting}


@router.put("/meetings/{meeting_id}")
async def update_meeting(meeting_id: str, data: MeetingUpdate, db: AsyncSession = Depends(get_db)):
    """Update a meeting"""
    service = get_devguru_service(db)
    update_data = data.model_dump(exclude_none=True)
    meeting = await service.update_meeting(meeting_id, **update_data)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"message": "Meeting updated", "meeting": meeting}


@router.get("/projects/{project_id}/feedback")
async def list_feedback(project_id: str, status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List feedback items for a project"""
    service = get_devguru_service(db)
    feedback = await service.list_feedback(project_id, status=status)
    return {"feedback": feedback, "total": len(feedback)}


@router.post("/projects/{project_id}/feedback")
async def add_feedback(project_id: str, data: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    """Add a feedback item"""
    service = get_devguru_service(db)
    feedback = await service.add_feedback(
        project_id=project_id,
        content=data.content,
        feedback_type=data.feedback_type,
        priority=data.priority,
        chapter_id=data.chapter_id,
        meeting_id=data.meeting_id,
        from_member_id=data.from_member_id
    )
    return {"message": "Feedback added", "feedback": feedback}


@router.put("/feedback/{feedback_id}")
async def update_feedback(feedback_id: str, data: FeedbackUpdate, db: AsyncSession = Depends(get_db)):
    """Update a feedback item"""
    service = get_devguru_service(db)
    feedback = await service.update_feedback(feedback_id, **data.model_dump(exclude_none=True))
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"message": "Feedback updated", "feedback": feedback}


@router.get("/projects/{project_id}/collaboration-stats")
async def get_collaboration_stats(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get collaboration statistics for a project"""
    service = get_devguru_service(db)
    stats = await service.get_collaboration_stats(project_id)
    return stats


# ============================================
# PHASE 6: BREEDING SCIENCE ENDPOINTS
# ============================================

@router.get("/topics")
async def get_breeding_topics(db: AsyncSession = Depends(get_db)):
    """List available breeding science topics"""
    service = get_devguru_service(db)
    topics = service.get_topics()
    return {"topics": topics}


@router.post("/explain")
async def explain_concept(request: ExplainRequest, db: AsyncSession = Depends(get_db)):
    """Explain a breeding concept or method"""
    service = get_devguru_service(db)
    result = await service.explain_concept(request.concept)
    return result


@router.post("/recommend")
async def recommend_approach(request: RecommendRequest, db: AsyncSession = Depends(get_db)):
    """Recommend a breeding approach for a given scenario"""
    service = get_devguru_service(db)
    result = await service.recommend_approach(request.scenario, request.project_id)
    return result
