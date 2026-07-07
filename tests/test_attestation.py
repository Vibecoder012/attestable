"""Tamper-evident attestations, keyed and unkeyed."""

from __future__ import annotations

import pytest

from attestable import Attestation, Derived, attest, entity_anchor, verify
from attestable.errors import AttestationError

ANCHOR = entity_anchor("document", "d1", 1)


def _d(value: object = "2026-01-15", confidence: float = 0.9) -> Derived[object]:
    return Derived(value=value, confidence=confidence, provenance=[ANCHOR])


def test_unkeyed_roundtrip() -> None:
    d = _d()
    token = attest(d)
    assert token.algorithm == "sha256"
    assert token.keyed is False
    assert verify(d, token) is True


def test_unkeyed_is_deterministic_and_stable() -> None:
    # A fixed input must always produce the same digest (cross-process stability).
    d = _d(value="2026-01-15", confidence=0.9)
    token = attest(d)
    assert token.digest == attest(_d(value="2026-01-15", confidence=0.9)).digest


def test_tampering_value_breaks_verification() -> None:
    d = _d()
    token = attest(d)
    assert verify(d.with_value("2026-02-02"), token) is False


def test_tampering_confidence_breaks_verification() -> None:
    d = _d(confidence=0.9)
    token = attest(d)
    assert verify(_d(confidence=0.91), token) is False


def test_keyed_roundtrip() -> None:
    d = _d()
    token = attest(d, key="s3cret")
    assert token.algorithm == "hmac-sha256"
    assert token.keyed is True
    assert verify(d, token, key="s3cret") is True


def test_keyed_wrong_key_fails() -> None:
    d = _d()
    token = attest(d, key="s3cret")
    assert verify(d, token, key="other") is False


def test_keyed_and_unkeyed_do_not_cross_verify() -> None:
    d = _d()
    unkeyed = attest(d)
    keyed = attest(d, key="k")
    assert verify(d, unkeyed, key="k") is False  # unkeyed token, key supplied
    assert verify(d, keyed) is False  # keyed token, no key


def test_bytes_key_equivalent_to_str_key() -> None:
    d = _d()
    assert attest(d, key="abc").digest == attest(d, key=b"abc").digest


def test_dict_value_attestation() -> None:
    d = Derived(value={"total": 1299, "currency": "GBP"}, confidence=0.8, provenance=[ANCHOR])
    token = attest(d)
    assert verify(d, token) is True


def test_non_serialisable_value_raises() -> None:
    d = Derived(value=object(), confidence=0.5, provenance=[ANCHOR])
    with pytest.raises(AttestationError):
        attest(d)


def test_attestation_dict_roundtrip() -> None:
    token = attest(_d())
    assert Attestation.from_dict(token.to_dict()) == token
