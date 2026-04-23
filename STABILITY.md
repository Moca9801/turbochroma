# API stability and versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
once the first stable line is published. Until `1.0.0`:

- **`0.x.y`** — Public symbols in `turbochroma` may add features and fix bugs;
  minor releases **may** include behavior changes to pre-release APIs if
  documented in [CHANGELOG.md](CHANGELOG.md). Prefer pinning `turbochroma~=0.x`
  in production and reading the changelog before upgrades.
- **Pre-alpha / alpha** (see `Development Status` in [pyproject.toml](pyproject.toml)) —
  treat the package as *research-grade*: the layout of metadata keys, codec
  wire format, and `QuantizedCollection` keyword arguments are subject to
  refinement before `0.1.0` stable.
- **Deprecations** — When a symbol is to be removed, a release will mark it
  deprecated in docstrings and the changelog, with a clear replacement when
  possible, before removal in a following minor/major per semver once `1.0.0` exists.

Security-sensitive behavior (blob size limits, `strict` ADC, `blobspec` checks)
is considered part of the *contract*; tightening validation is not treated as
a breaking change if it only rejects invalid or hostile inputs. Relaxing
validation would be called out in the changelog.
