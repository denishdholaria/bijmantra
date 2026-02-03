"""
Seed Processing Batch Service
Manage seed processing batches through various stages
"""

from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid


class ProcessingStage(Enum):
    RECEIVING = "receiving"
    PRE_CLEANING = "pre_cleaning"
    DRYING = "drying"
    CLEANING = "cleaning"
    GRADING = "grading"
    TREATING = "treating"
    PACKAGING = "packaging"
    LABELING = "labeling"
    STORAGE = "storage"
    COMPLETED = "completed"


class BatchStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class StageRecord:
    stage_id: str
    stage: str
    started_at: str
    completed_at: Optional[str] = None
    operator: str = ""
    equipment: str = ""
    input_quantity_kg: float = 0.0
    output_quantity_kg: float = 0.0
    loss_kg: float = 0.0
    loss_percent: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    status: str = "in_progress"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ProcessingBatch:
    batch_id: str
    batch_number: str
    lot_id: str
    variety_name: str
    crop: str
    seed_class: str
    input_quantity_kg: float
    current_quantity_kg: float
    current_stage: str
    status: str
    stages: List[StageRecord]
    quality_checks: List[Dict]
    created_at: str
    created_by: str
    completed_at: Optional[str] = None
    target_output_kg: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['stages'] = [s.to_dict() if isinstance(s, StageRecord) else s for s in self.stages]
        return d


class ProcessingBatchService:
    """Service for managing seed processing batches"""

    def __init__(self):
        self._batches: Dict[str, ProcessingBatch] = {}
        self._batch_counter = 0
        self._stage_order = [s.value for s in ProcessingStage]

    def _generate_batch_number(self) -> str:
        self._batch_counter += 1
        return f"BATCH-{datetime.now().year}-{self._batch_counter:04d}"

    def create_batch(
        self,
        lot_id: str,
        variety_name: str,
        crop: str,
        seed_class: str,
        input_quantity_kg: float,
        target_output_kg: Optional[float] = None,
        notes: str = "",
        created_by: str = "system",
    ) -> ProcessingBatch:
        """Create a new processing batch"""
        batch_id = str(uuid.uuid4())
        batch_number = self._generate_batch_number()

        batch = ProcessingBatch(
            batch_id=batch_id,
            batch_number=batch_number,
            lot_id=lot_id,
            variety_name=variety_name,
            crop=crop,
            seed_class=seed_class,
            input_quantity_kg=input_quantity_kg,
            current_quantity_kg=input_quantity_kg,
            current_stage=ProcessingStage.RECEIVING.value,
            status=BatchStatus.PENDING.value,
            stages=[],
            quality_checks=[],
            created_at=datetime.now(UTC).isoformat(),
            created_by=created_by,
            target_output_kg=target_output_kg,
            notes=notes,
        )

        self._batches[batch_id] = batch
        return batch

    def get_batch(self, batch_id: str) -> Optional[Dict]:
        """Get batch by ID"""
        batch = self._batches.get(batch_id)
        return batch.to_dict() if batch else None

    def list_batches(
        self,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        lot_id: Optional[str] = None,
        crop: Optional[str] = None,
    ) -> List[Dict]:
        """List batches with filters"""
        results = []
        for batch in self._batches.values():
            if status and batch.status != status:
                continue
            if stage and batch.current_stage != stage:
                continue
            if lot_id and batch.lot_id != lot_id:
                continue
            if crop and batch.crop.lower() != crop.lower():
                continue
            results.append(batch.to_dict())
        return sorted(results, key=lambda x: x["created_at"], reverse=True)

    def start_stage(
        self,
        batch_id: str,
        stage: str,
        operator: str,
        equipment: str = "",
        input_quantity_kg: Optional[float] = None,
        parameters: Optional[Dict] = None,
    ) -> Dict:
        """Start a processing stage"""
        batch = self._batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        if batch.status == BatchStatus.COMPLETED.value:
            raise ValueError("Cannot modify completed batch")

        # Validate stage order
        if stage not in self._stage_order:
            raise ValueError(f"Invalid stage: {stage}")

        stage_record = StageRecord(
            stage_id=str(uuid.uuid4()),
            stage=stage,
            started_at=datetime.now(UTC).isoformat(),
            operator=operator,
            equipment=equipment,
            input_quantity_kg=input_quantity_kg or batch.current_quantity_kg,
            parameters=parameters or {},
            status="in_progress",
        )

        batch.stages.append(stage_record)
        batch.current_stage = stage
        batch.status = BatchStatus.IN_PROGRESS.value

        return batch.to_dict()

    def complete_stage(
        self,
        batch_id: str,
        stage_id: str,
        output_quantity_kg: float,
        notes: str = "",
    ) -> Dict:
        """Complete a processing stage"""
        batch = self._batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        stage_record = None
        for s in batch.stages:
            if s.stage_id == stage_id:
                stage_record = s
                break

        if not stage_record:
            raise ValueError(f"Stage {stage_id} not found")

        stage_record.completed_at = datetime.now(UTC).isoformat()
        stage_record.output_quantity_kg = output_quantity_kg
        stage_record.loss_kg = stage_record.input_quantity_kg - output_quantity_kg
        stage_record.loss_percent = (stage_record.loss_kg / stage_record.input_quantity_kg * 100) if stage_record.input_quantity_kg > 0 else 0
        stage_record.notes = notes
        stage_record.status = "completed"

        batch.current_quantity_kg = output_quantity_kg

        # Check if this was the last stage
        if stage_record.stage == ProcessingStage.COMPLETED.value:
            batch.status = BatchStatus.COMPLETED.value
            batch.completed_at = datetime.now(UTC).isoformat()

        return batch.to_dict()

    def add_quality_check(
        self,
        batch_id: str,
        check_type: str,
        result_value: float,
        passed: bool,
        checked_by: str,
        notes: str = "",
    ) -> Dict:
        """Add quality check to batch"""
        batch = self._batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        check = {
            "check_id": str(uuid.uuid4()),
            "check_type": check_type,
            "result_value": result_value,
            "passed": passed,
            "checked_by": checked_by,
            "checked_at": datetime.now(UTC).isoformat(),
            "stage": batch.current_stage,
            "notes": notes,
        }

        batch.quality_checks.append(check)
        return batch.to_dict()

    def hold_batch(self, batch_id: str, reason: str) -> Dict:
        """Put batch on hold"""
        batch = self._batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        batch.status = BatchStatus.ON_HOLD.value
        batch.notes = f"{batch.notes}\nHold: {reason}"
        return batch.to_dict()

    def resume_batch(self, batch_id: str) -> Dict:
        """Resume batch from hold"""
        batch = self._batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        if batch.status != BatchStatus.ON_HOLD.value:
            raise ValueError("Batch is not on hold")

        batch.status = BatchStatus.IN_PROGRESS.value
        return batch.to_dict()

    def reject_batch(self, batch_id: str, reason: str) -> Dict:
        """Reject a batch"""
        batch = self._batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        batch.status = BatchStatus.REJECTED.value
        batch.notes = f"{batch.notes}\nRejected: {reason}"
        return batch.to_dict()

    def get_stage_summary(self, batch_id: str) -> Dict:
        """Get processing summary for a batch"""
        batch = self._batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        total_loss = sum(s.loss_kg for s in batch.stages if isinstance(s, StageRecord))
        total_loss_percent = (total_loss / batch.input_quantity_kg * 100) if batch.input_quantity_kg > 0 else 0

        return {
            "batch_id": batch_id,
            "batch_number": batch.batch_number,
            "input_quantity_kg": batch.input_quantity_kg,
            "current_quantity_kg": batch.current_quantity_kg,
            "total_loss_kg": total_loss,
            "total_loss_percent": round(total_loss_percent, 2),
            "stages_completed": sum(1 for s in batch.stages if isinstance(s, StageRecord) and s.status == "completed"),
            "quality_checks": len(batch.quality_checks),
            "quality_passed": sum(1 for c in batch.quality_checks if c.get("passed")),
        }

    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        total = len(self._batches)
        by_status = {}
        by_stage = {}
        total_input = 0.0
        total_output = 0.0

        for batch in self._batches.values():
            by_status[batch.status] = by_status.get(batch.status, 0) + 1
            by_stage[batch.current_stage] = by_stage.get(batch.current_stage, 0) + 1
            total_input += batch.input_quantity_kg
            if batch.status == BatchStatus.COMPLETED.value:
                total_output += batch.current_quantity_kg

        return {
            "total_batches": total,
            "by_status": by_status,
            "by_stage": by_stage,
            "total_input_kg": total_input,
            "total_output_kg": total_output,
            "average_yield_percent": round((total_output / total_input * 100) if total_input > 0 else 0, 2),
        }

    def get_processing_stages(self) -> List[Dict]:
        """Get available processing stages"""
        return [
            {"id": "receiving", "name": "Receiving", "order": 1, "description": "Receive raw seed from field"},
            {"id": "pre_cleaning", "name": "Pre-Cleaning", "order": 2, "description": "Remove large debris and foreign matter"},
            {"id": "drying", "name": "Drying", "order": 3, "description": "Reduce moisture content"},
            {"id": "cleaning", "name": "Cleaning", "order": 4, "description": "Remove weed seeds and inert matter"},
            {"id": "grading", "name": "Grading", "order": 5, "description": "Size grading and separation"},
            {"id": "treating", "name": "Treating", "order": 6, "description": "Apply seed treatment chemicals"},
            {"id": "packaging", "name": "Packaging", "order": 7, "description": "Pack into bags/containers"},
            {"id": "labeling", "name": "Labeling", "order": 8, "description": "Apply labels and tags"},
            {"id": "storage", "name": "Storage", "order": 9, "description": "Move to storage location"},
            {"id": "completed", "name": "Completed", "order": 10, "description": "Processing complete"},
        ]


# Singleton instance
processing_service = ProcessingBatchService()


def get_processing_service() -> ProcessingBatchService:
    return processing_service
