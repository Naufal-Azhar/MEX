"""Extract text from source PDFs, preserving page numbers and heading structure.

Outputs:
  knowledge_base/processed_documents/<document_id>.json
  knowledge_base/processed_documents/<document_id>.md
  knowledge_base/processed_documents/<document_id>.pages.jsonl
  knowledge_base/document_manifest.json

Never fabricates text: pages with no extractable text are flagged as needing OCR.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.document_processing.text_extractor import (  # noqa: E402
    build_document,
    load_overrides,
    write_document,
)

SOURCE_DIR = ROOT / "knowledge_base" / "source_documents"
PROCESSED_DIR = ROOT / "knowledge_base" / "processed_documents"
MANIFEST_PATH = ROOT / "knowledge_base" / "document_manifest.json"
OVERRIDES_PATH = ROOT / "knowledge_base" / "metadata" / "document_overrides.json"


def build_manifest_entry(document: dict) -> dict:
    extraction = document["extraction"]
    return {
        "document_id": document["document_id"],
        "file_name": document["file_name"],
        "title": document["title"],
        "sha256": document.get("sha256"),
        "file_size_bytes": document.get("file_size_bytes"),
        "document_type": document["document_type"],
        "authority": document["authority"],
        "publisher": document.get("publisher"),
        "authors": document.get("authors"),
        "venue": document.get("venue"),
        "doi": document.get("doi"),
        "year": document.get("year"),
        "issue": document.get("issue"),
        "document_date": document.get("document_date"),
        "section": document.get("section"),
        "metadata_provenance": document.get("metadata_provenance", {"source": "pdf_embedded_metadata"}),
        "location": f"knowledge_base/source_documents/{document['source_path']}",
        "page_count": document["page_count"],
        "processed_json": f"knowledge_base/processed_documents/{document['document_id']}.json",
        "processed_markdown": f"knowledge_base/processed_documents/{document['document_id']}.md",
        "processed_pages_jsonl": f"knowledge_base/processed_documents/{document['document_id']}.pages.jsonl",
        "extraction_status": extraction["status"],
        "extraction_notes": extraction["notes"],
        "pages_needing_ocr": extraction["pages_needing_ocr"],
        "average_characters_per_page": extraction["average_characters_per_page"],
    }


def main() -> int:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    overrides = load_overrides(OVERRIDES_PATH)
    pdf_paths = sorted(SOURCE_DIR.rglob("*.pdf"))
    if not pdf_paths:
        print("No PDFs found in", SOURCE_DIR)
        return 1

    manifest: list[dict] = []
    for path in pdf_paths:
        entry: dict
        try:
            document = build_document(path, SOURCE_DIR, overrides)
            write_document(document, PROCESSED_DIR)
            entry = build_manifest_entry(document)
            print(
                f"[ok] {path.name}: {document['page_count']} pages, "
                f"{document['extraction']['total_characters']} chars, "
                f"ocr_pages={len(document['extraction']['pages_needing_ocr'])}"
            )
        except Exception as exc:  # noqa: BLE001 - keep processing other documents
            entry = {
                "file_name": path.name,
                "location": f"knowledge_base/source_documents/{path.relative_to(SOURCE_DIR).as_posix()}",
                "document_id": path.stem.lower().replace(" ", "-"),
                "extraction_status": "failed",
                "extraction_notes": [f"Extraction error: {type(exc).__name__}: {exc}"],
            }
            print(f"[fail] {path.name}: {exc}")
        manifest.append(entry)

    manifest_doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/extract_documents.py",
        "source_root": "knowledge_base/source_documents",
        "document_count": len(manifest),
        "documents": manifest,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest written to {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
