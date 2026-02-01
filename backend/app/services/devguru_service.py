"""
DevGuru - AI PhD Mentor Service

Provides guidance for research students on:
- Research planning and experiment design
- PhD timeline and milestone management
- Literature review and methodology suggestions
- Data interpretation
- Thesis writing assistance

Phase 2: Integrates with BrAPI entities (Program, Trial, Study) for experiment tracking.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.devguru import ResearchProject, ResearchMilestone, ResearchPhase, MilestoneStatus
from app.models.core import Program, Trial, Study
from app.services.breeding_knowledge import BreedingKnowledgeBase
from app.services.ai.engine import get_llm_service

logger = logging.getLogger(__name__)


class DevGuruService:
    """DevGuru - AI PhD Mentor with database persistence"""
    
    SYSTEM_PROMPT = """You are DevGuru, an AI PhD mentor for plant breeding and agricultural research.

Your role is to:

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

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_system_prompt(self, project: Optional[ResearchProject] = None) -> str:
        """Get the DevGuru system prompt, optionally with project context"""
        prompt = self.SYSTEM_PROMPT
        
        if project:
            objectives = json.loads(project.objectives) if project.objectives else []
            prompt += f"""

---
CURRENT RESEARCH CONTEXT:

**Project:** {project.title}
**Student:** {project.student_name}
**Supervisor:** {project.supervisor or 'Not specified'}
**Research Area:** {project.research_area or 'Not specified'}
**Current Phase:** {project.current_phase.replace('_', ' ').title()}
**Timeline:** {project.start_date} to {project.expected_end_date}

**Objectives:**
{chr(10).join(f'- {obj}' for obj in objectives)}

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
                "completed": "✅",
                "in_progress": "🔄",
                "not_started": "⬜",
                "delayed": "⚠️",
                "at_risk": "🔴"
            }.get(m.status, "⬜")
            lines.append(f"{status_emoji} {m.name} (Target: {m.target_date})")
        return chr(10).join(lines) if lines else "No milestones defined"

    async def get_project(self, project_id: str) -> Optional[ResearchProject]:
        """Get a research project by ID"""
        result = await self.db.execute(
            select(ResearchProject)
            .options(selectinload(ResearchProject.milestones))
            .where(ResearchProject.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(self, user_id: Optional[int] = None) -> List[ResearchProject]:
        """List all research projects, optionally filtered by user"""
        query = select(ResearchProject).options(selectinload(ResearchProject.milestones))
        if user_id:
            query = query.where(ResearchProject.user_id == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())


    async def create_project(
        self,
        title: str,
        student_name: str,
        supervisor: str,
        start_date: date,
        expected_end_date: date,
        research_area: str,
        objectives: List[str],
        user_id: Optional[int] = None
    ) -> ResearchProject:
        """Create a new research project with default milestones"""
        import uuid
        project_id = f"phd-{uuid.uuid4().hex[:8]}"
        
        project = ResearchProject(
            id=project_id,
            user_id=user_id,
            title=title,
            student_name=student_name,
            supervisor=supervisor,
            start_date=start_date,
            expected_end_date=expected_end_date,
            current_phase=ResearchPhase.COURSEWORK.value,
            research_area=research_area,
            objectives=json.dumps(objectives)
        )
        
        self.db.add(project)
        await self.db.flush()
        
        # Generate default milestones
        milestones = self._generate_default_milestones(project)
        for m in milestones:
            self.db.add(m)
        
        await self.db.commit()
        await self.db.refresh(project)
        return project

    def _generate_default_milestones(self, project: ResearchProject) -> List[ResearchMilestone]:
        """Generate default PhD milestones based on timeline"""
        import uuid
        total_days = (project.expected_end_date - project.start_date).days
        
        milestone_templates = [
            ("Complete coursework", ResearchPhase.COURSEWORK.value, 0.15),
            ("Literature review", ResearchPhase.LITERATURE_REVIEW.value, 0.25),
            ("Research proposal defense", ResearchPhase.PROPOSAL.value, 0.30),
            ("Data collection Phase 1", ResearchPhase.DATA_COLLECTION.value, 0.45),
            ("Data collection Phase 2", ResearchPhase.DATA_COLLECTION.value, 0.60),
            ("Data analysis", ResearchPhase.ANALYSIS.value, 0.75),
            ("Thesis writing", ResearchPhase.WRITING.value, 0.90),
            ("Thesis defense", ResearchPhase.DEFENSE.value, 0.98),
        ]
        
        milestones = []
        for i, (name, phase, progress) in enumerate(milestone_templates):
            target = project.start_date + timedelta(days=int(total_days * progress))
            milestones.append(ResearchMilestone(
                id=f"m-{uuid.uuid4().hex[:8]}",
                project_id=project.id,
                name=name,
                description=f"Complete {name.lower()}",
                phase=phase,
                target_date=target,
                status=MilestoneStatus.NOT_STARTED.value
            ))
        return milestones


    async def update_milestone(
        self,
        project_id: str,
        milestone_id: str,
        status: Optional[str] = None,
        completed_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Optional[ResearchMilestone]:
        """Update a milestone"""
        result = await self.db.execute(
            select(ResearchMilestone)
            .where(ResearchMilestone.project_id == project_id)
            .where(ResearchMilestone.id == milestone_id)
        )
        milestone = result.scalar_one_or_none()
        
        if not milestone:
            return None
        
        if status:
            milestone.status = status
        if completed_date:
            milestone.completed_date = completed_date
        if notes is not None:
            milestone.notes = notes
        
        await self.db.commit()
        await self.db.refresh(milestone)
        return milestone

    async def get_timeline_analysis(self, project_id: str) -> Dict[str, Any]:
        """Analyze project timeline and identify risks"""
        project = await self.get_project(project_id)
        if not project:
            return {"error": "Project not found"}
        
        today = date.today()
        total_milestones = len(project.milestones)
        completed = sum(1 for m in project.milestones if m.status == MilestoneStatus.COMPLETED.value)
        in_progress = sum(1 for m in project.milestones if m.status == MilestoneStatus.IN_PROGRESS.value)
        
        days_remaining = (project.expected_end_date - today).days
        total_days = (project.expected_end_date - project.start_date).days
        progress_percent = ((total_days - days_remaining) / total_days) * 100 if total_days > 0 else 0
        
        at_risk = []
        for m in project.milestones:
            if m.status != MilestoneStatus.COMPLETED.value and m.target_date < today:
                at_risk.append(m.to_dict())
        
        next_milestone = None
        for m in project.milestones:
            if m.status != MilestoneStatus.COMPLETED.value:
                next_milestone = m.to_dict()
                break
        
        return {
            "project_id": project_id,
            "title": project.title,
            "current_phase": project.current_phase,
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


    def get_mentoring_suggestions(self, project: ResearchProject) -> List[Dict[str, str]]:
        """Get contextual mentoring suggestions based on current phase"""
        suggestions = {
            ResearchPhase.COURSEWORK.value: [
                {"type": "tip", "title": "Course Selection", "description": "Focus on courses that directly support your research methodology", "priority": "high"},
                {"type": "action", "title": "Start Reading", "description": "Begin reading key papers in your research area", "priority": "medium"},
                {"type": "tip", "title": "Build Relationships", "description": "Build relationships with committee members early", "priority": "medium"}
            ],
            ResearchPhase.LITERATURE_REVIEW.value: [
                {"type": "tip", "title": "Reference Management", "description": "Use reference management software (Zotero, Mendeley)", "priority": "high"},
                {"type": "action", "title": "Concept Mapping", "description": "Create a concept map of key themes and gaps", "priority": "high"},
                {"type": "tip", "title": "Balanced Reading", "description": "Read both classic papers and recent advances", "priority": "medium"}
            ],
            ResearchPhase.PROPOSAL.value: [
                {"type": "tip", "title": "Be Specific", "description": "Be specific about objectives and expected outcomes", "priority": "high"},
                {"type": "action", "title": "Practice", "description": "Practice your presentation with peers", "priority": "high"},
                {"type": "tip", "title": "Anticipate Questions", "description": "Anticipate committee questions and prepare answers", "priority": "medium"}
            ],
            ResearchPhase.DATA_COLLECTION.value: [
                {"type": "tip", "title": "Documentation", "description": "Document everything - future you will thank you", "priority": "high"},
                {"type": "action", "title": "Backup Data", "description": "Back up data regularly (3-2-1 rule)", "priority": "high"},
                {"type": "tip", "title": "Preliminary Analysis", "description": "Start preliminary analysis as you collect data", "priority": "medium"}
            ],
            ResearchPhase.ANALYSIS.value: [
                {"type": "tip", "title": "Visualize Early", "description": "Visualize data early to identify patterns and issues", "priority": "high"},
                {"type": "action", "title": "Document Pipeline", "description": "Document your analysis pipeline for reproducibility", "priority": "high"},
                {"type": "tip", "title": "Consult Expert", "description": "Consult a statistician if needed", "priority": "medium"}
            ],
            ResearchPhase.WRITING.value: [
                {"type": "tip", "title": "Write Daily", "description": "Write every day, even if just 30 minutes", "priority": "high"},
                {"type": "action", "title": "Start with Methods", "description": "Start with the methods section - it's easiest", "priority": "medium"},
                {"type": "tip", "title": "Get Feedback", "description": "Get feedback on chapters as you complete them", "priority": "high"}
            ],
            ResearchPhase.DEFENSE.value: [
                {"type": "tip", "title": "Know Your Thesis", "description": "Know your thesis inside out", "priority": "high"},
                {"type": "action", "title": "Mock Defense", "description": "Practice with mock defenses", "priority": "high"},
                {"type": "tip", "title": "Prepare for Questions", "description": "Prepare for both broad and specific questions", "priority": "medium"}
            ]
        }
        
        return suggestions.get(project.current_phase, [])

    # ============================================
    # BRAPI INTEGRATION METHODS (Phase 2)
    # ============================================

    async def link_program(self, project_id: str, program_id: int) -> Optional[ResearchProject]:
        """Link a research project to a BrAPI Program"""
        project = await self.get_project(project_id)
        if not project:
            return None
        
        # Verify program exists
        result = await self.db.execute(
            select(Program).where(Program.id == program_id)
        )
        program = result.scalar_one_or_none()
        if not program:
            return None
        
        # Update project with program link
        project.program_id = program_id
        
        # Mark program as research project
        program.is_research_project = True
        program.research_context = {
            "devguru_project_id": project_id,
            "student_name": project.student_name,
            "supervisor": project.supervisor,
            "research_area": project.research_area
        }
        
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_research_programs(self) -> List[Program]:
        """Get all programs marked as research projects"""
        result = await self.db.execute(
            select(Program)
            .where(Program.is_research_project == True)
            .options(selectinload(Program.trials))
        )
        return list(result.scalars().all())

    async def get_project_experiments(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all experiments (trials) linked to a research project"""
        project = await self.get_project(project_id)
        if not project or not project.program_id:
            return []
        
        result = await self.db.execute(
            select(Trial)
            .where(Trial.program_id == project.program_id)
            .options(selectinload(Trial.studies))
        )
        trials = result.scalars().all()
        
        return [
            {
                "id": t.id,
                "trial_db_id": t.trial_db_id,
                "trial_name": t.trial_name,
                "trial_description": t.trial_description,
                "trial_type": t.trial_type,
                "start_date": t.start_date,
                "end_date": t.end_date,
                "active": t.active,
                "studies_count": len(t.studies),
                "studies": [
                    {
                        "id": s.id,
                        "study_db_id": s.study_db_id,
                        "study_name": s.study_name,
                        "study_type": s.study_type,
                        "active": s.active
                    }
                    for s in t.studies
                ]
            }
            for t in trials
        ]

    async def get_experiment_studies(self, trial_id: int) -> List[Dict[str, Any]]:
        """Get all studies (sub-experiments) in a trial"""
        result = await self.db.execute(
            select(Study).where(Study.trial_id == trial_id)
        )
        studies = result.scalars().all()
        
        return [
            {
                "id": s.id,
                "study_db_id": s.study_db_id,
                "study_name": s.study_name,
                "study_description": s.study_description,
                "study_type": s.study_type,
                "start_date": s.start_date,
                "end_date": s.end_date,
                "active": s.active,
                "common_crop_name": s.common_crop_name
            }
            for s in studies
        ]

    async def get_synthesis_context(self, project_id: str) -> Dict[str, Any]:
        """Get all data needed for AI synthesis across experiments"""
        project = await self.get_project(project_id)
        if not project:
            return {"error": "Project not found"}
        
        experiments = await self.get_project_experiments(project_id)
        
        # Count totals
        total_studies = sum(len(e.get("studies", [])) for e in experiments)
        active_experiments = sum(1 for e in experiments if e.get("active"))
        
        return {
            "project": {
                "id": project.id,
                "title": project.title,
                "research_area": project.research_area,
                "current_phase": project.current_phase,
                "objectives": json.loads(project.objectives) if project.objectives else []
            },
            "experiments": experiments,
            "summary": {
                "total_experiments": len(experiments),
                "active_experiments": active_experiments,
                "total_studies": total_studies,
                "has_linked_program": project.program_id is not None
            }
        }

    def get_synthesis_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a synthesis prompt for the LLM based on experiment data"""
        project = context.get("project", {})
        experiments = context.get("experiments", [])
        summary = context.get("summary", {})
        
        objectives = project.get("objectives", [])
        objectives_text = "\n".join(f"- {obj}" for obj in objectives) if objectives else "Not specified"
        
        experiments_text = ""
        for exp in experiments:
            studies = exp.get("studies", [])
            studies_text = ", ".join(s.get("study_name", "Unknown") for s in studies) if studies else "No studies"
            experiments_text += f"\n- {exp.get('trial_name', 'Unknown')}: {studies_text}"
        
        return f"""Based on the following research project data, provide a synthesis of progress and insights:

**Research Project**: {project.get('title', 'Unknown')}
**Research Area**: {project.get('research_area', 'Not specified')}
**Current Phase**: {project.get('current_phase', 'Unknown')}

**Objectives**:
{objectives_text}

**Experiments** ({summary.get('total_experiments', 0)} total, {summary.get('active_experiments', 0)} active):
{experiments_text if experiments_text else 'No experiments linked yet'}

**Total Studies**: {summary.get('total_studies', 0)}

Please provide:
1. A brief summary of the research progress
2. How the experiments relate to the stated objectives
3. Any gaps or missing experiments that might be needed
4. Suggestions for next steps based on the current phase

Keep the response concise and actionable."""




    # ============================================
    # PHASE 3: LITERATURE INTEGRATION
    # ============================================

    async def list_papers(self, project_id: str) -> List[Dict[str, Any]]:
        """List all papers for a project"""
        from app.models.devguru import ResearchPaper
        result = await self.db.execute(
            select(ResearchPaper)
            .where(ResearchPaper.project_id == project_id)
            .order_by(ResearchPaper.year.desc())
        )
        papers = result.scalars().all()
        return [p.to_dict() for p in papers]

    async def add_paper(
        self,
        project_id: str,
        title: str,
        authors: List[str] = None,
        journal: str = None,
        year: int = None,
        doi: str = None,
        url: str = None,
        abstract: str = None,
        notes: str = None,
        tags: List[str] = None,
        relevance_score: int = None,
        citation_key: str = None
    ) -> Dict[str, Any]:
        """Add a paper to a project"""
        import uuid
        from app.models.devguru import ResearchPaper, ReadStatus
        
        paper = ResearchPaper(
            id=f"paper-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            title=title,
            authors=json.dumps(authors or []),
            journal=journal,
            year=year,
            doi=doi,
            url=url,
            abstract=abstract,
            notes=notes,
            tags=json.dumps(tags or []),
            relevance_score=relevance_score,
            read_status=ReadStatus.UNREAD.value,
            citation_key=citation_key
        )
        self.db.add(paper)
        await self.db.commit()
        await self.db.refresh(paper)
        return paper.to_dict()

    async def update_paper(self, paper_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a paper"""
        from app.models.devguru import ResearchPaper
        result = await self.db.execute(
            select(ResearchPaper).where(ResearchPaper.id == paper_id)
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return None
        
        for key, value in kwargs.items():
            if hasattr(paper, key) and value is not None:
                if key in ['authors', 'tags']:
                    setattr(paper, key, json.dumps(value))
                else:
                    setattr(paper, key, value)
        
        await self.db.commit()
        await self.db.refresh(paper)
        return paper.to_dict()

    async def delete_paper(self, paper_id: str) -> bool:
        """Delete a paper"""
        from app.models.devguru import ResearchPaper
        result = await self.db.execute(
            select(ResearchPaper).where(ResearchPaper.id == paper_id)
        )
        paper = result.scalar_one_or_none()
        if not paper:
            return False
        await self.db.delete(paper)
        await self.db.commit()
        return True

    async def link_paper_to_experiment(
        self,
        paper_id: str,
        trial_id: int = None,
        study_id: int = None,
        link_type: str = "supports",
        notes: str = None
    ) -> Dict[str, Any]:
        """Link a paper to an experiment (trial or study)"""
        from app.models.devguru import PaperExperimentLink
        link = PaperExperimentLink(
            paper_id=paper_id,
            trial_id=trial_id,
            study_id=study_id,
            link_type=link_type,
            notes=notes
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link.to_dict()

    async def get_literature_stats(self, project_id: str) -> Dict[str, Any]:
        """Get literature statistics for a project"""
        from app.models.devguru import ResearchPaper, ReadStatus
        from sqlalchemy import func
        
        result = await self.db.execute(
            select(ResearchPaper).where(ResearchPaper.project_id == project_id)
        )
        papers = result.scalars().all()
        
        total = len(papers)
        read = sum(1 for p in papers if p.read_status == ReadStatus.READ.value)
        reading = sum(1 for p in papers if p.read_status == ReadStatus.READING.value)
        unread = sum(1 for p in papers if p.read_status == ReadStatus.UNREAD.value)
        
        return {
            "total_papers": total,
            "read": read,
            "reading": reading,
            "unread": unread,
            "read_percentage": round((read / total) * 100, 1) if total > 0 else 0
        }

    # ============================================
    # PHASE 4: WRITING ASSISTANT
    # ============================================

    async def list_chapters(self, project_id: str) -> List[Dict[str, Any]]:
        """List all thesis chapters for a project"""
        from app.models.devguru import ThesisChapter
        result = await self.db.execute(
            select(ThesisChapter)
            .where(ThesisChapter.project_id == project_id)
            .order_by(ThesisChapter.chapter_number)
        )
        chapters = result.scalars().all()
        return [c.to_dict() for c in chapters]

    async def create_chapter(
        self,
        project_id: str,
        chapter_number: int,
        title: str,
        chapter_type: str = None,
        target_word_count: int = 5000,
        outline: List[Dict] = None,
        target_date: date = None
    ) -> Dict[str, Any]:
        """Create a thesis chapter"""
        import uuid
        from app.models.devguru import ThesisChapter, ChapterStatus
        
        chapter = ThesisChapter(
            id=f"ch-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            chapter_number=chapter_number,
            title=title,
            chapter_type=chapter_type,
            target_word_count=target_word_count,
            current_word_count=0,
            status=ChapterStatus.NOT_STARTED.value,
            outline=json.dumps(outline) if outline else None,
            target_date=target_date
        )
        self.db.add(chapter)
        await self.db.commit()
        await self.db.refresh(chapter)
        return chapter.to_dict()

    async def update_chapter(self, chapter_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a chapter"""
        from app.models.devguru import ThesisChapter
        result = await self.db.execute(
            select(ThesisChapter).where(ThesisChapter.id == chapter_id)
        )
        chapter = result.scalar_one_or_none()
        if not chapter:
            return None
        
        for key, value in kwargs.items():
            if hasattr(chapter, key) and value is not None:
                if key == 'outline':
                    setattr(chapter, key, json.dumps(value))
                else:
                    setattr(chapter, key, value)
        
        await self.db.commit()
        await self.db.refresh(chapter)
        return chapter.to_dict()

    async def log_writing_session(
        self,
        chapter_id: str,
        words_written: int,
        duration_minutes: int = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """Log a writing session and update chapter word count"""
        from app.models.devguru import ThesisChapter, WritingSession
        
        # Get chapter
        result = await self.db.execute(
            select(ThesisChapter).where(ThesisChapter.id == chapter_id)
        )
        chapter = result.scalar_one_or_none()
        if not chapter:
            return {"error": "Chapter not found"}
        
        # Create session
        session = WritingSession(
            chapter_id=chapter_id,
            session_date=date.today(),
            words_written=words_written,
            duration_minutes=duration_minutes,
            notes=notes
        )
        self.db.add(session)
        
        # Update chapter word count
        chapter.current_word_count += words_written
        
        await self.db.commit()
        await self.db.refresh(session)
        
        return {
            "session": session.to_dict(),
            "chapter_word_count": chapter.current_word_count,
            "chapter_progress": int((chapter.current_word_count / chapter.target_word_count) * 100) if chapter.target_word_count > 0 else 0
        }

    async def get_writing_stats(self, project_id: str) -> Dict[str, Any]:
        """Get writing statistics for a project"""
        from app.models.devguru import ThesisChapter, WritingSession, ChapterStatus
        
        result = await self.db.execute(
            select(ThesisChapter)
            .options(selectinload(ThesisChapter.writing_sessions))
            .where(ThesisChapter.project_id == project_id)
        )
        chapters = result.scalars().all()
        
        total_target = sum(c.target_word_count for c in chapters)
        total_written = sum(c.current_word_count for c in chapters)
        completed = sum(1 for c in chapters if c.status == ChapterStatus.COMPLETE.value)
        
        # Get recent sessions
        all_sessions = []
        for c in chapters:
            all_sessions.extend(c.writing_sessions)
        
        recent_sessions = sorted(all_sessions, key=lambda s: s.session_date, reverse=True)[:10]
        
        return {
            "total_chapters": len(chapters),
            "completed_chapters": completed,
            "total_target_words": total_target,
            "total_written_words": total_written,
            "overall_progress": round((total_written / total_target) * 100, 1) if total_target > 0 else 0,
            "recent_sessions": [s.to_dict() for s in recent_sessions]
        }

    async def generate_default_chapters(self, project_id: str) -> List[Dict[str, Any]]:
        """Generate default thesis chapters for a project"""
        from app.models.devguru import ChapterType
        
        default_chapters = [
            (1, "Introduction", ChapterType.INTRODUCTION.value, 3000),
            (2, "Literature Review", ChapterType.LITERATURE_REVIEW.value, 8000),
            (3, "Materials and Methods", ChapterType.METHODOLOGY.value, 5000),
            (4, "Results", ChapterType.RESULTS.value, 6000),
            (5, "Discussion", ChapterType.DISCUSSION.value, 5000),
            (6, "Conclusion", ChapterType.CONCLUSION.value, 2000),
        ]
        
        chapters = []
        for num, title, ch_type, target in default_chapters:
            chapter = await self.create_chapter(
                project_id=project_id,
                chapter_number=num,
                title=title,
                chapter_type=ch_type,
                target_word_count=target
            )
            chapters.append(chapter)
        
        return chapters

    # ============================================
    # PHASE 5: COLLABORATION
    # ============================================

    async def list_committee_members(self, project_id: str) -> List[Dict[str, Any]]:
        """List all committee members for a project"""
        from app.models.devguru import CommitteeMember
        result = await self.db.execute(
            select(CommitteeMember)
            .where(CommitteeMember.project_id == project_id)
            .order_by(CommitteeMember.is_primary.desc())
        )
        members = result.scalars().all()
        return [m.to_dict() for m in members]

    async def add_committee_member(
        self,
        project_id: str,
        name: str,
        email: str = None,
        role: str = "committee",
        institution: str = None,
        expertise: str = None,
        is_primary: bool = False
    ) -> Dict[str, Any]:
        """Add a committee member"""
        import uuid
        from app.models.devguru import CommitteeMember
        
        member = CommitteeMember(
            id=f"cm-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            name=name,
            email=email,
            role=role,
            institution=institution,
            expertise=expertise,
            is_primary=is_primary
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member.to_dict()

    async def update_committee_member(self, member_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a committee member"""
        from app.models.devguru import CommitteeMember
        result = await self.db.execute(
            select(CommitteeMember).where(CommitteeMember.id == member_id)
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        
        for key, value in kwargs.items():
            if hasattr(member, key) and value is not None:
                setattr(member, key, value)
        
        await self.db.commit()
        await self.db.refresh(member)
        return member.to_dict()

    async def list_meetings(self, project_id: str) -> List[Dict[str, Any]]:
        """List all meetings for a project"""
        from app.models.devguru import CommitteeMeeting
        from datetime import datetime
        result = await self.db.execute(
            select(CommitteeMeeting)
            .where(CommitteeMeeting.project_id == project_id)
            .order_by(CommitteeMeeting.scheduled_date.desc())
        )
        meetings = result.scalars().all()
        return [m.to_dict() for m in meetings]

    async def schedule_meeting(
        self,
        project_id: str,
        title: str,
        scheduled_date: str,
        meeting_type: str = "progress",
        duration_minutes: int = 60,
        location: str = None,
        agenda: str = None,
        attendees: List[str] = None
    ) -> Dict[str, Any]:
        """Schedule a committee meeting"""
        import uuid
        from datetime import datetime
        from app.models.devguru import CommitteeMeeting, MeetingStatus
        
        meeting = CommitteeMeeting(
            id=f"mtg-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            title=title,
            meeting_type=meeting_type,
            scheduled_date=datetime.fromisoformat(scheduled_date),
            duration_minutes=duration_minutes,
            location=location,
            agenda=agenda,
            status=MeetingStatus.SCHEDULED.value,
            attendees=json.dumps(attendees or [])
        )
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting.to_dict()

    async def update_meeting(self, meeting_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a meeting"""
        from app.models.devguru import CommitteeMeeting
        result = await self.db.execute(
            select(CommitteeMeeting).where(CommitteeMeeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            return None
        
        for key, value in kwargs.items():
            if hasattr(meeting, key) and value is not None:
                if key in ['action_items', 'attendees']:
                    setattr(meeting, key, json.dumps(value))
                else:
                    setattr(meeting, key, value)
        
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting.to_dict()

    async def list_feedback(self, project_id: str, status: str = None) -> List[Dict[str, Any]]:
        """List feedback items for a project"""
        from app.models.devguru import FeedbackItem
        query = select(FeedbackItem).where(FeedbackItem.project_id == project_id)
        if status:
            query = query.where(FeedbackItem.status == status)
        query = query.order_by(FeedbackItem.created_at.desc())
        
        result = await self.db.execute(query)
        items = result.scalars().all()
        return [f.to_dict() for f in items]

    async def add_feedback(
        self,
        project_id: str,
        content: str,
        feedback_type: str = "suggestion",
        priority: str = "medium",
        chapter_id: str = None,
        meeting_id: str = None,
        from_member_id: str = None
    ) -> Dict[str, Any]:
        """Add a feedback item"""
        import uuid
        from app.models.devguru import FeedbackItem, FeedbackStatus
        
        feedback = FeedbackItem(
            id=f"fb-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            chapter_id=chapter_id,
            meeting_id=meeting_id,
            from_member_id=from_member_id,
            feedback_type=feedback_type,
            priority=priority,
            content=content,
            status=FeedbackStatus.PENDING.value
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback.to_dict()

    async def update_feedback(self, feedback_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a feedback item"""
        from app.models.devguru import FeedbackItem
        result = await self.db.execute(
            select(FeedbackItem).where(FeedbackItem.id == feedback_id)
        )
        feedback = result.scalar_one_or_none()
        if not feedback:
            return None
        
        for key, value in kwargs.items():
            if hasattr(feedback, key) and value is not None:
                setattr(feedback, key, value)
        
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback.to_dict()

    async def get_collaboration_stats(self, project_id: str) -> Dict[str, Any]:
        """Get collaboration statistics for a project"""
        from app.models.devguru import CommitteeMember, CommitteeMeeting, FeedbackItem, MeetingStatus, FeedbackStatus
        
        # Committee members
        members_result = await self.db.execute(
            select(CommitteeMember).where(CommitteeMember.project_id == project_id)
        )
        members = members_result.scalars().all()
        
        # Meetings
        meetings_result = await self.db.execute(
            select(CommitteeMeeting).where(CommitteeMeeting.project_id == project_id)
        )
        meetings = meetings_result.scalars().all()
        
        # Feedback
        feedback_result = await self.db.execute(
            select(FeedbackItem).where(FeedbackItem.project_id == project_id)
        )
        feedback_items = feedback_result.scalars().all()
        
        upcoming_meetings = [m for m in meetings if m.status == MeetingStatus.SCHEDULED.value]
        pending_feedback = [f for f in feedback_items if f.status == FeedbackStatus.PENDING.value]
        
        return {
            "committee_size": len(members),
            "total_meetings": len(meetings),
            "upcoming_meetings": len(upcoming_meetings),
            "completed_meetings": sum(1 for m in meetings if m.status == MeetingStatus.COMPLETED.value),
            "total_feedback": len(feedback_items),
            "pending_feedback": len(pending_feedback),
            "addressed_feedback": sum(1 for f in feedback_items if f.status == FeedbackStatus.ADDRESSED.value)
        }

    # ============================================
    # PHASE 6: BREEDING SCIENCE KNOWLEDGE
    # ============================================

    def get_topics(self) -> List[str]:
        """Get list of available breeding science topics"""
        return BreedingKnowledgeBase.get_topics()

    async def explain_concept(self, concept: str) -> Dict[str, Any]:
        """
        Explain a breeding concept using knowledge base and LLM.

        If the concept exists in the knowledge base, it returns structured info.
        If not, or to enhance it, it uses the LLM.
        """
        # 1. Try to find in knowledge base
        kb_info = BreedingKnowledgeBase.find_topic(concept)

        # 2. Use LLM to generate explanation
        llm_service = get_llm_service()

        system_prompt = "You are an expert plant breeding mentor. Explain the requested concept clearly and scientifically."
        user_prompt = f"Explain the concept of '{concept}' in the context of plant breeding."

        if kb_info:
            user_prompt += f"\n\nHere is some reference information:\n{json.dumps(kb_info, indent=2)}\n\n" \
                           f"Please incorporate this information, especially the key methods and citations."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await llm_service.generate(messages)

        return {
            "concept": kb_info["title"] if kb_info else concept,
            "explanation": response.content,
            "structured_info": kb_info,
            "provider": response.provider.value,
            "citations": kb_info.get("citations", []) if kb_info else []
        }

    async def recommend_approach(self, scenario: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Recommend a breeding approach based on a scenario/problem.
        """
        # 1. Get project context if available
        project_context = ""
        if project_id:
            project = await self.get_project(project_id)
            if project:
                project_context = f"\n\nProject Context:\nTitle: {project.title}\nResearch Area: {project.research_area}"

        # 2. Identify potential topics from knowledge base to use as context
        kb_context = []
        scenario_lower = scenario.lower()

        # Access the raw topics dictionary to check keys, titles, and methods
        from app.services.breeding_knowledge import BreedingKnowledgeBase

        for key, info in BreedingKnowledgeBase.TOPICS.items():
            # Check key (e.g., "genomic_selection" or "genomic selection")
            if key.replace("_", " ") in scenario_lower:
                kb_context.append(info)
                continue

            # Check title (e.g., "Genomic Selection") - stripping parenthetical part if needed or just checking substrings
            title_lower = info["title"].lower()
            if title_lower in scenario_lower:
                kb_context.append(info)
                continue

            # Check if main title part (before parenthesis) matches
            if "(" in title_lower:
                main_title = title_lower.split("(")[0].strip()
                if main_title and main_title in scenario_lower:
                    kb_context.append(info)
                    continue

            # Check key methods
            for method in info.get("key_methods", []):
                if method.lower() in scenario_lower:
                    kb_context.append(info)
                    break

        # Deduplicate
        unique_context = []
        seen_titles = set()
        for item in kb_context:
            if item["title"] not in seen_titles:
                unique_context.append(item)
                seen_titles.add(item["title"])
        kb_context = unique_context

        kb_context_str = ""
        if kb_context:
            kb_context_str = "\n\nRelevant Knowledge Base Entries:\n" + json.dumps(kb_context, indent=2)

        # 3. Use LLM
        llm_service = get_llm_service()

        system_prompt = "You are an expert plant breeding mentor. Recommend the best scientific approach for the given scenario."
        user_prompt = f"Scenario: {scenario}{project_context}{kb_context_str}\n\n" \
                      f"Please provide a recommended approach, reasoning, and any relevant methods."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await llm_service.generate(messages)

        # Merge citations from relevant topics
        citations = []
        for info in kb_context:
            citations.extend(info.get("citations", []))

        return {
            "recommendation": response.content,
            "provider": response.provider.value,
            "citations": citations
        }

def get_devguru_service(db: AsyncSession) -> DevGuruService:
    """Get DevGuru service instance with database session"""
    return DevGuruService(db)
