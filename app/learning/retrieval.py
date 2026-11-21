"""Scoped retrieval over the engineering learning corpus."""

from __future__ import annotations

from pathlib import Path

from app.document_processing.chunker import Chunk
from app.rag.corpus import chunk_markdown
from app.rag.embeddings import TfidfEmbeddingBackend
from app.rag.vector_store import TfidfVectorStore
from app.schemas.results import RetrievalHit

DEFAULT_LEARNING_CORPUS = [
    (
        "telemetry-data-dictionary",
        "data_dictionary",
        "knowledge_base/source_documents/telemetry/data_dictionary.md",
    ),
    (
        "engineering-fundamentals",
        "engineering_notes",
        "knowledge_base/source_documents/telemetry/engineering_fundamentals.md",
    ),
]


class LearningCorpusIndex:
    def __init__(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise ValueError("learning corpus is empty")
        self.chunks = chunks
        self.backend = TfidfEmbeddingBackend()
        self.store = TfidfVectorStore.build(chunks, self.backend)

    @classmethod
    def from_paths(
        cls,
        corpus: list[tuple[str, str, str]] | None = None,
        root: Path | str = ".",
    ) -> "LearningCorpusIndex":
        base = Path(root)
        chunks: list[Chunk] = []
        for document_id, document_type, relative in corpus or DEFAULT_LEARNING_CORPUS:
            chunks.extend(chunk_markdown(base / relative, document_id, document_type))
        return cls(chunks)

    def search(self, query: str, top_k: int = 3) -> list[RetrievalHit]:
        if not query.strip():
            raise ValueError("query must not be empty")
        hits = self.store.search(query, top_k=top_k)
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
            for hit in hits
        ]
