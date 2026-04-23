"""Base interface for vector compression codecs.

A :class:`BaseCodec` takes dense float32 vectors and produces compact
byte blobs; it also knows how to compute distance between a float32
query and a compressed document **without full decompression**
(asymmetric distance computation, or ADC).

Concrete codecs live next to this module:
    - :class:`~turbochroma.codecs.sq8.SQ8Codec` — 8-bit scalar quantization.
    - *(planned)* PQCodec — product quantization, v0.2.
    - *(planned)* RaBitQCodec — 1-bit binary quantization, v0.3.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseCodec(ABC):
    """Abstract base class for vector compression codecs.

    Subclasses must implement :meth:`compress_batch`,
    :meth:`decompress_batch` and :meth:`asymmetric_dot`. The scalar
    helpers :meth:`compress` and :meth:`decompress` have batch-based
    default implementations that concrete codecs may override for speed.

    Attributes:
        dimension: Dimensionality of the input vectors.
        version: Codec version identifier. Used to invalidate stored
            blobs when the codec's internal format changes.
        compressed_size_bytes: Size in bytes of one compressed vector.
    """

    dimension: int
    version: str
    compressed_size_bytes: int

    @abstractmethod
    def compress_batch(self, vectors: np.ndarray) -> list[bytes]:
        """Compress ``N`` vectors into a list of byte blobs.

        Args:
            vectors: float32 array of shape ``(N, dimension)``.

        Returns:
            List of ``N`` byte strings, each of length
            ``compressed_size_bytes``.
        """

    @abstractmethod
    def decompress_batch(self, blobs: list[bytes]) -> np.ndarray:
        """Decompress a list of byte blobs back to float32 vectors.

        Args:
            blobs: list of byte strings produced by :meth:`compress_batch`.

        Returns:
            float32 array of shape ``(len(blobs), dimension)``.
        """

    @abstractmethod
    def asymmetric_dot(self, query: np.ndarray, blob: bytes) -> float:
        """Compute the dot product between a float32 query and a compressed doc.

        The "asymmetric" adjective means the query is never compressed;
        this preserves query precision while still reaping the
        memory / bandwidth benefits of compressed documents.

        Args:
            query: float32 array of shape ``(dimension,)``.
            blob: byte string produced by :meth:`compress`.

        Returns:
            Scalar dot product.
        """

    def compress(self, vector: np.ndarray) -> bytes:
        """Compress a single vector.

        Default implementation delegates to :meth:`compress_batch`.
        """
        return self.compress_batch(vector.reshape(1, -1))[0]

    def decompress(self, blob: bytes) -> np.ndarray:
        """Decompress a single blob to a float32 vector.

        Default implementation delegates to :meth:`decompress_batch`.
        """
        return self.decompress_batch([blob])[0]

    def fit(self, sample: np.ndarray) -> None:
        """Calibrate the codec on a sample of real vectors.

        Default: no-op. Subclasses may override to learn per-dimension
        scales, codebooks, or rotations.
        """
        return None
