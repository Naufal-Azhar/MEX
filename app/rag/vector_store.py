"""Vector stores: Qdrant (dense embeddings) and a local TF-IDF index fallback."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.document_processing.chunker import Chunk
from app.rag.embeddings import EmbeddingBackend, TfidfEmbeddingBackend


@dataclass
class SearchHit:
    chunk: Chunk
    score: float


class TfidfVectorStore:
    """Sparse TF-IDF index persisted inside the workspace with joblib."""

    kind = "tfidf"
    lexical = True

    def __init__(
        self,
        backend: TfidfEmbeddingBackend,
        chunks: list[Chunk],
        matrix: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.backend = backend
        self.chunks = chunks
        self.matrix = matrix
        self.metadata = metadata or {}

    @classmethod
    def build(cls, chunks: list[Chunk], backend: TfidfEmbeddingBackend) -> "TfidfVectorStore":
        texts = [chunk.text for chunk in chunks]
        backend.fit(texts)
        matrix = backend.embed_documents(texts)
        return cls(backend, chunks, matrix, {"count": len(chunks), "backend": backend.describe()})

    def search(
        self,
        query: str,
        top_k: int = 5,
        article: str | None = None,
        document_id: str | None = None,
        document_types: set[str] | None = None,
    ) -> list[SearchHit]:
        from sklearn.metrics.pairwise import linear_kernel

        query_vector = self.backend.embed_query(query)
        scores = np.asarray(linear_kernel(query_vector, self.matrix)[0], dtype=float)
        indices = [
            i
            for i, chunk in enumerate(self.chunks)
            if (article is None or chunk.article == article)
            and (document_id is None or chunk.document_id == document_id)
            and (document_types is None or chunk.document_type in document_types)
        ]
        ranked = sorted(indices, key=lambda i: scores[i], reverse=True)[:top_k]
        return [SearchHit(chunk=self.chunks[i], score=float(scores[i])) for i in ranked if scores[i] > 0]

    def save(self, path: Path) -> None:
        import joblib

        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "backend": self.backend,
                "chunks": [chunk.to_dict() for chunk in self.chunks],
                "matrix": self.matrix,
                "metadata": self.metadata,
            },
            path,
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        path.with_name(path.name + ".sha256").write_text(digest + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "TfidfVectorStore":
        import joblib

        checksum_path = path.with_name(path.name + ".sha256")
        if not checksum_path.exists():
            raise ValueError("TF-IDF index checksum is missing; rebuild the index.")
        expected = checksum_path.read_text(encoding="utf-8").strip()
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected != actual:
            raise ValueError("TF-IDF index checksum mismatch; rebuild the index.")
        payload = joblib.load(path)
        chunks = [Chunk(**item) for item in payload["chunks"]]
        return cls(payload["backend"], chunks, payload["matrix"], payload["metadata"])

    def describe(self) -> dict[str, Any]:
        return {**self.metadata, "kind": self.kind, "count": len(self.chunks)}


_BM25_TOKEN_RE = re.compile(
    r"[a-z]+\d+(?:[.\-]\d+)*|\d+(?:[.\-]\d+)*|[a-z]+(?:[-'][a-z]+)*",
    re.IGNORECASE,
)
_BM25_STOPWORDS = frozenset(
    "a an the is are was were be been being what how why in of to and or for with on at by "
    "from as it this that these those does do can could should would will i we you they "
    "there their than then if not no".split()
)


def _bm25_tokens(text: str) -> list[str]:
    return [
        token
        for token in _BM25_TOKEN_RE.findall(text.lower().replace("_", " "))
        if token not in _BM25_STOPWORDS
    ]


class BM25VectorStore:
    """Lexical BM25 index, kept in memory because the corpus is small."""

    kind = "bm25"
    lexical = True

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        if not chunks:
            raise ValueError("BM25 requires at least one chunk")
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.tokenized = [_bm25_tokens(chunk.text) for chunk in chunks]
        self.doc_len = np.asarray([max(len(tokens), 1) for tokens in self.tokenized], dtype=float)
        self.avgdl = float(self.doc_len.mean()) or 1.0
        self.term_freqs = [Counter(tokens) for tokens in self.tokenized]
        document_frequency: Counter[str] = Counter()
        for tokens in self.tokenized:
            document_frequency.update(set(tokens))
        total = len(self.chunks)
        self.idf = {
            term: math.log(1.0 + (total - freq + 0.5) / (freq + 0.5))
            for term, freq in document_frequency.items()
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        article: str | None = None,
        document_id: str | None = None,
        document_types: set[str] | None = None,
    ) -> list[SearchHit]:
        query_tokens = _bm25_tokens(query)
        if not query_tokens:
            return []
        indices = [
            i
            for i, chunk in enumerate(self.chunks)
            if (article is None or chunk.article == article)
            and (document_id is None or chunk.document_id == document_id)
            and (document_types is None or chunk.document_type in document_types)
        ]
        scored: list[tuple[float, int]] = []
        for index in indices:
            frequencies = self.term_freqs[index]
            doc_len = float(self.doc_len[index])
            score = 0.0
            for term in query_tokens:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                denominator = frequency + self.k1 * (1.0 - self.b + self.b * doc_len / self.avgdl)
                score += self.idf.get(term, 0.0) * frequency * (self.k1 + 1.0) / denominator
            if score > 0:
                scored.append((score, index))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            SearchHit(chunk=self.chunks[index], score=float(score))
            for score, index in scored[:top_k]
        ]

    def describe(self) -> dict[str, Any]:
        return {"kind": self.kind, "count": len(self.chunks), "k1": self.k1, "b": self.b}


class BM25TfidfFallbackStore:
    """BM25 primary store with a TF-IDF fallback when BM25 returns no hit."""

    kind = "bm25_tfidf"
    lexical = True

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.primary = BM25VectorStore(chunks)
        self.fallback_backend = TfidfEmbeddingBackend()
        self.fallback = TfidfVectorStore.build(chunks, self.fallback_backend)
        self.notes = [
            "BM25 primary: lexical retrieval with term saturation and length normalization.",
            "TF-IDF fallback: used only when BM25 returns no positive hit.",
        ]

    def search(
        self,
        query: str,
        top_k: int = 5,
        article: str | None = None,
        document_id: str | None = None,
        document_types: set[str] | None = None,
    ) -> list[SearchHit]:
        try:
            hits = self.primary.search(
                query,
                top_k=top_k,
                article=article,
                document_id=document_id,
                document_types=document_types,
            )
        except Exception:  # noqa: BLE001 - fallback must not take the API down
            hits = []
        if hits:
            return hits
        return self.fallback.search(
            query,
            top_k=top_k,
            article=article,
            document_id=document_id,
            document_types=document_types,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "count": len(self.chunks),
            "primary": self.primary.describe(),
            "fallback": self.fallback.describe(),
            "notes": list(self.notes),
        }


class NumpyVectorStore:
    """Small in-memory dense store used by tests and as a portable fallback."""

    kind = "numpy"

    def __init__(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        self.chunks = chunks
        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        self.vectors = matrix / np.clip(norms, 1e-12, None)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        article: str | None = None,
        document_id: str | None = None,
        document_types: set[str] | None = None,
    ) -> list[SearchHit]:
        vector = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        vector = vector / max(float(np.linalg.norm(vector)), 1e-12)
        scores = self.vectors @ vector
        indices = [
            i
            for i, chunk in enumerate(self.chunks)
            if (article is None or chunk.article == article)
            and (document_id is None or chunk.document_id == document_id)
            and (document_types is None or chunk.document_type in document_types)
        ]
        ranked = sorted(indices, key=lambda i: scores[i], reverse=True)[:top_k]
        return [SearchHit(chunk=self.chunks[i], score=float(scores[i])) for i in ranked]

    def describe(self) -> dict[str, Any]:
        return {"kind": self.kind, "count": len(self.chunks)}


class QdrantVectorStore:
    """Dense vector store backed by Qdrant local mode (on-disk inside the workspace)."""

    kind = "qdrant"

    def __init__(
        self,
        path: Path | None,
        collection: str,
        dimension: int,
        metadata: dict[str, Any] | None = None,
        url: str | None = None,
    ) -> None:
        from qdrant_client import QdrantClient

        self.path = path
        self.url = url
        self.collection = collection
        self.dimension = dimension
        self.metadata = metadata or {}
        if url:
            self.client = QdrantClient(url=url)
        else:
            assert path is not None
            path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(path))

    def is_ready(self) -> bool:
        if not self.client.collection_exists(self.collection):
            return False
        try:
            info = self.client.get_collection(self.collection)
            points_count = int(info.points_count or 0)
        except Exception:  # noqa: BLE001 - treat an unreadable collection as not ready
            return False
        expected = self.metadata.get("chunk_count")
        return points_count > 0 and (expected is None or points_count >= int(expected))

    def replace(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        from qdrant_client.models import Distance, PointStruct, VectorParams

        if self.client.collection_exists(self.collection):
            self.client.delete_collection(collection_name=self.collection)
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
        )
        points = [
            PointStruct(id=index, vector=np.asarray(vector, dtype=np.float32).tolist(), payload=chunk.to_dict())
            for index, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        if points:
            self.client.upsert(collection_name=self.collection, points=points)
        self.metadata.update({"count": len(points), "dimension": self.dimension, "kind": self.kind})

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        article: str | None = None,
        document_id: str | None = None,
        document_types: set[str] | None = None,
    ) -> list[SearchHit]:
        from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

        conditions = []
        if article is not None:
            conditions.append(FieldCondition(key="article", match=MatchValue(value=article)))
        if document_id is not None:
            conditions.append(FieldCondition(key="document_id", match=MatchValue(value=document_id)))
        if document_types:
            conditions.append(FieldCondition(key="document_type", match=MatchAny(any=sorted(document_types))))
        query_filter = Filter(must=conditions) if conditions else None

        vector = np.asarray(query_vector, dtype=np.float32).reshape(-1).tolist()
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection,
                query=vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )
            points = response.points
        else:  # pragma: no cover - older qdrant-client
            points = self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=top_k,
                query_filter=query_filter,
            )
        hits: list[SearchHit] = []
        for point in points:
            payload = dict(point.payload or {})
            hits.append(SearchHit(chunk=Chunk(**payload), score=float(point.score)))
        return hits

    def describe(self) -> dict[str, Any]:
        target = self.url or str(self.path)
        return {**self.metadata, "kind": self.kind, "collection": self.collection, "target": target}

    def close(self) -> None:
        self.client.close()
