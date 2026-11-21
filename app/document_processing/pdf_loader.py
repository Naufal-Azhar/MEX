"""PDF loading and page/block extraction with PyMuPDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz

OCR_PAGE_CHAR_THRESHOLD = 40


def open_document(path: Path | str) -> fitz.Document:
    return fitz.open(Path(path))


def read_metadata(path: Path | str) -> dict[str, Any]:
    with fitz.open(Path(path)) as doc:
        meta = doc.metadata or {}
        return {
            "title": meta.get("title"),
            "author": meta.get("author"),
            "subject": meta.get("subject"),
            "creator": meta.get("creator"),
            "producer": meta.get("producer"),
            "creation_date": meta.get("creationDate"),
            "modification_date": meta.get("modDate"),
            "page_count": doc.page_count,
        }


def extract_page(page: fitz.Page, index: int) -> dict[str, Any]:
    raw_text = page.get_text("text") or ""
    blocks: list[dict[str, Any]] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines: list[str] = []
        max_size = 0.0
        bold = False
        for line in block.get("lines", []):
            text_parts = []
            for span in line.get("spans", []):
                text_parts.append(span.get("text", ""))
                max_size = max(max_size, float(span.get("size", 0.0)))
                if int(span.get("flags", 0)) & 16:
                    bold = True
            line_text = "".join(text_parts).strip()
            if line_text:
                lines.append(line_text)
        block_text = " ".join(lines).strip()
        if block_text:
            blocks.append({"text": block_text, "font_size": round(max_size, 1), "bold": bold})

    return {
        "page": index + 1,
        "text": raw_text,
        "char_count": len(raw_text.strip()),
        "blocks": blocks,
        "needs_ocr": len(raw_text.strip()) < OCR_PAGE_CHAR_THRESHOLD,
    }


def extract_pages(path: Path | str) -> list[dict[str, Any]]:
    with fitz.open(Path(path)) as doc:
        return [extract_page(doc.load_page(i), i) for i in range(doc.page_count)]
