# turbochroma

> Drop-in compression for ChromaDB: **4× less RAM, <1% recall loss, zero ingest-code changes.**

`turbochroma` wraps a ChromaDB collection, stores quantized int8 blobs next
to the original float32 vectors, and performs **asymmetric distance
computation (ADC)** at query time. You get most of the memory and latency
benefits of dedicated ANN systems like FAISS or Qdrant without leaving
Chroma.

> **Status**: pre-alpha (`0.1.0.dev0`). Private repo, API unstable. Do not
> pin to this for production until `0.1.0` lands.

---

## Why turbochroma

ChromaDB [does not ship native vector quantization](https://github.com/chroma-core/chroma/issues).
If your collection grows past what your RAM can comfortably hold, your options
today are:

| Option | Cost |
|---|---|
| Migrate to Qdrant / Milvus / Weaviate | Infra rewrite, new ops surface |
| Reduce embedding dimension (e.g. PCA, smaller model) | Model retraining, recall loss across the board |
| **`pip install turbochroma`** | ~10 lines of code, no infra change |

---

## Installation

```bash
pip install turbochroma
```

Optional extras:

- `turbochroma[fast]` — numba kernels for faster ADC
- `turbochroma[parquet]` — sidecar parquet storage backend
- `turbochroma[bench]` — datasets + matplotlib for reproducing benchmarks

---

## 30-second quickstart

*(API not implemented yet in this commit; see the roadmap below.)*

```python
import chromadb
from turbochroma import QuantizedCollection, SQ8Codec

client = chromadb.PersistentClient(path="./chroma")
coll = client.get_or_create_collection("docs")

qcoll = QuantizedCollection(coll, codec=SQ8Codec())
qcoll.fit_existing()   # idempotent; compresses existing vectors

results = qcoll.query(
    query_embeddings=[query_vec],
    n_results=10,
    refine_factor=4,   # 2-stage: Chroma top-40 → ADC re-rank to top-10
)
```

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

More detail in [`docs/design/002-codec-interface.md`](docs/design/).

---

## Benchmarks

*Reproducible via `python benchmarks/beir_nfcorpus.py`. Results table will
be filled in once benchmarks land (v0.1.0).*

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
