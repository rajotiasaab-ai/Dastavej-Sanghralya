"""Retro Design Results View for Dastavej Sanghralya.
Square bevels, white reading wells, raised keys, and smooth non-blocking card list.
"""

import os
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
import customtkinter as ctk
from tkinter import Menu
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
        return dt.strftime("%b %d, %Y")
    except Exception:
        return "Unknown"

class ResultCard(ctk.CTkFrame):
    """Retro Desktop Document Card with square bevels, clear typography, and active highlights."""

    def __init__(
        self,
        parent,
        doc_data: Dict[str, Any],
        on_select: Callable[[Dict[str, Any]], None],
        on_open: Callable[[Dict[str, Any]], None],
        is_selected: bool = False,
        **kwargs
    ):
        kwargs.setdefault("corner_radius", 0)
        super().__init__(parent, **kwargs)
        self.doc_data = doc_data
        self.on_select = on_select
        self.on_open = on_open
        self.is_selected = is_selected
        self._is_hovered = False

        self._build_ui()
        self._apply_theme_colors()
        self._bind_events()

    def _apply_theme_colors(self):
        if self.is_selected:
            self.configure(
                fg_color="#000080",             # Retro Navy Active
                border_width=2,
                border_color="#000000"
            )
            if hasattr(self, "title_lbl"):
                self.title_lbl.configure(text_color="#ffffff")
            if hasattr(self, "path_lbl"):
                self.path_lbl.configure(text_color="#e0e0e0")
            if hasattr(self, "meta_chip"):
                self.meta_chip.configure(text_color="#ffff00")
            if hasattr(self, "snippet_container"):
                self.snippet_container.configure(fg_color="#ffffff", border_color="#000000")
            if hasattr(self, "snippet_lbl"):
                self.snippet_lbl.configure(text_color="#000000")
        elif self._is_hovered:
            self.configure(
                fg_color="#ffffff",             # White Hover Focus
                border_width=1,
                border_color="#000080"           # Navy Border
            )
            if hasattr(self, "title_lbl"):
                self.title_lbl.configure(text_color="#0000ff")  # Retro link hover blue
            if hasattr(self, "path_lbl"):
                self.path_lbl.configure(text_color="#555555")
            if hasattr(self, "meta_chip"):
                self.meta_chip.configure(text_color="#444444")
            if hasattr(self, "snippet_container"):
                self.snippet_container.configure(fg_color="#ffffea", border_color="#c0c090")
            if hasattr(self, "snippet_lbl"):
                self.snippet_lbl.configure(text_color="#000000")
        else:
            self.configure(
                fg_color="#f8f8f8",             # Crisp Off-White Reading Box
                border_width=1,
                border_color="#808080"           # Bevel Dark Grey
            )
            if hasattr(self, "title_lbl"):
                self.title_lbl.configure(text_color="#000000")
            if hasattr(self, "path_lbl"):
                self.path_lbl.configure(text_color="#555555")
            if hasattr(self, "meta_chip"):
                self.meta_chip.configure(text_color="#444444")
            if hasattr(self, "snippet_container"):
                self.snippet_container.configure(fg_color="#ffffea", border_color="#c0c090")
            if hasattr(self, "snippet_lbl"):
                self.snippet_lbl.configure(text_color="#000000")

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._apply_theme_colors()

    def _on_hover_enter(self, event=None):
        if not self.is_selected:
            self._is_hovered = True
            self._apply_theme_colors()

    def _on_hover_leave(self, event=None):
        if not self.is_selected:
            self._is_hovered = False
            self._apply_theme_colors()

    def _build_ui(self):
        filename = self.doc_data.get("filename", "Untitled.docx")
        path_str = self.doc_data.get("path", "")
        file_size = format_file_size(self.doc_data.get("file_size", 0))
        mtime = format_timestamp(self.doc_data.get("mtime", 0))
        words = self.doc_data.get("word_count", 0)
        snippet = self.doc_data.get("snippet_text", "")

        # Top row: Filename, Badges, Metrics
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 2))

        # DOCX badge (Retro Highlight Yellow Chip)
        self.ext_badge = ctk.CTkLabel(
            top_row,
            text=" DOCX ",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color="#ffff00",
            border_width=1,
            border_color="#808080",
            text_color="#000000",
            corner_radius=0,
            height=18
        )
        self.ext_badge.pack(side="left", padx=(0, 6))

        # Document Title
        self.title_lbl = ctk.CTkLabel(
            top_row,
            text=filename,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#000000",
            anchor="w"
        )
        self.title_lbl.pack(side="left", fill="x", expand=True)

        # Metrics Chip
        self.meta_chip = ctk.CTkLabel(
            top_row,
            text=f"📊 {words:,}w  •  💾 {file_size}  •  🕒 {mtime}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#444444"
        )
        self.meta_chip.pack(side="right")

        # Second row: Path
        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.pack(fill="x", padx=10, pady=(0, 4))

        self.path_lbl = ctk.CTkLabel(
            path_row,
            text=f"📁 {path_str}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#555555",
            anchor="w"
        )
        self.path_lbl.pack(fill="x")

        # Third row: Snippet Box (if search terms were matched)
        if snippet:
            self.snippet_container = ctk.CTkFrame(
                self,
                fg_color="#ffffea",
                border_width=1,
                border_color="#c0c090",
                corner_radius=0
            )
            self.snippet_container.pack(fill="x", padx=10, pady=(2, 8))

            clean_snippet = snippet.replace("«HL»", "「").replace("«/HL»", "」")
            self.snippet_lbl = ctk.CTkLabel(
                self.snippet_container,
                text=f"⚡ {clean_snippet.strip()}",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#000000",
                anchor="w",
                justify="left",
                wraplength=540,
                padx=8,
                pady=4
            )
            self.snippet_lbl.pack(fill="x")
        else:
            spacer = ctk.CTkFrame(self, height=4, fg_color="transparent")
            spacer.pack()

    def _bind_events(self):
        # Click to select, Double-click to open
        self.bind("<Button-1>", lambda e: self.on_select(self.doc_data))
        self.bind("<Double-Button-1>", lambda e: self.on_open(self.doc_data))

        # Hover flow bindings
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)

        # Propagate click & hover to children
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda e: self.on_select(self.doc_data))
            child.bind("<Double-Button-1>", lambda e: self.on_open(self.doc_data))
            child.bind("<Enter>", self._on_hover_enter)
            child.bind("<Leave>", self._on_hover_leave)
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e: self.on_select(self.doc_data))
                sub.bind("<Double-Button-1>", lambda e: self.on_open(self.doc_data))
                sub.bind("<Enter>", self._on_hover_enter)
                sub.bind("<Leave>", self._on_hover_leave)

        # Right-click context menu
        self.bind("<Button-3>", self._show_context_menu)
        for child in self.winfo_children():
            child.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        menu = Menu(self, tearoff=0, bg="#d4d4d4", fg="#000000", activebackground="#000080", activeforeground="#ffffff")
        menu.add_command(label="🚀 Open in Word", command=lambda: self.on_open(self.doc_data))
        menu.add_command(label="📂 Show in File Explorer", command=self._reveal_in_explorer)
        menu.add_command(label="📋 Copy Path", command=self._copy_path)
        menu.tk_popup(event.x_root, event.y_root)

    def _reveal_in_explorer(self):
        path_str = self.doc_data.get("path", "")
        if Path(path_str).exists():
            subprocess.Popen(f'explorer /select,"{os.path.normpath(path_str)}"')

    def _copy_path(self):
        path_str = self.doc_data.get("path", "")
        self.clipboard_clear()
        self.clipboard_append(path_str)


class ResultsView(ctk.CTkScrollableFrame):
    """Scrollable list container for ResultCards with LoadingSpinner integration."""

    def __init__(
        self,
        parent,
        on_doc_selected: Callable[[Dict[str, Any]], None],
        on_doc_open: Callable[[Dict[str, Any]], None],
        **kwargs
    ):
        kwargs.setdefault("fg_color", "#ffffff")
        kwargs.setdefault("border_width", 2)
        kwargs.setdefault("border_color", "#808080")
        kwargs.setdefault("corner_radius", 0)
        super().__init__(parent, **kwargs)
        self.on_doc_selected = on_doc_selected
        self.on_doc_open = on_doc_open
        self.cards: List[ctk.CTkBaseClass] = []
        self.selected_doc_id: Optional[int] = None

        # Retro Processing Circle
        self.spinner = LoadingSpinner(
            self,
            size=44,
            ring_width=4,
            ring_color="#000080",
            track_color="#d4d4d4",
            text="Searching repository in background...",
            text_size=11,
            bg_color="#ffffff"
        )
        self.is_loading = False

    def show_loading(self, text: str = "Searching repository in background..."):
        self.is_loading = True
        self._clear_cards()
        self.spinner.set_text(text)
        self.spinner.pack(fill="both", expand=True, pady=60)
        self.spinner.start()

    def hide_loading(self):
        self.is_loading = False
        self.spinner.stop()
        self.spinner.pack_forget()

    def _clear_cards(self):
        for card in self.cards:
            try:
                card.destroy()
            except Exception:
                pass
            self.cards.clear()

    def display_results(self, results: List[Dict[str, Any]]):
        """Renders list of document cards cleanly without freezing."""
        self.hide_loading()
        self._clear_cards()

        if not results:
            empty_container = ctk.CTkFrame(self, fg_color="transparent")
            empty_container.pack(expand=True, pady=60)

            icon_lbl = ctk.CTkLabel(
                empty_container,
                text="🔍",
                font=ctk.CTkFont(size=36)
            )
            icon_lbl.pack(pady=(0, 8))

            empty_lbl = ctk.CTkLabel(
                empty_container,
                text="No documents found matching query.",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color="#000000"
            )
            empty_lbl.pack()

            hint_lbl = ctk.CTkLabel(
                empty_container,
                text="Try searching with fewer words, partial terms, or check other monitored folders.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#555555"
            )
            hint_lbl.pack(pady=(4, 0))

            self.cards.append(empty_container)
            return

        # Render cards
        for doc in results:
            doc_id = doc.get("id")
            card = ResultCard(
                self,
                doc_data=doc,
                on_select=self._handle_card_select,
                on_open=self.on_doc_open,
                is_selected=(doc_id == self.selected_doc_id)
            )
            card.pack(fill="x", pady=3, padx=4)
            self.cards.append(card)

    def _handle_card_select(self, doc_data: Dict[str, Any]):
        self.selected_doc_id = doc_data.get("id")
        for widget in self.cards:
            if isinstance(widget, ResultCard):
                widget.set_selected(widget.doc_data.get("id") == self.selected_doc_id)
        self.on_doc_selected(doc_data)
