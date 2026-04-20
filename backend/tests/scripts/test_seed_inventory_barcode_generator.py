import pytest
import csv
import os
from sqlalchemy import select
from app.models.germplasm import Seedlot
from app.scripts.seed_inventory_barcode_generator import generate_barcodes

@pytest.mark.asyncio
async def test_generate_barcodes_db_update(async_db_session):
    # Create seedlot
    seedlot = Seedlot(
        organization_id=1,
        seedlot_db_id="TEST-LOT-001",
        seedlot_name="Test Variety",
        additional_info={"species": "Wheat"}
    )
    async_db_session.add(seedlot)
    await async_db_session.commit()
    await async_db_session.refresh(seedlot)

    # Generate barcodes
    await generate_barcodes(async_db_session, org_id=1)

    # Verify
    await async_db_session.refresh(seedlot)
    assert seedlot.additional_info is not None
    assert "barcode" in seedlot.additional_info
    barcode = seedlot.additional_info["barcode"]
    assert barcode.startswith("SL-")

    # Verify idempotent (doesn't change on second run)
    await generate_barcodes(async_db_session, org_id=1)
    await async_db_session.refresh(seedlot)
    assert seedlot.additional_info["barcode"] == barcode

    # Verify force update
    import asyncio
    await asyncio.sleep(1.1)  # Ensure timestamp changes for barcode generation
    await generate_barcodes(async_db_session, org_id=1, force=True)
    await async_db_session.refresh(seedlot)
    new_barcode = seedlot.additional_info["barcode"]
    assert new_barcode != barcode
    assert new_barcode.startswith("SL-")

@pytest.mark.asyncio
async def test_generate_barcodes_csv_export(async_db_session, tmp_path):
    # Create seedlot
    seedlot = Seedlot(
        organization_id=1,
        seedlot_db_id="TEST-LOT-002",
        seedlot_name="Test Rice",
        additional_info={"species": "Rice"}
    )
    async_db_session.add(seedlot)
    await async_db_session.commit()

    csv_file = tmp_path / "barcodes.csv"

    # Generate and export
    await generate_barcodes(async_db_session, org_id=1, export_path=str(csv_file))

    # Verify CSV
    assert csv_file.exists()
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        # Check that our row is present
        found = False
        for row in rows:
            if row['lot_id'] == "TEST-LOT-002":
                assert row['species'] == "Rice"
                assert row['barcode'].startswith("SL-")
                found = True
        assert found
