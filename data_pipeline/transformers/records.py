from __future__ import annotations

from typing import Any

from data_pipeline.crop_catalog import CropRecord, crop_intelligence
from data_pipeline.transformers.trait_registry import TraitDef, get_traits_for_crop


TARGET_TRAITS = [
    {
        "trait_name": trait.trait_name,
        "trait_class": trait.trait_class,
        "scale_name": trait.scale_name,
        "data_type": trait.data_type,
        "ontology_db_id": trait.ontology_db_id,
        "method_name": trait.method_name,
        "valid_range": [trait.valid_min, trait.valid_max],
    }
    for trait in get_traits_for_crop("Cereals & Grains")[:5]
]


def transform_crop_to_germplasm(
    crop: CropRecord,
    organization_id: int,
    *,
    gbif_map: dict[str, dict[str, Any]] | None = None,
    brapi_germplasm: list[dict[str, Any]] | None = None,
) -> list[dict[str, object]]:
    intelligence = crop_intelligence(crop)
    gbif_record = (gbif_map or {}).get(_normalize_name(crop.scientific_name))
    taxonomy = intelligence["taxonomy"]
    if gbif_record:
        taxonomy = {
            **taxonomy,
            "kingdom": gbif_record.get("kingdom") or taxonomy["kingdom"],
            "order": gbif_record.get("order") or taxonomy["order"],
            "family": gbif_record.get("family") or taxonomy["family"],
            "genus": gbif_record.get("genus") or taxonomy["genus"],
            "species": gbif_record.get("canonicalName") or gbif_record.get("species") or taxonomy["species"],
        }
        intelligence = {**intelligence, "taxonomy": taxonomy}
    records = []
    for index, variety in enumerate(intelligence["varieties"], start=1):
        accession_number = f"PIPE-{organization_id}-{crop.crop_id.upper()}-{index:03d}"
        records.append(
            {
                "organization_id": organization_id,
                "record_key": f"org{organization_id}:{crop.crop_id}:germplasm:{index}",
                "germplasm_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_{index}",
                "germplasm_name": variety["name"],
                "default_display_name": variety["name"],
                "accession_number": accession_number,
                "common_crop_name": crop.common_name,
                "genus": str(taxonomy.get("genus") or crop.genus),
                "species": str(taxonomy.get("species") or crop.species),
                "country_of_origin_code": "IND" if organization_id == 1 else "XXX",
                "institute_code": "BIJ",
                "institute_name": "BijMantra Pipeline",
                "biological_status_of_accession_code": "500",
                "pedigree": f"{variety['name']} source-attributed pipeline entry",
                "synonyms": [variety["name"], crop.common_name],
                "data_source": "hybrid",
                "synthetic_method": "crop_catalog_variety_template",
                "additional_info": {
                    "pipeline": {
                        "source": "repo_crop_catalog_plus_public_source_registry",
                        "crop_intelligence": intelligence,
                        "variety": variety,
                        "gbif_taxonomy": gbif_record,
                        "taxonomy_data_source": "real" if gbif_record else "curated",
                    }
                },
            }
        )
    records.extend(_transform_brapi_germplasm(crop, organization_id, brapi_germplasm or [], len(records)))
    return records


def transform_traits(
    crops: list[CropRecord],
    organization_id: int,
    *,
    crop_ontology_traits: list[dict[str, Any]] | None = None,
    brapi_variables: list[dict[str, Any]] | None = None,
) -> list[dict[str, object]]:
    records = []
    raw_traits_by_name = _raw_traits_by_name((crop_ontology_traits or []) + (brapi_variables or []))
    for crop in crops:
        for trait in get_traits_for_crop(crop.category):
            trait_name = trait.trait_name
            raw_trait = raw_traits_by_name.get(_normalize_name(trait_name))
            ontology_db_id = trait.ontology_db_id or _raw_ontology_id(raw_trait)
            data_source = "real" if ontology_db_id or raw_trait else "synthetic"
            records.append(
                {
                    "organization_id": organization_id,
                    "record_key": f"org{organization_id}:{crop.crop_id}:trait:{trait_name}",
                    "observation_variable_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_{_slug(trait_name)}",
                    "observation_variable_name": trait_name,
                    "common_crop_name": crop.common_name,
                    "trait_name": trait_name,
                    "trait_description": f"{trait_name} for {crop.common_name}",
                    "trait_class": trait.trait_class,
                    "method_name": _raw_method_name(raw_trait) or trait.method_name,
                    "method_description": trait.method_description,
                    "scale_name": trait.scale_name,
                    "data_type": trait.data_type,
                    "valid_values": _valid_values(trait),
                    "ontology_db_id": ontology_db_id,
                    "ontology_name": "Crop Ontology" if ontology_db_id else None,
                    "status": "active",
                    "data_source": data_source,
                    "synthetic_method": None if data_source == "real" else "category_trait_dictionary",
                    "additional_info": {
                        "pipeline": {
                            "category": crop.category,
                            "unit": trait.unit,
                            "raw_trait": raw_trait,
                        }
                    },
                }
            )
    return records


def _transform_brapi_germplasm(
    crop: CropRecord,
    organization_id: int,
    brapi_germplasm: list[dict[str, Any]],
    offset: int,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    crop_keys = {_normalize_name(crop.common_name), _normalize_name(crop.scientific_name)}
    for raw_index, raw in enumerate(brapi_germplasm, start=1):
        raw_crop = _brapi_crop_name(raw)
        if raw_crop and _normalize_name(raw_crop) not in crop_keys:
            continue
        if not raw_crop and crop.crop_id not in _normalize_name(str(raw.get("germplasmName", ""))):
            continue
        index = offset + len(records) + 1
        accession_number = str(raw.get("accessionNumber") or raw.get("germplasmDbId") or f"BRAPI-{crop.crop_id}-{raw_index}")
        records.append(
            {
                "organization_id": organization_id,
                "record_key": f"org{organization_id}:{crop.crop_id}:germplasm:brapi:{raw_index}",
                "germplasm_db_id": f"pipeline_org{organization_id}_{crop.crop_id}_brapi_{raw_index}",
                "germplasm_name": str(raw.get("germplasmName") or raw.get("defaultDisplayName") or accession_number),
                "default_display_name": str(raw.get("defaultDisplayName") or raw.get("germplasmName") or accession_number),
                "accession_number": f"PIPE-{organization_id}-{crop.crop_id.upper()}-BRAPI-{index:03d}",
                "common_crop_name": raw_crop or crop.common_name,
                "genus": str(raw.get("genus") or crop.genus),
                "species": str(raw.get("species") or crop.species),
                "country_of_origin_code": str(raw.get("countryOfOriginCode") or ("IND" if organization_id == 1 else "XXX")),
                "institute_code": str(raw.get("instituteCode") or "BRAPI"),
                "institute_name": str(raw.get("instituteName") or "BrAPI Test Server"),
                "biological_status_of_accession_code": str(raw.get("biologicalStatusOfAccessionCode") or "500"),
                "pedigree": str(raw.get("pedigree") or "BrAPI test-server germplasm record"),
                "synonyms": raw.get("synonyms") if isinstance(raw.get("synonyms"), list) else [crop.common_name],
                "data_source": "real",
                "synthetic_method": None,
                "additional_info": {
                    "pipeline": {
                        "source": "brapi_test_server",
                        "raw_germplasm": raw,
                    }
                },
            }
        )
    return records


def _valid_values(trait: TraitDef) -> dict[str, object]:
    if trait.nominal_values:
        return {"categories": list(trait.nominal_values)}
    values: dict[str, object] = {}
    if trait.valid_min is not None:
        values["min"] = trait.valid_min
    if trait.valid_max is not None:
        values["max"] = trait.valid_max
    return values


def _raw_traits_by_name(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        for key in ("observationVariableName", "traitName", "trait", "name"):
            if record.get(key):
                result.setdefault(_normalize_name(str(record[key])), record)
    return result


def _raw_ontology_id(record: dict[str, Any] | None) -> str | None:
    if not record:
        return None
    return (
        record.get("ontologyDbId")
        or record.get("observationVariableDbId")
        or record.get("traitDbId")
        or record.get("id")
    )


def _raw_method_name(record: dict[str, Any] | None) -> str | None:
    if not record:
        return None
    method = record.get("method")
    if isinstance(method, dict):
        return method.get("methodName")
    return record.get("methodName")


def _brapi_crop_name(record: dict[str, Any]) -> str | None:
    common_crop = record.get("commonCropName") or record.get("common_crop_name")
    if isinstance(common_crop, str) and common_crop:
        return common_crop
    crop_name = record.get("cropName") or record.get("crop")
    return str(crop_name) if crop_name else None


def _normalize_name(value: str) -> str:
    return " ".join(value.replace("×", "x").lower().split())


def _slug(value: str) -> str:
    return value.lower().replace(" ", "_").replace("-", "_").replace("/", "_").replace("&", "and")
