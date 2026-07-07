# attestable

**Make it structurally impossible to ship an AI-produced value without a confidence score and a version-pinned, resolvable citation.**

`attestable` is a tiny, **zero-dependency** Python library for auditable provenance on model output. It gives you four things that compose:

- **`Derived[T]`** — a value that *cannot be constructed* without a confidence in `[0, 1]` and at least one valid source anchor. Provenance travels with the value, by construction, everywhere it goes.
- **An anchor grammar** — a frozen citation URI that pins the source **version**, so re-chunking or re-embedding a newer revision never invalidates a citation stored against an older one. This is the one correctness property hand-rolled citation schemes get wrong.
- **Resolvers + dangling detection** — resolve anchors back to source text, and batch-check a corpus for citations that no longer point anywhere.
- **Attestations** — deterministic, tamper-evident (optionally HMAC-signed) digests that prove a value/confidence/citation triple has not been altered.

[![CI](https://github.com/Vibecoder012/attestable/actions/workflows/ci.yml/badge.svg)](https://github.com/Vibecoder012/attestable/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/attestable.py.svg)](https://pypi.org/project/attestable.py/)
[![Python](https://img.shields.io/pypi/pyversions/attestable.py.svg)](https://pypi.org/project/attestable.py/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

---

## Why

Auditors, regulators, and reviewers reject *"the model said so."* When an LLM extracts a field, answers a question, or flags a finding, three things must be true for that output to survive scrutiny:

1. It carries a **confidence** you can threshold on.
2. It carries a **pointer to the exact source** it came from.
3. That pointer **still works** after you re-index the corpus.

Most stacks bolt this on as an afterthought and get (3) wrong: citations are stored as raw offsets or chunk ids that break the moment a document is re-chunked. `attestable` makes (1) and (2) a **type-level requirement** and makes (3) correct by pinning the source version in the citation itself.

It is deliberately small, dependency-free, offline-capable, and framework-agnostic — it *composes with* your extraction/RAG stack rather than replacing it.

## Install

```bash
pip install attestable.py
```

> The PyPI distribution is named `attestable.py` (the plain `attestable` name is an
> unrelated, unmaintained package). The import name is unaffected: `import attestable`.

Requires Python 3.10+. No third-party runtime dependencies.

## Quick start

```python
from attestable import Derived, span_anchor, attest, verify, InMemoryResolver, parse_anchor

# 1. Cite the exact characters — pinned to version 3 of the source.
anchor = span_anchor("document", "invoice-abc", version=3, chunk_id="p2", start=40, end=52)

# 2. Wrap the value. This raises unless confidence is in [0,1] and provenance is a valid anchor.
total = Derived(value="2026-01-15", confidence=0.94, provenance=[anchor])

# 3. Attest it (keyed = forge-resistant).
token = attest(total, key="rotate-me")
assert verify(total, token, key="rotate-me")

# 4. Tampering is detected.
assert not verify(total.with_value("2026-02-02"), token, key="rotate-me")

# 5. Resolve back to source, and detect citations that no longer point anywhere.
resolver = InMemoryResolver()
resolver.put("document", "invoice-abc", 3, "… issued on 2026-01-15 …")
assert resolver.resolve(parse_anchor(anchor)) is not None
```

Run the full tour: `python examples/quickstart.py`.

## The anchor grammar

```
attest://<type>/<lineage_id>@<version>
attest://<type>/<lineage_id>@<version>#chunk:<chunk_id>
attest://<type>/<lineage_id>@<version>#span:<chunk_id>:<start>-<end>
attest://<type>/<lineage_id>@<version>#field:<json_pointer>
```

| Part | Meaning |
|---|---|
| `type` | lowercase entity type, e.g. `document` or `document.sop` |
| `lineage_id` | identity that is **stable across versions** of the source |
| `version` | the specific integer version cited |
| `chunk_id` | opaque, stable id of a chunk/paragraph |
| `start`/`end` | character range within a chunk (`start <= end`) |
| `json_pointer` | RFC-6901 pointer into a structured record |

`parse_anchor()` is total: it returns a fully-typed `ParsedAnchor` or raises `AnchorSyntaxError` — never a half-populated result. The scheme (`attest`) is fixed per deployment; use `Grammar("your-scheme")` to change it.

## Integrating with your store

Implement the `Resolver` protocol over wherever your source text actually lives:

```python
from attestable import Resolver, ResolvedSource, ParsedAnchor

class SqliteResolver:
    def resolve(self, anchor: ParsedAnchor) -> ResolvedSource | None:
        row = db.get(anchor.entity_type, anchor.lineage_id, anchor.version)
        if row is None:
            return None                       # -> reported by find_dangling()
        text = row.text[anchor.start:anchor.end] if anchor.fragment == "span" else row.text
        return ResolvedSource(anchor=anchor.to_anchor(), text=text)
```

Then `find_dangling(anchors, resolver)` and `dangling_in(derived_values, resolver)` give you a corpus-wide integrity check to run after every re-ingest.

## Documentation

- [Architecture & design decisions](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [FAQ & troubleshooting](docs/FAQ.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md) · [Code of conduct](CODE_OF_CONDUCT.md)

## License

[Apache-2.0](LICENSE).
