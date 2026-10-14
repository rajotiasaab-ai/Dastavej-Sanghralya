"""Real-time background file system watcher using watchdog.
Automatically indexes added or modified .docx files, and removes deleted ones.
100% offline.
"""

import time
import threading
from pathlib import Path
from typing import List, Callable, Optional, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.parser import DocxParser
from src.database import Database

class DocxFileEventHandler(FileSystemEventHandler):
    """Handles file system events for .docx files with debouncing."""

    def __init__(self, db: Database, on_change_callback: Optional[Callable[[str, str], None]] = None):
        super().__init__()
        self.db = db
        self.on_change_callback = on_change_callback
        # Debounce timer dict: path -> timer
        self._debounce_timers: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def _is_target_docx(self, path_str: str) -> bool:
        p = Path(path_str)
        return p.suffix.lower() == ".docx" and not p.name.startswith("~$")

    def _schedule_index(self, file_path: str):
        with self._lock:
            # Cancel existing timer for this file if active
            if file_path in self._debounce_timers:
                self._debounce_timers[file_path].cancel()

            # Schedule execution after 1.5 seconds to allow Word to finish writing
            t = threading.Timer(1.5, self._execute_index, args=[file_path])
            self._debounce_timers[file_path] = t
            t.daemon = True
            t.start()

    def _execute_index(self, file_path: str):
        with self._lock:
            self._debounce_timers.pop(file_path, None)

        p = Path(file_path)
        if not p.exists():
            return

        try:
            parsed = DocxParser.parse(file_path)
            if not parsed.error:
                changed = self.db.upsert_document(parsed)
                if changed and self.on_change_callback:
                    self.on_change_callback("updated", file_path)
        except Exception as e:
            print(f"[Watcher] Error indexing {file_path}: {e}")

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory and self._is_target_docx(event.src_path):
            self._schedule_index(event.src_path)

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory and self._is_target_docx(event.src_path):
            self._schedule_index(event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory and self._is_target_docx(event.src_path):
            norm_path = str(Path(event.src_path).resolve())
            with self._lock:
                if norm_path in self._debounce_timers:
                    self._debounce_timers[norm_path].cancel()
                    self._debounce_timers.pop(norm_path, None)
            
            removed = self.db.remove_document(norm_path)
            if removed and self.on_change_callback:
                self.on_change_callback("deleted", norm_path)

    def on_moved(self, event: FileSystemEvent):
        if not event.is_directory:
            if self._is_target_docx(event.src_path):
                self.db.remove_document(str(Path(event.src_path).resolve()))
            if self._is_target_docx(event.dest_path):
                self._schedule_index(event.dest_path)


class DocxWatcher:
    """Manages the background Observer watching all monitored folders."""

    def __init__(self, db: Database, on_change: Optional[Callable[[str, str], None]] = None):
        self.db = db
        self.on_change = on_change
        self.observer: Optional[Observer] = None
        self.handler = DocxFileEventHandler(db, on_change)
        self.watched_folders: List[str] = []

    def start(self, folders: List[str]):
        """Starts the observer on the specified list of directory paths."""
        self.stop()
        self.observer = Observer()
        self.watched_folders = []

        for folder_str in folders:
            p = Path(folder_str)
            if p.exists() and p.is_dir():
                try:
                    self.observer.schedule(self.handler, str(p.resolve()), recursive=True)
                    self.watched_folders.append(str(p.resolve()))
                except Exception as e:
                    print(f"[Watcher] Failed to watch {folder_str}: {e}")

        if self.watched_folders:
            self.observer.daemon = True
            self.observer.start()
            print(f"[Watcher] Watching {len(self.watched_folders)} directories in real-time.")

    def stop(self):
        """Stops the observer if currently running."""
        if self.observer and self.observer.is_alive():
            try:
                self.observer.stop()
                self.observer.join(timeout=2.0)
            except Exception as e:
                print(f"[Watcher] Error stopping observer: {e}")
        self.observer = None
        self.watched_folders = []

    def update_folders(self, folders: List[str]):
        """Updates the set of watched folders."""
        self.start(folders)

