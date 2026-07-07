"""The anchor grammar — a frozen, version-pinned citation URI.

An *anchor* is a stable, machine-parseable pointer to the exact source a value
came from. Because it pins the source **version**, re-chunking or re-embedding a
newer version of a document never invalidates an anchor stored against an older
one — the single correctness property hand-rolled citation schemes get wrong.

Grammar
-------
::

    <scheme>://<type>/<lineage_id>@<version>
    <scheme>://<type>/<lineage_id>@<version>#chunk:<chunk_id>
    <scheme>://<type>/<lineage_id>@<version>#span:<chunk_id>:<start>-<end>
    <scheme>://<type>/<lineage_id>@<version>#field:<json_pointer>

* ``scheme``      — URI scheme, ``attest`` by default. Frozen per deployment.
* ``type``        — lowercase entity type, e.g. ``document`` or ``document.sop``.
* ``lineage_id``  — an identity that is **stable across versions** of the source.
* ``version``     — the specific integer version the citation was made against.
* ``chunk_id``    — an opaque, stable id for a chunk/paragraph within the source.
* ``start``/``end`` — a character range within a chunk (``start <= end``).
* ``json_pointer`` — an RFC-6901 pointer into a structured record.

The grammar is deliberately tiny and total: :func:`Grammar.parse` either returns
a fully-typed :class:`ParsedAnchor` or raises :class:`AnchorSyntaxError` — it
never returns a partially-populated result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from typing import Literal

from .errors import AnchorSyntaxError

Fragment = Literal["none", "chunk", "span", "field"]

_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*$")
# URL-safe unreserved characters (RFC 3986 §2.3) — safe to embed without escaping.
_ID = r"[A-Za-z0-9._~-]+"
_TYPE = r"[a-z0-9_.]+"

DEFAULT_SCHEME = "attest"


@dataclass(frozen=True, slots=True)
class ParsedAnchor:
    """A parsed anchor. Immutable and hashable, so it is safe to use as a dict key.

    Only the fields relevant to :attr:`fragment` are populated; the rest are ``None``.
    """

    scheme: str
    entity_type: str
    lineage_id: str
    version: int
    fragment: Fragment = "none"
    chunk_id: str | None = None
    start: int | None = None
    end: int | None = None
    json_pointer: str | None = None

    def to_anchor(self) -> str:
        """Render back to the canonical string form (round-trips :func:`Grammar.parse`)."""
        base = f"{self.scheme}://{self.entity_type}/{self.lineage_id}@{self.version}"
        if self.fragment == "chunk":
            return f"{base}#chunk:{self.chunk_id}"
        if self.fragment == "span":
            return f"{base}#span:{self.chunk_id}:{self.start}-{self.end}"
        if self.fragment == "field":
            return f"{base}#field:{self.json_pointer}"
        return base

    @property
    def source_key(self) -> tuple[str, str, int]:
        """The ``(type, lineage_id, version)`` that identifies the exact source revision."""
        return (self.entity_type, self.lineage_id, self.version)


@cache
def _compiled(scheme: str) -> re.Pattern[str]:
    return re.compile(
        rf"^{re.escape(scheme)}://(?P<type>{_TYPE})/(?P<lineage_id>{_ID})@(?P<version>\d+)"
        r"(?:#(?:"
        rf"chunk:(?P<chunk_cid>{_ID})"
        rf"|span:(?P<span_cid>{_ID}):(?P<start>\d+)-(?P<end>\d+)"
        r"|field:(?P<pointer>.+)"
        r"))?$"
    )


class Grammar:
    """A parser/constructor bound to one URI ``scheme``.

    Instantiate with a custom scheme if ``attest`` collides with something in your
    domain; otherwise use the module-level convenience functions, which delegate to
    a shared default-scheme instance.
    """

    __slots__ = ("_re", "scheme")

    def __init__(self, scheme: str = DEFAULT_SCHEME) -> None:
        if not _SCHEME_RE.match(scheme):
            raise ValueError(f"invalid scheme {scheme!r}: must match {_SCHEME_RE.pattern}")
        self.scheme = scheme
        self._re = _compiled(scheme)

    # -- parsing -------------------------------------------------------------

    def parse(self, anchor: str) -> ParsedAnchor:
        """Parse ``anchor`` into a :class:`ParsedAnchor` or raise :class:`AnchorSyntaxError`."""
        if not isinstance(anchor, str):  # defensive: parse() is a trust boundary
            raise AnchorSyntaxError(f"anchor must be a str, got {type(anchor).__name__}")
        m = self._re.match(anchor)
        if m is None:
            raise AnchorSyntaxError(f"invalid anchor for scheme {self.scheme!r}: {anchor!r}")
        g = m.groupdict()
        entity_type = g["type"]
        lineage_id = g["lineage_id"]
        version = int(g["version"])
        if g["chunk_cid"] is not None:
            return ParsedAnchor(
                scheme=self.scheme,
                entity_type=entity_type,
                lineage_id=lineage_id,
                version=version,
                fragment="chunk",
                chunk_id=g["chunk_cid"],
            )
        if g["span_cid"] is not None:
            start, end = int(g["start"]), int(g["end"])
            if start > end:
                raise AnchorSyntaxError(f"span start {start} is after end {end} in {anchor!r}")
            return ParsedAnchor(
                scheme=self.scheme,
                entity_type=entity_type,
                lineage_id=lineage_id,
                version=version,
                fragment="span",
                chunk_id=g["span_cid"],
                start=start,
                end=end,
            )
        if g["pointer"] is not None:
            return ParsedAnchor(
                scheme=self.scheme,
                entity_type=entity_type,
                lineage_id=lineage_id,
                version=version,
                fragment="field",
                json_pointer=g["pointer"],
            )
        return ParsedAnchor(
            scheme=self.scheme,
            entity_type=entity_type,
            lineage_id=lineage_id,
            version=version,
        )

    def is_valid(self, anchor: str) -> bool:
        """Return ``True`` if ``anchor`` parses, ``False`` otherwise. Never raises."""
        try:
            self.parse(anchor)
            return True
        except AnchorSyntaxError:
            return False

    # -- construction --------------------------------------------------------

    def entity(self, entity_type: str, lineage_id: str, version: int = 1) -> str:
        """Anchor to a whole source revision."""
        return self.parse(f"{self.scheme}://{entity_type}/{lineage_id}@{version}").to_anchor()

    def chunk(self, entity_type: str, lineage_id: str, version: int, chunk_id: str) -> str:
        """Anchor to a chunk within a source revision."""
        raw = f"{self.scheme}://{entity_type}/{lineage_id}@{version}#chunk:{chunk_id}"
        return self.parse(raw).to_anchor()

    def span(
        self,
        entity_type: str,
        lineage_id: str,
        version: int,
        chunk_id: str,
        start: int,
        end: int,
    ) -> str:
        """Anchor to a character range within a chunk (``start <= end``)."""
        raw = f"{self.scheme}://{entity_type}/{lineage_id}@{version}#span:{chunk_id}:{start}-{end}"
        return self.parse(raw).to_anchor()

    def field(self, entity_type: str, lineage_id: str, version: int, json_pointer: str) -> str:
        """Anchor to a field, addressed by an RFC-6901 JSON pointer."""
        raw = f"{self.scheme}://{entity_type}/{lineage_id}@{version}#field:{json_pointer}"
        return self.parse(raw).to_anchor()


#: The shared default-scheme grammar used by the module-level convenience functions.
default_grammar = Grammar(DEFAULT_SCHEME)


def parse_anchor(anchor: str) -> ParsedAnchor:
    """Parse an anchor using the default (``attest``) scheme."""
    return default_grammar.parse(anchor)


def is_valid_anchor(anchor: str) -> bool:
    """Return whether ``anchor`` is valid under the default scheme. Never raises."""
    return default_grammar.is_valid(anchor)


def entity_anchor(entity_type: str, lineage_id: str, version: int = 1) -> str:
    """Construct a whole-source anchor (default scheme)."""
    return default_grammar.entity(entity_type, lineage_id, version)


def chunk_anchor(entity_type: str, lineage_id: str, version: int, chunk_id: str) -> str:
    """Construct a chunk anchor (default scheme)."""
    return default_grammar.chunk(entity_type, lineage_id, version, chunk_id)


def span_anchor(
    entity_type: str, lineage_id: str, version: int, chunk_id: str, start: int, end: int
) -> str:
    """Construct a span anchor (default scheme)."""
    return default_grammar.span(entity_type, lineage_id, version, chunk_id, start, end)


def field_anchor(entity_type: str, lineage_id: str, version: int, json_pointer: str) -> str:
    """Construct a field anchor (default scheme)."""
    return default_grammar.field(entity_type, lineage_id, version, json_pointer)
