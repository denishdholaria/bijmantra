"""
AI Quota Service
Enforces daily usage limits for organization-managed AI keys.
"""

from datetime import date
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_quota import AIUsageDaily
from app.models.core import Organization


# Default limit if not set in DB
DEFAULT_DAILY_LIMIT = 50


class AIQuotaService:
    """
    Manages AI usage quotas and enforcement.
    """

    @staticmethod
    async def _get_organization(db: AsyncSession, organization_id: int) -> Organization | None:
        stmt_org = select(Organization).where(Organization.id == organization_id)
        result_org = await db.execute(stmt_org)
        return result_org.scalar_one_or_none()

    @staticmethod
    async def _get_usage_record(
        db: AsyncSession,
        organization_id: int,
        usage_day: date,
    ) -> AIUsageDaily | None:
        stmt_usage = select(AIUsageDaily).where(
            AIUsageDaily.organization_id == organization_id,
            AIUsageDaily.usage_date == usage_day,
        )
        result_usage = await db.execute(stmt_usage)
        return result_usage.scalar_one_or_none()

    @staticmethod
    def _build_provider_snapshot(provider_status: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(provider_status, dict):
            return {
                "active_provider": None,
                "active_model": None,
                "active_provider_source": None,
                "active_provider_source_label": None,
            }

        return {
            "active_provider": provider_status.get("active_provider")
            if isinstance(provider_status.get("active_provider"), str)
            else None,
            "active_model": provider_status.get("active_model")
            if isinstance(provider_status.get("active_model"), str)
            else None,
            "active_provider_source": provider_status.get("active_provider_source")
            if isinstance(provider_status.get("active_provider_source"), str)
            else None,
            "active_provider_source_label": provider_status.get("active_provider_source_label")
            if isinstance(provider_status.get("active_provider_source_label"), str)
            else None,
        }

    @staticmethod
    def _build_token_telemetry(
        request_count: int,
        input_tokens: int,
        output_tokens: int,
    ) -> dict[str, Any]:
        total_tokens = input_tokens + output_tokens
        if request_count == 0:
            coverage_message = "No managed REEVU requests recorded today yet."
        elif total_tokens == 0:
            coverage_message = (
                "Token telemetry has not been observed yet. Streaming and some provider "
                "paths remain uninstrumented in this slice."
            )
        else:
            coverage_message = (
                "Token telemetry is supplemental only. Request-count quota remains the "
                "enforcement authority for this slice."
            )

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "coverage_state": "supplemental" if total_tokens > 0 else "unavailable",
            "coverage_message": coverage_message,
        }

    @staticmethod
    def _build_soft_alert(request_count: int, daily_limit: int) -> dict[str, Any]:
        if daily_limit <= 0:
            percent_used = 0.0
        else:
            percent_used = round((request_count / daily_limit) * 100, 1)

        if daily_limit > 0 and request_count >= daily_limit:
            return {
                "state": "exhausted",
                "threshold_basis": "request_count",
                "percent_used": 100.0,
                "message": "Daily managed REEVU request quota is exhausted. Use BYOK or wait for reset.",
            }

        if percent_used >= 95:
            state = "critical"
            message = "Daily managed REEVU request quota is near exhaustion. Limit nonessential traffic now."
        elif percent_used >= 85:
            state = "warning"
            message = "Daily managed REEVU request quota is under sustained pressure. Review traffic before the hard stop."
        elif percent_used >= 70:
            state = "watch"
            message = "Quota pressure is rising. Plan managed usage carefully."
        else:
            state = "healthy"
            message = "Managed REEVU usage is within the normal request range."

        return {
            "state": state,
            "threshold_basis": "request_count",
            "percent_used": percent_used,
            "message": message,
        }

    @staticmethod
    async def check_and_increment_usage(
        db: AsyncSession,
        organization_id: int,
        tokens_input: int = 0,
        tokens_output: int = 0,
        increment: bool = True,
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
        org = await AIQuotaService._get_organization(db, organization_id)

        if not org:
            # Should likely never happen in valid flow
            return True

        daily_limit = getattr(org, "ai_daily_limit", DEFAULT_DAILY_LIMIT)

        # 2. Get Usage Record
        usage_record = await AIQuotaService._get_usage_record(db, organization_id, today)

        current_count = usage_record.request_count if usage_record else 0

        # check limit
        if current_count >= daily_limit:
            if increment:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Daily AI quota exceeded ({daily_limit} requests/day). Upgrade plan or use BYOK.",
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
                    token_count_output=tokens_output,
                )
                db.add(new_record)

            await db.commit()

        return True

    @staticmethod
    async def record_generation_usage(
        db: AsyncSession,
        organization_id: int,
        *,
        tokens_input: int | None = None,
        tokens_output: int | None = None,
    ) -> None:
        """Record supplemental post-response token telemetry for managed requests.

        This intentionally does not participate in quota enforcement. Request-count limits
        remain authoritative and are recorded before model execution.
        """
        normalized_input = max(int(tokens_input or 0), 0)
        normalized_output = max(int(tokens_output or 0), 0)

        if normalized_input == 0 and normalized_output == 0:
            return

        today = date.today()
        usage_record = await AIQuotaService._get_usage_record(db, organization_id, today)

        if usage_record:
            usage_record.token_count_input = (usage_record.token_count_input or 0) + normalized_input
            usage_record.token_count_output = (usage_record.token_count_output or 0) + normalized_output
            db.add(usage_record)
        else:
            db.add(
                AIUsageDaily(
                    organization_id=organization_id,
                    usage_date=today,
                    # Backfill a request when quota increment failed open earlier in the call path.
                    request_count=1,
                    token_count_input=normalized_input,
                    token_count_output=normalized_output,
                )
            )

        await db.commit()

    @staticmethod
    async def get_usage_stats(
        db: AsyncSession,
        organization_id: int,
        *,
        provider_status: dict[str, Any] | None = None,
    ):
        """Get richer daily usage stats for today."""
        today = date.today()
        record = await AIQuotaService._get_usage_record(db, organization_id, today)
        org = await AIQuotaService._get_organization(db, organization_id)
        limit = getattr(org, "ai_daily_limit", DEFAULT_DAILY_LIMIT)
        used = record.request_count if record else 0
        remaining = max(0, limit - used)
        request_percentage_used = round((used / limit) * 100, 1) if limit > 0 else 0.0
        input_tokens = max(record.token_count_input or 0, 0) if record else 0
        output_tokens = max(record.token_count_output or 0, 0) if record else 0

        return {
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "request_percentage_used": request_percentage_used,
            "quota_authority": "request_count",
            "provider": AIQuotaService._build_provider_snapshot(provider_status),
            "token_telemetry": AIQuotaService._build_token_telemetry(
                used,
                input_tokens,
                output_tokens,
            ),
            "attribution": {
                "lane": {
                    "supported": False,
                    "value": None,
                    "reason": "Lane attribution is not linked from the canonical REEVU chat request path yet.",
                },
                "mission": {
                    "supported": False,
                    "value": None,
                    "reason": "Mission attribution is not linked from the canonical REEVU chat request path yet.",
                },
            },
            "soft_alert": AIQuotaService._build_soft_alert(used, limit),
        }
