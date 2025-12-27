"""
DevGuru (देवगुरु) - AI PhD Mentor API

API endpoints for the DevGuru PhD mentoring system.
Works as a specialized mode within Veena AI.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from app.services.devguru_service import (
    get_devguru_service,
    ResearchPhase,
    MilestoneStatus
)
from app.services.llm_service import get_llm_service

router = APIRouter(prefix="/devguru", tags=["DevGuru PhD Mentor"])


# ============================================
# SCHEMAS
# ============================================

class ProjectCreate(BaseModel):
    """Schema for creating a research project"""
    title: str = Field(..., description="Research project title")
    student_name: str = Field(..., description="PhD student name")
    supervisor: str = Field(..., description="Supervisor name")
    start_date: date = Field(..., description="Project start date")
    expected_end_date: date = Field(..., description="Expected completion date")
    research_area: str = Field(..., description="Research area/field")
    objectives: List[str] = Field(default=[], description="Research objectives")


class MilestoneUpdate(BaseModel):
    """Schema for updating a milestone"""
    status: Optional[MilestoneStatus] = None
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


# ============================================
# PROJECT ENDPOINTS
# ============================================

@router.get("/projects")
async def list_projects():
    """List all research projects"""
    service = get_devguru_service()
    projects = service.list_projects()
    return {
        "projects": [p.to_dict() for p in projects],
        "total": len(projects)
    }


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific research project"""
    service = get_devguru_service()
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.post("/projects")
async def create_project(data: ProjectCreate):
    """Create a new research project"""
    service = get_devguru_service()
    project = service.create_project(
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
async def get_milestones(project_id: str):
    """Get all milestones for a project"""
    service = get_devguru_service()
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "milestones": [m.to_dict() for m in project.milestones],
        "total": len(project.milestones)
    }


@router.put("/projects/{project_id}/milestones/{milestone_id}")
async def update_milestone(project_id: str, milestone_id: str, data: MilestoneUpdate):
    """Update a milestone"""
    service = get_devguru_service()
    milestone = service.update_milestone(
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
async def get_timeline_analysis(project_id: str):
    """Get timeline analysis for a project"""
    service = get_devguru_service()
    analysis = service.get_timeline_analysis(project_id)
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    return analysis


@router.get("/projects/{project_id}/suggestions")
async def get_mentoring_suggestions(project_id: str):
    """Get contextual mentoring suggestions based on current phase"""
    service = get_devguru_service()
    suggestions = service.get_mentoring_suggestions(project_id)
    return {
        "suggestions": suggestions,
        "total": len(suggestions)
    }


# ============================================
# CHAT ENDPOINT (DevGuru Mode)
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def devguru_chat(request: ChatRequest):
    """
    Chat with DevGuru - PhD mentoring mode.
    
    Uses the DevGuru system prompt and optionally includes
    project context for personalized guidance.
    """
    devguru_service = get_devguru_service()
    llm_service = get_llm_service()
    
    # Get project context if provided
    project = None
    if request.project_id:
        project = devguru_service.get_project(request.project_id)
    
    # Build messages with DevGuru system prompt
    system_prompt = devguru_service.get_system_prompt(project)
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    if request.conversation_history:
        for msg in request.conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # Add current message
    messages.append({"role": "user", "content": request.message})
    
    # Generate response
    response = await llm_service.generate(messages)
    
    # Get suggestions if we have a project
    suggestions = None
    if project:
        suggestions = devguru_service.get_mentoring_suggestions(request.project_id)
    
    return ChatResponse(
        message=response.content,
        provider=response.provider.value,
        model=response.model,
        cached=response.cached,
        suggestions=suggestions
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
async def get_devguru_status():
    """Get DevGuru service status"""
    devguru_service = get_devguru_service()
    llm_service = get_llm_service()
    
    llm_status = await llm_service.get_status()
    projects = devguru_service.list_projects()
    
    return {
        "devguru": {
            "available": True,
            "projects_count": len(projects)
        },
        "llm": llm_status
    }
