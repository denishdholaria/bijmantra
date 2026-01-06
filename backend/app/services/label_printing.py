"""
Label Printing Service
Manages label templates, print jobs, and label generation
"""
from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4


class LabelPrintingService:
    """Service for label printing operations."""

    def __init__(self):
        self._templates: dict[str, dict] = {}
        self._print_jobs: dict[str, dict] = {}
        self._init_templates()
        self._init_demo_data()

    def _init_templates(self):
        """Initialize default label templates."""
        templates = [
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
        for t in templates:
            self._templates[t["id"]] = t

    def _init_demo_data(self):
        """Initialize demo print jobs."""
        demo_jobs = [
            {
                "id": "job-001",
                "template_id": "plot-standard",
                "status": "completed",
                "created_at": "2025-12-22T10:30:00Z",
                "completed_at": "2025-12-22T10:32:00Z",
                "label_count": 48,
                "copies": 1,
                "created_by": "demo@bijmantra.org",
            },
            {
                "id": "job-002",
                "template_id": "seed-packet",
                "status": "completed",
                "created_at": "2025-12-22T14:15:00Z",
                "completed_at": "2025-12-22T14:18:00Z",
                "label_count": 24,
                "copies": 2,
                "created_by": "demo@bijmantra.org",
            },
        ]
        for job in demo_jobs:
            self._print_jobs[job["id"]] = job

    def get_templates(self, label_type: Optional[str] = None) -> list[dict]:
        """Get all label templates."""
        templates = list(self._templates.values())
        if label_type:
            templates = [t for t in templates if t["type"] == label_type]
        return templates

    def get_template(self, template_id: str) -> Optional[dict]:
        """Get a single template by ID."""
        return self._templates.get(template_id)

    def create_template(self, data: dict) -> dict:
        """Create a custom label template."""
        template_id = data.get("id") or f"custom-{uuid4().hex[:8]}"
        template = {
            "id": template_id,
            "name": data.get("name", "Custom Template"),
            "type": data.get("type", "custom"),
            "size": data.get("size", "2x1 inch"),
            "width_mm": data.get("width_mm", 50.8),
            "height_mm": data.get("height_mm", 25.4),
            "fields": data.get("fields", []),
            "barcode_type": data.get("barcode_type", "qr"),
            "is_default": False,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._templates[template_id] = template
        return template

    def get_label_data(
        self,
        source_type: str,
        study_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get data for label generation based on source type."""
        # Demo data for different source types
        if source_type == "plots":
            return [
                {"id": "1", "plot_id": "A-01-01", "germplasm": "IR64", "rep": "R1", "row": 1, "column": 1, "entry": "E001"},
                {"id": "2", "plot_id": "A-01-02", "germplasm": "Nipponbare", "rep": "R1", "row": 1, "column": 2, "entry": "E002"},
                {"id": "3", "plot_id": "A-01-03", "germplasm": "Kasalath", "rep": "R1", "row": 1, "column": 3, "entry": "E003"},
                {"id": "4", "plot_id": "A-02-01", "germplasm": "IR64", "rep": "R2", "row": 2, "column": 1, "entry": "E001"},
                {"id": "5", "plot_id": "A-02-02", "germplasm": "Nipponbare", "rep": "R2", "row": 2, "column": 2, "entry": "E002"},
                {"id": "6", "plot_id": "A-02-03", "germplasm": "Kasalath", "rep": "R2", "row": 2, "column": 3, "entry": "E003"},
                {"id": "7", "plot_id": "B-01-01", "germplasm": "N22", "rep": "R1", "row": 3, "column": 1, "entry": "E004"},
                {"id": "8", "plot_id": "B-01-02", "germplasm": "Moroberekan", "rep": "R1", "row": 3, "column": 2, "entry": "E005"},
            ]
        elif source_type == "seedlots":
            return [
                {"id": "1", "lot_number": "SL-2025-001", "germplasm": "IR64", "harvest_date": "2025-11-15", "weight": "500g", "quantity": 1000},
                {"id": "2", "lot_number": "SL-2025-002", "germplasm": "Nipponbare", "harvest_date": "2025-11-18", "weight": "450g", "quantity": 900},
                {"id": "3", "lot_number": "SL-2025-003", "germplasm": "Kasalath", "harvest_date": "2025-11-20", "weight": "380g", "quantity": 760},
                {"id": "4", "lot_number": "SL-2025-004", "germplasm": "N22", "harvest_date": "2025-11-22", "weight": "420g", "quantity": 840},
            ]
        elif source_type == "samples":
            return [
                {"id": "1", "sample_id": "SAM-001", "germplasm": "IR64", "date": "2025-12-20", "type": "Leaf"},
                {"id": "2", "sample_id": "SAM-002", "germplasm": "Nipponbare", "date": "2025-12-20", "type": "Leaf"},
                {"id": "3", "sample_id": "SAM-003", "germplasm": "Kasalath", "date": "2025-12-20", "type": "Root"},
                {"id": "4", "sample_id": "SAM-004", "germplasm": "N22", "date": "2025-12-21", "type": "Seed"},
                {"id": "5", "sample_id": "SAM-005", "germplasm": "Moroberekan", "date": "2025-12-21", "type": "Leaf"},
            ]
        elif source_type == "accessions":
            return [
                {"id": "1", "accession_id": "ACC-001", "species": "Oryza sativa", "origin": "India", "collection_date": "2024-06-15"},
                {"id": "2", "accession_id": "ACC-002", "species": "Oryza sativa", "origin": "Japan", "collection_date": "2024-07-20"},
                {"id": "3", "accession_id": "ACC-003", "species": "Oryza sativa", "origin": "Bangladesh", "collection_date": "2024-08-10"},
            ]
        return []

    def create_print_job(self, data: dict) -> dict:
        """Create a new print job."""
        job_id = f"job-{uuid4().hex[:8]}"
        job = {
            "id": job_id,
            "template_id": data.get("template_id"),
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "label_count": data.get("label_count", 0),
            "copies": data.get("copies", 1),
            "items": data.get("items", []),
            "created_by": data.get("created_by", "system"),
        }
        self._print_jobs[job_id] = job
        return job

    def get_print_jobs(self, status: Optional[str] = None, limit: int = 50) -> list[dict]:
        """Get print job history."""
        jobs = list(self._print_jobs.values())
        if status:
            jobs = [j for j in jobs if j["status"] == status]
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs[:limit]

    def get_print_job(self, job_id: str) -> Optional[dict]:
        """Get a single print job."""
        return self._print_jobs.get(job_id)

    def update_print_job_status(self, job_id: str, status: str) -> Optional[dict]:
        """Update print job status."""
        if job_id not in self._print_jobs:
            return None
        job = self._print_jobs[job_id]
        job["status"] = status
        if status == "completed":
            job["completed_at"] = datetime.now(UTC).isoformat()
        return job

    def get_stats(self) -> dict:
        """Get label printing statistics."""
        jobs = list(self._print_jobs.values())
        completed = [j for j in jobs if j["status"] == "completed"]
        total_labels = sum(j.get("label_count", 0) * j.get("copies", 1) for j in completed)
        
        return {
            "total_jobs": len(jobs),
            "completed_jobs": len(completed),
            "pending_jobs": len([j for j in jobs if j["status"] == "pending"]),
            "total_labels_printed": total_labels,
            "templates_count": len(self._templates),
            "last_print": max((j.get("completed_at") for j in completed if j.get("completed_at")), default=None),
        }


# Singleton instance
label_printing_service = LabelPrintingService()
