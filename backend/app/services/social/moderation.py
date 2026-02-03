"""
Social Moderation Service
Reporting, Profanity Filter, Reputation
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.models.social import Report, Reputation, ReportStatus, TargetType
from app.schemas.social import ReportCreate

# Simple bad words list (would use a library or external service in production)
BAD_WORDS = {"badword", "spam", "fake"}

class ModerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def check_profanity(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        return any(word in text_lower for word in BAD_WORDS)

    async def create_report(self, user_id: int, report_in: ReportCreate) -> Report:
        report = Report(
            reporter_id=user_id,
            target_id=report_in.target_id,
            target_type=report_in.target_type,
            reason=report_in.reason,
            description=report_in.description
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_reports(self, status: Optional[ReportStatus] = None, skip: int = 0, limit: int = 20) -> List[Report]:
        stmt = select(Report)
        if status:
            stmt = stmt.where(Report.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def resolve_report(self, report_id: int, resolved_by_id: int, resolution_note: str, status: ReportStatus = ReportStatus.RESOLVED) -> Optional[Report]:
        stmt = select(Report).where(Report.id == report_id)
        result = await self.db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            return None

        report.status = status
        report.resolved_by_id = resolved_by_id
        report.resolution_note = resolution_note

        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def update_reputation(self, user_id: int, action: str) -> Reputation:
        # Check if reputation record exists
        stmt = select(Reputation).where(Reputation.user_id == user_id)
        result = await self.db.execute(stmt)
        rep = result.scalar_one_or_none()

        if not rep:
            rep = Reputation(user_id=user_id)
            self.db.add(rep)

        # Points logic
        points = 0
        if action == "post_created":
            points = 5
            rep.posts_count += 1
        elif action == "helpful_vote":
            points = 10
            rep.helpful_votes += 1
        elif action == "report_accepted":
            points = 20
        elif action == "spam_penalty":
            points = -50

        rep.score += points

        # Level logic
        if rep.score < 100:
            rep.level = "Newcomer"
        elif rep.score < 500:
            rep.level = "Contributor"
        elif rep.score < 1000:
            rep.level = "Expert"
        else:
            rep.level = "Guru"

        await self.db.commit()
        await self.db.refresh(rep)
        return rep

    async def get_reputation(self, user_id: int) -> Reputation:
        stmt = select(Reputation).where(Reputation.user_id == user_id)
        result = await self.db.execute(stmt)
        rep = result.scalar_one_or_none()
        if not rep:
            return Reputation(user_id=user_id, score=0, level="Newcomer")
        return rep
