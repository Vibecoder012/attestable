"""attestable — make it structurally impossible to ship an unattributed AI value.

A tiny, zero-dependency library for **auditable, version-pinned provenance** on
model-produced values:

* :class:`Derived` — a value that *cannot exist* without a confidence score and at
  least one valid source anchor.
* an anchor grammar (:func:`parse_anchor`, :func:`span_anchor`, ...) whose citations
  stay valid across re-chunking because they pin the source **version**.
* :class:`Resolver` + :func:`find_dangling` — resolve anchors back to source text
  and detect citations that no longer point anywhere.
* :func:`attest` / :func:`verify` — tamper-evident (optionally HMAC-signed) digests
  proving a value/confidence/citation has not been altered.

Quick start
-----------
>>> from attestable import Derived, span_anchor, attest, verify
>>> anchor = span_anchor("document", "invoice-abc", version=3, chunk_id="p2", start=40, end=52)
>>> field = Derived(value="2026-01-15", confidence=0.94, provenance=[anchor])
>>> token = attest(field, key="my-secret")
>>> verify(field, token, key="my-secret")
True
"""

from __future__ import annotations

from .anchors import (
    DEFAULT_SCHEME,
    Grammar,
    ParsedAnchor,
    chunk_anchor,
    default_grammar,
    entity_anchor,
    field_anchor,
    is_valid_anchor,
    parse_anchor,
    span_anchor,
)
from .attestation import Attestation, attest, verify
from .derived import Derived, derive
from .errors import (
    AnchorSyntaxError,
    AttestableError,
    AttestationError,
    ProvenanceError,
)
from .resolver import (
    InMemoryResolver,
    ResolvedSource,
    Resolver,
    dangling_in,
    find_dangling,
    resolve_all,
)

__version__ = "0.1.1"

__all__ = [  # noqa: RUF022 - grouped by module for readability, not sorted
    "__version__",
    # anchors
    "DEFAULT_SCHEME",
    "Grammar",
    "ParsedAnchor",
    "default_grammar",
    "parse_anchor",
    "is_valid_anchor",
    "entity_anchor",
    "chunk_anchor",
    "span_anchor",
    "field_anchor",
    # derived
    "Derived",
    "derive",
    # resolver
    "Resolver",
    "ResolvedSource",
    "InMemoryResolver",
    "resolve_all",
    "find_dangling",
    "dangling_in",
    # attestation
    "Attestation",
    "attest",
    "verify",
    # errors
    "AttestableError",
    "AnchorSyntaxError",
    "ProvenanceError",
    "AttestationError",
]
