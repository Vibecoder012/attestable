"""Resolving anchors and detecting dangling citations."""

from __future__ import annotations

from attestable import (
    Derived,
    InMemoryResolver,
    Resolver,
    chunk_anchor,
    dangling_in,
    entity_anchor,
    field_anchor,
    find_dangling,
    parse_anchor,
    resolve_all,
    span_anchor,
)


def _resolver() -> InMemoryResolver:
    r = InMemoryResolver()
    r.put(
        "document",
        "d1",
        1,
        "The quick brown fox jumps over the lazy dog.",
        chunks={"p1": "The quick brown fox", "p2": "jumps over the lazy dog"},
    )
    return r


def test_inmemory_is_a_resolver() -> None:
    assert isinstance(InMemoryResolver(), Resolver)


def test_resolve_span_slices_text() -> None:
    r = _resolver()
    a = span_anchor("document", "d1", 1, "p1", 4, 9)  # "quick"
    got = r.resolve(parse_anchor(a))
    assert got is not None
    assert got.text == "quick"
    assert got.metadata["start"] == 4


def test_resolve_chunk() -> None:
    r = _resolver()
    got = r.resolve(parse_anchor(chunk_anchor("document", "d1", 1, "p2")))
    assert got is not None
    assert got.text == "jumps over the lazy dog"


def test_resolve_entity_returns_full_text() -> None:
    r = _resolver()
    got = r.resolve(parse_anchor(entity_anchor("document", "d1", 1)))
    assert got is not None
    assert got.text.startswith("The quick brown fox")


def test_resolve_field_surfaces_pointer() -> None:
    r = _resolver()
    got = r.resolve(parse_anchor(field_anchor("document", "d1", 1, "/title")))
    assert got is not None
    assert got.metadata["json_pointer"] == "/title"


def test_missing_version_is_dangling() -> None:
    r = _resolver()
    # Same lineage, different (absent) version -> the whole point of version pinning.
    a = span_anchor("document", "d1", 99, "p1", 0, 3)
    assert r.resolve(parse_anchor(a)) is None
    assert find_dangling([a], r) == [a]


def test_missing_chunk_is_dangling() -> None:
    r = _resolver()
    a = chunk_anchor("document", "d1", 1, "nope")
    assert r.resolve(parse_anchor(a)) is None


def test_find_dangling_partitions() -> None:
    r = _resolver()
    good = entity_anchor("document", "d1", 1)
    bad = entity_anchor("document", "gone", 1)
    assert find_dangling([good, bad], r) == [bad]


def test_resolve_all_maps_each() -> None:
    r = _resolver()
    good = entity_anchor("document", "d1", 1)
    bad = entity_anchor("document", "gone", 1)
    out = resolve_all([good, bad], r)
    assert out[good] is not None
    assert out[bad] is None


def test_dangling_in_flattens_derived() -> None:
    r = _resolver()
    good = span_anchor("document", "d1", 1, "p1", 0, 3)
    bad = span_anchor("document", "gone", 1, "p1", 0, 3)
    items = [
        Derived(value="a", confidence=0.9, provenance=[good]),
        Derived(value="b", confidence=0.5, provenance=[good, bad]),
    ]
    assert dangling_in(items, r) == [bad]
