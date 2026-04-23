"""Tests for SQ8Codec: roundtrip, determinism, shape, asymmetric dot sanity."""

from __future__ import annotations

import numpy as np
import pytest

from turbochroma import MAX_COMPRESSED_BLOB_BYTES, BaseCodec, SparseRotation, SQ8Codec


@pytest.fixture
def codec() -> SQ8Codec:
    return SQ8Codec(dimension=128, seed=42)


@pytest.fixture
def normalized_vectors() -> np.ndarray:
    rng = np.random.default_rng(seed=2024)
    data = rng.standard_normal((50, 128)).astype(np.float32)
    return data / np.linalg.norm(data, axis=1, keepdims=True)


def test_version_and_shape(codec: SQ8Codec) -> None:
    assert codec.version == "sq8-v1"
    assert codec.dimension == 128
    assert codec.compressed_size_bytes == 128


def test_default_rotation_is_sparse(codec: SQ8Codec) -> None:
    assert isinstance(codec.rotation, SparseRotation)
    assert codec.rotation.dimension == 128


def test_custom_rotation_is_honored() -> None:
    rot = SparseRotation(dimension=64, seed=7)
    codec = SQ8Codec(dimension=64, rotation=rot)
    assert codec.rotation is rot


def test_rejects_rotation_with_mismatched_dimension() -> None:
    rot = SparseRotation(dimension=64, seed=7)
    with pytest.raises(ValueError, match="does not match"):
        SQ8Codec(dimension=128, rotation=rot)


def test_rejects_out_of_range_dimension() -> None:
    with pytest.raises(ValueError, match="dimension must be in"):
        SQ8Codec(dimension=0)
    with pytest.raises(ValueError, match="dimension must be in"):
        SQ8Codec(dimension=MAX_COMPRESSED_BLOB_BYTES + 1)


def test_compress_batch_returns_correct_blob_size(
    codec: SQ8Codec, normalized_vectors: np.ndarray
) -> None:
    blobs = codec.compress_batch(normalized_vectors)
    assert len(blobs) == len(normalized_vectors)
    assert all(len(b) == codec.compressed_size_bytes for b in blobs)
    assert all(isinstance(b, bytes) for b in blobs)


def test_roundtrip_preserves_structure(
    codec: SQ8Codec, normalized_vectors: np.ndarray
) -> None:
    blobs = codec.compress_batch(normalized_vectors)
    recovered = codec.decompress_batch(blobs)
    assert recovered.shape == normalized_vectors.shape
    mae = float(np.mean(np.abs(recovered - normalized_vectors)))
    assert mae < 0.02, f"MAE too high after roundtrip: {mae}"


def test_asymmetric_dot_approximates_true_dot(
    codec: SQ8Codec, normalized_vectors: np.ndarray
) -> None:
    query = normalized_vectors[0]
    for i in range(1, 10):
        doc = normalized_vectors[i]
        blob = codec.compress(doc)
        true_dot = float(np.dot(query, doc))
        adc_dot = codec.asymmetric_dot(query, blob)
        assert abs(true_dot - adc_dot) < 0.05, (
            f"ADC drift too large: true={true_dot}, adc={adc_dot}"
        )


def test_determinism_across_instances() -> None:
    rng = np.random.default_rng(seed=7)
    vectors = rng.standard_normal((10, 64)).astype(np.float32)
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    codec_a = SQ8Codec(dimension=64, seed=42)
    codec_b = SQ8Codec(dimension=64, seed=42)

    blobs_a = codec_a.compress_batch(vectors)
    blobs_b = codec_b.compress_batch(vectors)
    assert blobs_a == blobs_b, "Same seed must produce identical blobs"


def test_inherits_basecodec() -> None:
    assert issubclass(SQ8Codec, BaseCodec)


def test_blobspec_fingerprint_includes_codec_rotation_seed() -> None:
    a = SQ8Codec(dimension=128, seed=1)
    b = SQ8Codec(dimension=128, seed=2)
    assert a.blobspec_fingerprint() == a.blobspec_fingerprint()
    assert a.blobspec_fingerprint() != b.blobspec_fingerprint()
    assert "sq8-v1" in a.blobspec_fingerprint()
    assert "sparse-v1" in a.blobspec_fingerprint()
    assert "s=1" in a.blobspec_fingerprint()
    assert "s=2" in b.blobspec_fingerprint()
