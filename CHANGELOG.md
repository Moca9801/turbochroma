# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial repository scaffold: project layout, tooling config, CI workflows,
  placeholders for codecs / rotations / storage / kernels modules.
- `BaseCodec` abstract base class in `turbochroma.codecs.base`.
- `SQ8Codec` (8-bit scalar quantization with sparse rotation), promoted from
  Minervia's `TurboQuantizer`; inherits from `BaseCodec`. Exported at the
  package root as `turbochroma.SQ8Codec`.
- Test suite `tests/test_sq8_codec.py`: roundtrip MAE, blob shape,
  asymmetric-dot sanity, cross-instance determinism.
- `BaseRotation` abstract base class in `turbochroma.rotations.base`.
- `SparseRotation` (sign-flip + permutation, O(d)) in
  `turbochroma.rotations.sparse`, extracted out of `SQ8Codec`. Exported
  at the package root as `turbochroma.SparseRotation`.
- Test suite `tests/test_sparse_rotation.py`: determinism,
  invertibility (1D and 2D), batch-vs-per-vector equivalence, ndim
  validation.

### Changed

- `TurboQuantizer` → `SQ8Codec` (class renamed). The old name is not
  aliased because the package has no external users yet.
- `SQ8Codec` now takes an optional `rotation: BaseRotation` dependency;
  defaults to `SparseRotation(dimension, seed=seed)`. The previous
  `cache_dir` parameter was removed: the rotation is deterministic
  given `(dimension, seed)`, so the on-disk pickle cache was redundant.
- `benchmarks/synthetic_mae.py` ported from Minervia's
  `benchmark_turbo.py`: updated to the new API, English output, strict
  `zip()`, type hints, no `sys.path` hack. Still a bare-bones script;
  a proper CLI with JSON output and BEIR integration lands later.

<!--
## [0.1.0] - YYYY-MM-DD

First public pre-release.

### Added
- ...
-->
