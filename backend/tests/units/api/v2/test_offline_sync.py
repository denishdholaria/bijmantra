
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from app.api.v2.offline_sync import resolve_conflict, get_model_class, deep_merge
from app.models.collaboration import SyncItem, SyncStatus, SyncEntityType
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_deep_merge():
    target = {"a": 1, "b": {"c": 2}}
    source = {"b": {"d": 3}, "e": 4}
    result = deep_merge(target, source)
    assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

@pytest.mark.asyncio
async def test_get_model_class():
    from app.models.phenotyping import Observation
    assert get_model_class("observation") == Observation
    assert get_model_class("Observation") == Observation
    assert get_model_class("invalid") is None

@pytest.mark.asyncio
async def test_resolve_conflict_server_wins():
    # Setup mocks
    db = AsyncMock()
    current_user = MagicMock()
    current_user.id = 1
    
    # Mock SyncItem
    sync_item = SyncItem(
        id=1,
        user_id=1,
        entity_type="observation",
        entity_id="100",
        local_data={"value": "client"},
        status=SyncStatus.CONFLICT
    )
    
    # Mock query execution
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = sync_item
    db.execute.return_value = result_mock
    
    # Execute
    response = await resolve_conflict(1, "server_wins", db, current_user)
    
    # Verify
    assert response["success"] is True
    assert sync_item.status == SyncStatus.SYNCED
    assert "Server wins" in sync_item.error_message
    db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_resolve_conflict_client_wins_existing_record():
    # Setup mocks
    db = AsyncMock()
    current_user = MagicMock()
    current_user.id = 1
    
    # Mock SyncItem
    sync_item = SyncItem(
        id=1,
        user_id=1,
        entity_type="observation",
        entity_id="100",
        local_data={"obs_value": "client_val"},
        status=SyncStatus.CONFLICT
    )
    
    # Mock DB Record
    record = MagicMock()
    record.obs_value = "server_val"
    db.get.return_value = record
    
    # Mock query execution for SyncItem
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = sync_item
    db.execute.return_value = result_mock
    
    # Execute
    response = await resolve_conflict(1, "client_wins", db, current_user)
    
    # Verify
    assert response["success"] is True
    assert record.obs_value == "client_val" # Should be updated
    assert sync_item.status == SyncStatus.SYNCED
    db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_resolve_conflict_invalid_resolution():
    db = AsyncMock()
    current_user = MagicMock()
    current_user.id = 1
    
    sync_item = SyncItem(id=1, user_id=1, entity_type="observation")
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = sync_item
    db.execute.return_value = result_mock
    
    with pytest.raises(HTTPException) as exc:
        await resolve_conflict(1, "rock_paper_scissors", db, current_user)
    assert exc.value.status_code == 400
