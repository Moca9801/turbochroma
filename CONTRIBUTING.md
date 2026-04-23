# Contributing

## Setup

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -e ".[dev]"
```

Optional: install [pre-commit](https://pre-commit.com/) hooks so ruff, ruff format, and mypy run before each commit (requires the dev environment on `PATH` — mypy is invoked as a system command):

```bash
pre-commit install
```

Run all hooks on the tree:

```bash
pre-commit run --all-files
```

## Checks

- `ruff check .` and `ruff format --check .`
- `mypy src`
- `pytest` (use `pytest --cov` as in CI)
- `pip-audit` (optional locally; the same run is executed in GitHub Actions after install)

## Pull requests

- Keep changes focused; update `CHANGELOG.md` under **Unreleased** for user-visible changes.
- CI must pass on `main` (Python 3.10–3.12 on Ubuntu; lint on 3.11).
