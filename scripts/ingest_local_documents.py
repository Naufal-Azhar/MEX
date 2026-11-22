"""Ingest local engineering PDFs into a separate, gitignored engineering corpus.

Source PDFs are read-only. Processed text is written under storage/engineering.
Metadata and provenance are written to knowledge_base/metadata/engineering_sources.json.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "folder_dokumen" / "dokumen-jurnal"
PROCESSED = ROOT / "storage" / "engineering" / "processed"
MARKDOWN = ROOT / "storage" / "engineering" / "markdown"
MANIFEST = ROOT / "knowledge_base" / "metadata" / "engineering_sources.json"

DOCUMENTS = {
    "548872_Fulltext.pdf": {
        "document_id": "vehicle-motion-engineering-2025",
        "document_type": "engineering_textbook",
        "title": "Vehicle Motion Engineering (2025 Edition)",
        "authors": ["Jacobson, B.", "Jonasson, M.", "Bruzelius, F."],
        "year": 2025,
        "publisher": "Chalmers University of Technology",
        "doi": None,
        "rights_status": "copyright_user_provided_local_only",
        "rights_note": "Copyright marker present; reuse permission not verified. Local academic indexing only; do not redistribute processed text.",
        "reference_match": "Vehicle Motion Engineering — 2025 Edition, Chalmers University of Technology",
        "relevance": "high: longitudinal, lateral, vertical vehicle dynamics; braking; tyres; suspension",
    },
    "2005.11401v4.pdf": {
        "document_id": "rag-knowledge-intensive-nlp-2020",
        "document_type": "methodology",
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": ["Lewis, P.", "Perez, E.", "Piktus, A.", "Petronii, F.", "Karpukhin, V."],
        "year": 2020,
        "publisher": "arXiv / NeurIPS 2020",
        "doi": "10.48550/arXiv.2005.11401",
        "rights_status": "arxiv_nonexclusive_1.0_local_only",
        "rights_note": "arXiv non-exclusive distribution license; local research use. Do not redistribute processed text.",
        "reference_match": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "relevance": "methodology: RAG architecture and evaluation, not engineering evidence",
    },
    "applsci-14-01903.pdf": {
        "document_id": "elsd-tire-road-friction-2024",
        "document_type": "engineering_paper",
        "title": "Enhanced Vehicle Dynamics and Safety through Tire–Road Friction Estimation for Predictive ELSD Control under Various Conditions of General Racing Tracks",
        "authors": ["Woo, S.", "Jeon, S.", "Joa, E.", "Shin, D."],
        "year": 2024,
        "publisher": "Applied Sciences (MDPI)",
        "doi": "10.3390/app14051903",
        "rights_status": "cc_by_4.0",
        "rights_note": "Open access, CC BY 4.0; attribution required.",
        "reference_match": "Enhanced Vehicle Dynamics and Safety through Tire–Road Friction Estimation for Predictive ELSD Control under Various Conditions of General Racing Tracks",
        "relevance": "high: tire-road friction estimation, ELSD control, racing vehicle dynamics",
    },
    "energies-14-05118-v2.pdf": {
        "document_id": "racing-tire-sliding-energy-2021",
        "document_type": "engineering_paper",
        "title": "Sensitivity of Racing Tire Sliding Energy to Major Setup Changes: An Estimate Based on Standard Sensors",
        "authors": ["Chindamo, D.", "Gadola, M.", "Bonera, E.", "Magri, P."],
        "year": 2021,
        "publisher": "Energies (MDPI)",
        "doi": "10.3390/en14165118",
        "rights_status": "cc_by_4.0",
        "rights_note": "Open access, CC BY 4.0; attribution required.",
        "reference_match": "Sensitivity of Racing Tire Sliding Energy to Major Setup Changes",
        "relevance": "high: tire sliding energy, setup changes, racing tire management",
    },
    "sensors-22-06380-v3.pdf": {
        "document_id": "tire-lateral-dynamics-2022",
        "document_type": "engineering_paper",
        "title": "Modeling of the Influence of Operational Parameters on Tire Lateral Dynamics",
        "authors": ["Alcázar Vargas, M.", "Pérez Fernández, J.", "Sánchez Andrades, I.", "Cabrera Carrillo, J.A.", "Castillo Aguilar, J.J."],
        "year": 2022,
        "publisher": "Sensors (MDPI)",
        "doi": "10.3390/s22176380",
        "rights_status": "cc_by_4.0",
        "rights_note": "Open access, CC BY 4.0; attribution required.",
        "reference_match": "Modeling of the Influence of Operational Parameters on Tire Lateral Dynamics",
        "relevance": "high: tire lateral dynamics, relaxation length, temperature, load, speed",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _markdown(document_id: str, title: str, metadata: dict, pages: list[dict]) -> str:
    lines = [f"# {title}", ""]
    for key, value in metadata.items():
        if value:
            lines.append(f"{key}: {value}")
    lines.append("")
    for page in pages:
        lines.append(f"## Page {page['page']}")
        lines.append("")
        lines.append(page["text"].strip())
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not SOURCE.exists():
        print(f"MISSING: {SOURCE}")
        return 1

    PROCESSED.mkdir(parents=True, exist_ok=True)
    MARKDOWN.mkdir(parents=True, exist_ok=True)
    entries = []
    for filename, spec in DOCUMENTS.items():
        path = SOURCE / filename
        if not path.exists():
            entries.append({"file_name": filename, "status": "MISSING"})
            print(f"MISSING {filename}")
            continue
        doc = fitz.open(path)
        pages = []
        low_text = []
        for index, page in enumerate(doc):
            text = page.get_text("text") or ""
            if len(text.strip()) < 40:
                low_text.append(index + 1)
            pages.append({"page": index + 1, "text": text, "low_text": len(text.strip()) < 40})
        embedded = doc.embfile_count()
        encrypted = doc.is_encrypted
        doc.close()

        entry = {
            "document_id": spec["document_id"],
            "file_name": filename,
            "source_path": f"folder_dokumen/dokumen-jurnal/{filename}",
            "document_type": spec["document_type"],
            "title": spec["title"],
            "authors": spec["authors"],
            "year": spec["year"],
            "publisher": spec["publisher"],
            "doi": spec["doi"],
            "rights_status": spec["rights_status"],
            "rights_note": spec["rights_note"],
            "reference_match": spec["reference_match"],
            "relevance": spec["relevance"],
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
            "page_count": len(pages),
            "low_text_pages": low_text,
            "embedded_files": embedded,
            "encrypted": encrypted,
            "processed_json": f"storage/engineering/processed/{spec['document_id']}.json",
            "processed_markdown": f"storage/engineering/markdown/{spec['document_id']}.md",
            "processed_pages_jsonl": f"storage/engineering/processed/{spec['document_id']}.pages.jsonl",
            "status": "VERIFIED_IDENTITY",
        }
        payload = {
            "document_id": spec["document_id"],
            "title": spec["title"],
            "metadata": {key: entry[key] for key in ("authors", "year", "publisher", "doi")},
            "source_path": entry["source_path"],
            "sha256": entry["sha256"],
            "page_count": len(pages),
            "pages": pages,
        }
        (PROCESSED / f"{spec['document_id']}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (MARKDOWN / f"{spec['document_id']}.md").write_text(
            _markdown(spec["document_id"], spec["title"], payload["metadata"], pages), encoding="utf-8"
        )
        with (PROCESSED / f"{spec['document_id']}.pages.jsonl").open("w", encoding="utf-8") as handle:
            for page in pages:
                handle.write(json.dumps({"document_id": spec["document_id"], **page}, ensure_ascii=False) + "\n")
        entries.append(entry)
        print(f"OK {spec['document_id']}: {len(pages)} pages, low_text={low_text}")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": "folder_dokumen/dokumen-jurnal",
        "processed_root": "storage/engineering",
        "document_count": len(entries),
        "documents": entries,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
