"""Vector rotations applied before quantization.

Rotations spread distribution outliers across dimensions so scalar or
product quantization loses less information. This subpackage will host
``BaseRotation`` (ABC), ``SparseRotation`` (sign-flip + permutation,
v0.1) and eventually ``HadamardRotation`` / ``LearnedRotation`` (OPQ).

Empty in the scaffold commit; populated in subsequent refactors.
"""
