"""Integration tests: QuantizedCollection + in-memory Chroma."""

from __future__ import annotations

import base64
import uuid

import chromadb
import numpy as np
import pytest
from chromadb import Collection
from chromadb.config import Settings

from turbochroma import DefaultBlobKey, DefaultBlobspecKey, QuantizedCollection, SQ8Codec

_DIM = 4


def _name() -> str:
    return f"tcoll_{uuid.uuid4().hex[:10]}"


def _l2n_rows(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32)
    n = np.linalg.norm(a, axis=1, keepdims=True)
    n = np.where(n == 0, 1.0, n)
    return a / n


def _client() -> chromadb.Client:
    return chromadb.Client(Settings(anonymized_telemetry=False))


@pytest.fixture
def coll() -> Collection:
    c = _client()
    return c.create_collection(_name(), metadata={"hnsw:space": "l2"})


@pytest.fixture
def codec() -> SQ8Codec:
    return SQ8Codec(dimension=_DIM, seed=42)


@pytest.fixture
def qcoll(coll: Collection, codec: SQ8Codec) -> QuantizedCollection:
    return QuantizedCollection(coll, codec, refine_factor=4)


def test_add_injects_metadata_blob(qcoll: QuantizedCollection, coll: Collection, codec: SQ8Codec) -> None:
    emb = _l2n_rows(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
            ]
        )
    )
    qcoll.add(
        ids=["a", "b"],
        embeddings=emb.tolist(),
        metadatas=[{"i": 0}, {"i": 1}],
    )
    g = coll.get(include=["metadatas", "embeddings"])
    assert g["metadatas"] is not None
    m0, m1 = g["metadatas"]
    assert m0 and DefaultBlobKey in m0
    assert m1 and DefaultBlobKey in m1
    b0 = m0[DefaultBlobKey] if m0 is not None else None
    assert b0 and isinstance(b0, str)
    raw = base64.b64decode(b0)
    assert len(raw) == codec.compressed_size_bytes
    assert m0[DefaultBlobspecKey] == codec.blobspec_fingerprint()
    assert m1[DefaultBlobspecKey] == codec.blobspec_fingerprint()


def test_fit_existing_backfills_blobs() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    emb = _l2n_rows(
        np.array(
            [
                [0.0, 0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
            ]
        )
    )
    col.add(
        ids=["x0", "x1"],
        embeddings=emb.tolist(),
    )
    codec = SQ8Codec(dimension=_DIM, seed=99)
    qc = QuantizedCollection(col, codec, refine_factor=1)
    n = qc.fit_existing(batch_size=10)
    assert n == 2
    g = col.get(include=["metadatas"], ids=["x0"])
    m0 = g["metadatas"] and g["metadatas"][0]
    assert m0 and DefaultBlobKey in m0
    assert m0[DefaultBlobspecKey] == codec.blobspec_fingerprint()


def test_query_refine_passthrough_when_rf_is_one() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=1)
    qc2 = QuantizedCollection(col, codec, refine_factor=1)
    emb2 = _l2n_rows(np.eye(_DIM, dtype=np.float32))
    qc2.add(ids=[f"r{i}" for i in range(4)], embeddings=emb2.tolist())
    qv = _l2n_rows(emb2[0:1])
    a = col.query(
        query_embeddings=qv.tolist(), n_results=2, include=["distances", "metadatas"]
    )
    b = qc2.query(
        query_embeddings=qv.tolist(),
        n_results=2,
        include=["distances", "metadatas"],
        refine_factor=1,
    )
    assert a["ids"] == b["ids"]


def test_query_with_refine_returns_expected_length() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=42)
    qc2 = QuantizedCollection(col, codec, refine_factor=4)
    emb = _l2n_rows(np.eye(_DIM, dtype=np.float32))
    qc2.add(ids=[f"r{i}" for i in range(4)], embeddings=emb.tolist())
    qv = _l2n_rows(emb[0:1])
    r = qc2.query(
        query_embeddings=qv.tolist(),
        n_results=2,
        include=["distances", "metadatas"],
    )
    assert r["ids"] and len(r["ids"][0]) == 2
    assert r["metadatas"] and len(r["metadatas"][0]) == 2


def test_delegation_count() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=0)
    qc2 = QuantizedCollection(col, codec, refine_factor=1)
    emb = _l2n_rows(np.eye(_DIM, dtype=np.float32))
    qc2.add(ids=[f"r{i}" for i in range(2)], embeddings=emb[:2].tolist())
    assert qc2.count() == 2


def test_blobspec_key_none_skips_spec_field() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=1)
    qc = QuantizedCollection(col, codec, refine_factor=1, blobspec_key=None)
    emb = _l2n_rows(np.eye(_DIM, dtype=np.float32))
    qc.add(ids=["a"], embeddings=emb.tolist())
    g = col.get(include=["metadatas"], ids=["a"])
    m = g["metadatas"] and g["metadatas"][0]
    assert m and DefaultBlobKey in m
    assert DefaultBlobspecKey not in m


def test_empty_blobspec_key_raises() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=0)
    with pytest.raises(ValueError, match="blobspec_key"):
        QuantizedCollection(col, codec, blobspec_key="  ")


def test_mismatched_dim_raises() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=0)
    qc2 = QuantizedCollection(col, codec, refine_factor=1)
    bad = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
    with pytest.raises(ValueError, match="does not match"):
        qc2.add(ids=["a"], embeddings=bad.tolist())


def test_query_refine_strict_raises_on_tampered_blob() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=42)
    qc = QuantizedCollection(col, codec, refine_factor=4, strict=True)
    emb = _l2n_rows(np.eye(_DIM, dtype=np.float32))
    qc.add(ids=[f"r{i}" for i in range(4)], embeddings=emb.tolist())
    # Valid base64 that decodes to 3 bytes; codec expects 4.
    col.update(ids=["r0"], metadatas=[{DefaultBlobKey: "AAAA"}])
    qv = _l2n_rows(emb[0:1])
    with pytest.raises(ValueError, match="ADC metadata error"):
        qc.query(
            query_embeddings=qv.tolist(),
            n_results=2,
            include=["distances", "metadatas"],
        )


def test_query_refine_strict_raises_on_blobspec_mismatch() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=42)
    qc = QuantizedCollection(col, codec, refine_factor=4, strict=True)
    emb = _l2n_rows(np.eye(_DIM, dtype=np.float32))
    qc.add(ids=[f"r{i}" for i in range(4)], embeddings=emb.tolist())
    got = col.get(ids=["r0"], include=["metadatas"])
    assert got["metadatas"] and got["metadatas"][0]
    m0 = dict(got["metadatas"][0] or {})
    m0[DefaultBlobspecKey] = "1|d=4|cv=fake|b=0|rv=sparse-v1|s=0"
    col.update(ids=["r0"], metadatas=[m0])
    qv = _l2n_rows(emb[0:1])
    with pytest.raises(ValueError, match="ADC metadata error"):
        qc.query(
            query_embeddings=qv.tolist(),
            n_results=2,
            include=["distances", "metadatas"],
        )


def test_query_refine_tolerant_when_blob_tampered() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=42)
    qc = QuantizedCollection(col, codec, refine_factor=4, strict=False)
    emb = _l2n_rows(np.eye(_DIM, dtype=np.float32))
    qc.add(ids=[f"r{i}" for i in range(4)], embeddings=emb.tolist())
    col.update(ids=["r0"], metadatas=[{DefaultBlobKey: "AAAA"}])
    qv = _l2n_rows(emb[0:1])
    r = qc.query(
        query_embeddings=qv.tolist(),
        n_results=2,
        include=["distances", "metadatas"],
    )
    assert r["ids"] and len(r["ids"][0]) == 2
