"""Verification router for developer control plane.

Thin router — HTTP route definitions only.
Business logic lives in app.services.control_plane.verification_service.

Endpoints:
  GET /runtime/watchdog-status
  GET /runtime/autonomy-cycle
  GET /runtime/completion-assist
  GET /runtime/silent-monitors
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_organization_id
from app.middleware.tenant_context import get_tenant_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Routes
# Helpers that are still in developer_control_plane.py are imported lazily
# (inside function bodies) to avoid circular imports at module load time.
# ---------------------------------------------------------------------------

@router.get("/runtime/watchdog-status")
async def get_runtime_watchdog_status():
    from app.control_plane.orchestration.closeout_writer import CloseoutWriter

    return CloseoutWriter.watchdog_status_response(
        CloseoutWriter.load_watchdog_state_payload()
    )


@router.get("/runtime/autonomy-cycle")
async def get_runtime_autonomy_cycle(
    db: AsyncSession = Depends(get_tenant_db),
    organization_id: int = Depends(get_organization_id),
):
    from app.control_plane.orchestration.dispatch_planner import DispatchPlanner

    response = DispatchPlanner.autonomy_cycle_response(
        DispatchPlanner.load_autonomy_cycle_payload()
    )
    if response.exists is not True:
        return response

    response.next_actions, response.next_action_ordering_source = (
        await DispatchPlanner.memory_biased_autonomy_cycle_next_actions(
            db,
            organization_id,
            response.next_actions,
        )
    )
    response.next_actions = await DispatchPlanner.hydrate_autonomy_cycle_completion_write_preparations(
        db,
        organization_id,
        response.next_actions,
    )
    response.first_actionable_completion_write = DispatchPlanner.resolve_first_actionable_completion_write(
        response.next_actions
    )
    return response


@router.get("/runtime/completion-assist")
async def get_runtime_completion_assist():
    from app.control_plane.orchestration.closeout_writer import CloseoutWriter

    return CloseoutWriter.completion_assist_response(
        CloseoutWriter.load_completion_assist_payload()
    )


@router.get("/runtime/silent-monitors")
async def get_runtime_silent_monitors():
    from app.control_plane.contracts.api_schema import (
        DeveloperControlPlaneSilentMonitorsResponse,
    )
    from app.control_plane.orchestration.closeout_writer import CloseoutWriter
    from app.control_plane.orchestration.queue_materializer import QueueMaterializer

    queue_status = QueueMaterializer.overnight_queue_status_response()
    monitors = [
        CloseoutWriter.queue_staleness_monitor(queue_status),
        CloseoutWriter.control_surface_drift_monitor(),
        CloseoutWriter.reevu_readiness_monitor(),
    ]
    return DeveloperControlPlaneSilentMonitorsResponse(
        generated_at=datetime.now(UTC).isoformat(),
        overall_state=CloseoutWriter.derive_silent_monitor_overall_state(monitors),
        should_emit=any(monitor.should_emit for monitor in monitors),
        monitors=monitors,
    )
