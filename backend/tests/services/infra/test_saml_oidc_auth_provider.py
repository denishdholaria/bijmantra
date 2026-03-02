import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import base64
import zlib
import xml.etree.ElementTree as ET

# Ensure backend is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from app.services.infra.saml_oidc_auth_provider import (
    SSOConfig,
    OIDCAuthProvider,
    SAMLAuthProvider,
    AuthUser,
    AuthError
)

class TestOIDCAuthProvider(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = SSOConfig(
            provider_id="test-oidc",
            type="oidc",
            name="Test OIDC",
            client_id="client-123",
            client_secret="secret-123",
            discovery_url="https://idp.example.com/.well-known/openid-configuration"
        )
        self.provider = OIDCAuthProvider(self.config)

    @patch("httpx.AsyncClient")
    async def test_discovery_and_login_url(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client

        # Configure client.get as an AsyncMock so it can be awaited
        mock_client.get = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "authorization_endpoint": "https://idp.example.com/auth",
            "token_endpoint": "https://idp.example.com/token",
            "userinfo_endpoint": "https://idp.example.com/userinfo",
            "jwks_uri": "https://idp.example.com/keys",
            "issuer": "https://idp.example.com"
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        url = await self.provider.get_login_url("state123", "http://callback")

        self.assertIn("https://idp.example.com/auth", url)
        self.assertIn("client_id=client-123", url)
        self.assertIn("state=state123", url)

        # Verify config was updated
        self.assertEqual(self.config.authorization_endpoint, "https://idp.example.com/auth")

    @patch("app.services.infra.saml_oidc_auth_provider.jwt")
    @patch("httpx.AsyncClient")
    async def test_validate_callback_success(self, mock_client_cls, mock_jwt):
        # Pre-populate endpoints to skip discovery
        self.config.token_endpoint = "https://idp.example.com/token"
        self.config.authorization_endpoint = "https://idp.example.com/auth" # satisfy check in _discover if it runs?
        # Actually _discover_endpoints checks if (auth AND token) are set.
        # But discovery_url is set, so it might try to run if logic is not perfect.
        # Logic: if discovery_url and not (auth and token): run discovery.
        # I set token_endpoint, but need authorization_endpoint too to skip discovery or mock discovery too.

        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client

        # Mock Discovery (just in case)
        mock_client.get = AsyncMock()

        # Mock Token Response
        mock_client.post = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id_token": "mock.id.token",
            "access_token": "mock.access.token"
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        # Mock JWT Decode
        mock_jwt.get_unverified_claims.return_value = {
            "sub": "user-123",
            "email": "test@example.com",
            "name": "Test User"
        }

        user = await self.provider.validate_callback("code123", "state123", "http://callback")

        self.assertIsInstance(user, AuthUser)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.external_id, "user-123")
        self.assertEqual(user.provider_id, "test-oidc")

class TestSAMLAuthProvider(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = SSOConfig(
            provider_id="test-saml",
            type="saml",
            name="Test SAML",
            sp_entity_id="http://sp.example.com",
            idp_sso_url="https://idp.example.com/sso"
        )
        self.provider = SAMLAuthProvider(self.config)

    async def test_get_login_url(self):
        url = await self.provider.get_login_url("state123", "http://callback")
        self.assertIn("https://idp.example.com/sso", url)
        self.assertIn("SAMLRequest=", url)
        self.assertIn("RelayState=state123", url)

    async def test_validate_callback_success(self):
        # Construct a mock SAML Response XML
        xml = """<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
            <saml:Assertion>
                <saml:Subject>
                    <saml:NameID>user@example.com</saml:NameID>
                </saml:Subject>
                <saml:AttributeStatement>
                    <saml:Attribute Name="email">
                        <saml:AttributeValue>user@example.com</saml:AttributeValue>
                    </saml:Attribute>
                    <saml:Attribute Name="name">
                        <saml:AttributeValue>SAML User</saml:AttributeValue>
                    </saml:Attribute>
                </saml:AttributeStatement>
            </saml:Assertion>
        </samlp:Response>"""

        encoded_xml = base64.b64encode(xml.encode('utf-8')).decode('utf-8')

        user = await self.provider.validate_callback(None, "state123", "http://callback", SAMLResponse=encoded_xml)

        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.name, "SAML User")
        self.assertEqual(user.provider_id, "test-saml")

if __name__ == "__main__":
    unittest.main()
