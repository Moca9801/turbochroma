"""Unit tests for ``turbochroma.blob_utils``."""

from __future__ import annotations

import base64

import pytest

from turbochroma.blob_utils import decode_stored_blob, max_base64_chars_for_n_bytes


def test_max_base64_monotonic() -> None:
    assert max_base64_chars_for_n_bytes(0) == 0
    assert max_base64_chars_for_n_bytes(1) == 4
    assert max_base64_chars_for_n_bytes(2) == 4
    assert max_base64_chars_for_n_bytes(3) == 4
    assert max_base64_chars_for_n_bytes(4) == 8
    with pytest.raises(ValueError, match="non-negative"):
        max_base64_chars_for_n_bytes(-1)


def test_decode_rejects_length_before_decode() -> None:
    n = 4
    max_c = max_base64_chars_for_n_bytes(n)
    long_s = "A" * (max_c + 1)
    with pytest.raises(ValueError, match="exceeds maximum"):
        decode_stored_blob(long_s, n)


def test_decode_rejects_invalid_charset() -> None:
    b = b"abcd"
    s = base64.b64encode(b).decode("ascii")
    s_nl = s[:2] + "\n" + s[2:]
    with pytest.raises(ValueError, match="invalid character"):
        decode_stored_blob(s_nl, len(b))

    s_bad = s[:-1] + "!"
    with pytest.raises(ValueError, match="invalid character"):
        decode_stored_blob(s_bad, len(b))


def test_decode_rejects_wrong_length() -> None:
    # "AAAA" decodes to 3 bytes, not 4
    with pytest.raises(ValueError, match="decoded length"):
        decode_stored_blob("AAAA", 4)


def test_decode_round_trip() -> None:
    raw = b"\x00\x01\x02\x03"
    s = base64.b64encode(raw).decode("ascii")
    assert decode_stored_blob(s, 4) == raw


def test_decode_empty_zero_expected() -> None:
    assert decode_stored_blob("", 0) == b""
