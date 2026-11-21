"""Retrieval pipeline: chunked regulation pages -> vector index -> evidence hits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import PROCESSED_DIR, ROOT, VECTOR_DB_DIR, load_settings
from app.document_processing.chunker import Chunk, chunks_from_processed_dir
from app.rag.embeddings import (
    EmbeddingBackend,
    SentenceTransformerBackend,
    TfidfEmbeddingBackend,
    get_embedding_backend,
)
from app.rag.vector_store import NumpyVectorStore, QdrantVectorStore, SearchHit, TfidfVectorStore
from app.schemas.results import RetrievalHit

TFIDF_INDEX_PATH = VECTOR_DB_DIR / "tfidf_index.joblib"
DENSE_META_PATH = VECTOR_DB_DIR / "dense_index.json"
DENSE_COLLECTION = "regulation_chunks"


class Retriever:
    def __init__(self, store: Any, backend: EmbeddingBackend | None = None, notes: list[str] | None = None) -> None:
        self.store = store
        self.backend = backend
        self.notes = notes or []

    # ------------------------------------------------------------------ builders
    @classmethod
    def from_chunks(
        cls,
        chunks: list[Chunk],
        backend: str = "tfidf",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> "Retriever":
        if not chunks:
            raise ValueError("Cannot build a retriever without chunks.")
        if backend in ("tfidf", "lexical"):
            tfidf = TfidfEmbeddingBackend()
            store = TfidfVectorStore.build(chunks, tfidf)
            return cls(store, tfidf, notes=tfidf.notes)
        embedder = get_embedding_backend(backend, model_name)
        vectors = embedder.embed_documents([chunk.text for chunk in chunks])
        if backend == "numpy":
            return cls(NumpyVectorStore(chunks, vectors), embedder, notes=embedder.notes)
        store = QdrantVectorStore(VECTOR_DB_DIR / "qdrant", DENSE_COLLECTION, embedder.dimension or 0)
        store.replace(chunks, vectors)
        return cls(store, embedder, notes=embedder.notes)

    @classmethod
    def load_or_build(
        cls,
        processed_dir: Path | str = PROCESSED_DIR,
        force: bool = False,
    ) -> "Retriever":
        settings = load_settings()
        backend_pref = settings.embedding_backend
        qdrant_url = settings.qdrant_url or None
        embedder = get_embedding_backend(backend_pref, settings.embedding_model)
        is_tfidf = isinstance(embedder, TfidfEmbeddingBackend)

        if is_tfidf:
            if TFIDF_INDEX_PATH.exists() and not force:
                store = TfidfVectorStore.load(TFIDF_INDEX_PATH)
                return cls(store, store.backend, notes=store.backend.notes)
            chunks = chunks_from_processed_dir(processed_dir, max_chars=settings.chunk_size)
            store = TfidfVectorStore.build(chunks, embedder)
            store.save(TFIDF_INDEX_PATH)
            return cls(store, embedder, notes=embedder.notes)

        if not isinstance(embedder, SentenceTransformerBackend):
            chunks = chunks_from_processed_dir(processed_dir, max_chars=settings.chunk_size)
            return cls.from_chunks(chunks, backend="numpy", model_name=settings.embedding_model)

        if DENSE_META_PATH.exists() and not force:
            meta = json.loads(DENSE_META_PATH.read_text(encoding="utf-8"))
            store = QdrantVectorStore(
                VECTOR_DB_DIR / "qdrant", DENSE_COLLECTION, int(meta["dimension"]), meta, url=qdrant_url
            )
            return cls(store, embedder, notes=embedder.notes)

        chunks = chunks_from_processed_dir(processed_dir, max_chars=settings.chunk_size)
        vectors = embedder.embed_documents([chunk.text for chunk in chunks])
        store = QdrantVectorStore(
            VECTOR_DB_DIR / "qdrant", DENSE_COLLECTION, embedder.dimension or 0, url=qdrant_url
        )
        store.replace(chunks, vectors)
        DENSE_META_PATH.parent.mkdir(parents=True, exist_ok=True)
        DENSE_META_PATH.write_text(
            json.dumps(
                {
                    "backend": embedder.name,
                    "model": settings.embedding_model,
                    "dimension": embedder.dimension,
                    "chunk_count": len(chunks),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return cls(store, embedder, notes=embedder.notes)

    # ------------------------------------------------------------------ search
    def search(
        self,
        query: str,
        top_k: int = 5,
        article: str | None = None,
        document_id: str | None = None,
        include_methodology: bool = False,
        document_types: set[str] | None = None,
    ) -> list[RetrievalHit]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if document_types is None:
            selected_types = None if include_methodology else {"regulation"}
        else:
            selected_types = set(document_types)

        if isinstance(self.store, TfidfVectorStore):
            raw_hits: list[SearchHit] = self.store.search(
                query,
                top_k=top_k,
                article=article,
                document_id=document_id,
                document_types=selected_types,
            )
        else:
            assert self.backend is not None
            vector = self.backend.embed_query(query)
            raw_hits = self.store.search(
                vector,
                top_k=top_k,
                article=article,
                document_id=document_id,
                document_types=selected_types,
            )
        return [
            RetrievalHit(
                document_id=hit.chunk.document_id,
                document_type=hit.chunk.document_type,
                article=hit.chunk.article,
                page=hit.chunk.page,
                text=hit.chunk.text,
                score=round(hit.score, 6),
                chunk_id=hit.chunk.chunk_id,
            )
            for hit in raw_hits
        ]

    def describe(self) -> dict[str, Any]:
        info = self.store.describe()
        target = info.get("target")
        if isinstance(target, str):
            target_path = Path(target)
            if target_path.is_absolute():
                try:
                    info["target"] = target_path.relative_to(ROOT).as_posix()
                except ValueError:
                    pass
        if self.backend is not None:
            info["embedding"] = self.backend.describe()
        if self.notes:
            info["notes"] = list(self.notes)
        return info
