"""The Derived envelope enforces its invariants at construction."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from attestable import Derived, derive, entity_anchor, span_anchor
from attestable.errors import ProvenanceError

ANCHOR = entity_anchor("document", "d1", 1)


def test_valid_derived() -> None:
    d = Derived(value=42, confidence=0.8, provenance=[ANCHOR])
    assert d.value == 42
    assert d.confidence == 0.8
    assert d.provenance == (ANCHOR,)  # normalised to a tuple


def test_provenance_required() -> None:
    with pytest.raises(ProvenanceError, match="at least one provenance anchor"):
        Derived(value="x", confidence=1.0, provenance=[])


@pytest.mark.parametrize("bad", [-0.1, 1.1, 2, -1])
def test_confidence_range_enforced(bad: float) -> None:
    with pytest.raises(ProvenanceError):
        Derived(value="x", confidence=bad, provenance=[ANCHOR])


def test_confidence_bounds_inclusive() -> None:
    assert Derived("x", 0.0, [ANCHOR]).confidence == 0.0
    assert Derived("x", 1.0, [ANCHOR]).confidence == 1.0


def test_bool_confidence_rejected() -> None:
    # bool is an int subclass; a True confidence is almost always a bug.
    with pytest.raises(ProvenanceError):
        Derived(value="x", confidence=True, provenance=[ANCHOR])  # type: ignore[arg-type]


def test_invalid_anchor_in_provenance_rejected() -> None:
    with pytest.raises(ProvenanceError, match="invalid provenance anchor"):
        Derived(value="x", confidence=0.5, provenance=["not-an-anchor"])


def test_frozen() -> None:
    d = Derived(value=1, confidence=0.5, provenance=[ANCHOR])
    with pytest.raises(FrozenInstanceError):
        d.value = 2  # type: ignore[misc]


def test_to_from_dict_roundtrip() -> None:
    span = span_anchor("document", "d1", 2, "p1", 0, 10)
    d = Derived(value={"date": "2026-01-15"}, confidence=0.9, provenance=[ANCHOR, span])
    payload = d.to_dict()
    assert json.loads(json.dumps(payload)) == payload  # JSON-serialisable
    restored = Derived.from_dict(payload)
    assert restored == d


def test_from_dict_revalidates() -> None:
    with pytest.raises(ProvenanceError):
        Derived.from_dict({"value": 1, "confidence": 5, "provenance": [ANCHOR]})


def test_with_value_preserves_metadata() -> None:
    d = Derived(value=1, confidence=0.7, provenance=[ANCHOR])
    d2 = d.with_value("changed")
    assert d2.value == "changed"
    assert d2.confidence == 0.7
    assert d2.provenance == d.provenance


def test_derive_helper() -> None:
    d = derive("v", 0.5, (ANCHOR,))
    assert isinstance(d, Derived)
    assert d.value == "v"
