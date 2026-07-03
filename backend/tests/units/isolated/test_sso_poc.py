# BIJMANTRA JULES JOB CARD: D08
# Isolated unit tests for the SSO Integration POC script.

import unittest
import sys
import os
import importlib.util
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the scripts directory to sys.path to allow importing the script
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "scripts"
sys.path.append(str(SCRIPT_DIR))

# Dynamically import the script module
spec = importlib.util.spec_from_file_location("sso_integration_poc", SCRIPT_DIR / "sso_integration_poc.py")
sso_module = importlib.util.module_from_spec(spec)
sys.modules["sso_integration_poc"] = sso_module
spec.loader.exec_module(sso_module)

from sso_integration_poc import OIDCValidator, generate_mock_token

class TestSSOPOC(unittest.TestCase):

    def setUp(self):
        self.issuer = "https://test-idp.com"
        self.client_id = "test-client-id"
        self.user_email = "test@bijmantra.org"
        self.validator = OIDCValidator(self.issuer, self.client_id)

    def test_valid_token(self):
        """Test that a valid token is correctly validated and claims extracted."""
        token = generate_mock_token(self.issuer, self.client_id, self.user_email)
        payload = self.validator.validate_token(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload['email'], self.user_email)
        self.assertEqual(payload['iss'], self.issuer)
        self.assertEqual(payload['aud'], self.client_id)

    def test_expired_token(self):
        """Test that an expired token is rejected."""
        # Generate token expired 1 hour ago
        token = generate_mock_token(self.issuer, self.client_id, self.user_email, expires_in=-3600)

        # Capture logs to verify warning (optional, but good practice)
        with self.assertLogs('sso_integration_poc', level='WARNING') as cm:
            payload = self.validator.validate_token(token)
            self.assertIsNone(payload)
            self.assertTrue(any("Token has expired" in log for log in cm.output))

    def test_wrong_audience(self):
        """Test that a token with the wrong audience is rejected."""
        token = generate_mock_token(self.issuer, "wrong-client", self.user_email)

        # Capture logs to verify warning
        with self.assertLogs('sso_integration_poc', level='WARNING') as cm:
            payload = self.validator.validate_token(token)
            self.assertIsNone(payload)
            # The exact error message depends on python-jose implementation details
            # usually it says "Invalid audience"
            self.assertTrue(any("Invalid claim" in log or "Audience" in log for log in cm.output))

    def test_wrong_issuer(self):
        """Test that a token with the wrong issuer is rejected."""
        token = generate_mock_token("https://wrong-issuer.com", self.client_id, self.user_email)

        with self.assertLogs('sso_integration_poc', level='WARNING') as cm:
            payload = self.validator.validate_token(token)
            self.assertIsNone(payload)
            self.assertTrue(any("Invalid claim" in log or "Issuer" in log for log in cm.output))

    def test_invalid_signature(self):
        """Test that a token with an invalid signature is rejected."""
        valid_token = generate_mock_token(self.issuer, self.client_id, self.user_email)
        # Tamper with the signature part (last part of JWT)
        parts = valid_token.split('.')
        parts[2] = parts[2][:-5] + "XtYqZ" # Change last 5 chars
        tampered_token = ".".join(parts)

        with self.assertLogs('sso_integration_poc', level='WARNING') as cm:
            payload = self.validator.validate_token(tampered_token)
            self.assertIsNone(payload)
            self.assertTrue(any("Invalid token signature" in log or "Signature verification failed" in log for log in cm.output))

if __name__ == '__main__':
    unittest.main()
