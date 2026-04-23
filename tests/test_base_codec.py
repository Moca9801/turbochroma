"""Tests for BaseCodec default helpers and concrete behavior via SQ8Codec."""

from __future__ import annotations

import numpy as np

from turbochroma import SQ8Codec


def test_compress_decompress_single_vector_roundtrip() -> None:
    codec = SQ8Codec(dimension=8, seed=0)
    v = np.random.default_rng(1).standard_normal(8).astype(np.float32)
    b = codec.compress(v)
    assert len(b) == codec.compressed_size_bytes
    w = codec.decompress(b)
    assert w.shape == (8,)
    assert w.dtype == np.float32
    mae = float(np.mean(np.abs(w - v)))
    assert mae < 0.5


def test_fit_default_is_noop() -> None:
    codec = SQ8Codec(dimension=8, seed=0)
    sample = np.zeros((2, 8), dtype=np.float32)
    assert codec.fit(sample) is None
