"""
NLP Token Normalizer — Stage C (Expansions)

Provides standalone text normalization for REEVU domain detection.
Operates purely on string manipulation and regex to avoid heavy NLP dependencies.
"""

from __future__ import annotations

import re


class NLPTokenNormalizer:
    """Normalizes raw text into a clean list of tokens for downstream analysis."""

    # Simple English stop words to reduce noise
    STOP_WORDS = {
        "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
        "where", "when", "how", "who", "which", "this", "that", "these", "those",
        "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did",
        "at", "by", "for", "from", "in", "into", "of", "off", "on", "onto",
        "over", "to", "up", "with", "within", "without",
        "can", "could", "will", "would", "shall", "should", "may", "might", "must",
        "it", "its", "their", "them", "they", "we", "us", "our", "you", "your",
        "i", "me", "my", "he", "him", "his", "she", "her", "hers",
    }

    # Regex to capture words (alphanumeric sequences)
    # This pattern treats hyphenated words as separate tokens if spaces surround them,
    # or keeps them if they are part of the word (depending on split).
    # Here we split by non-alphanumeric chars except maybe internal hyphens?
    # For simplicity and domain matching, splitting on non-alphanumeric is usually safer.
    _TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")

    def normalize(self, text: str) -> list[str]:
        """
        Tokenize and normalize input text.

        Steps:
        1. Lowercase the text.
        2. Extract alphanumeric tokens.
        3. Remove stop words.
        4. Return unique list of tokens (or ordered list? Ordered is better for context).
        """
        if not text:
            return []

        # 1. Lowercase
        text_lower = text.lower()

        # 2. Extract tokens
        tokens = self._TOKEN_PATTERN.findall(text_lower)

        # 3. Filter stop words and short tokens (optional, but keep 1-letter words if relevant?)
        # For domain detection, 1-letter words are rarely useful except maybe 'g' matrix?
        # Let's keep them if not in stop words.
        filtered_tokens = [
            t for t in tokens
            if t not in self.STOP_WORDS
        ]

        return filtered_tokens
