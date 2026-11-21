"""Section-aware ingestion for Markdown learning corpora."""

from __future__ import annotations

import re
from pathlib import Path

from app.document_processing.chunker import Chunk

SECTION_RE = re.compile(r"(?m)^(?=## )")


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    paragraphs = [item.strip() for item in text.split("\n\n") if item.strip()]
    parts: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) + 2 > max_chars and buffer:
            parts.append(buffer.strip())
            buffer = ""
        buffer += paragraph + "\n\n"
    if buffer.strip():
        parts.append(buffer.strip())
    return parts


def chunk_markdown(
    path: Path | str,
    document_id: str,
    document_type: str,
    max_chars: int = 1600,
) -> list[Chunk]:
    source = Path(path)
    if not source.exists():
        return []
    text = source.read_text(encoding="utf-8")
    chunks: list[Chunk] = []
    index = 0
    for part in SECTION_RE.split(text):
        part = part.strip()
        if not part:
            continue
        if part.startswith("## "):
            article = part.splitlines()[0].lstrip("# ").strip()
        else:
            article = "introduction"
        for piece in _split_long(part, max_chars):
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}:s{index}",
                    document_id=document_id,
                    text=piece,
                    article=article,
                    subarticle=None,
                    page=1,
                    page_end=1,
                    document_type=document_type,
                )
            )
            index += 1
    return chunks
