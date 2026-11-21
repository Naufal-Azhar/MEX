"""Build processed document records (JSON/Markdown/JSONL) from source PDFs."""

from __future__ import annotations

import json
import re
import unicodedata
import hashlib
from pathlib import Path
from typing import Any

from app.document_processing.pdf_loader import extract_pages, read_metadata

ARTICLE_RE = re.compile(r"^\s*(ARTICLE|APPENDIX|SECTION)\s+[A-Z0-9]+", re.IGNORECASE)
MIN_CHARS_PER_PAGE = 120


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value


def classify(path: Path) -> dict[str, str]:
    parent = path.parent.name.lower()
    name = path.name.lower()
    if "regulasi" in parent or "regulasi" in path.parent.parent.name.lower():
        return {"document_type": "regulation", "authority": "FIA"}
    if "jurnal" in parent:
        return {"document_type": "journal", "authority": "scientific_literature"}
    if "section" in name and "regulations" in name:
        return {"document_type": "regulation", "authority": "FIA"}
    return {"document_type": "unknown", "authority": "unknown"}


def parse_fia_filename(name: str) -> dict[str, Any]:
    info: dict[str, Any] = {}
    match = re.search(r"Section\s+([A-Z])\s*\[([^\]]+)\]", name, re.IGNORECASE)
    if match:
        info["section"] = match.group(1).upper()
        info["section_title"] = match.group(2).strip()
    match = re.search(r"Iss\s*(\d+)", name, re.IGNORECASE)
    if match:
        info["issue"] = match.group(1)
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if match:
        info["document_date"] = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"(20\d{2})", name)
    if match:
        info["year"] = match.group(1)
    return info


def load_overrides(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("overrides", {})


def render_markdown(document: dict[str, Any]) -> str:
    lines = [f"# {document['title']}", ""]
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    for key in (
        "document_id",
        "document_type",
        "authority",
        "publisher",
        "authors",
        "year",
        "issue",
        "document_date",
    ):
        lines.append(f"| {key} | {document.get(key) or '-'} |")
    lines.append("")

    for page in document["pages"]:
        lines.append(f"<!-- page: {page['page']} -->")
        lines.append("")
        if page["needs_ocr"]:
            lines.append(f"> [NO EXTRACTABLE TEXT ON PAGE {page['page']} — OCR REQUIRED]")
            lines.append("")
            continue
        body_sizes = [b["font_size"] for b in page["blocks"] if b["font_size"]]
        median_size = sorted(body_sizes)[len(body_sizes) // 2] if body_sizes else 0.0
        for block in page["blocks"]:
            text = block["text"].strip()
            if not text:
                continue
            is_heading = (
                block["font_size"] >= median_size + 1.5
                or (block["bold"] and len(text) < 120)
                or bool(ARTICLE_RE.match(text))
            )
            lines.append(f"### {text}" if is_heading and len(text) < 200 else text)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_document(
    path: Path,
    source_root: Path,
    overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Extract one PDF into a structured document. Never fabricates text."""
    overrides = overrides or {}
    meta = classify(path)
    parsed = parse_fia_filename(path.name)
    pages = extract_pages(path)
    pdf_meta = read_metadata(path)
    page_count = len(pages)

    total_chars = sum(p["char_count"] for p in pages)
    ocr_pages = [p["page"] for p in pages if p["needs_ocr"]]
    average_chars = round(total_chars / page_count, 1) if page_count else 0.0
    notes: list[str] = []
    if ocr_pages:
        notes.append(f"{len(ocr_pages)} page(s) have no extractable text and require OCR: {ocr_pages}")
    if average_chars < MIN_CHARS_PER_PAGE:
        notes.append("Low average character density; extraction quality may be poor.")

    document_id = slugify(path.stem)
    if parsed.get("section_title"):
        title = (
            f"FIA 2026 Formula One Regulations — Section {parsed['section']} "
            f"[{parsed['section_title']}]"
        )
    else:
        title = pdf_meta.get("title") or path.stem

    document: dict[str, Any] = {
        "document_id": document_id,
        "title": title,
        "file_name": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "file_size_bytes": path.stat().st_size,
        "document_type": meta["document_type"],
        "authority": meta["authority"],
        "publisher": pdf_meta.get("author") or ("FIA" if meta["authority"] == "FIA" else None),
        "year": parsed.get("year"),
        "issue": parsed.get("issue"),
        "document_date": parsed.get("document_date"),
        "section": parsed.get("section"),
        "section_title": parsed.get("section_title"),
        "pdf_metadata": pdf_meta,
        "page_count": page_count,
        "extraction": {
            "status": "partial" if ocr_pages else "success",
            "total_characters": total_chars,
            "average_characters_per_page": average_chars,
            "pages_needing_ocr": ocr_pages,
            "notes": notes,
        },
        "pages": pages,
    }

    override = overrides.get(document_id)
    if override:
        for key in (
            "title",
            "publisher",
            "authors",
            "year",
            "issue",
            "document_date",
            "venue",
            "doi",
        ):
            if override.get(key):
                document[key] = override[key]
        document["metadata_provenance"] = {
            "source": "manual_verification",
            "verified_from": override.get("verified_from"),
        }

    document["source_path"] = str(path.relative_to(source_root)).replace("\\", "/")
    return document


def write_document(document: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    document_id = document["document_id"]
    json_path = out_dir / f"{document_id}.json"
    md_path = out_dir / f"{document_id}.md"
    jsonl_path = out_dir / f"{document_id}.pages.jsonl"

    json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(document), encoding="utf-8")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for page in document["pages"]:
            handle.write(
                json.dumps(
                    {
                        "document_id": document_id,
                        "page": page["page"],
                        "text": page["text"],
                        "needs_ocr": page["needs_ocr"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return {
        "processed_json": str(json_path.as_posix()),
        "processed_markdown": str(md_path.as_posix()),
        "processed_pages_jsonl": str(jsonl_path.as_posix()),
    }
