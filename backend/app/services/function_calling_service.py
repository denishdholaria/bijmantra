"""
Function Calling Service using FunctionGemma

Detects user intent and converts natural language to function calls.
Uses FunctionGemma (270M) for efficient function calling.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
import httpx

from app.schemas.functions import BIJMANTRA_FUNCTIONS, format_functions_for_prompt

logger = logging.getLogger(__name__)


class FunctionCall:
    """Represents a detected function call"""

    def __init__(self, name: str, parameters: Dict[str, Any], confidence: float = 1.0):
        self.name = name
        self.parameters = parameters
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
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

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = "google/functiongemma-270m-it"
        self.base_url = "https://api-inference.huggingface.co/models"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def detect_function_call(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Optional[FunctionCall]:
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
        conversation_history: Optional[List[Dict]] = None
    ) -> Optional[FunctionCall]:
        """Use FunctionGemma API to detect function calls"""

        # Build prompt with function definitions
        functions_text = format_functions_for_prompt()

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
                    logger.info(f"FunctionGemma detected: {function_call.name}")
                    return function_call

            else:
                logger.error(f"FunctionGemma API error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"FunctionGemma API exception: {e}")
            raise

        return None

    def _parse_function_json(self, text: str) -> Optional[FunctionCall]:
        """Parse function call from JSON text"""
        try:
            # Try to find JSON in the text
            json_match = re.search(r'\{[^}]+\}', text)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)

                function_name = data.get("function")
                if function_name and function_name != "null":
                    parameters = data.get("parameters", {})
                    return FunctionCall(function_name, parameters)

        except json.JSONDecodeError:
            logger.debug(f"Failed to parse JSON from: {text}")

        return None

    def _detect_with_patterns(self, user_message: str) -> Optional[FunctionCall]:
        """
        Fallback: Use pattern matching to detect function calls.
        
        This is a simple rule-based system for when FunctionGemma is unavailable.
        """
        message_lower = user_message.lower()

        # Search patterns
        if any(word in message_lower for word in ["search", "find", "show me", "list"]):
            if "germplasm" in message_lower or "variety" in message_lower or "varieties" in message_lower:
                params = self._extract_search_params(user_message, "germplasm")
                return FunctionCall("search_germplasm", params, confidence=0.7)

            elif "trial" in message_lower:
                params = self._extract_search_params(user_message, "trial")
                return FunctionCall("search_trials", params, confidence=0.7)

            elif "cross" in message_lower:
                params = self._extract_search_params(user_message, "cross")
                return FunctionCall("search_crosses", params, confidence=0.7)

            elif "accession" in message_lower:
                params = self._extract_search_params(user_message, "accession")
                return FunctionCall("search_accessions", params, confidence=0.7)

        # Compare patterns
        if "compare" in message_lower:
            if "germplasm" in message_lower or "variety" in message_lower:
                # Try to extract variety names
                varieties = self._extract_variety_names(user_message)
                if varieties:
                    return FunctionCall("compare_germplasm", {
                        "germplasm_ids": varieties
                    }, confidence=0.6)

        # Proposal Patterns
        if "create" in message_lower and "trial" in message_lower:
            params = self._extract_create_trial_params(user_message)
            return FunctionCall("propose_create_trial", params, confidence=0.7)

        if ("create" in message_lower or "make" in message_lower) and "cross" in message_lower:
            params = self._extract_create_cross_params(user_message)
            return FunctionCall("propose_create_cross", params, confidence=0.7)

        if "record" in message_lower and ("observation" in message_lower or "score" in message_lower):
            # Simple extraction for observation
            # Ideally needs more complex extraction logic, but this is fallback
            return FunctionCall("propose_record_observation", {
                "trial_id": "extract_from_context", # Placeholder
                "date": "today"
            }, confidence=0.5)



        # Weather patterns
        if "weather" in message_lower:
            location = self._extract_location(user_message)
            return FunctionCall("get_weather_forecast", {
                "location": location or "current",
                "days": 7
            }, confidence=0.7)

        # Navigate patterns
        if any(word in message_lower for word in ["go to", "open", "navigate"]):
            page = self._extract_page_name(user_message)
            if page:
                return FunctionCall("navigate_to", {"page": page}, confidence=0.8)

        return None

    def _extract_search_params(self, message: str, entity_type: str) -> Dict[str, Any]:
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
        traits = ["blast resistance", "drought tolerance", "yield", "height", "maturity"]
        for trait in traits:
            if trait in message_lower:
                params["trait"] = trait.replace(" ", "_")
                break

        return params

    def _extract_variety_names(self, message: str) -> List[str]:
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

    def _extract_create_trial_params(self, message: str) -> Dict[str, Any]:
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

    def _extract_create_cross_params(self, message: str) -> Dict[str, Any]:
        """Extract cross creation parameters"""
        params = {}

        # Look for "between X and Y" pattern
        match = re.search(r'between\s+(\w+)\s+and\s+(\w+)', message, re.IGNORECASE)
        if match:
            params["parent1_id"] = match.group(1)
            params["parent2_id"] = match.group(2)

        return params

    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location from message"""
        # Common breeding stations
        locations = ["Ludhiana", "Delhi", "Hyderabad", "IRRI", "CIMMYT", "Bangalore"]
        message_lower = message.lower()

        for location in locations:
            if location.lower() in message_lower:
                return location

        return None

    def _extract_page_name(self, message: str) -> Optional[str]:
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
