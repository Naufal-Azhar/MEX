import hashlib
import json

from app.config import MANIFEST_PATH, PROCESSED_DIR, ROOT
from app.document_processing.chunker import chunks_from_processed_dir
from app.document_processing.pdf_loader import extract_pages, read_metadata

SECTION_C_ID = "fia-2026-f1-regulations-section-c-technical-iss-21-2026-10-19"


def test_manifest_lists_all_documents():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["document_count"] == 4
    ids = {doc["document_id"] for doc in manifest["documents"]}
    assert SECTION_C_ID in ids
    for doc in manifest["documents"]:
        assert doc["extraction_status"] in {"success", "partial"}
        assert doc["location"].startswith("knowledge_base/source_documents/")
        assert doc["page_count"] > 0
        assert doc["publisher"]
        assert len(doc["sha256"]) == 64
        source_path = ROOT / doc["location"]
        assert doc["sha256"] == hashlib.sha256(source_path.read_bytes()).hexdigest()
        assert doc["file_size_bytes"] == source_path.stat().st_size


def test_section_c_page_count_and_ocr_flags():
    path = PROCESSED_DIR / f"{SECTION_C_ID}.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["page_count"] == 254
    assert document["extraction"]["pages_needing_ocr"] == []
    pages = [page["page"] for page in document["pages"]]
    assert pages == sorted(pages)
    assert pages[0] == 1 and pages[-1] == 254
    assert all(page["char_count"] > 0 for page in document["pages"])


def test_processed_outputs_exist():
    for suffix in (".json", ".md", ".pages.jsonl"):
        path = PROCESSED_DIR / f"{SECTION_C_ID}{suffix}"
        assert path.exists()
        assert path.stat().st_size > 0


def test_pdf_loader_reads_metadata_and_pages():
    pdf_path = next((ROOT / "knowledge_base" / "source_documents" / "REGULASI FIA").glob("*.pdf"))
    metadata = read_metadata(pdf_path)
    assert metadata["page_count"] > 0
    pages = extract_pages(pdf_path)
    assert len(pages) == metadata["page_count"]
    assert pages[0]["page"] == 1


def test_chunks_have_article_metadata_and_no_empty_text():
    chunks = chunks_from_processed_dir(PROCESSED_DIR)
    assert len(chunks) > 500
    assert all(chunk.text.strip() for chunk in chunks)
    assert all(chunk.document_id for chunk in chunks)

    wheelbase_chunks = [chunk for chunk in chunks if chunk.subarticle == "C2.3.3"]
    assert wheelbase_chunks
    assert any("3400mm" in chunk.text for chunk in wheelbase_chunks)
    assert all(chunk.page == 11 for chunk in wheelbase_chunks)


def test_toc_pages_are_not_indexed():
    chunks = chunks_from_processed_dir(PROCESSED_DIR)
    section_c = [chunk for chunk in chunks if chunk.document_id == SECTION_C_ID]
    numbered = [chunk for chunk in section_c if chunk.page <= 6]
    assert numbered == [], "table-of-contents pages should not produce retrieval chunks"


def test_journal_documents_are_indexed():
    chunks = chunks_from_processed_dir(PROCESSED_DIR)
    journal_chunks = [chunk for chunk in chunks if chunk.document_type == "journal"]
    assert len(journal_chunks) > 0
