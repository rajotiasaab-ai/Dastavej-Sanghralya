"""Results View for Dastavej Sanghralya.
Supports Glassy (inspired by Spicetify Glassy / iOS Flow), Retro, Dark, and Light themes.
"""

import os
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional
import customtkinter as ctk
from tkinter import Menu
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
        return dt.strftime("%b %d, %Y")
    except Exception:
        return "Unknown"

class ResultCard(ctk.CTkFrame):
    """Dynamic theme-aware document card."""

    def __init__(
        self,
        parent,
        doc_data: Dict[str, Any],
        on_select: Callable[[Dict[str, Any]], None],
        on_open: Callable[[Dict[str, Any]], None],
        is_selected: bool = False,
        theme: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.theme = theme or getattr(parent, "theme", None) or get_theme("glassy")
        radius = self.theme.get("corner_radius", 12)
        kwargs.setdefault("corner_radius", radius)
        super().__init__(parent, **kwargs)
        self.doc_data = doc_data
        self.on_select = on_select
        self.on_open = on_open
        self.is_selected = is_selected
        self._is_hovered = False

        self._build_ui()
        self._apply_theme_colors()
        self._bind_events()

    def apply_theme(self, theme: Dict[str, Any]):
        self.theme = theme
        radius = self.theme.get("corner_radius", 12)
        self.configure(corner_radius=radius)
        if hasattr(self, "ext_badge"):
            self.ext_badge.configure(
                fg_color=self.theme["card_badge_bg"],
                text_color=self.theme["card_badge_fg"],
                border_color=self.theme["card_badge_border"],
                corner_radius=4 if radius > 0 else 0
            )
        self._apply_theme_colors()

    def _apply_theme_colors(self):
        t = self.theme
        if self.is_selected:
            self.configure(
                fg_color=t["card_selected_bg"],
                border_width=2,
                border_color=t["card_selected_border"]
            )
            if hasattr(self, "title_lbl"):
                self.title_lbl.configure(text_color=t.get("card_selected_fg", t["card_title_fg"]))
            if hasattr(self, "path_lbl"):
                self.path_lbl.configure(text_color=t["card_meta_fg"])
            if hasattr(self, "meta_chip"):
                self.meta_chip.configure(text_color=t["card_badge_bg"])
            if hasattr(self, "snippet_container"):
                self.snippet_container.configure(fg_color=t["snippet_bg"], border_color=t["card_selected_border"])
            if hasattr(self, "snippet_lbl"):
                self.snippet_lbl.configure(text_color=t["snippet_fg"])
        elif self._is_hovered:
            self.configure(
                fg_color=t["card_hover_bg"],
                border_width=1,
                border_color=t["card_hover_border"]
            )
            if hasattr(self, "title_lbl"):
                self.title_lbl.configure(text_color=t.get("card_hover_fg", t["card_title_fg"]))
            if hasattr(self, "path_lbl"):
                self.path_lbl.configure(text_color=t["card_path_fg"])
            if hasattr(self, "meta_chip"):
                self.meta_chip.configure(text_color=t["card_meta_fg"])
            if hasattr(self, "snippet_container"):
                self.snippet_container.configure(fg_color=t["snippet_bg"], border_color=t["snippet_border"])
            if hasattr(self, "snippet_lbl"):
                self.snippet_lbl.configure(text_color=t["snippet_fg"])
        else:
            self.configure(
                fg_color=t["card_bg"],
                border_width=1,
                border_color=t["card_border"]
            )
            if hasattr(self, "title_lbl"):
                self.title_lbl.configure(text_color=t["card_title_fg"])
            if hasattr(self, "path_lbl"):
                self.path_lbl.configure(text_color=t["card_path_fg"])
            if hasattr(self, "meta_chip"):
                self.meta_chip.configure(text_color=t["card_meta_fg"])
            if hasattr(self, "snippet_container"):
                self.snippet_container.configure(fg_color=t["snippet_bg"], border_color=t["snippet_border"])
            if hasattr(self, "snippet_lbl"):
                self.snippet_lbl.configure(text_color=t["snippet_fg"])

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
        t = self.theme
        radius = t.get("corner_radius", 12)
        filename = self.doc_data.get("filename", "Untitled.docx")
        path_str = self.doc_data.get("path", "")
        file_size = format_file_size(self.doc_data.get("file_size", 0))
        mtime = format_timestamp(self.doc_data.get("mtime", 0))
        words = self.doc_data.get("word_count", 0)
        snippet = self.doc_data.get("snippet_text", "")

        # Top row: Filename, Badges, Metrics
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(8, 2))

        # DOCX badge
        self.ext_badge = ctk.CTkLabel(
            top_row,
            text=" DOCX ",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color=t["card_badge_bg"],
            border_width=1,
            border_color=t["card_badge_border"],
            text_color=t["card_badge_fg"],
            corner_radius=4 if radius > 0 else 0,
            height=18
        )
        self.ext_badge.pack(side="left", padx=(0, 6))

        # Document Title
        self.title_lbl = ctk.CTkLabel(
            top_row,
            text=filename,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=t["card_title_fg"],
            anchor="w"
        )
        self.title_lbl.pack(side="left", fill="x", expand=True)

        # Metrics Chip
        self.meta_chip = ctk.CTkLabel(
            top_row,
            text=f"📊 {words:,}w  •  💾 {file_size}  •  🕒 {mtime}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=t["card_meta_fg"]
        )
        self.meta_chip.pack(side="right")

        # Second row: Path
        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.pack(fill="x", padx=12, pady=(0, 4))

        self.path_lbl = ctk.CTkLabel(
            path_row,
            text=f"📁 {path_str}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=t["card_path_fg"],
            anchor="w"
        )
        self.path_lbl.pack(fill="x")

        # Third row: Snippet Box
        if snippet:
            self.snippet_container = ctk.CTkFrame(
                self,
                fg_color=t["snippet_bg"],
                border_width=1,
                border_color=t["snippet_border"],
                corner_radius=6 if radius > 0 else 0
            )
            self.snippet_container.pack(fill="x", padx=12, pady=(2, 8))

            clean_snippet = snippet.replace("«HL»", "「").replace("«/HL»", "」")
            self.snippet_lbl = ctk.CTkLabel(
                self.snippet_container,
                text=f"⚡ {clean_snippet.strip()}",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=t["snippet_fg"],
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
        t = self.theme
        menu = Menu(
            self,
            tearoff=0,
            bg=t.get("menu_dropdown_bg", "#1c140e"),
            fg=t.get("menu_dropdown_fg", "#fff6e8"),
            activebackground=t.get("btn_primary_bg", "#e8b847"),
            activeforeground=t.get("btn_primary_fg", "#140e0a")
        )
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
        theme: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.theme = theme or getattr(parent, "theme", None) or get_theme("glassy")
        kwargs.setdefault("fg_color", self.theme["results_bg"])
        kwargs.setdefault("border_width", self.theme["border_width"])
        kwargs.setdefault("border_color", self.theme["results_border"])
        kwargs.setdefault("corner_radius", self.theme["corner_radius"])
        super().__init__(parent, **kwargs)
        self.on_doc_selected = on_doc_selected
        self.on_doc_open = on_doc_open
        self.cards: List[ctk.CTkBaseClass] = []
        self.selected_doc_id: Optional[int] = None

        # Theme-aware Animated Processing Circle
        self.spinner = LoadingSpinner(
            self,
            size=44,
            ring_width=4,
            ring_color=self.theme["spinner_ring"],
            track_color=self.theme["spinner_track"],
            text="Searching repository in background...",
            text_size=11,
            bg_color=self.theme["spinner_bg"]
        )
        self.is_loading = False

    def apply_theme(self, theme: Dict[str, Any]):
        self.theme = theme
        self.configure(
            fg_color=theme["results_bg"],
            border_color=theme["results_border"],
            border_width=theme["border_width"],
            corner_radius=theme["corner_radius"]
        )
        self.spinner.apply_theme(theme)
        for widget in self.cards:
            if isinstance(widget, ResultCard):
                widget.apply_theme(theme)

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
                text_color=self.theme["card_title_fg"]
            )
            empty_lbl.pack()

            hint_lbl = ctk.CTkLabel(
                empty_container,
                text="Try searching with fewer words, partial terms, or check other monitored folders.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self.theme["card_meta_fg"]
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
                is_selected=(doc_id == self.selected_doc_id),
                theme=self.theme
            )
            card.pack(fill="x", pady=3, padx=4)
            self.cards.append(card)

    def _handle_card_select(self, doc_data: Dict[str, Any]):
        self.selected_doc_id = doc_data.get("id")
        for widget in self.cards:
            if isinstance(widget, ResultCard):
                widget.set_selected(widget.doc_data.get("id") == self.selected_doc_id)
        self.on_doc_selected(doc_data)
