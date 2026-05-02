"""
BrAPI Genotyping Service
Manages variant sets, calls, call sets, references, and marker positions
Database-backed implementation using SQLAlchemy and AsyncSession
"""
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core import Study
from app.models.genotyping import (
    Call,
    CallSet,
    MarkerPosition,
    Reference,
    ReferenceSet,
    Variant,
    VariantSet,
    VendorOrder,
)
from app.schemas.genotyping import VariantCreate, VariantSetCreate, VariantSetUpdate, VariantUpdate


class GenotypingService:
    """Service for BrAPI genotyping operations"""

    # --- Variant Sets ---

    async def list_variant_sets(
        self,
        db: AsyncSession,
        variant_set_db_id: str | None = None,
        study_db_id: str | None = None,
        reference_set_db_id: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> tuple[list[VariantSet], int]:
        """List variant sets with optional filters"""
        query = select(VariantSet).options(
            selectinload(VariantSet.study),
            selectinload(VariantSet.reference_set)
        )

        if variant_set_db_id:
            query = query.where(VariantSet.variant_set_db_id == variant_set_db_id)
        if study_db_id:
            query = query.join(Study).where(Study.study_db_id == study_db_id)
        if reference_set_db_id:
            query = query.join(ReferenceSet).where(ReferenceSet.reference_set_db_id == reference_set_db_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    async def get_variant_set(self, db: AsyncSession, variant_set_db_id: str) -> VariantSet | None:
        """Get a single variant set"""
        query = select(VariantSet).options(
            selectinload(VariantSet.reference_set),
            selectinload(VariantSet.study)
        ).where(VariantSet.variant_set_db_id == variant_set_db_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_variant_set(self, db: AsyncSession, data: VariantSetCreate | dict, organization_id: int) -> VariantSet:
        """Create a new variant set"""
        # Determine values from data
        if isinstance(data, dict):
             variant_set_name = data.get("variantSetName")
             study_db_id = data.get("studyDbId")
             reference_set_db_id = data.get("referenceSetDbId")
             analysis = data.get("analysis")
             available_formats = data.get("availableFormats")
             additional_info = data.get("additionalInfo")
             # Handle extra fields from dict implementation
             variant_count = data.get("variantCount", 0)
             call_set_count = data.get("callSetCount", 0)
        else:
             # Pydantic model
             variant_set_name = data.variantSetName
             study_db_id = data.studyDbId
             reference_set_db_id = data.referenceSetDbId
             analysis = data.analysis
             available_formats = data.availableFormats
             additional_info = data.additionalInfo
             # Model might not have these, default to 0
             variant_count = 0
             call_set_count = 0

        # Resolve Study and ReferenceSet if provided
        study_id = None
        reference_set_id = None

        if study_db_id:
            study_result = await db.execute(select(Study).where(Study.study_db_id == study_db_id))
            study = study_result.scalar_one_or_none()
            if study:
                study_id = study.id

        if reference_set_db_id:
            ref_set_result = await db.execute(select(ReferenceSet).where(ReferenceSet.reference_set_db_id == reference_set_db_id))
            ref_set = ref_set_result.scalar_one_or_none()
            if ref_set:
                reference_set_id = ref_set.id

        # Generate DB ID if not exists (usually system generated)
        # Check if dict has it (legacy behavior)
        if isinstance(data, dict) and data.get("variantSetDbId"):
             variant_set_db_id = data.get("variantSetDbId")
        else:
             variant_set_db_id = str(uuid.uuid4())

        db_obj = VariantSet(
            variant_set_db_id=variant_set_db_id,
            variant_set_name=variant_set_name,
            study_id=study_id,
            reference_set_id=reference_set_id,
            analysis=analysis,
            available_formats=available_formats,
            additional_info=additional_info,
            variant_count=variant_count,
            call_set_count=call_set_count,
            organization_id=organization_id
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_variant_set(self, db: AsyncSession, variant_set_db_id: str, data: VariantSetUpdate) -> VariantSet | None:
        """Update a variant set"""
        variant_set = await self.get_variant_set(db, variant_set_db_id)
        if not variant_set:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle relationships
        if "studyDbId" in update_data:
            study_db_id = update_data.pop("studyDbId")
            if study_db_id:
                study = (await db.execute(select(Study).where(Study.study_db_id == study_db_id))).scalar_one_or_none()
                if study:
                    variant_set.study_id = study.id
            else:
                variant_set.study_id = None

        if "referenceSetDbId" in update_data:
            ref_set_db_id = update_data.pop("referenceSetDbId")
            if ref_set_db_id:
                ref_set = (await db.execute(select(ReferenceSet).where(ReferenceSet.reference_set_db_id == ref_set_db_id))).scalar_one_or_none()
                if ref_set:
                    variant_set.reference_set_id = ref_set.id
            else:
                variant_set.reference_set_id = None

        # Map camelCase to snake_case
        if "variantSetName" in update_data:
            variant_set.variant_set_name = update_data.pop("variantSetName")
        if "availableFormats" in update_data:
            variant_set.available_formats = update_data.pop("availableFormats")
        if "additionalInfo" in update_data:
            variant_set.additional_info = update_data.pop("additionalInfo")

        # Apply other updates
        for field, value in update_data.items():
            if hasattr(variant_set, field):
                setattr(variant_set, field, value)

        await db.commit()
        await db.refresh(variant_set)
        return variant_set

    async def delete_variant_set(self, db: AsyncSession, variant_set_db_id: str) -> bool:
        """Delete a variant set"""
        variant_set = await self.get_variant_set(db, variant_set_db_id)
        if not variant_set:
            return False

        await db.delete(variant_set)
        await db.commit()
        return True

    # --- Variants ---

    async def list_variants(
        self,
        db: AsyncSession,
        variant_db_id: str | None = None,
        variant_set_db_id: str | None = None,
        reference_db_id: str | None = None,
        reference_name: str | None = None,
        start: int | None = None,
        end: int | None = None,
        variant_type: str | None = None,
        page: int = 0,
        page_size: int = 1000,
    ) -> tuple[list[Variant], int]:
        """List variants with optional filters"""
        query = select(Variant).options(
            selectinload(Variant.variant_set),
            selectinload(Variant.reference)
        )

        if variant_db_id:
            query = query.where(Variant.variant_db_id == variant_db_id)
        if variant_set_db_id:
            query = query.join(VariantSet).where(VariantSet.variant_set_db_id == variant_set_db_id)
        if reference_db_id:
            query = query.join(Reference).where(Reference.reference_db_id == reference_db_id)
        if reference_name:
            query = query.join(Reference).where(Reference.reference_name == reference_name)
        if variant_type:
            query = query.where(Variant.variant_type == variant_type)
        if start is not None:
            query = query.where(Variant.start >= start)
        if end is not None:
            query = query.where(Variant.end <= end)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Pagination
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    async def get_variant(self, db: AsyncSession, variant_db_id: str) -> Variant | None:
        """Get a single variant"""
        query = select(Variant).options(
            selectinload(Variant.variant_set),
            selectinload(Variant.reference)
        ).where(Variant.variant_db_id == variant_db_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_variant(self, db: AsyncSession, data: VariantCreate, organization_id: int) -> Variant:
        """Create a new variant"""
        # Resolve relationships
        variant_set_id = None
        reference_id = None

        if data.variantSetDbId:
            vs_result = await db.execute(select(VariantSet).where(VariantSet.variant_set_db_id == data.variantSetDbId))
            vs = vs_result.scalar_one_or_none()
            if vs:
                variant_set_id = vs.id
            else:
                pass

        if data.referenceDbId:
            ref_result = await db.execute(select(Reference).where(Reference.reference_db_id == data.referenceDbId))
            ref = ref_result.scalar_one_or_none()
            if ref:
                reference_id = ref.id

        variant_db_id = str(uuid.uuid4())

        db_obj = Variant(
            variant_db_id=variant_db_id,
            variant_name=data.variantName,
            variant_type=data.variantType,
            reference_bases=data.referenceBases,
            alternate_bases=data.alternateBases,
            start=data.start,
            end=data.end,
            cipos=data.cipos,
            ciend=data.ciend,
            svlen=data.svlen,
            filters_applied=data.filtersApplied,
            filters_passed=data.filtersPassed,
            additional_info=data.additionalInfo,
            variant_set_id=variant_set_id,
            reference_id=reference_id,
            organization_id=organization_id
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # Reload relationships for response
        query = select(Variant).options(
            selectinload(Variant.variant_set),
            selectinload(Variant.reference)
        ).where(Variant.id == db_obj.id)
        result = await db.execute(query)
        return result.scalar_one()

    async def update_variant(self, db: AsyncSession, variant_db_id: str, data: VariantUpdate) -> Variant | None:
        """Update a variant"""
        variant = await self.get_variant(db, variant_db_id)
        if not variant:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Map camelCase
        mapping = {
            "variantName": "variant_name",
            "variantType": "variant_type",
            "referenceBases": "reference_bases",
            "alternateBases": "alternate_bases",
            "filtersApplied": "filters_applied",
            "filtersPassed": "filters_passed",
            "additionalInfo": "additional_info"
        }

        for key, value in update_data.items():
            if key in mapping:
                setattr(variant, mapping[key], value)
            elif hasattr(variant, key):
                setattr(variant, key, value)

        # Handle FKs if updated
        if "variantSetDbId" in update_data:
            vs_db_id = update_data["variantSetDbId"]
            if vs_db_id:
                vs = (await db.execute(select(VariantSet).where(VariantSet.variant_set_db_id == vs_db_id))).scalar_one_or_none()
                if vs:
                    variant.variant_set_id = vs.id

        if "referenceDbId" in update_data:
            ref_db_id = update_data["referenceDbId"]
            if ref_db_id:
                ref = (await db.execute(select(Reference).where(Reference.reference_db_id == ref_db_id))).scalar_one_or_none()
                if ref:
                    variant.reference_id = ref.id

        await db.commit()
        await db.refresh(variant)
        return variant

    # --- Call Sets ---

    async def list_call_sets(
        self,
        db: AsyncSession,
        call_set_db_id: str | None = None,
        call_set_name: str | None = None,
        sample_db_id: str | None = None,
        variant_set_db_id: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> tuple[list[CallSet], int]:
        """List call sets with optional filters"""
        query = select(CallSet).options(selectinload(CallSet.variant_sets))

        if call_set_db_id:
            query = query.where(CallSet.call_set_db_id == call_set_db_id)
        if call_set_name:
            query = query.where(CallSet.call_set_name.ilike(f"%{call_set_name}%"))
        if sample_db_id:
            query = query.where(CallSet.sample_db_id == sample_db_id)
        if variant_set_db_id:
            query = query.join(CallSet.variant_sets).where(VariantSet.variant_set_db_id == variant_set_db_id)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    async def get_call_set(self, db: AsyncSession, call_set_db_id: str) -> CallSet | None:
        """Get a single call set by ID"""
        query = select(CallSet).where(CallSet.call_set_db_id == call_set_db_id).options(selectinload(CallSet.variant_sets))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    # --- Calls ---

    async def list_calls(
        self,
        db: AsyncSession,
        call_set_db_id: str | None = None,
        variant_db_id: str | None = None,
        variant_set_db_id: str | None = None,
        organization_id: int | None = None,
        page: int = 0,
        page_size: int = 1000,
    ) -> tuple[list[Call], int]:
        """List genotype calls with optional filters"""
        query = select(Call).options(
            selectinload(Call.call_set),
            selectinload(Call.variant)
        )

        if organization_id:
            query = query.where(Call.organization_id == organization_id)

        if call_set_db_id:
            query = query.join(Call.call_set).where(CallSet.call_set_db_id == call_set_db_id)
        if variant_db_id:
            query = query.join(Call.variant).where(Variant.variant_db_id == variant_db_id)
        if variant_set_db_id:
            query = query.join(Call.variant).join(Variant.variant_set).where(VariantSet.variant_set_db_id == variant_set_db_id)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Pagination
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    def _call_to_dict(self, item: Call) -> dict:
        return {
            "callSetDbId": item.call_set.call_set_db_id if item.call_set else None,
            "callSetName": item.call_set.call_set_name if item.call_set else None,
            "variantDbId": item.variant.variant_db_id if item.variant else None,
            "variantName": item.variant.variant_name if item.variant else None,
            "genotype": item.genotype,
            "genotypeValue": item.genotype_value,
            "genotypeLikelihood": item.genotype_likelihood,
            "phaseSet": item.phaseSet,
            "additionalInfo": item.additional_info
        }

    async def update_calls(self, db: AsyncSession, calls: list[dict]) -> list[dict]:
        """Update multiple calls"""
        updated = []

        for call_data in calls:
            call_set_db_id = call_data.get("callSetDbId")
            variant_db_id = call_data.get("variantDbId")

            if not call_set_db_id or not variant_db_id:
                continue

            # Find the call
            query = select(Call).join(CallSet).join(Variant, Call.variant_id == Variant.id).where(
                CallSet.call_set_db_id == call_set_db_id,
                Variant.variant_db_id == variant_db_id
            ).options(
                selectinload(Call.call_set),
                selectinload(Call.variant)
            )

            result = await db.execute(query)
            call = result.scalar_one_or_none()

            if call:
                # Update fields
                if "genotype" in call_data:
                    call.genotype = call_data["genotype"]
                if "genotypeValue" in call_data:
                    call.genotype_value = call_data["genotypeValue"]
                elif "genotype_value" in call_data:
                    call.genotype_value = call_data["genotype_value"]

                if "genotypeLikelihood" in call_data:
                    call.genotype_likelihood = call_data["genotypeLikelihood"]
                if "phaseSet" in call_data:
                    call.phaseSet = call_data["phaseSet"]
                if "additionalInfo" in call_data:
                    call.additional_info = call_data["additionalInfo"]

                updated.append(self._call_to_dict(call))

        await db.commit()
        return updated

    async def get_calls_statistics(self, db: AsyncSession, variant_set_db_id: str | None = None) -> dict:
        """Get statistics for genotype calls"""
        query = select(Call)
        if variant_set_db_id:
            query = query.join(Variant).join(VariantSet).where(VariantSet.variant_set_db_id == variant_set_db_id)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        if total == 0:
            return {"total": 0, "heterozygous": 0, "homozygousRef": 0, "homozygousAlt": 0, "missing": 0, "avgQuality": 0}

        # Example aggregation: Count by genotype_value
        agg_query = select(Call.genotype_value, func.count(Call.id)).group_by(Call.genotype_value)
        if variant_set_db_id:
             agg_query = agg_query.join(Variant).join(VariantSet).where(VariantSet.variant_set_db_id == variant_set_db_id)

        agg_result = await db.execute(agg_query)
        counts = dict(agg_result.all())

        het = counts.get("0/1", 0) + counts.get("1/0", 0)
        hom_ref = counts.get("0/0", 0)
        hom_alt = counts.get("1/1", 0)
        missing = counts.get("./.", 0) + counts.get(".", 0)

        return {
            "total": total,
            "heterozygous": het,
            "homozygousRef": hom_ref,
            "homozygousAlt": hom_alt,
            "missing": missing,
            "avgQuality": 0, # Placeholder
            "heterozygosityRate": round(het / total * 100, 2) if total > 0 else 0,
            "missingRate": round(missing / total * 100, 2) if total > 0 else 0,
        }

    # --- References ---

    async def list_references(
        self,
        db: AsyncSession,
        reference_db_id: str | None = None,
        reference_set_db_id: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> tuple[list[Reference], int]:
        """List references (chromosomes)"""
        query = select(Reference)

        if reference_db_id:
            query = query.where(Reference.reference_db_id == reference_db_id)
        if reference_set_db_id:
            query = query.join(ReferenceSet).where(ReferenceSet.reference_set_db_id == reference_set_db_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.offset(page * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    async def get_reference(self, db: AsyncSession, reference_db_id: str) -> Reference | None:
        """Get a single reference by ID"""
        query = select(Reference).where(Reference.reference_db_id == reference_db_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    # --- Reference Sets ---

    async def list_reference_sets(
        self,
        db: AsyncSession,
        reference_set_db_id: str | None = None,
        page: int = 0,
        page_size: int = 20,
    ) -> tuple[list[ReferenceSet], int]:
        """List reference sets (genomes)"""
        query = select(ReferenceSet)
        if reference_set_db_id:
            query = query.where(ReferenceSet.reference_set_db_id == reference_set_db_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.offset(page * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    # --- Marker Positions ---

    async def list_marker_positions(
        self,
        db: AsyncSession,
        map_db_id: str | None = None,
        linkage_group_name: str | None = None,
        min_position: float | None = None,
        max_position: float | None = None,
        page: int = 0,
        page_size: int = 100,
    ) -> tuple[list[MarkerPosition], int]:
        """List marker positions on linkage maps"""
        query = select(MarkerPosition)
        if map_db_id:
            query = query.where(MarkerPosition.map_id == map_db_id) # Should check if map_id matches
        if linkage_group_name:
            query = query.where(MarkerPosition.linkage_group_name == linkage_group_name)
        if min_position is not None:
            query = query.where(MarkerPosition.position >= min_position)
        if max_position is not None:
            query = query.where(MarkerPosition.position <= max_position)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.offset(page * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    # --- Vendor Orders ---

    async def list_vendor_orders(
        self,
        db: AsyncSession,
        vendor_order_db_id: str | None = None,
        status: str | None = None,
        page: int = 0,
        page_size: int = 20
    ) -> tuple[list[VendorOrder], int]:
        """List vendor orders"""
        query = select(VendorOrder)

        if vendor_order_db_id:
            query = query.where(VendorOrder.order_db_id == vendor_order_db_id)
        if status:
            query = query.where(VendorOrder.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.offset(page * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    async def get_vendor_order(self, db: AsyncSession, vendor_order_db_id: str) -> VendorOrder | None:
        """Get a single vendor order"""
        query = select(VendorOrder).where(VendorOrder.order_db_id == vendor_order_db_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_vendor_order(self, db: AsyncSession, data: dict, organization_id: int) -> VendorOrder:
        """Create a vendor order"""
        db_id = str(uuid.uuid4())
        # Generate a readable order ID if not provided (e.g. VO-123456)
        order_id = data.get("orderId") or f"VO-{db_id[:8]}"

        order = VendorOrder(
            order_db_id=db_id,
            client_id=data.get("clientId"),
            number_of_samples=data.get("numberOfSamples"),
            service_ids=data.get("serviceIds"),
            required_service_info=data.get("requiredServiceInfo"),
            order_id=order_id,
            status="submitted",
            status_time_stamp=datetime.now().isoformat(),
            organization_id=organization_id
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        return order

    async def update_vendor_order_status(self, db: AsyncSession, vendor_order_db_id: str, status: str) -> VendorOrder | None:
        """Update status"""
        query = select(VendorOrder).where(VendorOrder.order_db_id == vendor_order_db_id)
        result = await db.execute(query)
        order = result.scalar_one_or_none()

        if order:
            order.status = status
            order.status_time_stamp = datetime.now().isoformat()
            await db.commit()
            return order
        return None


# Singleton instance
genotyping_service = GenotypingService()
