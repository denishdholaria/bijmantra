"""
AI Quota Service
Enforces daily usage limits for organization-managed AI keys.
"""

from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.ai_quota import AIUsageDaily
from app.models.core import Organization

# Default limit if not set in DB
DEFAULT_DAILY_LIMIT = 50

class AIQuotaService:
    """
    Manages AI usage quotas and enforcement.
    """
    
    @staticmethod
    async def check_and_increment_usage(
        db: AsyncSession, 
        organization_id: int,
        tokens_input: int = 0,
        tokens_output: int = 0,
        increment: bool = True
    ) -> bool:
        """
        Check if organization has reached daily limit.
        If increment=True, also increments usage counter.
        
        Returns:
            True if usage allowed (under limit)
            False if usage blocked (over limit)
        
        Raises:
            HTTPException(429) if over limit and increment=True
        """
        today = date.today()
        
        # 1. Get Organization Limit
        stmt_org = select(Organization).where(Organization.id == organization_id)
        result_org = await db.execute(stmt_org)
        org = result_org.scalar_one_or_none()
        
        if not org:
            # Should likely never happen in valid flow
            return True 
            
        daily_limit = getattr(org, 'ai_daily_limit', DEFAULT_DAILY_LIMIT)
        
        # 2. Get Usage Record
        stmt_usage = select(AIUsageDaily).where(
            AIUsageDaily.organization_id == organization_id,
            AIUsageDaily.usage_date == today
        )
        result_usage = await db.execute(stmt_usage)
        usage_record = result_usage.scalar_one_or_none()
        
        current_count = usage_record.request_count if usage_record else 0
        
        # check limit
        if current_count >= daily_limit:
            if increment:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily AI quota exceeded ({daily_limit} requests/day). Upgrade plan or use BYOK."
                )
            return False
            
        # 3. Increment Usage
        if increment:
            if usage_record:
                usage_record.request_count += 1
                usage_record.token_count_input += tokens_input
                usage_record.token_count_output += tokens_output
                # dirty tracking by ORM usually enough, but let's be explicit if needed
                db.add(usage_record)
            else:
                new_record = AIUsageDaily(
                    organization_id=organization_id,
                    usage_date=today,
                    request_count=1,
                    token_count_input=tokens_input,
                    token_count_output=tokens_output
                )
                db.add(new_record)
                
            await db.commit()
            
        return True

    @staticmethod
    async def get_usage_stats(db: AsyncSession, organization_id: int):
        """Get usage stats for today"""
        today = date.today()
        stmt = select(AIUsageDaily).where(
            AIUsageDaily.organization_id == organization_id,
            AIUsageDaily.usage_date == today
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        
        stmt_org = select(Organization).where(Organization.id == organization_id)
        result_org = await db.execute(stmt_org)
        org = result_org.scalar_one_or_none()
        limit = getattr(org, 'ai_daily_limit', DEFAULT_DAILY_LIMIT)
        
        return {
            "used": record.request_count if record else 0,
            "limit": limit,
            "remaining": max(0, limit - (record.request_count if record else 0))
        }
