"""Low-level compute kernels for asymmetric distance computation.

Two implementations are planned for v0.1:

- ``numpy_impl`` — vectorized ADC in pure numpy (always available).
- ``numba_impl`` — JIT-compiled ADC via numba (optional extra
  ``turbochroma[fast]``; falls back transparently if not installed).

Empty in the scaffold commit; populated in subsequent refactors.
"""
