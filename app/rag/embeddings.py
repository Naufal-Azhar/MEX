"""Embedding backends.

Primary: Sentence Transformers (model cache kept inside ``storage/model_cache``).
Fallback: TF-IDF, which keeps the prototype fully runnable offline and lets the
retrieval pipeline be tested without downloading a model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from app.config import MODEL_CACHE_DIR, configure_local_caches


def normalize_for_tfidf(text: str) -> str:
    """Split digit/letter boundaries so '1830mm' matches the token '1830'."""
    import re

    return re.sub(r"(?<=\d)(?=[A-Za-z])|(?<=[A-Za-z])(?=\d)", " ", text.lower())


class EmbeddingError(RuntimeError):
    pass


class EmbeddingBackend(ABC):
    name: str = "base"
    notes: list[str]

    def __init__(self) -> None:
        self.notes = []

    @abstractmethod
    def fit(self, texts: list[str]) -> None:
        ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> Any:
        ...

    @abstractmethod
    def embed_query(self, text: str) -> Any:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int | None:
        ...

    def describe(self) -> dict[str, Any]:
        return {"backend": self.name, "dimension": self.dimension, "notes": list(self.notes)}


class TfidfEmbeddingBackend(EmbeddingBackend):
    name = "tfidf"

    def __init__(self, max_features: int = 4096) -> None:
        super().__init__()
        self.max_features = max_features
        self.vectorizer = None
        self._dimension: int | None = None

    def fit(self, texts: list[str]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(
            lowercase=False,
            preprocessor=normalize_for_tfidf,
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=self.max_features,
            token_pattern=r"(?u)\b\w+\b",
        )
        self.vectorizer.fit(texts)
        self._dimension = len(self.vectorizer.get_feature_names_out())
        self.notes.append("TF-IDF fallback: lexical retrieval, not neural embeddings.")

    def _require_fitted(self) -> None:
        if self.vectorizer is None:
            raise EmbeddingError("TF-IDF backend is not fitted; call fit() with the corpus first.")

    def embed_documents(self, texts: list[str]) -> Any:
        self._require_fitted()
        return self.vectorizer.transform(texts)

    def embed_query(self, text: str) -> Any:
        self._require_fitted()
        return self.vectorizer.transform([text])

    @property
    def dimension(self) -> int | None:
        return self._dimension


class SentenceTransformerBackend(EmbeddingBackend):
    name = "sentence_transformers"

    def __init__(self, model_name: str) -> None:
        super().__init__()
        configure_local_caches()
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise EmbeddingError(
                "sentence-transformers is not installed. Install it inside the workspace venv "
                "or set EMBEDDING_BACKEND=tfidf."
            ) from exc
        self.model_name = model_name
        self._model = SentenceTransformer(
            model_name,
            cache_folder=str(MODEL_CACHE_DIR / "sentence-transformers"),
        )
        if hasattr(self._model, "get_embedding_dimension"):
            self._dimension = int(self._model.get_embedding_dimension())
        else:  # pragma: no cover - older sentence-transformers
            self._dimension = int(self._model.get_sentence_embedding_dimension())

    def fit(self, texts: list[str]) -> None:
        return None

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.asarray(
            self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32,
        )

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(
            self._model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0],
            dtype=np.float32,
        )

    @property
    def dimension(self) -> int:
        return self._dimension


def _sentence_transformer_cached(model_name: str) -> bool:
    safe = model_name.replace("/", "--")
    candidates = [
        MODEL_CACHE_DIR / "sentence-transformers" / model_name,
        MODEL_CACHE_DIR / "sentence-transformers" / safe,
        MODEL_CACHE_DIR / "sentence-transformers" / f"models--{safe}",
        MODEL_CACHE_DIR / "hub" / f"models--{safe}",
    ]
    return any(path.exists() for path in candidates)


def get_embedding_backend(preferred: str = "auto", model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> EmbeddingBackend:
    preferred = (preferred or "auto").lower()
    if preferred in ("bm25", "lexical-bm25"):
        backend = TfidfEmbeddingBackend()
        backend.notes.append("BM25 uses the lexical store directly; the embedding backend is a fallback only.")
        return backend
    if preferred in ("tfidf", "lexical"):
        return TfidfEmbeddingBackend()
    if preferred in ("sentence_transformers", "sentence-transformers", "st", "dense"):
        return SentenceTransformerBackend(model_name)
    if preferred == "auto":
        try:
            if _sentence_transformer_cached(model_name):
                return SentenceTransformerBackend(model_name)
        except EmbeddingError:
            pass
        backend = TfidfEmbeddingBackend()
        backend.notes.append(
            "Auto mode selected TF-IDF because no cached sentence-transformers model was found. "
            "Run scripts/build_index.py with EMBEDDING_BACKEND=sentence_transformers to download and use a neural model."
        )
        return backend
    raise EmbeddingError(f"Unknown embedding backend: {preferred}")
