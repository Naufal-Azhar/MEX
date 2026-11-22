"""Application configuration.

All caches (Hugging Face, sentence-transformers, torch) are redirected into
``storage/model_cache`` so that nothing is written outside the workspace.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = ROOT / "storage"
MODEL_CACHE_DIR = STORAGE_DIR / "model_cache"
VECTOR_DB_DIR = STORAGE_DIR / "vector_db"
LOG_DIR = STORAGE_DIR / "logs"

PROCESSED_DIR = ROOT / "knowledge_base" / "processed_documents"
RULES_PATH = ROOT / "knowledge_base" / "rules" / "rules.json"
SAMPLE_FACTS_PATH = ROOT / "knowledge_base" / "facts" / "sample_facts.json"
MANIFEST_PATH = ROOT / "knowledge_base" / "document_manifest.json"
DATASETS_DIR = ROOT / "datasets"


def ensure_directories() -> None:
    for path in (STORAGE_DIR, MODEL_CACHE_DIR, VECTOR_DB_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def configure_local_caches() -> None:
    """Point every model cache at the workspace before heavy libraries load."""
    ensure_directories()
    os.environ.setdefault("HF_HOME", str(MODEL_CACHE_DIR))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(MODEL_CACHE_DIR / "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(MODEL_CACHE_DIR / "transformers"))
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(MODEL_CACHE_DIR / "sentence-transformers"))
    os.environ.setdefault("TORCH_HOME", str(MODEL_CACHE_DIR / "torch"))


@dataclass
class Settings:
    llm_provider: str = "none"
    llm_api_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_api_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    embedding_backend: str = "bm25"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store: str = "qdrant"
    qdrant_url: str = ""
    chunk_size: int = 1200
    top_k: int = 5
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def provider_enabled(self) -> bool:
        return self.llm_provider not in ("", "none", "disabled")

    def llm_configured(self) -> bool:
        if self.llm_provider == "api":
            return bool(self.llm_api_key)
        if self.llm_provider == "ollama":
            return True
        return False


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "none").strip().lower(),
        llm_api_base_url=os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_api_model=os.getenv("LLM_API_MODEL", "gpt-4o-mini"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        embedding_backend=os.getenv("EMBEDDING_BACKEND", "bm25").strip().lower(),
        embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        vector_store=os.getenv("VECTOR_STORE", "qdrant").strip().lower(),
        qdrant_url=os.getenv("QDRANT_URL", "").strip().rstrip("/"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1200")),
        top_k=int(os.getenv("TOP_K", "5")),
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


def get_logger(name: str):
    import logging

    ensure_directories()
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = getattr(logging, load_settings().log_level, logging.INFO)
        logger.setLevel(level)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    return logger
