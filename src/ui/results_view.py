"""Hard Aesthetic Results View for Dastavej Sanghralya.
High-tech dark theme, neon accents, crisp badges, and smooth non-blocking card list.
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
    """iOS Glassy Flow Document Card with frosted glass surface and responsive hover flow."""

    def __init__(
        self,
        parent,
        doc_data: Dict[str, Any],
        on_select: Callable[[Dict[str, Any]], None],
        on_open: Callable[[Dict[str, Any]], None],
        is_selected: bool = False,
        **kwargs
    ):
        kwargs.setdefault("corner_radius", 14)
        super().__init__(parent, **kwargs)
        self.doc_data = doc_data
        self.on_select = on_select
        self.on_open = on_open
        self.is_selected = is_selected
        self._is_hovered = False

        self._apply_theme_colors()
        self._build_ui()
        self._bind_events()

    def _apply_theme_colors(self):
        if self.is_selected:
            self.configure(
                fg_color="#142340",             # Active Sapphire Glass
                border_width=1.5,
                border_color="#38bdf8"           # Neon Sky Blue Glow
            )
        elif self._is_hovered:
            self.configure(
                fg_color="#121d33",             # Hover Frosted Highlight
                border_width=1,
                border_color="#2b3e60"           # Light Specular Glass Rim
            )
        else:
            self.configure(
                fg_color="#0e1526",             # Deep Frosted Glass
                border_width=1,
                border_color="#1a273e"           # Subtle Specular Glass Edge
            )

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
        top_row.pack(fill="x", padx=14, pady=(10, 2))

        # DOCX badge (Translucent iOS Glass Chip)
        ext_badge = ctk.CTkLabel(
            top_row,
            text=" DOCX ",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color="#182742",
            border_width=1,
            border_color="#253c66",
            text_color="#38bdf8",
            corner_radius=6,
            height=20
        )
        ext_badge.pack(side="left", padx=(0, 8))

        # Document Title
        title_lbl = ctk.CTkLabel(
            top_row,
            text=filename,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#ffffff",
            anchor="w"
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        # Metrics Chip (Frosted Pill)
        meta_chip = ctk.CTkLabel(
            top_row,
            text=f"📊 {words:,}w  •  💾 {file_size}  •  🕒 {mtime}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#94a3b8"
        )
        meta_chip.pack(side="right")

        # Second row: Path
        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.pack(fill="x", padx=14, pady=(0, 4))

        path_lbl = ctk.CTkLabel(
            path_row,
            text=f"📁 {path_str}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#64748b",
            anchor="w"
        )
        path_lbl.pack(fill="x")

        # Third row: Snippet Box (if search terms were matched)
        if snippet:
            snippet_container = ctk.CTkFrame(
                self,
                fg_color="#080c16",
                border_width=1,
                border_color="#162032",
                corner_radius=8
            )
            snippet_container.pack(fill="x", padx=14, pady=(4, 10))

            clean_snippet = snippet.replace("«HL»", "「").replace("«/HL»", "」")
            snippet_lbl = ctk.CTkLabel(
                snippet_container,
                text=f"⚡ {clean_snippet.strip()}",
                font=ctk.CTkFont(family="Segoe UI", size=11, slant="italic"),
                text_color="#cbd5e1",
                anchor="w",
                justify="left",
                wraplength=540,
                padx=10,
                pady=6
            )
            snippet_lbl.pack(fill="x")
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
        menu = Menu(self, tearoff=0, bg="#0e1526", fg="#ffffff", activebackground="#0284c7", activeforeground="#ffffff")
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
        kwargs.setdefault("fg_color", "#0a0f1d")
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", "#162236")
        kwargs.setdefault("corner_radius", 16)
        super().__init__(parent, **kwargs)
        self.on_doc_selected = on_doc_selected
        self.on_doc_open = on_doc_open
        self.cards: List[ctk.CTkBaseClass] = []
        self.selected_doc_id: Optional[int] = None

        # Neon Processing Circle
        self.spinner = LoadingSpinner(
            self,
            size=48,
            ring_width=4,
            ring_color="#00d2ff",
            text="Searching repository in background...",
            text_size=12,
            bg_color="#0a0f1d"
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
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color="#94a3b8"
            )
            empty_lbl.pack()

            hint_lbl = ctk.CTkLabel(
                empty_container,
                text="Try searching with fewer words, partial terms, or check other monitored folders.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#64748b"
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
            card.pack(fill="x", pady=4, padx=6)
            self.cards.append(card)

    def _handle_card_select(self, doc_data: Dict[str, Any]):
        self.selected_doc_id = doc_data.get("id")
        for widget in self.cards:
            if isinstance(widget, ResultCard):
                widget.set_selected(widget.doc_data.get("id") == self.selected_doc_id)
        self.on_doc_selected(doc_data)
