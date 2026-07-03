from app.modules.phenotyping.services.interpretation_service import (
    PhenotypeInterpretationRecord,
    phenotype_interpretation_service,
)


def test_build_interpretation_for_comparison_uses_baseline_and_requested_order():
    records = [
        PhenotypeInterpretationRecord(
            entity_db_id="B",
            entity_name="Variety B",
            trait_key="yield",
            trait_name="Yield",
            unit="kg/ha",
            value=120.0,
            observation_ref="obs-b-1",
        ),
        PhenotypeInterpretationRecord(
            entity_db_id="A",
            entity_name="Check A",
            trait_key="yield",
            trait_name="Yield",
            unit="kg/ha",
            value=100.0,
            observation_ref="obs-a-1",
            role_hint="baseline_candidate",
        ),
        PhenotypeInterpretationRecord(
            entity_db_id="B",
            entity_name="Variety B",
            trait_key="yield",
            trait_name="Yield",
            unit="kg/ha",
            value=130.0,
            observation_ref="obs-b-2",
        ),
        PhenotypeInterpretationRecord(
            entity_db_id="A",
            entity_name="Check A",
            trait_key="yield",
            trait_name="Yield",
            unit="kg/ha",
            value=110.0,
            observation_ref="obs-a-2",
            role_hint="baseline_candidate",
        ),
    ]

    interpretation = phenotype_interpretation_service.build_interpretation(
        scope="germplasm_comparison",
        records=records,
        methodology="database_observation_means_by_germplasm",
        entity_order=["B", "A"],
        baseline_entity_id="A",
        baseline_entity_name="Check A",
        baseline_selection="explicit_check_id",
        evidence_refs=["db:germplasm:A", "db:germplasm:B"],
    )

    assert interpretation.contract_version == "phenotyping.interpretation.v1"
    assert [entity.entity_db_id for entity in interpretation.entities] == ["B", "A"]
    assert interpretation.baseline is not None
    assert interpretation.baseline.entity_db_id == "A"
    assert interpretation.primary_trait_key == "yield"
    assert interpretation.ranking[0].entity_db_id == "B"
    assert interpretation.ranking[0].delta_percent_vs_baseline == 19.0
    assert interpretation.ranking[0].evidence_refs == ["obs-b-1", "obs-b-2"]
    assert "calc:delta_percent_vs_baseline" in interpretation.calculation_ids


def test_build_interpretation_for_trial_summary_prefers_yield_trait():
    records = [
        PhenotypeInterpretationRecord(
            entity_db_id="101",
            entity_name="Line 101",
            trait_key="height",
            trait_name="Plant Height",
            unit="cm",
            value=95.0,
            observation_ref="obs-1",
        ),
        PhenotypeInterpretationRecord(
            entity_db_id="102",
            entity_name="Line 102",
            trait_key="height",
            trait_name="Plant Height",
            unit="cm",
            value=90.0,
            observation_ref="obs-2",
        ),
        PhenotypeInterpretationRecord(
            entity_db_id="101",
            entity_name="Line 101",
            trait_key="yield",
            trait_name="Grain Yield",
            unit="kg/ha",
            value=4.2,
            observation_ref="obs-3",
        ),
        PhenotypeInterpretationRecord(
            entity_db_id="102",
            entity_name="Line 102",
            trait_key="yield",
            trait_name="Grain Yield",
            unit="kg/ha",
            value=5.1,
            observation_ref="obs-4",
        ),
    ]

    interpretation = phenotype_interpretation_service.build_interpretation(
        scope="trial_summary",
        records=records,
        methodology="database_trial_observation_means_by_germplasm",
        evidence_refs=["db:trial:T-1", "db:study:10"],
    )

    assert interpretation.primary_trait_key == "yield"
    assert interpretation.primary_trait_name == "Grain Yield"
    assert interpretation.summary.entity_count == 2
    assert interpretation.summary.trait_count == 2
    assert interpretation.ranking[0].entity_db_id == "102"
    assert interpretation.ranking[0].score == 5.1
    assert "db:trial:T-1" in interpretation.evidence_refs
    assert "db:trait:yield" in interpretation.evidence_refs


def test_build_interpretation_without_records_reports_warning():
    interpretation = phenotype_interpretation_service.build_interpretation(
        scope="trial_summary",
        records=[],
        methodology="database_trial_observation_means_by_germplasm",
    )

    assert interpretation.entities == []
    assert interpretation.traits == []
    assert interpretation.ranking == []
    assert interpretation.warnings == ["No numeric observations available for interpretation."]