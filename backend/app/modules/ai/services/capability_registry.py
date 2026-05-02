from __future__ import annotations

from typing import Any

from app.models.ai_configuration import ReevuAgentSetting
from app.schemas.functions import BIJMANTRA_FUNCTIONS


class CapabilityRegistry:
    def __init__(
        self,
        *,
        function_schemas: list[dict[str, Any]] | None = None,
        capability_overrides: list[str] | None = None,
        tool_policy: dict[str, Any] | None = None,
    ):
        self._function_schemas = function_schemas or BIJMANTRA_FUNCTIONS
        self._all_names = {function["name"] for function in self._function_schemas}
        self._allowed_names = self._resolve_allowed_names(capability_overrides, tool_policy)

    @classmethod
    def from_agent_setting(
        cls,
        agent_setting: ReevuAgentSetting | None,
        *,
        function_schemas: list[dict[str, Any]] | None = None,
    ) -> "CapabilityRegistry":
        if agent_setting is None:
            return cls(function_schemas=function_schemas)

        return cls(
            function_schemas=function_schemas,
            capability_overrides=agent_setting.capability_overrides,
            tool_policy=agent_setting.tool_policy,
        )

    def get_allowed_functions(self) -> list[dict[str, Any]]:
        return [
            function
            for function in self._function_schemas
            if function["name"] in self._allowed_names
        ]

    def get_allowed_function_names(self) -> list[str]:
        return [function["name"] for function in self.get_allowed_functions()]

    def can_execute(self, function_name: str) -> bool:
        return function_name in self._allowed_names

    def _resolve_allowed_names(
        self,
        capability_overrides: list[str] | None,
        tool_policy: dict[str, Any] | None,
    ) -> set[str]:
        allowed_names = set(self._all_names)

        override_names = self._normalize_names(capability_overrides)
        if override_names:
            allowed_names = override_names

        if tool_policy is None:
            return allowed_names

        if "allow" in tool_policy:
            allow_names = self._normalize_names(tool_policy.get("allow"))
            allowed_names = allowed_names & allow_names if override_names else allow_names

        if "deny" in tool_policy:
            allowed_names -= self._normalize_names(tool_policy.get("deny"))

        return allowed_names

    def _normalize_names(self, values: Any) -> set[str]:
        if values is None:
            return set()

        if isinstance(values, str):
            candidates = [values]
        elif isinstance(values, list):
            candidates = values
        else:
            return set()

        return {
            value.strip()
            for value in candidates
            if isinstance(value, str) and value.strip() in self._all_names
        }