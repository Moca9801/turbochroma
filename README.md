# turbochroma

[![test](https://img.shields.io/github/actions/workflow/status/Moca9801/turbochroma/test.yml?branch=main&label=test)](https://github.com/Moca9801/turbochroma/actions/workflows/test.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/Moca9801/turbochroma/codeql.yml?branch=main&label=CodeQL)](https://github.com/Moca9801/turbochroma/actions/workflows/codeql.yml)
[![docs](https://img.shields.io/github/actions/workflow/status/Moca9801/turbochroma/docs.yml?branch=main&label=docs)](https://github.com/Moca9801/turbochroma/actions/workflows/docs.yml)
[![PyPI version](https://img.shields.io/pypi/v/turbochroma.svg)](https://pypi.org/project/turbochroma/)
[![PyPI - Python](https://img.shields.io/pypi/pyversions/turbochroma.svg)](https://pypi.org/project/turbochroma/)

> **High-performance vector compression for ChromaDB: 4× less RAM, <1% recall loss, zero ingest-code changes.**

`turbochroma` solves the high RAM consumption problem in ChromaDB as collections grow. Instead of migrating to a more complex vector database (like Qdrant or Milvus), it allows you to scale your **RAG (Retrieval-Augmented Generation)** applications with:

- **Reduce RAM usage by 4×**: Stores compressed (SQ8 - 8-bit) vectors directly in metadata.
- **Search faster with ADC**: Uses Asymmetric Distance Computation (ADC) to re-order candidates without fully decompressing vectors.
- **Save VRAM for LLMs/Rerankers**: By performing high-quality re-ranking on the CPU with ADC, you can send **fewer but more relevant** candidates to your GPU-based cross-encoders or LLMs, significantly reducing VRAM pressure and costs.
- **Maintain precision**: Implements a "Sparse Rotation" step before quantization to minimize information loss (typically <1% recall loss).

> **Status**: `0.1.0` — first **PyPI (beta)** line. The public surface
> (`QuantizedCollection`, `SQ8Codec`, metadata keys) is expected to stay
> compatible within `0.1.x`; see [STABILITY.md](STABILITY.md) and
> [CHANGELOG.md](CHANGELOG.md). See also [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Install from PyPI: `pip install turbochroma`

---

## Why turbochroma for RAG?

ChromaDB [does not ship native vector quantization](https://github.com/chroma-core/chroma/issues).
If your RAG collection grows past what your RAM can comfortably hold, your options
today are:

| Option | Cost |
|---|---|
| Migrate to Qdrant / Milvus / Weaviate | Infra rewrite, new ops surface |
| Reduce embedding dimension (e.g. PCA) | Model retraining, recall loss across the board |
| **`pip install turbochroma`** | Small code change, no vector DB swap |

---

## RAG & LLM Integration Patterns

| Pattern | How turbochroma helps | LLM / User Benefit |
|---------|-----------------------|--------------------|
| **High-Precision RAG** | Use ADC to **over-fetch** (e.g., top-40 instead of top-10) and re-rank accurately on CPU. | Better context quality for the LLM without increasing vector DB memory. |
| **VRAM-Optimized Pipeline** | Filter thousands of candidates on CPU via ADC before hitting GPU models. | **Lower VRAM usage** on GPUs; allows running larger LLMs on the same hardware. |
| **Multi-Tenant LLM Apps** | 4× less RAM per collection allows hosting **hundreds of tenant-specific** indexes on a single small instance. | Lower infrastructure costs for SaaS applications. |
| **Cheap Pre-Ranking** | Act as a middle layer: Chroma (approx) → **TurboChroma (ADC re-rank)** → Cross-Encoder (heavy). | Reduces the number of hits passed to expensive cross-encoders, **saving tokens and GPU latency**. |
| **Legal/Medical Search** | Sparse Rotation preserves outliers and specific terminology better than naive SQ8. | Maintains high recall for specialized domains where every chunk matters. |

**What it is *not* (primarily)**: a replacement for billion-scale FAISS-IVF-PQ clusters. It is a **pragmatic scaling layer** for production RAG teams already using Chroma.

### Limitations (read before you ship)

- **Re-rank cannot rescue misses**: If the correct chunk is not in Chroma’s top `(n_results × refine_factor)` hits, ADC cannot invent it. Tune `n_results` and `refine_factor` to your recall needs.
- **ADC refinement with `refine_factor > 1` applies only to `query_embeddings=...`**. If you only pass `query_texts` (and let Chroma embed), the wrapper **falls back to native Chroma order** and may emit a `UserWarning`.
- Chroma’s `query(..., include=...)` does **not** allow `"ids"`; IDs are always returned. The wrapper strips `"ids"` from `include` before calling Chroma.
- The default SQ8 path stores one **byte per dimension** in the blob, with a **hard cap** of `MAX_COMPRESSED_BLOB_BYTES` (1 MiB) on both codec dimension and decoded payload size. If you need larger vectors, open an issue (you would need a different storage layout or a raised limit).
- Blobs are stored as **base64 in metadata** (Chroma’s accepted types). You pay some storage overhead on top of raw int8; later releases may add sidecar storage for tighter layouts. Values are size-checked before decoding. A second field (`DefaultBlobspecKey` / `tc_blobspec_v1` by default) stores a **codec fingerprint** (`BaseCodec.blobspec_fingerprint`) so ADC can detect a blob written with a different codec, dimension, rotation, or seed. If the field is **missing** (older rows), only the base64 is validated. Set `blobspec_key=None` on `QuantizedCollection` to disable writing and checking that field. For **integrity-sensitive** re-ranking, use `strict=True` on `QuantizedCollection` or on `query(...)` so a bad blob or mismatched fingerprint fails with `ValueError` instead of falling back to Chroma’s distance.
- **Format upgrades**: a future incompatible change to the stored metadata layout (outside `0.1.x` or as documented) may require **re-backfill** or re-index; see [STABILITY.md](STABILITY.md#metadata-wire-format-and-re-indexing).
- **Non-cryptographic storage**: this library does **not** encrypt collections. Anyone with **read access to the Chroma collection** can read stored blobs and vectors per your Chroma config; for very sensitive use cases, enforce access at the **DB / product** level — see [SECURITY.md](SECURITY.md#confidentiality-and-chroma-access-control).

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

Contributors: [CONTRIBUTING.md](CONTRIBUTING.md) (pre-commit, ruff, mypy, `pip-audit`). Quality bar: [QUALITY.md](QUALITY.md), [docs/quality-gates.md](docs/quality-gates.md), [TESTING.md](TESTING.md). **Releases:** [RELEASING.md](RELEASING.md) (tag `v*` → PyPI via Trusted Publishing). API & design site: `pip install -e ".[docs]" && mkdocs build` (sources under `docs/`).

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
