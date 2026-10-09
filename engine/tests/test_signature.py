from __future__ import annotations

import pytest

from churnwise.billing.signature import TOLERANCE_SECONDS, sign, verify_signature

SECRET = "whsec_unit"
BODY = '{"id":"evt_1"}'
NOW = 1_790_000_000


def test_round_trip():
    header = sign(BODY, SECRET, NOW)
    assert verify_signature(BODY, header, SECRET, now=NOW).ok
    assert verify_signature(BODY.encode(), header, SECRET, now=NOW + TOLERANCE_SECONDS).ok


def test_known_vector():
    # HMAC-SHA256("whsec_unit", "1790000000.{\"id\":\"evt_1\"}"), computed independently with openssl.
    expected = "f63e7e759e7ddf8823c51eb3cc16d2d2e7209621a6770158bcececc3565f9304"
    assert sign(BODY, SECRET, NOW) == f"t=1790000000,v1={expected}"


@pytest.mark.parametrize(
    ("header", "reason"),
    [
        (None, "missing"),
        ("", "missing"),
        ("v1=abc", "malformed"),
        ("t=abc,v1=00", "malformed"),
        ("t=1790000000,v1=zz", "malformed"),
        ("t=1790000000", "malformed"),
        ("t=1790000000,v1=", "malformed"),
    ],
)
def test_rejects_missing_or_malformed_headers(header, reason):
    result = verify_signature(BODY, header, SECRET, now=NOW)
    assert (result.ok, result.reason) == (False, reason)


def test_rejects_stale_and_future_deliveries():
    header = sign(BODY, SECRET, NOW)
    assert verify_signature(BODY, header, SECRET, now=NOW + TOLERANCE_SECONDS + 1).reason == "expired"
    assert verify_signature(BODY, header, SECRET, now=NOW - TOLERANCE_SECONDS - 1).reason == "expired"


def test_rejects_tampering_and_wrong_secrets():
    header = sign(BODY, SECRET, NOW)
    assert verify_signature(BODY + " ", header, SECRET, now=NOW).reason == "mismatch"
    assert verify_signature(BODY, header, "other", now=NOW).reason == "mismatch"
    assert verify_signature(BODY, header.replace("v1=", "v1=00"), SECRET, now=NOW).reason == "mismatch"


def test_extra_header_parts_are_ignored():
    header = sign(BODY, SECRET, NOW) + ",v0=legacy"
    assert verify_signature(BODY, f" {header} ", SECRET, now=NOW).ok
