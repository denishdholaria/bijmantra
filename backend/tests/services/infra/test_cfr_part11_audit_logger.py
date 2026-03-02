"""
Tests for CFR Part 11 Audit Logger Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, UTC
from sqlalchemy import Column, Integer
from app.core.database import Base
from app.services.infra.cfr_part11_audit_logger import CFRPart11AuditLogger
from app.models.cfr_audit import CFRLog

# Mock models to satisfy relationships without importing the entire dependency tree
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)

class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)

@pytest.mark.asyncio
async def test_log_action_creates_entry():
    # Setup
    mock_db = AsyncMock()
    mock_db.add = MagicMock() # db.add is synchronous

    # Mock previous entry query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None # No previous log (genesis)
    mock_db.execute.return_value = mock_result

    logger = CFRPart11AuditLogger(mock_db)

    # Action
    entry = await logger.log_action(
        action_type="CREATE",
        resource_type="Trial",
        resource_id="TR-001",
        user_id=1,
        changes={"field": "value"},
        reason="Initial creation"
    )

    # Verify
    assert entry.action_type == "CREATE"
    assert entry.previous_hash == "0" * 64
    assert entry.signature is not None
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_verify_chain_valid():
    # Setup
    mock_db = AsyncMock()
    logger = CFRPart11AuditLogger(mock_db)

    # Create a valid chain manually
    log1 = CFRLog(
        timestamp=datetime(2023, 1, 1, 10, 0, 0, tzinfo=UTC),
        previous_hash="0"*64,
        user_id=1,
        action_type="CREATE",
        resource_type="Trial",
        resource_id="TR-001",
        changes={"a": 1},
        reason="Start"
    )
    log1.signature = logger._calculate_hash(log1)

    log2 = CFRLog(
        timestamp=datetime(2023, 1, 1, 11, 0, 0, tzinfo=UTC),
        previous_hash=log1.signature,
        user_id=1,
        action_type="UPDATE",
        resource_type="Trial",
        resource_id="TR-001",
        changes={"a": 2},
        reason="Update"
    )
    log2.signature = logger._calculate_hash(log2)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [log1, log2]
    mock_db.execute.return_value = mock_result

    # Verify
    assert await logger.verify_chain() is True

@pytest.mark.asyncio
async def test_verify_chain_tampered_content():
    # Setup
    mock_db = AsyncMock()
    logger = CFRPart11AuditLogger(mock_db)

    # Create a chain where log1 is tampered
    log1 = CFRLog(
        timestamp=datetime(2023, 1, 1, 10, 0, 0, tzinfo=UTC),
        previous_hash="0"*64,
        user_id=1,
        action_type="CREATE",
        resource_type="Trial",
        resource_id="TR-001",
        changes={"a": 1}, # Original content
        reason="Start"
    )
    # Calculate valid signature for original content
    log1.signature = logger._calculate_hash(log1)

    # Tamper with content AFTER signing
    log1.changes = {"a": 999}

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [log1]
    mock_db.execute.return_value = mock_result

    # Verify
    assert await logger.verify_chain() is False

@pytest.mark.asyncio
async def test_verify_chain_broken_link():
    # Setup
    mock_db = AsyncMock()
    logger = CFRPart11AuditLogger(mock_db)

    log1 = CFRLog(
        timestamp=datetime(2023, 1, 1, 10, 0, 0, tzinfo=UTC),
        previous_hash="0"*64,
        user_id=1,
        action_type="CREATE",
        resource_type="Trial",
        resource_id="TR-001"
    )
    log1.signature = logger._calculate_hash(log1)

    log2 = CFRLog(
        timestamp=datetime(2023, 1, 1, 11, 0, 0, tzinfo=UTC),
        previous_hash="WRONG_HASH", # Broken link
        user_id=1,
        action_type="UPDATE",
        resource_type="Trial",
        resource_id="TR-001"
    )
    log2.signature = logger._calculate_hash(log2)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [log1, log2]
    mock_db.execute.return_value = mock_result

    # Verify
    assert await logger.verify_chain() is False
