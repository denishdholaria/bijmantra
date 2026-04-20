from __future__ import annotations

from app.schemas.compute_contract import (
    COMPUTE_CONTRACT_VERSION,
    ComputeErrorDetail,
    ComputeInputSummary,
    ComputeJobAcceptedResponse,
    ComputeProvenance,
    ComputeSuccessResponse,
    GBLUPOutput,
)
from app.schemas.cross_domain_query_contract import (
    CROSS_DOMAIN_QUERY_CONTRACT_VERSION,
    CROSS_DOMAIN_QUERY_TRUST_SURFACE,
    CrossDomainQueryContractMetadata,
)
from app.schemas.genomics_marker_lookup_contract import (
    GENOMICS_MARKER_LOOKUP_CONTRACT_VERSION,
    GENOMICS_MARKER_LOOKUP_TRUST_SURFACE,
    GenomicsMarkerLookupContractMetadata,
)
from app.schemas.germplasm_lookup_contract import (
    GERMPLASM_LOOKUP_CONTRACT_VERSION,
    GERMPLASM_LOOKUP_TRUST_SURFACE,
    GermplasmLookupContractMetadata,
)
from app.schemas.phenotype_comparison_contract import (
    PHENOTYPE_COMPARISON_CONTRACT_VERSION,
    PHENOTYPE_COMPARISON_TRUST_SURFACE,
    PhenotypeComparisonContractMetadata,
)
from app.schemas.trial_summary_contract import (
    TRIAL_SUMMARY_CONTRACT_VERSION,
    TRIAL_SUMMARY_TRUST_SURFACE,
    TrialSummaryContractMetadata,
)


def test_germplasm_lookup_contract_metadata_defaults_are_stable() -> None:
    metadata = GermplasmLookupContractMetadata()

    assert metadata.response_contract_version == GERMPLASM_LOOKUP_CONTRACT_VERSION
    assert metadata.trust_surface == GERMPLASM_LOOKUP_TRUST_SURFACE
    assert metadata.data_source == "database"
    assert metadata.schema_version == "1"
    assert metadata.confidence_score is None
    assert metadata.data_age_seconds is None


def test_genomics_marker_lookup_contract_metadata_defaults_are_stable() -> None:
    metadata = GenomicsMarkerLookupContractMetadata()

    assert metadata.response_contract_version == GENOMICS_MARKER_LOOKUP_CONTRACT_VERSION
    assert metadata.trust_surface == GENOMICS_MARKER_LOOKUP_TRUST_SURFACE
    assert metadata.data_source == "database"
    assert metadata.schema_version == "1"
    assert metadata.confidence_score is None


def test_cross_domain_query_contract_metadata_defaults_are_stable() -> None:
    metadata = CrossDomainQueryContractMetadata()

    assert metadata.response_contract_version == CROSS_DOMAIN_QUERY_CONTRACT_VERSION
    assert metadata.trust_surface == CROSS_DOMAIN_QUERY_TRUST_SURFACE
    assert metadata.data_source == "database_and_weather_service"
    assert metadata.schema_version == "1"
    assert metadata.confidence_score is None
    assert metadata.calculation_method_refs == []


def test_trial_summary_contract_metadata_defaults_are_stable() -> None:
    metadata = TrialSummaryContractMetadata()

    assert metadata.response_contract_version == TRIAL_SUMMARY_CONTRACT_VERSION
    assert metadata.trust_surface == TRIAL_SUMMARY_TRUST_SURFACE
    assert metadata.data_source == "database"
    assert metadata.schema_version == "1"
    assert metadata.confidence_score is None
    assert metadata.data_age_seconds is None
    assert metadata.calculation_method_refs == []


def test_phenotype_comparison_contract_metadata_defaults_are_stable() -> None:
    metadata = PhenotypeComparisonContractMetadata(scope="compare")

    assert metadata.response_contract_version == PHENOTYPE_COMPARISON_CONTRACT_VERSION
    assert metadata.trust_surface == PHENOTYPE_COMPARISON_TRUST_SURFACE
    assert metadata.data_source == "database"
    assert metadata.schema_version == "1"
    assert metadata.confidence_score is None
    assert metadata.data_age_seconds is None
    assert metadata.scope == "compare"


def test_compute_contract_defaults_are_stable() -> None:
    input_summary = ComputeInputSummary()
    provenance = ComputeProvenance(
        routine="gblup",
        output_kind="breeding_values",
        backend="numpy",
        execution_mode="sync",
        input_summary=input_summary,
    )
    success = ComputeSuccessResponse(
        routine="gblup",
        output_kind="breeding_values",
        output=GBLUPOutput(breeding_values=[0.12], mean=0.12, converged=True),
        compute_time_ms=12.5,
        provenance=provenance,
    )
    accepted = ComputeJobAcceptedResponse(
        routine="gblup",
        job_id="job-1",
        poll_url="/api/v2/compute/jobs/job-1",
        accepted_input=input_summary,
    )
    error = ComputeErrorDetail(code="missing_inputs", message="Need genotype data")

    assert provenance.contract_version == COMPUTE_CONTRACT_VERSION
    assert provenance.policy_flags == []
    assert success.contract_version == COMPUTE_CONTRACT_VERSION
    assert success.status == "succeeded"
    assert accepted.contract_version == COMPUTE_CONTRACT_VERSION
    assert accepted.status == "pending"
    assert error.contract_version == COMPUTE_CONTRACT_VERSION
    assert error.retryable is False
    assert error.details == {}