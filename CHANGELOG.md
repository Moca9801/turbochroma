# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-04-24

### Fixed

- **CI/CD**: Corrected `pip-audit` flag and fixed code formatting globally.
- **Docs**: Improved badge robustness in README.

## [0.1.3] - 2026-04-24

### Fixed

- **CI/CD**: Fixed `pip-audit` failure by skipping `pip` package audit.
- **CLI**: Fixed lint errors (unused variable, imports) in `cli.py`.

## [0.1.2] - 2026-04-24

### Fixed

- **Docs**: Fixed broken GitHub Action badges on PyPI by switching to Shields.io.

## [0.1.1] - 2026-04-24

### Added

- **CLI**: Added `turbochroma` command and `python -m turbochroma` support to display version info (`--version`).

## [0.1.0] - 2026-04-24

First public release on **PyPI** (beta). Library API: `QuantizedCollection`, `SQ8Codec`,
`SparseRotation`, `DefaultBlobKey`, `DefaultBlobspecKey`, `MAX_COMPRESSED_BLOB_BYTES`.

### Documentation

- Documented **operational risk** of future metadata wire-format changes (re-index /
  backfill) in `STABILITY.md` and a short **Limitations** pointer in the README.
- Documented **confidentiality and Chroma read access** (not encryption) in
  `SECURITY.md` and the README, for sensitive deployments.
- Added **RAG & LLM Integration Patterns** and **VRAM optimization** benefits to the README.

First public release on **PyPI** (beta). Library API: `QuantizedCollection`, `SQ8Codec`,
`SparseRotation`, `DefaultBlobKey`, `DefaultBlobspecKey`, `MAX_COMPRESSED_BLOB_BYTES`.

### Added

- **Chroma**: `QuantizedCollection` — metadata SQ8 blobs, `fit_existing`, ADC re-ranking
  with `refine_factor`, `strict` / `blobspec_key` for safe metadata handling.
- **Codecs**: `BaseCodec`, `SQ8Codec` (8-bit SQ + pluggable rotation), `blob_utils`
  (bounded base64 decode, 1 MiB max payload / dimension cap).
- **Rotations**: `BaseRotation`, `SparseRotation` (sign-flip + permutation).
- **Tooling**: Ruff, Mypy (strict), Bandit, pip-audit, Hypothesis property tests, pytest
  with ≥90% line coverage, pre-commit, Dependabot (grouped).
- **CI**: multi-OS/Python test matrix, lint, MkDocs strict build, CodeQL, OpenSSF Scorecard,
  dependency-review on PRs, SBOM (Syft / CycloneDX) on `main`.
- **Docs**: README, design note, MkDocs site, `STABILITY.md`, `SECURITY.md`, `QUALITY.md`,
  `TESTING.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `RELEASING.md`.

### Changed

- ADC re-ranking decodes blobs via `decode_stored_blob` (length cap, charset, exact size).

### Security

- Metadata treated as untrusted: size limits, optional `strict` mode, codec fingerprint in
  metadata, SAST and dependency scanning in CI.

---

History before this file was consolidated: see git log for `v0.1.0` and earlier commits on `main`.
