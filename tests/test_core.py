"""Unit tests for DOCX Parser and SQLite FTS5 Database."""

import sys
import os
import shutil
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docx import Document
from src.parser import DocxParser
from src.database import Database

def create_sample_docx(path: str, title: str, author: str, paragraphs: list):
    doc = Document()
    doc.core_properties.title = title
    doc.core_properties.author = author
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(path)

def run_tests():
    temp_dir = tempfile.mkdtemp(prefix="docx_test_")
    try:
        temp_path = Path(temp_dir)
        db_path = temp_path / "test.db"
        db = Database(str(db_path))

        # 1. Create two test docx files
        doc1_path = temp_path / "financial_report_2026.docx"
        create_sample_docx(
            str(doc1_path),
            title="Q3 Financial Overview",
            author="Rajiv",
            paragraphs=[
                "This document summarizes quarterly performance and revenue projections.",
                "Total net profit increased by 18 percent compared to the previous fiscal quarter.",
                "Capital expenditure for cloud infrastructure and AI workstation hardware was approved."
            ]
        )

        doc2_path = temp_path / "project_alpha_spec.docx"
        create_sample_docx(
            str(doc2_path),
            title="Project Alpha Specifications",
            author="Engineering Lead",
            paragraphs=[
                "System architecture overview for the desktop document indexing client.",
                "The engine indexes word documents locally using an offline SQLite database.",
                "Key requirements include instant search and low latency text retrieval."
            ]
        )

        # 2. Test Parser
        parsed1 = DocxParser.parse(str(doc1_path))
        print("Parsed doc1:", parsed1.file_name, "Title:", parsed1.title, "Words:", parsed1.word_count)
        assert parsed1.word_count > 0, "Word count should be positive"
        assert "quarterly performance" in parsed1.content.lower(), "Content must contain paragraph text"

        parsed2 = DocxParser.parse(str(doc2_path))
        print("Parsed doc2:", parsed2.file_name, "Title:", parsed2.title, "Words:", parsed2.word_count)
        assert "architecture" in parsed2.content.lower(), "Content must contain paragraph text"

        # 3. Test Database Insertion
        inserted1 = db.upsert_document(parsed1)
        inserted2 = db.upsert_document(parsed2)
        assert inserted1 and inserted2, "Both docs should be inserted"

        # 4. Test Search by Content
        results, count = db.search_documents("quarterly profit", scope="all")
        print(f"Search 'quarterly profit': found {count} results")
        assert count == 1, f"Expected 1 match, got {count}"
        assert results[0]["filename"] == "financial_report_2026.docx"
        assert "«HL»" in results[0]["snippet_text"], "Snippet should contain highlight tags"

        # 5. Test Search by Prefix (e.g. 'architec*' matching 'architecture')
        results, count = db.search_documents("architec", scope="all")
        print(f"Search prefix 'architec': found {count} results")
        assert count == 1, f"Expected 1 match, got {count}"
        assert results[0]["filename"] == "project_alpha_spec.docx"

        # 6. Test Scope: Title only
        results, count = db.search_documents("Financial", scope="title")
        print(f"Search 'Financial' in Title: found {count} results")
        assert count == 1

        # 7. Test Empty Search (Lists all files)
        results, count = db.search_documents("")
        print(f"Empty search (all files): found {count} results")
        assert count == 2

        # 8. Test Stats
        stats = db.get_stats()
        print("Stats:", stats)
        assert stats["total_docs"] == 2
        assert stats["total_words"] > 0

        # 9. Test Incremental Update (no-op if unchanged)
        res_unchanged = db.upsert_document(parsed1)
        assert not res_unchanged, "Should return False when unchanged"

        # 10. Test Removal
        assert db.remove_document(str(doc1_path)), "Document 1 should be removed"
        stats_after = db.get_stats()
        assert stats_after["total_docs"] == 1

        print("=== ALL CORE TESTS PASSED SUCCESSFULLY! ===")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_tests()

