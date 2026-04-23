"""turbochroma - drop-in vector compression for ChromaDB.

Public surface (grows commit by commit; see ``CHANGELOG.md``):

Codecs
    :class:`BaseCodec`   - ABC for all codecs.
    :class:`SQ8Codec`    - 8-bit scalar quantization with a pluggable rotation.

Rotations
    :class:`BaseRotation`    - ABC for all rotations.
    :class:`SparseRotation`  - sign-flip + permutation, O(d). Default.
"""

from turbochroma._version import __version__
from turbochroma.codecs import BaseCodec, SQ8Codec
from turbochroma.rotations import BaseRotation, SparseRotation

__all__ = [
    "BaseCodec",
    "BaseRotation",
    "SQ8Codec",
    "SparseRotation",
    "__version__",
]
