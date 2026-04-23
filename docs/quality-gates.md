# Quality gates (target: audit 9+ / approaching 10)

This document lists **enforced** checks. “10/10” in external audits is a direction
of travel; no repository can credibly claim perfection.

## Mandatory on every change (CI + local)

| Gate | Tool | Purpose |
|------|------|--------|
| Style / import / bugbear | Ruff | Fast static lint |
| Format | Ruff format | One style |
| Typing | Mypy (`strict` on `src/`) | Contract errors before runtime |
| SAST (Python) | Bandit | Common security anti-patterns |
| Dependency CVEs (PyPI) | pip-audit | Known vulnerable packages in the environment |
| Tests + line coverage (≥ **90%**) | Pytest + Coverage | Regressions and dead code control |
| Property tests (blob decode) | Hypothesis | Randomized robustness of untrusted string handling |

## Security analysis (CI)

| Gate | Tool | Purpose |
|------|------|--------|
| Semantic code analysis | CodeQL (Python) | Deep vulnerability patterns |
| Supply-chain health | OpenSSF Scorecard (scheduled) | Policy and workflow signals |
| SBOM | Syft (Anchore) | CycloneDX JSON artifact on `main` |
| PR dependencies | GitHub dependency-review | Block moderate+ known issues on new deps |

## Documentation

| Gate | Tool | Purpose |
|------|------|--------|
| API + narrative | MkDocs + Material + mkdocstrings | Discoverable, versioned public API |
| Stability / semver | `STABILITY.md` | Pre-1.0 expectations |
| Reporting security | `SECURITY.md` | Coordinated disclosure |

## Human process

- **CHANGELOG** for user-visible changes.
- **Pre-commit** (optional locally) aligned with the lint job.
- **Code of conduct** for community safety expectations.

## Not yet automated (optional stretch)

- Formal mutation testing in CI.
- Nightly full fuzzing of binary codecs.
- Windows wheels for native extensions (this project is pure Python; Chroma is the heavy native dep).

To run the doc build: `pip install -e ".[docs]"` then `mkdocs build --strict` from the repository root.
