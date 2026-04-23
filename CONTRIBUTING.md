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
- `bandit -c pyproject.toml -q -r src/turbochroma` (SAST; same as the lint job)
- `pytest -n auto --cov=turbochroma --cov-report=term-missing --cov-fail-under=90` (line coverage must stay ≥ 90%)
- `pip install -e ".[docs]"` then `mkdocs build --strict` (see also `docs.yml` in CI)
- `pip-audit` (optional locally; the same run is executed in GitHub Actions after install)
- Property-based checks on blob decoding: `pytest tests/test_blob_utils.py` (uses Hypothesis)

## Pull requests

- Keep changes focused; update `CHANGELOG.md` under **Unreleased** for user-visible changes.
- CI must pass on `main` (Python 3.10–3.12 on Ubuntu, plus macOS on 3.11; lint on 3.11; CodeQL and docs workflows as configured in `.github/workflows/`).
- For the **Dependency review** check on pull requests, enable **Dependency graph** in the GitHub repository **Settings → Code security and analysis** (or the workflow is skipped for some forks).
