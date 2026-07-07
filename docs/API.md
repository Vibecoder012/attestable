# API reference

Everything below is importable directly from the top-level `attestable` package.

## Anchors — `attestable.anchors`

### `parse_anchor(anchor: str) -> ParsedAnchor`
Parse an anchor using the default (`attest`) scheme. Raises `AnchorSyntaxError` on any
malformed input (bad scheme, non-numeric version, empty fragment, `span` with
`start > end`, non-`str` input, ...).

### `is_valid_anchor(anchor: str) -> bool`
`True` if the string parses under the default scheme. Never raises.

### Constructors
All return a canonical anchor string and validate their inputs by construction:

- `entity_anchor(entity_type, lineage_id, version=1)` → `attest://type/lineage@v`
- `chunk_anchor(entity_type, lineage_id, version, chunk_id)` → `…#chunk:cid`
- `span_anchor(entity_type, lineage_id, version, chunk_id, start, end)` → `…#span:cid:s-e`
- `field_anchor(entity_type, lineage_id, version, json_pointer)` → `…#field:/ptr`

### `ParsedAnchor`
Frozen dataclass: `scheme`, `entity_type`, `lineage_id`, `version`, `fragment`
(`"none"|"chunk"|"span"|"field"`), and the fragment-specific `chunk_id`, `start`, `end`,
`json_pointer`. Methods/properties:

- `.to_anchor() -> str` — render back to canonical string (round-trips `parse_anchor`).
- `.source_key -> tuple[str, str, int]` — `(type, lineage_id, version)`.

### `Grammar(scheme="attest")`
Bind the parser/constructors to a custom scheme. Methods mirror the module functions:
`.parse`, `.is_valid`, `.entity`, `.chunk`, `.span`, `.field`.

## Derived — `attestable.derived`

### `Derived(value, confidence, provenance)`
Frozen generic dataclass. Raises `ProvenanceError` unless `confidence` is a real number in
`[0, 1]` and `provenance` is a non-empty iterable of valid anchor strings (normalized to a
tuple).

- `.to_dict() -> dict` / `Derived.from_dict(d) -> Derived` — round-trip (re-validates).
- `.with_value(value) -> Derived` — copy with a new value, same confidence/provenance.

### `derive(value, confidence, provenance) -> Derived`
Functional constructor equivalent to `Derived(...)`.

## Resolver — `attestable.resolver`

### `Resolver` (Protocol)
`resolve(anchor: ParsedAnchor) -> ResolvedSource | None`. Return `None` (do not raise) when
the anchor's source revision is absent.

### `ResolvedSource`
Frozen dataclass: `anchor: str`, `text: str`, `metadata: dict`.

### `InMemoryResolver`
`.put(entity_type, lineage_id, version, text, *, chunks=None)` registers a revision;
`.resolve(...)` slices spans, looks up chunks, or returns whole text for entity/field
anchors.

### Batch helpers
- `resolve_all(anchors, resolver) -> dict[str, ResolvedSource | None]`
- `find_dangling(anchors, resolver) -> list[str]` — anchors that no longer resolve.
- `dangling_in(derived_items, resolver) -> list[str]` — flatten `Derived.provenance` first.

## Attestation — `attestable.attestation`

### `attest(derived, *, key=None) -> Attestation`
Deterministic digest over `(value, confidence, provenance)`. With `key` (str or bytes):
`hmac-sha256` (forge-resistant). Without: `sha256` (tamper-evident). Raises
`AttestationError` if `value` is not JSON-serializable.

### `verify(derived, attestation, *, key=None) -> bool`
Constant-time comparison; total predicate (returns `False` rather than raising on
key/mode mismatch).

### `Attestation`
Frozen dataclass: `algorithm` (`"sha256"|"hmac-sha256"`), `digest` (hex). `.keyed`,
`.verify(...)`, `.to_dict()`, `Attestation.from_dict(d)`.

## Errors — `attestable.errors`

`AttestableError` (base) ← `AnchorSyntaxError` (also `ValueError`), `ProvenanceError` (also
`ValueError`), `AttestationError`.
