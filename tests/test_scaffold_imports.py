"""Scaffold and namespace packages stay importable (coverage + packaging sanity)."""

from __future__ import annotations


def test_scaffold_subpackages_import() -> None:
    import turbochroma.codecs
    import turbochroma.kernels
    import turbochroma.rotations
    import turbochroma.storage
    import turbochroma.utils  # noqa: F401
