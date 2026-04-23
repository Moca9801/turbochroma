"""Synthetic MAE benchmark for turbochroma codecs.

Measures three things on a batch of L2-normalized synthetic vectors:

1. Compression throughput (seconds per vector).
2. ADC drift: |true_dot - asymmetric_dot| across all (query, doc) pairs.
3. Storage ratio vs. raw float32.

This script is ported from Minervia's ``benchmark_turbo.py``. The public
API shift (``TurboQuantizer`` -> ``SQ8Codec``, method rename
``compute_asymmetric_dot`` -> ``asymmetric_dot``) and the removal of the
``cache_dir`` parameter are reflected here.

Usage:
    python benchmarks/synthetic_mae.py
"""

from __future__ import annotations

import time

import numpy as np

from turbochroma import SQ8Codec


def run_benchmark(num_vectors: int = 500, dim: int = 1024) -> None:
    codec = SQ8Codec(dimension=dim)

    rng = np.random.default_rng(seed=2024)
    data = rng.standard_normal((num_vectors, dim)).astype(np.float32)
    data = data / np.linalg.norm(data, axis=1, keepdims=True)

    queries = rng.standard_normal((5, dim)).astype(np.float32)
    queries = queries / np.linalg.norm(queries, axis=1, keepdims=True)

    print(
        f"\n--- Benchmark SQ8Codec "
        f"(dim: {dim}, vectors: {num_vectors}, queries: {len(queries)}) ---\n"
    )

    t0 = time.time()
    compressed_data = [codec.compress(v) for v in data]
    t_compress = time.time() - t0
    print(
        f"Compression: {t_compress:.3f}s "
        f"({t_compress / num_vectors * 1000:.2f} ms per vector)"
    )

    errors: list[float] = []
    t0 = time.time()
    for query in queries:
        for v, comp in zip(data, compressed_data, strict=True):
            original_dot = float(np.dot(query, v))
            adc_dot = codec.asymmetric_dot(query, comp)
            errors.append(abs(original_dot - adc_dot))
    t_search = time.time() - t0

    total_ops = len(queries) * num_vectors
    print(f"Asymmetric search: {t_search:.3f}s ({total_ops} pairs)")
    print("\nDistortion results:")
    print(f"  Mean absolute error (MAE): {np.mean(errors):.6f}")
    print(f"  Max error:                 {np.max(errors):.6f}")
    print(f"  Std dev:                   {np.std(errors):.6f}")

    sample_comp = compressed_data[0]
    original_bytes = dim * 4
    compressed_bytes = len(sample_comp)
    ratio = original_bytes / compressed_bytes
    print(
        f"\nCompression: {original_bytes} B -> {compressed_bytes} B "
        f"(ratio: {ratio:.1f}x)"
    )

    mae = float(np.mean(errors))
    if mae < 0.02:
        print(f"\nOK: MAE={mae:.4f} < 2%. SQ8Codec performing within spec.")
    else:
        print(f"\nWARN: MAE={mae:.4f} > 2%. Check rotation / calibration.")


if __name__ == "__main__":
    run_benchmark()
