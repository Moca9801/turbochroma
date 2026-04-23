"""Shared pytest fixtures.

Populated in subsequent commits once the public API exists.
Typical fixtures will include:
    - ``random_vectors(n, d)`` — deterministic L2-normalized vectors
    - ``in_memory_chroma_collection`` — ephemeral Chroma for tests
    - ``calibrated_sq8_codec`` — codec fitted on a small sample
"""
