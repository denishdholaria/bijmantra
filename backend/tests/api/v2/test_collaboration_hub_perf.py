import pytest
import time
import asyncio
from sqlalchemy import select
from httpx import AsyncClient
from app.models.collaboration import CollaborationWorkspace, WorkspaceMember, WorkspaceType, MemberRole
from app.models.core import User
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_list_workspaces_performance(
    authenticated_client: AsyncClient,
    test_user: User,
    async_db_session: AsyncSession
):
    # 1. Setup Data
    NUM_WORKSPACES = 2000
    NUM_MEMBER_WORKSPACES = 1000

    # Create workspaces
    workspaces = []
    for i in range(NUM_WORKSPACES):
        ws = CollaborationWorkspace(
            organization_id=test_user.organization_id,
            name=f"Perf Workspace {i}",
            type=WorkspaceType.TRIAL,
            owner_id=test_user.id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        async_db_session.add(ws)
        workspaces.append(ws)

    await async_db_session.flush()

    # Add user to a subset of workspaces
    for i in range(NUM_MEMBER_WORKSPACES):
        member = WorkspaceMember(
            workspace_id=workspaces[i].id,
            user_id=test_user.id,
            role=MemberRole.EDITOR
        )
        async_db_session.add(member)

    await async_db_session.commit()

    # 2. Benchmark
    start_time = time.time()
    response = await authenticated_client.get(f"/api/v2/collaboration-hub/workspaces?member_id={test_user.id}")
    end_time = time.time()

    duration = end_time - start_time
    print(f"\nTime taken to list workspaces: {duration:.4f} seconds")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == NUM_MEMBER_WORKSPACES
