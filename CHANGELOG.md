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

### Changed

- `TurboQuantizer` → `SQ8Codec` (class renamed). The old name is not
  aliased because the package has no external users yet.

<!--
## [0.1.0] - YYYY-MM-DD

First public pre-release.

### Added
- ...
-->
