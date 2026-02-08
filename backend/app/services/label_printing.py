"""
Label Printing Service
Manages label templates, print jobs, and label generation.
Queries real data from database - no demo/mock data.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


# Reference data for label templates (not demo data - configuration)
DEFAULT_TEMPLATES = [
    {
        "id": "plot-standard",
        "name": "Plot Label (Standard)",
        "type": "plot",
        "size": "2x1 inch",
        "width_mm": 50.8,
        "height_mm": 25.4,
        "fields": ["plot_id", "germplasm", "rep", "barcode"],
        "barcode_type": "qr",
        "is_default": True,
    },
    {
        "id": "seed-packet",
        "name": "Seed Packet Label",
        "type": "seed",
        "size": "3x2 inch",
        "width_mm": 76.2,
        "height_mm": 50.8,
        "fields": ["lot_number", "germplasm", "harvest_date", "weight", "barcode"],
        "barcode_type": "code128",
        "is_default": False,
    },
    {
        "id": "sample-tube",
        "name": "Sample Tube Label",
        "type": "sample",
        "size": "1x0.5 inch",
        "width_mm": 25.4,
        "height_mm": 12.7,
        "fields": ["sample_id", "date", "barcode"],
        "barcode_type": "datamatrix",
        "is_default": False,
    },
    {
        "id": "field-stake",
        "name": "Field Stake Label",
        "type": "plot",
        "size": "4x1 inch",
        "width_mm": 101.6,
        "height_mm": 25.4,
        "fields": ["entry", "germplasm", "row", "column"],
        "barcode_type": "qr",
        "is_default": False,
    },
    {
        "id": "accession-tag",
        "name": "Accession Tag",
        "type": "accession",
        "size": "2x3 inch",
        "width_mm": 50.8,
        "height_mm": 76.2,
        "fields": ["accession_id", "species", "origin", "collection_date", "barcode"],
        "barcode_type": "qr",
        "is_default": False,
    },
]


def generate_zpl_label(template: Dict[str, Any], data: Dict[str, Any]) -> str:
    """Generate ZPL code for a single label based on template and data.

    Args:
        template: Template definition dictionary
        data: Data dictionary for the label

    Returns:
        ZPL string
    """
    # Initialize ZPL
    zpl = ["^XA"]

    # 1. Setup Label Dimensions (203 dpi assumption = 8 dots/mm)
    dots_per_mm = 8
    width_mm = template.get("width_mm", 50.8)
    height_mm = template.get("height_mm", 25.4)

    width_dots = int(width_mm * dots_per_mm)
    height_dots = int(height_mm * dots_per_mm)

    zpl.append(f"^PW{width_dots}")
    zpl.append(f"^LL{height_dots}")
    zpl.append("^CI28")  # UTF-8 encoding

    # 2. Add Fields
    # Simple vertical layout logic
    current_y = 30
    x_pos = 30
    line_height = 35

    fields = template.get("fields", [])
    barcode_type = template.get("barcode_type", "qr")

    for field in fields:
        value = str(data.get(field, ""))
        if not value:
            continue

        if field == "barcode":
            # Barcode generation
            # Position barcode at bottom right or specific position
            # For simplicity, we put it at current_y but with specific logic

            if barcode_type == "qr":
                # QR Code: ^BQN,2,height
                zpl.append(f"^FO{width_dots - 150},{30}^BQN,2,4^FDQA,{value}^FS")
            elif barcode_type == "code128":
                # Code 128: ^BCN,height,N,N,N
                zpl.append(f"^FO{30},{height_dots - 100}^BCN,60,Y,N,N^FD{value}^FS")
            elif barcode_type == "datamatrix":
                # DataMatrix: ^BXN,height,200
                zpl.append(f"^FO{width_dots - 100},{30}^BXN,4,200^FD{value}^FS")
        else:
            # Text field
            # ^FOx,y^A0N,height,width^FDdata^FS
            # Truncate text if too long?
            zpl.append(f"^FO{x_pos},{current_y}^A0N,30,30^FD{field}: {value}^FS")
            current_y += line_height

    zpl.append("^XZ")
    return "".join(zpl)


class LabelPrintingService:
    """Service for label printing operations.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    def get_templates(self, label_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all label templates (reference data).
        
        Args:
            label_type: Filter by label type
            
        Returns:
            List of template dictionaries
        """
        templates = DEFAULT_TEMPLATES.copy()
        if label_type:
            templates = [t for t in templates if t["type"] == label_type]
        return templates

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a single template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template dictionary or None if not found
        """
        for t in DEFAULT_TEMPLATES:
            if t["id"] == template_id:
                return t
        return None

    def generate_label(self, template_id: str, data: Dict[str, Any]) -> Optional[str]:
        """Generate ZPL for a single label.

        Args:
            template_id: ID of the template to use
            data: Data to populate the label with

        Returns:
            ZPL string or None if template not found
        """
        template = self.get_template(template_id)
        if not template:
            return None

        return generate_zpl_label(template, data)

    async def get_label_data(
        self,
        db: AsyncSession,
        organization_id: int,
        source_type: str,
        study_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get data for label generation from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            source_type: Data source type (plots, seedlots, samples, accessions)
            study_id: Filter by study ID
            trial_id: Filter by trial ID
            limit: Maximum results
            
        Returns:
            List of data dictionaries for label generation
        """
        if source_type == "plots":
            return await self._get_plot_data(db, organization_id, study_id, limit)
        elif source_type == "seedlots":
            return await self._get_seedlot_data(db, organization_id, limit)
        elif source_type == "samples":
            return await self._get_sample_data(db, organization_id, limit)
        elif source_type == "accessions":
            return await self._get_accession_data(db, organization_id, limit)
        return []
    
    async def _get_plot_data(
        self,
        db: AsyncSession,
        organization_id: int,
        study_id: Optional[str],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get plot data for labels."""
        from app.models.phenotyping import ObservationUnit
        from sqlalchemy.orm import selectinload
        
        stmt = (
            select(ObservationUnit)
            .where(ObservationUnit.organization_id == organization_id)
            .options(selectinload(ObservationUnit.germplasm))
            .limit(limit)
        )
        
        if study_id:
            stmt = stmt.where(ObservationUnit.study_id == int(study_id))
        
        result = await db.execute(stmt)
        units = result.scalars().all()
        
        return [
            {
                "id": str(u.id),
                "plot_id": u.observation_unit_db_id or str(u.id),
                "germplasm": u.germplasm.germplasm_name if u.germplasm else "Unknown",
                "rep": u.additional_info.get("rep", "R1") if u.additional_info else "R1",
                "row": u.position_coordinate_y or 1,
                "column": u.position_coordinate_x or 1,
                "entry": u.additional_info.get("entry", f"E{u.id}") if u.additional_info else f"E{u.id}",
            }
            for u in units
        ]
    
    async def _get_seedlot_data(
        self,
        db: AsyncSession,
        organization_id: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get seedlot data for labels."""
        from app.models.germplasm import SeedLot
        from sqlalchemy.orm import selectinload
        
        stmt = (
            select(SeedLot)
            .where(SeedLot.organization_id == organization_id)
            .options(selectinload(SeedLot.germplasm))
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        lots = result.scalars().all()
        
        return [
            {
                "id": str(lot.id),
                "lot_number": lot.seed_lot_db_id or str(lot.id),
                "germplasm": lot.germplasm.germplasm_name if lot.germplasm else "Unknown",
                "harvest_date": lot.additional_info.get("harvest_date") if lot.additional_info else None,
                "weight": f"{lot.amount or 0}{lot.units or 'g'}",
                "quantity": lot.amount or 0,
            }
            for lot in lots
        ]
    
    async def _get_sample_data(
        self,
        db: AsyncSession,
        organization_id: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get sample data for labels."""
        from app.models.phenotyping import Sample
        
        stmt = (
            select(Sample)
            .where(Sample.organization_id == organization_id)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        samples = result.scalars().all()
        
        return [
            {
                "id": str(s.id),
                "sample_id": s.sample_db_id or str(s.id),
                "germplasm": s.additional_info.get("germplasm") if s.additional_info else "Unknown",
                "date": s.sample_timestamp.strftime("%Y-%m-%d") if s.sample_timestamp else None,
                "type": s.sample_type or "Unknown",
            }
            for s in samples
        ]
    
    async def _get_accession_data(
        self,
        db: AsyncSession,
        organization_id: int,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Get accession data for labels."""
        from app.models.germplasm import Germplasm
        
        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        accessions = result.scalars().all()
        
        return [
            {
                "id": str(a.id),
                "accession_id": a.accession_number or a.germplasm_db_id or str(a.id),
                "species": a.species or "Unknown",
                "origin": a.country_of_origin_code or "Unknown",
                "collection_date": a.acquisition_date,
            }
            for a in accessions
        ]

    async def get_print_jobs(
        self,
        db: AsyncSession,
        organization_id: int,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get print job history from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of print job dictionaries
        """
        from app.models.label_printing import PrintJob

        stmt = (
            select(PrintJob)
            .where(PrintJob.organization_id == organization_id)
            .order_by(PrintJob.created_at.desc())
            .limit(limit)
        )

        if status:
            stmt = stmt.where(PrintJob.status == status)

        result = await db.execute(stmt)
        jobs = result.scalars().all()

        return [
            {
                "id": job.job_id,
                "template_id": job.template_id,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "label_count": job.label_count,
                "copies": job.copies,
                "items": job.items,
                "created_by": job.created_by,
            }
            for job in jobs
        ]

    async def create_print_job(
        self,
        db: AsyncSession,
        organization_id: int,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new print job.
        
        Args:
            db: Database session
            organization_id: Organization ID
            data: Print job data
            
        Returns:
            Created print job dictionary
        """
        from app.models.label_printing import PrintJob, PrintJobStatus

        job_id = f"job-{uuid4().hex[:8]}"

        job = PrintJob(
            organization_id=organization_id,
            job_id=job_id,
            template_id=data.get("template_id"),
            status=PrintJobStatus.PENDING,
            label_count=data.get("label_count", 0),
            copies=data.get("copies", 1),
            items=data.get("items", []),
            created_by=data.get("created_by", "system"),
            created_at=datetime.now(timezone.utc)
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        return {
            "id": job.job_id,
            "template_id": job.template_id,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "completed_at": None,
            "label_count": job.label_count,
            "copies": job.copies,
            "items": job.items,
            "created_by": job.created_by,
        }

    async def get_stats(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get label printing statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary
        """
        from app.models.label_printing import PrintJob, PrintJobStatus

        # Get counts by status
        stmt_counts = (
            select(PrintJob.status, func.count(PrintJob.id))
            .where(PrintJob.organization_id == organization_id)
            .group_by(PrintJob.status)
        )

        result_counts = await db.execute(stmt_counts)
        counts = dict(result_counts.all())

        completed_count = counts.get(PrintJobStatus.COMPLETED, 0)
        pending_count = counts.get(PrintJobStatus.PENDING, 0)
        total_jobs = sum(counts.values())

        # Calculate total labels printed (only for completed jobs)
        stmt_labels = (
            select(func.sum(PrintJob.label_count * PrintJob.copies))
            .where(PrintJob.organization_id == organization_id)
            .where(PrintJob.status == PrintJobStatus.COMPLETED)
        )

        result_labels = await db.execute(stmt_labels)
        total_labels_printed = result_labels.scalar() or 0

        # Get last printed job
        stmt_last = (
            select(PrintJob.completed_at)
            .where(PrintJob.organization_id == organization_id)
            .where(PrintJob.status == PrintJobStatus.COMPLETED)
            .order_by(PrintJob.completed_at.desc())
            .limit(1)
        )

        result_last = await db.execute(stmt_last)
        last_print = result_last.scalar()
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_count,
            "pending_jobs": pending_count,
            "total_labels_printed": total_labels_printed,
            "templates_count": len(DEFAULT_TEMPLATES),
            "last_print": last_print.isoformat() if last_print else None,
        }


# Singleton instance
label_printing_service = LabelPrintingService()
