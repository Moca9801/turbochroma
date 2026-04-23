"""Base interface for rotations applied before quantization.

A rotation preprocesses vectors so that scalar or product quantization
loses less information. Typical choices, from cheapest to most powerful:

- :class:`~turbochroma.rotations.sparse.SparseRotation`
    O(d), sign-flip + permutation. Default in v0.1.
- *(planned)* HadamardRotation — O(d log d), structured orthogonal
  transform with better JL-style guarantees.
- *(planned)* LearnedRotation — OPQ-style, learned from a sample via SVD.

All rotations are **exact inverses of themselves** up to floating-point
error; :meth:`inverse` is mandatory.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseRotation(ABC):
    """Abstract base class for reversible vector rotations.

    Attributes:
        dimension: Dimensionality of the vectors the rotation operates on.
        version: Identifier that disambiguates different rotation
            families or parameterizations.
    """

    dimension: int
    version: str

    @abstractmethod
    def apply(self, vectors: np.ndarray) -> np.ndarray:
        """Rotate one vector or a batch of vectors.

        Args:
            vectors: float32 array of shape ``(dimension,)`` or
                ``(N, dimension)``.

        Returns:
            Rotated array of the same shape.
        """

    @abstractmethod
    def inverse(self, rotated: np.ndarray) -> np.ndarray:
        """Reverse :meth:`apply`.

        Args:
            rotated: float32 array of shape ``(dimension,)`` or
                ``(N, dimension)``.

        Returns:
            Un-rotated array of the same shape.
        """
