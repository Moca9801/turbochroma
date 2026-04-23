"""8-bit scalar quantization codec with sparse rotation preprocessing.

Produces 4:1 compression (e.g. 4096 B → 1024 B for 1024-d vectors) with
typical mean-absolute error below 0.01 on L2-normalized inputs.

The rotation (sparse sign-flip + permutation) is kept internal to this
codec for now; it is extracted into its own :mod:`turbochroma.rotations`
subpackage in a subsequent commit so users can plug in custom rotations
(Hadamard, OPQ, etc.).
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from turbochroma.codecs.base import BaseCodec


class SQ8Codec(BaseCodec):
    """8-bit scalar quantization with sparse rotation.

    Pipeline per vector:
        1. sign-flip + permutation (O(d)) — spreads outliers across dims.
        2. scale by 127, clip to ``[-128, 127]``, cast to ``int8``.

    On query:
        the query is rotated in the same space and dotted against the
        decompressed int8 blob (asymmetric distance computation).

    The rotation seed is deterministic so that blobs generated in
    different processes with the same ``dimension`` and ``seed`` are
    interchangeable. The rotation is persisted to ``cache_dir`` so the
    next run of the same process can reload it without drift.
    """

    version = "sq8-v1"

    def __init__(
        self,
        dimension: int = 1024,
        cache_dir: str | Path = "cache",
        seed: int = 42,
    ) -> None:
        self.dimension = dimension
        self.compressed_size_bytes = dimension
        self._seed = seed
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._config_path = self._cache_dir / f"turbo_pro_config_{dimension}.pkl"
        self._permutation, self._sign_flip = self._load_or_generate_rotation()

    @property
    def config_version(self) -> str:
        """Alias of :attr:`version` kept for compatibility with Minervia callers."""
        return self.version

    def _load_or_generate_rotation(self) -> tuple[np.ndarray, np.ndarray]:
        if self._config_path.exists():
            with self._config_path.open("rb") as f:
                data = pickle.load(f)
            stored_version = data.get("version", "legacy")
            if stored_version == self.version or "8bit" in stored_version or stored_version == "legacy":
                return data["perm"], data["signs"]

        rng = np.random.default_rng(self._seed)
        perm = rng.permutation(self.dimension)
        signs = rng.choice([-1.0, 1.0], size=self.dimension).astype(np.float32)
        with self._config_path.open("wb") as f:
            pickle.dump({"perm": perm, "signs": signs, "version": self.version}, f)
        return perm, signs

    def _apply_rotation(self, v: np.ndarray) -> np.ndarray:
        return (v * self._sign_flip)[self._permutation]

    def _inverse_rotation(self, v_rot: np.ndarray) -> np.ndarray:
        unpermuted = np.empty_like(v_rot)
        unpermuted[self._permutation] = v_rot
        return unpermuted * self._sign_flip

    def _decompress_to_rotated(self, blob: bytes) -> np.ndarray:
        data = np.frombuffer(blob, dtype=np.int8)
        return data.astype(np.float32) / 127.0

    def compress_batch(self, vectors: np.ndarray) -> list[bytes]:
        v = vectors.astype(np.float32)
        v_rot = (v * self._sign_flip)[:, self._permutation]
        v_int8 = np.clip(v_rot * 127.0, -128, 127).astype(np.int8)
        return [row.tobytes() for row in v_int8]

    def decompress_batch(self, blobs: list[bytes]) -> np.ndarray:
        rotated = np.stack(
            [np.frombuffer(b, dtype=np.int8).astype(np.float32) / 127.0 for b in blobs]
        )
        unpermuted = np.empty_like(rotated)
        unpermuted[:, self._permutation] = rotated
        return unpermuted * self._sign_flip

    def asymmetric_dot(self, query: np.ndarray, blob: bytes) -> float:
        q_rot = self._apply_rotation(query)
        v_recon_rot = self._decompress_to_rotated(blob)
        return float(np.dot(q_rot, v_recon_rot))
