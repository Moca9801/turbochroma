"""Unit tests for ``turbochroma.blob_utils``."""

from __future__ import annotations

import base64

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings

from turbochroma.blob_utils import (
    MAX_COMPRESSED_BLOB_BYTES,
    decode_stored_blob,
    max_base64_chars_for_n_bytes,
)


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


def test_max_base64_grows_linearly_for_large_n() -> None:
    """O(1) formula for large n (e.g. high embedding dim): bounded, no pathological int edges."""
    n = 1_048_576
    m = max_base64_chars_for_n_bytes(n)
    assert m == 4 * ((n + 2) // 3)
    assert 1_300_000 < m < 1_500_000


def test_decode_rejects_oversize_declared_length() -> None:
    with pytest.raises(ValueError, match="exceeds maximum"):
        decode_stored_blob("YQ==", MAX_COMPRESSED_BLOB_BYTES + 1)


@given(
    b64_body=st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
        max_size=8_000,
    ),
    declared=st.integers(min_value=0, max_value=MAX_COMPRESSED_BLOB_BYTES + 2),
)
@settings(max_examples=120, deadline=None)
def test_decode_stored_blob_property_never_crashes(b64_body: str, declared: int) -> None:
    """Random strings and lengths only raise ValueError or succeed — no interpreter crash."""
    import contextlib

    with contextlib.suppress(ValueError):
        decode_stored_blob(b64_body, declared)
