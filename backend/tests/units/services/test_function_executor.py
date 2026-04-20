from types import SimpleNamespace

import pytest

import app.modules.ai.services.tools as tools_module
from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.modules.ai.services.tools import FunctionExecutor
from app.modules.ai.services.tools import FunctionExecutionError
from app.modules.ai.services.tools import _derive_germplasm_confidence
from app.modules.environment.services.weather_service import WeatherForecastUnavailableError
from app.schemas.cross_domain_query_contract import (
    CROSS_DOMAIN_QUERY_CONTRACT_VERSION,
    CROSS_DOMAIN_QUERY_TRUST_SURFACE,
)
from app.schemas.genomics_marker_lookup_contract import (
    GENOMICS_MARKER_LOOKUP_CONTRACT_VERSION,
    GENOMICS_MARKER_LOOKUP_TRUST_SURFACE,
)
from app.schemas.germplasm_lookup_contract import (
    GERMPLASM_LOOKUP_CONTRACT_VERSION,
    GERMPLASM_LOOKUP_TRUST_SURFACE,
)
from app.schemas.phenotype_comparison_contract import (
    PHENOTYPE_COMPARISON_CONTRACT_VERSION,
    PHENOTYPE_COMPARISON_TRUST_SURFACE,
)
from app.modules.breeding.services.breeding_value_service import BreedingValueService
from app.schemas.trial_summary_contract import (
    TRIAL_SUMMARY_CONTRACT_VERSION,
    TRIAL_SUMMARY_TRUST_SURFACE,
)


class GermplasmSearchStub:
    async def get_by_id(self, db, organization_id, germplasm_id):
        records = {
            "101": {
                "id": "101",
                "name": "IR64",
                "accession": "IR64",
                "species": "Oryza sativa",
                "origin": "IN",
                "traits": ["yield"],
            },
            "102": {"id": "102", "name": "Swarna", "accession": "Swarna", "traits": ["yield"]},
        }
        return records.get(str(germplasm_id))

    async def search(self, db, organization_id, query=None, trait=None, limit=5):
        mapping = {
            "ir64": [{"id": "101", "name": "IR64", "accession": "IR64", "traits": ["yield"]}],
            "swarna": [{"id": "102", "name": "Swarna", "accession": "Swarna", "traits": ["yield"]}],
            "ambiguous": [
                {"id": "101", "name": "IR64", "accession": "IR64", "traits": ["yield"]},
                {"id": "102", "name": "Swarna", "accession": "Swarna", "traits": ["yield"]},
            ],
        }
        return mapping.get((query or "").lower(), [])


class TrialSearchStub:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    async def search(
        self,
        db,
        organization_id,
        query=None,
        crop=None,
        season=None,
        location=None,
        program=None,
        limit=5,
    ):
        self.calls.append(
            {
                "organization_id": organization_id,
                "query": query,
                "crop": crop,
                "season": season,
                "location": location,
                "program": program,
            }
        )
        if query == "Yield Trial":
            return [{"id": "1", "trial_db_id": "TRIAL-1", "name": "Yield Trial"}]
        if query == "wheat trial":
            return [{"id": "1", "trial_db_id": "TRIAL-1", "name": "Wheat Trial"}]
        if query == "ambiguous":
            return [
                {"id": "1", "trial_db_id": "TRIAL-1", "name": "Yield Trial"},
                {"id": "2", "trial_db_id": "TRIAL-2", "name": "Yield Trial 2"},
            ]
        return []

    async def get_by_id(self, db, organization_id, trial_id):
        return {
            "id": str(trial_id),
            "trial_db_id": "TRIAL-1",
            "name": "Yield Trial",
            "studies": [{"id": "11", "name": "Study 11", "type": "FIELD"}],
        }


class QTLMappingStub:
    async def get_traits(self, db, organization_id):
        return ["Blast Resistance", "Yield"]

    async def list_qtls(self, db, organization_id, trait=None, chromosome=None, min_lod=0, population=None):
        if trait == "Blast Resistance":
            return [
                {
                    "qtl_id": "qtl_blast_1",
                    "qtl_name": "Blast Resistance QTL 1",
                    "trait": "Blast Resistance",
                    "chromosome": "Chr6",
                    "lod": 6.3,
                    "pve": 14.2,
                    "marker_name": "M123",
                    "confidence_interval": {"low": 1200, "high": 1800},
                    "candidate_genes": [],
                    "additional_info": {},
                }
            ]
        return []

    async def get_gwas_results(self, db, organization_id, trait=None, chromosome=None, min_log_p=0, max_p_value=None):
        if trait == "Blast Resistance":
            return [
                {
                    "marker_name": "M123",
                    "chromosome": "Chr6",
                    "position": 1500,
                    "p_value": 1e-6,
                    "log_p": 6.0,
                    "effect_size": 0.82,
                    "standard_error": 0.12,
                    "maf": 0.24,
                    "is_significant": True,
                    "trait": "Blast Resistance",
                }
            ]
        return []


class CrossDomainTrialSearchStub:
    async def search(
        self,
        db,
        organization_id,
        query=None,
        crop=None,
        location=None,
        program=None,
        limit=20,
    ):
        return [
            {
                "id": "1",
                "trial_db_id": "TRIAL-1",
                "name": "Ludhiana Wheat Trial",
                "study_count": 2,
            }
        ]

    async def get_by_id(self, db, organization_id, trial_id):
        return {
            "id": str(trial_id),
            "trial_db_id": "TRIAL-1",
            "name": "Ludhiana Wheat Trial",
            "studies": [{"id": "11", "name": "Study 11", "type": "FIELD"}],
        }


class TrialPhenotypeWeatherInferenceStub:
    async def search(
        self,
        db,
        organization_id,
        query=None,
        crop=None,
        location=None,
        program=None,
        limit=20,
    ):
        return [
            {
                "id": "3",
                "trial_db_id": "TRIAL-RICE-1",
                "name": "Rice Yield Trial 2024",
                "location": "IRRI Research Station",
                "study_count": 1,
            }
        ]

    async def get_by_id(self, db, organization_id, trial_id):
        return {
            "id": str(trial_id),
            "trial_db_id": "TRIAL-RICE-1",
            "name": "Rice Yield Trial 2024",
            "location": {
                "id": "LOC-IRRI",
                "name": "IRRI Research Station",
                "country": "Philippines",
            },
            "studies": [{"id": "31", "name": "Rice Study 31", "type": "FIELD"}],
            "additional_info": {},
        }


class CrossDomainBreedingGenomicsSearchStub:
    async def search(self, db, organization_id, query=None, trait=None, limit=20):
        if trait in {"blast resistance", "yield"}:
            return [
                {
                    "id": "101",
                    "name": "IR64",
                    "accession": "IR64",
                    "traits": [trait],
                }
            ]
        return []


class ProtocolSearchStub:
    async def get_protocols(self, db, organization_id, crop=None, status=None):
        if crop in {"rice", "wheat"}:
            return [
                {
                    "id": "protocol-1",
                    "name": f"{crop.title()} Speed Breeding",
                    "crop": crop,
                    "status": "active",
                    "photoperiod": 22,
                    "days_to_flower": 35,
                    "generations_per_year": 4.0,
                }
            ]
        return []


class PredictHarvestTimingStub:
    def __init__(self, db):
        self.db = db
        self.calls: list[dict[str, object]] = []

    def predict_harvest_timing(self, field_id, planting_date, crop_name):
        self.calls.append(
            {
                "field_id": field_id,
                "planting_date": planting_date.isoformat(),
                "crop_name": crop_name,
            }
        )
        return {
            "field_id": field_id,
            "crop_name": crop_name,
            "predicted_harvest_date": "2026-11-01",
        }


class AnalyzeGDDStub:
    def __init__(self, db):
        self.db = db
        self.calls: list[dict[str, object]] = []

    def recommend_varieties(self, field_id):
        self.calls.append({"method": "recommend_varieties", "field_id": field_id})
        return {
            "recommendations": [
                {"variety": "IR64", "score": 0.91, "reason": "Optimal GDD match"}
            ]
        }

    def analyze_planting_windows(self, field_id, crop_name):
        self.calls.append(
            {
                "method": "analyze_planting_windows",
                "field_id": field_id,
                "crop_name": crop_name,
            }
        )
        return {
            "planting_windows": [
                {
                    "start_date": "2026-05-01",
                    "predicted_maturity": "2026-09-15",
                    "days_to_maturity": 137,
                    "suitability_score": 0.72,
                }
            ]
        }


class FailingAnalyzeGDDStub:
    def __init__(self, db):
        self.db = db

    def recommend_varieties(self, field_id):
        raise RuntimeError("gdd service unavailable")

    def analyze_planting_windows(self, field_id, crop_name):
        raise RuntimeError("gdd service unavailable")

    def create_climate_risk_alerts(self, field_id):
        raise RuntimeError("gdd service unavailable")


class FailingPredictHarvestTimingStub:
    def __init__(self, db):
        self.db = db

    def predict_harvest_timing(self, field_id, planting_date, crop_name):
        raise RuntimeError("gdd service unavailable")


class AnalyzeGxeResultStub:
    def to_dict(self):
        return {"principal_components": [0.62, 0.24], "summary": "ammi-stub"}


class AnalyzeGxeServiceStub:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def ammi_analysis(self, yield_matrix, genotype_names, environment_names):
        self.calls.append(
            {
                "method": "AMMI",
                "shape": yield_matrix.shape,
                "genotype_names": genotype_names,
                "environment_names": environment_names,
            }
        )
        return AnalyzeGxeResultStub()


class LocationSearchStub:
    async def search(self, db, organization_id, query=None, limit=20):
        return [
            {
                "id": "LOC-1",
                "name": query or "Ludhiana",
                "latitude": 30.9010,
                "longitude": 75.8573,
            }
        ]


class LocationSearchWithoutCoordinatesStub:
    async def search(self, db, organization_id, query=None, limit=20):
        return [{"id": "LOC-1", "name": query or "Ludhiana", "latitude": None, "longitude": None}]


class WeatherWindowStub:
    def __init__(self):
        self.activity = SimpleNamespace(value="selection_review")
        self.start = SimpleNamespace(isoformat=lambda: "2026-03-28T00:00:00+00:00")
        self.end = SimpleNamespace(isoformat=lambda: "2026-03-30T00:00:00+00:00")
        self.confidence = 0.8


class WeatherForecastStub:
    def __init__(self):
        self.alerts = ["heat_risk"]
        self.impacts = ["watch irrigation"]
        self.optimal_windows = [WeatherWindowStub()]


class WeatherServiceStub:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    async def get_forecast(
        self,
        location_id,
        location_name,
        days,
        crop,
        lat=None,
        lon=None,
        allow_generated_fallback=True,
    ):
        self.calls.append(
            {
                "location_id": location_id,
                "location_name": location_name,
                "days": days,
                "crop": crop,
                "lat": lat,
                "lon": lon,
                "allow_generated_fallback": allow_generated_fallback,
            }
        )
        return WeatherForecastStub()

    def get_veena_summary(self, forecast):
        return "Heat risk may influence current field performance."


class FailingWeatherServiceStub(WeatherServiceStub):
    async def get_forecast(
        self,
        location_id,
        location_name,
        days,
        crop,
        lat=None,
        lon=None,
        allow_generated_fallback=True,
    ):
        await super().get_forecast(
            location_id,
            location_name,
            days,
            crop,
            lat=lat,
            lon=lon,
            allow_generated_fallback=allow_generated_fallback,
        )
        raise WeatherForecastUnavailableError("weather provider request failed")


@pytest.mark.asyncio
async def test_handle_get_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_get(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "get_trait_details"
        assert params == {"organization_id": 1}
        assert shared.get_trial_summary is tools_module.get_trial_summary
        assert shared.observation_search_service is tools_module.observation_search_service
        assert shared.cross_domain_gdd_service_cls.__name__ == "CrossDomainGDDService"
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_get", fake_handle_get)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_get("get_trait_details", {"organization_id": 1})

    assert result == {
        "success": True,
        "delegated": True,
        "function": "get_trait_details",
    }


@pytest.mark.asyncio
async def test_handle_calculate_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_calculate(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "calculate_genetic_diversity"
        assert params == {"organization_id": 1}
        assert shared.observation_search_service is tools_module.observation_search_service
        assert shared.compute_engine is tools_module.compute_engine
        assert shared.resolve_database_backed_gblup_inputs is tools_module._resolve_database_backed_gblup_inputs
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_calculate", fake_handle_calculate)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_calculate("calculate_genetic_diversity", {"organization_id": 1})

    assert result == {
        "success": True,
        "delegated": True,
        "function": "calculate_genetic_diversity",
    }


@pytest.mark.asyncio
async def test_calculate_genetic_diversity_includes_deterministic_message(monkeypatch):
    class GeneticDiversityServiceStub:
        async def calculate_diversity_metrics(
            self,
            db,
            organization_id,
            population_id=None,
            program_id=None,
            germplasm_ids=None,
        ):
            assert organization_id == 1
            assert population_id == "POP-1"
            assert program_id is None
            assert germplasm_ids is None
            return {
                "population_id": "POP-1",
                "sample_size": 12,
                "loci_analyzed": 48,
                "metrics": [{"name": "Expected Heterozygosity (He)", "value": 0.42}],
                "recommendations": ["Maintain the current breeding population breadth."],
            }

    monkeypatch.setattr(
        "app.modules.genomics.services.genetic_diversity_service.genetic_diversity_service",
        GeneticDiversityServiceStub(),
    )

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "calculate_genetic_diversity",
        {"organization_id": 1, "population_id": "POP-1"},
    )

    assert result == {
        "success": True,
        "function": "calculate_genetic_diversity",
        "result_type": "diversity_metrics",
        "data": {
            "population_id": "POP-1",
            "sample_size": 12,
            "loci_analyzed": 48,
            "metrics": [{"name": "Expected Heterozygosity (He)", "value": 0.42}],
            "recommendations": ["Maintain the current breeding population breadth."],
            "message": "Calculated genetic diversity metrics for 12 samples across 48 loci.",
        },
        "demo": False,
    }


@pytest.mark.asyncio
async def test_handle_cross_domain_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_cross_domain(executor, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert params == {"organization_id": 1, "query": "recommend wheat lines"}
        assert shared.get_qtl_mapping_service is tools_module.get_qtl_mapping_service
        assert shared.resolve_trait_query is tools_module._resolve_trait_query
        assert shared.build_cross_domain_retrieval_tables is tools_module._build_cross_domain_retrieval_tables
        assert shared.build_cross_domain_evidence_envelope is tools_module._build_cross_domain_evidence_envelope
        assert shared.is_recommendation_query("recommend wheat lines") is True
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": "cross_domain_query"}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_cross_domain", fake_handle_cross_domain)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_cross_domain_query(
        {"organization_id": 1, "query": "recommend wheat lines"}
    )

    assert result == {
        "success": True,
        "delegated": True,
        "function": "cross_domain_query",
    }


@pytest.mark.asyncio
async def test_handle_search_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_search(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "search_traits"
        assert params == {"organization_id": 1, "query": "yield"}
        assert shared.seedlot_search_service is tools_module.seedlot_search_service
        assert shared.program_search_service is tools_module.program_search_service
        assert shared.trait_search_service is tools_module.trait_search_service
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_search", fake_handle_search)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_search("search_traits", {"organization_id": 1, "query": "yield"})

    assert result == {
        "success": True,
        "delegated": True,
        "function": "search_traits",
    }


@pytest.mark.asyncio
async def test_handle_statistics_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_statistics(executor, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert params == {"organization_id": 1}
        assert shared.observation_search_service is tools_module.observation_search_service
        assert shared.seedlot_search_service is tools_module.seedlot_search_service
        assert shared.program_search_service is tools_module.program_search_service
        assert shared.trait_search_service is tools_module.trait_search_service
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": "get_statistics"}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_statistics", fake_handle_statistics)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_statistics({"organization_id": 1})

    assert result == {
        "success": True,
        "delegated": True,
        "function": "get_statistics",
    }


@pytest.mark.asyncio
async def test_handle_check_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_check(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "check_seed_viability"
        assert params == {"organization_id": 1, "seedlot_id": "SL-1"}
        assert shared.seedlot_search_service is tools_module.seedlot_search_service
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_check", fake_handle_check)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_check("check_seed_viability", {"organization_id": 1, "seedlot_id": "SL-1"})

    assert result == {
        "success": True,
        "delegated": True,
        "function": "check_seed_viability",
    }


@pytest.mark.asyncio
async def test_handle_export_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_export(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "export_data"
        assert params == {"organization_id": 1, "data_type": "germplasm", "format": "json"}
        assert shared.observation_search_service is tools_module.observation_search_service
        assert shared.seedlot_search_service is tools_module.seedlot_search_service
        assert shared.program_search_service is tools_module.program_search_service
        assert shared.trait_search_service is tools_module.trait_search_service
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_export", fake_handle_export)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_export(
        "export_data",
        {"organization_id": 1, "data_type": "germplasm", "format": "json"},
    )

    assert result == {
        "success": True,
        "delegated": True,
        "function": "export_data",
    }


@pytest.mark.asyncio
async def test_handle_proposal_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_proposal(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "propose_create_trial"
        assert params == {"organization_id": 1, "crop": "rice"}
        assert shared.action_type_enum is tools_module.ActionType
        assert shared.get_proposal_service is tools_module.get_proposal_service
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_proposal", fake_handle_proposal)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_proposal(
        "propose_create_trial",
        {"organization_id": 1, "crop": "rice"},
    )

    assert result == {
        "success": True,
        "delegated": True,
        "function": "propose_create_trial",
    }


@pytest.mark.asyncio
async def test_handle_compare_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_compare(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "compare_germplasm"
        assert params == {"organization_id": 1, "germplasm_ids": ["IR64", "Swarna"]}
        assert shared.get_germplasm_identifier is tools_module._get_germplasm_identifier
        assert shared.observation_search_service is tools_module.observation_search_service
        assert shared.phenotype_interpretation_service is tools_module.phenotype_interpretation_service
        assert shared.envelope_observation_record_cls is tools_module.EnvelopeObservationRecord
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_compare", fake_handle_compare)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_compare(
        "compare_germplasm",
        {"organization_id": 1, "germplasm_ids": ["IR64", "Swarna"]},
    )

    assert result == {
        "success": True,
        "delegated": True,
        "function": "compare_germplasm",
    }


@pytest.mark.asyncio
async def test_handle_predict_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_predict(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "predict_cross"
        assert params == {"organization_id": 1, "parent1_id": "101", "parent2_id": "102"}
        assert shared.observation_search_service is tools_module.observation_search_service
        assert shared.cross_domain_gdd_service_cls is tools_module.CrossDomainGDDService
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_predict", fake_handle_predict)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_predict(
        "predict_cross",
        {"organization_id": 1, "parent1_id": "101", "parent2_id": "102"},
    )

    assert result == {
        "success": True,
        "delegated": True,
        "function": "predict_cross",
    }


@pytest.mark.asyncio
async def test_handle_analyze_delegates_to_extracted_module(monkeypatch):
    async def fake_handle_analyze(executor, function_name, params, *, shared, logger):
        assert isinstance(executor, FunctionExecutor)
        assert function_name == "analyze_gxe"
        assert params == {"organization_id": 1, "trait": "Yield"}
        assert shared.observation_search_service is tools_module.observation_search_service
        assert shared.cross_domain_gdd_service_cls is tools_module.CrossDomainGDDService
        assert logger.name == tools_module.__name__
        return {"success": True, "delegated": True, "function": function_name}

    monkeypatch.setattr("app.modules.ai.services.tools.handle_analyze", fake_handle_analyze)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor._handle_analyze("analyze_gxe", {"organization_id": 1, "trait": "Yield"})

    assert result == {
        "success": True,
        "delegated": True,
        "function": "analyze_gxe",
    }


class GermplasmSearchRecorder:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    async def search(self, db, organization_id, query=None, trait=None, limit=20):
        self.calls.append(
            {
                "organization_id": organization_id,
                "query": query,
                "trait": trait,
                "limit": limit,
            }
        )
        return [{"id": "101", "name": "IR64", "accession": "IR64"}]


@pytest.mark.asyncio
async def test_search_germplasm_combines_crop_into_query():
    search_service = GermplasmSearchRecorder()
    executor = FunctionExecutor(db=SimpleNamespace(), germplasm_search_service=search_service)

    result = await executor.execute(
        "search_germplasm",
        {
            "organization_id": 1,
            "crop": "rice",
            "query": "blast tolerance",
            "trait": "yield",
        },
    )

    assert result == {
        "success": True,
        "function": "search_germplasm",
        "result_type": "germplasm_list",
        "data": {
            "total": 1,
            "items": [{"id": "101", "name": "IR64", "accession": "IR64"}],
            "message": "Found 1 germplasm records matching 'rice blast tolerance'",
        },
        "demo": False,
    }
    assert search_service.calls == [
        {
            "organization_id": 1,
            "query": "rice blast tolerance",
            "trait": "yield",
            "limit": 20,
        }
    ]


@pytest.mark.asyncio
async def test_search_germplasm_returns_failure_when_service_unavailable():
    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "search_germplasm",
        {"organization_id": 1, "query": "rice"},
    )

    assert result == {
        "success": False,
        "error": "Germplasm search service not available",
        "message": "Failed to search germplasm database",
    }


class StatisticsRecorder:
    def __init__(self, payload: dict[str, int]):
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    async def get_statistics(self, db, organization_id):
        self.calls.append({"organization_id": organization_id})
        return self.payload


class FailingStatisticsRecorder:
    async def get_statistics(self, db, organization_id):
        raise RuntimeError("statistics temporarily unavailable")


@pytest.mark.asyncio
async def test_get_statistics_returns_cross_domain_counts(monkeypatch):
    observation_stats = StatisticsRecorder({"total_observations": 33})
    seedlot_stats = StatisticsRecorder({"total_seedlots": 11})
    program_stats = StatisticsRecorder({"total_programs": 3})
    trait_stats = StatisticsRecorder({"total_traits": 9})

    monkeypatch.setattr(tools_module, "observation_search_service", observation_stats)
    monkeypatch.setattr(tools_module, "seedlot_search_service", seedlot_stats)
    monkeypatch.setattr(tools_module, "program_search_service", program_stats)
    monkeypatch.setattr(tools_module, "trait_search_service", trait_stats)

    germplasm_stats = StatisticsRecorder({"total_germplasm": 21})
    trial_stats = StatisticsRecorder({"total_trials": 7})
    cross_stats = StatisticsRecorder({"total_crosses": 5})
    location_stats = StatisticsRecorder({"total_locations": 4})

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=germplasm_stats,
        trial_search_service=trial_stats,
        cross_search_service=cross_stats,
        location_search_service=location_stats,
    )

    result = await executor.execute("get_statistics", {"organization_id": 1})

    assert result["success"] is True
    assert result["result_type"] == "statistics"
    assert result["data"]["programs"] == {"total_programs": 3}
    assert result["data"]["germplasm"] == {"total_germplasm": 21}
    assert result["data"]["trials"] == {"total_trials": 7}
    assert result["data"]["observations"] == {"total_observations": 33}
    assert result["data"]["crosses"] == {"total_crosses": 5}
    assert result["data"]["locations"] == {"total_locations": 4}
    assert result["data"]["seedlots"] == {"total_seedlots": 11}
    assert result["data"]["traits"] == {"total_traits": 9}
    assert result["data"]["message"] == (
        "Database contains 3 programs, 21 germplasm, 7 trials, 33 observations, 11 seedlots, 9 traits"
    )
    assert result["calculation_ids"] == ["fn:get_statistics"]
    assert germplasm_stats.calls == [{"organization_id": 1}]
    assert trial_stats.calls == [{"organization_id": 1}]
    assert observation_stats.calls == [{"organization_id": 1}]
    assert cross_stats.calls == [{"organization_id": 1}]
    assert location_stats.calls == [{"organization_id": 1}]
    assert seedlot_stats.calls == [{"organization_id": 1}]
    assert program_stats.calls == [{"organization_id": 1}]
    assert trait_stats.calls == [{"organization_id": 1}]


@pytest.mark.asyncio
async def test_get_statistics_returns_failure_when_service_errors(monkeypatch):
    monkeypatch.setattr(tools_module, "observation_search_service", StatisticsRecorder({"total_observations": 0}))
    monkeypatch.setattr(tools_module, "seedlot_search_service", StatisticsRecorder({"total_seedlots": 0}))
    monkeypatch.setattr(tools_module, "program_search_service", StatisticsRecorder({"total_programs": 0}))
    monkeypatch.setattr(tools_module, "trait_search_service", StatisticsRecorder({"total_traits": 0}))

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=FailingStatisticsRecorder(),
        trial_search_service=StatisticsRecorder({"total_trials": 0}),
        cross_search_service=StatisticsRecorder({"total_crosses": 0}),
        location_search_service=StatisticsRecorder({"total_locations": 0}),
    )

    result = await executor.execute("get_statistics", {"organization_id": 1})

    assert result == {
        "success": False,
        "error": "statistics temporarily unavailable",
        "message": "Failed to get database statistics",
    }


class SeedlotViabilityRecorder:
    def __init__(self, seedlots: list[dict[str, object]] | None = None):
        self.seedlots = seedlots or []
        self.get_by_germplasm_calls: list[dict[str, object]] = []
        self.check_viability_calls: list[dict[str, object]] = []

    async def get_by_germplasm(self, db, organization_id, germplasm_id, limit=5):
        self.get_by_germplasm_calls.append(
            {
                "organization_id": organization_id,
                "germplasm_id": germplasm_id,
                "limit": limit,
            }
        )
        return self.seedlots

    async def check_viability(self, db, organization_id, seedlot_id):
        self.check_viability_calls.append(
            {
                "organization_id": organization_id,
                "seedlot_id": seedlot_id,
            }
        )
        return {
            "seedlot_id": seedlot_id,
            "is_viable": True,
        }


@pytest.mark.asyncio
async def test_check_seed_viability_by_germplasm_checks_all_seedlots(monkeypatch):
    seedlot_service = SeedlotViabilityRecorder(seedlots=[{"id": "SL-1"}, {"id": "SL-2"}])
    monkeypatch.setattr(tools_module, "seedlot_search_service", seedlot_service)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "check_seed_viability",
        {"organization_id": 1, "germplasm_id": "101"},
    )

    assert result == {
        "success": True,
        "function": "check_seed_viability",
        "result_type": "viability_results",
        "data": {
            "seedlot_count": 2,
            "results": [
                {"seedlot_id": "SL-1", "is_viable": True},
                {"seedlot_id": "SL-2", "is_viable": True},
            ],
            "message": "Checked viability for 2 seedlots",
        },
        "demo": False,
    }
    assert seedlot_service.get_by_germplasm_calls == [
        {
            "organization_id": 1,
            "germplasm_id": 101,
            "limit": 5,
        }
    ]
    assert seedlot_service.check_viability_calls == [
        {"organization_id": 1, "seedlot_id": "SL-1"},
        {"organization_id": 1, "seedlot_id": "SL-2"},
    ]


@pytest.mark.asyncio
async def test_check_seed_viability_single_seedlot_includes_deterministic_message(monkeypatch):
    seedlot_service = SeedlotViabilityRecorder()
    monkeypatch.setattr(tools_module, "seedlot_search_service", seedlot_service)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "check_seed_viability",
        {"organization_id": 1, "seedlot_id": "SL-1"},
    )

    assert result == {
        "success": True,
        "function": "check_seed_viability",
        "result_type": "viability_result",
        "data": {
            "seedlot_id": "SL-1",
            "is_viable": True,
            "message": "Checked viability for seedlot SL-1",
        },
        "demo": False,
    }
    assert seedlot_service.check_viability_calls == [
        {"organization_id": 1, "seedlot_id": "SL-1"},
    ]


@pytest.mark.asyncio
async def test_check_seed_viability_requires_identifier(monkeypatch):
    monkeypatch.setattr(tools_module, "seedlot_search_service", SeedlotViabilityRecorder())

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute("check_seed_viability", {"organization_id": 1})

    assert result == {
        "success": False,
        "error": "seedlot_id or germplasm_id required",
        "message": "Please specify a seedlot ID or germplasm ID",
    }


@pytest.mark.asyncio
async def test_navigate_to_includes_deterministic_message():
    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "navigate_to",
        {"page": "/trials", "filters": {"crop": "rice"}},
    )

    assert result == {
        "success": True,
        "function": "navigate_to",
        "result_type": "navigation",
        "data": {
            "page": "/trials",
            "filters": {"crop": "rice"},
            "action": "navigate",
            "message": "Open /trials with the requested filters.",
        },
    }


class ExportServiceRecorder:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def export_to_csv(self, data):
        self.calls.append({"format": "csv", "count": len(data)})
        return "csv-export"

    def export_to_tsv(self, data):
        self.calls.append({"format": "tsv", "count": len(data)})
        return "tsv-export"

    def export_to_json(self, data):
        self.calls.append({"format": "json", "count": len(data)})
        return '{"items": [{"id": "101"}]}'


@pytest.mark.asyncio
async def test_export_data_returns_preview_and_length(monkeypatch):
    export_service = ExportServiceRecorder()
    monkeypatch.setattr(
        "app.modules.ai.services.tool_export_handlers.get_export_service",
        lambda: export_service,
    )

    search_service = GermplasmSearchRecorder()
    executor = FunctionExecutor(db=SimpleNamespace(), germplasm_search_service=search_service)

    result = await executor.execute(
        "export_data",
        {
            "organization_id": 1,
            "data_type": "germplasm",
            "format": "json",
            "query": "IR64",
            "limit": 5,
        },
    )

    assert result == {
        "success": True,
        "function": "export_data",
        "result_type": "data_exported",
        "data": {
            "data_type": "germplasm",
            "format": "json",
            "record_count": 1,
            "content_preview": '{"items": [{"id": "101"}]}',
            "content_length": 26,
            "message": "Exported 1 germplasm records in JSON format",
        },
        "demo": False,
    }
    assert search_service.calls == [
        {
            "organization_id": 1,
            "query": "IR64",
            "trait": None,
            "limit": 5,
        }
    ]
    assert export_service.calls == [{"format": "json", "count": 1}]


@pytest.mark.asyncio
async def test_export_data_rejects_unknown_data_type():
    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "export_data",
        {"organization_id": 1, "data_type": "unknown"},
    )

    assert result == {
        "success": False,
        "error": "Unknown data type: unknown",
        "message": "Supported types: germplasm, trials, observations, crosses, locations, seedlots, traits, programs",
    }


class ProposalServiceRecorder:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    async def create_proposal(
        self,
        db,
        organization_id,
        title,
        description,
        action_type,
        target_data,
        ai_rationale,
        confidence_score,
        user_id,
    ):
        self.calls.append(
            {
                "organization_id": organization_id,
                "title": title,
                "description": description,
                "action_type": action_type,
                "target_data": target_data,
                "ai_rationale": ai_rationale,
                "confidence_score": confidence_score,
                "user_id": user_id,
            }
        )
        return SimpleNamespace(id=77, status="pending_review", title=title)


@pytest.mark.asyncio
async def test_propose_create_trial_creates_reviewable_proposal(monkeypatch):
    proposal_service = ProposalServiceRecorder()
    monkeypatch.setattr(tools_module, "get_proposal_service", lambda: proposal_service)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "propose_create_trial",
        {
            "organization_id": 1,
            "user_id": 9,
            "title": "Rice Trial Proposal",
            "description": "Create a new irrigated rice trial",
            "rationale": "Requested by breeding lead",
            "confidence": 88,
            "crop": "rice",
            "location": "IRRI",
        },
    )

    assert result == {
        "success": True,
        "function": "propose_create_trial",
        "result_type": "proposal_created",
        "data": {
            "proposal_id": 77,
            "status": "pending_review",
            "title": "Rice Trial Proposal",
            "message": "Proposal created successfully (ID: 77). Pending review.",
        },
        "demo": False,
    }
    assert proposal_service.calls == [
        {
            "organization_id": 1,
            "title": "Rice Trial Proposal",
            "description": "Create a new irrigated rice trial",
            "action_type": tools_module.ActionType.CREATE_TRIAL,
            "target_data": {"crop": "rice", "location": "IRRI"},
            "ai_rationale": "Requested by breeding lead",
            "confidence_score": 88,
            "user_id": 9,
        }
    ]


@pytest.mark.asyncio
async def test_proposal_handler_rejects_unknown_proposal_type():
    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "propose_unknown_action",
        {"organization_id": 1},
    )

    assert result == {
        "success": False,
        "error": "Unknown proposal type: propose_unknown_action",
        "message": "This action cannot be proposed.",
    }


@pytest.mark.asyncio
async def test_recommend_varieties_by_gdd_uses_cross_domain_gdd_service(monkeypatch):
    created_instances: list[AnalyzeGDDStub] = []

    def fake_gdd_service_cls(db):
        instance = AnalyzeGDDStub(db)
        created_instances.append(instance)
        return instance

    monkeypatch.setattr("app.modules.ai.services.tools.CrossDomainGDDService", fake_gdd_service_cls)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "recommend_varieties_by_gdd",
        {"field_id": 17, "target_gdd_range": {"min": 1200, "max": 1450}},
    )

    assert result == {
        "success": True,
        "function": "recommend_varieties_by_gdd",
        "result_type": "variety_recommendations",
        "data": {
            "recommendations": [
                {"variety": "IR64", "score": 0.91, "reason": "Optimal GDD match"}
            ],
            "message": "Recommended 1 varieties for field 17 based on GDD suitability.",
        },
    }
    assert len(created_instances) == 1
    assert created_instances[0].calls == [{"method": "recommend_varieties", "field_id": 17}]


@pytest.mark.asyncio
async def test_recommend_varieties_by_gdd_returns_deterministic_failure_message(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.services.tools.CrossDomainGDDService",
        lambda db: FailingAnalyzeGDDStub(db),
    )

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "recommend_varieties_by_gdd",
        {"field_id": 17},
    )

    assert result == {
        "success": False,
        "error": "gdd service unavailable",
        "message": "Failed to recommend varieties by GDD",
    }


@pytest.mark.asyncio
async def test_analyze_planting_windows_uses_cross_domain_gdd_service(monkeypatch):
    created_instances: list[AnalyzeGDDStub] = []

    def fake_gdd_service_cls(db):
        instance = AnalyzeGDDStub(db)
        created_instances.append(instance)
        return instance

    monkeypatch.setattr("app.modules.ai.services.tools.CrossDomainGDDService", fake_gdd_service_cls)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "analyze_planting_windows",
        {"field_id": 23, "crop_name": "maize"},
    )

    assert result == {
        "success": True,
        "function": "analyze_planting_windows",
        "result_type": "planting_windows",
        "data": {
            "planting_windows": [
                {
                    "start_date": "2026-05-01",
                    "predicted_maturity": "2026-09-15",
                    "days_to_maturity": 137,
                    "suitability_score": 0.72,
                }
            ],
            "message": "Analyzed planting windows for maize in field 23.",
        },
    }
    assert len(created_instances) == 1
    assert created_instances[0].calls == [
        {
            "method": "analyze_planting_windows",
            "field_id": 23,
            "crop_name": "maize",
        }
    ]


@pytest.mark.asyncio
async def test_analyze_planting_windows_returns_deterministic_failure_message(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.services.tools.CrossDomainGDDService",
        lambda db: FailingAnalyzeGDDStub(db),
    )

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "analyze_planting_windows",
        {"field_id": 23, "crop_name": "maize"},
    )

    assert result == {
        "success": False,
        "error": "gdd service unavailable",
        "message": "Failed to analyze planting windows",
    }


@pytest.mark.asyncio
async def test_analyze_gxe_returns_expected_summary(monkeypatch):
    created_services: list[AnalyzeGxeServiceStub] = []

    async def fake_observation_search(db, organization_id, trait=None, limit=1000):
        assert organization_id == 1
        assert trait == "Yield"
        assert limit == 1000
        return [
            {
                "value": "10.0",
                "germplasm": {"id": "101", "name": "IR64"},
                "study": {"id": "ENV-1", "name": "Env 1"},
            },
            {
                "value": "12.0",
                "germplasm": {"id": "101", "name": "IR64"},
                "study": {"id": "ENV-2", "name": "Env 2"},
            },
            {
                "value": "8.0",
                "germplasm": {"id": "102", "name": "Swarna"},
                "study": {"id": "ENV-1", "name": "Env 1"},
            },
            {
                "value": "11.0",
                "germplasm": {"id": "102", "name": "Swarna"},
                "study": {"id": "ENV-2", "name": "Env 2"},
            },
            {
                "value": "9.0",
                "germplasm": {"id": "103", "name": "N22"},
                "study": {"id": "ENV-1", "name": "Env 1"},
            },
            {
                "value": "13.0",
                "germplasm": {"id": "103", "name": "N22"},
                "study": {"id": "ENV-2", "name": "Env 2"},
            },
        ]

    def fake_get_gxe_service():
        instance = AnalyzeGxeServiceStub()
        created_services.append(instance)
        return instance

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.search",
        fake_observation_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tool_analyze_handlers.get_gxe_service",
        fake_get_gxe_service,
    )

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "analyze_gxe",
        {"organization_id": 1, "trait": "Yield"},
    )

    assert result["success"] is True
    assert result["result_type"] == "gxe_analysis"
    assert result["data"]["method"] == "AMMI"
    assert result["data"]["trait"] == "Yield"
    assert result["data"]["n_genotypes"] == 3
    assert result["data"]["n_environments"] == 2
    assert result["data"]["n_observations"] == 6
    assert result["data"]["analysis"] == {
        "principal_components": [0.62, 0.24],
        "summary": "ammi-stub",
    }
    assert created_services[0].calls == [
        {
            "method": "AMMI",
            "shape": (3, 2),
            "genotype_names": ["IR64", "Swarna", "N22"],
            "environment_names": ["Env 1", "Env 2"],
        }
    ]


@pytest.mark.asyncio
async def test_analyze_gxe_requires_minimum_observations(monkeypatch):
    async def fake_observation_search(db, organization_id, trait=None, limit=1000):
        return [
            {
                "value": "10.0",
                "germplasm": {"id": "101", "name": "IR64"},
                "study": {"id": "ENV-1", "name": "Env 1"},
            }
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.search",
        fake_observation_search,
    )

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "analyze_gxe",
        {"organization_id": 1, "trait": "Yield"},
    )

    assert result == {
        "success": False,
        "error": "Insufficient data",
        "message": "Need at least 6 observations for G×E analysis. Found 1 for trait 'Yield'",
    }


@pytest.mark.asyncio
async def test_predict_cross_returns_expected_summary(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=50):
        if germplasm_id == 101:
            return [{"value": "4.0", "trait": {"name": "Yield"}}]
        return [{"value": "6.0", "trait": {"name": "Yield"}}]

    async def fake_observation_search(db, organization_id, trait=None, limit=200):
        return [
            {"value": "4.0", "trait": {"name": "Yield"}},
            {"value": "6.0", "trait": {"name": "Yield"}},
            {"value": "5.0", "trait": {"name": "Yield"}},
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.search",
        fake_observation_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        breeding_value_service=BreedingValueService(),
    )

    result = await executor.execute(
        "predict_cross",
        {
            "organization_id": 1,
            "parent1_id": "101",
            "parent2_id": "102",
            "trait": "Yield",
            "heritability": 0.5,
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "cross_prediction"
    assert result["data"]["parent1"]["name"] == "IR64"
    assert result["data"]["parent2"]["name"] == "Swarna"
    assert result["data"]["parent1"]["mean_phenotype"] == 4.0
    assert result["data"]["parent2"]["mean_phenotype"] == 6.0
    assert result["data"]["trait_mean"] == 5.0
    assert result["data"]["heritability"] == 0.5


@pytest.mark.asyncio
async def test_predict_cross_requires_parent_ids():
    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "predict_cross",
        {"organization_id": 1, "parent1_id": "101"},
    )

    assert result == {
        "success": False,
        "error": "parent1_id and parent2_id are required",
        "message": "Please specify both parent IDs for cross prediction",
    }


@pytest.mark.asyncio
async def test_predict_harvest_timing_uses_cross_domain_gdd_service(monkeypatch):
    created_instances: list[PredictHarvestTimingStub] = []

    def fake_gdd_service_cls(db):
        instance = PredictHarvestTimingStub(db)
        created_instances.append(instance)
        return instance

    monkeypatch.setattr("app.modules.ai.services.tools.CrossDomainGDDService", fake_gdd_service_cls)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "predict_harvest_timing",
        {
            "field_id": 17,
            "planting_date": "2026-07-01",
            "crop_name": "maize",
        },
    )

    assert result == {
        "success": True,
        "function": "predict_harvest_timing",
        "result_type": "harvest_timing_prediction",
        "data": {
            "field_id": 17,
            "crop_name": "maize",
            "predicted_harvest_date": "2026-11-01",
            "message": "Predicted harvest timing for maize planted on 2026-07-01.",
        },
    }
    assert len(created_instances) == 1
    assert created_instances[0].calls == [
        {
            "field_id": 17,
            "planting_date": "2026-07-01",
            "crop_name": "maize",
        }
    ]


@pytest.mark.asyncio
async def test_predict_harvest_timing_returns_deterministic_failure_message(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.services.tools.CrossDomainGDDService",
        lambda db: FailingPredictHarvestTimingStub(db),
    )

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "predict_harvest_timing",
        {
            "field_id": 17,
            "planting_date": "2026-07-01",
            "crop_name": "maize",
        },
    )

    assert result == {
        "success": False,
        "error": "gdd service unavailable",
        "message": "Failed to predict harvest timing",
    }


@pytest.mark.asyncio
async def test_get_gdd_insights_includes_deterministic_message(monkeypatch):
    created_instances: list[AnalyzeGDDStub] = []

    def fake_gdd_service_cls(db):
        instance = AnalyzeGDDStub(db)
        created_instances.append(instance)
        return instance

    monkeypatch.setattr("app.modules.ai.services.tools.CrossDomainGDDService", fake_gdd_service_cls)

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "get_gdd_insights",
        {"field_id": 23, "insight_type": "planting"},
    )

    assert result == {
        "success": True,
        "function": "get_gdd_insights",
        "result_type": "gdd_insights",
        "data": {
            "planting_windows": [
                {
                    "start_date": "2026-05-01",
                    "predicted_maturity": "2026-09-15",
                    "days_to_maturity": 137,
                    "suitability_score": 0.72,
                }
            ],
            "message": "Generated planting GDD insights for field 23.",
        },
    }
    assert len(created_instances) == 1
    assert created_instances[0].calls == [
        {
            "method": "analyze_planting_windows",
            "field_id": 23,
            "crop_name": "maize",
        }
    ]


@pytest.mark.asyncio
async def test_get_gdd_insights_returns_deterministic_failure_message(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.services.tools.CrossDomainGDDService",
        lambda db: FailingAnalyzeGDDStub(db),
    )

    executor = FunctionExecutor(db=SimpleNamespace())

    result = await executor.execute(
        "get_gdd_insights",
        {"field_id": 23, "insight_type": "planting"},
    )

    assert result == {
        "success": False,
        "error": "gdd service unavailable",
        "message": "Failed to get GDD insights",
    }


@pytest.mark.asyncio
async def test_compare_germplasm_returns_shared_interpretation(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=100):
        if germplasm_id == 101:
            return [
                {
                    "id": "obs-1",
                    "observation_db_id": "OBS-1",
                    "value": "4.0",
                    "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                    "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
                },
            ]
        return [
            {
                "id": "obs-2",
                "observation_db_id": "OBS-2",
                "value": "5.5",
                "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                "germplasm": {"id": "102", "name": "Swarna", "accession": "Swarna"},
            },
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        breeding_value_service=BreedingValueService(),
    )

    result = await executor.execute(
        "compare_germplasm",
        {"organization_id": 1, "germplasm_ids": ["IR64", "Swarna"]},
    )

    assert result["success"] is True
    assert result["result_type"] == "comparison"
    assert isinstance(result["data"], list)
    assert result["comparison_context"]["germplasm_count"] == 2
    assert len(result["comparison_context"]["items"]) == 2
    assert result["comparison_context"]["message"] == (
        "Compared 2 germplasm entries using the shared phenotype interpretation contract"
    )
    assert result["comparison_context"]["interpretation"]["contract_version"] == "phenotyping.interpretation.v1"
    assert result["data"][0]["candidate"] == "Swarna"
    assert result["calculation_ids"]
    assert result["response_contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert result["trust_surface"] == PHENOTYPE_COMPARISON_TRUST_SURFACE
    assert result["data_source"] == "database"
    assert result["schema_version"] == "1"
    assert result["scope"] == "compare"
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["data_age_seconds"] is None
    assert result["evidence_envelope"]["claims"]
    assert any(
        ref["entity_id"] == "db:germplasm:IR64"
        for ref in result["evidence_envelope"]["evidence_refs"]
    )
    assert result["evidence_envelope"]["calculation_steps"]
    assert result["retrieval_audit"]["services"] == [
        "germplasm_search_service.search",
        "observation_search_service.get_by_germplasm",
        "phenotype_interpretation_service.build_interpretation",
    ]
    assert result["retrieval_audit"]["tables"] == [
        "Germplasm",
        "Observation",
        "ObservationVariable",
    ]
    assert result["retrieval_audit"]["entities"]["requested_germplasm_ids"] == ["IR64", "Swarna"]
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == ["IR64", "Swarna"]
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "requested_traits": [],
    }
    assert result["plan_execution_summary"]["domains_involved"] == ["breeding", "analytics"]
    compare_step = result["plan_execution_summary"]["steps"][0]
    assert compare_step["status"] == "completed"
    assert set(compare_step["actual_outputs"]) >= {
        "comparison",
        "germplasm",
        "interpretation",
    }
    assert compare_step["output_counts"]["comparison"] == len(result["data"])
    assert compare_step["output_counts"]["germplasm"] == 2
    assert compare_step["output_entity_ids"]["comparison"] == [
        item["candidate"] for item in result["data"]
    ]
    assert compare_step["output_entity_ids"]["germplasm"] == ["IR64", "Swarna"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_compare_germplasm_returns_safe_failure_when_not_enough_germplasm_resolve(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=100):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "value": "4.0",
                "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            },
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    result = await executor.execute(
        "compare_germplasm",
        {"organization_id": 1, "germplasm_ids": ["IR64", "unknown-line"]},
    )

    assert result["success"] is False
    assert result["error"] == "Not enough germplasm found"
    assert result["message"] == "Only found 1 of 2 requested germplasm"
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert result["safe_failure"]["searched"] == [
        "phenotype_comparison.compare",
        "germplasm_search_service",
    ]
    assert result["safe_failure"]["missing"] == [
        "at least two resolvable germplasm identifiers"
    ]
    assert result["safe_failure"]["next_steps"] == [
        "Retry with exact accession or germplasm IDs.",
        "Reduce the comparison to two explicitly named germplasm entries.",
    ]
    assert result["retrieval_audit"]["services"] == [
        "germplasm_search_service.search",
        "observation_search_service.get_by_germplasm",
    ]
    assert result["retrieval_audit"]["tables"] == [
        "Germplasm",
        "Observation",
        "ObservationVariable",
    ]
    assert result["retrieval_audit"]["entities"] == {
        "requested_germplasm_ids": ["IR64", "unknown-line"],
        "resolved_germplasm_ids": ["IR64"],
    }
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "requested_traits": [],
    }
    assert result["plan_execution_summary"]["missing_domains"] == ["breeding"]
    compare_step = result["plan_execution_summary"]["steps"][0]
    assert compare_step["status"] == "missing"
    assert "germplasm" in compare_step["actual_outputs"]
    assert "observations" in compare_step["actual_outputs"]
    assert compare_step["output_counts"]["germplasm"] == 1
    assert compare_step["output_counts"]["observations"] == 1
    assert compare_step["output_entity_ids"]["germplasm"] == ["IR64"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_trait_summary_returns_contract_metadata(monkeypatch):
    async def fake_get_comparison_statistics(germplasm_ids, db, organization_id):
        assert germplasm_ids == "IR64,Swarna"
        return {
            "response_contract_version": "phenotype_comparison.response.v1",
            "contract_version": "phenotype_comparison.response.v1",
            "trust_surface": "phenotype_comparison",
            "data_source": "database",
            "source": "database",
            "schema_version": "1",
            "confidence_score": 0.75,
            "data_age_seconds": None,
            "scope": "statistics",
            "total_germplasm": 2,
            "total_traits": 1,
            "trait_summary": {"yield": {"mean": 4.75, "min": 4.0, "max": 5.5, "std": 1.06}},
            "interpretation": {"contract_version": "phenotyping.interpretation.v1"},
            "evidence_refs": ["db:germplasm:IR64", "db:germplasm:Swarna"],
            "calculation_ids": ["calc:yield:mean"],
            "evidence_envelope": {
                "claims": ["Trait summary generated"],
                "evidence_refs": [{"entity_id": "db:germplasm:IR64"}],
                "calculation_steps": [{"step_id": "calc:yield:mean"}],
                "policy_flags": [],
                "uncertainty": {"confidence": 0.75, "missing_data": []},
            },
        }

    monkeypatch.setattr(
        "app.modules.ai.services.tools.get_comparison_statistics",
        fake_get_comparison_statistics,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    result = await executor.execute(
        "get_trait_summary",
        {"organization_id": 1, "germplasm_ids": ["IR64", "Swarna"]},
    )

    assert result["success"] is True
    assert result["result_type"] == "trait_summary"
    assert result["response_contract_version"] == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert result["trust_surface"] == PHENOTYPE_COMPARISON_TRUST_SURFACE
    assert result["data_source"] == "database"
    assert result["schema_version"] == "1"
    assert result["scope"] == "statistics"
    assert result["confidence_score"] == 0.75
    assert result["data_age_seconds"] is None
    assert result["data"]["message"] == (
        "Trait summary statistics retrieved from database-backed phenotype "
        "comparison surfaces."
    )
    assert result["data"]["trait_summary"]["yield"]["mean"] == 4.75
    assert result["evidence_envelope"]["claims"] == ["Trait summary generated"]
    assert result["evidence_envelope"]["evidence_refs"] == [{"entity_id": "db:germplasm:IR64"}]
    assert result["evidence_envelope"]["calculation_steps"] == [
        {"step_id": "calc:yield:mean"}
    ]
    assert result["evidence_envelope"]["uncertainty"]["confidence"] == 0.75
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["evidence_refs"] == ["db:germplasm:IR64", "db:germplasm:Swarna"]
    assert result["calculation_ids"] == ["calc:yield:mean"]
    assert result["retrieval_audit"]["services"] == [
        "app.api.v2.phenotype_comparison.get_comparison_statistics"
    ]
    assert result["retrieval_audit"]["tables"] == [
        "Germplasm",
        "Observation",
        "ObservationVariable",
    ]
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == ["IR64", "Swarna"]
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "statistics_scope": "statistics",
    }
    assert result["plan_execution_summary"]["domains_involved"] == ["breeding", "analytics"]
    trait_step = result["plan_execution_summary"]["steps"][0]
    assert trait_step["status"] == "completed"
    assert set(trait_step["actual_outputs"]) >= {"trait_summary", "interpretation", "germplasm"}
    assert trait_step["output_counts"]["trait_summary"] == 1
    assert trait_step["output_counts"]["germplasm"] == 2
    assert trait_step["output_entity_ids"]["trait_summary"] == ["yield"]
    assert trait_step["output_entity_ids"]["germplasm"] == ["IR64", "Swarna"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_trait_summary_returns_safe_failure_when_germplasm_unresolved():
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    result = await executor.execute(
        "get_trait_summary",
        {"organization_id": 1, "germplasm_ids": ["unknown-line"]},
    )

    assert result["success"] is False
    assert result["error"] == "Trait summary requires at least one resolvable germplasm"
    assert result["message"] == "No requested germplasm could be resolved for phenotype trait summary."
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert result["safe_failure"]["searched"] == [
        "phenotype_comparison.statistics",
        "germplasm_search_service",
    ]
    assert result["safe_failure"]["missing"] == ["resolvable germplasm identifiers"]
    assert result["safe_failure"]["next_steps"] == [
        "Retry with exact accession or germplasm IDs.",
        "Use fewer or more specific germplasm names.",
    ]
    assert result["retrieval_audit"]["services"] == [
        "germplasm_search_service.get_by_id",
        "germplasm_search_service.search",
    ]
    assert result["retrieval_audit"]["tables"] == ["Germplasm"]
    assert result["retrieval_audit"]["entities"]["requested_germplasm_ids"] == ["unknown-line"]
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == []
    assert result["retrieval_audit"]["scope"] == {"organization_id": 1}
    assert result["plan_execution_summary"]["missing_domains"] == ["breeding"]
    trait_step = result["plan_execution_summary"]["steps"][0]
    assert trait_step["status"] == "missing"
    assert trait_step["missing_reason"] == (
        "no requested germplasm identifiers resolved to an authoritative phenotype comparison scope"
    )
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_marker_associations_returns_contract_metadata(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.services.tools.get_qtl_mapping_service",
        lambda: QTLMappingStub(),
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
    )

    result = await executor.execute(
        "get_marker_associations",
        {"organization_id": 1, "query": "blast resistance"},
    )

    assert result["success"] is True
    assert result["result_type"] == "marker_associations"
    assert result["response_contract_version"] == GENOMICS_MARKER_LOOKUP_CONTRACT_VERSION
    assert result["trust_surface"] == GENOMICS_MARKER_LOOKUP_TRUST_SURFACE
    assert result["data_source"] == "database"
    assert result["schema_version"] == "1"
    assert result["confidence_score"] == 0.9
    assert result["data"]["message"] == (
        "Retrieved genomics marker associations for trait 'Blast Resistance' from "
        "database-backed QTL and GWAS records."
    )
    assert result["data"]["trait"] == "Blast Resistance"
    assert result["data"]["summary"]["qtl_count"] == 1
    assert "db:qtl:qtl_blast_1" in result["evidence_refs"]
    assert "db:marker:M123" in result["evidence_refs"]
    assert result["calculation_ids"] == ["calc:genomics:marker_lookup"]
    assert result["evidence_envelope"]["claims"] == [
        "Genomics marker associations for trait 'Blast Resistance' were retrieved from database-backed QTL/GWAS records.",
        "Matched 1 QTLs and 1 marker associations.",
    ]
    assert result["evidence_envelope"]["evidence_refs"][0]["entity_id"] == "db:qtl:qtl_blast_1"
    assert result["evidence_envelope"]["evidence_refs"][0]["query_or_method"] == "QTLMappingService.list_qtls"
    assert result["evidence_envelope"]["calculation_steps"] == [
        {
            "step_id": "calc:genomics:marker_lookup",
            "formula": "trait-filtered retrieval across QTL and GWAS records",
            "inputs": {
                "trait": "Blast Resistance",
                "qtl_count": 1,
                "association_count": 1,
            },
        }
    ]
    assert result["evidence_envelope"]["uncertainty"]["confidence"] == 0.9
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["retrieval_audit"]["entities"]["resolved_trait"] == "Blast Resistance"
    assert result["retrieval_audit"]["services"] == [
        "QTLMappingService.get_traits",
        "QTLMappingService.list_qtls",
        "QTLMappingService.get_gwas_results",
    ]
    assert result["retrieval_audit"]["tables"] == ["BioQTL", "GWASResult", "GWASRun"]
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "candidate_traits": ["Blast Resistance"],
    }
    assert result["plan_execution_summary"]["domains_involved"] == ["genomics"]
    genomics_step = result["plan_execution_summary"]["steps"][0]
    assert genomics_step["status"] == "completed"
    assert set(genomics_step["actual_outputs"]) == {"qtls", "marker_associations"}
    assert genomics_step["output_counts"]["qtls"] == 1
    assert genomics_step["output_counts"]["marker_associations"] == 1
    assert genomics_step["output_entity_ids"]["qtls"] == ["qtl_blast_1"]
    assert genomics_step["output_entity_ids"]["marker_associations"] == ["M123"]
    assert genomics_step["output_metadata"]["resolved_trait"] == "Blast Resistance"
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_marker_associations_returns_safe_failure_when_trait_unresolved(monkeypatch):
    monkeypatch.setattr(
        "app.modules.ai.services.tools.get_qtl_mapping_service",
        lambda: QTLMappingStub(),
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
    )

    result = await executor.execute(
        "get_marker_associations",
        {"organization_id": 1, "query": "unknown resistance"},
    )

    assert result["success"] is False
    assert result["error"] == "Unresolvable marker association query"
    assert result["message"] == (
        "Could not resolve 'unknown resistance' to one authoritative genomics trait."
    )
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert result["safe_failure"]["searched"] == [
        "QTLMappingService.get_traits",
        "QTLMappingService.get_gwas_results",
    ]
    assert result["safe_failure"]["missing"] == ["single authoritative genomics trait"]
    assert result["safe_failure"]["next_steps"] == [
        "Retry with the exact trait name used in QTL or GWAS records.",
        "Ask for available genomics traits before requesting markers.",
    ]
    assert result["retrieval_audit"]["services"] == ["QTLMappingService.get_traits"]
    assert result["retrieval_audit"]["tables"] == ["BioQTL", "GWASResult", "GWASRun"]
    assert result["retrieval_audit"]["entities"] == {
        "requested_trait": "unknown resistance",
        "candidate_traits": [],
    }
    assert result["retrieval_audit"]["scope"] == {"organization_id": 1}
    assert result["plan_execution_summary"]["missing_domains"] == ["genomics"]
    genomics_step = result["plan_execution_summary"]["steps"][0]
    assert genomics_step["status"] == "missing"
    assert genomics_step["missing_reason"] == "the requested trait did not resolve to one authoritative genomics trait"
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_joined_plan_and_contract_metadata(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "trait": {"id": "trait-1", "name": "Yield"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            }
        ]

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Yield"}]

    async def fake_seedlot_search(**kwargs):
        return []

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.seedlot_search_service.search",
        fake_seedlot_search,
    )

    weather_service = WeatherServiceStub()
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchStub(),
        weather_service=weather_service,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which wheat varieties performed best in trials at Ludhiana under current weather?",
            "crop": "wheat",
            "trait": "yield",
            "location": "Ludhiana",
            "germplasm": "IR64",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "cross_domain_results"
    assert result["response_contract_version"] == CROSS_DOMAIN_QUERY_CONTRACT_VERSION
    assert result["trust_surface"] == CROSS_DOMAIN_QUERY_TRUST_SURFACE
    assert result["data_source"] == "database_and_weather_service"
    assert result["schema_version"] == "1"
    assert result["data"]["summary"]["weather_count"] == 1
    assert result["data"]["results"]["weather"]["summary"]
    assert result["calculation_method_refs"] == []
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert "joined_breeding_trial_environment" in {
        insight["type"] for insight in result["data"]["results"]["cross_domain_insights"]
    }
    assert "db:germplasm:IR64" in result["evidence_refs"]
    assert "db:trial:TRIAL-1" in result["evidence_refs"]
    assert "fn:weather.forecast" in result["evidence_refs"]
    assert weather_service.calls == [
        {
            "location_id": "LOC-1",
            "location_name": "Ludhiana",
            "days": 7,
            "crop": "wheat",
            "lat": 30.9010,
            "lon": 75.8573,
            "allow_generated_fallback": False,
        }
    ]
    assert result["calculation_ids"] == ["calc:cross_domain:join"]
    assert result["plan_execution_summary"]["is_compound"] is True
    assert result["plan_execution_summary"]["total_steps"] == len(
        result["plan_execution_summary"]["steps"]
    )
    assert "weather" in result["plan_execution_summary"]["domains_involved"]
    breeding_step = next(
        step for step in result["plan_execution_summary"]["steps"] if step["domain"] == "breeding"
    )
    trials_step = next(
        step for step in result["plan_execution_summary"]["steps"] if step["domain"] == "trials"
    )
    weather_step = next(
        step for step in result["plan_execution_summary"]["steps"] if step["domain"] == "weather"
    )
    analytics_step = next(
        step for step in result["plan_execution_summary"]["steps"] if step["domain"] == "analytics"
    )
    assert breeding_step["status"] == "completed"
    assert set(breeding_step["actual_outputs"]) >= {"traits", "germplasm", "observations"}
    assert breeding_step["output_counts"]["germplasm"] == 1
    assert breeding_step["output_entity_ids"]["germplasm"] == ["IR64"]
    assert "germplasm_search_service.search" in breeding_step["services"]
    assert trials_step["status"] == "completed"
    assert trials_step["output_counts"]["trials"] == 1
    assert trials_step["output_entity_ids"]["trials"] == ["TRIAL-1"]
    assert weather_step["status"] == "completed"
    assert set(weather_step["actual_outputs"]) >= {"locations", "weather"}
    assert weather_step["output_counts"]["weather"] == 1
    assert weather_step["output_metadata"]["weather_source"] == "live_provider"
    assert "weather_service.get_forecast" in weather_step["services"]
    assert analytics_step["status"] == "completed"
    assert "joined_breeding_trial_environment" in analytics_step["output_entity_ids"]["insights"]
    assert set(result["retrieval_audit"]["tables"]) >= {
        "Germplasm",
        "Location",
        "Observation",
        "ObservationVariable",
        "Trait",
        "Trial",
    }
    assert set(result["retrieval_audit"]["entities"]["resolved_domains"]) >= {
        "breeding",
        "trials",
        "weather",
    }
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == ["IR64"]
    assert result["retrieval_audit"]["entities"]["resolved_trial_ids"] == ["TRIAL-1"]
    assert result["retrieval_audit"]["entities"]["resolved_observation_ids"] == ["OBS-1"]
    assert result["retrieval_audit"]["entities"]["resolved_location_ids"] == ["LOC-1"]
    assert result["retrieval_audit"]["entities"]["resolved_weather_location_id"] == "LOC-1"
    assert result["retrieval_audit"]["entities"]["weather_coordinates_used"] is True
    assert result["retrieval_audit"]["entities"]["weather_data_source"] == "live_provider"
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]
    assert result["data"]["results"]["weather"]["source"] == "live_provider"


@pytest.mark.asyncio
async def test_cross_domain_query_returns_multi_domain_recommendations(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "trait": {"id": "trait-1", "name": "Yield"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            }
        ]

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Yield"}]

    async def fake_seedlot_search(**kwargs):
        return []

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.seedlot_search_service.search",
        fake_seedlot_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchStub(),
        weather_service=WeatherServiceStub(),
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Recommend a wheat variety from trials at Ludhiana under current weather",
            "crop": "wheat",
            "trait": "yield",
            "location": "Ludhiana",
            "germplasm": "IR64",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "cross_domain_results"
    assert result["data"]["summary"]["recommendation_count"] == 1
    assert result["data"]["recommendations"][0]["candidate"] == "IR64"
    assert result["data"]["recommendations"][0]["score"] >= 0.8
    assert "db:germplasm:IR64" in result["data"]["recommendations"][0]["evidence_refs"]
    assert "db:trial:TRIAL-1" in result["data"]["recommendations"][0]["evidence_refs"]
    assert "fn:weather.forecast" in result["data"]["recommendations"][0]["evidence_refs"]
    assert result["calculation_method_refs"] == ["fn:cross_domain_recommendation_ranker"]
    assert "multi_domain_recommendation" in {
        insight["type"] for insight in result["data"]["results"]["cross_domain_insights"]
    }
    analytics_step = next(
        step for step in result["plan_execution_summary"]["steps"] if step["domain"] == "analytics"
    )
    assert analytics_step["status"] == "completed"
    assert "recommendations" in analytics_step["actual_outputs"]
    assert analytics_step["output_counts"]["recommendations"] == 1
    assert analytics_step["output_entity_ids"]["recommendations"] == ["IR64"]
    assert analytics_step["compute_methods"] == ["fn:cross_domain_recommendation_ranker"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_safe_failure_when_requested_domain_missing(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return []

    async def fake_seedlot_search(**kwargs):
        return []

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.seedlot_search_service.search",
        fake_seedlot_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchStub(),
        weather_service=None,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which wheat varieties performed best in trials at Ludhiana under current weather?",
            "crop": "wheat",
            "location": "Ludhiana",
            "germplasm": "IR64",
        },
    )

    assert result["success"] is False
    assert result["error"] == "Cross-domain query could not retrieve requested domains: weather"
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert "weather" in result["plan_execution_summary"]["missing_domains"]
    assert result["plan_execution_summary"]["total_steps"] == len(
        result["plan_execution_summary"]["steps"]
    )
    weather_step = next(
        step for step in result["plan_execution_summary"]["steps"] if step["domain"] == "weather"
    )
    assert weather_step["status"] == "missing"
    assert weather_step["missing_reason"] == "weather service is unavailable"
    assert weather_step["actual_outputs"] == ["locations"]
    assert weather_step["output_counts"]["locations"] == 1
    assert weather_step["output_entity_ids"]["locations"] == ["LOC-1"]
    assert "weather_service.get_forecast" in weather_step["services"]
    assert set(result["retrieval_audit"]["tables"]) >= {"Germplasm", "Location", "Trial"}
    assert set(result["retrieval_audit"]["entities"]["resolved_domains"]) >= {"breeding", "trials"}
    assert result["retrieval_audit"]["entities"]["missing_domains"] == ["weather"]
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == ["IR64"]
    assert result["retrieval_audit"]["entities"]["resolved_trial_ids"] == ["TRIAL-1"]
    assert result["retrieval_audit"]["entities"]["resolved_location_ids"] == ["LOC-1"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_joined_breeding_trial_results_without_weather(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "trait": {"id": "trait-1", "name": "Yield"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            }
        ]

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Yield"}]

    async def fake_seedlot_search(**kwargs):
        return []

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.seedlot_search_service.search",
        fake_seedlot_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchStub(),
        weather_service=None,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which wheat varieties performed best in trials at Ludhiana?",
            "crop": "wheat",
            "trait": "yield",
            "location": "Ludhiana",
            "germplasm": "IR64",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "cross_domain_results"
    assert result["response_contract_version"] == CROSS_DOMAIN_QUERY_CONTRACT_VERSION
    assert result["trust_surface"] == CROSS_DOMAIN_QUERY_TRUST_SURFACE
    assert result["data_source"] == "database_and_weather_service"
    assert result["schema_version"] == "1"
    assert result["data"]["summary"]["weather_count"] == 0
    assert result["data"]["summary"]["trial_count"] == 1
    assert result["data"]["summary"]["germplasm_count"] == 1
    assert "db:germplasm:IR64" in result["evidence_refs"]
    assert "db:trial:TRIAL-1" in result["evidence_refs"]
    assert "fn:weather.forecast" not in result["evidence_refs"]
    assert result["calculation_ids"] == ["calc:cross_domain:join"]
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert len(result["evidence_envelope"]["claims"]) == 2
    assert result["evidence_envelope"]["calculation_steps"][0]["step_id"] == "calc:cross_domain:join"
    assert result["plan_execution_summary"]["is_compound"] is True
    assert "trials" in result["plan_execution_summary"]["domains_involved"]
    assert "breeding" in result["plan_execution_summary"]["domains_involved"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_safe_failure_when_weather_location_has_no_coordinates(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "trait": {"id": "trait-1", "name": "Yield"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            }
        ]

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Yield"}]

    async def fake_seedlot_search(**kwargs):
        return []

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.seedlot_search_service.search",
        fake_seedlot_search,
    )

    weather_service = WeatherServiceStub()
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchWithoutCoordinatesStub(),
        weather_service=weather_service,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which wheat varieties performed best in trials at Ludhiana under current weather?",
            "crop": "wheat",
            "trait": "yield",
            "location": "Ludhiana",
            "germplasm": "IR64",
        },
    )

    assert result["success"] is False
    assert result["error"] == "Cross-domain query could not retrieve requested domains: weather"
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert result["safe_failure"]["missing_context"] == [
        {
            "domain": "weather",
            "location_query": "Ludhiana",
            "reason": "resolved location has no stored coordinates",
        }
    ]
    assert "weather_location_coordinate_resolution" in result["safe_failure"]["searched"]
    assert result["safe_failure"]["next_steps"][0] == "Use a location with stored coordinates so REEVU can call the real weather provider."
    assert weather_service.calls == []


@pytest.mark.asyncio
async def test_cross_domain_query_returns_safe_failure_when_weather_provider_fails(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "trait": {"id": "trait-1", "name": "Yield"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            }
        ]

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Yield"}]

    async def fake_seedlot_search(**kwargs):
        return []

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.seedlot_search_service.search",
        fake_seedlot_search,
    )

    weather_service = FailingWeatherServiceStub()
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchStub(),
        weather_service=weather_service,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which wheat varieties performed best in trials at Ludhiana under current weather?",
            "crop": "wheat",
            "trait": "yield",
            "location": "Ludhiana",
            "germplasm": "IR64",
        },
    )

    assert result["success"] is False
    assert result["error"] == "Cross-domain query could not retrieve requested domains: weather"
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert result["safe_failure"]["missing_context"] == [
        {
            "domain": "weather",
            "location_query": "Ludhiana",
            "reason": "weather provider request failed",
        }
    ]
    assert "weather_service.get_forecast" in result["safe_failure"]["searched"]
    assert result["safe_failure"]["next_steps"][0] == "Retry once the live weather provider is available for the resolved location."
    assert result["retrieval_audit"]["entities"]["weather_failure_reason"] == "weather provider request failed"
    assert weather_service.calls == [
        {
            "location_id": "LOC-1",
            "location_name": "Ludhiana",
            "days": 7,
            "crop": "wheat",
            "lat": 30.9010,
            "lon": 75.8573,
            "allow_generated_fallback": False,
        }
    ]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_joined_breeding_genomics_results(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return []

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Blast Resistance"}]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.get_qtl_mapping_service",
        lambda: QTLMappingStub(),
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=CrossDomainBreedingGenomicsSearchStub(),
        trial_search_service=None,
        location_search_service=None,
        weather_service=None,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which rice varieties have blast resistance markers?",
            "crop": "rice",
            "trait": "blast resistance",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "cross_domain_results"
    assert result["response_contract_version"] == CROSS_DOMAIN_QUERY_CONTRACT_VERSION
    assert result["trust_surface"] == CROSS_DOMAIN_QUERY_TRUST_SURFACE
    assert result["data_source"] == "database_and_weather_service"
    assert result["schema_version"] == "1"
    assert result["data"]["summary"]["trial_count"] == 0
    assert result["data"]["summary"]["genomics_qtl_count"] == 1
    assert result["data"]["summary"]["genomics_association_count"] == 1
    assert result["data"]["results"]["genomics"]["trait"] == "Blast Resistance"
    assert "joined_breeding_genomics" in {
        insight["type"] for insight in result["data"]["results"]["cross_domain_insights"]
    }
    assert "db:germplasm:IR64" in result["evidence_refs"]
    assert "db:qtl:qtl_blast_1" in result["evidence_refs"]
    assert "db:marker:M123" in result["evidence_refs"]
    assert result["calculation_ids"] == ["calc:cross_domain:join"]
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert len(result["evidence_envelope"]["claims"]) == 2
    assert any(ref["entity_id"] == "db:qtl:qtl_blast_1" for ref in result["evidence_envelope"]["evidence_refs"])
    assert any(ref["entity_id"] == "db:marker:M123" for ref in result["evidence_envelope"]["evidence_refs"])
    assert "genomics" in result["plan_execution_summary"]["domains_involved"]
    genomics_step = next(
        step for step in result["plan_execution_summary"]["steps"] if step["domain"] == "genomics"
    )
    assert genomics_step["status"] == "completed"
    assert set(genomics_step["actual_outputs"]) == {"qtls", "marker_associations"}
    assert genomics_step["output_counts"]["qtls"] == 1
    assert genomics_step["output_entity_ids"]["qtls"] == ["qtl_blast_1"]
    assert genomics_step["output_entity_ids"]["marker_associations"] == ["M123"]
    assert genomics_step["output_metadata"]["trait"] == "Blast Resistance"
    assert "QTLMappingService.get_traits" in genomics_step["services"]
    assert set(result["retrieval_audit"]["tables"]) >= {"BioQTL", "GWASResult", "Germplasm", "Trait"}
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == ["IR64"]
    assert result["retrieval_audit"]["entities"]["resolved_qtl_ids"] == ["qtl_blast_1"]
    assert result["retrieval_audit"]["entities"]["resolved_marker_ids"] == ["M123"]
    assert result["retrieval_audit"]["entities"]["matched_genomics_trait_candidates"] == ["Blast Resistance"]
    assert result["retrieval_audit"]["entities"]["resolved_genomics_trait"] == "Blast Resistance"


@pytest.mark.asyncio
async def test_cross_domain_query_returns_safe_failure_when_genomics_domain_missing(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return []

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Blast Resistance"}]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.get_qtl_mapping_service",
        lambda: QTLMappingStub(),
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=CrossDomainBreedingGenomicsSearchStub(),
        trial_search_service=None,
        location_search_service=None,
        weather_service=None,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which rice varieties have yield markers?",
            "crop": "rice",
            "trait": "yield",
        },
    )

    assert result["success"] is False
    assert result["error"] == "Cross-domain query could not retrieve requested domains: genomics"
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert "genomics" in result["plan_execution_summary"]["missing_domains"]
    assert "QTLMappingService.get_traits" in result["retrieval_audit"]["services"]
    assert result["retrieval_audit"]["entities"]["missing_domains"] == ["genomics"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_joined_germplasm_trait_protocol_results(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return []

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Yield"}]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=CrossDomainBreedingGenomicsSearchStub(),
        protocol_search_service=ProtocolSearchStub(),
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which rice germplasm support yield improvement under speed breeding protocols?",
            "crop": "rice",
            "trait": "yield",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "cross_domain_results"
    assert result["response_contract_version"] == CROSS_DOMAIN_QUERY_CONTRACT_VERSION
    assert result["trust_surface"] == CROSS_DOMAIN_QUERY_TRUST_SURFACE
    assert result["data_source"] == "database_and_weather_service"
    assert result["schema_version"] == "1"
    assert result["data"]["summary"]["germplasm_count"] == 1
    assert result["data"]["summary"]["trait_count"] == 1
    assert result["data"]["summary"]["protocol_count"] == 1
    assert "joined_germplasm_trait_protocol" in {
        insight["type"] for insight in result["data"]["results"]["cross_domain_insights"]
    }
    assert "db:germplasm:IR64" in result["evidence_refs"]
    assert "db:protocol:protocol-1" in result["evidence_refs"]
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert len(result["evidence_envelope"]["claims"]) == 2
    assert any(ref["entity_id"] == "db:protocol:protocol-1" for ref in result["evidence_envelope"]["evidence_refs"])
    assert "speed_breeding_service.get_protocols" in result["retrieval_audit"]["services"]
    assert set(result["retrieval_audit"]["tables"]) >= {"Germplasm", "Protocol", "Trait"}
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == ["IR64"]
    assert result["retrieval_audit"]["entities"]["resolved_protocol_ids"] == ["protocol-1"]
    assert result["retrieval_audit"]["entities"]["resolved_trait_ids"] == ["trait-1"]
    assert "protocols" in result["plan_execution_summary"]["domains_involved"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_safe_failure_when_protocol_domain_missing(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return []

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Yield"}]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=CrossDomainBreedingGenomicsSearchStub(),
        protocol_search_service=None,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Which rice germplasm support yield improvement under speed breeding protocols?",
            "crop": "rice",
            "trait": "yield",
        },
    )

    assert result["success"] is False
    assert result["error"] == "Cross-domain query services unavailable"
    assert "protocol_search_service" in result["safe_failure"]["missing"]
    assert result["retrieval_audit"]["entities"]["missing_runtime_services"] == ["protocol_search_service"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_joined_trial_phenotype_environment_results(monkeypatch):
    async def fake_observation_search(*, db, organization_id, query=None, trait=None, study_id=None, germplasm_id=None, date_from=None, date_to=None, limit=50):
        assert study_id == 11
        return [
            {
                "id": "obs-11",
                "observation_db_id": "OBS-T1",
                "value": "5.4",
                "trait": {"id": "trait-1", "name": "Yield"},
                "study": {"id": "11", "name": "Study 11"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            }
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.search",
        fake_observation_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=None,
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchStub(),
        weather_service=WeatherServiceStub(),
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Show phenotype observations from trials at Ludhiana under current weather",
            "location": "Ludhiana",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "cross_domain_results"
    assert result["response_contract_version"] == CROSS_DOMAIN_QUERY_CONTRACT_VERSION
    assert result["trust_surface"] == CROSS_DOMAIN_QUERY_TRUST_SURFACE
    assert result["data_source"] == "database_and_weather_service"
    assert result["schema_version"] == "1"
    assert result["data"]["summary"]["germplasm_count"] == 0
    assert result["data"]["summary"]["trial_count"] == 1
    assert result["data"]["summary"]["observation_count"] == 1
    assert result["data"]["summary"]["weather_count"] == 1
    assert "joined_trial_phenotype_environment" in {
        insight["type"] for insight in result["data"]["results"]["cross_domain_insights"]
    }
    assert "db:trial:TRIAL-1" in result["evidence_refs"]
    assert "db:observation:OBS-T1" in result["evidence_refs"]
    assert "fn:weather.forecast" in result["evidence_refs"]
    assert "observation_search_service.search" in result["retrieval_audit"]["services"]
    assert result["calculation_ids"] == ["calc:cross_domain:join"]
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert len(result["evidence_envelope"]["claims"]) == 2
    assert any(ref["entity_id"] == "db:observation:OBS-T1" for ref in result["evidence_envelope"]["evidence_refs"])
    assert any(ref["entity_id"] == "fn:weather.forecast" for ref in result["evidence_envelope"]["evidence_refs"])
    assert result["plan_execution_summary"]["is_compound"] is True
    assert set(result["retrieval_audit"]["tables"]) >= {
        "Location",
        "Observation",
        "ObservationVariable",
        "Trial",
    }
    assert set(result["retrieval_audit"]["entities"]["resolved_domains"]) >= {
        "breeding",
        "trials",
        "weather",
    }
    assert result["retrieval_audit"]["entities"]["resolved_trial_ids"] == ["TRIAL-1"]
    assert result["retrieval_audit"]["entities"]["resolved_observation_ids"] == ["OBS-T1"]
    assert result["retrieval_audit"]["entities"]["resolved_location_ids"] == ["LOC-1"]
    assert result["retrieval_audit"]["entities"]["resolved_study_ids"] == ["11"]


@pytest.mark.asyncio
async def test_cross_domain_query_infers_weather_location_from_trial_context(monkeypatch):
    async def fake_observation_search(*, db, organization_id, query=None, trait=None, study_id=None, germplasm_id=None, date_from=None, date_to=None, limit=50):
        assert study_id == 31
        return [
            {
                "id": "obs-31",
                "observation_db_id": "OBS-RICE-31",
                "value": "6.1",
                "trait": {"id": "trait-1", "name": "Grain Yield"},
                "study": {"id": "31", "name": "Rice Study 31"},
                "germplasm": {"id": "501", "name": "IR64", "accession": "IR64"},
            }
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.search",
        fake_observation_search,
    )

    weather_service = WeatherServiceStub()
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=None,
        trial_search_service=TrialPhenotypeWeatherInferenceStub(),
        location_search_service=LocationSearchStub(),
        weather_service=weather_service,
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Compare trial performance with phenotype observations and local weather for our current rice season",
            "crop": "rice",
        },
    )

    assert result["success"] is True
    assert result["data"]["summary"]["trial_count"] == 1
    assert result["data"]["summary"]["observation_count"] == 1
    assert result["data"]["summary"]["weather_count"] == 1
    assert "joined_trial_phenotype_environment" in {
        insight["type"] for insight in result["data"]["results"]["cross_domain_insights"]
    }
    assert weather_service.calls == [
        {
            "location_id": "LOC-1",
            "location_name": "IRRI Research Station",
            "days": 7,
            "crop": "rice",
            "lat": 30.9010,
            "lon": 75.8573,
            "allow_generated_fallback": False,
        }
    ]
    assert result["retrieval_audit"]["entities"]["inferred_location_query"] == "IRRI Research Station"
    assert result["retrieval_audit"]["entities"]["resolved_study_ids"] == ["31"]
    assert result["retrieval_audit"]["entities"]["resolved_location_ids"] == ["LOC-1"]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_safe_failure_when_trial_phenotype_missing(monkeypatch):
    async def fake_observation_search(*, db, organization_id, query=None, trait=None, study_id=None, germplasm_id=None, date_from=None, date_to=None, limit=50):
        return []

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.search",
        fake_observation_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=None,
        trial_search_service=CrossDomainTrialSearchStub(),
        location_search_service=LocationSearchStub(),
        weather_service=WeatherServiceStub(),
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Show phenotype observations from trials at Ludhiana under current weather",
            "location": "Ludhiana",
        },
    )

    assert result["success"] is False
    assert result["error"] == "Cross-domain query could not retrieve requested domains: breeding"
    assert result["safe_failure"]["error_category"] == "insufficient_retrieval_scope"
    assert "breeding" in result["plan_execution_summary"]["missing_domains"]


@pytest.mark.asyncio
async def test_calculate_breeding_value_gblup_uses_matrix_backed_compute(monkeypatch):
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    captured: dict[str, object] = {}

    def fake_compute_gblup(*, genotypes, phenotypes, heritability):
        captured["genotypes_shape"] = tuple(genotypes.shape)
        captured["phenotypes_shape"] = tuple(phenotypes.shape)
        captured["heritability"] = heritability
        from app.services.compute_engine import BLUPResult
        import numpy as np

        return BLUPResult(
            fixed_effects=np.array([2.5]),
            breeding_values=np.array([0.45, 0.12]),
            reliability=np.array([0.91, 0.73]),
            genetic_variance=0.11,
            error_variance=0.04,
            converged=True,
        )

    monkeypatch.setattr("app.modules.ai.services.tools.compute_engine.compute_gblup", fake_compute_gblup)

    result = await executor.execute(
        "calculate_breeding_value",
        {
            "organization_id": 1,
            "trait": "yield",
            "method": "GBLUP",
            "germplasm_ids": ["IR64", "Swarna"],
            "phenotypes": [4.2, 5.1],
            "genotype_matrix": [[0, 1, 2], [2, 1, 0]],
            "heritability": 0.45,
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "breeding_values"
    assert result["response_contract_version"] == "compute.v1"
    assert result["trust_surface"] == "compute_contract"
    assert captured["genotypes_shape"] == (2, 3)
    assert captured["phenotypes_shape"] == (2,)
    assert captured["heritability"] == 0.45
    assert result["data"][0]["candidate"] == "IR64"
    assert result["data"][0]["score"] == 0.45
    assert result["message"] == "Calculated deterministic GBLUP breeding values for trait 'yield' across the resolved training population."
    assert result["summary"] == {
        "method": "GBLUP",
        "trait": "yield",
        "n_individuals": 2,
        "n_markers": 3,
        "heritability": 0.45,
        "genetic_variance": 0.11,
        "error_variance": 0.04,
        "converged": True,
    }
    assert result["evidence_refs"] == ["fn:compute.gblup"]
    assert result["calculation_ids"] == ["fn:compute.gblup"]
    assert result["calculation_method_refs"] == ["fn:compute.gblup"]
    assert result["evidence_envelope"]["routine"] == "gblup"
    assert result["evidence_envelope"]["claims"] == [
        "GBLUP breeding values were computed deterministically for trait 'yield'."
    ]
    assert result["evidence_envelope"]["calculations"][0]["step_id"] == "fn:compute.gblup"
    assert result["evidence_envelope"]["calculations"][0]["inputs"]["n_individuals"] == 2
    assert result["evidence_envelope"]["calculations"][0]["inputs"]["n_markers"] == 3
    assert result["confidence_score"] == 0.82
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["retrieval_audit"]["services"] == ["compute_engine.compute_gblup"]
    assert result["retrieval_audit"]["tables"] == []
    assert result["retrieval_audit"]["entities"] == {
        "trait": "yield",
        "method": "GBLUP",
        "crop": None,
        "germplasm_ids": ["IR64", "Swarna"],
        "study_id": None,
        "n_individuals": 2,
        "n_markers": 3,
    }
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "execution_mode": "matrix_backed_compute",
    }
    assert result["plan_execution_summary"]["domains_involved"] == ["genomics", "analytics"]
    compute_step = result["plan_execution_summary"]["steps"][0]
    assert compute_step["status"] == "completed"
    assert compute_step["actual_outputs"] == ["breeding_values"]
    assert compute_step["output_counts"]["breeding_values"] == 2
    assert compute_step["output_counts"]["n_individuals"] == 2
    assert compute_step["output_entity_ids"]["breeding_values"] == ["IR64", "Swarna"]
    assert compute_step["compute_methods"] == ["fn:compute.gblup"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_calculate_breeding_value_gblup_resolves_database_training_population(monkeypatch):
    executor = FunctionExecutor(
        db=SimpleNamespace(execute=object()),
        germplasm_search_service=GermplasmSearchStub(),
    )

    async def fake_resolve_database_backed_gblup_inputs(**kwargs):
        assert kwargs["organization_id"] == 1
        assert kwargs["trait"] == "yield"
        assert kwargs["crop"] == "wheat"
        return {
            "success": True,
            "phenotype_values": [58.675, 55.05, 56.125],
            "genotype_matrix": [
                [0.0, 1.0, 2.0, 0.0, 1.0],
                [1.0, 1.0, 0.0, 2.0, 0.0],
                [2.0, 0.0, 1.0, 0.0, 2.0],
            ],
            "germplasm_labels": ["HD2967", "PBW343", "Kalyan Sona"],
            "retrieval_audit": {
                "services": [
                    "calculate_breeding_value.database_training_population.observations",
                    "calculate_breeding_value.database_training_population.genotypes",
                ],
                "tables": [
                    "Observation",
                    "ObservationVariable",
                    "Germplasm",
                    "Study",
                    "Trial",
                    "CallSet",
                    "Call",
                    "Variant",
                ],
                "entities": {
                    "trait": "yield",
                    "method": "GBLUP",
                    "crop": "wheat",
                    "resolved_germplasm_ids": ["HD2967", "PBW343", "Kalyan Sona"],
                    "observation_count": 6,
                    "n_markers": 5,
                },
                "scope": {
                    "organization_id": 1,
                    "execution_mode": "database_training_population_gblup",
                },
            },
        }

    captured: dict[str, object] = {}

    def fake_compute_gblup(*, genotypes, phenotypes, heritability):
        captured["genotypes_shape"] = tuple(genotypes.shape)
        captured["phenotypes_shape"] = tuple(phenotypes.shape)
        captured["heritability"] = heritability
        from app.services.compute_engine import BLUPResult
        import numpy as np

        return BLUPResult(
            fixed_effects=np.array([56.62]),
            breeding_values=np.array([0.42, -0.11, 0.18]),
            reliability=np.array([0.88, 0.61, 0.74]),
            genetic_variance=0.19,
            error_variance=0.08,
            converged=True,
        )

    monkeypatch.setattr(
        "app.modules.ai.services.tools._resolve_database_backed_gblup_inputs",
        fake_resolve_database_backed_gblup_inputs,
    )
    monkeypatch.setattr("app.modules.ai.services.tools.compute_engine.compute_gblup", fake_compute_gblup)

    result = await executor.execute(
        "calculate_breeding_value",
        {
            "organization_id": 1,
            "trait": "yield",
            "method": "GBLUP",
            "crop": "wheat",
        },
    )

    assert result["success"] is True
    assert result["response_contract_version"] == "compute.v1"
    assert result["trust_surface"] == "compute_contract"
    assert captured["genotypes_shape"] == (3, 5)
    assert captured["phenotypes_shape"] == (3,)
    assert captured["heritability"] == 0.3
    assert result["message"] == "Calculated deterministic GBLUP breeding values for trait 'yield' across the resolved training population."
    assert result["data"][0]["candidate"] == "HD2967"
    assert result["summary"] == {
        "method": "GBLUP",
        "trait": "yield",
        "n_individuals": 3,
        "n_markers": 5,
        "heritability": 0.3,
        "genetic_variance": 0.19,
        "error_variance": 0.08,
        "converged": True,
    }
    assert result["evidence_refs"] == ["fn:compute.gblup"]
    assert result["calculation_ids"] == ["fn:compute.gblup"]
    assert result["calculation_method_refs"] == ["fn:compute.gblup"]
    assert result["confidence_score"] == 0.74
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["evidence_envelope"]["routine"] == "gblup"
    assert result["evidence_envelope"]["claims"] == [
        "GBLUP breeding values were computed deterministically for trait 'yield'."
    ]
    assert result["evidence_envelope"]["calculations"][0]["step_id"] == "fn:compute.gblup"
    assert result["evidence_envelope"]["calculations"][0]["inputs"]["n_individuals"] == 3
    assert result["evidence_envelope"]["calculations"][0]["inputs"]["n_markers"] == 5
    assert result["retrieval_audit"]["scope"]["execution_mode"] == "database_training_population_gblup"
    assert result["retrieval_audit"]["services"][-1] == "compute_engine.compute_gblup"
    assert result["retrieval_audit"]["tables"] == [
        "Observation",
        "ObservationVariable",
        "Germplasm",
        "Study",
        "Trial",
        "CallSet",
        "Call",
        "Variant",
    ]
    assert result["retrieval_audit"]["entities"]["trait"] == "yield"
    assert result["retrieval_audit"]["entities"]["method"] == "GBLUP"
    assert result["retrieval_audit"]["entities"]["crop"] == "wheat"
    assert result["retrieval_audit"]["entities"]["resolved_germplasm_ids"] == ["HD2967", "PBW343", "Kalyan Sona"]
    assert result["retrieval_audit"]["entities"]["observation_count"] == 6
    assert result["retrieval_audit"]["entities"]["n_markers"] == 5
    assert result["retrieval_audit"]["entities"]["n_individuals"] == 3
    assert result["plan_execution_summary"]["steps"][0]["output_entity_ids"]["breeding_values"] == [
        "HD2967",
        "Kalyan Sona",
        "PBW343",
    ]
    assert result["plan_execution_summary"]["steps"][0]["output_counts"]["n_individuals"] == 3
    assert result["plan_execution_summary"]["steps"][0]["compute_methods"] == ["fn:compute.gblup"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_calculate_breeding_value_blup_from_database_emits_retrieval_audit(monkeypatch):
    async def fake_observation_search(*, db, organization_id, query=None, trait=None, study_id=None, germplasm_id=None, date_from=None, date_to=None, limit=50):
        assert organization_id == 1
        assert trait == "yield"
        return [
            {
                "id": "obs-1",
                "value": "4.2",
                "germplasm": {"id": "101", "name": "IR64"},
            },
            {
                "id": "obs-2",
                "value": "5.1",
                "germplasm": {"id": "102", "name": "Swarna"},
            },
            {
                "id": "obs-3",
                "value": "4.7",
                "germplasm": {"id": "103", "name": "MTU1010"},
            },
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.search",
        fake_observation_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
        breeding_value_service=BreedingValueService(),
    )

    result = await executor.execute(
        "calculate_breeding_value",
        {
            "organization_id": 1,
            "trait": "yield",
            "method": "BLUP",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "breeding_values"
    assert result["message"] == "Calculated heuristic BLUP breeding values for 3 individuals on trait 'yield' from 3 database observations."
    assert result["response_contract_version"] == "compute.v1"
    assert result["trust_surface"] == "compute_contract"
    assert result["calculation_method_refs"] == ["fn:calculate_breeding_value.blup_heuristic"]
    assert result["evidence_refs"] == [
        "db:observation:obs-1",
        "db:observation:obs-2",
        "db:observation:obs-3",
        "fn:calculate_breeding_value.blup_heuristic",
    ]
    assert result["calculation_ids"] == ["fn:calculate_breeding_value.blup_heuristic"]
    assert result["confidence_score"] == 0.09
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["evidence_envelope"]["routine"] == "blup_heuristic"
    assert result["evidence_envelope"]["claims"] == [
        "Heuristic BLUP breeding values were estimated deterministically for trait 'yield' from 3 database observations."
    ]
    assert result["evidence_envelope"]["calculations"] == [
        {
            "step_id": "fn:calculate_breeding_value.blup_heuristic",
            "formula": "EBV = h^2 x (phenotype - mean)",
            "inputs": {
                "trait": "yield",
                "heritability": 0.3,
                "n_observations": 3,
                "n_individuals": 3,
            },
        }
    ]
    assert result["retrieval_audit"]["services"] == [
        "observation_search_service.search",
        "breeding_value_service.estimate_blup",
    ]
    assert result["retrieval_audit"]["entities"]["trait"] == "yield"
    assert result["retrieval_audit"]["entities"]["method"] == "BLUP"
    assert result["retrieval_audit"]["entities"]["observation_count"] == 3
    assert result["plan_execution_summary"]["domains_involved"] == ["analytics"]
    compute_step = result["plan_execution_summary"]["steps"][0]
    assert compute_step["status"] == "completed"
    assert compute_step["actual_outputs"] == ["breeding_values"]
    assert compute_step["output_counts"]["breeding_values"] == 3
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_calculate_breeding_value_gblup_returns_safe_failure_without_matrix_inputs():
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    result = await executor.execute(
        "calculate_breeding_value",
        {
            "organization_id": 1,
            "trait": "yield",
            "method": "GBLUP",
            "germplasm_ids": ["IR64", "Swarna"],
        },
    )

    assert result["success"] is False
    assert result["error"] == "GBLUP requires genotype_matrix or g_matrix together with phenotypes"
    assert result["message"] == (
        "Matrix-backed deterministic GBLUP inputs are required; REEVU will not silently substitute BLUP."
    )
    assert result["safe_failure"]["error_category"] == "insufficient_compute_inputs"
    assert result["safe_failure"]["missing_inputs"] == [
        "phenotypes",
        "genotype_matrix or g_matrix",
    ]
    assert result["safe_failure"]["required_inputs"] == [
        "phenotypes",
        "genotype_matrix or g_matrix",
    ]
    assert result["response_contract_version"] == "compute.v1"
    assert result["trust_surface"] == "compute_contract"
    assert result["calculation_method_refs"] == ["fn:compute.gblup"]
    assert result["retrieval_audit"]["services"] == ["calculate_breeding_value.input_validation"]
    assert result["retrieval_audit"]["tables"] == []
    assert result["retrieval_audit"]["entities"] == {
        "trait": "yield",
        "method": "GBLUP",
        "germplasm_ids": ["IR64", "Swarna"],
        "study_id": None,
    }
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "missing_inputs": ["phenotypes", "genotype_matrix or g_matrix"],
    }
    assert result["plan_execution_summary"]["missing_domains"] == ["analytics"]
    compute_step = result["plan_execution_summary"]["steps"][0]
    assert compute_step["status"] == "missing"
    assert compute_step["compute_methods"] == ["fn:compute.gblup"]
    assert compute_step["output_metadata"]["missing_inputs"] == ["phenotypes", "genotype_matrix or g_matrix"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


def test_germplasm_confidence_higher_with_enriched_metadata_and_observations():
    rich_confidence = _derive_germplasm_confidence(
        {
            "id": "101",
            "accession": "IR64",
            "species": "Oryza sativa",
            "origin": "IN",
            "traits": ["yield"],
        },
        [{"observation_db_id": "OBS-1"}],
    )
    sparse_confidence = _derive_germplasm_confidence(
        {"id": "101"},
        [],
    )

    assert rich_confidence == 0.95
    assert sparse_confidence == 0.35
    assert rich_confidence > sparse_confidence


@pytest.mark.asyncio
async def test_get_germplasm_details_resolves_query_and_returns_contract_metadata(monkeypatch):
    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=100):
        return [
            {
                "id": "obs-1",
                "observation_db_id": "OBS-1",
                "value": "4.0",
                "observation_time_stamp": "2026-03-20T00:00:00+00:00",
                "trait": {"name": "Yield", "trait_name": "Yield", "scale": "t/ha", "data_type": "numeric"},
                "germplasm": {"id": "101", "name": "IR64", "accession": "IR64"},
            },
        ]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    result = await executor.execute(
        "get_germplasm_details",
        {"organization_id": 1, "query": "IR64"},
    )

    assert result["success"] is True
    assert result["result_type"] == "germplasm_details"
    assert result["response_contract_version"] == GERMPLASM_LOOKUP_CONTRACT_VERSION
    assert result["trust_surface"] == GERMPLASM_LOOKUP_TRUST_SURFACE
    assert result["data_source"] == "database"
    assert result["schema_version"] == "1"
    assert result["confidence_score"] == 0.95
    assert result["data_age_seconds"] is not None
    assert result["evidence_refs"] == ["db:germplasm:IR64", "db:observation:OBS-1"]
    assert result["data"]["message"] == "Germplasm 'IR64' with 1 observations"
    assert result["data"]["germplasm"]["species"] == "Oryza sativa"
    assert result["data"]["observation_count"] == 1
    assert result["evidence_envelope"]["claims"] == [
        "Germplasm 'IR64' was retrieved from database-backed search.",
        "Linked observation count: 1",
    ]
    evidence_refs = result["evidence_envelope"]["evidence_refs"]
    assert len(evidence_refs) == 2
    assert evidence_refs[0]["source_type"] == "database"
    assert evidence_refs[0]["entity_id"] == "db:germplasm:IR64"
    assert evidence_refs[0]["query_or_method"] == "germplasm_search_service.get_by_id"
    assert evidence_refs[0]["freshness_seconds"] is None
    assert evidence_refs[0]["retrieved_at"]
    assert evidence_refs[1]["source_type"] == "database"
    assert evidence_refs[1]["entity_id"] == "db:observation:OBS-1"
    assert evidence_refs[1]["query_or_method"] == "observation_search_service.get_by_germplasm"
    assert evidence_refs[1]["freshness_seconds"] == float(result["data_age_seconds"])
    assert evidence_refs[1]["retrieved_at"]
    assert result["evidence_envelope"]["calculations"] == []
    assert result["evidence_envelope"]["uncertainty"]["confidence"] == 0.95
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["retrieval_audit"]["entities"]["germplasm_accession"] == "IR64"
    assert result["retrieval_audit"]["services"] == [
        "germplasm_search_service.get_by_id",
        "observation_search_service.get_by_germplasm",
    ]
    assert result["retrieval_audit"]["tables"] == ["Germplasm", "Observation", "ObservationVariable"]
    assert result["retrieval_audit"]["scope"] == {"organization_id": 1, "query": "IR64"}
    assert result["plan_execution_summary"]["domains_involved"] == ["breeding"]
    assert result["plan_execution_summary"]["metadata"]["contract_function"] == "get_germplasm_details"
    germplasm_step = result["plan_execution_summary"]["steps"][0]
    assert germplasm_step["status"] == "completed"
    assert set(germplasm_step["actual_outputs"]) == {"germplasm", "observations"}
    assert germplasm_step["output_counts"]["germplasm"] == 1
    assert germplasm_step["output_counts"]["observations"] == 1
    assert germplasm_step["output_entity_ids"]["germplasm"] == ["IR64"]
    assert germplasm_step["output_entity_ids"]["observations"] == ["OBS-1"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_germplasm_details_returns_safe_failure_for_ambiguous_query():
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=GermplasmSearchStub(),
    )

    result = await executor.execute(
        "get_germplasm_details",
        {"organization_id": 1, "query": "ambiguous"},
    )

    assert result["success"] is False
    assert result["error"] == "Ambiguous germplasm query"
    assert result["message"] == (
        "Multiple germplasm records matched 'ambiguous'. Please choose one explicit accession."
    )
    assert result["safe_failure"]["error_category"] == "ambiguous_retrieval_scope"
    assert result["safe_failure"]["searched"] == ["germplasm_lookup", "germplasm_search_service"]
    assert result["safe_failure"]["missing"] == ["single authoritative germplasm match"]
    assert result["safe_failure"]["next_steps"] == [
        "Retry with the exact accession or internal germplasm ID.",
        "Add more identifying context such as species or origin.",
    ]
    assert len(result["candidates"]) == 2
    assert result["retrieval_audit"]["services"] == ["germplasm_search_service.search"]
    assert result["retrieval_audit"]["tables"] == ["Germplasm"]
    assert result["retrieval_audit"]["entities"]["match_count"] == 2
    assert result["retrieval_audit"]["entities"]["candidate_ids"] == ["101", "102"]
    assert result["retrieval_audit"]["scope"] == {"organization_id": 1}
    assert result["plan_execution_summary"]["missing_domains"] == ["breeding"]
    germplasm_step = result["plan_execution_summary"]["steps"][0]
    assert germplasm_step["status"] == "missing"
    assert germplasm_step["actual_outputs"] == ["candidate_matches"]
    assert germplasm_step["output_counts"]["candidate_matches"] == 2
    assert germplasm_step["output_entity_ids"]["candidate_matches"] == ["101", "102"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_trial_results_includes_interpretation(monkeypatch):
    async def fake_get_trial_summary(trial_id, db, organization_id):
        return SimpleNamespace(
            model_dump=lambda mode="json": {
                "trial": {"trialDbId": "TRIAL-1", "trialName": "Yield Trial"},
                "topPerformers": [{"germplasmName": "Swarna", "yield_value": 5.1}],
                "traitSummary": [{"trait": "Yield", "mean": 4.65, "cv": 9.68}],
                "locationPerformance": [],
                "statistics": {"primary_trait": "Yield"},
                "interpretation": {
                    "contract_version": "phenotyping.interpretation.v1",
                    "ranking": [{"entity_name": "Swarna", "score": 5.1}],
                },
                "evidence_refs": ["db:trial:TRIAL-1", "db:observation:OBS-2"],
                "calculation_ids": ["calc:trial:yield_mean"],
                "response_contract_version": "trial_summary.response.v1",
                "trust_surface": "trial_summary",
                "data_source": "database",
                "schema_version": "1",
                "confidence_score": 0.91,
                "data_age_seconds": 3600,
                "calculation_method_refs": ["fn:trial_summary.mean"],
                "evidence_envelope": {
                    "claims": ["Yield Trial summary"],
                    "evidence_refs": [{"entity_id": "db:trial:TRIAL-1"}],
                    "calculation_steps": [{"step_id": "calc:trial:yield_mean"}],
                    "policy_flags": [],
                    "uncertainty": {"confidence": 0.91, "missing_data": []},
                },
            }
        )

    monkeypatch.setattr("app.modules.ai.services.tools.get_trial_summary", fake_get_trial_summary)

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        trial_search_service=TrialSearchStub(),
    )

    result = await executor.execute(
        "get_trial_results",
        {"organization_id": 1, "trial_id": "1"},
    )

    assert result["success"] is True
    assert result["result_type"] == "trial_results"
    assert result["data"]["interpretation"]["contract_version"] == "phenotyping.interpretation.v1"
    assert result["data"]["message"] == (
        "Trial 'Yield Trial' summary retrieved from database-backed trial surfaces."
    )
    assert result["data"]["top_performers"][0]["germplasmName"] == "Swarna"
    assert result["evidence_refs"]
    assert result["response_contract_version"] == TRIAL_SUMMARY_CONTRACT_VERSION
    assert result["trust_surface"] == TRIAL_SUMMARY_TRUST_SURFACE
    assert result["data_source"] == "database"
    assert result["schema_version"] == "1"
    assert result["confidence_score"] == 0.91
    assert result["data_age_seconds"] == 3600
    assert result["calculation_method_refs"] == ["fn:trial_summary.mean"]
    assert result["evidence_envelope"]["claims"] == ["Yield Trial summary"]
    assert result["evidence_envelope"]["uncertainty"]["confidence"] == 0.91
    assert result["confidence_score"] == result["evidence_envelope"]["uncertainty"]["confidence"]
    assert result["evidence_refs"] == ["db:trial:TRIAL-1", "db:observation:OBS-2"]
    assert result["evidence_envelope"]["evidence_refs"] == [{"entity_id": "db:trial:TRIAL-1"}]
    assert result["evidence_envelope"]["calculation_steps"] == [{"step_id": "calc:trial:yield_mean"}]
    assert result["calculation_ids"] == ["calc:trial:yield_mean"]
    assert result["retrieval_audit"]["services"] == ["app.api.v2.trial_summary.get_trial_summary"]
    assert result["retrieval_audit"]["tables"] == [
        "Trial",
        "Study",
        "Observation",
        "ObservationUnit",
        "ObservationVariable",
        "Germplasm",
        "Location",
    ]
    assert result["retrieval_audit"]["entities"]["trial_db_id"] == "TRIAL-1"
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "query": None,
        "crop": None,
        "season": None,
        "location": None,
    }
    assert result["plan_execution_summary"]["domains_involved"] == ["trials", "analytics"]
    trial_step = result["plan_execution_summary"]["steps"][0]
    assert trial_step["status"] == "completed"
    assert set(trial_step["actual_outputs"]) == {"trial", "top_performers", "trait_summary"}
    assert trial_step["output_counts"]["trial"] == 1
    assert trial_step["output_counts"]["top_performers"] == 1
    assert trial_step["output_counts"]["trait_summary"] == 1
    assert trial_step["output_entity_ids"]["trial"] == ["TRIAL-1"]
    assert trial_step["output_entity_ids"]["top_performers"] == ["Swarna"]
    assert trial_step["output_entity_ids"]["trait_summary"] == ["Yield"]
    assert trial_step["compute_methods"] == ["fn:trial_summary.mean"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_trial_results_returns_safe_failure_for_ambiguous_query():
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        trial_search_service=TrialSearchStub(),
    )

    result = await executor.execute(
        "get_trial_results",
        {"organization_id": 1, "query": "ambiguous"},
    )

    assert result["success"] is False
    assert result["error"] == "Ambiguous trial query"
    assert result["message"] == "Multiple trials matched 'ambiguous'. Please choose one explicit trial."
    assert result["safe_failure"]["error_category"] == "ambiguous_retrieval_scope"
    assert result["safe_failure"]["searched"] == ["trial_summary", "trial_search_service"]
    assert result["safe_failure"]["missing"] == ["single authoritative trial match"]
    assert result["safe_failure"]["next_steps"] == [
        "Retry with the exact trial ID.",
        "Specify the trial name more precisely.",
    ]
    assert len(result["candidates"]) == 2
    assert result["retrieval_audit"]["services"] == ["trial_search_service.search"]
    assert result["retrieval_audit"]["tables"] == ["Trial"]
    assert result["retrieval_audit"]["entities"] == {
        "query": "ambiguous",
        "match_count": 2,
        "candidate_ids": ["TRIAL-1", "TRIAL-2"],
    }
    assert result["retrieval_audit"]["scope"] == {
        "organization_id": 1,
        "crop": None,
        "season": None,
        "location": None,
    }
    assert result["plan_execution_summary"]["missing_domains"] == ["trials"]
    trial_step = result["plan_execution_summary"]["steps"][0]
    assert trial_step["status"] == "missing"
    assert trial_step["actual_outputs"] == ["candidate_matches"]
    assert trial_step["output_counts"]["candidate_matches"] == 2
    assert trial_step["output_entity_ids"]["candidate_matches"] == ["TRIAL-1", "TRIAL-2"]
    assert result["retrieval_audit"]["plan"] == result["plan_execution_summary"]


@pytest.mark.asyncio
async def test_get_trial_results_forwards_lookup_filters(monkeypatch):
    async def fake_get_trial_summary(trial_id, db, organization_id):
        return SimpleNamespace(
            model_dump=lambda mode="json": {
                "trial": {"trialDbId": "TRIAL-1", "trialName": "Wheat Trial"},
                "topPerformers": [],
                "traitSummary": [],
                "locationPerformance": [],
                "statistics": {},
                "interpretation": {},
                "evidence_refs": ["db:trial:TRIAL-1"],
                "calculation_ids": [],
                "response_contract_version": "trial_summary.response.v1",
                "trust_surface": "trial_summary",
                "data_source": "database",
                "schema_version": "1",
                "confidence_score": 0.9,
                "data_age_seconds": 60,
                "calculation_method_refs": [],
                "evidence_envelope": {
                    "claims": [],
                    "evidence_refs": [],
                    "calculation_steps": [],
                    "policy_flags": [],
                    "uncertainty": {"confidence": 0.9, "missing_data": []},
                },
            }
        )

    monkeypatch.setattr("app.modules.ai.services.tools.get_trial_summary", fake_get_trial_summary)

    trial_search_service = TrialSearchStub()
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        trial_search_service=trial_search_service,
    )

    result = await executor.execute(
        "get_trial_results",
        {"organization_id": 1, "query": "wheat trial", "crop": "wheat", "location": "Ludhiana"},
    )

    assert result["success"] is True
    assert trial_search_service.calls[0] == {
        "organization_id": 1,
        "query": "wheat trial",
        "crop": "wheat",
        "season": None,
        "location": "Ludhiana",
        "program": None,
    }
    assert result["retrieval_audit"]["scope"]["crop"] == "wheat"
    assert result["retrieval_audit"]["scope"]["location"] == "Ludhiana"


@pytest.mark.asyncio
async def test_get_trial_results_retries_generic_crop_query_without_text_filter(monkeypatch):
    async def fake_get_trial_summary(trial_id, db, organization_id):
        return SimpleNamespace(
            model_dump=lambda mode="json": {
                "trial": {"trialDbId": "TRIAL-9", "trialName": "Ludhiana Advanced Yield Trial 2025"},
                "topPerformers": [],
                "traitSummary": [],
                "locationPerformance": [],
                "statistics": {},
                "interpretation": {},
                "evidence_refs": ["db:trial:TRIAL-9"],
                "calculation_ids": [],
                "response_contract_version": "trial_summary.response.v1",
                "trust_surface": "trial_summary",
                "data_source": "database",
                "schema_version": "1",
                "confidence_score": 0.9,
                "data_age_seconds": 60,
                "calculation_method_refs": [],
                "evidence_envelope": {
                    "claims": [],
                    "evidence_refs": [],
                    "calculation_steps": [],
                    "policy_flags": [],
                    "uncertainty": {"confidence": 0.9, "missing_data": []},
                },
            }
        )

    class GenericCropFallbackTrialSearchStub(TrialSearchStub):
        async def search(
            self,
            db,
            organization_id,
            query=None,
            crop=None,
            season=None,
            location=None,
            program=None,
            limit=5,
        ):
            self.calls.append(
                {
                    "organization_id": organization_id,
                    "query": query,
                    "crop": crop,
                    "season": season,
                    "location": location,
                    "program": program,
                }
            )
            if query == "wheat trial":
                return []
            if query is None and crop == "wheat":
                return [
                    {
                        "id": "9",
                        "trial_db_id": "TRIAL-9",
                        "name": "Ludhiana Advanced Yield Trial 2025",
                    }
                ]
            return []

    monkeypatch.setattr("app.modules.ai.services.tools.get_trial_summary", fake_get_trial_summary)

    trial_search_service = GenericCropFallbackTrialSearchStub()
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        trial_search_service=trial_search_service,
    )

    result = await executor.execute(
        "get_trial_results",
        {"organization_id": 1, "query": "wheat trial", "crop": "wheat"},
    )

    assert result["success"] is True
    assert [call["query"] for call in trial_search_service.calls] == ["wheat trial", None]
    assert trial_search_service.calls[1]["crop"] == "wheat"
    assert result["retrieval_audit"]["entities"]["trial_db_id"] == "TRIAL-9"


@pytest.mark.asyncio
async def test_get_weather_forecast_uses_injected_weather_service():
    weather_service = WeatherServiceStub()
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        weather_service=weather_service,
    )

    result = await executor.execute(
        "get_weather_forecast",
        {
            "location": "LOC-1",
            "location_name": "Ludhiana",
            "days": 3,
            "crop": "wheat",
        },
    )

    assert result["success"] is True
    assert result["result_type"] == "weather_forecast"
    assert result["data"]["location"] == "Ludhiana"
    assert result["data"]["days"] == 3
    assert result["data"]["summary"] == "Heat risk may influence current field performance."
    assert result["data"]["alerts"] == ["heat_risk"]
    assert result["data"]["impacts_count"] == 1
    assert result["data"]["optimal_windows"][0]["activity"] == "selection_review"
    assert weather_service.calls == [
        {
            "location_id": "LOC-1",
            "location_name": "Ludhiana",
            "days": 3,
            "crop": "wheat",
            "lat": None,
            "lon": None,
            "allow_generated_fallback": True,
        }
    ]


@pytest.mark.asyncio
async def test_cross_domain_query_returns_joined_breeding_trial_results_for_trait_only_prompt(monkeypatch):
    class DroughtToleranceSearchStub:
        async def search(self, db, organization_id, query=None, trait=None, limit=20):
            if trait != "drought tolerance":
                return []
            return [
                {"id": "201", "name": "HD2967", "accession": "HD2967", "traits": ["drought tolerance"]},
                {"id": "202", "name": "PBW343", "accession": "PBW343", "traits": ["drought tolerance"]},
            ]

    async def fake_get_by_germplasm(db, organization_id, germplasm_id, limit=10):
        return [
            {
                "id": f"obs-{germplasm_id}",
                "observation_db_id": f"OBS-{germplasm_id}",
                "value": "4.6",
                "trait": {"id": "trait-1", "name": "Drought Tolerance"},
                "germplasm": {"id": str(germplasm_id), "name": "HD2967" if str(germplasm_id) == "201" else "PBW343"},
            }
        ]

    async def fake_trait_search(**kwargs):
        return [{"id": "trait-1", "name": "Drought Tolerance"}]

    monkeypatch.setattr(
        "app.modules.ai.services.tools.observation_search_service.get_by_germplasm",
        fake_get_by_germplasm,
    )
    monkeypatch.setattr(
        "app.modules.ai.services.tools.trait_search_service.search",
        fake_trait_search,
    )

    executor = FunctionExecutor(
        db=SimpleNamespace(),
        germplasm_search_service=DroughtToleranceSearchStub(),
        trial_search_service=CrossDomainTrialSearchStub(),
    )

    result = await executor.execute(
        "cross_domain_query",
        {
            "organization_id": 1,
            "query": "Compare breeding lines with the latest trial results for drought tolerance",
            "trait": "drought tolerance",
        },
    )

    assert result["success"] is True
    assert result["data"]["summary"]["trial_count"] == 1
    assert result["data"]["summary"]["recommendation_count"] == 0
    assert "joined_breeding_trial" in {
        insight["type"] for insight in result["data"]["results"]["cross_domain_insights"]
    }


@pytest.mark.asyncio
async def test_function_executor_rejects_disallowed_tool_before_dispatch():
    capability_registry = CapabilityRegistry(
        capability_overrides=["search_germplasm"],
    )
    executor = FunctionExecutor(
        db=SimpleNamespace(),
        capability_registry=capability_registry,
        trial_search_service=TrialSearchStub(),
    )

    with pytest.raises(FunctionExecutionError, match="not permitted"):
        await executor.execute("get_trial_results", {"organization_id": 1, "trial_id": "1"})
