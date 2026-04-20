"""
Function Calling Service using FunctionGemma

Detects user intent and converts natural language to function calls.
Uses FunctionGemma (270M) for efficient function calling.
"""

import json
import logging
import re
from typing import Any

import httpx

from app.core.http_tracing import create_traced_async_client
from app.modules.ai.services.reevu.planner import _detect_domains
from app.schemas.functions import (
    BIJMANTRA_FUNCTIONS,
    format_functions_for_prompt,
    get_all_function_names,
)


logger = logging.getLogger(__name__)
# Matches explicit trial references like "TRIAL-22", "TRIAL 22", or "T-105".
TRIAL_ID_PREFIX_PATTERN = r"\b(TRIAL[-_ ]?\d+|T[-_]\d+)\b"
# Matches contextual trial references like "trial id: ABC123" or "trial 42".
TRIAL_ID_CONTEXT_PATTERN = r"\btrial(?:\s+(?:id|db\s*id))?\s*[:#-]?\s*([A-Za-z]*\d[\w-]*)\b"
# Matches contextual germplasm references like "germplasm IR64" or "accession: G-7".
GERMPLASM_ID_CONTEXT_PATTERN = (
    r"\b(?:germplasm|variety|accession)(?:\s+(?:id|db\s*id|named))?\s*[:#-]?\s*([A-Za-z0-9][\w-]*)\b"
)
MARKER_TRAIT_QUERY_PATTERN = (
    r"(?:linked to|associated with|associations for|association for|for)\s+"
    r"([A-Za-z0-9][A-Za-z0-9\s\-_]+)"
)
KNOWN_TRAIT_PHRASES: tuple[str, ...] = (
    "blast resistance",
    "drought tolerance",
    "yield",
    "height",
    "maturity",
)
CROSS_DOMAIN_QUERY_DOMAIN_CLASSES: tuple[frozenset[str], ...] = (
    frozenset({"breeding", "trials", "weather"}),
    frozenset({"breeding", "trials"}),
    frozenset({"breeding", "genomics"}),
    frozenset({"breeding", "protocols"}),
)
MARKER_TERMS: tuple[str, ...] = ("marker", "markers", "qtl", "qtls", "gwas", "snp", "snps")
MARKER_ACTION_PHRASES: tuple[str, ...] = (
    "linked to",
    "associated with",
    "association",
    "associations",
    "lookup",
    "show",
    "find",
    "list",
)
TRIAL_SUMMARY_ACTION_PHRASES: tuple[str, ...] = (
    "trial result",
    "trial results",
    "trial summary",
    "summarize trial",
    "top performer",
    "top performers",
    "best performer",
    "best performers",
    "performed best",
    "rank entries",
    "ranking",
    "rankings",
    "rank trial",
)
TRIAL_RESULT_KEYWORDS: tuple[str, ...] = (
    "result",
    "results",
    "summary",
    "top performer",
    "top performers",
    "best performer",
    "best performers",
    "performed best",
    "ranking",
    "rankings",
)
TRAIT_SUMMARY_ACTION_PHRASES: tuple[str, ...] = (
    "trait summary",
    "summary statistics",
    "trait statistics",
    "mean performance",
)
GENOMIC_SELECTION_PHRASES: tuple[str, ...] = (
    "genomic selection",
    "genomic breeding value",
    "genomic breeding values",
    "genomic estimated breeding value",
    "genomic estimated breeding values",
    "gebv",
    "gebvs",
    "gblup",
)
GENOMIC_SELECTION_NON_VARIETY_TOKENS: frozenset[str] = frozenset({"GBLUP", "GEBV", "GEBVS"})
BREEDING_ENTITY_TERMS: tuple[str, ...] = (
    "variety",
    "varieties",
    "cultivar",
    "cultivars",
    "germplasm",
    "accession",
    "line",
    "lines",
)
GERMPLASM_CONTEXT_STOPWORDS: frozenset[str] = frozenset(
    {
        "and",
        "are",
        "best",
        "current",
        "for",
        "from",
        "has",
        "have",
        "is",
        "latest",
        "or",
        "support",
        "supporting",
        "supports",
        "under",
        "with",
    }
)
PROTOCOL_QUERY_TERMS: tuple[str, ...] = (
    "protocol",
    "protocols",
    "speed breeding",
    "photoperiod",
    "growth chamber",
)
TRIAL_QUERY_LEADING_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "our",
        "my",
        "this",
        "that",
        "current",
        "latest",
        "exact",
        "in",
        "for",
        "at",
        "from",
        "of",
    }
)
TRIAL_QUERY_GENERIC_TERMS: frozenset[str] = frozenset(
    {
        "best",
        "performer",
        "performers",
        "performed",
        "ranking",
        "rankings",
        "result",
        "results",
        "summary",
        "top",
    }
)
TRIAL_QUERY_ACTION_TERMS: frozenset[str] = frozenset(
    {
        "compare",
        "find",
        "give",
        "list",
        "rank",
        "show",
        "summarise",
        "summarize",
        "tell",
        "what",
        "which",
        "who",
    }
)


class FunctionCall:
    """Represents a detected function call"""

    def __init__(self, name: str, parameters: dict[str, Any], confidence: float = 1.0):
        self.name = name
        self.parameters = parameters
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "parameters": self.parameters,
            "confidence": self.confidence
        }


class FunctionCallingService:
    """
    Service for detecting and parsing function calls from natural language.

    Uses FunctionGemma (270M) via HuggingFace Inference API.
    Falls back to pattern matching if API unavailable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        function_schemas: list[dict[str, Any]] | None = None,
    ):
        self.api_key = api_key
        self.model = "google/functiongemma-270m-it"
        self.base_url = "https://api-inference.huggingface.co/models"
        self._client: httpx.AsyncClient | None = None
        self.function_schemas = function_schemas or BIJMANTRA_FUNCTIONS
        self.allowed_function_names = set(get_all_function_names(self.function_schemas))

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = create_traced_async_client(timeout=30.0)
        return self._client

    async def detect_function_call(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None
    ) -> FunctionCall | None:
        """
        Detect if user message is a function call request.

        Args:
            user_message: User's natural language message
            conversation_history: Previous conversation for context

        Returns:
            FunctionCall if detected, None otherwise
        """

        # Try FunctionGemma API first
        if self.api_key:
            try:
                return await self._detect_with_functiongemma(user_message, conversation_history)
            except Exception as e:
                logger.warning(f"FunctionGemma API failed: {e}, falling back to pattern matching")

        # Fallback to pattern matching
        return self._detect_with_patterns(user_message)

    async def _detect_with_functiongemma(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None
    ) -> FunctionCall | None:
        """Use FunctionGemma API to detect function calls"""

        # Build prompt with function definitions
        functions_text = format_functions_for_prompt(self.function_schemas)

        prompt = f"""You are a function calling assistant for a plant breeding application.

{functions_text}

User message: "{user_message}"

If the user wants to execute a function, respond with JSON:
{{"function": "function_name", "parameters": {{"param1": "value1"}}}}

If the user is just asking a question (not requesting an action), respond with:
{{"function": null}}

Response:"""

        try:
            client = await self._get_client()
            headers = {"Authorization": f"Bearer {self.api_key}"}

            response = await client.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 256,
                        "temperature": 0.1,
                        "return_full_text": False
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()

                # Parse response
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    generated_text = result.get("generated_text", "")
                else:
                    generated_text = str(result)

                # Extract JSON from response
                function_call = self._parse_function_json(generated_text)
                if function_call:
                    finalized_call = self._finalize_detected_call(
                        function_call.name,
                        function_call.parameters,
                        confidence=function_call.confidence,
                    )
                    if finalized_call:
                        logger.info(f"FunctionGemma detected: {finalized_call.name}")
                        return finalized_call

            else:
                logger.error(f"FunctionGemma API error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"FunctionGemma API exception: {e}")
            raise

        return None

    def _parse_function_json(self, text: str) -> FunctionCall | None:
        """Parse function call from JSON text"""
        decoder = json.JSONDecoder()

        try:
            for match in re.finditer(r"\{", text):
                try:
                    data, _ = decoder.raw_decode(text[match.start():])
                except json.JSONDecodeError:
                    continue

                if not isinstance(data, dict):
                    continue

                function_name = data.get("function")
                if function_name and function_name != "null":
                    parameters = data.get("parameters", {})
                    return FunctionCall(function_name, parameters)

        except json.JSONDecodeError:
            logger.debug(f"Failed to parse JSON from: {text}")

        return None

    def _detect_with_patterns(self, user_message: str) -> FunctionCall | None:
        """
        Fallback: Use pattern matching to detect function calls.

        This is a simple rule-based system for when FunctionGemma is unavailable.
        """
        message_lower = user_message.lower()
        detected_domains = set(_detect_domains(user_message))

        if self._is_trial_results_request(message_lower) and self._should_prefer_trial_results_route(
            user_message=user_message,
            message_lower=message_lower,
            detected_domains=detected_domains,
        ):
            return self._finalize_detected_call(
                "get_trial_results",
                self._build_trial_results_params(user_message),
                confidence=0.75,
            )

        if self._is_trait_summary_request(message_lower) and not self._has_explicit_cross_domain_cues(
            user_message=user_message,
            message_lower=message_lower,
            detected_domains=detected_domains,
        ):
            trait_summary_params: dict[str, Any] = {}
            varieties = self._extract_variety_names(user_message)
            if varieties:
                trait_summary_params["germplasm_ids"] = varieties

            return self._finalize_detected_call(
                "get_trait_summary",
                trait_summary_params,
                confidence=0.75,
            )

        if self._should_route_cross_domain_query(
            detected_domains=detected_domains,
            message_lower=message_lower,
        ):
            return self._finalize_detected_call(
                "cross_domain_query",
                self._extract_cross_domain_params(user_message),
                confidence=0.8,
            )

        if self._is_trial_results_request(message_lower):
            return self._finalize_detected_call(
                "get_trial_results",
                self._build_trial_results_params(user_message),
                confidence=0.75,
            )

        if any(token in message_lower for token in ("germplasm", "variety", "accession")) and any(
            phrase in message_lower
            for phrase in (
                "detail",
                "details",
                "lookup",
                "profile",
                "tell me about",
            )
        ):
            germplasm_identifier = self._extract_germplasm_identifier(user_message)
            germplasm_params: dict[str, Any] = {}
            # Numeric identifiers are treated as internal germplasm IDs; accession-style
            # identifiers stay query-backed so the search service can resolve them safely.
            if germplasm_identifier and germplasm_identifier.isdigit():
                germplasm_params["germplasm_id"] = germplasm_identifier
            elif germplasm_identifier:
                germplasm_params["query"] = germplasm_identifier
            else:
                germplasm_params["query"] = user_message.strip()

            return self._finalize_detected_call(
                "get_germplasm_details",
                germplasm_params,
                confidence=0.75,
            )

        if any(term in message_lower for term in MARKER_TERMS) and any(
            phrase in message_lower for phrase in MARKER_ACTION_PHRASES
        ):
            marker_query = self._extract_marker_trait_query(user_message)
            marker_params = {"query": marker_query or user_message.strip()}
            return self._finalize_detected_call(
                "get_marker_associations",
                marker_params,
                confidence=0.75,
            )

        if any(phrase in message_lower for phrase in GENOMIC_SELECTION_PHRASES):
            breeding_value_params: dict[str, Any] = {"method": "GBLUP"}
            if trait := self._extract_trait_query(user_message):
                breeding_value_params["trait"] = trait
            if crop := self._extract_search_params(user_message, "genomic_selection").get("crop"):
                breeding_value_params["crop"] = crop
            if varieties := self._extract_variety_names_for_genomic_selection(user_message):
                breeding_value_params["germplasm_ids"] = varieties
            return self._finalize_detected_call(
                "calculate_breeding_value",
                breeding_value_params,
                confidence=0.72,
            )

        # Search patterns
        if any(word in message_lower for word in ["search", "find", "show me", "show", "list"]):
            if "germplasm" in message_lower or "variety" in message_lower or "varieties" in message_lower:
                params = self._extract_search_params(user_message, "germplasm")
                return self._finalize_detected_call("search_germplasm", params, confidence=0.7)

            elif "trial" in message_lower:
                params = self._extract_search_params(user_message, "trial")
                return self._finalize_detected_call("search_trials", params, confidence=0.7)

            elif "cross" in message_lower:
                params = self._extract_search_params(user_message, "cross")
                return self._finalize_detected_call("search_crosses", params, confidence=0.7)

            elif "accession" in message_lower or "accessions" in message_lower:
                params = self._extract_search_params(user_message, "accession")
                return self._finalize_detected_call("search_accessions", params, confidence=0.7)

        # Compare patterns
        if "compare" in message_lower:
            if (
                "germplasm" in message_lower
                or "variety" in message_lower
                or "varieties" in message_lower
                or any(term in message_lower for term in ("trait", "traits", "yield", "performance", "phenotype"))
            ):
                varieties = self._extract_variety_names(user_message)
                if varieties:
                    return self._finalize_detected_call(
                        "compare_germplasm",
                        {
                            "germplasm_ids": varieties
                        },
                        confidence=0.6,
                    )

        # Proposal Patterns
        if "create" in message_lower and "trial" in message_lower:
            params = self._extract_create_trial_params(user_message)
            return self._finalize_detected_call("propose_create_trial", params, confidence=0.7)

        if ("create" in message_lower or "make" in message_lower) and "cross" in message_lower:
            params = self._extract_create_cross_params(user_message)
            return self._finalize_detected_call("propose_create_cross", params, confidence=0.7)

        if "record" in message_lower and ("observation" in message_lower or "score" in message_lower):
            # Simple extraction for observation
            # Ideally needs more complex extraction logic, but this is fallback
            return self._finalize_detected_call(
                "propose_record_observation",
                {
                    "trial_id": "extract_from_context",
                    "date": "today"
                },
                confidence=0.5,
            )



        # Weather patterns
        if "weather" in message_lower:
            location = self._extract_location(user_message)
            return self._finalize_detected_call(
                "get_weather_forecast",
                {
                    "location": location or "current",
                    "days": 7
                },
                confidence=0.7,
            )

        # Navigate patterns
        if any(word in message_lower for word in ["go to", "open", "navigate"]):
            page = self._extract_page_name(user_message)
            if page:
                return self._finalize_detected_call("navigate_to", {"page": page}, confidence=0.8)

        return None

    def _finalize_detected_call(
        self,
        function_name: str,
        parameters: dict[str, Any],
        *,
        confidence: float,
    ) -> FunctionCall | None:
        if function_name not in self.allowed_function_names:
            logger.info("Function %s blocked by capability registry", function_name)
            return None

        return FunctionCall(function_name, parameters, confidence=confidence)

    def _extract_search_params(self, message: str, entity_type: str) -> dict[str, Any]:
        """Extract search parameters from message"""
        params = {}
        message_lower = message.lower()

        # Extract crop
        crops = ["rice", "wheat", "maize", "soybean", "cotton", "chickpea", "pigeon pea"]
        for crop in crops:
            if crop in message_lower:
                params["crop"] = crop
                break

        # Extract traits
        for trait in KNOWN_TRAIT_PHRASES:
            if trait in message_lower:
                params["trait"] = trait.replace(" ", "_")
                break

        return params

    def _extract_variety_names(self, message: str) -> list[str]:
        """Extract variety names from message"""
        # Look for capitalized words that might be variety names
        words = message.split()
        varieties = []

        for i, word in enumerate(words):
            # Check if word is capitalized and not at start of sentence
            if word[0].isupper() and i > 0:
                # Common variety patterns: IR64, Swarna, Basmati 370
                if len(word) > 2:
                    varieties.append(word)

        return varieties[:5]  # Max 5 varieties

    def _extract_variety_names_for_genomic_selection(self, message: str) -> list[str]:
        """Extract likely variety names while excluding genomics method tokens.

        This avoids treating method acronyms such as ``GBLUP`` or result labels
        such as ``GEBV``/``GEBVs`` as candidate germplasm names in compound
        genomic-selection requests.
        """
        return [
            variety
            for variety in self._extract_variety_names(message)
            if variety.upper() not in GENOMIC_SELECTION_NON_VARIETY_TOKENS
        ]

    def _extract_marker_trait_query(self, message: str) -> str | None:
        """Extract a trait phrase from marker/QTL/GWAS lookup requests.

        Examples that match include:
        - ``Find SNP markers linked to blast resistance``
        - ``Show QTL associations for yield``
        - ``List markers associated with drought tolerance``
        """
        match = re.search(
            MARKER_TRAIT_QUERY_PATTERN,
            message,
            re.IGNORECASE,
        )
        if not match:
            return None

        extracted = match.group(1).strip(" .?!,:;")
        if not extracted:
            return None

        normalized = " ".join(extracted.split())
        normalized_lower = normalized.lower()
        for trait in KNOWN_TRAIT_PHRASES:
            if trait in normalized_lower:
                return trait

        return normalized

    def _is_trial_results_request(self, message_lower: str) -> bool:
        """Return whether the request is asking for a trial summary or ranking surface."""
        if "trial" not in message_lower:
            return False

        if any(phrase in message_lower for phrase in TRIAL_SUMMARY_ACTION_PHRASES):
            return True

        return any(keyword in message_lower for keyword in TRIAL_RESULT_KEYWORDS)

    def _is_trait_summary_request(self, message_lower: str) -> bool:
        """Return whether the request should route to phenotype trait summary."""
        if any(phrase in message_lower for phrase in TRAIT_SUMMARY_ACTION_PHRASES):
            return True

        return (
            "trait" in message_lower
            and any(keyword in message_lower for keyword in ("summarize", "summary", "summarise"))
        )

    def _should_prefer_trial_results_route(
        self,
        *,
        user_message: str,
        message_lower: str,
        detected_domains: set[str],
    ) -> bool:
        """Keep trial-summary prompts on the dedicated trial path unless compound cues are explicit."""
        if not self._is_trial_results_request(message_lower):
            return False

        return not self._has_explicit_cross_domain_cues(
            user_message=user_message,
            message_lower=message_lower,
            detected_domains=detected_domains,
        )

    def _has_explicit_cross_domain_cues(
        self,
        *,
        user_message: str,
        message_lower: str,
        detected_domains: set[str],
    ) -> bool:
        """Return whether the prompt carries explicit signals that it must stay compound."""
        if any(domain in detected_domains for domain in ("weather", "genomics", "protocols")):
            return True

        if self._extract_location(user_message):
            return True

        if any(term in message_lower for term in BREEDING_ENTITY_TERMS):
            return True

        return False

    def _build_trial_results_params(self, message: str) -> dict[str, Any]:
        """Build normalized trial lookup parameters for result and ranking requests."""
        trial_id = self._extract_trial_identifier(message)
        if trial_id:
            return {"trial_id": trial_id}

        params: dict[str, Any] = {}
        if query := self._extract_trial_lookup_query(message):
            params["query"] = query
        else:
            params["query"] = message.strip()

        search_params = self._extract_search_params(message, "trial")
        if crop := search_params.get("crop"):
            params["crop"] = crop
        if location := self._extract_location(message):
            params["location"] = location

        return params

    def _extract_trial_lookup_query(self, message: str) -> str | None:
        """Extract a concise trial lookup phrase from a natural-language question."""
        crop = self._extract_search_params(message, "trial").get("crop")
        best_query: str | None = None
        best_score = -1

        for match in re.finditer(
            r"\b((?:[A-Za-z][\w-]*\s+){0,4}trial)\b",
            message,
            re.IGNORECASE,
        ):
            candidate = self._score_trial_lookup_candidate(
                match.group(1),
                crop=crop,
            )
            if candidate is None:
                continue

            query, score = candidate
            if score > best_score:
                best_query = query
                best_score = score

        if best_query:
            return best_query

        return f"{crop} trial" if crop else None

    def _score_trial_lookup_candidate(
        self,
        candidate: str,
        *,
        crop: str | None,
    ) -> tuple[str, int] | None:
        """Rank a candidate trial phrase so generic lead-in text loses to specific trial names."""
        tokens = candidate.split()
        while tokens and (
            tokens[0].lower() in TRIAL_QUERY_LEADING_STOPWORDS
            or tokens[0].lower() in TRIAL_QUERY_GENERIC_TERMS
            or tokens[0].lower() in TRIAL_QUERY_ACTION_TERMS
        ):
            tokens.pop(0)

        query = " ".join(tokens).strip()
        if not query or query.lower() == "trial":
            return (f"{crop} trial", 1) if crop else None

        descriptor_tokens = tokens[:-1]
        descriptive_tokens = [
            token
            for token in descriptor_tokens
            if token.lower() not in TRIAL_QUERY_LEADING_STOPWORDS
            and token.lower() not in TRIAL_QUERY_GENERIC_TERMS
            and token.lower() not in TRIAL_QUERY_ACTION_TERMS
        ]
        has_proper_noun_anchor = any(
            token[:1].isupper()
            and token.lower() not in TRIAL_QUERY_GENERIC_TERMS
            and token.lower() not in TRIAL_QUERY_ACTION_TERMS
            for token in descriptor_tokens
        )

        if crop and not has_proper_noun_anchor and not descriptive_tokens:
            return f"{crop} trial", 1

        if not has_proper_noun_anchor and not descriptive_tokens:
            return None

        score = len(descriptive_tokens) * 10 + len(tokens)
        if has_proper_noun_anchor:
            score += 5
        if crop and query.lower() == f"{crop} trial":
            score += 1

        return query, score

    def _should_route_cross_domain_query(
        self,
        *,
        detected_domains: set[str],
        message_lower: str,
    ) -> bool:
        """Return whether the request should use the compound cross-domain route.

        The breeding+genomics class is only treated as compound when the prompt
        explicitly mentions breeding entities such as varieties, germplasm, or
        accessions. This keeps pure marker lookups and genomic-selection compute
        requests on their dedicated deterministic routes.
        """
        for domain_class in CROSS_DOMAIN_QUERY_DOMAIN_CLASSES:
            if not domain_class.issubset(detected_domains):
                continue
            if domain_class == frozenset({"breeding", "genomics"}) and not any(
                term in message_lower for term in BREEDING_ENTITY_TERMS
            ):
                continue
            if domain_class == frozenset({"breeding", "protocols"}) and not (
                any(term in message_lower for term in BREEDING_ENTITY_TERMS)
                and any(term in message_lower for term in PROTOCOL_QUERY_TERMS)
                and any(trait in message_lower for trait in KNOWN_TRAIT_PHRASES)
            ):
                continue
            return True
        return False

    def _extract_cross_domain_params(self, message: str) -> dict[str, Any]:
        """Extract normalized parameters for compound breeding/trial/environment requests."""
        params: dict[str, Any] = {"query": message.strip()}

        search_params = self._extract_search_params(message, "cross_domain")
        if crop := search_params.get("crop"):
            params["crop"] = crop
        if trait := self._extract_trait_query(message):
            params["trait"] = trait
        if location := self._extract_location(message):
            params["location"] = location

        if germplasm_identifier := self._extract_germplasm_identifier(message):
            params["germplasm"] = germplasm_identifier

        return params

    def _extract_trait_query(self, message: str) -> str | None:
        """Extract a known breeding trait phrase from a free-form request."""
        message_lower = message.lower()
        for trait in KNOWN_TRAIT_PHRASES:
            if trait in message_lower:
                return trait
        return None

    def _extract_create_trial_params(self, message: str) -> dict[str, Any]:
        """Extract trial creation parameters"""
        params = {}
        message_lower = message.lower()

        # Extract crop
        crops = ["rice", "wheat", "maize"]
        for crop in crops:
            if crop in message_lower:
                params["crop"] = crop
                break

        # Extract location
        location = self._extract_location(message)
        if location:
            params["location"] = location

        # Extract trial type
        trial_types = ["PYT", "AYT", "MLT", "OYT"]
        for trial_type in trial_types:
            if trial_type.lower() in message_lower:
                params["trial_type"] = trial_type
                break

        return params

    def _extract_create_cross_params(self, message: str) -> dict[str, Any]:
        """Extract cross creation parameters"""
        params = {}

        # Look for "between X and Y" pattern
        match = re.search(r'between\s+(\w+)\s+and\s+(\w+)', message, re.IGNORECASE)
        if match:
            params["parent1_id"] = match.group(1)
            params["parent2_id"] = match.group(2)

        return params

    def _extract_location(self, message: str) -> str | None:
        """Extract location from message"""
        # Common breeding stations
        locations = ["Ludhiana", "Delhi", "Hyderabad", "IRRI", "CIMMYT", "Bangalore"]
        message_lower = message.lower()

        for location in locations:
            if location.lower() in message_lower:
                return location

        return None

    def _extract_trial_identifier(self, message: str) -> str | None:
        """Extract an explicit trial identifier from free-form text when present.

        This first checks for prefixed identifiers such as ``TRIAL-22`` or
        ``T-105``, then falls back to contextual matches like ``trial id: 22``.
        Returns the first match found, or ``None`` when neither pattern matches.
        """
        prefixed_match = re.search(TRIAL_ID_PREFIX_PATTERN, message, re.IGNORECASE)
        if prefixed_match:
            return prefixed_match.group(1).replace(" ", "")

        match = re.search(TRIAL_ID_CONTEXT_PATTERN, message, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def _extract_germplasm_identifier(self, message: str) -> str | None:
        """Extract a germplasm/accession token for detail lookups.

        Numeric tokens are treated later as internal germplasm IDs, while
        accession-style identifiers remain query-backed so the search service can
        resolve them safely against external names/accessions.
        """
        match = re.search(GERMPLASM_ID_CONTEXT_PATTERN, message, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if not candidate:
                return None
            if candidate.lower() in GERMPLASM_CONTEXT_STOPWORDS:
                return None
            return candidate

        return None

    def _extract_page_name(self, message: str) -> str | None:
        """Extract page name from navigation request"""
        pages = {
            "dashboard": "/dashboard",
            "programs": "/programs",
            "trials": "/trials",
            "germplasm": "/germplasm",
            "crosses": "/crosses",
            "settings": "/settings",
        }

        message_lower = message.lower()
        for page_name, route in pages.items():
            if page_name in message_lower:
                return route

        return None
