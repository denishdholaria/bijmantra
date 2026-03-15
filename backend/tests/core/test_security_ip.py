import pytest
from fastapi import Request
from app.core.security import get_client_ip, is_ip_trusted
from app.core.config import settings

def mock_request(client_host: str, headers: dict = None):
    scope = {
        "type": "http",
        "client": (client_host, 12345),
        "headers": []
    }
    if headers:
        for k, v in headers.items():
            scope["headers"].append((k.lower().encode(), v.encode()))

    request = Request(scope)
    return request

@pytest.fixture(autouse=True)
def reset_settings():
    original = settings.TRUSTED_PROXIES
    yield
    settings.TRUSTED_PROXIES = original

class TestSecurityIP:

    def test_direct_connection_untrusted(self):
        # Scenario: No trusted proxies configured.
        # Request comes from 1.2.3.4
        settings.TRUSTED_PROXIES = []
        req = mock_request("1.2.3.4")
        assert get_client_ip(req) == "1.2.3.4"

    def test_direct_connection_with_spoofed_header_untrusted(self):
        # Scenario: Attacker sends X-Forwarded-For, but we don't trust any proxies.
        settings.TRUSTED_PROXIES = []
        req = mock_request("1.2.3.4", {"X-Forwarded-For": "5.6.7.8"})
        # Should ignore header and return peer IP
        assert get_client_ip(req) == "1.2.3.4"

    def test_trusted_proxy_single(self):
        # Scenario: We trust 10.0.0.1. Request comes from 10.0.0.1.
        # Header has real client IP.
        settings.TRUSTED_PROXIES = ["10.0.0.1"]
        req = mock_request("10.0.0.1", {"X-Forwarded-For": "5.6.7.8"})
        assert get_client_ip(req) == "5.6.7.8"

    def test_trusted_proxy_spoofed(self):
        # Scenario: Attacker (1.2.3.4) sends "X-Forwarded-For: spoofed".
        # Connects to trusted proxy (10.0.0.1).
        # Proxy appends attacker IP. Header: "spoofed, 1.2.3.4".
        settings.TRUSTED_PROXIES = ["10.0.0.1"]
        req = mock_request("10.0.0.1", {"X-Forwarded-For": "spoofed, 1.2.3.4"})

        # Logic:
        # remote=10.0.0.1 (Trusted)
        # Check XFF reversed:
        # 1. 1.2.3.4 (Untrusted) -> Return 1.2.3.4
        assert get_client_ip(req) == "1.2.3.4"

    def test_multiple_trusted_proxies(self):
        # Scenario: Client (5.6.7.8) -> LB (10.0.0.2) -> Nginx (10.0.0.1) -> App.
        # We trust 10.0.0.1 and 10.0.0.2.
        # Header at App: "5.6.7.8, 10.0.0.2".
        # Remote: 10.0.0.1.
        settings.TRUSTED_PROXIES = ["10.0.0.1", "10.0.0.2"]
        req = mock_request("10.0.0.1", {"X-Forwarded-For": "5.6.7.8, 10.0.0.2"})

        # Logic:
        # remote=10.0.0.1 (Trusted)
        # Check XFF reversed:
        # 1. 10.0.0.2 (Trusted) -> Continue
        # 2. 5.6.7.8 (Untrusted) -> Return 5.6.7.8
        assert get_client_ip(req) == "5.6.7.8"

    def test_cidr_trusted_proxy(self):
        # Scenario: Trust 10.0.0.0/8.
        settings.TRUSTED_PROXIES = ["10.0.0.0/8"]
        req = mock_request("10.5.5.5", {"X-Forwarded-For": "1.2.3.4"})
        assert get_client_ip(req) == "1.2.3.4"

    def test_cidr_untrusted_proxy(self):
        settings.TRUSTED_PROXIES = ["10.0.0.0/8"]
        req = mock_request("192.168.1.1", {"X-Forwarded-For": "1.2.3.4"})
        assert get_client_ip(req) == "192.168.1.1"

    def test_x_real_ip_trusted(self):
        settings.TRUSTED_PROXIES = ["10.0.0.1"]
        req = mock_request("10.0.0.1", {"X-Real-IP": "5.6.7.8"})
        assert get_client_ip(req) == "5.6.7.8"

    def test_x_real_ip_untrusted(self):
        settings.TRUSTED_PROXIES = []
        req = mock_request("10.0.0.1", {"X-Real-IP": "5.6.7.8"})
        assert get_client_ip(req) == "10.0.0.1"

    def test_recursive_trust_all_trusted(self):
         # Scenario: Internal service call through proxy chain.
         # Client (10.0.0.3) -> Proxy (10.0.0.2) -> App.
         # All trusted.
         settings.TRUSTED_PROXIES = ["10.0.0.0/8"]
         req = mock_request("10.0.0.2", {"X-Forwarded-For": "10.0.0.3"})
         assert get_client_ip(req) == "10.0.0.3"
