"""Inventory local engineering PDFs without modifying the source files."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "folder_dokumen" / "dokumen-jurnal"
MANIFEST = ROOT / "knowledge_base" / "document_manifest.json"
OUTPUT = ROOT / "datasets" / "evaluation" / "local_document_inventory.json"


def _manifest_hashes() -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        doc["sha256"]: doc.get("document_id") or doc.get("file_name")
        for doc in data.get("documents", [])
        if doc.get("sha256")
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not SOURCE.exists():
        print(f"MISSING: {SOURCE}")
        return 1

    known_hashes = _manifest_hashes()
    rows = []
    for path in sorted(SOURCE.rglob("*")):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        row = {
            "file_name": path.name,
            "relative_path": path.relative_to(SOURCE).as_posix(),
            "size_bytes": len(raw),
            "sha256": sha,
            "duplicate_of_manifest": known_hashes.get(sha),
        }
        try:
            doc = fitz.open(path)
            row["page_count"] = doc.page_count
            row["encrypted"] = doc.is_encrypted
            row["embedded_files"] = doc.embfile_count()
            row["metadata"] = {key: value for key, value in (doc.metadata or {}).items() if value}
            page_texts = []
            low_text_pages = []
            total_chars = 0
            for index, page in enumerate(doc):
                text = page.get_text("text") or ""
                page_texts.append(text)
                total_chars += len(text)
                if len(text.strip()) < 40:
                    low_text_pages.append(index + 1)
            row["total_chars"] = total_chars
            row["low_text_pages"] = low_text_pages
            all_text = "\n".join(page_texts)
            row["first_page_text"] = " ".join(page_texts[0].split())[:1200] if page_texts else ""
            row["dois"] = sorted(set(re.findall(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", all_text)))[:10]
            lowered = all_text.lower()
            row["rights_markers"] = [
                marker
                for marker in ("creative commons", "cc by", "open access", "copyright", "license")
                if marker in lowered
            ]
            doc.close()
        except Exception as exc:  # noqa: BLE001 - report per-file failures
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in rows:
        print("=" * 90)
        print(row["file_name"], "|", row.get("page_count"), "pages |", row["size_bytes"], "bytes")
        print("  sha256:", row["sha256"])
        print("  title:", (row.get("metadata") or {}).get("title"))
        print("  author:", (row.get("metadata") or {}).get("author"))
        print("  doi:", row.get("dois"))
        print("  rights:", row.get("rights_markers"))
        print("  chars:", row.get("total_chars"), "low_text_pages:", row.get("low_text_pages"))
        print("  first:", (row.get("first_page_text") or "")[:500])
    print(f"\nWrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
