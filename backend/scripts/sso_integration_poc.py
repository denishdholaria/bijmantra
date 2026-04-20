# BIJMANTRA JULES JOB CARD: D08
# Enterprise SSO Integration POC
# Demonstrates OIDC ID Token validation using python-jose.

import json
import time
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from jose import jwt, jwk
    from jose.utils import base64url_decode
except ImportError:
    logger.error("python-jose is required. Run 'pip install python-jose[cryptography]'")
    exit(1)

# --- Mock Data for POC ---

# 1. Simulate an IdP's Private Key (RSA)
# In a real scenario, this key is held securely by the IdP (Google, Okta, etc.)
# We use this to SIGN our mock token.
MOCK_RSA_KEY = {
    "kty": "RSA",
    "d": "Yi_XJpX6T5_Jg2_1o3_2Q0_... (private part truncated)",
    "e": "AQAB",
    "use": "sig",
    "kid": "mock-key-id-1",
    "alg": "RS256",
    "n": "sXchJZ8h_3zL8_2u2_5A0_... (modulus truncated)"
}

# Real RSA Key Pair for demonstration (generated for this script)
# This is a valid RSA key pair for testing purposes only.
RSA_KEY_PAIR = {
    "kty": "RSA",
    "d": "Eq5xpGnNCivDflJsRQBXHx1hdR1k6Ulwe2UEc50y-ukjczMLCrrM_uBkc3-G5bFz9hZ2x9s2r_2Z4q_1z2_3A0_... (truncated for brevity, using library to generate)",
    "n": "pXchJZ8h_3zL8_2u2_5A0_...",
    "e": "AQAB"
}

# Let's generate a real key pair using python-jose for the POC to be functional
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
public_key = private_key.public_key()
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Convert to JWK format
jwk_private = jwk.construct(private_pem.decode('utf-8'), algorithm="RS256").to_dict()
jwk_public = jwk.construct(public_pem.decode('utf-8'), algorithm="RS256").to_dict()
jwk_public['kid'] = 'mock-key-id-1' # Key ID is important for matching
jwk_private['kid'] = 'mock-key-id-1'


# 2. Simulate the IdP's Public JWKS (JSON Web Key Set)
# This is what the Backend fetches from `https://idp.com/.well-known/jwks.json`
MOCK_JWKS = {
    "keys": [
        jwk_public
    ]
}


class OIDCValidator:
    """
    Validates OIDC ID Tokens using a JWKS endpoint.
    """
    def __init__(self, issuer: str, client_id: str):
        self.issuer = issuer
        self.client_id = client_id
        # In a real app, you would fetch this from the JWKS URI and cache it.
        self.jwks = MOCK_JWKS

    def get_signing_key(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Extracts the 'kid' (Key ID) from the token header and finds the matching key in JWKS.
        """
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')

            if not kid:
                logger.error("Token header missing 'kid' field.")
                return None

            for key in self.jwks['keys']:
                if key['kid'] == kid:
                    return key

            logger.error(f"No matching key found in JWKS for kid: {kid}")
            return None

        except Exception as e:
            logger.error(f"Error getting signing key: {e}")
            return None

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes and verifies the ID Token.
        """
        key = self.get_signing_key(token)
        if not key:
            return None

        try:
            # jwt.decode verifies signature, audience, issuer, and expiration
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=self.issuer,
                options={
                    "verify_at_hash": False # Skip at_hash verification for this POC
                }
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired.")
            return None
        except jwt.JWTClaimsError as e:
            logger.warning(f"Invalid claims: {e}")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Invalid token signature: {e}")
            return None


def generate_mock_token(issuer: str, client_id: str, user_email: str, expires_in: int = 3600) -> str:
    """
    Generates a signed JWT simulating an ID Token from an IdP.
    """
    now = int(time.time())
    claims = {
        "iss": issuer,
        "sub": "user_12345", # Subject identifier (unique user ID)
        "aud": client_id,
        "exp": now + expires_in,
        "iat": now,
        "email": user_email,
        "name": "Jules Agent",
        "roles": ["viewer", "editor"] # Custom claim
    }

    # Sign with our private key
    token = jwt.encode(claims, jwk_private, algorithm="RS256", headers={"kid": jwk_private['kid']})
    return token


def main():
    logger.info("--- Starting Enterprise SSO Integration POC ---")

    # Configuration
    ISSUER = "https://mock-idp.com"
    CLIENT_ID = "bijmantra-app"
    USER_EMAIL = "jules@bijmantra.org"

    # 1. Generate a valid mock token
    logger.info(f"Generating mock token for user: {USER_EMAIL}")
    valid_token = generate_mock_token(ISSUER, CLIENT_ID, USER_EMAIL)
    logger.info(f"Token: {valid_token[:20]}...{valid_token[-20:]}")

    # 2. Validate the token
    validator = OIDCValidator(issuer=ISSUER, client_id=CLIENT_ID)
    logger.info("Validating token...")
    payload = validator.validate_token(valid_token)

    if payload:
        logger.info("✅ Token Validated Successfully!")
        logger.info(f"User Email: {payload.get('email')}")
        logger.info(f"User Roles: {payload.get('roles')}")
    else:
        logger.error("❌ Token Validation Failed!")

    # 3. Demonstrate validation failure (Expired Token)
    logger.info("\n--- Testing Expired Token ---")
    expired_token = generate_mock_token(ISSUER, CLIENT_ID, USER_EMAIL, expires_in=-3600) # Expired 1 hour ago
    payload_expired = validator.validate_token(expired_token)

    if not payload_expired:
         logger.info("✅ Correctly rejected expired token.")
    else:
         logger.error("❌ Failed to reject expired token!")

    # 4. Demonstrate validation failure (Wrong Audience)
    logger.info("\n--- Testing Wrong Audience ---")
    wrong_aud_token = generate_mock_token(ISSUER, "wrong-client-id", USER_EMAIL)
    payload_wrong_aud = validator.validate_token(wrong_aud_token)

    if not payload_wrong_aud:
         logger.info("✅ Correctly rejected token with wrong audience.")
    else:
         logger.error("❌ Failed to reject token with wrong audience!")


if __name__ == "__main__":
    main()
