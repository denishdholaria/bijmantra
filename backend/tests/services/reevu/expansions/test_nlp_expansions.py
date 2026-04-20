"""
Tests for REEVU NLP Expansions (Domain Detection)
"""

import pytest

from app.modules.ai.services.reevu.expansions.domain_matcher import DomainMatcher
from app.modules.ai.services.reevu.expansions.nlp_token_normalizer import NLPTokenNormalizer


class TestNLPTokenNormalizer:
    @pytest.fixture
    def normalizer(self):
        return NLPTokenNormalizer()

    def test_normalize_basic(self, normalizer):
        text = "Hello World! This is a Test."
        tokens = normalizer.normalize(text)
        # "Hello", "World", "Test" -> "hello", "world", "test"
        # "This", "is", "a" are stopwords (check list)
        # "this", "is", "a" are in STOP_WORDS
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert "is" not in tokens
        assert "a" not in tokens
        assert "this" not in tokens

    def test_normalize_punctuation(self, normalizer):
        text = "genomics, breeding; (trials) & weather."
        tokens = normalizer.normalize(text)
        expected = ["genomics", "breeding", "trials", "weather"]
        assert sorted(tokens) == sorted(expected)

    def test_normalize_empty(self, normalizer):
        assert normalizer.normalize("") == []
        assert normalizer.normalize(None) == []

    def test_normalize_numbers(self, normalizer):
        text = "Plot 123 in Block 4."
        tokens = normalizer.normalize(text)
        # "plot", "123", "block", "4" -> "plot", "block" (numbers might be kept? Regex allows 0-9)
        # The regex is `[a-zA-Z0-9]+`
        # "in" is stopword
        assert "plot" in tokens
        assert "block" in tokens
        assert "123" in tokens
        assert "4" in tokens


class TestDomainMatcher:
    @pytest.fixture
    def matcher(self):
        return DomainMatcher()

    def test_detect_genomics(self, matcher):
        tokens = ["snp", "marker", "genotype", "dna", "sequencing"]
        result = matcher.detect_domain(tokens)
        assert result["primary_domain"] == "GENOMICS"
        assert result["confidence"] > 0.8
        assert result["scores"]["GENOMICS"] == 5

    def test_detect_trials(self, matcher):
        tokens = ["field", "plot", "yield", "harvest", "experiment"]
        result = matcher.detect_domain(tokens)
        assert result["primary_domain"] == "TRIALS"
        assert result["scores"]["TRIALS"] == 5

    def test_detect_mixed_ambiguous(self, matcher):
        # "breeding" is in GENOMICS and BREEDING
        # "selection" is in GENOMICS and BREEDING
        # "program" is in BREEDING
        tokens = ["breeding", "selection", "program", "variety"]
        result = matcher.detect_domain(tokens)
        # BREEDING: breeding, selection, program, variety = 4 matches
        # GENOMICS: breeding, selection = 2 matches
        assert result["primary_domain"] == "BREEDING"
        assert result["scores"]["BREEDING"] == 4
        assert result["scores"]["GENOMICS"] >= 2

    def test_detect_unknown(self, matcher):
        tokens = ["lorem", "ipsum", "dolor", "sit", "amet"]
        result = matcher.detect_domain(tokens)
        assert result["primary_domain"] == "UNKNOWN"
        assert result["confidence"] == 0.0

    def test_detect_weather(self, matcher):
        tokens = ["temperature", "humidity", "rainfall", "precipitation"]
        result = matcher.detect_domain(tokens)
        assert result["primary_domain"] == "WEATHER"
