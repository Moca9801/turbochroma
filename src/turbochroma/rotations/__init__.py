"""Vector rotations applied before quantization.

Rotations spread distribution outliers across dimensions so scalar or
product quantization loses less information.

Public classes:

- :class:`BaseRotation` — abstract base class.
- :class:`SparseRotation` — sign-flip + permutation, O(d). Default in v0.1.

Planned additions:

- ``HadamardRotation`` — structured orthogonal, O(d log d).
- ``LearnedRotation`` — OPQ-style, learned from a sample.
"""

from turbochroma.rotations.base import BaseRotation
from turbochroma.rotations.sparse import SparseRotation

__all__ = ["BaseRotation", "SparseRotation"]
