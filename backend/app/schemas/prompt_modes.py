from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class PromptModeCapability(StrEnum):
	BREEDING = "breeding_mode"
	GENOMICS = "genomics_mode"
	ENVIRONMENT = "environment_mode"
	COMPLIANCE = "compliance_mode"


class PromptModeDefinition(BaseModel):
	id: str
	label: str
	description: str


PROMPT_MODE_DEFINITIONS: tuple[PromptModeDefinition, ...] = (
	PromptModeDefinition(
		id=PromptModeCapability.BREEDING.value,
		label="Breeding Mode",
		description="Cross-domain breeding decision support and selection framing.",
	),
	PromptModeDefinition(
		id=PromptModeCapability.GENOMICS.value,
		label="Genomics Mode",
		description="Genomic analysis, marker interpretation, and selection reasoning.",
	),
	PromptModeDefinition(
		id=PromptModeCapability.ENVIRONMENT.value,
		label="Environment Mode",
		description="Soil, climate, and environmental context for agronomic recommendations.",
	),
	PromptModeDefinition(
		id=PromptModeCapability.COMPLIANCE.value,
		label="Compliance Mode",
		description="Identity preservation, policy, and operational guardrail emphasis.",
	),
)


PROMPT_MODE_FRAGMENTS: dict[str, str] = {
	PromptModeCapability.BREEDING.value: (
		"Breeding mode is active. Prioritize selection decisions, crossing strategy, trial interpretation, "
		"and practical breeding tradeoffs with explicit rationale."
	),
	PromptModeCapability.GENOMICS.value: (
		"Genomics mode is active. Prioritize marker interpretation, relationship structure, genomic prediction, "
		"and the limits of genetic evidence."
	),
	PromptModeCapability.ENVIRONMENT.value: (
		"Environment mode is active. Incorporate soil, climate, geography, and management constraints when "
		"explaining recommendations."
	),
	PromptModeCapability.COMPLIANCE.value: (
		"Compliance mode is active. Emphasize traceability, identity preservation, policy guardrails, and when "
		"claims require verification or explicit evidence."
	),
}


def resolve_prompt_mode_fragments(prompt_mode_capabilities: list[str] | None) -> list[str]:
	if not prompt_mode_capabilities:
		return []

	enabled = set(prompt_mode_capabilities)
	return [
		PROMPT_MODE_FRAGMENTS[definition.id]
		for definition in PROMPT_MODE_DEFINITIONS
		if definition.id in enabled and definition.id in PROMPT_MODE_FRAGMENTS
	]