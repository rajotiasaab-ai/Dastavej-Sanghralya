"""Hard Aesthetic Desktop Application for Dastavej Sanghralya (दस्तावेज़ संग्रहालय).
100% offline, native desktop interface powered by CustomTkinter.
Features dark cyber-obsidian graphics, neon accents, background search, and keyboard shortcuts.
"""

import os
import sys
import time
import queue
import threading
import subprocess
import colorsys
from pathlib import Path
from typing import Optional, Dict, Any, List

import customtkinter as ctk
from tkinter import messagebox

from src.config import ConfigManager
from src.database import Database
from src.scanner import DirectoryScanner
from src.watcher import DocxWatcher
from src.ui.results_view import ResultsView
from src.ui.preview_pane import PreviewPane
from src.ui.folder_dialog import FolderManagerDialog
from src.ui.spinner import LoadingSpinner

class DocxDatabaseApp(ctk.CTk):
    """Main Application Window for Dastavej Sanghralya."""

    def __init__(self):
        super().__init__()

        # 1. Initialize Core Services (Preserved 100%)
        self.config = ConfigManager()
        self.db = Database(self.config.db_path)
        self.scanner = DirectoryScanner(self.db)
        self.watcher = DocxWatcher(self.db, on_change=self._on_file_changed)

        # 2. Window Configurations & Retro Computing Theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Dastavej Sanghralya - Developed by Anoop Kumar")
        self.geometry("1320x840")
        self.minsize(1020, 640)
        self.configure(fg_color="#008080")

        # Set Window Icon
        icon_candidates = [
            Path(__file__).resolve().parent.parent.parent / "assets" / "app_icon.ico",
            Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico",
            Path(getattr(sys, "_MEIPASS", "")) / "assets" / "app_icon.ico" if hasattr(sys, "_MEIPASS") else None
        ]
        for ic in icon_candidates:
            if ic and ic.exists():
                try:
                    self.iconbitmap(str(ic))
                    break
                except Exception:
                    pass

        # State Variables & Background Search Worker
        self.current_query = ""
        self.current_scope = "all"
        self.current_sort = "rank"
        self._is_scanning = False

        # Asynchronous search pipeline
        self._query_counter = 0
        self._latest_delivered_id = 0
        self._is_typing = False
        self._typing_timer = None
        self._latest_results: Optional[Dict[str, Any]] = None
        self._search_queue: queue.Queue = queue.Queue()

        # Start persistent background search worker thread
        self._search_worker_running = True
        self._search_thread = threading.Thread(target=self._search_worker_loop, daemon=True)
        self._search_thread.start()

        # RGB Lighting Animation State
        self._rgb_hue = 0.0
        self._rgb_running = True
        self._rgb_timer = None

        # 3. Build UI
        self._build_layout()
        self._bind_keyboard_shortcuts()
        self._step_rgb_lights()

        # 4. Start Background Services
        if self.config.auto_watch:
            self.watcher.start(self.config.monitored_folders)

        # Initial data load
        self._update_stats_display()
        self._trigger_background_search(immediate=True)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=280)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_content()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=280,
            corner_radius=0,
            fg_color="#d4d4d4",
            border_width=2,
            border_color="#808080"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
        self.sidebar.grid_rowconfigure(9, weight=1)

        # Retro Window Title Bar
        sb_titlebar = ctk.CTkFrame(self.sidebar, fg_color="#000080", corner_radius=0, height=24)
        sb_titlebar.grid(row=0, column=0, sticky="ew", padx=2, pady=(2, 6))

        sb_title_lbl = ctk.CTkLabel(
            sb_titlebar,
            text="💾 DASTAVEJ CONTROL PANEL",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#ffffff"
        )
        sb_title_lbl.pack(side="left", padx=6, pady=2)

        # App Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=1, column=0, padx=14, pady=(6, 4), sticky="ew")

        brand_lbl = ctk.CTkLabel(
            brand_frame,
            text="📑 DASTAVEJ",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#000000"
        )
        brand_lbl.pack(anchor="w")

        sub_brand_lbl = ctk.CTkLabel(
            brand_frame,
            text="दस्तावेज़ संग्रहालय • Offline Word Hub",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#000080"
        )
        sub_brand_lbl.pack(anchor="w", pady=(1, 0))

        # RGB Developer Credit with Animated Addressable RGB Lights (Beveled Inset Display)
        self.rgb_badge = ctk.CTkFrame(
            brand_frame,
            fg_color="#000000",
            border_width=2,
            border_color="#808080",
            corner_radius=0
        )
        self.rgb_badge.pack(anchor="w", pady=(8, 0))

        # Mini RGB lights strip container
        self.rgb_led_strip = ctk.CTkFrame(self.rgb_badge, fg_color="transparent")
        self.rgb_led_strip.pack(side="left", padx=(8, 4), pady=4)

        self.rgb_leds = []
        for _ in range(3):
            dot = ctk.CTkLabel(
                self.rgb_led_strip,
                text="●",
                font=ctk.CTkFont(family="Segoe UI", size=8, weight="bold"),
                text_color="#ffff00",
                width=10
            )
            dot.pack(side="left", padx=1)
            self.rgb_leds.append(dot)

        self.rgb_dev_lbl = ctk.CTkLabel(
            self.rgb_badge,
            text="Developed by Anoop Kumar",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#ffffff"
        )
        self.rgb_dev_lbl.pack(side="left", padx=(2, 10), pady=4)

        # Real-Time Engine Status Inset Well
        self.status_pill = ctk.CTkFrame(
            self.sidebar,
            fg_color="#ffffff",
            border_width=2,
            border_color="#808080",
            corner_radius=0
        )
        self.status_pill.grid(row=2, column=0, padx=14, pady=(8, 10), sticky="ew")

        self.status_pill_lbl = ctk.CTkLabel(
            self.status_pill,
            text="● LIVE SYNC ACTIVE" if self.config.auto_watch else "○ LIVE SYNC OFF",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#006600" if self.config.auto_watch else "#808080",
            padx=8,
            pady=3
        )
        self.status_pill_lbl.pack(anchor="w")

        # Stats Card (White Inset Reading Well)
        self.stats_card = ctk.CTkFrame(
            self.sidebar,
            fg_color="#ffffff",
            border_width=2,
            border_color="#808080",
            corner_radius=0
        )
        self.stats_card.grid(row=3, column=0, padx=14, pady=4, sticky="ew")

        stats_hdr = ctk.CTkLabel(
            self.stats_card,
            text="INDEX METRICS",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#808080"
        )
        stats_hdr.pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_stat_docs = ctk.CTkLabel(
            self.stats_card,
            text="0 Documents",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#000000",
            anchor="w"
        )
        self.lbl_stat_docs.pack(fill="x", padx=12, pady=(0, 2))

        self.lbl_stat_words = ctk.CTkLabel(
            self.stats_card,
            text="0 total indexed words",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#000080",
            anchor="w"
        )
        self.lbl_stat_words.pack(fill="x", padx=12, pady=(0, 10))

        # Raised 3D Bevel Keys
        self.btn_rescan = ctk.CTkButton(
            self.sidebar,
            text="🔄 Rescan Folders",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=34,
            fg_color="#d4d4d4",
            hover_color="#e6e6e6",
            border_width=2,
            border_color="#808080",
            text_color="#000000",
            corner_radius=0,
            command=self._start_manual_scan
        )
        self.btn_rescan.grid(row=4, column=0, padx=14, pady=(12, 5), sticky="ew")

        self.btn_folders = ctk.CTkButton(
            self.sidebar,
            text="📁 Monitored Folders...",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=34,
            fg_color="#d4d4d4",
            hover_color="#e6e6e6",
            border_width=2,
            border_color="#808080",
            text_color="#000000",
            corner_radius=0,
            command=self._open_folder_dialog
        )
        self.btn_folders.grid(row=5, column=0, padx=14, pady=5, sticky="ew")

        # Auto-watch switch
        self.switch_watch = ctk.CTkSwitch(
            self.sidebar,
            text="Real-time Auto Sync",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#000000",
            progress_color="#000080",
            command=self._on_toggle_auto_watch
        )
        self.switch_watch.grid(row=6, column=0, padx=18, pady=(10, 4), sticky="w")
        if self.config.auto_watch:
            self.switch_watch.select()
        else:
            self.switch_watch.deselect()

        # Keyboard Shortcuts (White Inset Reading Well)
        shortcuts_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="#ffffff",
            border_width=2,
            border_color="#808080",
            corner_radius=0
        )
        self.sidebar.grid_rowconfigure(8, weight=1)
        shortcuts_frame.grid(row=8, column=0, padx=14, pady=(12, 8), sticky="ew")

        sc_title = ctk.CTkLabel(
            shortcuts_frame,
            text="KEYBOARD SHORTCUTS",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#808080"
        )
        sc_title.pack(anchor="w", padx=10, pady=(6, 2))

        sc_list = ctk.CTkLabel(
            shortcuts_frame,
            text="[Ctrl + F]  Focus Search\n[Esc]       Clear Search\n[Enter]     Open in Word\n[↑ / ↓]     Navigate Cards",
            font=ctk.CTkFont(family="Consolas" if os.name == "nt" else "Monospace", size=10),
            text_color="#000000",
            justify="left",
            anchor="w"
        )
        sc_list.pack(anchor="w", padx=10, pady=(0, 6))

        # Bottom Theme selector
        theme_lbl = ctk.CTkLabel(
            self.sidebar,
            text="APPEARANCE:",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#808080"
        )
        theme_lbl.grid(row=10, column=0, padx=16, pady=(0, 2), sticky="w")

        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Light", "Dark", "System"],
            command=self._on_change_theme,
            fg_color="#d4d4d4",
            button_color="#d4d4d4",
            button_hover_color="#e0e0e0",
            dropdown_fg_color="#ffffff",
            dropdown_hover_color="#e0e0e0",
            dropdown_text_color="#000000",
            text_color="#000000",
            height=28,
            corner_radius=0
        )
        self.theme_menu.grid(row=11, column=0, padx=14, pady=(0, 8), sticky="ew")
        self.theme_menu.set("Retro Light")

        # Offline Engine Status
        engine_lbl = ctk.CTkLabel(
            self.sidebar,
            text="🔒 100% Offline Local Engine",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#000000"
        )
        engine_lbl.grid(row=12, column=0, padx=16, pady=(0, 12), sticky="w")

    def _build_main_content(self):
        # Framed Main Window on Teal Desktop
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="#d4d4d4",
            border_width=2,
            border_color="#808080",
            corner_radius=0
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
        self.main_frame.grid_columnconfigure(0, weight=6)
        self.main_frame.grid_columnconfigure(1, weight=4)
        self.main_frame.grid_rowconfigure(3, weight=1)

        # Window Title Bar (Deep Navy with White Text)
        main_titlebar = ctk.CTkFrame(self.main_frame, fg_color="#000080", corner_radius=0, height=24)
        main_titlebar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 6))

        main_title_lbl = ctk.CTkLabel(
            main_titlebar,
            text="📑 DASTAVEJ SANGHRALYA - DOCUMENT ARCHIVE EXPLORER",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#ffffff"
        )
        main_title_lbl.pack(side="left", padx=8, pady=2)

        # 1. Search Bar Command Center (Grey Frame)
        search_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#d4d4d4",
            border_width=1,
            border_color="#808080",
            corner_radius=0
        )
        search_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6))
        search_frame.grid_columnconfigure(0, weight=1)

        # Input container with clear button
        input_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        input_container.grid(row=0, column=0, sticky="ew", padx=(6, 4), pady=6)
        input_container.grid_columnconfigure(0, weight=1)

        # White Inset Reading Well for Search Entry (100% visible black text!)
        self.search_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="🔍 Search document name or content (e.g. invoice, contract, budget)...",
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#ffffff",
            text_color="#000000",
            placeholder_text_color="#808080",
            border_width=2,
            border_color="#808080",
            corner_radius=0
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.configure(border_color="#000080"))
        self.search_entry.bind("<FocusOut>", lambda e: self.search_entry.configure(border_color="#808080"))

        # Clear button [×] (Raised 3D Bevel Key)
        self.btn_clear = ctk.CTkButton(
            input_container,
            text="✕",
            width=28,
            height=28,
            fg_color="#d4d4d4",
            hover_color="#e0e0e0",
            border_width=2,
            border_color="#808080",
            text_color="#000000",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            corner_radius=0,
            command=self._clear_search
        )
        self.btn_clear.grid(row=0, column=1, padx=(4, 0))

        # Scope Segmented Filter Tabs (Classic Bevel Tabs)
        self.scope_segment = ctk.CTkSegmentedButton(
            search_frame,
            values=["⚡ All Fields", "🏷️ Title Only", "📄 Inside Content"],
            command=self._on_scope_chip_changed,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#d4d4d4",
            selected_color="#000080",
            selected_hover_color="#0000aa",
            unselected_color="#d4d4d4",
            unselected_hover_color="#e6e6e6",
            text_color="#ffffff",
            corner_radius=0
        )
        self.scope_segment.grid(row=0, column=1, sticky="e", padx=(0, 6), pady=6)
        self.scope_segment.set("⚡ All Fields")

        # Sort Menu (Classic Grey Dropdown)
        self.sort_menu = ctk.CTkOptionMenu(
            search_frame,
            values=["🎯 Best Match", "🕒 Recent", "🔤 By Name", "📦 By Size"],
            command=self._on_sort_chip_changed,
            height=32,
            width=125,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#d4d4d4",
            button_color="#d4d4d4",
            button_hover_color="#e0e0e0",
            dropdown_fg_color="#ffffff",
            dropdown_hover_color="#e0e0e0",
            dropdown_text_color="#000000",
            text_color="#000000",
            corner_radius=0
        )
        self.sort_menu.grid(row=0, column=2, sticky="e", padx=(0, 8), pady=6)
        self.sort_menu.set("🎯 Best Match")

        # 2. Status & Progress bar (Inset Reading Strip)
        status_bar_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#ffffff",
            border_width=1,
            border_color="#808080",
            corner_radius=0
        )
        status_bar_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 6))

        self.status_lbl = ctk.CTkLabel(
            status_bar_frame,
            text="Ready • Type to search documents",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#000000",
            anchor="w",
            padx=8,
            pady=3
        )
        self.status_lbl.pack(side="left")

        self.scan_progress = ctk.CTkProgressBar(
            status_bar_frame,
            height=4,
            width=200,
            progress_color="#000080",
            fg_color="#d4d4d4"
        )
        self.scan_progress.set(0)

        # 3. Main Split View: Results List (Left) and Preview Pane (Right)
        self.results_view = ResultsView(
            self.main_frame,
            on_doc_selected=self._on_select_document,
            on_doc_open=self._on_open_document,
            fg_color="#ffffff",
            border_color="#808080",
            border_width=2,
            corner_radius=0
        )
        self.results_view.grid(row=3, column=0, sticky="nsew", padx=(8, 4), pady=(0, 8))

        self.preview_pane = PreviewPane(
            self.main_frame,
            fg_color="#d4d4d4",
            border_color="#808080",
            border_width=2,
            corner_radius=0
        )
        self.preview_pane.grid(row=3, column=1, sticky="nsew", padx=(4, 8), pady=(0, 8))

    def _bind_keyboard_shortcuts(self):
        """Binds intuitive keyboard navigation for frictionless operation."""
        # Focus search bar
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-F>", lambda e: self._focus_search())
        # Clear search
        self.bind("<Escape>", lambda e: self._clear_search())

    def _focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, "end")

    def _clear_search(self):
        self.search_entry.delete(0, "end")
        self._on_search_key_release()
        self.search_entry.focus_set()

    # --- Asynchronous Background Search Engine (100% Preserved) ---

    def _search_worker_loop(self):
        """Dedicated background thread executing database queries without freezing the GUI."""
        while self._search_worker_running:
            try:
                item = self._search_queue.get()
                if item is None:
                    break

                query_id, query, scope, sort_by = item

                # Coalesce queue: skip directly to latest query if user is typing rapidly
                while not self._search_queue.empty():
                    try:
                        next_item = self._search_queue.get_nowait()
                        if next_item is None:
                            return
                        if next_item[0] > query_id:
                            query_id, query, scope, sort_by = next_item
                    except queue.Empty:
                        break

                start_t = time.time()
                try:
                    results, total_cnt = self.db.search_documents(
                        query_str=query,
                        scope=scope,
                        sort_by=sort_by,
                        limit=50
                    )
                except Exception as e:
                    results, total_cnt = [], 0
                    print(f"[SearchWorker] Database query error: {e}")

                elapsed = time.time() - start_t

                if self._search_worker_running:
                    self.after(0, lambda qid=query_id, res=results, cnt=total_cnt, el=elapsed:
                        self._on_background_search_done(qid, res, cnt, el)
                    )

            except Exception as e:
                print(f"[SearchWorker] Unexpected error in worker: {e}")

    def _on_search_key_release(self, event=None):
        self._trigger_background_search(immediate=False)

    def _trigger_background_search(self, immediate: bool = False):
        self._query_counter += 1
        query_id = self._query_counter
        query = self.search_entry.get().strip()
        self.current_query = query

        # 1. Immediately dispatch query to background worker
        self._search_queue.put((query_id, query, self.current_scope, self.current_sort))

        # 2. Immediate trigger (e.g. startup or filter change)
        if immediate:
            self._is_typing = False
            self.results_view.show_loading("Loading repository documents...")
            self.status_lbl.configure(text="Loading repository...")
            return

        # 3. User is actively typing
        self._is_typing = True
        self.results_view.show_loading("Searching repository in background...")
        self.status_lbl.configure(text="Searching in background...")

        # 4. Debounce display: when typing stops (300ms pause), show results
        if self._typing_timer:
            self.after_cancel(self._typing_timer)
        self._typing_timer = self.after(300, self._on_typing_stopped)

    def _on_typing_stopped(self):
        self._is_typing = False
        if self._latest_results and self._latest_results["query_id"] == self._query_counter:
            self._commit_results_to_ui(self._latest_results)
        else:
            self.results_view.show_loading("Finalizing results...")

    def _on_background_search_done(self, query_id: int, results: list, total_cnt: int, elapsed: float):
        if query_id < self._latest_delivered_id:
            return  # Discard obsolete results

        self._latest_delivered_id = query_id
        self._latest_results = {
            "query_id": query_id,
            "results": results,
            "total_cnt": total_cnt,
            "elapsed": elapsed
        }

        if not self._is_typing:
            self._commit_results_to_ui(self._latest_results)

    def _commit_results_to_ui(self, res_data: dict):
        results = res_data["results"]
        total_cnt = res_data["total_cnt"]
        elapsed = res_data["elapsed"]
        query = self.current_query

        self.results_view.display_results(results)

        if query:
            self.status_lbl.configure(text=f"Found {total_cnt} match(es) in {elapsed:.3f}s")
        else:
            self.status_lbl.configure(text=f"Repository Library: {total_cnt} documents indexed")

        if results:
            first_doc_summary = results[0]
            doc_id = first_doc_summary.get("id")
            if doc_id:
                full_doc = self.db.get_document_by_id(doc_id)
                if full_doc:
                    self.preview_pane.display_document(full_doc, search_term=query)
        else:
            self.preview_pane.show_placeholder()

    def _on_scope_chip_changed(self, value: str):
        scope_map = {
            "⚡ All Fields": "all",
            "🏷️ Title Only": "title",
            "📄 Inside Content": "content"
        }
        self.current_scope = scope_map.get(value, "all")
        self._trigger_background_search(immediate=True)

    def _on_sort_chip_changed(self, value: str):
        sort_map = {
            "🎯 Best Match": "rank",
            "🕒 Recent": "date",
            "🔤 By Name": "name",
            "📦 By Size": "size"
        }
        self.current_sort = sort_map.get(value, "rank")
        self._trigger_background_search(immediate=True)

    def _on_select_document(self, doc_summary: Dict[str, Any]):
        doc_id = doc_summary.get("id")
        if doc_id:
            full_doc = self.db.get_document_by_id(doc_id)
            if full_doc:
                self.preview_pane.display_document(full_doc, search_term=self.current_query)

    def _on_open_document(self, doc_data: Dict[str, Any]):
        path_str = doc_data.get("path", "")
        if Path(path_str).exists():
            os.startfile(path_str)
        else:
            messagebox.showerror("File Not Found", f"The file no longer exists at:\n{path_str}", parent=self)

    # --- Scanning & Auto-Sync (100% Preserved) ---

    def _start_manual_scan(self):
        if self._is_scanning:
            return

        self._is_scanning = True
        self.btn_rescan.configure(state="disabled", text="Scanning...")
        self.scan_progress.pack(side="right", padx=10)
        self.scan_progress.set(0)

        def run_scan():
            def on_progress(current, total, filename):
                frac = current / total if total > 0 else 0
                self.after(0, lambda: self._update_scan_progress(frac, f"Indexing {current}/{total}: {filename}"))

            def on_status(msg):
                self.after(0, lambda: self.status_lbl.configure(text=msg))

            summary = self.scanner.scan_folders(
                self.config.monitored_folders,
                on_progress=on_progress,
                on_status=on_status
            )
            self.after(0, lambda: self._on_scan_completed(summary))

        threading.Thread(target=run_scan, daemon=True).start()

    def _update_scan_progress(self, frac: float, msg: str):
        self.scan_progress.set(frac)
        self.status_lbl.configure(text=msg)

    def _on_scan_completed(self, summary: Dict[str, Any]):
        self._is_scanning = False
        self.btn_rescan.configure(state="normal", text="🔄 Rescan Folders")
        self.scan_progress.pack_forget()

        self._update_stats_display()
        self._trigger_background_search(immediate=True)

        indexed = summary.get("indexed", 0)
        skipped = summary.get("skipped", 0)
        pruned = summary.get("pruned", 0)
        dur = summary.get("duration", 0)
        self.status_lbl.configure(
            text=f"Scan complete in {dur:.1f}s. Indexed: {indexed}, Up-to-date: {skipped}, Pruned: {pruned}."
        )

    def _update_stats_display(self):
        stats = self.db.get_stats()
        docs = stats.get("total_docs", 0)
        words = stats.get("total_words", 0)
        self.lbl_stat_docs.configure(text=f"{docs:,} Documents")
        self.lbl_stat_words.configure(text=f"{words:,} total indexed words")

    def _on_file_changed(self, event_type: str, file_path: str):
        def safe_refresh():
            self._update_stats_display()
            self._trigger_background_search(immediate=True)
        self.after(0, safe_refresh)

    def _on_toggle_auto_watch(self):
        val = bool(self.switch_watch.get())
        self.config.auto_watch = val
        if val:
            self.watcher.start(self.config.monitored_folders)
            self.status_pill.configure(fg_color="#ffffff", border_color="#808080")
            self.status_pill_lbl.configure(text="● LIVE SYNC ACTIVE", text_color="#006600")
        else:
            self.watcher.stop()
            self.status_pill.configure(fg_color="#d4d4d4", border_color="#808080")
            self.status_pill_lbl.configure(text="○ LIVE SYNC OFF", text_color="#808080")

    def _open_folder_dialog(self):
        FolderManagerDialog(self, self.config, on_folders_changed=self._on_folders_updated)

    def _on_folders_updated(self, new_folders: List[str]):
        if self.config.auto_watch:
            self.watcher.update_folders(new_folders)
        self._start_manual_scan()

    def _on_change_theme(self, choice: str):
        theme_str = choice.lower()
        self.config.theme = theme_str
        ctk.set_appearance_mode(theme_str)
        try:
            self.search_entry.configure(text_color="#000000", placeholder_text_color="#808080")
        except Exception:
            pass

    def _step_rgb_lights(self):
        if not getattr(self, "_rgb_running", False) or not self.winfo_exists():
            return

        self._rgb_hue = (self._rgb_hue + 0.007) % 1.0

        # Dynamic rainbow RGB wave across LEDs
        led_colors = []
        for i in range(len(self.rgb_leds)):
            h = (self._rgb_hue + i * 0.12) % 1.0
            r, g, b = colorsys.hsv_to_rgb(h, 0.90, 1.0)
            led_colors.append(f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}")

        # Text glow color (vibrant, luminous RGB)
        h_text = (self._rgb_hue + 0.06) % 1.0
        rt, gt, bt = colorsys.hsv_to_rgb(h_text, 0.70, 1.0)
        text_color = f"#{int(rt*255):02x}{int(gt*255):02x}{int(bt*255):02x}"

        try:
            for dot, col in zip(self.rgb_leds, led_colors):
                dot.configure(text_color=col)
            self.rgb_badge.configure(border_color=led_colors[0])
            self.rgb_dev_lbl.configure(text_color=text_color)
        except Exception:
            pass

        self._rgb_timer = self.after(45, self._step_rgb_lights)

    def _on_close(self):
        self._rgb_running = False
        if getattr(self, "_rgb_timer", None):
            try:
                self.after_cancel(self._rgb_timer)
            except Exception:
                pass
        self._search_worker_running = False
        try:
            self._search_queue.put(None)
        except Exception:
            pass
        self.watcher.stop()
        self.scanner.stop()
        self.destroy()
