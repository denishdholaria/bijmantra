"""Policy guard primitives for REEVU intelligent data access."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessDecision:
    """Result of a policy guard access evaluation."""

    allowed: bool
    reason: str
    tier: str


class PolicyGuard:
    """Server-side policy enforcement for REEVU data access."""

    ALLOWED_DOMAIN_SCOPES: set[str] = {
        "breeding",
        "weather",
        "analytics",
        "genomics",
        "operations",
        "performance",
    }

    SECURITY_DENYLIST: set[str] = {
        "api_keys",
        "auth_tokens",
        "credentials",
        "secrets",
        "security_audits_internal",
        "private_keys",
    }

    def evaluate_access(self, domain_scope: str, entity: str, operation: str = "read") -> AccessDecision:
        """Evaluate whether REEVU may access a domain/entity pair."""
        normalized_scope = domain_scope.strip().lower()
        normalized_entity = entity.strip().lower()
        normalized_operation = operation.strip().lower()

        if normalized_entity in self.SECURITY_DENYLIST:
            return AccessDecision(
                allowed=False,
                reason=f"entity '{normalized_entity}' is blocked by security denylist",
                tier="D",
            )

        if normalized_scope not in self.ALLOWED_DOMAIN_SCOPES:
            return AccessDecision(
                allowed=False,
                reason=f"domain scope '{normalized_scope}' is not in REEVU allowlist",
                tier="D",
            )

        if normalized_operation != "read":
            return AccessDecision(
                allowed=False,
                reason=f"operation '{normalized_operation}' requires human confirmation",
                tier="C",
            )

        return AccessDecision(
            allowed=True,
            reason="read access allowed by default REEVU policy",
            tier="A",
        )
