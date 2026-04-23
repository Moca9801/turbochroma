"""Vector compression codecs.

Public classes:

- :class:`BaseCodec` — abstract base class that all codecs implement.
- :class:`SQ8Codec` — 8-bit scalar quantization (v0.1 MVP codec).

Planned additions (not in this release):

- ``PQCodec`` — product quantization, v0.2.
- ``RaBitQCodec`` — 1-bit binary quantization, v0.3.
"""

from turbochroma.codecs.base import BaseCodec
from turbochroma.codecs.sq8 import SQ8Codec

__all__ = ["BaseCodec", "SQ8Codec"]
