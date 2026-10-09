"""Webhook signatures.

Senders sign each delivery with ``x-churnwise-signature: t=<unix seconds>,v1=<hex hmac>``, where the
HMAC-SHA256 is computed over ``"<t>.<raw body>"`` with the shared secret. Deliveries older (or newer) than
five minutes are rejected to limit replays.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Literal

TOLERANCE_SECONDS = 300
HEADER = "x-churnwise-signature"

FailureReason = Literal["missing", "malformed", "expired", "mismatch"]


@dataclass(frozen=True, slots=True)
class SignatureResult:
    ok: bool
    reason: FailureReason | None = None


def sign(raw_body: bytes | str, secret: str, timestamp: int) -> str:
    """Build a signature header value. Used by tests and by anyone writing a connector."""
    body = raw_body.encode() if isinstance(raw_body, str) else raw_body
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def _parse_header(header: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for item in header.split(","):
        key, sep, value = item.strip().partition("=")
        if sep:
            parts.setdefault(key, value)
    return parts


def verify_signature(
    raw_body: bytes | str,
    header: str | None,
    secret: str,
    now: float | None = None,
    tolerance: int = TOLERANCE_SECONDS,
) -> SignatureResult:
    if not header:
        return SignatureResult(False, "missing")
    parts = _parse_header(header)
    try:
        timestamp = int(parts["t"])
        received = bytes.fromhex(parts["v1"])
    except (KeyError, ValueError):
        return SignatureResult(False, "malformed")
    if not received:
        return SignatureResult(False, "malformed")

    current = time.time() if now is None else now
    if abs(current - timestamp) > tolerance:
        return SignatureResult(False, "expired")

    body = raw_body.encode() if isinstance(raw_body, str) else raw_body
    expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).digest()
    if not hmac.compare_digest(received, expected):
        return SignatureResult(False, "mismatch")
    return SignatureResult(True)
