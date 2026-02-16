"""
Workflow Automation API

Provides endpoints for managing automated workflows and tasks.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
from app.api.deps import get_current_user

router = APIRouter(prefix="/workflows", tags=["workflows"], dependencies=[Depends(get_current_user)])

# ============ SCHEMAS ============

class WorkflowStep(BaseModel):
    id: str
    type: Literal["trigger", "action", "condition"]
    name: str
    config: dict

class WorkflowCreate(BaseModel):
    name: str
    description: str
    trigger: str
    steps: List[WorkflowStep]
    enabled: bool = True

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    enabled: Optional[bool] = None

class WorkflowRun(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    status: Literal["success", "error", "running"]
    started_at: str
    completed_at: Optional[str]
    duration: str
    error: Optional[str] = None

# ============ DEMO DATA ============

_workflows = [
    {
        "id": "1",
        "name": "Daily Data Backup",
        "description": "Automated backup of all breeding data",
        "trigger": "Schedule: Daily 2:00 AM",
        "status": "active",
        "last_run": "2 hours ago",
        "next_run": "Tomorrow 2:00 AM",
        "runs": 365,
        "success_rate": 99.7,
        "enabled": True,
        "steps": [
            {"id": "1", "type": "trigger", "name": "Schedule Trigger", "config": {"schedule": "0 2 * * *"}},
            {"id": "2", "type": "action", "name": "Backup Database", "config": {"target": "all"}},
            {"id": "3", "type": "action", "name": "Upload to Cloud", "config": {"provider": "s3"}}
        ]
    },
    {
        "id": "2",
        "name": "Trial Completion Alert",
        "description": "Notify team when trial reaches completion",
        "trigger": "Event: Trial status change",
        "status": "active",
        "last_run": "1 day ago",
        "next_run": "On trigger",
        "runs": 47,
        "success_rate": 100.0,
        "enabled": True,
        "steps": [
            {"id": "1", "type": "trigger", "name": "Trial Status Change", "config": {"event": "trial.completed"}},
            {"id": "2", "type": "condition", "name": "Check Completion", "config": {"field": "status", "value": "completed"}},
            {"id": "3", "type": "action", "name": "Send Email", "config": {"to": "team@example.com"}}
        ]
    },
    {
        "id": "3",
        "name": "Weekly Report Generation",
        "description": "Generate and email weekly progress reports",
        "trigger": "Schedule: Every Monday 8:00 AM",
        "status": "active",
        "last_run": "5 days ago",
        "next_run": "Monday 8:00 AM",
        "runs": 52,
        "success_rate": 98.1,
        "enabled": True,
        "steps": []
    },
    {
        "id": "4",
        "name": "Low Seed Inventory Alert",
        "description": "Alert when seed lot falls below threshold",
        "trigger": "Event: Inventory change",
        "status": "active",
        "last_run": "3 hours ago",
        "next_run": "On trigger",
        "runs": 23,
        "success_rate": 100.0,
        "enabled": True,
        "steps": []
    },
    {
        "id": "5",
        "name": "Cross Verification",
        "description": "Verify crosses and update pedigree records",
        "trigger": "Event: New cross recorded",
        "status": "paused",
        "last_run": "2 weeks ago",
        "next_run": "Paused",
        "runs": 156,
        "success_rate": 95.5,
        "enabled": False,
        "steps": []
    },
    {
        "id": "6",
        "name": "Weather Alert Integration",
        "description": "Send alerts for adverse weather conditions",
        "trigger": "Event: Weather API update",
        "status": "error",
        "last_run": "1 hour ago",
        "next_run": "Retry in 30 min",
        "runs": 89,
        "success_rate": 87.6,
        "enabled": True,
        "steps": []
    }
]

_workflow_runs = [
    {"id": "1", "workflow_id": "1", "workflow_name": "Daily Data Backup", "status": "success", "started_at": "2 hours ago", "completed_at": "2 hours ago", "duration": "3m 24s", "error": None},
    {"id": "2", "workflow_id": "4", "workflow_name": "Low Seed Inventory Alert", "status": "success", "started_at": "3 hours ago", "completed_at": "3 hours ago", "duration": "0.5s", "error": None},
    {"id": "3", "workflow_id": "6", "workflow_name": "Weather Alert Integration", "status": "error", "started_at": "1 hour ago", "completed_at": "1 hour ago", "duration": "12s", "error": "API timeout"},
    {"id": "4", "workflow_id": "2", "workflow_name": "Trial Completion Alert", "status": "success", "started_at": "1 day ago", "completed_at": "1 day ago", "duration": "1.2s", "error": None}
]

_workflow_templates = [
    {"id": "1", "name": "Data Backup", "description": "Scheduled database backups", "category": "maintenance"},
    {"id": "2", "name": "Email Notifications", "description": "Send automated emails", "category": "notifications"},
    {"id": "3", "name": "Report Generation", "description": "Create periodic reports", "category": "reports"},
    {"id": "4", "name": "Data Sync", "description": "Sync data between systems", "category": "integration"},
    {"id": "5", "name": "Alert System", "description": "Threshold-based alerts", "category": "monitoring"},
    {"id": "6", "name": "Pipeline Automation", "description": "Breeding pipeline tasks", "category": "breeding"}
]

# ============ ENDPOINTS ============

@router.get("")
async def list_workflows(
    status: Optional[str] = None,
    enabled: Optional[bool] = None
):
    """List all workflows with optional filters"""
    workflows = _workflows.copy()

    if status:
        workflows = [w for w in workflows if w["status"] == status]
    if enabled is not None:
        workflows = [w for w in workflows if w["enabled"] == enabled]

    return {
        "status": "success",
        "data": workflows,
        "total": len(workflows)
    }

@router.get("/stats")
async def get_workflow_stats():
    """Get workflow statistics"""
    active_count = len([w for w in _workflows if w["status"] == "active"])
    total_runs = sum(w["runs"] for w in _workflows)
    avg_success_rate = sum(w["success_rate"] for w in _workflows) / len(_workflows) if _workflows else 0

    return {
        "status": "success",
        "data": {
            "total_workflows": len(_workflows),
            "active_workflows": active_count,
            "paused_workflows": len([w for w in _workflows if w["status"] == "paused"]),
            "error_workflows": len([w for w in _workflows if w["status"] == "error"]),
            "total_runs": total_runs,
            "average_success_rate": round(avg_success_rate, 1),
            "time_saved_hours": 142
        }
    }

@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow"""
    workflow = next((w for w in _workflows if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "status": "success",
        "data": workflow
    }

@router.post("")
async def create_workflow(workflow: WorkflowCreate):
    """Create a new workflow"""
    new_workflow = {
        "id": str(len(_workflows) + 1),
        "name": workflow.name,
        "description": workflow.description,
        "trigger": workflow.trigger,
        "status": "active" if workflow.enabled else "paused",
        "last_run": "Never",
        "next_run": "Pending",
        "runs": 0,
        "success_rate": 0.0,
        "enabled": workflow.enabled,
        "steps": [step.dict() for step in workflow.steps]
    }
    _workflows.append(new_workflow)

    return {
        "status": "success",
        "data": new_workflow,
        "message": "Workflow created successfully"
    }

@router.patch("/{workflow_id}")
async def update_workflow(workflow_id: str, workflow: WorkflowUpdate):
    """Update a workflow"""
    existing = next((w for w in _workflows if w["id"] == workflow_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.name is not None:
        existing["name"] = workflow.name
    if workflow.description is not None:
        existing["description"] = workflow.description
    if workflow.trigger is not None:
        existing["trigger"] = workflow.trigger
    if workflow.enabled is not None:
        existing["enabled"] = workflow.enabled
        existing["status"] = "active" if workflow.enabled else "paused"
    if workflow.steps is not None:
        existing["steps"] = [step.dict() for step in workflow.steps]

    return {
        "status": "success",
        "data": existing,
        "message": "Workflow updated successfully"
    }

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    global _workflows
    workflow = next((w for w in _workflows if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    _workflows = [w for w in _workflows if w["id"] != workflow_id]

    return {
        "status": "success",
        "message": "Workflow deleted successfully"
    }

@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    """Manually trigger a workflow run"""
    workflow = next((w for w in _workflows if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow["enabled"]:
        raise HTTPException(status_code=400, detail="Cannot run disabled workflow")

    # Create a new run
    new_run = {
        "id": str(len(_workflow_runs) + 1),
        "workflow_id": workflow_id,
        "workflow_name": workflow["name"],
        "status": "running",
        "started_at": "Just now",
        "completed_at": None,
        "duration": "0s",
        "error": None
    }
    _workflow_runs.insert(0, new_run)

    # Update workflow stats
    workflow["runs"] += 1
    workflow["last_run"] = "Just now"

    return {
        "status": "success",
        "data": new_run,
        "message": "Workflow run started"
    }

@router.post("/{workflow_id}/toggle")
async def toggle_workflow(workflow_id: str):
    """Toggle workflow enabled/disabled status"""
    workflow = next((w for w in _workflows if w["id"] == workflow_id), None)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow["enabled"] = not workflow["enabled"]
    workflow["status"] = "active" if workflow["enabled"] else "paused"

    return {
        "status": "success",
        "data": workflow,
        "message": f"Workflow {'enabled' if workflow['enabled'] else 'disabled'}"
    }

@router.get("/runs/history")
async def get_workflow_runs(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get workflow run history"""
    runs = _workflow_runs.copy()

    if workflow_id:
        runs = [r for r in runs if r["workflow_id"] == workflow_id]
    if status:
        runs = [r for r in runs if r["status"] == status]

    return {
        "status": "success",
        "data": runs[:limit],
        "total": len(runs)
    }

@router.get("/templates/list")
async def list_workflow_templates():
    """List available workflow templates"""
    return {
        "status": "success",
        "data": _workflow_templates
    }

@router.post("/templates/{template_id}/use")
async def use_workflow_template(template_id: str, name: str):
    """Create a workflow from a template"""
    template = next((t for t in _workflow_templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_workflow = {
        "id": str(len(_workflows) + 1),
        "name": name,
        "description": template["description"],
        "trigger": "Manual",
        "status": "paused",
        "last_run": "Never",
        "next_run": "Not scheduled",
        "runs": 0,
        "success_rate": 0.0,
        "enabled": False,
        "steps": []
    }
    _workflows.append(new_workflow)

    return {
        "status": "success",
        "data": new_workflow,
        "message": "Workflow created from template"
    }
