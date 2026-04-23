# Testing and verification

## Quick path

```bash
python -m venv .venv
# activate .venv, then:
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy src
bandit -c pyproject.toml -q -r src/turbochroma
pip-audit
pytest -n auto --cov=turbochroma --cov-report=term-missing --cov-fail-under=90
```

## With documentation build

```bash
pip install -e ".[dev,docs]"
mkdocs build --strict
```

## What CI runs

- **test.yml**: the pytest command above (parallel workers where available) on a
  matrix of **Ubuntu and macOS** Python versions, **lint** job (Ruff, Mypy,
  Bandit, pip-audit), and a **docs** job (MkDocs strict).
- **codeql.yml**: CodeQL for Python.
- **scorecards.yml**: OpenSSF Scorecard (main branch, scheduled).
- **sbom.yml**: CycloneDX JSON SBOM (Syft) on `main`.
- **dependency-review.yml** (pull requests): GitHub native dependency review.

## Hypothesis

Blob decoding has property-based tests. To run that file only:

```bash
pytest tests/test_blob_utils.py -q
```

## Coverage policy

**90%** line coverage on `src/turbochroma` is required (see
[`docs/quality-gates.md`](docs/quality-gates.md)). If you add a new module, add
tests or a documented exclusion with maintainers’ approval.
