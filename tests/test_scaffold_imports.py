"""Scaffold and namespace packages stay importable (coverage + packaging sanity)."""

from __future__ import annotations


def test_scaffold_subpackages_import() -> None:
    import turbochroma.codecs  # noqa: F401
    import turbochroma.kernels  # noqa: F401
    import turbochroma.rotations  # noqa: F401
    import turbochroma.storage  # noqa: F401
    import turbochroma.utils  # noqa: F401
