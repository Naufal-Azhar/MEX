import numpy as np
import pytest

from app.config import PROCESSED_DIR
from app.document_processing.chunker import Chunk, chunks_from_processed_dir
from app.rag.retriever import Retriever
from app.rag.vector_store import NumpyVectorStore, QdrantVectorStore

TARGET_ARTICLES = {"C2.3.1", "C2.3.3", "C2.3.5", "C4.1", "C4.2"}


@pytest.fixture(scope="module")
def chunks() -> list[Chunk]:
    all_chunks = chunks_from_processed_dir(PROCESSED_DIR)
    subset = [chunk for chunk in all_chunks if chunk.subarticle in TARGET_ARTICLES]
    assert len(subset) >= 5
    return subset


@pytest.fixture(scope="module")
def retriever(chunks) -> Retriever:
    return Retriever.from_chunks(chunks, backend="tfidf")


def test_wheelbase_query_retrieves_c233(retriever):
    hits = retriever.search("maximum wheelbase 3400 mm", top_k=3)
    assert hits
    assert hits[0].article == "C2.3.3"
    assert hits[0].page == 11


def test_retrieval_returns_metadata_and_positive_scores(retriever):
    hits = retriever.search("minimum mass nominal tyre mass", top_k=5)
    assert all(hit.score > 0 for hit in hits)
    assert all(hit.document_id for hit in hits)
    assert all(hit.chunk_id for hit in hits)


def test_article_filter(retriever):
    hits = retriever.search("mass distribution front axle rear axle", top_k=10, article="C4.2")
    assert hits
    assert {hit.article for hit in hits} == {"C4.2"}


def test_empty_query_rejected(retriever):
    with pytest.raises(ValueError):
        retriever.search("   ")


def test_methodology_documents_excluded_from_compliance_search():
    chunks = [
        Chunk("r1", "doc-regulation", "wheelbase 3400 mm", "C2.3.3", None, 11, 11, "regulation"),
        Chunk("j1", "doc-journal", "retrieval augmented generation citation precision", "retrieval", None, 1, 1, "journal"),
    ]
    retriever = Retriever.from_chunks(chunks, backend="tfidf")

    default_hits = retriever.search("retrieval augmented generation citation precision", top_k=5)
    assert all(hit.document_type == "regulation" for hit in default_hits)

    all_hits = retriever.search(
        "retrieval augmented generation citation precision",
        top_k=5,
        include_methodology=True,
    )
    assert any(hit.document_type == "journal" for hit in all_hits)


def test_numpy_store_cosine_similarity():
    chunks = [
        Chunk("c1", "doc", "text one", "C1", None, 1, 1, "regulation"),
        Chunk("c2", "doc", "text two", "C2", None, 2, 2, "regulation"),
    ]
    store = NumpyVectorStore(chunks, np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))
    hits = store.search(np.array([1.0, 0.0], dtype=np.float32), top_k=1)
    assert hits[0].chunk.chunk_id == "c1"
    assert hits[0].score == pytest.approx(1.0)


def test_qdrant_local_store(tmp_path):
    pytest.importorskip("qdrant_client")
    chunks = [
        Chunk("c1", "doc", "ethanol fuel", "C16", None, 1, 1, "regulation"),
        Chunk("c2", "doc", "wheelbase limit", "C2.3.3", None, 2, 2, "regulation"),
        Chunk("c3", "journal", "chaining experiment", "method", None, 3, 3, "journal"),
    ]
    store = QdrantVectorStore(tmp_path / "qdrant", "test_collection", 2)
    try:
        store.replace(
            chunks,
            np.array([[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]], dtype=np.float32),
        )
        hits = store.search(np.array([0.0, 1.0], dtype=np.float32), top_k=1)
        assert hits[0].chunk.chunk_id == "c2"
        filtered = store.search(np.array([0.0, 1.0], dtype=np.float32), top_k=5, article="C16")
        assert filtered[0].chunk.chunk_id == "c1"
        journal_only = store.search(
            np.array([0.0, 1.0], dtype=np.float32), top_k=5, document_types={"journal"}
        )
        assert [hit.chunk.chunk_id for hit in journal_only] == ["c3"]
    finally:
        store.close()
