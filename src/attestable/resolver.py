"""Resolving anchors back to live source text, and detecting dangling citations.

A :class:`Resolver` maps a :class:`~attestable.anchors.ParsedAnchor` to the source
material it points at. The bundled :class:`InMemoryResolver` is enough for tests,
demos, and small corpora; production callers implement :class:`Resolver` over their
own store (SQLite, object storage, a document service) and get
:func:`find_dangling` / :func:`resolve_all` for free.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from .anchors import ParsedAnchor, parse_anchor
from .derived import Derived


@dataclass(frozen=True, slots=True)
class ResolvedSource:
    """The material an anchor resolves to.

    ``text`` is the resolved slice (the span substring, the chunk body, or the whole
    source, depending on the anchor's fragment). ``metadata`` carries anything the
    resolver wants to surface (page number, bounding box, title, ...).
    """

    anchor: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Resolver(Protocol):
    """Resolve a parsed anchor to its source, or ``None`` if it no longer exists.

    Implementations must be pure lookups: given the same store state and anchor they
    return the same result, and they return ``None`` (rather than raising) for an
    anchor whose source revision is absent — that ``None`` is what
    :func:`find_dangling` reports.
    """

    def resolve(self, anchor: ParsedAnchor) -> ResolvedSource | None: ...


class InMemoryResolver:
    """A dictionary-backed :class:`Resolver`, mostly for tests and small corpora.

    Register the full text of a source revision with :meth:`put`. Span anchors are
    resolved by slicing that text; chunk anchors by an optional per-source chunk map;
    field anchors return the whole source text with the pointer surfaced in metadata.
    """

    def __init__(self) -> None:
        # (type, lineage_id, version) -> full source text
        self._sources: dict[tuple[str, str, int], str] = {}
        # (type, lineage_id, version) -> {chunk_id: chunk_text}
        self._chunks: dict[tuple[str, str, int], dict[str, str]] = {}

    def put(
        self,
        entity_type: str,
        lineage_id: str,
        version: int,
        text: str,
        *,
        chunks: dict[str, str] | None = None,
    ) -> None:
        """Register the text (and optional chunk map) for one source revision."""
        key = (entity_type, lineage_id, version)
        self._sources[key] = text
        if chunks is not None:
            self._chunks[key] = dict(chunks)

    def resolve(self, anchor: ParsedAnchor) -> ResolvedSource | None:
        key = anchor.source_key
        text = self._sources.get(key)
        if text is None:
            return None  # source revision absent -> dangling
        rendered = anchor.to_anchor()
        if anchor.fragment == "span":
            assert anchor.start is not None
            assert anchor.end is not None
            return ResolvedSource(
                anchor=rendered,
                text=text[anchor.start : anchor.end],
                metadata={"chunk_id": anchor.chunk_id, "start": anchor.start, "end": anchor.end},
            )
        if anchor.fragment == "chunk":
            chunk_text = self._chunks.get(key, {}).get(anchor.chunk_id or "")
            if chunk_text is None:
                return None  # chunk id not found in this revision -> dangling
            return ResolvedSource(
                anchor=rendered, text=chunk_text, metadata={"chunk_id": anchor.chunk_id}
            )
        if anchor.fragment == "field":
            return ResolvedSource(
                anchor=rendered, text=text, metadata={"json_pointer": anchor.json_pointer}
            )
        return ResolvedSource(anchor=rendered, text=text, metadata={})


def resolve_all(anchors: Iterable[str], resolver: Resolver) -> dict[str, ResolvedSource | None]:
    """Resolve each anchor string, returning ``{anchor: ResolvedSource | None}``."""
    out: dict[str, ResolvedSource | None] = {}
    for anchor in anchors:
        out[anchor] = resolver.resolve(parse_anchor(anchor))
    return out


def find_dangling(anchors: Iterable[str], resolver: Resolver) -> list[str]:
    """Return the subset of ``anchors`` that no longer resolve against ``resolver``.

    This is the batch integrity check to run after re-ingesting or garbage-collecting
    a corpus: a non-empty result means stored citations point at material that is
    gone, which is a data-quality alarm in an audit context.
    """
    return [a for a in anchors if resolver.resolve(parse_anchor(a)) is None]


def dangling_in(derived: Iterable[Derived[Any]], resolver: Resolver) -> list[str]:
    """Convenience: flatten the provenance of many :class:`Derived` values and return
    the anchors among them that no longer resolve."""
    seen: list[str] = []
    for item in derived:
        seen.extend(item.provenance)
    return find_dangling(seen, resolver)
