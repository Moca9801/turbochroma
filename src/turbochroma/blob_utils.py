"""Size bounds and safe decoding for base64-wrapped int8 vector blobs.

Metadata values come from the application / database and must be treated
as *untrusted* for size and shape: reject pathological strings before
``base64.b64decode`` allocates large buffers.
"""

from __future__ import annotations

import base64
import binascii
import re

# Only standard base64 alphabet + padding. Rejects newlines, URLs, etc.
_B64_RE = re.compile(r"^[A-Za-z0-9+/]+=*$")


def max_base64_chars_for_n_bytes(n: int) -> int:
    """Upper bound on length of a standard base64 *string* for *n* raw bytes (with padding)."""
    if n < 0:
        msg = "n must be non-negative"
        raise ValueError(msg)
    if n == 0:
        return 0
    return 4 * ((n + 2) // 3)


def decode_stored_blob(b64: str, compressed_size_bytes: int) -> bytes:
    """Decode a base64 blob and enforce exact raw byte length.

    Args:
        b64: Base64 (ASCII) string, no newlines. Must decode to *exactly*
            ``compressed_size_bytes`` bytes.
        compressed_size_bytes: Expected size of the decoded payload (e.g.
            from :attr:`turbochroma.codecs.base.BaseCodec.compressed_size_bytes`).

    Returns:
        The decoded :class:`bytes` object of length ``compressed_size_bytes``.

    Raises:
        ValueError: If the string is too long, malformed, or decodes to a
            length other than ``compressed_size_bytes``.

    This function never calls :func:`base64.b64decode` on strings longer
    than the documented maximum for the target size, which bounds worst-case
    memory use from hostile metadata.
    """
    if compressed_size_bytes < 0:
        msg = "compressed_size_bytes must be non-negative"
        raise ValueError(msg)
    max_chars = max_base64_chars_for_n_bytes(compressed_size_bytes)
    n = len(b64)
    if n == 0:
        if compressed_size_bytes == 0:
            return b""
        msg = "empty base64 for non-zero expected payload size"
        raise ValueError(msg)
    if n > max_chars:
        msg = (
            f"base64 length {n} exceeds maximum {max_chars} for "
            f"{compressed_size_bytes} byte payload (possible abuse or corruption)"
        )
        raise ValueError(msg)
    if not _B64_RE.match(b64):
        msg = "base64 string has invalid characters or format"
        raise ValueError(msg)
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as e:
        msg = "invalid base64"
        raise ValueError(msg) from e
    if len(raw) != compressed_size_bytes:
        msg = f"decoded length {len(raw)} != expected {compressed_size_bytes}"
        raise ValueError(msg)
    return raw
