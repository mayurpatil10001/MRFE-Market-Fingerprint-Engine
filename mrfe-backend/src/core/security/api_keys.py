"""API key utilities for service accounts."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_api_key(prefix: str = "mrfe") -> str:
    """Generate random API key."""
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str, salt: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(f"{salt}:{api_key}".encode()).hexdigest()


def verify_api_key(api_key: str, expected_hash: str, salt: str) -> bool:
    """Constant-time key hash verification."""
    computed = hash_api_key(api_key, salt)
    return hmac.compare_digest(computed, expected_hash)
