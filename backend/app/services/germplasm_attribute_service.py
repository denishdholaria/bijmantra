from typing import List, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct, delete
from fastapi import HTTPException
import uuid

from app.models.brapi_phenotyping import GermplasmAttributeDefinition
from app.schemas.germplasm_attribute import GermplasmAttributeDefinitionNewRequest, GermplasmAttributeDefinition as GermplasmAttributeSchema

class GermplasmAttributeService:
    @staticmethod
    async def get_attributes(
        db: AsyncSession,
        page: int = 0,
        page_size: int = 1000,
        attribute_category: Optional[str] = None,
        attribute_db_id: Optional[str] = None,
        attribute_name: Optional[str] = None,
        common_crop_name: Optional[str] = None,
        trait_db_id: Optional[str] = None,
        method_db_id: Optional[str] = None,
        scale_db_id: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> Sequence[GermplasmAttributeDefinition]:
        query = select(GermplasmAttributeDefinition)

        if organization_id:
            query = query.where(GermplasmAttributeDefinition.organization_id == organization_id)

        if attribute_category:
            query = query.where(GermplasmAttributeDefinition.attribute_category == attribute_category)
        if attribute_db_id:
            query = query.where(GermplasmAttributeDefinition.attribute_db_id == attribute_db_id)
        if attribute_name:
            query = query.where(GermplasmAttributeDefinition.attribute_name.ilike(f"%{attribute_name}%"))
        if common_crop_name:
            query = query.where(GermplasmAttributeDefinition.common_crop_name == common_crop_name)
        if trait_db_id:
            query = query.where(GermplasmAttributeDefinition.trait_db_id == trait_db_id)
        if method_db_id:
            query = query.where(GermplasmAttributeDefinition.method_db_id == method_db_id)
        if scale_db_id:
            query = query.where(GermplasmAttributeDefinition.scale_db_id == scale_db_id)

        # Add offset and limit
        query = query.offset(page * page_size).limit(page_size)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_total_count(
        db: AsyncSession,
        attribute_category: Optional[str] = None,
        attribute_db_id: Optional[str] = None,
        attribute_name: Optional[str] = None,
        common_crop_name: Optional[str] = None,
        trait_db_id: Optional[str] = None,
        method_db_id: Optional[str] = None,
        scale_db_id: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> int:
        # Note: This is a simplified count. Ideally use count(*) query.
        # For simplicity reusing the filter logic but without pagination
        query = select(GermplasmAttributeDefinition)

        if organization_id:
            query = query.where(GermplasmAttributeDefinition.organization_id == organization_id)

        if attribute_category:
            query = query.where(GermplasmAttributeDefinition.attribute_category == attribute_category)
        if attribute_db_id:
            query = query.where(GermplasmAttributeDefinition.attribute_db_id == attribute_db_id)
        if attribute_name:
            query = query.where(GermplasmAttributeDefinition.attribute_name.ilike(f"%{attribute_name}%"))
        if common_crop_name:
            query = query.where(GermplasmAttributeDefinition.common_crop_name == common_crop_name)
        if trait_db_id:
            query = query.where(GermplasmAttributeDefinition.trait_db_id == trait_db_id)
        if method_db_id:
            query = query.where(GermplasmAttributeDefinition.method_db_id == method_db_id)
        if scale_db_id:
            query = query.where(GermplasmAttributeDefinition.scale_db_id == scale_db_id)

        result = await db.execute(query)
        return len(result.scalars().all())

    @staticmethod
    async def get_attribute_categories(
        db: AsyncSession,
        page: int = 0,
        page_size: int = 1000,
        organization_id: Optional[int] = None
    ) -> List[str]:
        query = select(distinct(GermplasmAttributeDefinition.attribute_category)).where(
            GermplasmAttributeDefinition.attribute_category.isnot(None)
        )
        if organization_id:
            query = query.where(GermplasmAttributeDefinition.organization_id == organization_id)

        result = await db.execute(query)
        categories = [row[0] for row in result.fetchall()]

        # If no categories in DB, return standard list
        if not categories:
            categories = [
                "Morphological", "Phenological", "Agronomic",
                "Biotic Stress", "Abiotic Stress", "Quality",
                "Biochemical", "Molecular", "Physiological",
                "Root", "Seed", "Grain", "Panicle", "Leaf", "Stem"
            ]

        start = page * page_size
        end = start + page_size
        return categories[start:end]

    @staticmethod
    async def get_attribute(
        db: AsyncSession,
        attribute_db_id: str,
        organization_id: Optional[int] = None
    ) -> Optional[GermplasmAttributeDefinition]:
        query = select(GermplasmAttributeDefinition).where(
            GermplasmAttributeDefinition.attribute_db_id == attribute_db_id
        )
        if organization_id:
            query = query.where(GermplasmAttributeDefinition.organization_id == organization_id)

        result = await db.execute(query)
        attr = result.scalar_one_or_none()

        if not attr:
            # Fallback for ID lookup
            try:
                attr_id = int(attribute_db_id)
                query = select(GermplasmAttributeDefinition).where(
                    GermplasmAttributeDefinition.id == attr_id
                )
                if organization_id:
                    query = query.where(GermplasmAttributeDefinition.organization_id == organization_id)
                result = await db.execute(query)
                attr = result.scalar_one_or_none()
            except ValueError:
                pass

        return attr

    @staticmethod
    async def create_attributes(
        db: AsyncSession,
        attributes: List[GermplasmAttributeDefinitionNewRequest],
        organization_id: int
    ) -> List[GermplasmAttributeDefinition]:
        created = []
        for attr_in in attributes:
            # Convert Pydantic model to dict
            attr_data = attr_in.model_dump(exclude_unset=True)

            # Handle additional info and external references specifically if needed
            # but model_dump should handle it if schemas match

            # Generate ID if not provided
            if not attr_data.get("attributeDbId"):
                attr_data["attributeDbId"] = f"attr-{uuid.uuid4().hex[:8]}"

            # Map camelCase to snake_case for SQLAlchemy model
            # Note: We can iterate and convert keys or instantiate directly if keys match.
            # Since model uses snake_case, we need to convert.

            db_obj = GermplasmAttributeDefinition(
                organization_id=organization_id,
                attribute_db_id=attr_data.get("attributeDbId"),
                attribute_name=attr_data.get("attributeName"),
                attribute_pui=attr_data.get("attributePUI"),
                attribute_description=attr_data.get("attributeDescription"),
                attribute_category=attr_data.get("attributeCategory"),
                common_crop_name=attr_data.get("commonCropName"),
                context_of_use=attr_data.get("contextOfUse"),
                default_value=attr_data.get("defaultValue"),
                documentation_url=attr_data.get("documentationURL"),
                growth_stage=attr_data.get("growthStage"),
                institution=attr_data.get("institution"),
                language=attr_data.get("language", "en"),
                scientist=attr_data.get("scientist"),
                status=attr_data.get("status", "active"),
                submission_timestamp=attr_data.get("submissionTimestamp"),
                synonyms=attr_data.get("synonyms"),
                trait_db_id=attr_data.get("traitDbId"),
                trait_name=attr_data.get("traitName"),
                trait_description=attr_data.get("traitDescription"),
                trait_class=attr_data.get("traitClass"),
                method_db_id=attr_data.get("methodDbId"),
                method_name=attr_data.get("methodName"),
                method_description=attr_data.get("methodDescription"),
                method_class=attr_data.get("methodClass"),
                scale_db_id=attr_data.get("scaleDbId"),
                scale_name=attr_data.get("scaleName"),
                data_type=attr_data.get("dataType", "Text"),
                additional_info=attr_data.get("additionalInfo", {}),
                external_references=[er.model_dump() for er in attr_data.get("externalReferences", [])] if attr_data.get("externalReferences") else []
            )
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            created.append(db_obj)

        await db.commit()
        return created

    @staticmethod
    async def update_attribute(
        db: AsyncSession,
        attribute_db_id: str,
        attr_in: GermplasmAttributeDefinitionNewRequest,
        organization_id: Optional[int] = None
    ) -> Optional[GermplasmAttributeDefinition]:
        attr = await GermplasmAttributeService.get_attribute(db, attribute_db_id, organization_id)
        if not attr:
            return None

        attr_data = attr_in.model_dump(exclude_unset=True)

        # Mapping dict
        field_map = {
            "attributeName": "attribute_name",
            "attributePUI": "attribute_pui",
            "attributeDescription": "attribute_description",
            "attributeCategory": "attribute_category",
            "commonCropName": "common_crop_name",
            "contextOfUse": "context_of_use",
            "defaultValue": "default_value",
            "documentationURL": "documentation_url",
            "growthStage": "growth_stage",
            "institution": "institution",
            "language": "language",
            "scientist": "scientist",
            "status": "status",
            "submissionTimestamp": "submission_timestamp",
            "synonyms": "synonyms",
            "traitDbId": "trait_db_id",
            "traitName": "trait_name",
            "traitDescription": "trait_description",
            "traitClass": "trait_class",
            "methodDbId": "method_db_id",
            "methodName": "method_name",
            "methodDescription": "method_description",
            "methodClass": "method_class",
            "scaleDbId": "scale_db_id",
            "scaleName": "scale_name",
            "dataType": "data_type",
            "additionalInfo": "additional_info"
        }

        for key, value in attr_data.items():
            if key in field_map:
                setattr(attr, field_map[key], value)
            if key == "externalReferences" and value is not None:
                attr.external_references = [er.model_dump() for er in value]

        await db.commit()
        await db.refresh(attr)
        return attr

    @staticmethod
    async def delete_attribute(
        db: AsyncSession,
        attribute_db_id: str,
        organization_id: Optional[int] = None
    ) -> bool:
        attr = await GermplasmAttributeService.get_attribute(db, attribute_db_id, organization_id)
        if not attr:
            return False

        await db.delete(attr)
        await db.commit()
        return True
