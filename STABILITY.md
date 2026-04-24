# API stability and versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## Current line: `0.1.x` (beta)

- **`0.1.0`** is the first **PyPI** release. The public surface area — in particular
  `QuantizedCollection`, `SQ8Codec`, `SparseRotation`, `DefaultBlobKey`,
  `DefaultBlobspecKey`, and the metadata/wire layout for SQ8 blobs — is intended to
  remain **compatible** within **`0.1.x`** (additive changes and bug fixes; breaking
  changes only with a clear changelog entry and migration note when unavoidable).
- **`0.2+` / `1.0`** — Broader API or format changes will be versioned and documented
  in [CHANGELOG.md](CHANGELOG.md). Prefer pinning `turbochroma~=0.1` until you
  explicitly adopt a newer minor.

The [PyPI classifier](https://pypi.org/classifiers/) **Development Status :: 4 - Beta**
reflects “usable, API still maturing toward 1.0”.

## Before `1.0.0`

- **Deprecations** — When a symbol is to be removed, a release will mark it
  deprecated in docstrings and the changelog, with a replacement when possible,
  before removal in a later minor/major per semver.

## Security contract

Security-sensitive behavior (blob size limits, `strict` ADC, `blobspec` checks)
is part of the *contract*; tightening validation is not treated as a breaking
change if it only rejects invalid or hostile inputs. Relaxing validation would
be called out in the changelog.
