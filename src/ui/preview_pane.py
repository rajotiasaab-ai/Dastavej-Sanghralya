"""Document Inspector / Preview Pane for Dastavej Sanghralya.
Supports Glassy (inspired by Spicetify Glassy / iOS Flow), Retro, Dark, and Light themes.
"""

import os
import subprocess
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import customtkinter as ctk
from tkinter import messagebox
from src.ui.spinner import LoadingSpinner
from src.ui.theme import get_theme

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
    """Right-side Document Inspector pane with dynamic theme awareness."""

    def __init__(self, parent, theme: Optional[Dict[str, Any]] = None, **kwargs):
        self.theme = theme or getattr(parent, "theme", None) or get_theme("glassy")
        kwargs.setdefault("fg_color", self.theme["preview_bg"])
        kwargs.setdefault("border_width", self.theme["border_width"])
        kwargs.setdefault("border_color", self.theme["preview_border"])
        kwargs.setdefault("corner_radius", self.theme["corner_radius"])
        super().__init__(parent, **kwargs)
        self.current_doc: Optional[Dict[str, Any]] = None
        self._load_token = 0
        self._build_ui()
        self.show_placeholder()

    def _build_ui(self):
        t = self.theme
        radius = t.get("corner_radius", 12)
        btn_rad = 8 if radius > 0 else 0

        # Window Title Bar
        self.preview_titlebar = ctk.CTkFrame(self, fg_color=t["titlebar_bg"], corner_radius=radius, height=24)
        self.preview_titlebar.pack(fill="x", padx=2, pady=(2, 6))

        self.preview_title_lbl = ctk.CTkLabel(
            self.preview_titlebar,
            text=f"{t.get('titlebar_icon', '📄')} DOCUMENT PREVIEW INSPECTOR",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=t["titlebar_fg"]
        )
        self.preview_title_lbl.pack(side="left", padx=6, pady=2)

        # 1. Header Frame (Title + Actions)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=12, pady=(4, 6))

        # Title row
        title_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_row.pack(fill="x")

        # DOCX Badge
        self.icon_badge = ctk.CTkLabel(
            title_row,
            text=" 📄 DOCX ",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color=t["card_badge_bg"],
            border_width=1,
            border_color=t["card_badge_border"],
            text_color=t["card_badge_fg"],
            corner_radius=4 if radius > 0 else 0,
            height=20
        )
        self.icon_badge.pack(side="left", padx=(0, 6))

        self.filename_label = ctk.CTkLabel(
            title_row,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=t["preview_title_fg"],
            anchor="w"
        )
        self.filename_label.pack(side="left", fill="x", expand=True)

        self.path_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=t["preview_path_fg"],
            anchor="w"
        )
        self.path_label.pack(fill="x", pady=(2, 8))

        # Action Buttons Bar
        self.actions_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.actions_frame.pack(fill="x", pady=(0, 8))

        self.btn_open_word = ctk.CTkButton(
            self.actions_frame,
            text="🚀 Open in Word",
            fg_color=t["btn_primary_bg"],
            hover_color=t["btn_primary_hover"],
            border_width=t["border_width"],
            border_color=t["btn_primary_border"],
            text_color=t["btn_primary_fg"],
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=btn_rad,
            command=self._on_open_in_word
        )
        self.btn_open_word.pack(side="left", padx=(0, 6))

        self.btn_reveal = ctk.CTkButton(
            self.actions_frame,
            text="📂 Reveal in Folder",
            fg_color=t["btn_secondary_bg"],
            hover_color=t["btn_secondary_hover"],
            border_width=t["border_width"],
            border_color=t["btn_secondary_border"],
            text_color=t["btn_secondary_fg"],
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=btn_rad,
            command=self._on_reveal_in_explorer
        )
        self.btn_reveal.pack(side="left", padx=(0, 6))

        self.btn_copy_path = ctk.CTkButton(
            self.actions_frame,
            text="📋 Copy Path",
            fg_color=t["btn_secondary_bg"],
            hover_color=t["btn_secondary_hover"],
            border_width=t["border_width"],
            border_color=t["btn_secondary_border"],
            text_color=t["btn_secondary_fg"],
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=btn_rad,
            command=self._on_copy_path
        )
        self.btn_copy_path.pack(side="left")

        # Metadata Strip
        self.meta_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color=t["preview_meta_bg"],
            border_width=1,
            border_color=t["preview_meta_border"],
            corner_radius=btn_rad
        )
        self.meta_frame.pack(fill="x", pady=(0, 6))

        self.meta_info_label = ctk.CTkLabel(
            self.meta_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=t["preview_meta_fg"],
            anchor="w",
            padx=10,
            pady=6
        )
        self.meta_info_label.pack(fill="x")

        # Section Divider
        self.content_title_label = ctk.CTkLabel(
            self,
            text="DOCUMENT CONTENT READING WELL",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=t.get("subbrand_fg", t["titlebar_bg"]),
            anchor="w"
        )
        self.content_title_label.pack(fill="x", padx=12, pady=(4, 2))

        # Processing Circle
        self.spinner = LoadingSpinner(
            self,
            size=44,
            ring_width=4,
            ring_color=t["spinner_ring"],
            track_color=t["spinner_track"],
            text="Retrieving document content...",
            text_size=11,
            bg_color=t["spinner_bg"]
        )

        # Editor-Style Text Preview Box
        self.text_preview = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas" if os.name == "nt" else "Monospace", size=11),
            fg_color=t["preview_text_bg"],
            text_color=t["preview_text_fg"],
            border_width=t["border_width"],
            border_color=t["preview_text_border"],
            corner_radius=btn_rad
        )
        self.text_preview.tag_config("match_hl", background=t["preview_match_hl"], foreground=t["preview_match_hl_fg"])

    def apply_theme(self, theme: Dict[str, Any]):
        self.theme = theme
        t = self.theme
        radius = t.get("corner_radius", 12)
        btn_rad = 8 if radius > 0 else 0

        self.configure(
            fg_color=t["preview_bg"],
            border_color=t["preview_border"],
            border_width=t["border_width"],
            corner_radius=radius
        )
        self.preview_titlebar.configure(fg_color=t["titlebar_bg"], corner_radius=radius)
        self.preview_title_lbl.configure(
            text=f"{t.get('titlebar_icon', '📄')} DOCUMENT PREVIEW INSPECTOR",
            text_color=t["titlebar_fg"]
        )
        self.icon_badge.configure(
            fg_color=t["card_badge_bg"],
            text_color=t["card_badge_fg"],
            border_color=t["card_badge_border"],
            corner_radius=4 if radius > 0 else 0
        )
        self.filename_label.configure(text_color=t["preview_title_fg"])
        self.path_label.configure(text_color=t["preview_path_fg"])

        self.btn_open_word.configure(
            fg_color=t["btn_primary_bg"],
            hover_color=t["btn_primary_hover"],
            border_color=t["btn_primary_border"],
            border_width=t["border_width"],
            text_color=t["btn_primary_fg"],
            corner_radius=btn_rad
        )
        self.btn_reveal.configure(
            fg_color=t["btn_secondary_bg"],
            hover_color=t["btn_secondary_hover"],
            border_color=t["btn_secondary_border"],
            border_width=t["border_width"],
            text_color=t["btn_secondary_fg"],
            corner_radius=btn_rad
        )
        self.btn_copy_path.configure(
            fg_color=t["btn_secondary_bg"],
            hover_color=t["btn_secondary_hover"],
            border_color=t["btn_secondary_border"],
            border_width=t["border_width"],
            text_color=t["btn_secondary_fg"],
            corner_radius=btn_rad
        )

        self.meta_frame.configure(
            fg_color=t["preview_meta_bg"],
            border_color=t["preview_meta_border"],
            corner_radius=btn_rad
        )
        self.meta_info_label.configure(text_color=t["preview_meta_fg"])
        self.content_title_label.configure(text_color=t.get("subbrand_fg", t["titlebar_bg"]))

        self.spinner.apply_theme(t)

        self.text_preview.configure(
            fg_color=t["preview_text_bg"],
            text_color=t["preview_text_fg"],
            border_color=t["preview_text_border"],
            border_width=t["border_width"],
            corner_radius=btn_rad
        )
        self.text_preview.tag_config("match_hl", background=t["preview_match_hl"], foreground=t["preview_match_hl_fg"])

    def show_placeholder(self):
        """Displays empty state when no document is selected."""
        self._load_token += 1
        self.spinner.stop()
        self.spinner.pack_forget()
        self.current_doc = None
        self.icon_badge.pack_forget()
        self.filename_label.configure(text="No Document Selected", text_color=self.theme["preview_title_fg"])
        self.path_label.configure(text="Select any document from the results to inspect content.", text_color=self.theme["preview_path_fg"])
        self.actions_frame.pack_forget()
        self.meta_frame.pack_forget()
        self.content_title_label.pack_forget()
        self.text_preview.pack_forget()

    def show_loading(self, filename: str = "Loading document..."):
        """Displays processing circle instead of full document text."""
        self._load_token += 1
        self.icon_badge.pack(side="left", padx=(0, 6))
        self.filename_label.configure(text=filename, text_color=self.theme["preview_title_fg"])
        self.path_label.configure(text="Retrieving document content...", text_color=self.theme["preview_path_fg"])
        self.actions_frame.pack_forget()
        self.meta_frame.pack_forget()
        self.content_title_label.pack(fill="x", padx=12, pady=(4, 2))
        self.text_preview.pack_forget()

        self.spinner.set_text("Reading document contents...")
        self.spinner.pack(fill="both", expand=True, pady=40)
        self.spinner.start()

    def display_document(self, doc_data: Dict[str, Any], search_term: str = ""):
        """Loads and displays document metadata and extracts text smoothly."""
        self._load_token += 1
        current_token = self._load_token
        self.current_doc = doc_data

        self.icon_badge.pack(side="left", padx=(0, 6))
        self.actions_frame.pack(fill="x", pady=(0, 8))
        self.meta_frame.pack(fill="x", pady=(0, 6))
        self.content_title_label.pack(fill="x", padx=12, pady=(4, 2))

        filename = doc_data.get("filename", "")
        path_str = doc_data.get("path", "")
        file_size = format_file_size(doc_data.get("file_size", 0))
        mtime = format_timestamp(doc_data.get("mtime", 0))
        words = doc_data.get("word_count", 0)
        author = doc_data.get("author", "")
        title = doc_data.get("title", "")

        self.filename_label.configure(text=filename, text_color=self.theme["preview_title_fg"])
        self.path_label.configure(text=path_str, text_color=self.theme["preview_path_fg"])

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
        self.text_preview.pack(fill="both", expand=True, padx=12, pady=(0, 12))

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
        self.btn_copy_path.configure(text="✓ Copied!", fg_color="#008000", text_color="#ffffff")
        self.after(1500, lambda: self.btn_copy_path.configure(
            text=orig_text,
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["btn_secondary_fg"]
        ))
