"""Tamper-evident attestations over :class:`~attestable.derived.Derived` values.

An :class:`Attestation` is a deterministic digest of a derived value's
``(value, confidence, provenance)`` triple. Recomputing the digest later and
comparing proves the stored value/confidence/citation has not been altered — the
"provably unaltered" property regulated reviewers ask for.

Two modes:

* **Unkeyed** (``sha256``) — anyone can recompute the digest. Detects accidental
  or unauthenticated tampering.
* **Keyed** (``hmac-sha256`` with a secret) — only a holder of the key can produce
  or verify a valid digest, so a third party cannot forge an attestation.

The canonical serialisation is stable across processes and Python versions: keys
are sorted, separators are fixed, and non-ASCII is preserved, so the same triple
always hashes to the same digest.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from .derived import Derived
from .errors import AttestationError

_UNKEYED = "sha256"
_KEYED = "hmac-sha256"


def _canonical_bytes(derived: Derived[Any]) -> bytes:
    """Deterministic byte serialisation of a derived value's attestable content."""
    payload = {
        "value": derived.value,
        "confidence": round(float(derived.confidence), 12),
        "provenance": list(derived.provenance),
    }
    try:
        return json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    except TypeError as exc:
        raise AttestationError(
            f"cannot attest a Derived whose value is not JSON-serialisable: {exc}"
        ) from exc


@dataclass(frozen=True, slots=True)
class Attestation:
    """A tamper-evident digest over a :class:`Derived` value.

    ``algorithm`` is ``"sha256"`` (unkeyed) or ``"hmac-sha256"`` (keyed). ``digest``
    is the lowercase hex digest. :meth:`verify` recomputes and compares in constant
    time.
    """

    algorithm: str
    digest: str

    @property
    def keyed(self) -> bool:
        """Whether this attestation was produced with a secret key."""
        return self.algorithm == _KEYED

    def verify(self, derived: Derived[Any], *, key: bytes | str | None = None) -> bool:
        """Return ``True`` iff ``derived`` still matches this attestation.

        A keyed attestation requires the same ``key``; an unkeyed one must be
        verified without a key. Mismatched key/attestation modes return ``False``
        rather than raising, so verification is a total predicate.
        """
        try:
            expected = attest(derived, key=key)
        except AttestationError:
            return False
        if expected.algorithm != self.algorithm:
            return False
        return hmac.compare_digest(expected.digest, self.digest)

    def to_dict(self) -> dict[str, str]:
        """JSON-serialisable form."""
        return {"algorithm": self.algorithm, "digest": self.digest}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Attestation:
        """Reconstruct from :meth:`to_dict` output."""
        return cls(algorithm=data["algorithm"], digest=data["digest"])


def attest(derived: Derived[Any], *, key: bytes | str | None = None) -> Attestation:
    """Produce an :class:`Attestation` over ``derived``.

    Pass ``key`` for a forge-resistant keyed (HMAC) attestation; omit it for an
    unkeyed digest anyone can recompute.
    """
    message = _canonical_bytes(derived)
    if key is None:
        return Attestation(algorithm=_UNKEYED, digest=hashlib.sha256(message).hexdigest())
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    digest = hmac.new(key_bytes, message, hashlib.sha256).hexdigest()
    return Attestation(algorithm=_KEYED, digest=digest)


def verify(
    derived: Derived[Any], attestation: Attestation, *, key: bytes | str | None = None
) -> bool:
    """Functional alias for :meth:`Attestation.verify`."""
    return attestation.verify(derived, key=key)
