"""Section-aware ingestion for Markdown learning corpora."""

from __future__ import annotations

import re
from pathlib import Path

from app.document_processing.chunker import Chunk

SECTION_RE = re.compile(r"(?m)^(?=## )")
TABLE_ROW_RE = re.compile(r"^\s*\|")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def _split_tables(text: str) -> tuple[str, list[list[str]]]:
    prose: list[str] = []
    tables: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if TABLE_ROW_RE.match(line):
            current.append(line)
        else:
            if current:
                tables.append(current)
                current = []
            prose.append(line)
    if current:
        tables.append(current)
    return "\n".join(prose).strip(), tables


def _table_row_chunks(article: str, table: list[str]) -> list[str]:
    rows = [row for row in table if TABLE_ROW_RE.match(row)]
    if len(rows) < 2:
        return []
    header = rows[0]
    data_rows = rows[2:] if len(rows) > 1 and TABLE_SEPARATOR_RE.match(rows[1]) else rows[1:]
    return [f"{article}\n{header}\n{row}" for row in data_rows]


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
        prose, tables = _split_tables(part)
        for piece in _split_long(prose, max_chars):
            piece = piece.strip()
            if not piece:
                continue
            if len(piece) < 40 and tables:
                continue
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
        for table in tables:
            for row_text in _table_row_chunks(article, table):
                chunks.append(
                    Chunk(
                        chunk_id=f"{document_id}:t{index}",
                        document_id=document_id,
                        text=row_text,
                        article=article,
                        subarticle="table_row",
                        page=1,
                        page_end=1,
                        document_type=document_type,
                    )
                )
                index += 1
    return chunks
