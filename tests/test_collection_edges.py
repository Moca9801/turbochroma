"""Extra integration tests for collection branches (warnings, includes, errors)."""

from __future__ import annotations

import uuid
from unittest import mock

import chromadb
import numpy as np
import pytest
from chromadb import Collection
from chromadb.config import Settings

from turbochroma import QuantizedCollection, SQ8Codec

_DIM = 4


def _name() -> str:
    return f"te_{uuid.uuid4().hex[:10]}"


def _client() -> chromadb.Client:
    return chromadb.Client(Settings(anonymized_telemetry=False))


def _l2n(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32)
    n = np.linalg.norm(a, axis=1, keepdims=True)
    n = np.where(n == 0, 1.0, n)
    return a / n


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


def test_order_by_indices_none() -> None:
    assert QuantizedCollection._order_by_indices([0, 1], None) is None


def test_add_rejects_3d_embedding_matrix(qcoll: QuantizedCollection) -> None:
    bad = np.zeros((1, 1, _DIM), dtype=np.float32)
    with pytest.raises(ValueError, match="1D or 2D"):
        qcoll.add(ids=["a"], embeddings=bad.tolist())


def test_query_embedding_batch_mismatch_raises_runtime() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=1)
    qc = QuantizedCollection(col, codec, refine_factor=2)
    emb = _l2n(np.eye(_DIM, dtype=np.float32))
    qc.add(ids=[f"r{i}" for i in range(3)], embeddings=emb.tolist())
    qv2 = _l2n(emb[:2])
    bad: dict[str, list] = {
        "ids": [["a"]],
        "metadatas": [[{"x": 1}]],
        "distances": [[0.1]],
    }
    with (
        mock.patch.object(qc._coll, "query", return_value=bad),
        pytest.raises(RuntimeError, match="batch size mismatch"),
    ):
            qc.query(
                query_embeddings=qv2.tolist(),
                n_results=1,
                include=["metadatas"],
            )


def test_quantized_collection_repr() -> None:
    c = _client()
    col = c.create_collection(_name(), metadata={"hnsw:space": "l2"})
    codec = SQ8Codec(dimension=_DIM, seed=0)
    qc = QuantizedCollection(col, codec, refine_factor=1)
    s = repr(qc)
    assert "QuantizedCollection" in s
    assert "codec=" in s


def test_query_refine_includes_extra_fields(qcoll: QuantizedCollection) -> None:
    emb = _l2n(
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
        metadatas=[{"t": "1"}, {"t": "2"}],
        documents=["d1", "d2"],
    )
    qv = _l2n(emb[0:1])
    r = qcoll.query(
        query_embeddings=qv.tolist(),
        n_results=2,
        include=["distances", "metadatas", "documents"],
        refine_factor=2,
    )
    assert r.get("metadatas") and r.get("documents")
    assert len(r["ids"][0]) == 2
