# Contributing to attestable

Thanks for your interest! attestable aims to stay tiny, dependency-free, and boring in
the best way — a primitive you can trust. Contributions that keep it that way are very
welcome.

## Ground rules

- **Zero runtime dependencies.** The core library must import only the standard library.
  Optional integrations may add extras, but the core never does.
- **The anchor grammar is frozen.** Changing how an existing anchor parses would break
  every citation already stored by every user. New *fragment kinds* can be proposed, but
  existing forms must parse identically forever. Open an issue before touching `anchors.py`.
- **Everything is typed and tested.** New code ships with type hints and tests; `mypy
  --strict` and `ruff` must pass.

## Development setup

```bash
git clone https://github.com/<your-username>/attestable
cd attestable
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## The checks (all must pass)

```bash
ruff check .          # lint
ruff format --check . # formatting
mypy src              # strict type-check
pytest                # tests
```

Or run them the way CI does with [`uv`](https://docs.astral.sh/uv/):

```bash
uvx ruff check . && uvx mypy src && python -m pytest
```

## Pull requests

1. Fork and branch from `main`.
2. Add tests for any behaviour change; keep coverage of the invariants intact.
3. Update `CHANGELOG.md` under `[Unreleased]`.
4. Keep PRs focused — one concern each.

## Reporting bugs / requesting features

Use the issue templates. A minimal reproduction (a few lines using only `attestable`)
turns a bug report into a fix much faster.

By contributing you agree that your contributions are licensed under the project's
[Apache-2.0](LICENSE) license.
