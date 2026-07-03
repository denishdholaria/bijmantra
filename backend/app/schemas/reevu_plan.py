"""
REEVU Execution Plan Schema — Stage C

Defines structured multi-domain execution plans for compound queries.
Aligns with reevu-agent-contract.md orchestrator stages.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlanStep(BaseModel):
    """A single step in a multi-domain execution plan."""

    step_id: str = Field(..., description="Unique step identifier, e.g. 'step-1'")
    domain: str = Field(
        ...,
        description="Target domain: 'breeding', 'genomics', 'weather', 'trials', 'analytics'",
    )
    description: str = Field(..., description="Human-readable description of what this step does")
    prerequisites: list[str] = Field(
        default_factory=list,
        description="Step IDs that must complete before this step can execute",
    )
    expected_outputs: list[str] = Field(
        default_factory=list,
        description="Expected output types, e.g. 'germplasm_list', 'weather_data'",
    )
    completed: bool = Field(False, description="Whether this step has been executed")
    deterministic: bool = Field(
        False,
        description="True if this step should be routed through deterministic computation",
    )

    model_config = ConfigDict(frozen=True)


class ReevuExecutionPlan(BaseModel):
    """Multi-domain execution plan for a compound REEVU query."""

    plan_id: str = Field(..., description="Unique plan identifier")
    original_query: str = Field(..., description="The original user query that generated this plan")
    is_compound: bool = Field(
        False,
        description="True if the query spans multiple domains",
    )
    steps: list[PlanStep] = Field(
        default_factory=list,
        description="Ordered list of execution steps",
    )
    domains_involved: list[str] = Field(
        default_factory=list,
        description="Distinct domain tags present in the plan",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Planner metadata and fallback markers for observability",
    )

    @property
    def completed_count(self) -> int:
        return sum(1 for s in self.steps if s.completed)

    @property
    def total_steps(self) -> int:
        return len(self.steps)


class RoutingDecision(BaseModel):
    """Result of deterministic routing evaluation."""

    should_route: bool = Field(
        False,
        description="Whether the request should be routed to deterministic computation",
    )
    reason: str = Field("", description="Human-readable reason for the routing decision")
    matched_criteria: list[str] = Field(
        default_factory=list,
        description="Which routing criteria triggered the decision",
    )

    model_config = ConfigDict(frozen=True)


class RankedItem(BaseModel):
    """A single ranked item in a comparative recommendation."""

    candidate: str = Field(..., description="Name or identifier of the candidate")
    rank: int = Field(..., ge=1, description="Rank position (1 = best)")
    score: float | None = Field(None, description="Numeric score if available")
    rationale: str = Field("", description="Why this candidate has this rank")
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Evidence references supporting this ranking",
    )
    calculation_method_refs: list[str] = Field(
        default_factory=list,
        description="Deterministic calculation methods used to produce this score",
    )
    uncertainty_note: str = Field(
        "",
        description="Data gaps or caveats for this recommendation",
    )


class ComparisonResult(BaseModel):
    """Structured output for comparative recommendations."""

    items: list[RankedItem] = Field(
        default_factory=list,
        description="Ranked list of candidates",
    )
    methodology: str = Field(
        "",
        description="Brief description of ranking methodology",
    )
    calculation_method_refs: list[str] = Field(
        default_factory=list,
        description="Top-level deterministic calculation methods used in the comparison",
    )
    overall_recommendation: str = Field(
        "",
        description="Summary recommendation statement",
    )
    domains_used: list[str] = Field(
        default_factory=list,
        description="Domains consulted for this comparison",
    )
