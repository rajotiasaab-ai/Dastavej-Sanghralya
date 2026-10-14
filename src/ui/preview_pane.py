"""Hard Aesthetic Document Inspector / Preview Pane for Dastavej Sanghralya.
High-tech dark theme, neon action buttons, metadata chips, and non-blocking preview.
"""

import os
import subprocess
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import customtkinter as ctk
from tkinter import messagebox
from src.ui.spinner import LoadingSpinner

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def format_timestamp(ts: float) -> str:
    try:
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return "Unknown"

class PreviewPane(ctk.CTkFrame):
    """Right-side Document Inspector pane with hard aesthetic styling."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("fg_color", "#0a0d14")
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", "#182030")
        kwargs.setdefault("corner_radius", 12)
        super().__init__(parent, **kwargs)
        self.current_doc: Optional[Dict[str, Any]] = None
        self._load_token = 0
        self._build_ui()
        self.show_placeholder()

    def _build_ui(self):
        # 1. Header Frame (Title + Actions)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(16, 8))

        # Title row
        title_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_row.pack(fill="x")

        self.icon_badge = ctk.CTkLabel(
            title_row,
            text=" 📄 DOCX ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#1e293b",
            text_color="#38bdf8",
            corner_radius=4,
            height=20
        )
        self.icon_badge.pack(side="left", padx=(0, 8))

        self.filename_label = ctk.CTkLabel(
            title_row,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#f8fafc",
            anchor="w"
        )
        self.filename_label.pack(side="left", fill="x", expand=True)

        self.path_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#64748b",
            anchor="w"
        )
        self.path_label.pack(fill="x", pady=(2, 10))

        # Action Buttons Bar
        self.actions_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.actions_frame.pack(fill="x", pady=(0, 10))

        self.btn_open_word = ctk.CTkButton(
            self.actions_frame,
            text="🚀 Open in Word",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            text_color="#ffffff",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=6,
            command=self._on_open_in_word
        )
        self.btn_open_word.pack(side="left", padx=(0, 8))

        self.btn_reveal = ctk.CTkButton(
            self.actions_frame,
            text="📂 Reveal in Folder",
            fg_color="#1e293b",
            hover_color="#334155",
            text_color="#cbd5e1",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=6,
            command=self._on_reveal_in_explorer
        )
        self.btn_reveal.pack(side="left", padx=(0, 8))

        self.btn_copy_path = ctk.CTkButton(
            self.actions_frame,
            text="📋 Copy Path",
            fg_color="#1e293b",
            hover_color="#334155",
            text_color="#cbd5e1",
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=6,
            command=self._on_copy_path
        )
        self.btn_copy_path.pack(side="left")

        # Metadata Chips Strip
        self.meta_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="#111622",
            border_width=1,
            border_color="#1e2536",
            corner_radius=8
        )
        self.meta_frame.pack(fill="x", pady=(0, 8))

        self.meta_info_label = ctk.CTkLabel(
            self.meta_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#94a3b8",
            anchor="w",
            padx=12,
            pady=7
        )
        self.meta_info_label.pack(fill="x")

        # Section Divider
        self.content_title_label = ctk.CTkLabel(
            self,
            text="CONTENT STREAM PREVIEW",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#64748b",
            anchor="w"
        )
        self.content_title_label.pack(fill="x", padx=16, pady=(8, 4))

        # Processing Circle (Neon Spinner)
        self.spinner = LoadingSpinner(
            self,
            size=48,
            ring_width=4,
            ring_color="#00d2ff",
            text="Decrypting and streaming text...",
            text_size=12,
            bg_color="#0a0d14"
        )

        # Editor-Style Text Preview Box
        self.text_preview = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas" if os.name == "nt" else "Monospace", size=12),
            fg_color="#06080d",
            text_color="#e2e8f0",
            border_width=1,
            border_color="#182030",
            corner_radius=8
        )
        self.text_preview.tag_config("match_hl", background="#ca8a04", foreground="#000000")

    def show_placeholder(self):
        """Displays empty state when no document is selected."""
        self._load_token += 1
        self.spinner.stop()
        self.spinner.pack_forget()
        self.current_doc = None
        self.icon_badge.pack_forget()
        self.filename_label.configure(text="No Document Selected")
        self.path_label.configure(text="Select any document from the results to inspect content.")
        self.actions_frame.pack_forget()
        self.meta_frame.pack_forget()
        self.content_title_label.pack_forget()
        self.text_preview.pack_forget()

    def show_loading(self, filename: str = "Loading document..."):
        """Displays processing circle instead of full document text."""
        self._load_token += 1
        self.icon_badge.pack(side="left", padx=(0, 8))
        self.filename_label.configure(text=filename)
        self.path_label.configure(text="Retrieving document content...")
        self.actions_frame.pack_forget()
        self.meta_frame.pack_forget()
        self.content_title_label.pack(fill="x", padx=16, pady=(8, 4))
        self.text_preview.pack_forget()

        self.spinner.set_text("Streaming document contents...")
        self.spinner.pack(fill="both", expand=True, pady=40)
        self.spinner.start()

    def display_document(self, doc_data: Dict[str, Any], search_term: str = ""):
        """Loads and displays document metadata and extracts text smoothly."""
        self._load_token += 1
        current_token = self._load_token
        self.current_doc = doc_data

        self.icon_badge.pack(side="left", padx=(0, 8))
        self.actions_frame.pack(fill="x", pady=(0, 10))
        self.meta_frame.pack(fill="x", pady=(0, 8))
        self.content_title_label.pack(fill="x", padx=16, pady=(8, 4))

        filename = doc_data.get("filename", "")
        path_str = doc_data.get("path", "")
        file_size = format_file_size(doc_data.get("file_size", 0))
        mtime = format_timestamp(doc_data.get("mtime", 0))
        words = doc_data.get("word_count", 0)
        author = doc_data.get("author", "")
        title = doc_data.get("title", "")

        self.filename_label.configure(text=filename)
        self.path_label.configure(text=path_str)

        meta_parts = [
            f"📊 Words: {words:,}",
            f"💾 Size: {file_size}",
            f"🕒 Modified: {mtime}"
        ]
        if author:
            meta_parts.append(f"👤 Author: {author}")
        if title and title != filename:
            meta_parts.append(f"🏷️ Title: {title}")

        self.meta_info_label.configure(text="   •   ".join(meta_parts))

        # Show Processing Circle first
        self.text_preview.pack_forget()
        self.spinner.set_text("Rendering document preview...")
        self.spinner.pack(fill="both", expand=True, pady=30)
        self.spinner.start()

        # Asynchronously render text content in next tick so the UI does not freeze
        self.after(35, lambda: self._render_text_content(current_token, doc_data, search_term))

    def _render_text_content(self, token: int, doc_data: Dict[str, Any], search_term: str):
        if token != self._load_token:
            return

        content = doc_data.get("content", "").strip()
        if not content:
            content = "(This document contains no readable text or is empty)"

        max_chars = 60000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n... [Preview truncated for performance. Click 'Open in Word' to view full document.]"

        self.text_preview.configure(state="normal")
        self.text_preview.delete("1.0", "end")
        self.text_preview.insert("1.0", content)

        if search_term and search_term.strip():
            self._highlight_matches(search_term.strip(), max_matches=40)

        self.text_preview.configure(state="disabled")

        # Hide spinner and show text
        self.spinner.stop()
        self.spinner.pack_forget()
        self.text_preview.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _highlight_matches(self, term: str, max_matches: int = 40):
        query_words = [w for w in term.replace('"', '').split() if len(w) > 1]
        matches_found = 0
        for word in query_words:
            start_pos = "1.0"
            while matches_found < max_matches:
                pos = self.text_preview.search(word, start_pos, stopindex="end", nocase=True)
                if not pos:
                    break
                end_pos = f"{pos}+{len(word)}c"
                self.text_preview.tag_add("match_hl", pos, end_pos)
                start_pos = end_pos
                matches_found += 1

    def _on_open_in_word(self):
        if not self.current_doc:
            return
        path_str = self.current_doc.get("path", "")
        if not Path(path_str).exists():
            messagebox.showerror("File Not Found", f"The file no longer exists at:\n{path_str}", parent=self)
            return

        try:
            os.startfile(path_str)
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Could not launch file:\n{e}", parent=self)

    def _on_reveal_in_explorer(self):
        if not self.current_doc:
            return
        path_str = self.current_doc.get("path", "")
        if not Path(path_str).exists():
            messagebox.showerror("File Not Found", f"The file no longer exists at:\n{path_str}", parent=self)
            return

        try:
            subprocess.Popen(f'explorer /select,"{os.path.normpath(path_str)}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open File Explorer:\n{e}", parent=self)

    def _on_copy_path(self):
        if not self.current_doc:
            return
        path_str = self.current_doc.get("path", "")
        self.clipboard_clear()
        self.clipboard_append(path_str)
        orig_text = self.btn_copy_path.cget("text")
        self.btn_copy_path.configure(text="✓ Copied!", fg_color="#10b981")
        self.after(1500, lambda: self.btn_copy_path.configure(text=orig_text, fg_color="#1e293b"))
