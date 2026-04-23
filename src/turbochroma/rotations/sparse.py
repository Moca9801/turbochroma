"""Sparse rotation: sign-flip followed by permutation.

Operates in O(d). Deterministic given ``(dimension, seed)``, so no
persistence is required — two ``SparseRotation`` instances constructed
with identical arguments produce byte-identical outputs across
processes.

Rationale:
    Scalar quantization (e.g. SQ8) clips each dimension independently.
    When an embedder concentrates energy in a few dimensions (common
    with transformer encoders), uniform per-dimension clipping
    saturates those dimensions and under-uses the rest.  A random
    sign-flip + permutation spreads that energy across all dimensions,
    reducing average quantization error at a negligible cost.

This is a simplification of the structured random rotations used in
QJL / RaBitQ. It does not carry formal JL-type guarantees, but is very
cheap and empirically effective for the L2-normalized vectors produced
by most modern embedders.
"""

from __future__ import annotations

import numpy as np

from turbochroma.rotations.base import BaseRotation


class SparseRotation(BaseRotation):
    """O(d) rotation composed of a sign-flip and a dimension permutation.

    Args:
        dimension: Vector dimensionality.
        seed: PRNG seed used to generate the sign pattern and the
            permutation. The default (``42``) matches the rotation used
            by the Minervia project, so blobs are interchangeable.

    Attributes:
        permutation: ``int64`` array of shape ``(dimension,)``.
        sign_flip: ``float32`` array of shape ``(dimension,)``, values
            in ``{-1.0, +1.0}``.
    """

    version = "sparse-v1"

    def __init__(self, dimension: int, seed: int = 42) -> None:
        self.dimension = dimension
        self.seed = seed
        rng = np.random.default_rng(seed)
        self.permutation = rng.permutation(dimension)
        self.sign_flip = rng.choice([-1.0, 1.0], size=dimension).astype(np.float32)

    def apply(self, vectors: np.ndarray) -> np.ndarray:
        if vectors.ndim == 1:
            return (vectors * self.sign_flip)[self.permutation]
        if vectors.ndim == 2:
            return (vectors * self.sign_flip)[:, self.permutation]
        raise ValueError(
            f"SparseRotation.apply expects 1D or 2D arrays, got {vectors.ndim}D"
        )

    def inverse(self, rotated: np.ndarray) -> np.ndarray:
        if rotated.ndim == 1:
            unpermuted = np.empty_like(rotated)
            unpermuted[self.permutation] = rotated
            return unpermuted * self.sign_flip
        if rotated.ndim == 2:
            unpermuted = np.empty_like(rotated)
            unpermuted[:, self.permutation] = rotated
            return unpermuted * self.sign_flip
        raise ValueError(
            f"SparseRotation.inverse expects 1D or 2D arrays, got {rotated.ndim}D"
        )
