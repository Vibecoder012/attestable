"""Grammar: parsing, construction, round-tripping, and rejection."""

from __future__ import annotations

import pytest

from attestable import (
    Grammar,
    ParsedAnchor,
    chunk_anchor,
    entity_anchor,
    field_anchor,
    is_valid_anchor,
    parse_anchor,
    span_anchor,
)
from attestable.errors import AnchorSyntaxError


def test_entity_anchor_roundtrip() -> None:
    a = entity_anchor("document", "abc-123", 4)
    assert a == "attest://document/abc-123@4"
    p = parse_anchor(a)
    assert p == ParsedAnchor("attest", "document", "abc-123", 4)
    assert p.to_anchor() == a
    assert p.source_key == ("document", "abc-123", 4)


def test_entity_anchor_defaults_to_version_1() -> None:
    assert entity_anchor("note", "n1") == "attest://note/n1@1"


def test_chunk_anchor_roundtrip() -> None:
    a = chunk_anchor("document.sop", "sop-9", 2, "para_7")
    p = parse_anchor(a)
    assert p.fragment == "chunk"
    assert p.chunk_id == "para_7"
    assert p.entity_type == "document.sop"
    assert p.to_anchor() == a


def test_span_anchor_roundtrip() -> None:
    a = span_anchor("document", "d1", 3, "p12", 40, 88)
    p = parse_anchor(a)
    assert p.fragment == "span"
    assert (p.chunk_id, p.start, p.end) == ("p12", 40, 88)
    assert p.to_anchor() == a


def test_field_anchor_roundtrip() -> None:
    a = field_anchor("record", "r1", 1, "/invoice/total")
    p = parse_anchor(a)
    assert p.fragment == "field"
    assert p.json_pointer == "/invoice/total"
    assert p.to_anchor() == a


def test_zero_length_span_is_valid() -> None:
    a = span_anchor("document", "d1", 1, "p1", 5, 5)
    assert parse_anchor(a).start == parse_anchor(a).end == 5


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "attest://Document/d1@1",  # uppercase type
        "attest://document/d1@x",  # non-numeric version
        "attest://document/d1",  # missing version
        "attest://document/d1@1#chunk:",  # empty chunk id
        "attest://document/d1@1#bogus:x",  # unknown fragment
        "http://document/d1@1",  # wrong scheme
        "attest://document/spaces here@1",  # invalid id char
    ],
)
def test_invalid_anchors_raise(bad: str) -> None:
    assert is_valid_anchor(bad) is False
    with pytest.raises(AnchorSyntaxError):
        parse_anchor(bad)


def test_span_start_after_end_rejected() -> None:
    with pytest.raises(AnchorSyntaxError):
        parse_anchor("attest://document/d1@1#span:p1:10-3")


def test_is_valid_never_raises_on_non_str() -> None:
    with pytest.raises(AnchorSyntaxError):
        parse_anchor(123)  # type: ignore[arg-type]


def test_custom_scheme() -> None:
    g = Grammar("myapp")
    a = g.entity("document", "abc", 2)
    assert a == "myapp://document/abc@2"
    assert g.is_valid(a)
    # default-scheme parser must reject a different scheme
    assert is_valid_anchor(a) is False


def test_invalid_scheme_rejected() -> None:
    with pytest.raises(ValueError):
        Grammar("1nope")
