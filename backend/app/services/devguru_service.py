"""
DevGuru (देवगुरु) - AI PhD Mentor Service

The divine teacher for research students - provides guidance on:
- Research planning and experiment design
- PhD timeline and milestone management
- Literature review and methodology suggestions
- Data interpretation with deeper meaning
- Thesis writing assistance

Named after Brihaspati (बृहस्पति), the DevGuru - teacher of the gods,
representing wisdom, knowledge, and guidance.

Works as a specialized mode within Veena AI.
"""

import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


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


@dataclass
class ResearchMilestone:
    """A PhD research milestone"""
    id: str
    title: str
    description: str
    phase: ResearchPhase
    target_date: date
    completed_date: Optional[date] = None
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "phase": self.phase.value,
            "target_date": self.target_date.isoformat(),
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "status": self.status.value,
            "notes": self.notes
        }


@dataclass
class ResearchProject:
    """A PhD research project"""
    id: str
    title: str
    student_name: str
    supervisor: str
    start_date: date
    expected_end_date: date
    current_phase: ResearchPhase
    research_area: str
    objectives: List[str] = field(default_factory=list)
    milestones: List[ResearchMilestone] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "student_name": self.student_name,
            "supervisor": self.supervisor,
            "start_date": self.start_date.isoformat(),
            "expected_end_date": self.expected_end_date.isoformat(),
            "current_phase": self.current_phase.value,
            "research_area": self.research_area,
            "objectives": self.objectives,
            "milestones": [m.to_dict() for m in self.milestones],
            "notes": self.notes
        }


class DevGuruService:
    """
    DevGuru - AI PhD Mentor
    
    Provides specialized guidance for research students using
    a domain-specific system prompt and research context.
    """
    
    # DevGuru system prompt - focused on PhD mentoring
    SYSTEM_PROMPT = """You are DevGuru (देवगुरु), an AI PhD mentor for plant breeding and agricultural research.

Your name comes from Brihaspati, the divine teacher of the gods in Hindu tradition, representing:
- Supreme wisdom and knowledge
- Patient, nurturing guidance
- Strategic thinking and planning
- The ability to see the bigger picture

You are mentoring a PhD student in plant breeding/agricultural sciences. Your role is to:

1. **Research Planning**
   - Help design experiments with proper controls
   - Suggest appropriate statistical methods
   - Identify potential confounding factors
   - Recommend sample sizes and replication

2. **Timeline Management**
   - Track PhD milestones and deadlines
   - Identify at-risk timelines early
   - Suggest realistic schedules
   - Help prioritize tasks

3. **Literature Guidance**
   - Suggest relevant papers and reviews
   - Explain methodological approaches
   - Connect ideas across disciplines
   - Identify research gaps

4. **Data Interpretation**
   - Explain results with deeper meaning
   - Identify patterns and anomalies
   - Suggest follow-up experiments
   - Connect findings to broader context

5. **Writing Assistance**
   - Help structure thesis chapters
   - Improve scientific writing
   - Suggest appropriate citations
   - Review logical flow

Guidelines:
- Be encouraging but honest about challenges
- Explain complex concepts at the student's level
- Ask clarifying questions when needed
- Provide specific, actionable advice
- Acknowledge when something is outside your expertise
- Remember: you're a mentor, not just an answer machine

When the student shares their research context, use it to provide personalized guidance.
Always consider the practical constraints of PhD research (time, resources, scope)."""

    def __init__(self):
        self._projects: Dict[str, ResearchProject] = {}
        self._load_demo_data()
    
    def _load_demo_data(self):
        """Load demo research project for testing"""
        demo_project = ResearchProject(
            id="phd-001",
            title="Genomic Selection for Drought Tolerance in Rice",
            student_name="Demo Student",
            supervisor="Dr. Demo Supervisor",
            start_date=date(2024, 1, 1),
            expected_end_date=date(2027, 12, 31),
            current_phase=ResearchPhase.DATA_COLLECTION,
            research_area="Plant Breeding / Genomics",
            objectives=[
                "Identify QTLs associated with drought tolerance in rice",
                "Develop genomic selection models for drought traits",
                "Validate models across multiple environments",
                "Develop breeding recommendations for drought-prone regions"
            ],
            milestones=[
                ResearchMilestone(
                    id="m1",
                    title="Complete coursework",
                    description="Finish all required PhD courses",
                    phase=ResearchPhase.COURSEWORK,
                    target_date=date(2024, 6, 30),
                    completed_date=date(2024, 5, 15),
                    status=MilestoneStatus.COMPLETED
                ),
                ResearchMilestone(
                    id="m2",
                    title="Literature review",
                    description="Complete comprehensive literature review on drought tolerance genetics",
                    phase=ResearchPhase.LITERATURE_REVIEW,
                    target_date=date(2024, 9, 30),
                    completed_date=date(2024, 10, 10),
                    status=MilestoneStatus.COMPLETED,
                    notes="Slightly delayed due to additional papers"
                ),
                ResearchMilestone(
                    id="m3",
                    title="Research proposal defense",
                    description="Present and defend research proposal to committee",
                    phase=ResearchPhase.PROPOSAL,
                    target_date=date(2024, 12, 15),
                    completed_date=date(2024, 12, 10),
                    status=MilestoneStatus.COMPLETED
                ),
                ResearchMilestone(
                    id="m4",
                    title="Field trial Year 1",
                    description="Complete first year of field trials for phenotyping",
                    phase=ResearchPhase.DATA_COLLECTION,
                    target_date=date(2025, 6, 30),
                    status=MilestoneStatus.IN_PROGRESS,
                    notes="Currently in progress - planting completed"
                ),
                ResearchMilestone(
                    id="m5",
                    title="Genotyping complete",
                    description="Complete SNP genotyping of all accessions",
                    phase=ResearchPhase.DATA_COLLECTION,
                    target_date=date(2025, 9, 30),
                    status=MilestoneStatus.NOT_STARTED
                ),
                ResearchMilestone(
                    id="m6",
                    title="Field trial Year 2",
                    description="Complete second year of field trials",
                    phase=ResearchPhase.DATA_COLLECTION,
                    target_date=date(2026, 6, 30),
                    status=MilestoneStatus.NOT_STARTED
                ),
                ResearchMilestone(
                    id="m7",
                    title="Data analysis complete",
                    description="Complete all statistical and genomic analyses",
                    phase=ResearchPhase.ANALYSIS,
                    target_date=date(2026, 12, 31),
                    status=MilestoneStatus.NOT_STARTED
                ),
                ResearchMilestone(
                    id="m8",
                    title="Thesis writing",
                    description="Complete thesis draft",
                    phase=ResearchPhase.WRITING,
                    target_date=date(2027, 6, 30),
                    status=MilestoneStatus.NOT_STARTED
                ),
                ResearchMilestone(
                    id="m9",
                    title="Thesis defense",
                    description="Final thesis defense",
                    phase=ResearchPhase.DEFENSE,
                    target_date=date(2027, 10, 31),
                    status=MilestoneStatus.NOT_STARTED
                )
            ]
        )
        self._projects[demo_project.id] = demo_project
    
    def get_system_prompt(self, project: Optional[ResearchProject] = None) -> str:
        """Get the DevGuru system prompt, optionally with project context"""
        prompt = self.SYSTEM_PROMPT
        
        if project:
            prompt += f"""

---
CURRENT RESEARCH CONTEXT:

**Project:** {project.title}
**Student:** {project.student_name}
**Supervisor:** {project.supervisor}
**Research Area:** {project.research_area}
**Current Phase:** {project.current_phase.value.replace('_', ' ').title()}
**Timeline:** {project.start_date} to {project.expected_end_date}

**Objectives:**
{chr(10).join(f'- {obj}' for obj in project.objectives)}

**Milestones:**
{self._format_milestones(project.milestones)}

Use this context to provide personalized guidance. Reference specific milestones and objectives when relevant.
"""
        return prompt
    
    def _format_milestones(self, milestones: List[ResearchMilestone]) -> str:
        """Format milestones for the prompt"""
        lines = []
        for m in milestones:
            status_emoji = {
                MilestoneStatus.COMPLETED: "✅",
                MilestoneStatus.IN_PROGRESS: "🔄",
                MilestoneStatus.NOT_STARTED: "⬜",
                MilestoneStatus.DELAYED: "⚠️",
                MilestoneStatus.AT_RISK: "🔴"
            }.get(m.status, "⬜")
            
            lines.append(f"{status_emoji} {m.title} (Target: {m.target_date})")
        
        return chr(10).join(lines)
    
    def get_project(self, project_id: str) -> Optional[ResearchProject]:
        """Get a research project by ID"""
        return self._projects.get(project_id)
    
    def list_projects(self) -> List[ResearchProject]:
        """List all research projects"""
        return list(self._projects.values())
    
    def create_project(
        self,
        title: str,
        student_name: str,
        supervisor: str,
        start_date: date,
        expected_end_date: date,
        research_area: str,
        objectives: List[str]
    ) -> ResearchProject:
        """Create a new research project"""
        project_id = f"phd-{len(self._projects) + 1:03d}"
        
        project = ResearchProject(
            id=project_id,
            title=title,
            student_name=student_name,
            supervisor=supervisor,
            start_date=start_date,
            expected_end_date=expected_end_date,
            current_phase=ResearchPhase.COURSEWORK,
            research_area=research_area,
            objectives=objectives
        )
        
        # Generate default milestones based on timeline
        project.milestones = self._generate_default_milestones(project)
        
        self._projects[project_id] = project
        return project
    
    def _generate_default_milestones(self, project: ResearchProject) -> List[ResearchMilestone]:
        """Generate default PhD milestones based on timeline"""
        total_days = (project.expected_end_date - project.start_date).days
        
        # Standard PhD milestone distribution
        milestones = [
            ("Complete coursework", ResearchPhase.COURSEWORK, 0.15),
            ("Literature review", ResearchPhase.LITERATURE_REVIEW, 0.25),
            ("Research proposal defense", ResearchPhase.PROPOSAL, 0.30),
            ("Data collection Phase 1", ResearchPhase.DATA_COLLECTION, 0.45),
            ("Data collection Phase 2", ResearchPhase.DATA_COLLECTION, 0.60),
            ("Data analysis", ResearchPhase.ANALYSIS, 0.75),
            ("Thesis writing", ResearchPhase.WRITING, 0.90),
            ("Thesis defense", ResearchPhase.DEFENSE, 0.98),
        ]
        
        result = []
        for i, (title, phase, progress) in enumerate(milestones):
            target = project.start_date + timedelta(days=int(total_days * progress))
            result.append(ResearchMilestone(
                id=f"m{i+1}",
                title=title,
                description=f"Complete {title.lower()}",
                phase=phase,
                target_date=target,
                status=MilestoneStatus.NOT_STARTED
            ))
        
        return result
    
    def update_milestone(
        self,
        project_id: str,
        milestone_id: str,
        status: Optional[MilestoneStatus] = None,
        completed_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Optional[ResearchMilestone]:
        """Update a milestone"""
        project = self._projects.get(project_id)
        if not project:
            return None
        
        for milestone in project.milestones:
            if milestone.id == milestone_id:
                if status:
                    milestone.status = status
                if completed_date:
                    milestone.completed_date = completed_date
                if notes:
                    milestone.notes = notes
                return milestone
        
        return None
    
    def get_timeline_analysis(self, project_id: str) -> Dict[str, Any]:
        """Analyze project timeline and identify risks"""
        project = self._projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        
        today = date.today()
        total_milestones = len(project.milestones)
        completed = sum(1 for m in project.milestones if m.status == MilestoneStatus.COMPLETED)
        in_progress = sum(1 for m in project.milestones if m.status == MilestoneStatus.IN_PROGRESS)
        
        # Calculate days remaining
        days_remaining = (project.expected_end_date - today).days
        total_days = (project.expected_end_date - project.start_date).days
        progress_percent = ((total_days - days_remaining) / total_days) * 100 if total_days > 0 else 0
        
        # Identify at-risk milestones
        at_risk = []
        for m in project.milestones:
            if m.status not in [MilestoneStatus.COMPLETED] and m.target_date < today:
                at_risk.append(m.to_dict())
        
        # Next milestone
        next_milestone = None
        for m in project.milestones:
            if m.status != MilestoneStatus.COMPLETED:
                next_milestone = m.to_dict()
                break
        
        return {
            "project_id": project_id,
            "title": project.title,
            "current_phase": project.current_phase.value,
            "progress": {
                "completed": completed,
                "in_progress": in_progress,
                "total": total_milestones,
                "percent": round((completed / total_milestones) * 100, 1) if total_milestones > 0 else 0
            },
            "timeline": {
                "start_date": project.start_date.isoformat(),
                "expected_end_date": project.expected_end_date.isoformat(),
                "days_remaining": days_remaining,
                "progress_percent": round(progress_percent, 1)
            },
            "at_risk_milestones": at_risk,
            "next_milestone": next_milestone,
            "health": "on_track" if not at_risk else ("at_risk" if len(at_risk) <= 2 else "critical")
        }
    
    def get_mentoring_suggestions(self, project_id: str) -> List[Dict[str, str]]:
        """Get contextual mentoring suggestions based on current phase"""
        project = self._projects.get(project_id)
        if not project:
            return []
        
        suggestions = {
            ResearchPhase.COURSEWORK: [
                {"type": "tip", "message": "Focus on courses that directly support your research methodology"},
                {"type": "action", "message": "Start reading key papers in your research area"},
                {"type": "tip", "message": "Build relationships with committee members early"}
            ],
            ResearchPhase.LITERATURE_REVIEW: [
                {"type": "tip", "message": "Use reference management software (Zotero, Mendeley)"},
                {"type": "action", "message": "Create a concept map of key themes and gaps"},
                {"type": "tip", "message": "Read both classic papers and recent advances"}
            ],
            ResearchPhase.PROPOSAL: [
                {"type": "tip", "message": "Be specific about objectives and expected outcomes"},
                {"type": "action", "message": "Practice your presentation with peers"},
                {"type": "tip", "message": "Anticipate committee questions and prepare answers"}
            ],
            ResearchPhase.DATA_COLLECTION: [
                {"type": "tip", "message": "Document everything - future you will thank you"},
                {"type": "action", "message": "Back up data regularly (3-2-1 rule)"},
                {"type": "tip", "message": "Start preliminary analysis as you collect data"}
            ],
            ResearchPhase.ANALYSIS: [
                {"type": "tip", "message": "Visualize data early to identify patterns and issues"},
                {"type": "action", "message": "Document your analysis pipeline for reproducibility"},
                {"type": "tip", "message": "Consult a statistician if needed"}
            ],
            ResearchPhase.WRITING: [
                {"type": "tip", "message": "Write every day, even if just 30 minutes"},
                {"type": "action", "message": "Start with the methods section - it's easiest"},
                {"type": "tip", "message": "Get feedback on chapters as you complete them"}
            ],
            ResearchPhase.DEFENSE: [
                {"type": "tip", "message": "Know your thesis inside out"},
                {"type": "action", "message": "Practice with mock defenses"},
                {"type": "tip", "message": "Prepare for both broad and specific questions"}
            ]
        }
        
        return suggestions.get(project.current_phase, [])


# Global singleton
_devguru_service: Optional[DevGuruService] = None


def get_devguru_service() -> DevGuruService:
    """Get or create the DevGuru service singleton"""
    global _devguru_service
    if _devguru_service is None:
        _devguru_service = DevGuruService()
    return _devguru_service
