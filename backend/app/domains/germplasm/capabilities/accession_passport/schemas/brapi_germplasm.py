"""BrAPI germplasm request/response DTOs owned by Accession Passport."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domains.germplasm.capabilities.accession_passport.ports import (
    BrAPIGermplasmMCPDRecord,
    BrAPIGermplasmMutationData,
    BrAPIGermplasmPedigreeRecord,
    BrAPIGermplasmPedigreeRelation,
    BrAPIGermplasmProgenyResult,
    BrAPIGermplasmRecord,
)


class GermplasmBase(BaseModel):
    germplasmName: str
    accessionNumber: str | None = None
    germplasmPUI: str | None = None
    defaultDisplayName: str | None = None
    species: str | None = None
    genus: str | None = None
    subtaxa: str | None = None
    commonCropName: str | None = None
    instituteCode: str | None = None
    instituteName: str | None = None
    biologicalStatusOfAccessionCode: str | None = None
    countryOfOriginCode: str | None = None
    synonyms: list[str] | None = []
    pedigree: str | None = None
    seedSource: str | None = None
    seedSourceDescription: str | None = None


class GermplasmCreate(GermplasmBase):
    pass


class Germplasm(GermplasmBase):
    germplasmDbId: str

    model_config = ConfigDict(from_attributes=True)


def brapi_germplasm_record_to_payload(record: BrAPIGermplasmRecord) -> dict[str, Any]:
    """Convert a capability-owned germplasm record to BrAPI response fields."""

    return {
        "germplasmDbId": record.germplasm_db_id,
        "germplasmName": record.germplasm_name,
        "germplasmPUI": record.germplasm_pui,
        "defaultDisplayName": record.default_display_name or record.germplasm_name,
        "accessionNumber": record.accession_number,
        "species": record.species,
        "genus": record.genus,
        "subtaxa": record.subtaxa,
        "commonCropName": record.common_crop_name,
        "instituteCode": record.institute_code,
        "instituteName": record.institute_name,
        "biologicalStatusOfAccessionCode": record.biological_status_of_accession_code,
        "countryOfOriginCode": record.country_of_origin_code,
        "synonyms": list(record.synonyms or ()),
        "pedigree": record.pedigree,
        "seedSource": record.seed_source,
        "seedSourceDescription": record.seed_source_description,
        "additionalInfo": record.additional_info,
        "externalReferences": record.external_references,
    }


def brapi_germplasm_pedigree_to_payload(
    record: BrAPIGermplasmPedigreeRecord,
) -> dict[str, Any]:
    """Convert a capability-owned pedigree record to BrAPI response fields."""

    return {
        "germplasmDbId": record.germplasm_db_id,
        "germplasmName": record.germplasm_name,
        "pedigree": record.pedigree,
        "crossingProjectDbId": record.crossing_project_db_id,
        "crossingYear": record.crossing_year,
        "familyCode": record.family_code,
        "breedingMethodDbId": record.breeding_method_db_id,
        "breedingMethodName": record.breeding_method_name,
        "parents": [
            _brapi_germplasm_relation_to_payload(parent)
            for parent in record.parents
        ],
        "siblings": [
            _brapi_germplasm_relation_to_payload(sibling)
            for sibling in record.siblings
        ],
    }


def brapi_germplasm_progeny_to_payload(
    result: BrAPIGermplasmProgenyResult,
) -> dict[str, Any]:
    """Convert a capability-owned progeny result to BrAPI response fields."""

    return {
        "germplasmDbId": result.germplasm_db_id,
        "germplasmName": result.germplasm_name,
        "progeny": [
            {
                "germplasmDbId": progeny.germplasm_db_id,
                "germplasmName": progeny.germplasm_name,
                "parentType": progeny.parent_type,
            }
            for progeny in result.progeny
        ],
    }


def brapi_germplasm_mcpd_to_payload(record: BrAPIGermplasmMCPDRecord) -> dict[str, Any]:
    """Convert a capability-owned MCPD record to BrAPI response fields."""

    return {
        "germplasmDbId": record.germplasm_db_id,
        "accessionNumber": record.accession_number,
        "accessionNames": list(record.accession_names),
        "acquisitionDate": str(record.acquisition_date) if record.acquisition_date else None,
        "acquisitionSourceCode": record.acquisition_source_code,
        "alternateIDs": list(record.alternate_ids),
        "ancestralData": record.ancestral_data,
        "biologicalStatusOfAccessionCode": record.biological_status_of_accession_code,
        "breedingInstitutes": list(record.breeding_institutes),
        "collectingInfo": {
            "collectingDate": str(record.collecting_date) if record.collecting_date else None,
            "collectingInstitutes": list(record.collecting_institutes),
            "collectingMissionIdentifier": record.collecting_mission_identifier,
            "collectingNumber": record.collecting_number,
            "collectingSite": record.collecting_site,
        },
        "commonCropName": record.common_crop_name,
        "countryOfOrigin": record.country_of_origin,
        "donorInfo": {
            "donorAccessionNumber": record.donor_accession_number,
            "donorAccessionPui": record.donor_accession_pui,
            "donorInstitute": record.donor_institute,
        },
        "genus": record.genus,
        "germplasmPUI": record.germplasm_pui,
        "instituteCode": record.institute_code,
        "mlsStatus": record.mls_status,
        "remarks": record.remarks,
        "safetyDuplicateInstitutes": list(record.safety_duplicate_institutes),
        "species": record.species,
        "speciesAuthority": record.species_authority,
        "storageTypeCodes": list(record.storage_type_codes),
        "subtaxon": record.subtaxon,
        "subtaxonAuthority": record.subtaxon_authority,
    }


def _brapi_germplasm_relation_to_payload(
    relation: BrAPIGermplasmPedigreeRelation,
) -> dict[str, Any]:
    payload = {
        "germplasmDbId": relation.germplasm_db_id,
        "germplasmName": relation.germplasm_name,
    }
    if relation.parent_type is not None:
        payload["parentType"] = relation.parent_type
    return payload


def brapi_germplasm_request_to_mutation_data(
    germplasm: GermplasmBase,
) -> BrAPIGermplasmMutationData:
    """Convert a BrAPI germplasm request DTO into a mutation command payload."""

    return BrAPIGermplasmMutationData(
        germplasm_name=germplasm.germplasmName,
        accession_number=germplasm.accessionNumber,
        germplasm_pui=germplasm.germplasmPUI,
        default_display_name=germplasm.defaultDisplayName,
        species=germplasm.species,
        genus=germplasm.genus,
        subtaxa=germplasm.subtaxa,
        common_crop_name=germplasm.commonCropName,
        institute_code=germplasm.instituteCode,
        institute_name=germplasm.instituteName,
        biological_status_of_accession_code=germplasm.biologicalStatusOfAccessionCode,
        country_of_origin_code=germplasm.countryOfOriginCode,
        synonyms=tuple(germplasm.synonyms) if germplasm.synonyms is not None else None,
        pedigree=germplasm.pedigree,
        seed_source=germplasm.seedSource,
        seed_source_description=germplasm.seedSourceDescription,
    )


def brapi_response(
    data: Any,
    page: int = 0,
    pageSize: int = 20,
    total: int = 0,
    message: str = "Request successful",
) -> dict[str, Any]:
    """Create a standard BrAPI response envelope."""

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0,
            },
            "status": [{"message": message, "messageType": "INFO"}],
        },
        "result": {"data": data} if isinstance(data, list) else data,
    }
