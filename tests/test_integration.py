"""Full integration test verifying scanner, parser, database, watcher, and search queries."""

import sys
import os
import time
import shutil
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docx import Document
from src.config import ConfigManager
from src.database import Database
from src.scanner import DirectoryScanner
from src.watcher import DocxWatcher

def make_doc(path: Path, title: str, author: str, paragraphs: list):
    doc = Document()
    doc.core_properties.title = title
    doc.core_properties.author = author
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(str(path))

def test_full_pipeline():
    temp_dir = tempfile.mkdtemp(prefix="docx_integration_")
    try:
        root_path = Path(temp_dir)
        docs_folder = root_path / "WordDocs"
        docs_folder.mkdir()
        sub_folder = docs_folder / "Confidential"
        sub_folder.mkdir()

        db_path = root_path / "test_index.db"
        db = Database(str(db_path))
        scanner = DirectoryScanner(db)

        # 1. Create a suite of realistic sample documents
        doc1 = docs_folder / "Sales_Forecast_2026.docx"
        make_doc(
            doc1,
            title="Annual Sales Projections",
            author="Finance Team",
            paragraphs=[
                "Executive Summary for FY2026 sales pipeline.",
                "The European market demonstrated exceptional revenue growth of 24 percent.",
                "Targeted client contracts include enterprise SaaS licenses and cloud infrastructure migrations."
            ]
        )

        doc2 = sub_folder / "Employee_Code_of_Conduct.docx"
        make_doc(
            doc2,
            title="Global HR Guidelines",
            author="Human Resources",
            paragraphs=[
                "All staff members must adhere to workplace safety and cybersecurity compliance standards.",
                "Confidential customer records and financial statements must remain strictly encrypted.",
                "Remote employees are permitted flexible scheduling with prior managerial sign-off."
            ]
        )

        doc3 = docs_folder / "Machine_Learning_Architecture.docx"
        make_doc(
            doc3,
            title="Neural Network Engine Spec",
            author="AI Research Lab",
            paragraphs=[
                "This specification details our custom transformer model for semantic retrieval.",
                "Offline text indexing enables sub-millisecond keyword lookup without network dependency.",
                "Vector embeddings complement full-text inverted indexes for hybrid ranking."
            ]
        )

        print("[Test] Created 3 test documents in nested directories.")

        # 2. Run Scanner
        print("[Test] Running DirectoryScanner...")
        summary = scanner.scan_folders([str(docs_folder)])
        print(f"[Test] Scan Summary: {summary}")

        assert summary["total_found"] == 3, f"Expected 3 docs found, got {summary['total_found']}"
        assert summary["indexed"] == 3, f"Expected 3 docs indexed, got {summary['indexed']}"
        assert summary["errors"] == 0, f"Expected 0 errors, got {summary['errors']}"

        # 3. Test Search Queries
        print("\n--- Verifying Search Queries ---")

        # Query A: Full text inside document
        results, count = db.search_documents("European revenue growth")
        print(f"Query 'European revenue growth': {count} match(es)")
        assert count == 1
        assert results[0]["filename"] == "Sales_Forecast_2026.docx"
        assert "«HL»" in results[0]["snippet_text"]
        print(f"Snippet: {results[0]['snippet_text']}")

        # Query B: Search by word in body of confidential doc
        results, count = db.search_documents("cybersecurity compliance")
        print(f"Query 'cybersecurity compliance': {count} match(es)")
        assert count == 1
        assert results[0]["filename"] == "Employee_Code_of_Conduct.docx"

        # Query C: Prefix search
        results, count = db.search_documents("transform")
        print(f"Query 'transform': {count} match(es)")
        assert count == 1
        assert results[0]["filename"] == "Machine_Learning_Architecture.docx"

        # Query D: Search by filename
        results, count = db.search_documents("Forecast", scope="title")
        print(f"Query 'Forecast' (scope=title): {count} match(es)")
        assert count == 1
        assert results[0]["filename"] == "Sales_Forecast_2026.docx"

        # Query E: Empty search returns all documents
        results, count = db.search_documents("")
        print(f"Empty Query: {count} total documents in index")
        assert count == 3

        # 4. Test Rescan (Incremental caching: no unnecessary re-indexes)
        print("\n--- Verifying Incremental Scan ---")
        rescan_summary = scanner.scan_folders([str(docs_folder)])
        print(f"Rescan Summary: {rescan_summary}")
        assert rescan_summary["indexed"] == 0, "Unchanged files should not be re-indexed"
        assert rescan_summary["skipped"] == 3, "All 3 files should be skipped as up-to-date"

        # 5. Test Live Watcher with file creation and deletion
        print("\n--- Verifying Watcher / Live Sync ---")
        changed_events = []
        def on_change(event_type, path):
            changed_events.append((event_type, path))

        watcher = DocxWatcher(db, on_change=on_change)
        watcher.start([str(docs_folder)])

        # Create a new 4th doc
        doc4 = docs_folder / "Urgent_Notice.docx"
        make_doc(
            doc4,
            title="Office Relocation",
            author="Operations",
            paragraphs=["Headquarters will be moving to new facility on November 1st."]
        )
        print("Created new file Urgent_Notice.docx. Waiting for watcher debounce...")
        time.sleep(3.0)

        # Check if doc4 was indexed automatically
        results, count = db.search_documents("Relocation")
        print(f"Query 'Relocation' after auto-watch: {count} match(es)")
        assert count == 1, "Urgent_Notice.docx should be automatically indexed by watcher"
        assert results[0]["filename"] == "Urgent_Notice.docx"

        # Delete doc4
        print("Deleting Urgent_Notice.docx. Waiting for watcher...")
        doc4.unlink()
        time.sleep(1.0)
        # Note: In Windows watchdog, deletion triggers on_deleted
        # Let's verify DB state
        results_after_del, count_after_del = db.search_documents("Relocation")
        assert count_after_del == 0, "Urgent_Notice.docx should be pruned upon deletion"

        watcher.stop()
        print("\n[SUCCESS] ALL INTEGRATION TESTS PASSED PERFECTLY!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_full_pipeline()

