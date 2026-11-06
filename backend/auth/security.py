"""
Cryptographic Security & JWT Token Service for Vibe Finance.
Implements RFC 7519 JSON Web Tokens (HS256) and PBKDF2-SHA256 password hashing
using Python's standard library cryptographic primitives (hashlib, hmac, secrets).

Guarantees:
- Zero third-party dependency (eliminates C-extension build issues on various OSes).
- Secure random salt generation (16 bytes) per password hash.
- Constant-time string comparison (`secrets.compare_digest`) preventing timing attacks.
- Tamper-evident JWT token encoding and verification with configurable expiration.
"""
import os
import time
import json
import hmac
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional

# JWT Signing Secret (Defaults to environment variable or secure fallback)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "vibe-finance-super-secret-jwt-signing-key-2026-production")
JWT_ALGORITHM = "HS256"
DEFAULT_TOKEN_EXPIRY_MINUTES = 60 * 24  # 24 Hours


# --- Base64URL Encoding / Decoding Helpers ---

def _base64url_encode(data: bytes) -> str:
    """Encodes bytes to URL-safe Base64 without trailing '=' padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data_str: str) -> bytes:
    """Decodes URL-safe Base64 with automatic padding restoration."""
    rem = len(data_str) % 4
    if rem > 0:
        data_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))


# --- Password Hashing (PBKDF2-SHA256) ---

def hash_password(password: str, iterations: int = 100_000) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a unique 16-byte random salt.
    Format returned: 'pbkdf2_sha256$<iterations>$<hex_salt>$<hex_hash>'
    """
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored PBKDF2-HMAC-SHA256 hash
    using constant-time comparison to prevent timing attacks.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        stored_key = bytes.fromhex(parts[3])

        computed_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return secrets.compare_digest(computed_key, stored_key)
    except Exception:
        return False


# --- JSON Web Token (JWT) HS256 Implementation ---

def create_access_token(
    payload_data: Dict[str, Any],
    expires_minutes: int = DEFAULT_TOKEN_EXPIRY_MINUTES,
    secret_key: str = JWT_SECRET_KEY
) -> str:
    """
    Generates a signed HS256 JWT access token.
    Appends 'iat' (issued-at) and 'exp' (expiration) timestamps automatically.
    """
    now = int(time.time())
    payload = payload_data.copy()
    payload["iat"] = now
    payload["exp"] = now + (expires_minutes * 60)

    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}

    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"

    signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256
    ).digest()
    signature_b64 = _base64url_encode(signature)

    return f"{signing_input}.{signature_b64}"


def decode_access_token(token: str, secret_key: str = JWT_SECRET_KEY) -> Optional[Dict[str, Any]]:
    """
    Validates and decodes an HS256 JWT access token.
    Verifies cryptographic HMAC signature, structure, and token expiration.
    Returns payload dictionary if valid, or None if invalid or expired.
    """
    if not token or not isinstance(token, str):
        return None

    parts = token.strip().split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"

    # 1. Verify HMAC Signature (Constant-Time)
    expected_sig = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256
    ).digest()
    expected_sig_b64 = _base64url_encode(expected_sig)

    if not secrets.compare_digest(signature_b64, expected_sig_b64):
        return None

    # 2. Parse Header & Payload
    try:
        header = json.loads(_base64url_decode(header_b64).decode("utf-8"))
        if header.get("alg") != JWT_ALGORITHM:
            return None

        payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None

    # 3. Verify Expiration
    now = int(time.time())
    exp = payload.get("exp")
    if exp is not None and now > exp:
        return None

    return payload
