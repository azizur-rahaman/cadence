"""HMAC-SHA256 signed session tokens using deterministic Clock timestamps."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime


class InvalidTokenError(ValueError):
    """Raised when a session token is missing, malformed, or fails signature verification."""


@dataclass(frozen=True)
class TokenPayload:
    user_id: str
    role: str
    issued_at: int


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def create_access_token(
    *,
    user_id: str,
    role: str,
    secret: str,
    issued_at: datetime,
) -> str:
    """Create a compact HMAC-SHA256 signed session token."""
    body = {
        "sub": user_id,
        "role": role,
        "iat": int(issued_at.timestamp()),
    }
    payload_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)
    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{payload_b64}.{sig_b64}"


def verify_access_token(token: str, *, secret: str) -> TokenPayload:
    """Verify signature and decode a signed session token."""
    parts = token.strip().split(".")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise InvalidTokenError("Malformed session token")

    payload_b64, sig_b64 = parts
    expected_sig = hmac.new(
        secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
    ).digest()
    try:
        provided_sig = _b64url_decode(sig_b64)
    except Exception as exc:
        raise InvalidTokenError("Invalid token encoding") from exc

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise InvalidTokenError("Invalid token signature")

    try:
        raw = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        sub = raw["sub"]
        role = raw["role"]
        iat = raw["iat"]
    except Exception as exc:
        raise InvalidTokenError("Invalid token payload") from exc

    if not isinstance(sub, str) or not isinstance(role, str) or not isinstance(iat, int):
        raise InvalidTokenError("Invalid token claims")

    return TokenPayload(user_id=sub, role=role, issued_at=iat)
