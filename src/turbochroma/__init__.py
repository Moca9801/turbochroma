"""turbochroma — drop-in vector compression for ChromaDB.

Public surface (grows commit by commit; see ``CHANGELOG.md``):

Codecs
    :class:`BaseCodec`   — ABC for all codecs.
    :class:`SQ8Codec`    — 8-bit scalar quantization with sparse rotation.
"""

from turbochroma._version import __version__
from turbochroma.codecs import BaseCodec, SQ8Codec

__all__ = [
    "BaseCodec",
    "SQ8Codec",
    "__version__",
]
