# FAQ & troubleshooting

### Is this a RAG framework / vector store?
No. attestable has no retrieval, embeddings, or storage of its own. It is the provenance
layer you wrap *around* whatever retrieval/extraction stack you already run.

### Why do my old citations still work after re-chunking?
Because anchors pin the source **version**. A citation made against `@3` keeps resolving to
version 3's text even after you ingest and re-chunk `@4`. Point your resolver at the version
named in the anchor.

### `ProvenanceError: a Derived value must carry at least one provenance anchor`
That is by design — a `Derived` cannot exist without a source. If a value genuinely has no
source (e.g. a model "not found" result), don't wrap it in `Derived`; represent absence in
your own type instead.

### `ProvenanceError: confidence must be in [0, 1]`
Confidence is a probability-like score. If your model emits logits or a 0–100 scale,
normalize before constructing. Note `True`/`False` are rejected — a boolean confidence is
almost always a bug.

### `AttestationError: cannot attest a Derived whose value is not JSON-serialisable`
`attest` canonicalizes the value to JSON. Convert custom objects to dicts/strings first (or
store a stable string form as the value and the rich object elsewhere).

### Unkeyed vs keyed attestations — which do I want?
- **Unkeyed (`sha256`)**: detects accidental or unauthenticated changes. Anyone can
  recompute it.
- **Keyed (`hmac-sha256`)**: only a key-holder can produce/verify a valid digest, so a
  third party cannot forge one. Use this whenever the attestation must be trustworthy
  against a motivated actor. You manage the key; attestable never stores it.

### Can I change the `attest://` scheme?
Yes: `Grammar("your-scheme")`. Choose it once and freeze it — changing the scheme later
invalidates every anchor already stored, exactly like changing any other part of the
grammar.

### Does it work offline / in air-gapped environments?
Yes. Zero dependencies, no network/filesystem/subprocess use.

### Which Python versions?
3.10 through 3.14, tested in CI.
