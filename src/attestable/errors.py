"""Exception hierarchy for :mod:`attestable`.

All library errors derive from :class:`AttestableError`, so callers can catch the
whole family with one ``except`` while still discriminating on the specific type.
"""

from __future__ import annotations


class AttestableError(Exception):
    """Base class for every error raised by attestable."""


class AnchorSyntaxError(AttestableError, ValueError):
    """A string is not a valid anchor under the grammar.

    Subclasses :class:`ValueError` as well, so existing ``except ValueError``
    handlers keep working.
    """


class ProvenanceError(AttestableError, ValueError):
    """A :class:`~attestable.derived.Derived` value violated its invariants
    (bad confidence, missing or malformed provenance)."""


class AttestationError(AttestableError):
    """An attestation could not be produced or failed verification."""
