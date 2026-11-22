"""Static security audit for downloaded data and PDFs.

This script does not execute downloaded content. It checks file magic, hashes,
text-like data for suspicious tokens, and PDF active-content objects.
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
SCAN_ROOTS = [
    ROOT / "datasets" / "telemetry",
    ROOT / "datasets" / "reference",
    ROOT / "folder_dokumen",
    ROOT / "storage" / "engineering",
]
OUTPUT = ROOT / "datasets" / "evaluation" / "downloaded_source_audit.json"
TEXT_SUFFIXES = {".json", ".jsonl", ".csv", ".md", ".txt", ".yaml", ".yml"}
SUSPICIOUS = re.compile(
    r"(?i)(javascript:|<script|powershell|cmd\.exe|subprocess|os\.system|"
    r"eval\s*\(|exec\s*\(|base64,|\\x4d\\x5a|mimikatz|rundll32|regsvr32)"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _magic(path: Path) -> str:
    raw = path.read_bytes()[:16]
    if raw.startswith(b"%PDF"):
        return "pdf"
    if raw.startswith(b"MZ"):
        return "pe-executable"
    if raw.startswith(b"PK\x03\x04"):
        return "zip"
    if raw.startswith(b"\x89PNG"):
        return "png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    stripped = raw.lstrip()
    if stripped.startswith((b"{", b"[")):
        return "json-like"
    return "unknown"


def _pdf_check(path: Path) -> dict:
    doc = fitz.open(path)
    result = {
        "pages": doc.page_count,
        "encrypted": doc.is_encrypted,
        "embedded_files": list(doc.embfile_names()),
        "javascript_objects": [],
        "launch_objects": [],
        "open_actions": [],
        "xfa": [],
    }
    for xref in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(xref, compressed=False)
        except Exception:
            continue
        if not obj:
            continue
        for marker, key in (
            ("/JavaScript", "javascript_objects"),
            ("/JS", "javascript_objects"),
            ("/Launch", "launch_objects"),
            ("/OpenAction", "open_actions"),
            ("/XFA", "xfa"),
        ):
            if marker in obj:
                result[key].append({"xref": xref, "object": obj[:240]})
    doc.close()
    return result


def _text_check(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    matches = sorted(set(match.group(0) for match in SUSPICIOUS.finditer(text)))
    return {
        "suspicious_tokens": matches,
        "url_count": len(re.findall(r"https?://", text)),
        "has_null_byte": "\x00" in text,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            row = {
                "path": path.relative_to(ROOT).as_posix(),
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "magic": _magic(path),
            }
            if path.suffix.lower() == ".pdf":
                try:
                    row["pdf"] = _pdf_check(path)
                except Exception as exc:  # noqa: BLE001
                    row["pdf_error"] = f"{type(exc).__name__}: {exc}"
            elif path.suffix.lower() in TEXT_SUFFIXES:
                try:
                    row["text"] = _text_check(path)
                except Exception as exc:  # noqa: BLE001
                    row["text_error"] = f"{type(exc).__name__}: {exc}"
            rows.append(row)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scanned_roots": [root.relative_to(ROOT).as_posix() for root in SCAN_ROOTS if root.exists()],
        "file_count": len(rows),
        "files": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Scanned {len(rows)} files")
    print("Magic counts:")
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["magic"]] = counts.get(row["magic"], 0) + 1
    for magic, count in sorted(counts.items()):
        print(f"  {magic}: {count}")
    print("PDF active-content findings:")
    for row in rows:
        pdf = row.get("pdf")
        if not pdf:
            continue
        print(
            f"  {row['path']}: JS={len(pdf['javascript_objects'])}, "
            f"Launch={len(pdf['launch_objects'])}, "
            f"OpenAction={len(pdf['open_actions'])}, "
            f"Embedded={pdf['embedded_files']}, XFA={len(pdf['xfa'])}"
        )
    print("Suspicious text tokens:")
    for row in rows:
        tokens = (row.get("text") or {}).get("suspicious_tokens") or []
        if tokens:
            print(f"  {row['path']}: {tokens}")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
