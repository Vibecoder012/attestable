# Architecture & design decisions

attestable is four small modules that compose. Each is independently useful; together
they form a complete "provenance discipline" for AI output.

```
attestable/
├── anchors.py       the frozen citation grammar + parser + constructors
├── derived.py       the Derived[T] envelope (value + confidence + provenance)
├── resolver.py      Resolver protocol, InMemoryResolver, dangling detection
├── attestation.py   deterministic tamper-evident digests (keyed + unkeyed)
└── errors.py        one exception hierarchy
```

## Design decisions

### 1. The grammar pins the source *version*
The single hardest-won idea. A citation is `type/lineage_id@version#fragment`, where
`lineage_id` is stable across versions but `version` is fixed at citation time. When you
re-chunk or re-embed a *new* version of a document, every citation stored against an
*older* version still resolves correctly — you have not silently invalidated your audit
trail. Schemes that store bare offsets or chunk-ids without a version break on the next
re-index; this one does not.

### 2. Parsing is total; construction goes through the parser
`Grammar.parse` returns a fully-populated `ParsedAnchor` or raises — never a half-filled
object. The constructor helpers build a string and immediately parse it, so a constructed
anchor is guaranteed to be a parseable anchor (constructor and parser can never drift).

### 3. Invariants live in the type, not in a linter
`Derived.__post_init__` enforces `0 <= confidence <= 1` and non-empty, valid provenance.
There is no way to obtain a `Derived` that violates these — so "every model output is
attributed" becomes a property of the type system rather than a convention reviewers must
police. `bool` is explicitly rejected as a confidence because `True`/`False` are almost
always bugs there.

### 4. Frozen, hashable value objects
`ParsedAnchor` and `Derived` are frozen slotted dataclasses: cheap, immutable, hashable,
and safe to share. Serialization is explicit (`to_dict`/`from_dict`) and re-validates on
the way back in.

### 5. Resolution is a protocol, not a base class
The library ships `InMemoryResolver` for tests and small corpora, but production callers
implement the one-method `Resolver` protocol over their own store. `find_dangling` and
`dangling_in` then work against any resolver — the batch integrity check you run after
every re-ingest.

### 6. Attestation canonicalization is stable across processes
`attest` serializes `(value, confidence, provenance)` with sorted keys, fixed separators,
and preserved Unicode, then hashes. The same triple always produces the same digest, in
any process or Python version, so an attestation stored today verifies years later.
Keyed (HMAC) mode upgrades tamper-*evidence* to forge-*resistance*.

### 7. Zero dependencies, on purpose
The core imports only `re`, `dataclasses`, `hashlib`, `hmac`, `json`, `functools`, and
`typing`. No network, filesystem, or subprocess use. This maximizes trust (nothing to
audit but the code) and portability (runs anywhere Python does, including air-gapped and
locked-down environments).

## Non-goals

- **A vector store or RAG framework.** attestable *composes with* your retrieval stack;
  it does not retrieve.
- **A governance dashboard.** It is a primitive. Building an attestation registry or UI on
  top is straightforward and intentionally left to the caller.
- **Cryptographic non-repudiation with PKI.** Keyed HMAC gives symmetric forge-resistance;
  full signature/PKI schemes are out of scope for the core.
