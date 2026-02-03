import pytest
from app.services.barcode_service import barcode_service
from app.models.barcode import BarcodeScan
from sqlalchemy import select, func, delete

@pytest.fixture(autouse=True)
async def cleanup_barcode_scans(async_db_session):
    """Clean up barcode scans before/after each test"""
    # Before
    await async_db_session.execute(delete(BarcodeScan))
    await async_db_session.commit()
    yield
    # After
    await async_db_session.execute(delete(BarcodeScan))
    await async_db_session.commit()

@pytest.mark.asyncio
async def test_scan_barcode_stores_record(async_db_session, test_user):
    # We need an organization_id. test_user has one.
    org_id = test_user.organization_id
    barcode_val = "TEST-BARCODE-123"

    # Perform scan
    result = await barcode_service.scan_barcode(
        db=async_db_session,
        organization_id=org_id,
        barcode_value=barcode_val,
        scanned_by="test_user",
        location="Lab A"
    )

    assert result["scan"]["barcode_value"] == barcode_val
    assert result["scan"]["found"] is False  # Should be false as we didn't create the entity

    # Verify DB record
    stmt = select(BarcodeScan).where(BarcodeScan.barcode_value == barcode_val)
    scan_record = (await async_db_session.execute(stmt)).scalar_one_or_none()

    assert scan_record is not None
    assert scan_record.organization_id == org_id
    assert scan_record.scanned_by == "test_user"
    assert scan_record.location == "Lab A"
    assert scan_record.found is False

@pytest.mark.asyncio
async def test_get_statistics_counts_scans(async_db_session, test_user):
    org_id = test_user.organization_id

    # Create some scan records
    # 1. Failed scan
    await barcode_service.scan_barcode(
        db=async_db_session,
        organization_id=org_id,
        barcode_value="FAIL-1",
    )

    # 2. Manual successful scan
    scan_success = BarcodeScan(
        organization_id=org_id,
        barcode_value="SUCCESS-1",
        found=True,
        scanned_by="system"
    )
    async_db_session.add(scan_success)
    await async_db_session.commit()

    stats = await barcode_service.get_statistics(async_db_session, org_id)

    assert stats["total_scans"] == 2
    assert stats["successful_scans"] == 1
    assert stats["scan_success_rate"] == 50.0
