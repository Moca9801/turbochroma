"""turbochroma - drop-in vector compression for ChromaDB.

Public surface (grows commit by commit; see ``CHANGELOG.md``):

Codecs
    :class:`BaseCodec`   - ABC for all codecs.
    :class:`SQ8Codec`    - 8-bit scalar quantization with a pluggable rotation.

Rotations
    :class:`BaseRotation`    - ABC for all rotations.
    :class:`SparseRotation`  - sign-flip + permutation, O(d). Default.

Chroma
    :class:`QuantizedCollection` - wrap a Chroma collection with blob metadata + ADC re-rank.
    :data:`DefaultBlobKey`         - default metadata key for the stored blob (``"tc_sq8_v1"``).
"""

from turbochroma._version import __version__
from turbochroma.codecs import BaseCodec, SQ8Codec
from turbochroma.collection import DefaultBlobKey, QuantizedCollection
from turbochroma.rotations import BaseRotation, SparseRotation

__all__ = [
    "BaseCodec",
    "BaseRotation",
    "DefaultBlobKey",
    "QuantizedCollection",
    "SQ8Codec",
    "SparseRotation",
    "__version__",
]
