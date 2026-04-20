"""Orchestrator stage definitions for REEVU execution-first pipeline."""

from enum import StrEnum


class ReevuStage(StrEnum):
    """Canonical orchestrator stages for stage telemetry and tracing."""

    INTENT_SCOPE = "intent_scope"
    PLAN_GENERATION = "plan_generation"
    DATA_EXECUTION = "data_execution"
    COMPUTATION = "computation"
    EVIDENCE_ASSEMBLY = "evidence_assembly"
    ANSWER_SYNTHESIS = "answer_synthesis"
    POLICY_VALIDATION = "policy_validation"
    RESPONSE_EMISSION = "response_emission"
