"""
TurboShare — Session token generation and validation.

Tokens are 12-character URL-safe alphanumeric strings embedded in the
session URL path. Comparison is constant-time to prevent timing attacks.
"""

import hmac
import secrets
import string

from src.core.config import TOKEN_LENGTH

_ALPHABET = string.ascii_letters + string.digits


def generate_token(length: int = TOKEN_LENGTH) -> str:
    """Return a cryptographically random alphanumeric token."""
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def validate_token(provided: str, expected: str) -> bool:
    """Constant-time comparison of two tokens."""
    return hmac.compare_digest(provided.encode(), expected.encode())
