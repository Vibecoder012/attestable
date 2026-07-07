# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — initial release

### Added
- **Anchor grammar** (`Grammar`, `parse_anchor`, `is_valid_anchor`, and the
  `entity_anchor` / `chunk_anchor` / `span_anchor` / `field_anchor` constructors): a
  frozen, version-pinned citation URI. Parsing is total — it returns a fully-typed
  `ParsedAnchor` or raises `AnchorSyntaxError`.
- **`Derived[T]`** envelope: a frozen dataclass that refuses construction without a
  confidence in `[0, 1]` and at least one valid provenance anchor. `to_dict` /
  `from_dict` for round-tripping; `derive()` functional constructor.
- **Resolver** protocol + `InMemoryResolver`, plus `resolve_all`, `find_dangling`, and
  `dangling_in` for corpus-wide citation-integrity checks.
- **Attestations** (`attest`, `verify`, `Attestation`): deterministic, tamper-evident
  digests over a derived value, unkeyed (`sha256`) or keyed (`hmac-sha256`).
- Zero runtime dependencies; inline type information (`py.typed`); Python 3.10–3.14.
