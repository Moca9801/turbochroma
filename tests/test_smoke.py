"""Smoke test: the package imports and exposes a version string."""

import turbochroma


def test_has_version() -> None:
    assert hasattr(turbochroma, "__version__")
    assert isinstance(turbochroma.__version__, str)
    assert turbochroma.__version__
