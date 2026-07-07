"""The :class:`Derived` envelope — the type discipline at the heart of attestable.

A :class:`Derived` value cannot be constructed without a confidence score in
``[0, 1]`` and at least one valid provenance anchor. That single rule makes it
*structurally impossible* to ship a model-produced value that an auditor could
reject as "the model just said so" — the provenance travels with the value, by
construction, everywhere it goes.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from .anchors import is_valid_anchor
from .errors import ProvenanceError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Derived(Generic[T]):
    """A value produced from one or more sources, carrying its confidence and provenance.

    Parameters
    ----------
    value:
        The produced value (an extracted field, a generated claim, a finding, ...).
    confidence:
        A calibrated score in ``[0.0, 1.0]``.
    provenance:
        One or more anchors (see :mod:`attestable.anchors`) pointing at the exact
        sources this value was derived from. Stored as an immutable tuple.

    Raises
    ------
    ProvenanceError
        If ``confidence`` is out of range, ``provenance`` is empty, or any anchor
        is not syntactically valid.

    Examples
    --------
    >>> from attestable import Derived, span_anchor
    >>> a = span_anchor("document", "abc", 3, "p12", 40, 88)
    >>> Derived(value="2026-01-15", confidence=0.94, provenance=[a]).value
    '2026-01-15'
    """

    value: T
    confidence: float
    provenance: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        # Normalise provenance to a validated tuple even if a list/iterable was passed.
        prov = tuple(self.provenance)
        object.__setattr__(self, "provenance", prov)

        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise ProvenanceError(f"confidence must be a number, got {self.confidence!r}")
        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ProvenanceError(f"confidence must be in [0, 1], got {self.confidence!r}")
        if not prov:
            raise ProvenanceError(
                "a Derived value must carry at least one provenance anchor "
                "(that is the whole point). If a value has no source, do not wrap it."
            )
        for anchor in prov:
            if not is_valid_anchor(anchor):
                raise ProvenanceError(f"invalid provenance anchor: {anchor!r}")

    # -- serialisation -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict. ``value`` is passed through unchanged, so
        it must itself be JSON-serialisable for the result to be dumpable."""
        return {
            "value": self.value,
            "confidence": float(self.confidence),
            "provenance": list(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Derived[Any]:
        """Reconstruct from :meth:`to_dict` output (re-validates the invariants)."""
        try:
            return cls(
                value=data["value"],
                confidence=data["confidence"],
                provenance=tuple(data["provenance"]),
            )
        except KeyError as exc:  # pragma: no cover - defensive
            raise ProvenanceError(f"missing key in Derived dict: {exc}") from exc

    def with_value(self, value: object) -> Derived[Any]:
        """Return a copy carrying a new ``value`` but the same confidence/provenance."""
        return Derived(value=value, confidence=self.confidence, provenance=self.provenance)


def derive(value: T, confidence: float, provenance: Iterable[str]) -> Derived[T]:
    """Functional constructor for :class:`Derived` — handy in comprehensions/pipelines."""
    return Derived(value=value, confidence=confidence, provenance=tuple(provenance))
