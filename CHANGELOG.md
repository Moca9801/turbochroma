# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `turbochroma.blob_utils`: bounded base64 decoding for metadata blobs
  (`max_base64_chars_for_n_bytes`, `decode_stored_blob`) to limit work from
  hostile or corrupted metadata.
- `QuantizedCollection(..., strict=True)` and per-call
  `query(..., strict=True)`: on ADC re-ranking, invalid stored blobs raise
  `ValueError` instead of falling back to Chroma’s distance (default
  `strict=False` remains tolerant for backward compatibility).
- `py.typed` marker for PEP 561 type checking.
- `tests/test_blob_utils.py` and collection tests for strict vs tolerant decode.
- `SECURITY.md` and Dependabot config for `pip` and GitHub Actions.
- CI: `mypy src` in the lint job.
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
- `QuantizedCollection` in `turbochroma.collection`: wraps a Chroma
  `Collection`, injects base64 codec blobs into metadata on `add` /
  `upsert`, optional ADC re-ranking on `query` when
  `refine_factor>1` and `query_embeddings` is used, and `fit_existing`
  to backfill blobs for rows that already have stored vectors.  Default
  metadata key: `DefaultBlobKey` (`"tc_sq8_v1"`).  Other `Collection`
  methods are delegated via `__getattr__` (e.g. `count`, `get`, `delete`).
- `query` strips `"ids"` from `include` before calling Chroma (Chroma 1.5+
  does not accept `ids` in `include`; ids are always returned).
- Test suite `tests/test_collection.py`: metadata blob injection,
  `fit_existing`, `refine_factor=1` parity with raw Chroma, multi-candidate
  `refine_factor=4`, delegation, dimension validation, strict vs tolerant
  ADC on tampered blobs.

### Changed

- ADC re-ranking now decodes metadata blobs via `decode_stored_blob` (length
  cap, character set, `validate=True`, exact size check).
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
