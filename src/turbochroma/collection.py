"""ChromaDB collection wrapper: adds SQ8 blob storage and ADC re-ranking."""

from __future__ import annotations

import base64
import warnings
from typing import Any, TypeAlias, cast

import numpy as np
from chromadb import Collection
from chromadb.api.types import (
    ID,
    URI,
    Document,
    Embedding,
    Image,
    Include,
    Metadatas,
    PyEmbedding,
    QueryResult,
    Where,
    WhereDocument,
)

from turbochroma.blob_utils import decode_stored_blob
from turbochroma.codecs.base import BaseCodec

_Emb: TypeAlias = list[Embedding] | list[PyEmbedding] | list[list[float]] | np.ndarray

DefaultBlobKey = "tc_sq8_v1"
DefaultBlobspecKey = "tc_blobspec_v1"

_DEFAULT_INCLUDE: Include = ["metadatas", "documents", "distances"]


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _as_2d_float32(vectors: _Emb) -> np.ndarray:
    arr = np.asarray(vectors, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2:
        msg = f"embeddings must be 1D or 2D, got shape {arr.shape!r}"
        raise ValueError(msg)
    return arr


class QuantizedCollection:
    """Wraps a :class:`chromadb.Collection` with codec-compressed sidecar blobs.

    On :meth:`add` / :meth:`upsert`, each row's embedding is compressed with
    the given :class:`BaseCodec` and the result is base64-embedded in the
    record's metadata under :attr:`blob_key`.

    On :meth:`query` with ``refine_factor > 1`` and ``query_embeddings=``,
    Chroma fetches ``n_results * refine_factor`` candidates, then the pool
    is re-ordered by asymmetric dot (ADC) between the query and each stored
    blob.  Text / image / URI queries cannot access the raw float query
    vector, so they always use Chroma's native ordering (a warning is issued
    if ``refine_factor > 1``).

    Other :class:`chromadb.Collection` methods (``get``, ``peek``,
    ``count``, ``delete``, …) are delegated via :func:`getattr` — call them
    on this wrapper the same way you would on the inner collection, except
    for :meth:`add`, :meth:`upsert`, and :meth:`query` which are overridden.

    Args:
        collection: Chroma collection instance.
        codec: Codec used to produce blobs (e.g. :class:`SQ8Codec`).
        blob_key: Metadata field name for the base64 blob.
        refine_factor: When ``> 1`` and using ``query_embeddings``, Chroma
            over-fetches for ADC re-ranking.
        strict: If True, invalid stored blobs (wrong length, bad base64)
            during ADC re-ranking raise :exc:`ValueError` instead of
            falling back to Chroma's distance. Default False (tolerant;
            use for debugging or high-trust data only).
        blobspec_key: If not ``None``, store :meth:`BaseCodec.blobspec_fingerprint`
            under this metadata key and verify it on ADC. Use ``None`` to
            disable (legacy). Default :data:`DefaultBlobspecKey`.
    """

    def __init__(
        self,
        collection: Collection,
        codec: BaseCodec,
        *,
        blob_key: str = DefaultBlobKey,
        refine_factor: int = 4,
        strict: bool = False,
        blobspec_key: str | None = DefaultBlobspecKey,
    ) -> None:
        if not blob_key or not str(blob_key).strip():
            msg = "blob_key must be a non-empty string"
            raise ValueError(msg)
        if blobspec_key is not None and (not str(blobspec_key).strip()):
            msg = "blobspec_key must be None or a non-empty string"
            raise ValueError(msg)
        self._coll = collection
        self._codec = codec
        self._blob_key = str(blob_key)
        self._refine_factor = max(1, int(refine_factor))
        self._strict = bool(strict)
        self._blobspec_key = str(blobspec_key).strip() if blobspec_key is not None else None
        self._expected_blobspec = self._codec.blobspec_fingerprint()

    @property
    def collection(self) -> Collection:
        return self._coll

    @property
    def codec(self) -> BaseCodec:
        return self._codec

    @property
    def blob_key(self) -> str:
        return self._blob_key

    @property
    def refine_factor(self) -> int:
        return self._refine_factor

    @property
    def strict(self) -> bool:
        """If True, invalid metadata blobs during ADC fail fast."""
        return self._strict

    @property
    def blobspec_key(self) -> str | None:
        """Metadata key for :meth:`~turbochroma.codecs.base.BaseCodec.blobspec_fingerprint`, or None."""
        return self._blobspec_key

    def _validate_embedding_matrix(self, emb: np.ndarray) -> None:
        if emb.shape[1] != self._codec.dimension:
            msg = (
                f"embedding dim {emb.shape[1]} does not match codec "
                f"dimension {self._codec.dimension}"
            )
            raise ValueError(msg)

    def _merge_blobs(
        self,
        ids: list[str],
        emb: np.ndarray,
        metadatas: list[dict[str, Any] | None] | Metadatas | None,
    ) -> list[dict[str, Any]]:
        self._validate_embedding_matrix(emb)
        if emb.shape[0] != len(ids):
            msg = f"len(ids)={len(ids)} but embedding matrix has {emb.shape[0]} rows"
            raise ValueError(msg)
        blobs = self._codec.compress_batch(emb)
        mlist: list[dict[str, Any] | None] = list(cast(Any, metadatas)) if metadatas is not None else [None] * len(ids)
        out: list[dict[str, Any]] = []
        for i, _ in enumerate(ids):
            row: dict[str, Any] = {**(mlist[i] or {}), self._blob_key: _b64(blobs[i])}
            if self._blobspec_key is not None:
                row[self._blobspec_key] = self._expected_blobspec
            out.append(row)
        return out

    def add(
        self,
        ids: str | list[ID],
        embeddings: _Emb | list[Embedding] | list[PyEmbedding] | None = None,
        metadatas: list[dict[str, Any] | None] | None = None,
        documents: str | list[Document] | None = None,
        images: str | list[Image] | None = None,
        uris: str | list[URI] | None = None,
    ) -> None:
        if embeddings is None:
            self._coll.add(
                ids=cast(Any, ids),
                embeddings=None,
                metadatas=cast(Any, metadatas),
                documents=documents,
                images=cast(Any, images),
                uris=uris,
            )
            return
        id_list = [str(x) for x in (ids if isinstance(ids, list) else [ids])]
        emb2 = _as_2d_float32(embeddings)
        merged = self._merge_blobs(id_list, emb2, metadatas)
        self._coll.add(
            ids=cast(Any, ids),
            embeddings=cast(Any, emb2),
            metadatas=cast(Any, merged),
            documents=documents,
            images=cast(Any, images),
            uris=uris,
        )

    def upsert(
        self,
        ids: str | list[ID],
        embeddings: _Emb | list[Embedding] | list[PyEmbedding] | None = None,
        metadatas: list[dict[str, Any] | None] | None = None,
        documents: str | list[Document] | None = None,
        images: str | list[Image] | None = None,
        uris: str | list[URI] | None = None,
    ) -> None:
        if embeddings is None:
            self._coll.upsert(
                ids=cast(Any, ids),
                embeddings=None,
                metadatas=cast(Any, metadatas),
                documents=documents,
                images=cast(Any, images),
                uris=uris,
            )
            return
        id_list = [str(x) for x in (ids if isinstance(ids, list) else [ids])]
        emb2 = _as_2d_float32(embeddings)
        merged = self._merge_blobs(id_list, emb2, metadatas)
        self._coll.upsert(
            ids=cast(Any, ids),
            embeddings=cast(Any, emb2),
            metadatas=cast(Any, merged),
            documents=documents,
            images=cast(Any, images),
            uris=uris,
        )

    @staticmethod
    def _order_by_indices(order: list[int], row: list[Any] | None) -> list[Any] | None:
        if row is None:
            return None
        return [row[i] for i in order]

    def _refine_one_query(
        self,
        query_vec: np.ndarray,
        qi: int,
        raw: QueryResult,
        n_out: int,
        *,
        strict: bool,
    ) -> dict[str, list[Any] | None]:
        """Re-order a single row of a ``QueryResult`` to contain ``n_out`` hits."""
        row_ids: list[str] = list(raw.get("ids", [[]])[qi] or [])
        if not row_ids:
            out_empty: dict[str, list[Any] | None] = {"ids": []}
            for k in ("embeddings", "distances", "metadatas", "documents", "uris"):
                col = cast(Any, raw.get(k))
                if col is not None and qi < len(col):
                    out_empty[k] = []
            return out_empty

        dists: list[Any] | None = cast(Any, (raw.get("distances") or [None] * len(raw["ids"])))[qi]
        mets: list[dict[str, Any] | None] | None = (
            cast(Any, (raw.get("metadatas") or [None] * len(raw["ids"])))[qi]
            if raw.get("metadatas")
            else None
        )
        embs: list[Any] | None = (
            cast(Any, (raw.get("embeddings") or [None] * len(raw["ids"])))[qi]
            if raw.get("embeddings")
            else None
        )
        docs: list[Any] | None = (
            cast(Any, (raw.get("documents") or [None] * len(raw["ids"])))[qi]
            if raw.get("documents")
            else None
        )
        uris: list[Any] | None = (
            cast(Any, (raw.get("uris") or [None] * len(raw["ids"])))[qi]
            if raw.get("uris")
            else None
        )

        scores: list[tuple[int, float]] = []
        for j in range(len(row_ids)):
            mrow = mets[j] if mets and j < len(mets) else None
            b64 = mrow.get(self._blob_key) if mrow else None
            if b64 and isinstance(b64, str):
                try:
                    if self._blobspec_key is not None and mrow:
                        stored = mrow.get(self._blobspec_key)
                        if stored is not None and str(stored) != self._expected_blobspec:
                            msg = (
                                f"blobspec mismatch for id {row_ids[j]!r}: "
                                f"metadata has {stored!r}, expected {self._expected_blobspec!r}"
                            )
                            raise ValueError(msg)
                    rawb = decode_stored_blob(b64, self._codec.compressed_size_bytes)
                    s = self._codec.asymmetric_dot(query_vec, rawb)
                except (ValueError, OSError, TypeError) as e:
                    if strict:
                        eid = row_ids[j]
                        msg = f"ADC metadata error for id {eid!r}: {e}"
                        raise ValueError(msg) from e
                    if dists is not None and j < len(dists) and dists[j] is not None:
                        s = -float(dists[j])
                    else:
                        s = -j * 1e-9
            elif dists is not None and j < len(dists) and dists[j] is not None:
                s = -float(dists[j])
            else:
                s = -j * 1e-9
            scores.append((j, s))
        scores.sort(key=lambda t: -t[1])
        n_take = min(n_out, len(scores))
        top = [t[0] for t in scores[:n_take]]

        out: dict[str, list[Any] | None] = {
            "ids": [row_ids[i] for i in top],
        }
        if dists is not None:
            re_d = self._order_by_indices(top, list(dists))
            out["distances"] = re_d
        if mets is not None:
            re_m = self._order_by_indices(top, list(mets))
            out["metadatas"] = re_m
        if embs is not None:
            re_e = self._order_by_indices(top, list(embs))
            out["embeddings"] = re_e
        if docs is not None:
            re_doc = self._order_by_indices(top, list(docs))
            out["documents"] = re_doc
        if uris is not None:
            re_u = self._order_by_indices(top, list(uris))
            out["uris"] = re_u
        return out

    def query(
        self,
        query_embeddings: list[Embedding] | list[PyEmbedding] | _Emb | None = None,
        query_texts: str | list[Document] | None = None,
        query_images: str | list[Image] | None = None,
        query_uris: str | list[URI] | None = None,
        ids: str | list[ID] | None = None,
        n_results: int = 10,
        where: Where | None = None,
        where_document: WhereDocument | None = None,
        include: Include | None = None,
        *,
        refine_factor: int | None = None,
        strict: bool | None = None,
    ) -> QueryResult:
        use_strict = self._strict if strict is None else bool(strict)
        rf = self._refine_factor if refine_factor is None else int(refine_factor)
        rf = max(1, rf)

        if rf <= 1:
            include_pass = list(include) if include is not None else None
            if include_pass:
                include_pass = [k for k in include_pass if cast(Any, k) != "ids"]
            return self._coll.query(
                query_embeddings=cast(Any, query_embeddings),
                query_texts=query_texts,
                query_images=cast(Any, query_images),
                query_uris=query_uris,
                ids=ids,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=cast(Any, include_pass),
            )

        if query_embeddings is None:
            if query_texts is not None or query_images is not None or query_uris is not None:
                warnings.warn(
                    "refine_factor>1 only applies to query_embeddings; "
                    "using native Chroma ordering.",
                    UserWarning,
                    stacklevel=2,
                )
            include_pass2 = list(include) if include is not None else None
            if include_pass2:
                include_pass2 = [k for k in include_pass2 if cast(Any, k) != "ids"]
            return self._coll.query(
                query_embeddings=cast(Any, query_embeddings),
                query_texts=query_texts,
                query_images=cast(Any, query_images),
                query_uris=query_uris,
                ids=ids,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=cast(Any, include_pass2),
            )

        want: set[str] = set(include) if include is not None else set(_DEFAULT_INCLUDE)
        # Chroma "query" include does not accept "ids" (ids are always returned).
        want = {k for k in want if k != "ids"}
        n_fetch = n_results * rf
        internal: Include = cast(Any, list((want - {"ids"}) | {"metadatas", "distances"}))

        raw: QueryResult = self._coll.query(
            query_embeddings=cast(Any, query_embeddings),
            query_texts=query_texts,
            query_images=cast(Any, query_images),
            query_uris=query_uris,
            ids=ids,
            n_results=n_fetch,
            where=where,
            where_document=where_document,
            include=cast(Any, internal),
        )
        qe = _as_2d_float32(query_embeddings)
        nq = int(qe.shape[0])
        if not raw.get("ids") or len(raw["ids"]) != nq:
            msg = "Chroma query batch size mismatch with query_embeddings"
            raise RuntimeError(msg)

        rows: list[dict[str, list[Any] | None]] = [
            self._refine_one_query(qe[qi], qi, raw, n_results, strict=use_strict)
            for qi in range(nq)
        ]

        out: dict[str, list[Any] | list[list[Any]]] = {
            "ids": [r["ids"] or [] for r in rows],
        }
        for key in ("embeddings", "distances", "metadatas", "documents", "uris"):
            if key not in want or not rows:
                continue
            if key in rows[0]:
                out[key] = [cast(Any, r[key]) for r in rows]
        return cast(QueryResult, out)

    def fit_existing(self, batch_size: int = 256) -> int:
        """Backfill :attr:`blob_key` for rows that have stored embeddings.

        Returns the number of rows updated.
        """
        n_done = 0
        offset = 0
        while True:
            res = self._coll.get(
                include=["embeddings", "metadatas"],
                limit=batch_size,
                offset=offset,
            )
            got_ids: list[str] = list(res.get("ids") or [])
            if not got_ids:
                break
            embs = res.get("embeddings")
            if embs is None:
                break
            mlist: list[Any] = cast(list[Any], res.get("metadatas")) or [None] * len(got_ids)
            arr = np.asarray(embs, dtype=np.float32)
            if arr.ndim != 2 or arr.shape[0] != len(got_ids):
                msg = "unexpected layout from Chroma 'get' with embeddings"
                raise RuntimeError(msg)
            self._validate_embedding_matrix(arr)
            blobs = self._codec.compress_batch(arr)
            new_meta = []
            for i in range(len(got_ids)):
                row: dict[str, Any] = {**(mlist[i] or {}), self._blob_key: _b64(blobs[i])}
                if self._blobspec_key is not None:
                    row[self._blobspec_key] = self._expected_blobspec
                new_meta.append(row)
            self._coll.update(ids=got_ids, metadatas=cast(Any, new_meta))
            n_done += len(got_ids)
            if len(got_ids) < batch_size:
                break
            offset += len(got_ids)
        return n_done

    def __getattr__(self, name: str) -> Any:
        return getattr(self._coll, name)

    def __repr__(self) -> str:
        return f"QuantizedCollection({self._coll!r}, codec={self._codec!r})"
