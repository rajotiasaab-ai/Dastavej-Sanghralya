"""Directory scanner for discovering and incrementally indexing .docx files.
Fully offline with parallel batch parsing and progress callbacks.
"""

import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Set, Callable, Optional, Dict, Any

from src.parser import DocxParser, ParsedDocx
from src.database import Database

# Directories and file patterns to ignore during recursive walk
IGNORED_DIR_NAMES = {
    "$recycle.bin", "system volume information", "node_modules",
    ".git", ".svn", ".venv", "venv", "__pycache__", "appdata",
    "site-packages", ".idea", ".vscode"
}

class DirectoryScanner:
    """Recursively scans folders for .docx documents and updates the SQLite index."""

    def __init__(self, db: Database):
        self.db = db
        self.is_scanning = False
        self._stop_requested = False

    def stop(self):
        """Request the active scan to cancel gracefully."""
        self._stop_requested = True

    def scan_folders(
        self,
        folders: List[str],
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Discovers all .docx files in the specified folders and indexes new/updated ones.
        Returns summary stats: { 'scanned': int, 'indexed': int, 'skipped': int, 'errors': int }
        """
        self.is_scanning = True
        self._stop_requested = False
        start_time = time.time()

        if on_status:
            on_status("Discovering files...")

        all_docx_files: List[Path] = []
        for folder_str in folders:
            folder_path = Path(folder_str)
            if not folder_path.exists() or not folder_path.is_dir():
                continue
            
            try:
                for root, dirs, files in os.walk(folder_path, followlinks=False):
                    if self._stop_requested:
                        break

                    # Prune ignored directory trees in-place
                    dirs[:] = [
                        d for d in dirs
                        if d.lower() not in IGNORED_DIR_NAMES
                        and not d.startswith(".")
                    ]

                    for f in files:
                        if f.lower().endswith(".docx") and not f.startswith("~$"):
                            all_docx_files.append(Path(root) / f)
            except PermissionError:
                continue
            except Exception as e:
                print(f"[Scanner] Error walking {folder_str}: {e}")

        total_files = len(all_docx_files)
        if on_status:
            on_status(f"Found {total_files} Word documents. Checking index...")

        # Get existing indexed paths for fast comparison
        files_to_parse: List[Path] = []
        skipped_count = 0

        for f_path in all_docx_files:
            if self._stop_requested:
                break
            try:
                stat = f_path.stat()
                existing = self.db.get_document_by_path(str(f_path.resolve()))
                if existing:
                    # Check if file has changed
                    if existing["file_size"] == stat.st_size and abs(existing["mtime"] - stat.st_mtime) < 0.001:
                        skipped_count += 1
                        continue
                files_to_parse.append(f_path)
            except Exception:
                continue

        to_index_count = len(files_to_parse)
        indexed_count = 0
        error_count = 0

        if on_status:
            on_status(f"Indexing {to_index_count} new or updated documents...")

        # Helper function for worker threads
        def process_file(path_obj: Path) -> Optional[ParsedDocx]:
            try:
                return DocxParser.parse(str(path_obj.resolve()))
            except Exception as e:
                print(f"[Scanner] Error parsing {path_obj}: {e}")
                return None

        # Parallel extraction for speed
        if files_to_parse:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for i, parsed in enumerate(executor.map(process_file, files_to_parse)):
                    if self._stop_requested:
                        break

                    if parsed and not parsed.error:
                        try:
                            self.db.upsert_document(parsed)
                            indexed_count += 1
                        except Exception as e:
                            print(f"[Scanner] Database error: {e}")
                            error_count += 1
                    else:
                        error_count += 1

                    if on_progress:
                        on_progress(i + 1, to_index_count, parsed.file_name if parsed else "")

        # Prune records for files that were deleted from disk
        if not self._stop_requested:
            if on_status:
                on_status("Pruning removed files from index...")
            existing_set: Set[str] = {str(p.resolve()) for p in all_docx_files}
            pruned_count = self.db.prune_missing_files(existing_set)
        else:
            pruned_count = 0

        elapsed = time.time() - start_time
        self.is_scanning = False

        if on_status:
            on_status(f"Scan finished in {elapsed:.1f}s. {indexed_count} indexed, {skipped_count} up-to-date.")

        return {
            "total_found": total_files,
            "indexed": indexed_count,
            "skipped": skipped_count,
            "pruned": pruned_count,
            "errors": error_count,
            "duration": elapsed
        }

