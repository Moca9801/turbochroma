"""Tests for SparseRotation: determinism, invertibility, batch correctness."""

from __future__ import annotations

import numpy as np
import pytest

from turbochroma import BaseRotation, SparseRotation


@pytest.fixture
def rotation() -> SparseRotation:
    return SparseRotation(dimension=64, seed=42)


def test_is_basecodec_subclass() -> None:
    assert issubclass(SparseRotation, BaseRotation)


def test_attributes(rotation: SparseRotation) -> None:
    assert rotation.dimension == 64
    assert rotation.seed == 42
    assert rotation.version == "sparse-v1"
    assert rotation.permutation.shape == (64,)
    assert rotation.sign_flip.shape == (64,)
    assert set(np.unique(rotation.sign_flip).tolist()) <= {-1.0, 1.0}
    assert sorted(rotation.permutation.tolist()) == list(range(64))


def test_apply_1d_is_invertible(rotation: SparseRotation) -> None:
    rng = np.random.default_rng(seed=7)
    v = rng.standard_normal(64).astype(np.float32)
    recovered = rotation.inverse(rotation.apply(v))
    np.testing.assert_allclose(recovered, v, rtol=1e-6, atol=1e-6)


def test_apply_2d_is_invertible(rotation: SparseRotation) -> None:
    rng = np.random.default_rng(seed=11)
    batch = rng.standard_normal((30, 64)).astype(np.float32)
    recovered = rotation.inverse(rotation.apply(batch))
    np.testing.assert_allclose(recovered, batch, rtol=1e-6, atol=1e-6)


def test_batch_matches_per_vector(rotation: SparseRotation) -> None:
    rng = np.random.default_rng(seed=13)
    batch = rng.standard_normal((5, 64)).astype(np.float32)
    batched = rotation.apply(batch)
    per_vector = np.stack([rotation.apply(row) for row in batch])
    np.testing.assert_array_equal(batched, per_vector)


def test_determinism_across_instances() -> None:
    r1 = SparseRotation(dimension=32, seed=123)
    r2 = SparseRotation(dimension=32, seed=123)
    np.testing.assert_array_equal(r1.permutation, r2.permutation)
    np.testing.assert_array_equal(r1.sign_flip, r2.sign_flip)


def test_different_seeds_differ() -> None:
    r1 = SparseRotation(dimension=32, seed=1)
    r2 = SparseRotation(dimension=32, seed=2)
    assert not np.array_equal(r1.permutation, r2.permutation) or not np.array_equal(
        r1.sign_flip, r2.sign_flip
    )


def test_rejects_wrong_ndim(rotation: SparseRotation) -> None:
    bad = np.zeros((2, 3, 64), dtype=np.float32)
    with pytest.raises(ValueError, match="1D or 2D"):
        rotation.apply(bad)
    with pytest.raises(ValueError, match="1D or 2D"):
        rotation.inverse(bad)
