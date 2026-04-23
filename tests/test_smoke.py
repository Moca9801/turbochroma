"""Smoke test: the package imports and exposes a version string."""

import turbochroma


def test_has_version() -> None:
    assert hasattr(turbochroma, "__version__")
    assert isinstance(turbochroma.__version__, str)
    assert turbochroma.__version__


def test_max_blob_limit_exported() -> None:
    assert hasattr(turbochroma, "MAX_COMPRESSED_BLOB_BYTES")
    assert isinstance(turbochroma.MAX_COMPRESSED_BLOB_BYTES, int)
    assert turbochroma.MAX_COMPRESSED_BLOB_BYTES > 0
