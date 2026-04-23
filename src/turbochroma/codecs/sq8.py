"""8-bit scalar quantization codec with a pluggable rotation.

Produces 4:1 compression (e.g. 4096 B -> 1024 B for 1024-d vectors) with
typical mean-absolute error below 0.01 on L2-normalized inputs.

The rotation is now a pluggable :class:`BaseRotation` dependency. By
default ``SQ8Codec`` uses :class:`SparseRotation` with ``seed=42``,
which reproduces the exact behavior of the original Minervia
``TurboQuantizer``.
"""

from __future__ import annotations

import numpy as np

from turbochroma.codecs.base import BaseCodec
from turbochroma.rotations.base import BaseRotation
from turbochroma.rotations.sparse import SparseRotation


class SQ8Codec(BaseCodec):
    """8-bit scalar quantization with a pluggable rotation.

    Pipeline per vector:
        1. ``rotation.apply(v)`` — spreads outliers across dimensions.
        2. scale by 127, clip to ``[-128, 127]``, cast to ``int8``.

    On query, the query is rotated in the same space and dotted against
    the decompressed int8 blob (asymmetric distance computation).

    Args:
        dimension: Vector dimensionality.
        rotation: A :class:`BaseRotation` instance. If ``None``, a
            :class:`SparseRotation` with ``seed=seed`` is constructed.
        seed: Seed passed to the default ``SparseRotation`` when
            ``rotation`` is ``None``. Ignored otherwise.

    Raises:
        ValueError: if ``rotation.dimension`` does not match
            ``dimension``.
    """

    version = "sq8-v1"

    def __init__(
        self,
        dimension: int = 1024,
        rotation: BaseRotation | None = None,
        seed: int = 42,
    ) -> None:
        self.dimension = dimension
        self.compressed_size_bytes = dimension

        if rotation is None:
            rotation = SparseRotation(dimension=dimension, seed=seed)
        elif rotation.dimension != dimension:
            raise ValueError(
                f"rotation.dimension ({rotation.dimension}) does not match "
                f"codec dimension ({dimension})"
            )
        self.rotation = rotation

    @property
    def config_version(self) -> str:
        """Alias of :attr:`version` kept for compatibility with Minervia callers."""
        return self.version

    def compress_batch(self, vectors: np.ndarray) -> list[bytes]:
        v = vectors.astype(np.float32)
        v_rot = self.rotation.apply(v)
        v_int8 = np.clip(v_rot * 127.0, -128, 127).astype(np.int8)
        return [row.tobytes() for row in v_int8]

    def decompress_batch(self, blobs: list[bytes]) -> np.ndarray:
        rotated = np.stack(
            [np.frombuffer(b, dtype=np.int8).astype(np.float32) / 127.0 for b in blobs]
        )
        return self.rotation.inverse(rotated)

    def asymmetric_dot(self, query: np.ndarray, blob: bytes) -> float:
        q_rot = self.rotation.apply(query)
        v_recon_rot = np.frombuffer(blob, dtype=np.int8).astype(np.float32) / 127.0
        return float(np.dot(q_rot, v_recon_rot))
