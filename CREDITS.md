# Credits and lineage

`turbochroma` was originally incubated inside **Minervia**, a Spanish-language
legal-RAG system built by Angel Israel Moreno Castellanos. In that context
it lived as an internal module (`rag-service/utils/quantizer.py`, codename
*TurboQuant*) that paired BGE-M3 dense retrieval with an asymmetric SQ8
re-ranking layer to keep RAM pressure under control.

This repository is a **clean-room repackaging** of that module as a reusable
library for the broader ChromaDB community. No proprietary Minervia code
(domain logic, legal heuristics, BGE-M3 wiring, tenant/expediente concerns)
ships here — only the vector-compression primitives, refactored against a
stable public API.

## Intellectual lineage

- **TurboQuant → turbochroma**: the core idea of storing compressed int8
  blobs next to float32 vectors in ChromaDB and re-ranking with asymmetric
  distance computation (ADC) was prototyped in Minervia between March and
  April 2026.
- The specific choices of sparse rotation (sign-flip + permutation) and
  scalar quantization (SQ8) trace back to that prototype.

## Prior art acknowledged

- **Scalar Quantization (SQ8)**: standard technique in FAISS, ScaNN, Milvus,
  Qdrant, USearch, and others. `turbochroma` is *not* a novel quantization
  algorithm; it is a productized integration for a vector DB that lacks
  native quantization support.
- **Asymmetric Distance Computation (ADC)**: introduced by Jégou et al.
  (2011) in the Product Quantization paper; the pattern is widely used.
- **OPQ, RaBitQ, PQ**: related families of vector compression algorithms
  that may appear as additional codecs in future versions.
