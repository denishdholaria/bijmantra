"""
Vision Annotation Service - Phase 2: Advanced Annotation
Bounding box, segmentation, collaborative workflow, quality control

Converted to database queries per Zero Mock Data Policy (Session 77).
Returns empty results when no data exists.
"""

from datetime import datetime, UTC
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.vision import (
    VisionAnnotation,
    AnnotationTask,
    AnnotationTaskItem,
    AnnotationType,
    AnnotationStatus
)


class VisionAnnotationService:
    """Service for managing annotations.
    
    All methods are async and require database session.
    """

    async def create_annotation(
        self,
        db: AsyncSession,
        organization_id: int,
        image_id: str,
        dataset_id: str,
        annotation_type: AnnotationType,
        data: dict,
        annotator_id: str = "system",
    ) -> dict:
        """Create a new annotation for an image."""

        annotation = VisionAnnotation(
            image_id=image_id,
            dataset_id=dataset_id,
            annotation_type=annotation_type,
            data=data,
            status=AnnotationStatus.PENDING,
            annotator_id=annotator_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

        db.add(annotation)
        await db.commit()
        await db.refresh(annotation)

        # If there is a pending task item for this image, link it
        # This is a bit complex without knowing the specific task context,
        # but we can check if there's any pending task item for this image and dataset?
        # For now, we'll leave task linking to the task workflow or explicit update.

        return {
            "id": annotation.id,
            "image_id": annotation.image_id,
            "dataset_id": annotation.dataset_id,
            "annotation_type": annotation.annotation_type,
            "data": annotation.data,
            "status": annotation.status,
            "annotator_id": annotation.annotator_id,
            "reviewer_id": annotation.reviewer_id,
            "created_at": annotation.created_at.isoformat(),
            "updated_at": annotation.updated_at.isoformat(),
            "review_notes": annotation.review_notes,
        }

    async def create_bounding_box(
        self,
        db: AsyncSession,
        organization_id: int,
        image_id: str,
        dataset_id: str,
        boxes: list[dict],
        annotator_id: str = "system",
    ) -> dict:
        """Create bounding box annotations."""
        return await self.create_annotation(
            db=db,
            organization_id=organization_id,
            image_id=image_id,
            dataset_id=dataset_id,
            annotation_type=AnnotationType.BOUNDING_BOX,
            data={"boxes": boxes},
            annotator_id=annotator_id,
        )

    async def create_segmentation(
        self,
        db: AsyncSession,
        organization_id: int,
        image_id: str,
        dataset_id: str,
        polygons: list[dict],
        annotator_id: str = "system",
    ) -> dict:
        """Create segmentation annotations."""
        return await self.create_annotation(
            db=db,
            organization_id=organization_id,
            image_id=image_id,
            dataset_id=dataset_id,
            annotation_type=AnnotationType.SEGMENTATION,
            data={"polygons": polygons},
            annotator_id=annotator_id,
        )

    async def create_keypoints(
        self,
        db: AsyncSession,
        organization_id: int,
        image_id: str,
        dataset_id: str,
        keypoints: list[dict],
        annotator_id: str = "system",
    ) -> dict:
        """Create keypoint annotations."""
        return await self.create_annotation(
            db=db,
            organization_id=organization_id,
            image_id=image_id,
            dataset_id=dataset_id,
            annotation_type=AnnotationType.KEYPOINTS,
            data={"keypoints": keypoints},
            annotator_id=annotator_id,
        )

    async def get_annotation(
        self,
        db: AsyncSession,
        organization_id: int,
        annotation_id: str,
    ) -> Optional[dict]:
        """Get annotation by ID."""
        try:
            stmt = select(VisionAnnotation).where(VisionAnnotation.id == int(annotation_id))
            result = await db.execute(stmt)
            annotation = result.scalar_one_or_none()

            if not annotation:
                return None

            return {
                "id": annotation.id,
                "image_id": annotation.image_id,
                "dataset_id": annotation.dataset_id,
                "annotation_type": annotation.annotation_type,
                "data": annotation.data,
                "status": annotation.status,
                "annotator_id": annotation.annotator_id,
                "reviewer_id": annotation.reviewer_id,
                "created_at": annotation.created_at.isoformat(),
                "updated_at": annotation.updated_at.isoformat(),
                "review_notes": annotation.review_notes,
            }
        except ValueError:
            return None

    async def get_image_annotations(
        self,
        db: AsyncSession,
        organization_id: int,
        image_id: str,
    ) -> list[dict]:
        """Get all annotations for an image."""
        stmt = select(VisionAnnotation).where(VisionAnnotation.image_id == image_id)
        result = await db.execute(stmt)
        annotations = result.scalars().all()

        return [
            {
                "id": a.id,
                "image_id": a.image_id,
                "dataset_id": a.dataset_id,
                "annotation_type": a.annotation_type,
                "data": a.data,
                "status": a.status,
                "annotator_id": a.annotator_id,
                "reviewer_id": a.reviewer_id,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat(),
            }
            for a in annotations
        ]

    async def update_annotation(
        self,
        db: AsyncSession,
        organization_id: int,
        annotation_id: str,
        data: dict,
    ) -> Optional[dict]:
        """Update annotation data."""
        try:
            stmt = select(VisionAnnotation).where(VisionAnnotation.id == int(annotation_id))
            result = await db.execute(stmt)
            annotation = result.scalar_one_or_none()

            if not annotation:
                return None

            if "data" in data:
                annotation.data = data["data"]
            if "status" in data:
                annotation.status = data["status"]

            annotation.updated_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(annotation)

            return {
                "id": annotation.id,
                "image_id": annotation.image_id,
                "status": annotation.status,
                "data": annotation.data,
                "updated_at": annotation.updated_at.isoformat()
            }
        except ValueError:
            return None

    async def submit_for_review(
        self,
        db: AsyncSession,
        organization_id: int,
        annotation_id: str,
    ) -> Optional[dict]:
        """Submit annotation for review."""
        return await self.update_annotation(
            db, organization_id, annotation_id, {"status": AnnotationStatus.REVIEW}
        )

    async def review_annotation(
        self,
        db: AsyncSession,
        organization_id: int,
        annotation_id: str,
        approved: bool,
        reviewer_id: str,
        notes: Optional[str] = None,
    ) -> Optional[dict]:
        """Review and approve/reject annotation."""
        status = AnnotationStatus.APPROVED if approved else AnnotationStatus.REJECTED

        try:
            stmt = select(VisionAnnotation).where(VisionAnnotation.id == int(annotation_id))
            result = await db.execute(stmt)
            annotation = result.scalar_one_or_none()

            if not annotation:
                return None

            annotation.status = status
            annotation.reviewer_id = reviewer_id
            annotation.review_notes = notes
            annotation.updated_at = datetime.now(UTC)

            await db.commit()
            await db.refresh(annotation)

            return {
                "id": annotation.id,
                "status": annotation.status,
                "reviewer_id": annotation.reviewer_id,
                "review_notes": annotation.review_notes,
                "updated_at": annotation.updated_at.isoformat()
            }
        except ValueError:
            return None

    async def delete_annotation(
        self,
        db: AsyncSession,
        organization_id: int,
        annotation_id: str,
    ) -> bool:
        """Delete an annotation."""
        try:
            stmt = select(VisionAnnotation).where(VisionAnnotation.id == int(annotation_id))
            result = await db.execute(stmt)
            annotation = result.scalar_one_or_none()

            if not annotation:
                return False

            await db.delete(annotation)
            await db.commit()
            return True
        except ValueError:
            return False


class AnnotationTaskService:
    """Service for managing annotation tasks (collaborative workflow).
    
    All methods are async and require database session.
    """

    async def create_task(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
        name: str,
        annotation_type: AnnotationType,
        image_ids: list[str],
        assigned_to: list[str],
    ) -> dict:
        """Create an annotation task."""

        # Create the task
        task = AnnotationTask(
            dataset_id=dataset_id,
            name=name,
            annotation_type=annotation_type,
            status=AnnotationStatus.PENDING,
            total_images=len(image_ids),
            completed_images=0,
            assigned_to=assigned_to,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Create task items
        items = [
            AnnotationTaskItem(
                task_id=task.id,
                image_id=img_id,
                status=AnnotationStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            for img_id in image_ids
        ]

        db.add_all(items)
        await db.commit()

        return {
            "id": task.id,
            "dataset_id": task.dataset_id,
            "name": task.name,
            "annotation_type": task.annotation_type,
            "status": task.status,
            "total_images": task.total_images,
            "completed_images": task.completed_images,
            "image_ids": image_ids,
            "assigned_to": task.assigned_to,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def get_task(
        self,
        db: AsyncSession,
        organization_id: int,
        task_id: str,
    ) -> Optional[dict]:
        """Get task by ID."""
        try:
            stmt = select(AnnotationTask).options(selectinload(AnnotationTask.items)).where(AnnotationTask.id == int(task_id))
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return None

            return {
                "id": task.id,
                "dataset_id": task.dataset_id,
                "name": task.name,
                "annotation_type": task.annotation_type,
                "status": task.status,
                "total_images": task.total_images,
                "completed_images": task.completed_images,
                "image_ids": [item.image_id for item in task.items],
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
        except ValueError:
            return None

    async def list_tasks(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: Optional[str] = None,
        status: Optional[AnnotationStatus] = None,
        annotator_id: Optional[str] = None,
    ) -> list[dict]:
        """List annotation tasks."""
        stmt = select(AnnotationTask)

        if dataset_id:
            stmt = stmt.where(AnnotationTask.dataset_id == dataset_id)
        if status:
            stmt = stmt.where(AnnotationTask.status == status)

        # Filtering by annotator_id involves checking the JSON array 'assigned_to'
        # This depends on DB dialect (PG vs SQLite).
        # For simple list return, we can filter in python if needed, or implement dialect specific query.
        # Given potential SQLite usage, we might skip complex JSON query for now or do post-filter.

        result = await db.execute(stmt)
        tasks = result.scalars().all()

        task_list = []
        for task in tasks:
            if annotator_id and annotator_id not in (task.assigned_to or []):
                continue

            task_list.append({
                "id": task.id,
                "dataset_id": task.dataset_id,
                "name": task.name,
                "annotation_type": task.annotation_type,
                "status": task.status,
                "total_images": task.total_images,
                "completed_images": task.completed_images,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
            })

        return task_list

    async def update_task_progress(
        self,
        db: AsyncSession,
        organization_id: int,
        task_id: str,
        completed_images: int,
    ) -> Optional[dict]:
        """Update task progress."""
        try:
            stmt = select(AnnotationTask).where(AnnotationTask.id == int(task_id))
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return None

            task.completed_images = completed_images
            if task.completed_images >= task.total_images:
                task.status = AnnotationStatus.COMPLETED
                task.completed_at = datetime.now(UTC)

            task.updated_at = datetime.now(UTC)
            await db.commit()

            return {
                "id": task.id,
                "completed_images": task.completed_images,
                "status": task.status
            }
        except ValueError:
            return None

    async def assign_annotators(
        self,
        db: AsyncSession,
        organization_id: int,
        task_id: str,
        annotator_ids: list[str],
    ) -> Optional[dict]:
        """Assign annotators to a task."""
        try:
            stmt = select(AnnotationTask).where(AnnotationTask.id == int(task_id))
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return None

            task.assigned_to = annotator_ids
            task.updated_at = datetime.now(UTC)
            await db.commit()

            return {
                "id": task.id,
                "assigned_to": task.assigned_to
            }
        except ValueError:
            return None


class QualityControlService:
    """Service for annotation quality control.
    
    All methods are async and require database session.
    Returns empty results when no annotation data exists.
    """

    async def calculate_inter_annotator_agreement(
        self,
        db: AsyncSession,
        organization_id: int,
        annotations: list[dict],
    ) -> dict:
        """Calculate inter-annotator agreement (Cohen's Kappa)."""
        if len(annotations) < 2:
            return {
                "kappa": None,
                "agreement_percent": None,
                "interpretation": None,
                "annotations_compared": 0,
                "message": "Need at least 2 annotations to calculate agreement",
            }

        # Group by image_id
        image_annotations = {}
        annotators = set()

        for ann in annotations:
            aid = ann.get('annotator_id')
            iid = ann.get('image_id')

            # Check for data structure. Assuming classification uses 'label' in data.
            data = ann.get('data') or {}
            label = data.get('label')

            if not aid or not iid or label is None:
                continue

            annotators.add(aid)
            if iid not in image_annotations:
                image_annotations[iid] = {}
            image_annotations[iid][aid] = label

        annotators_list = sorted(list(annotators))
        if len(annotators_list) != 2:
            return {
                "kappa": None,
                "agreement_percent": None,
                "interpretation": None,
                "annotations_compared": 0,
                "message": f"Need exactly 2 unique annotators to calculate Cohen's Kappa, found {len(annotators_list)}",
            }

        a1, a2 = annotators_list

        # Filter images annotated by both
        common_images = []
        for iid, anns in image_annotations.items():
            if a1 in anns and a2 in anns:
                common_images.append((anns[a1], anns[a2]))

        if not common_images:
            return {
                "kappa": None,
                "agreement_percent": None,
                "interpretation": None,
                "annotations_compared": 0,
                "message": "No common images annotated by both annotators",
            }

        # Get unique labels
        labels = set()
        for l1, l2 in common_images:
            labels.add(l1)
            labels.add(l2)
        labels_list = sorted(list(labels))
        label_to_idx = {l: i for i, l in enumerate(labels_list)}

        k = len(labels_list)
        confusion = [[0] * k for _ in range(k)]

        n = len(common_images)

        for l1, l2 in common_images:
            i = label_to_idx[l1]
            j = label_to_idx[l2]
            confusion[i][j] += 1

        # Calculate Po
        sum_diag = sum(confusion[i][i] for i in range(k))
        po = sum_diag / n

        # Calculate Pe
        row_sums = [sum(row) for row in confusion]
        col_sums = [sum(confusion[i][j] for i in range(k)) for j in range(k)]

        pe = sum(row_sums[i] * col_sums[i] for i in range(k)) / (n * n)

        if pe == 1:
            kappa = 1.0 if po == 1 else 0.0
        else:
            kappa = (po - pe) / (1 - pe)

        # Interpretation
        if kappa > 0.8:
            interpretation = "Almost perfect agreement"
        elif kappa > 0.6:
            interpretation = "Substantial agreement"
        elif kappa > 0.4:
            interpretation = "Moderate agreement"
        elif kappa > 0.2:
            interpretation = "Fair agreement"
        elif kappa > 0:
            interpretation = "Slight agreement"
        else:
            interpretation = "Poor agreement"

        return {
            "kappa": kappa,
            "agreement_percent": po * 100,
            "interpretation": interpretation,
            "annotations_compared": n,
            "message": "Agreement calculated successfully",
        }

    async def get_annotator_stats(
        self,
        db: AsyncSession,
        organization_id: int,
        annotator_id: str,
    ) -> dict:
        """Get statistics for an annotator."""

        # Get count of approved/rejected annotations
        stmt = select(VisionAnnotation).where(VisionAnnotation.annotator_id == annotator_id)
        result = await db.execute(stmt)
        annotations = result.scalars().all()

        total = len(annotations)
        approved = sum(1 for a in annotations if a.status == AnnotationStatus.APPROVED)
        rejected = sum(1 for a in annotations if a.status == AnnotationStatus.REJECTED)

        approval_rate = (approved / total * 100) if total > 0 else 0

        return {
            "annotator_id": annotator_id,
            "name": None, # Should fetch user name if possible
            "total_annotations": total,
            "session_annotations": 0, # Not tracking sessions yet
            "approved": approved,
            "rejected": rejected,
            "accuracy": None, # Needs ground truth
            "approval_rate": round(approval_rate, 1),
            "message": "Stats calculated from database",
        }

    async def list_annotators(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> list[dict]:
        """List all annotators."""
        stmt = select(VisionAnnotation.annotator_id).distinct()
        result = await db.execute(stmt)
        annotator_ids = result.scalars().all()

        return [{"id": aid, "name": f"User {aid}"} for aid in annotator_ids]

    async def flag_for_review(
        self,
        db: AsyncSession,
        organization_id: int,
        annotation_id: str,
        reason: str,
    ) -> Optional[dict]:
        """Flag an annotation for review."""
        try:
            stmt = select(VisionAnnotation).where(VisionAnnotation.id == int(annotation_id))
            result = await db.execute(stmt)
            annotation = result.scalar_one_or_none()

            if not annotation:
                return None

            annotation.status = AnnotationStatus.REVIEW
            annotation.review_notes = reason
            await db.commit()

            return {"id": annotation.id, "status": annotation.status}
        except ValueError:
            return None

    async def get_quality_metrics(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
    ) -> dict:
        """Get quality metrics for a dataset."""
        stmt = select(VisionAnnotation).where(VisionAnnotation.dataset_id == dataset_id)
        result = await db.execute(stmt)
        annotations = result.scalars().all()

        total = len(annotations)
        approved = sum(1 for a in annotations if a.status == AnnotationStatus.APPROVED)
        rejected = sum(1 for a in annotations if a.status == AnnotationStatus.REJECTED)
        pending = sum(1 for a in annotations if a.status == AnnotationStatus.PENDING)
        in_progress = sum(1 for a in annotations if a.status == AnnotationStatus.IN_PROGRESS)

        approval_rate = (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 0

        return {
            "dataset_id": dataset_id,
            "total_annotations": total,
            "approved": approved,
            "rejected": rejected,
            "pending_review": sum(1 for a in annotations if a.status == AnnotationStatus.REVIEW),
            "in_progress": in_progress,
            "approval_rate": round(approval_rate, 1),
            "quality_score": round(approval_rate, 1), # Simplified score
            "message": "Metrics calculated from database",
        }


# Service instances
vision_annotation_service = VisionAnnotationService()
annotation_task_service = AnnotationTaskService()
quality_control_service = QualityControlService()
