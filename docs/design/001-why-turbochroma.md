# ADR 001 — Why turbochroma exists

**Status**: accepted
**Date**: 2026-04-23
**Author**: Angel Israel Moreno Castellanos

## Context

ChromaDB is one of the most popular open-source vector databases in the
Python ecosystem. It wins on developer experience: a few lines of code and
you have a working retrieval system. That success comes with a cost that
starts biting at scale: ChromaDB **does not ship native vector
quantization**. Every vector is stored as float32.

For a typical RAG workload using BGE-M3 (1024d), that is 4 KB per chunk.
500k chunks = 2 GB just for the vectors, before metadata, indexes, or
anything else. At 5M chunks we are already past what a single-box RAM
budget tolerates in production.

## Alternatives considered

1. **Migrate to Qdrant / Milvus / Weaviate / FAISS-backed systems.**
   These have native quantization. Problem: non-trivial infrastructure
   rewrite, new ops surface, and loss of Chroma's ergonomics.
2. **Reduce embedding dimension.** Retrain with a smaller model or add
   PCA. Degrades recall globally and ties you to a specific model choice.
3. **Build compression directly on top of Chroma.** This is what
   `turbochroma` does.

## Decision

We build `turbochroma` as a **thin, composable wrapper** around a
`chromadb.Collection` that:

- Stores int8-quantized blobs alongside (or instead of) the float32
  vectors.
- Performs **asymmetric distance computation (ADC)** at query time: the
  query stays in float32, documents decompress on the fly, and we
  re-rank Chroma's top-K results with the exact ADC score.
- Exposes a drop-in API: `qcoll.query()` mirrors `coll.query()` so
  existing Chroma code can migrate in minutes.

## Consequences

**Positive**

- ~4× RAM reduction for SQ8; ~16× for future PQ; ~32× for future RaBitQ.
- No new infrastructure: still ChromaDB under the hood.
- Opt-in at the collection level: a user can quantize only the huge
  collection while leaving small ones untouched.

**Negative / accepted trade-offs**

- Small, measurable recall loss vs full float32 (target: <1% at k=10).
- Extra storage for the blob sidecar (+33% for base64-in-metadata,
  ~1.01× for parquet sidecar).
- We rely on Chroma's own top-K retrieval as the first stage; if Chroma
  misses a relevant chunk in its top-K, ADC cannot recover it. (This is
  true of any refinement scheme; the `refine_factor` knob mitigates it.)

## Related ADRs

- ADR 002 — Codec interface (planned)
- ADR 003 — Storage backend trade-offs (planned)
- ADR 004 — API stability policy for v0.x (planned)
