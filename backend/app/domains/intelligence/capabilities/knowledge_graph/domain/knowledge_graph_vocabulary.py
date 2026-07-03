"""Pure Knowledge Graph vocabulary normalization rules."""

SUPPORTED_GRAPH_RELATIONSHIP_TYPES = (
    "evaluated_in",
    "observed_under",
    "adapted_for",
    "resistant_to",
    "derived_from",
    "has_trait",
    "has_evidence",
)

SUPPORTED_GRAPH_DIRECTIONS = ("incoming", "outgoing", "both")
SUPPORTED_GRAPH_RESULT_SIDES = ("source", "target")


def normalize_graph_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def normalize_relationship_type(relationship_type: str) -> str:
    return normalize_graph_token(relationship_type)


def require_supported_relationship_type(
    relationship_type: str,
    *,
    error_type: type[ValueError] = ValueError,
) -> str:
    normalized = normalize_relationship_type(relationship_type)
    if normalized not in SUPPORTED_GRAPH_RELATIONSHIP_TYPES:
        supported = ", ".join(SUPPORTED_GRAPH_RELATIONSHIP_TYPES)
        raise error_type(
            f"Unsupported graph relationship type '{relationship_type}'. Use: {supported}"
        )
    return normalized


def require_supported_direction(
    direction: str,
    *,
    error_type: type[ValueError] = ValueError,
) -> str:
    normalized = normalize_graph_token(direction)
    if normalized not in SUPPORTED_GRAPH_DIRECTIONS:
        supported = ", ".join(SUPPORTED_GRAPH_DIRECTIONS)
        raise error_type(
            f"Unsupported graph neighborhood direction '{direction}'. Use: {supported}"
        )
    return normalized


def require_supported_result_side(
    result_side: str,
    *,
    error_type: type[ValueError] = ValueError,
) -> str:
    normalized = normalize_graph_token(result_side)
    if normalized not in SUPPORTED_GRAPH_RESULT_SIDES:
        supported = ", ".join(SUPPORTED_GRAPH_RESULT_SIDES)
        raise error_type(
            f"Unsupported graph evidence-search result side '{result_side}'. Use: {supported}"
        )
    return normalized
