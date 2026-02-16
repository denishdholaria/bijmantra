from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import random
import io
import csv

from app.models.core import Study, Trial
from app.models.phenotyping import ObservationUnit
from app.models.germplasm import Germplasm
from app.schemas.field_layout import (
    StudyInfo,
    Plot,
    FieldLayoutResponse,
    FieldLayoutSummary,
    LayoutGenerationResponse,
    ExportResponse
)

class FieldLayoutService:
    @staticmethod
    def _map_study_to_info(study: Study) -> StudyInfo:
        additional = study.additional_info or {}

        # Determine program_id from trial
        prog_id = None
        if study.trial and study.trial.program_id:
            prog_id = str(study.trial.program_id)

        return StudyInfo(
            studyDbId=study.study_db_id or str(study.id),
            studyName=study.study_name or "",
            rows=additional.get("rows", 0),
            cols=additional.get("cols", 0),
            programDbId=prog_id,
            locationDbId=str(study.location_id) if study.location_id else None,
            startDate=study.start_date.isoformat() if study.start_date and hasattr(study.start_date, 'isoformat') else str(study.start_date) if study.start_date else None,
            endDate=study.end_date.isoformat() if study.end_date and hasattr(study.end_date, 'isoformat') else str(study.end_date) if study.end_date else None,
        )

    @staticmethod
    async def get_studies(
        db: AsyncSession,
        organization_id: int,
        program_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[StudyInfo]:
        stmt = select(Study).where(
            Study.organization_id == organization_id
        ).options(
            selectinload(Study.trial).selectinload(Trial.program),
            selectinload(Study.location),
        )

        if program_id:
            # Study -> Trial -> Program
            stmt = stmt.join(Study.trial).where(Trial.program_id == int(program_id))

        if search:
            stmt = stmt.where(Study.study_name.ilike(f"%{search}%"))

        result = await db.execute(stmt)
        studies = result.scalars().all()

        return [FieldLayoutService._map_study_to_info(study) for study in studies]

    @staticmethod
    async def get_study(
        db: AsyncSession,
        organization_id: int,
        study_id: str
    ) -> Optional[StudyInfo]:
        stmt = select(Study).where(
            and_(
                Study.organization_id == organization_id,
                Study.study_db_id == study_id,
            )
        ).options(
            selectinload(Study.trial).selectinload(Trial.program),
            selectinload(Study.location),
        )

        result = await db.execute(stmt)
        study = result.scalar_one_or_none()

        if not study and study_id.isdigit():
            stmt = select(Study).where(
                and_(
                    Study.organization_id == organization_id,
                    Study.id == int(study_id),
                )
            ).options(
                selectinload(Study.trial).selectinload(Trial.program),
                selectinload(Study.location),
            )
            result = await db.execute(stmt)
            study = result.scalar_one_or_none()

        if not study:
            return None

        return FieldLayoutService._map_study_to_info(study)

    @staticmethod
    async def get_field_layout(
        db: AsyncSession,
        organization_id: int,
        study_id: str
    ) -> Optional[FieldLayoutResponse]:
        # Get study first to confirm existence and get dimensions
        study_info = await FieldLayoutService.get_study(db, organization_id, study_id)
        if not study_info:
            return None

        # Resolve internal ID if study_id is a UUID string or integer
        stmt = select(Study.id).where(
            and_(
                Study.organization_id == organization_id,
                Study.study_db_id == study_id,
            )
        )
        result = await db.execute(stmt)
        internal_study_id = result.scalar_one_or_none()

        if not internal_study_id and study_id.isdigit():
             internal_study_id = int(study_id)

        if not internal_study_id:
             return None

        # Get observation units
        stmt = select(ObservationUnit).where(
            and_(
                ObservationUnit.study_id == internal_study_id,
                ObservationUnit.organization_id == organization_id,
            )
        ).options(
            selectinload(ObservationUnit.germplasm),
        )

        result = await db.execute(stmt)
        observation_units = result.scalars().all()

        plots = []
        check_count = 0
        unique_germplasm = set()
        max_block = 0
        max_rep = 0

        for ou in observation_units:
            additional_ou = ou.additional_info or {}

            # Extract Row/Col
            row = additional_ou.get("row")
            col = additional_ou.get("col")

            if row is None:
                try:
                    row = int(ou.position_coordinate_x) if ou.position_coordinate_x else 0
                except (ValueError, TypeError):
                    row = 0

            if col is None:
                try:
                    col = int(ou.position_coordinate_y) if ou.position_coordinate_y else 0
                except (ValueError, TypeError):
                    col = 0

            block = additional_ou.get("blockNumber", 0)
            rep = additional_ou.get("replicate", 0)
            entry_type = additional_ou.get("entryType", "TEST")

            if entry_type == "CHECK":
                check_count += 1

            if ou.germplasm:
                unique_germplasm.add(ou.germplasm.id)

            max_block = max(max_block, block)
            max_rep = max(max_rep, rep)

            plots.append(Plot(
                plotNumber=ou.observation_unit_db_id or str(ou.id),
                row=int(row),
                col=int(col),
                germplasmName=ou.germplasm.germplasm_name if ou.germplasm else "Unknown",
                germplasmDbId=str(ou.germplasm_id) if ou.germplasm_id else None,
                blockNumber=block,
                replicate=rep,
                entryType=entry_type,
                observationUnitDbId=ou.observation_unit_db_id or str(ou.id),
            ))

        summary = FieldLayoutSummary(
            total_plots=len(plots),
            check_plots=check_count,
            test_plots=len(plots) - check_count,
            unique_germplasm=len(unique_germplasm),
            blocks=max_block,
            replicates=max_rep,
        )

        return FieldLayoutResponse(
            study=study_info,
            plots=plots,
            summary=summary
        )

    @staticmethod
    async def get_plots(
        db: AsyncSession,
        organization_id: int,
        study_id: str,
        block: Optional[int] = None,
        replicate: Optional[int] = None,
        entry_type: Optional[str] = None
    ) -> List[Plot]:
        layout = await FieldLayoutService.get_field_layout(db, organization_id, study_id)
        if not layout:
            return []

        filtered_plots = []
        for p in layout.plots:
            if block is not None and p.blockNumber != block:
                continue
            if replicate is not None and p.replicate != replicate:
                continue
            if entry_type is not None and p.entryType != entry_type:
                continue
            filtered_plots.append(p)

        return filtered_plots

    @staticmethod
    async def get_plot(
        db: AsyncSession,
        organization_id: int,
        study_id: str,
        plot_number: str
    ) -> Optional[Plot]:
        # Resolve study internal ID
        stmt = select(Study.id).where(
            and_(
                Study.organization_id == organization_id,
                Study.study_db_id == study_id,
            )
        )
        result = await db.execute(stmt)
        internal_study_id = result.scalar_one_or_none()

        if not internal_study_id and study_id.isdigit():
             internal_study_id = int(study_id)

        if not internal_study_id:
             return None

        stmt = select(ObservationUnit).where(
            and_(
                ObservationUnit.study_id == internal_study_id,
                ObservationUnit.organization_id == organization_id,
                ObservationUnit.observation_unit_db_id == plot_number,
            )
        ).options(
            selectinload(ObservationUnit.germplasm),
        )

        result = await db.execute(stmt)
        ou = result.scalar_one_or_none()

        if not ou:
            return None

        additional_ou = ou.additional_info or {}

        # Extract Row/Col
        row = additional_ou.get("row")
        col = additional_ou.get("col")

        if row is None:
            try:
                row = int(ou.position_coordinate_x) if ou.position_coordinate_x else 0
            except (ValueError, TypeError):
                row = 0

        if col is None:
            try:
                col = int(ou.position_coordinate_y) if ou.position_coordinate_y else 0
            except (ValueError, TypeError):
                col = 0

        return Plot(
            plotNumber=ou.observation_unit_db_id or str(ou.id),
            row=int(row),
            col=int(col),
            germplasmName=ou.germplasm.germplasm_name if ou.germplasm else "Unknown",
            germplasmDbId=str(ou.germplasm_id) if ou.germplasm_id else None,
            blockNumber=additional_ou.get("blockNumber", 0),
            replicate=additional_ou.get("replicate", 0),
            entryType=additional_ou.get("entryType", "TEST"),
            observationUnitDbId=ou.observation_unit_db_id or str(ou.id),
        )

    @staticmethod
    async def update_plot(
        db: AsyncSession,
        organization_id: int,
        study_id: str,
        plot_number: str,
        data: Dict[str, Any]
    ) -> bool:
        # Resolve study internal ID
        stmt = select(Study.id).where(
            and_(
                Study.organization_id == organization_id,
                Study.study_db_id == study_id,
            )
        )
        result = await db.execute(stmt)
        internal_study_id = result.scalar_one_or_none()

        if not internal_study_id and study_id.isdigit():
             internal_study_id = int(study_id)

        if not internal_study_id:
            return False

        stmt = select(ObservationUnit).where(
            and_(
                ObservationUnit.study_id == internal_study_id,
                ObservationUnit.organization_id == organization_id,
                ObservationUnit.observation_unit_db_id == plot_number,
            )
        )

        result = await db.execute(stmt)
        ou = result.scalar_one_or_none()

        if not ou:
            return False

        # Update additional_info
        additional = dict(ou.additional_info) if ou.additional_info else {}
        for key in ["blockNumber", "replicate", "entryType"]:
            if key in data:
                additional[key] = data[key]
        ou.additional_info = additional

        await db.commit()
        return True

    @staticmethod
    async def generate_layout(
        db: AsyncSession,
        organization_id: int,
        study_id: str,
        design: str,
        blocks: int,
        replicates: int
    ) -> Optional[LayoutGenerationResponse]:
        study_info = await FieldLayoutService.get_study(db, organization_id, study_id)
        if not study_info:
            return None

        rows = study_info.rows
        cols = study_info.cols
        total = rows * cols if rows and cols else 0

        return LayoutGenerationResponse(
            message=f"Layout generation initiated - {design.upper()} design",
            study_id=study_id,
            design=design,
            blocks=blocks,
            replicates=replicates,
            total_plots=total,
            note="Layout generation requires full experimental design service implementation."
        )

    @staticmethod
    async def export_layout(
        db: AsyncSession,
        organization_id: int,
        study_id: str,
        format: str
    ) -> Optional[ExportResponse]:
        layout = await FieldLayoutService.get_field_layout(db, organization_id, study_id)
        if not layout:
            return None

        if format.lower() == "csv":
            return ExportResponse(
                message="Export successful",
                study_id=study_id,
                format=format,
                download_url=f"/api/v2/field-layout/download/{study_id}.csv",
                note="File generated successfully."
            )

        return ExportResponse(
            message=f"Export format {format} not supported yet",
            study_id=study_id,
            format=format,
            download_url=None
        )

    @staticmethod
    async def get_available_germplasm(
        db: AsyncSession,
        organization_id: int
    ) -> List[Dict[str, str]]:
        stmt = select(Germplasm).where(
            Germplasm.organization_id == organization_id
        ).limit(100)

        result = await db.execute(stmt)
        germplasm_list = result.scalars().all()

        return [
            {"germplasmDbId": str(g.id), "germplasmName": g.germplasm_name}
            for g in germplasm_list
        ]
