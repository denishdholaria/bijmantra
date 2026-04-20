"""
Function Executor for Veena AI

Executes functions called by FunctionGemma.
Maps function names to actual API calls and database operations.

Interim maintenance note:
- Read TOOLS_MODULE_AGENT_INDEX before adding new behavior here.
- This file is oversized; continue REEVU through extraction-first slices instead of
    treating this module as the default landing zone for every new capability.

Per veena-critical-milestone.md:
- Veena must intelligently fetch real data from the database
- Veena must analyze that data correctly (not return canned responses)
- Veena must reason across domains
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.phenotype_comparison import (
    _build_phenotype_evidence_envelope,
    get_comparison_statistics,
)
from app.api.v2.trial_summary import get_trial_summary
from app.models.proposal import ActionType
from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.modules.ai.services.tool_analyze_handlers import (
    AnalyzeHandlerSharedContext,
    handle_analyze,
)
from app.modules.ai.services.tool_evidence_helpers import (
    _build_compute_evidence_envelope,
    _build_cross_domain_evidence_envelope,
    _build_genomics_evidence_envelope,
    _build_germplasm_evidence_envelope,
    _derive_genomics_lookup_confidence,
    _derive_germplasm_confidence,
    _derive_germplasm_data_age_seconds,
)
from app.modules.ai.services.tool_plan_helpers import (
    _build_cross_domain_plan_execution_summary,
    _build_single_contract_plan_execution_summary,
    _with_plan_execution_summary,
)
from app.modules.ai.services.tool_query_helpers import (
    _dedupe_string_values,
    _get_germplasm_identifier,
    _resolve_trait_query,
    _sample_record_identifiers,
    _sample_scalar_values,
)
from app.modules.ai.services.tool_search_handlers import (
    SearchHandlerSharedContext,
    handle_search,
)
from app.modules.ai.services.tool_statistics_handlers import (
    StatisticsHandlerSharedContext,
    handle_statistics,
)
from app.modules.ai.services.tool_check_handlers import (
    CheckHandlerSharedContext,
    handle_check,
)
from app.modules.ai.services.tool_export_handlers import (
    ExportHandlerSharedContext,
    handle_export,
)
from app.modules.ai.services.tool_proposal_handlers import (
    ProposalHandlerSharedContext,
    handle_proposal,
)
from app.modules.ai.services.tool_compare_handlers import (
    CompareHandlerSharedContext,
    handle_compare,
)
from app.modules.ai.services.tool_cross_domain_handlers import (
    CrossDomainHandlerSharedContext,
    handle_cross_domain,
)
from app.modules.ai.services.tool_predict_handlers import (
    PredictHandlerSharedContext,
    handle_predict,
)
from app.modules.ai.services.tool_retrieval_helpers import (
    _build_cross_domain_retrieval_entities,
    _build_cross_domain_retrieval_tables,
)
from app.modules.environment.services.cross_domain_gdd_service import CrossDomainGDDService
from app.modules.ai.services.tool_calculate_handlers import (
    CalculateHandlerSharedContext,
    _build_gblup_compute_response,
    _build_gblup_input_safe_failure,
    _coerce_genotype_dosage,
    _normalize_training_population_label,
    _resolve_database_backed_gblup_inputs,
    handle_calculate,
)
from app.modules.ai.services.tool_get_handlers import GetHandlerSharedContext, handle_get
from app.modules.genomics.services.qtl_mapping_service import get_qtl_mapping_service
from app.modules.phenotyping.services.interpretation_service import (
    PhenotypeInterpretationRecord,
    phenotype_interpretation_service,
    safe_float,
)
from app.modules.phenotyping.services.observation_search_service import observation_search_service
from app.modules.germplasm.services.program_search_service import program_search_service
from app.modules.breeding.services.proposal_service import get_proposal_service
from app.modules.germplasm.services.seedlot_search_service import seedlot_search_service
from app.modules.phenotyping.services.trait_search_service import trait_search_service
from app.services.compute_engine import compute_engine

# Import services through dependency injection to avoid cross-domain imports
# These will be provided via constructor injection
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.breeding.services.cross_search_service import CrossSearchService
    from app.modules.breeding.services.trial_search_service import TrialSearchService
    from app.modules.breeding.services.breeding_value_service import BreedingValueService
    from app.modules.germplasm.services.search_service import GermplasmSearchService
    from app.modules.spatial.services.location_search_service import LocationSearchService
    from app.modules.environment.services.weather_service import WeatherService


logger = logging.getLogger(__name__)

TRIAL_PHENOTYPE_ENVIRONMENT_TOKENS: tuple[str, ...] = (
    "phenotype",
    "observation",
    "observations",
)
RECOMMENDATION_QUERY_TOKENS: tuple[str, ...] = (
    "recommend",
    "recommendation",
    "should i choose",
    "should we choose",
    "best option",
)
MIN_RECOMMENDATION_DOMAINS = 2
COMPUTE_CONTRACT_TRUST_SURFACE = "compute_contract"

# AI agents should read this index before adding behavior to this module.
TOOLS_MODULE_AGENT_INDEX = """
agent_index_version: 2026-04-03

purpose:
- Canonical REEVU function-execution compatibility surface.
- Holds shared helpers plus FunctionExecutor dispatch while extraction is still in progress.

current_decision:
- Do not pause REEVU for a broad all-at-once refactor.
- Do not keep growing this file as the default landing zone for new behavior.
- Continue REEVU through extraction-first slices: when a change is more than a small local fix,
    extract the touched handler family first and keep this file as a thin delegator.

module_map:
- Shared normalization, compute, provenance, retrieval-audit, and evidence helpers live above FunctionExecutor.
- Dispatch entrypoint: FunctionExecutor.execute
- Handler families: _handle_search, _handle_statistics, _handle_proposal, _handle_cross_domain_query,
    _handle_get, _handle_compare, _handle_calculate, _handle_analyze, _handle_predict,
    _handle_check, _handle_export, _handle_navigate

edit_rules:
- Acceptable direct edits: small bug fixes, contract metadata adjustments, safe-failure corrections,
    and trace or provenance fixes within one existing helper or one handler family.
- Extraction-first trigger: new capability, new handler family, cross-domain growth, or a change that
    adds substantial domain logic rather than a local fix.
- If a change touches more than one handler family or adds more than about 40 lines of new domain logic,
    stop and extract to sibling modules before continuing here.
- Keep FunctionExecutor moving toward thin orchestration, not permanent ownership of all tool behavior.

candidate_extraction_order:
- _handle_get family
- _handle_calculate family
- _handle_cross_domain_query helper cluster
- _handle_compare / _handle_analyze / _handle_predict families
- shared evidence, provenance, and retrieval-audit builders

hotspots:
- _handle_cross_domain_query
- _handle_get
- _handle_calculate
- shared evidence and provenance helper growth above FunctionExecutor
"""

# Calculate-family helpers now live in tool_calculate_handlers.py and are
# imported above to keep tools.py as a delegator while preserving the existing
# patch paths rooted at this module.


@dataclass(frozen=True)
class EnvelopeObservationRecord:
    id: str | None
    observation_db_id: str | None
    observation_time_stamp: str | None

# Shared helper clusters now live in dedicated modules and are imported above.
# Keep those imported names rooted here as the compatibility surface while the
# remaining handler-family extractions continue.


class FunctionExecutionError(Exception):
    """Raised when function execution fails"""
    pass


class FunctionExecutor:
    """
    Executes functions called by FunctionGemma.

    Each function maps to one or more backend services/APIs.
    Services are injected to avoid cross-domain imports.
    """

    def __init__(
        self,
        db: AsyncSession,
        capability_registry: CapabilityRegistry | None = None,
        cross_search_service: Optional[Any] = None,
        trial_search_service: Optional[Any] = None,
        germplasm_search_service: Optional[Any] = None,
        location_search_service: Optional[Any] = None,
        weather_service: Optional[Any] = None,
        breeding_value_service: Optional[Any] = None,
        protocol_search_service: Optional[Any] = None,
    ):
        self.db = db
        self.capability_registry = capability_registry
        # Services injected from domains (avoiding direct cross-domain imports)
        self.cross_search_service = cross_search_service
        self.trial_search_service = trial_search_service
        self.germplasm_search_service = germplasm_search_service
        self.location_search_service = location_search_service
        self.weather_service = weather_service
        self.breeding_value_service = breeding_value_service
        self.protocol_search_service = protocol_search_service

    def _is_baseline_candidate_name(self, name: str | None) -> bool:
        normalized_name = (name or "").lower()
        return "check" in normalized_name or "control" in normalized_name

    def _is_recommendation_query(self, query: str | None) -> bool:
        normalized_query = (query or "").lower()
        return any(token in normalized_query for token in RECOMMENDATION_QUERY_TOKENS)

    async def _resolve_germplasm_requests(
        self,
        *,
        organization_id: int,
        germplasm_ids: list[str],
    ) -> list[dict[str, Any]]:
        resolved: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for requested in germplasm_ids[:5]:
            candidate: dict[str, Any] | None = None
            if requested.isdigit():
                candidate = await self.germplasm_search_service.get_by_id(
                    db=self.db,
                    organization_id=organization_id,
                    germplasm_id=requested,
                )
            else:
                matches = await self.germplasm_search_service.search(
                    db=self.db,
                    organization_id=organization_id,
                    query=requested,
                    limit=5,
                )
                normalized_requested = requested.strip().lower()
                candidate = next(
                    (
                        match
                        for match in matches
                        if normalized_requested in {
                            (str(match.get("id") or "")).strip().lower(),
                            (str(match.get("name") or "")).strip().lower(),
                            (str(match.get("accession") or "")).strip().lower(),
                        }
                    ),
                    None,
                ) or (matches[0] if matches else None)

            if candidate and candidate.get("id") and candidate["id"] not in seen_ids:
                resolved.append(candidate)
                seen_ids.add(candidate["id"])

        return resolved

    def _build_interpretation_records_from_observations(
        self,
        observations: list[dict[str, Any]],
    ) -> list[PhenotypeInterpretationRecord]:
        records: list[PhenotypeInterpretationRecord] = []

        for observation in observations:
            numeric_value = safe_float(observation.get("value"))
            germplasm = observation.get("germplasm") or {}
            trait = observation.get("trait") or {}
            if numeric_value is None or not germplasm or not trait:
                continue

            entity_id = _get_germplasm_identifier(germplasm) or ""
            trait_name = trait.get("name") or trait.get("trait_name")
            if not entity_id or not trait_name:
                continue

            records.append(
                PhenotypeInterpretationRecord(
                    entity_db_id=entity_id,
                    entity_name=germplasm.get("name") or entity_id,
                    trait_key=trait_name,
                    trait_name=trait_name,
                    unit=trait.get("scale") or trait.get("data_type"),
                    value=numeric_value,
                    observation_ref=observation.get("observation_db_id") or f"db:observation:{observation.get('id')}",
                    role_hint="baseline_candidate" if self._is_baseline_candidate_name(germplasm.get("name")) else "candidate",
                )
            )

        return records

    def _build_ranked_candidates(self, interpretation: Any) -> list[dict[str, Any]]:
        return [
            {
                "candidate": item.entity_name,
                "entity_db_id": item.entity_db_id,
                "score": item.score,
                "rationale": item.rationale,
                "evidence_refs": item.evidence_refs,
                "uncertainty": "; ".join(interpretation.warnings) if interpretation.warnings else "",
            }
            for item in interpretation.ranking
        ]

    async def execute(
        self,
        function_name: str,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a function with given parameters.

        Args:
            function_name: Name of function to execute
            parameters: Function parameters

        Returns:
            Dict with execution result

        Raises:
            FunctionExecutionError: If execution fails
        """
        logger.info(f"Executing function: {function_name} with params: {parameters}")

        try:
            if self.capability_registry is not None and not self.capability_registry.can_execute(function_name):
                raise FunctionExecutionError(f"Function {function_name} is not permitted for this REEVU agent")

            # Route to appropriate handler
            if function_name.startswith("search_"):
                return await self._handle_search(function_name, parameters)
            elif function_name == "get_statistics":
                return await self._handle_statistics(parameters)
            elif function_name.startswith("get_"):
                return await self._handle_get(function_name, parameters)
            elif function_name.startswith("compare_"):
                return await self._handle_compare(function_name, parameters)
            elif function_name.startswith("calculate_"):
                return await self._handle_calculate(function_name, parameters)
            elif function_name.startswith("analyze_"):
                return await self._handle_analyze(function_name, parameters)
            elif function_name.startswith("recommend_"):
                return await self._handle_analyze(function_name, parameters)
            elif function_name.startswith("predict_"):
                return await self._handle_predict(function_name, parameters)
            elif function_name.startswith("check_"):
                return await self._handle_check(function_name, parameters)
            elif function_name.startswith("export_"):
                return await self._handle_export(function_name, parameters)
            elif function_name == "navigate_to":
                return await self._handle_navigate(parameters)
            elif function_name == "cross_domain_query":
                return await self._handle_cross_domain_query(parameters)
            elif function_name.startswith("propose_"):
                return await self._handle_proposal(function_name, parameters)
            else:
                raise FunctionExecutionError(f"Unknown function: {function_name}")

        except Exception as e:
            logger.error(f"Function execution error: {e}")
            raise FunctionExecutionError(f"Failed to execute {function_name}: {str(e)}")

    # ========== SEARCH HANDLERS ==========

    async def _handle_search(self, function_name: str, params: dict) -> dict:
        """Handle search_* functions"""
        return await handle_search(
            self,
            function_name,
            params,
            shared=SearchHandlerSharedContext(
                seedlot_search_service=seedlot_search_service,
                program_search_service=program_search_service,
                trait_search_service=trait_search_service,
            ),
            logger=logger,
        )

    # ========== STATISTICS HANDLER ==========

    async def _handle_statistics(self, params: dict) -> dict:
        """Get cross-domain statistics from database.

        This enables Veena to understand the scope of data available
        and provide context-aware responses.
        """
        return await handle_statistics(
            self,
            params,
            shared=StatisticsHandlerSharedContext(
                observation_search_service=observation_search_service,
                seedlot_search_service=seedlot_search_service,
                program_search_service=program_search_service,
                trait_search_service=trait_search_service,
            ),
            logger=logger,
        )

    # ========== PROPOSAL HANDLER (THE SCRIBE) ==========

    async def _handle_proposal(self, function_name: str, params: dict) -> dict:
        """
        Handle propose_* functions.
        Instead of executing writes, these create Proposals in the DB.
        """
        return await handle_proposal(
            self,
            function_name,
            params,
            shared=ProposalHandlerSharedContext(
                action_type_enum=ActionType,
                get_proposal_service=get_proposal_service,
            ),
            logger=logger,
        )

    # ========== CROSS-DOMAIN QUERY HANDLER ==========

    async def _handle_cross_domain_query(self, params: dict) -> dict:
        """Execute the REEVU compound-query path via the extracted handler family."""
        return await handle_cross_domain(
            self,
            params,
            shared=CrossDomainHandlerSharedContext(
                trial_phenotype_environment_tokens=TRIAL_PHENOTYPE_ENVIRONMENT_TOKENS,
                min_recommendation_domains=MIN_RECOMMENDATION_DOMAINS,
                get_qtl_mapping_service=get_qtl_mapping_service,
                resolve_trait_query=_resolve_trait_query,
                build_cross_domain_retrieval_tables=_build_cross_domain_retrieval_tables,
                build_cross_domain_retrieval_entities=_build_cross_domain_retrieval_entities,
                build_cross_domain_plan_execution_summary=_build_cross_domain_plan_execution_summary,
                build_cross_domain_evidence_envelope=_build_cross_domain_evidence_envelope,
                is_recommendation_query=self._is_recommendation_query,
            ),
            logger=logger,
        )

    # ========== GET HANDLERS ==========

    async def _handle_get(self, function_name: str, params: dict) -> dict:
        """Handle get_* functions"""
        return await handle_get(
            self,
            function_name,
            params,
            shared=GetHandlerSharedContext(
                build_single_contract_plan_execution_summary=_build_single_contract_plan_execution_summary,
                with_plan_execution_summary=_with_plan_execution_summary,
                get_germplasm_identifier=_get_germplasm_identifier,
                resolve_trait_query=_resolve_trait_query,
                derive_germplasm_data_age_seconds=_derive_germplasm_data_age_seconds,
                derive_germplasm_confidence=_derive_germplasm_confidence,
                build_germplasm_evidence_envelope=_build_germplasm_evidence_envelope,
                derive_genomics_lookup_confidence=_derive_genomics_lookup_confidence,
                build_genomics_evidence_envelope=_build_genomics_evidence_envelope,
                sample_record_identifiers=_sample_record_identifiers,
                sample_scalar_values=_sample_scalar_values,
                dedupe_string_values=_dedupe_string_values,
                get_trial_summary=get_trial_summary,
                get_comparison_statistics=get_comparison_statistics,
                get_qtl_mapping_service=get_qtl_mapping_service,
                observation_search_service=observation_search_service,
                program_search_service=program_search_service,
                seedlot_search_service=seedlot_search_service,
                trait_search_service=trait_search_service,
                cross_domain_gdd_service_cls=CrossDomainGDDService,
            ),
            logger=logger,
        )

    # ========== GET HANDLERS ==========

    # ========== COMPARE HANDLERS ==========

    async def _handle_compare(self, function_name: str, params: dict) -> dict:
        """Handle compare_* functions"""
        return await handle_compare(
            self,
            function_name,
            params,
            shared=CompareHandlerSharedContext(
                build_single_contract_plan_execution_summary=_build_single_contract_plan_execution_summary,
                with_plan_execution_summary=_with_plan_execution_summary,
                get_germplasm_identifier=_get_germplasm_identifier,
                observation_search_service=observation_search_service,
                phenotype_interpretation_service=phenotype_interpretation_service,
                envelope_observation_record_cls=EnvelopeObservationRecord,
            ),
            logger=logger,
        )

    # ========== CALCULATE HANDLERS ==========

    async def _handle_calculate(self, function_name: str, params: dict) -> dict:
        """Handle calculate_* functions"""
        return await handle_calculate(
            self,
            function_name,
            params,
            shared=CalculateHandlerSharedContext(
                build_single_contract_plan_execution_summary=_build_single_contract_plan_execution_summary,
                with_plan_execution_summary=_with_plan_execution_summary,
                sample_record_identifiers=_sample_record_identifiers,
                build_compute_evidence_envelope=_build_compute_evidence_envelope,
                observation_search_service=observation_search_service,
                compute_engine=compute_engine,
                resolve_database_backed_gblup_inputs=_resolve_database_backed_gblup_inputs,
            ),
            logger=logger,
        )

    # ========== ANALYZE HANDLERS ==========

    async def _handle_analyze(self, function_name: str, params: dict) -> dict:
        """Handle analyze_* functions"""
        return await handle_analyze(
            self,
            function_name,
            params,
            shared=AnalyzeHandlerSharedContext(
                observation_search_service=observation_search_service,
                cross_domain_gdd_service_cls=CrossDomainGDDService,
            ),
            logger=logger,
        )



    # ========== PREDICT HANDLERS ==========

    async def _handle_predict(self, function_name: str, params: dict) -> dict:
        """Handle predict_* functions"""
        return await handle_predict(
            self,
            function_name,
            params,
            shared=PredictHandlerSharedContext(
                observation_search_service=observation_search_service,
                cross_domain_gdd_service_cls=CrossDomainGDDService,
            ),
            logger=logger,
        )

    # ========== GET HANDLERS ==========

    # ========== CHECK HANDLERS ==========

    async def _handle_check(self, function_name: str, params: dict) -> dict:
        """Handle check_* functions"""
        return await handle_check(
            self,
            function_name,
            params,
            shared=CheckHandlerSharedContext(
                seedlot_search_service=seedlot_search_service,
            ),
            logger=logger,
        )

    # ========== GENERATE HANDLERS ==========



    # ========== EXPORT HANDLERS ==========

    async def _handle_export(self, function_name: str, params: dict) -> dict:
        """Handle export_* functions"""
        return await handle_export(
            self,
            function_name,
            params,
            shared=ExportHandlerSharedContext(
                observation_search_service=observation_search_service,
                seedlot_search_service=seedlot_search_service,
                program_search_service=program_search_service,
                trait_search_service=trait_search_service,
            ),
            logger=logger,
        )

    # ========== NAVIGATE HANDLERS ==========

    async def _handle_navigate(self, params: dict) -> dict:
        """Handle navigate_to function"""
        page = params.get("page")
        filters = params.get("filters", {})
        normalized_page = str(page or "requested page").strip() or "requested page"
        message = f"Open {normalized_page} with the requested filters."

        return {
            "success": True,
            "function": "navigate_to",
            "result_type": "navigation",
            "data": {
                "page": page,
                "filters": filters,
                "action": "navigate",
                "message": message,
            },
        }
