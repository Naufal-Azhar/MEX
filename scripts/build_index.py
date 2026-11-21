"""Build (or rebuild) the retrieval index inside the workspace."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import configure_local_caches, get_logger, load_settings  # noqa: E402
from app.rag.retriever import Retriever  # noqa: E402


def main() -> int:
    configure_local_caches()
    logger = get_logger("scripts.build_index")
    settings = load_settings()
    logger.info(
        "Building retrieval index (embedding_backend=%s, model=%s)",
        settings.embedding_backend,
        settings.embedding_model,
    )
    retriever = Retriever.load_or_build(force=True)
    description = retriever.describe()
    print(json.dumps(description, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
