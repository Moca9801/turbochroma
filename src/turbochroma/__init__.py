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
    :data:`DefaultBlobspecKey`     - default key for the codec fingerprint (``"tc_blobspec_v1"``).
    :data:`MAX_COMPRESSED_BLOB_BYTES` - max raw blob size (metadata / codec bound).
"""

from turbochroma._version import __version__
from turbochroma.blob_utils import MAX_COMPRESSED_BLOB_BYTES
from turbochroma.codecs import BaseCodec, SQ8Codec
from turbochroma.collection import DefaultBlobKey, DefaultBlobspecKey, QuantizedCollection
from turbochroma.rotations import BaseRotation, SparseRotation

__all__ = [
    "MAX_COMPRESSED_BLOB_BYTES",
    "BaseCodec",
    "BaseRotation",
    "DefaultBlobKey",
    "DefaultBlobspecKey",
    "QuantizedCollection",
    "SQ8Codec",
    "SparseRotation",
    "__version__",
]
