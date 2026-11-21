"""Chunk processed document pages into retrievable units with article/page metadata."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

ARTICLE_RE = re.compile(r"^(ARTICLE|APPENDIX)\s+(C?\d+)\s*:", re.IGNORECASE)
SUBARTICLE_RE = re.compile(r"^(C\d+(?:\.\d+)+)(?:\s*$|\s+[A-Z(\u201c\"])")

NOISE_PATTERNS = [
    re.compile(r"^SECTION\s+[AC]:\s", re.IGNORECASE),
    re.compile(r"^\d{1,2}\s+\w+\s+20\d{2}$"),
    re.compile(r"^Issue\s+\d+$"),
    re.compile(r"^[AC]\d{1,3}\s+20\d{2}\s+Formula", re.IGNORECASE),
    re.compile(r"^[AC]?\d{1,3}$"),
    re.compile(r"^[A-C]$"),
    re.compile(r"^\u00a9\d{4}", re.IGNORECASE),
]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    article: str | None
    subarticle: str | None
    page: int
    page_end: int
    document_type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_noise(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    return any(pattern.match(stripped) for pattern in NOISE_PATTERNS)


def load_document(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _is_toc_page(text: str) -> bool:
    upper = text.upper()
    if "CONTENTS:" in upper:
        return True
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 15:
        return False
    if any("Advisory Committee" in line or line.startswith("Governance:") for line in lines):
        return False
    toc_like = sum(
        1 for line in lines if re.match(r"^[A-Z]?\d+(?:\.\d+)*\s+.+\s+\d{1,3}$", line)
    )
    short_lines = sum(1 for line in lines if len(line) <= 60)
    if toc_like >= 5 and toc_like / len(lines) > 0.3:
        return True
    return short_lines / len(lines) > 0.75


def chunk_pages(
    pages: Iterable[dict[str, Any]],
    document_id: str,
    document_type: str = "regulation",
    max_chars: int = 1200,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_len = 0
    start_page: int | None = None
    end_page: int | None = None
    current_article: str | None = None
    current_subarticle: str | None = None

    def flush() -> None:
        nonlocal buffer, buffer_len, start_page, end_page
        if not buffer or start_page is None:
            buffer, buffer_len, start_page, end_page = [], 0, None, None
            return
        text = "\n".join(buffer).strip()
        if text:
            index = len(chunks)
            chunks.append(
                Chunk(
                    chunk_id=f"{document_id}:p{start_page}:{index}",
                    document_id=document_id,
                    text=text,
                    article=current_subarticle or current_article,
                    subarticle=current_subarticle,
                    page=start_page,
                    page_end=end_page or start_page,
                    document_type=document_type,
                )
            )
        buffer, buffer_len, start_page, end_page = [], 0, None, None

    for page in pages:
        page_number = int(page["page"])
        page_text = page.get("text") or ""
        if _is_toc_page(page_text):
            continue
        for raw_line in page_text.splitlines():
            line = raw_line.strip()
            if _is_noise(line):
                continue

            article_match = ARTICLE_RE.match(line)
            sub_match = SUBARTICLE_RE.match(line)
            if article_match:
                flush()
                current_article = article_match.group(2).upper()
                current_subarticle = None
            elif sub_match:
                flush()
                current_subarticle = sub_match.group(1)

            if start_page is None:
                start_page = page_number
            end_page = page_number
            buffer.append(line)
            buffer_len += len(line) + 1
            if buffer_len >= max_chars:
                flush()

    flush()
    return chunks


def chunks_from_processed_dir(processed_dir: Path | str, max_chars: int = 1200) -> list[Chunk]:
    directory = Path(processed_dir)
    all_chunks: list[Chunk] = []
    for path in sorted(directory.glob("*.json")):
        if path.name.endswith(".pages.json") or path.name == "document_manifest.json":
            continue
        document = load_document(path)
        if "pages" not in document:
            continue
        all_chunks.extend(
            chunk_pages(
                document["pages"],
                document_id=document["document_id"],
                document_type=document.get("document_type", "regulation"),
                max_chars=max_chars,
            )
        )
    return all_chunks
