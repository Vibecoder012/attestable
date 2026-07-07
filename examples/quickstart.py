"""A 60-second tour of attestable. Run with: python examples/quickstart.py

Requires only the standard library plus attestable itself (zero third-party deps).
"""

from __future__ import annotations

from attestable import (
    Derived,
    InMemoryResolver,
    attest,
    find_dangling,
    parse_anchor,
    span_anchor,
    verify,
)


def main() -> None:
    # 1. Point at the exact source characters a value came from — pinned to version 3.
    anchor = span_anchor("document", "invoice-abc", version=3, chunk_id="p2", start=40, end=52)
    print("anchor:", anchor)

    # 2. Wrap a model-produced value. This *cannot* be built without confidence + provenance.
    total = Derived(value="2026-01-15", confidence=0.94, provenance=[anchor])
    print("derived:", total.to_dict())

    # 3. Attest it. A keyed (HMAC) attestation is forge-resistant.
    token = attest(total, key="rotate-me")
    print("attestation:", token.to_dict())
    print("verifies:", verify(total, token, key="rotate-me"))

    # 4. Tampering is detected: change the value, the attestation no longer verifies.
    tampered = total.with_value("2026-02-02")
    print("tampered verifies:", verify(tampered, token, key="rotate-me"))

    # 5. Resolve the anchor back to its source text, and flag citations that dangle.
    resolver = InMemoryResolver()
    resolver.put(
        "document", "invoice-abc", 3, "Invoice #A-19 issued on 2026-01-15 for 1,299.00 GBP"
    )
    resolved = resolver.resolve(parse_anchor(anchor))
    print("cited text:", None if resolved is None else repr(resolved.text))

    stale = span_anchor("document", "invoice-abc", version=99, chunk_id="p2", start=0, end=3)
    print("dangling:", find_dangling([anchor, stale], resolver))


if __name__ == "__main__":
    main()
