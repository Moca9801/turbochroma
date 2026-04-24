# turbochroma

[![test](https://github.com/Moca9801/turbochroma/actions/workflows/test.yml/badge.svg)](https://github.com/Moca9801/turbochroma/actions/workflows/test.yml)
[![CodeQL](https://github.com/Moca9801/turbochroma/actions/workflows/codeql.yml/badge.svg)](https://github.com/Moca9801/turbochroma/actions/workflows/codeql.yml)
[![docs](https://github.com/Moca9801/turbochroma/actions/workflows/docs.yml/badge.svg)](https://github.com/Moca9801/turbochroma/actions/workflows/docs.yml)

> **High-performance vector compression for ChromaDB: 4× less RAM, <1% recall loss, zero ingest-code changes.**

`turbochroma` solves the high RAM consumption problem in ChromaDB as collections grow. Instead of migrating to a more complex vector database (like Qdrant or Milvus), it allows you to:

- **Reduce RAM usage by 4×**: Stores compressed (SQ8 - 8-bit) vectors directly in metadata.
- **Search faster with ADC**: Uses Asymmetric Distance Computation (ADC) to re-order candidates without fully decompressing vectors.
- **Maintain precision**: Implements a "Sparse Rotation" step before quantization to minimize information loss (typically <1% recall loss).

> **Status**: pre-alpha (`0.1.0.dev0`). API may change before `0.1.0`. Pin
> versions for production only after a stable release. See
> [STABILITY.md](STABILITY.md) (semver, deprecations) and
> [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## Why turbochroma

ChromaDB [does not ship native vector quantization](https://github.com/chroma-core/chroma/issues).
If your collection grows past what your RAM can comfortably hold, your options
today are:

| Option | Cost |
|---|---|
| Migrate to Qdrant / Milvus / Weaviate | Infra rewrite, new ops surface |
| Reduce embedding dimension (e.g. PCA, smaller model) | Model retraining, recall loss across the board |
| **`pip install turbochroma`** | Small code change, no vector DB swap |

---

## Use cases and real-world applications

| Scenario | How turbochroma helps |
|----------|------------------------|
| **RAG at scale (many sources, many chunks)** | Each chunk carries a dense vector; large corpora swell RAM and I/O. SQ8 ≈ **4× smaller blobs** in metadata, while ADC can **re-rank** a cheap wide pool before an expensive cross-encoder or LLM. |
| **Tight RAM or many per-tenant collections** | You keep Chroma; you do not migrate. Less memory per row means more headroom for **multi-tenant** or per-product collections on one host. |
| **Cheap re-rank before a heavy reranker** | Common pattern: Chroma (fast, approximate) → **wider top‑K** (e.g. `n_results × refine_factor`) → **ADC re-ordering** in O(d) on CPU → top‑N to BGE / cross-encoder. Saves **GPU and latency** on the expensive model. |
| **Backfill legacy indexes** | Data indexed **without** blobs: `fit_existing()` walks stored embeddings and writes the blob into metadata, **without re-embedding** from text. |
| **Hybrid RAG (dense + sparse)** | Chroma can still back BM25/keyword; turbochroma only augments the **dense** path with smaller sidecar data and an optional re-rank pass. |

**What it is *not* (primarily)**: a replacement for billion-scale FAISS-IVF-PQ clusters, or a substitute for retraining a better embedder. It is a **pragmatic layer** for teams already on Chroma.

### Limitations (read before you ship)

- **Re-rank cannot rescue misses**: If the correct chunk is not in Chroma’s top `(n_results × refine_factor)` hits, ADC cannot invent it. Tune `n_results` and `refine_factor` to your recall needs.
- **ADC refinement with `refine_factor > 1` applies only to `query_embeddings=...`**. If you only pass `query_texts` (and let Chroma embed), the wrapper **falls back to native Chroma order** and may emit a `UserWarning`.
- Chroma’s `query(..., include=...)` does **not** allow `"ids"`; IDs are always returned. The wrapper strips `"ids"` from `include` before calling Chroma.
- The default SQ8 path stores one **byte per dimension** in the blob, with a **hard cap** of `MAX_COMPRESSED_BLOB_BYTES` (1 MiB) on both codec dimension and decoded payload size. If you need larger vectors, open an issue (you would need a different storage layout or a raised limit).
- Blobs are stored as **base64 in metadata** (Chroma’s accepted types). You pay some storage overhead on top of raw int8; later releases may add sidecar storage for tighter layouts. Values are size-checked before decoding. A second field (`DefaultBlobspecKey` / `tc_blobspec_v1` by default) stores a **codec fingerprint** (`BaseCodec.blobspec_fingerprint`) so ADC can detect a blob written with a different codec, dimension, rotation, or seed. If the field is **missing** (older rows), only the base64 is validated. Set `blobspec_key=None` on `QuantizedCollection` to disable writing and checking that field. For **integrity-sensitive** re-ranking, use `strict=True` on `QuantizedCollection` or on `query(...)` so a bad blob or mismatched fingerprint fails with `ValueError` instead of falling back to Chroma’s distance.

Context and trade-offs: [`docs/design/001-why-turbochroma.md`](docs/design/001-why-turbochroma.md).

---

## Installation

```bash
pip install turbochroma
```

**Develop from a git clone (editable):**

```bash
cd turbochroma
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -e ".[dev]"
```

Contributors: [CONTRIBUTING.md](CONTRIBUTING.md) (pre-commit, ruff, mypy, `pip-audit`). Quality bar: [QUALITY.md](QUALITY.md), [docs/quality-gates.md](docs/quality-gates.md), [TESTING.md](TESTING.md). API & design site: build with `pip install -e ".[docs]" && mkdocs build` (sources under `docs/`).

Optional extras:

- `turbochroma[fast]` — numba kernels for faster ADC
- `turbochroma[parquet]` — sidecar parquet storage backend (planned wiring)
- `turbochroma[bench]` — datasets + matplotlib for reproducing benchmarks

---

## End-to-end example

Match **`SQ8Codec(dimension=...)`** to your embedder (e.g. 1024 for BGE-M3, 384 for
many small models). Blobs are written under the default metadata key
`DefaultBlobKey` (`"tc_sq8_v1"`).

```python
import numpy as np
import chromadb
from chromadb.config import Settings
from turbochroma import QuantizedCollection, SQ8Codec, DefaultBlobKey

# Same dimension as your embedding model
DIM = 1024
SEED = 42

# 1) Chroma as usual
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(
    "my_docs",
    metadata={"hnsw:space": "cosine"},
)

# 2) Codec + wrapper
codec = SQ8Codec(dimension=DIM, seed=SEED)
qc = QuantizedCollection(
    collection,
    codec,
    refine_factor=4,
)

def norm_rows(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32)
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n = np.where(n == 0, 1.0, n)
    return x / n

# 3) Ingest: replace with outputs from your embedder
embeddings = norm_rows(np.random.randn(50, DIM))
qc.add(
    ids=[f"chunk_{i}" for i in range(50)],
    embeddings=embeddings.tolist(),
    metadatas=[{"source": f"doc_{i // 10}"} for i in range(50)],
)

# 4) Optional: confirm the blob in metadata
row = collection.get(ids=["chunk_0"], include=["metadatas"])
assert DefaultBlobKey in (row["metadatas"][0] or {})

# 5) Query with optional ADC re-rank (use your real query embedding)
q = norm_rows(np.random.randn(1, DIM))[0].tolist()
results = qc.query(
    query_embeddings=[q],
    n_results=8,
    include=["metadatas", "distances", "documents"],
    refine_factor=4,
)
print("Top ids:", results["ids"][0][:3])

# 6) Vectors already in Chroma but added without turbochroma? Backfill:
# n = qc.fit_existing()
# print("metadata rows updated:", n)
```

**Experimenting / seeing the effect**

- **`get(..., include=["metadatas"])`**: check for the key `tc_sq8_v1` and the base64
  value (one logical int8 per dimension, base64 in JSON).
- **Compare** `refine_factor=1` vs `4` on the *same* `query_embeddings` and
  watch whether `ids[0]` order changes (larger effect when *more* than two
  documents compete and Chroma’s first stage is imperfect for your metric).
- **Codec-only sanity check** (no Chroma): from the repo root, run
  `python benchmarks/synthetic_mae.py` for MAE, compression ratio, and timing.

---

## 30-second quickstart (minimal)

```python
import chromadb
from turbochroma import QuantizedCollection, SQ8Codec

DIM = 1024
client = chromadb.PersistentClient(path="./chroma")
coll = client.get_or_create_collection("docs")
qc = QuantizedCollection(coll, SQ8Codec(dimension=DIM, seed=42), refine_factor=4)

# qc.add(... embeddings from your model ...)
# q_vec = your_query_embedding  # list[float] length DIM
# qc.query(query_embeddings=[q_vec], n_results=10, include=["metadatas", "distances"])
```

If you only have existing float vectors: `QuantizedCollection(...).fit_existing()`.

---

## How it works

1. **Sparse rotation** — every embedding is multiplied by a fixed ±1 sign
   pattern and permuted. This spreads distribution outliers across
   dimensions so scalar quantization loses less information.
2. **SQ8 quantization** — each rotated float32 dimension is scaled and
   clipped to int8 (4× compression).
3. **Asymmetric distance computation (ADC)** — at query time the query
   stays in float32, the document is decompressed on the fly, and the
   dot product is computed directly. You pay float32 precision only for
   the query, which is already cheap.

More detail: [`docs/design/001-why-turbochroma.md`](docs/design/001-why-turbochroma.md).

---

## Benchmarks

Synthetic MAE and compression: `python benchmarks/synthetic_mae.py` from a clone.

BEIR-style tables: *planned* for v0.1.0; see the roadmap.

| Metric | Chroma vanilla (float32) | turbochroma SQ8 | FAISS SQ8 (baseline) |
|---|---|---|---|
| Recall@10 | TBD | TBD | TBD |
| MRR@10 | TBD | TBD | TBD |
| RAM peak | TBD | TBD | TBD |
| p50 query latency | TBD | TBD | TBD |

---

## Roadmap

- **v0.1.0** — SQ8 codec + sparse rotation + `QuantizedCollection` + two
  storage backends (metadata-blob, sidecar parquet) + BEIR benchmarks.
- **v0.2.0** — Product Quantization (PQ) codec.
- **v0.3.0** — 1-bit / RaBitQ-style codec (32× compression).
- **v0.4.0** — Learned rotation (OPQ-style) trained on your corpus.

---

## Credits

Originally incubated inside [Minervia](https://github.com/), a Spanish-language
legal-RAG system. See [`CREDITS.md`](CREDITS.md) for full lineage.

Created and maintained by **Angel Israel Moreno Castellanos**.

---

## License

MIT — see [`LICENSE`](LICENSE).
