"""
Seed Inventory Barcode Generator
Generates and assigns barcodes to seed lots, and optionally exports a PDF of labels.
"""

import argparse
import asyncio
import csv
import logging
import os
import sys
from typing import Optional

# Add parent directory to path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.germplasm import Seedlot
from app.services.barcode_service import barcode_service, EntityType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @page { size: A4; margin: 10mm; }
        body { font-family: sans-serif; }
        .label {
            display: inline-block;
            width: 60mm;
            height: 40mm;
            border: 1px solid #ccc;
            margin: 2mm;
            padding: 2mm;
            box-sizing: border-box;
            page-break-inside: avoid;
            float: left;
        }
        .label h3 { margin: 0; font-size: 10pt; }
        .label p { margin: 2px 0; font-size: 8pt; }
        .barcode { text-align: center; margin-top: 5mm; }
    </style>
</head>
<body>
    {% for item in items %}
    <div class="label">
        <h3>{{ item.lot_id }}</h3>
        <p><strong>Species:</strong> {{ item.species }}</p>
        <p><strong>Variety:</strong> {{ item.variety }}</p>
        <div class="barcode">
            <!-- Text representation of barcode -->
            <p style="font-family: monospace; font-size: 12pt; letter-spacing: 2px;">*{{ item.barcode }}*</p>
            <p style="font-size: 8pt;">{{ item.barcode }}</p>
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

async def generate_barcodes(
    session: AsyncSession,
    org_id: Optional[int] = None,
    force: bool = False,
    export_path: Optional[str] = None,
    pdf_path: Optional[str] = None
):
    """
    Generate barcodes for seed lots.
    """
    logger.info("Fetching seed lots...")
    stmt = select(Seedlot)
    if org_id:
        stmt = stmt.where(Seedlot.organization_id == org_id)

    result = await session.execute(stmt)
    lots = result.scalars().all()

    updated_count = 0
    items_for_export = []

    logger.info(f"Found {len(lots)} seed lots.")

    for lot in lots:
        info = dict(lot.additional_info or {})
        current_barcode = info.get("barcode")

        if not current_barcode or force:
            # Use lot.id if available, otherwise lot.seedlot_db_id (which might be string)
            entity_id = str(lot.id) if lot.id else lot.seedlot_db_id
            new_barcode = barcode_service.generate_barcode_value(EntityType.SEED_LOT, entity_id)
            info["barcode"] = new_barcode
            lot.additional_info = info
            session.add(lot)
            updated_count += 1
            current_barcode = new_barcode

        items_for_export.append({
            "lot_id": lot.seedlot_db_id,
            "species": info.get("species", "Unknown"),
            "variety": lot.seedlot_name,
            "barcode": current_barcode
        })

    if updated_count > 0:
        await session.commit()
        logger.info(f"Updated {updated_count} seed lots with new barcodes.")
    else:
        logger.info("No seed lots needed updates.")

    if export_path:
        try:
            with open(export_path, 'w', newline='') as csvfile:
                fieldnames = ['lot_id', 'species', 'variety', 'barcode']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for item in items_for_export:
                    writer.writerow(item)
            logger.info(f"Exported barcodes to {export_path}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")

    if pdf_path:
        try:
            from jinja2 import Template
            from weasyprint import HTML

            logger.info("Generating PDF labels...")
            template = Template(TEMPLATE_HTML)
            html_content = template.render(items=items_for_export)
            HTML(string=html_content).write_pdf(pdf_path)
            logger.info(f"Generated PDF labels at {pdf_path}")
        except ImportError:
            logger.error("WeasyPrint or Jinja2 not installed. Cannot generate PDF.")
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Seed Inventory Barcode Generator")
    parser.add_argument("--org-id", type=int, help="Organization ID filter")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing barcodes")
    parser.add_argument("--output", type=str, help="Output CSV file path")
    parser.add_argument("--pdf", type=str, help="Output PDF file path")

    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        await generate_barcodes(
            session,
            org_id=args.org_id,
            force=args.force,
            export_path=args.output,
            pdf_path=args.pdf
        )

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
