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

DEFINITION_TERMS = (
    "unit",
    "definition",
    "define",
    "encoded",
    "encoding",
    "what is",
    "what does",
    "format",
    "represent",
    "satuan",
    "apa",
)
EXPLANATION_TERMS = (
    "how",
    "why",
    "should",
    "handle",
    "interpret",
    "explain",
    "mean",
    "compare",
    "difference",
    "bagaimana",
    "mengapa",
    "menangani",
)
CHANNEL_TERMS = ("brake", "throttle", "speed", "gear", "drs", "distance", "rpm", "time", "acc_x", "acc_y", "acc_z")
QUERY_EXPANSIONS = {
    "rem": "brake",
    "pengereman": "braking",
    "satuan": "unit",
    "kecepatan": "speed",
    "jarak": "distance",
    "ban": "tyre",
    "hilang": "missing",
    "nilai": "value",
    "tekanan": "pressure",
    "beban": "load",
    "sesi": "session",
    "massa": "mass",
    "bahan bakar": "fuel",
    "udara": "air",
    "ketidakpastian": "uncertainty",
    "posisi": "position",
    "antara": "between",
    "masuk": "entering",
    "menangani": "handle",
    "bagaimana": "how",
    "mengapa": "why",
}


def _expand_query(query: str) -> str:
    text = query.lower()
    extras = [english for indonesian, english in QUERY_EXPANSIONS.items() if indonesian in text]
    return f"{query} {' '.join(extras)}".strip() if extras else query


def _score_multiplier(query: str, chunk: Chunk) -> float:
    if chunk.subarticle != "table_row":
        return 1.0
    text = query.lower()
    if any(term in text for term in EXPLANATION_TERMS):
        return 0.3
    if any(term in text for term in DEFINITION_TERMS):
        chunk_text = chunk.text.lower()
        if any(term in text and term in chunk_text for term in CHANNEL_TERMS):
            return 3.0
        return 1.2
    return 0.6


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
        expanded = _expand_query(query)
        hits = self.store.search(expanded, top_k=max(top_k * 4, top_k))
        adjusted = sorted(
            ((hit.score * _score_multiplier(expanded, hit.chunk), hit) for hit in hits),
            key=lambda item: item[0],
            reverse=True,
        )[:top_k]
        return [
            RetrievalHit(
                document_id=hit.chunk.document_id,
                document_type=hit.chunk.document_type,
                article=hit.chunk.article,
                page=hit.chunk.page,
                text=hit.chunk.text,
                score=round(score, 6),
                chunk_id=hit.chunk.chunk_id,
            )
            for score, hit in adjusted
        ]
