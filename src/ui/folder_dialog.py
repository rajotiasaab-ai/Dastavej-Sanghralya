"""Folder Management Dialog for Dastavej Sanghralya.
Supports Liquid Glass (Apple HIG), Glassy, Retro, Dark, and Light themes.
Features large, clear typography for effortless readability.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable, List, Optional, Dict, Any
from src.config import ConfigManager
from src.ui.theme import get_theme

class FolderManagerDialog(ctk.CTkToplevel):
    """Modal dialog allowing users to add/remove monitored folders with dynamic theme styling and clear typography."""

    def __init__(
        self,
        parent,
        config: ConfigManager,
        on_folders_changed: Callable[[List[str]], None],
        theme: Optional[Dict[str, Any]] = None
    ):
        super().__init__(parent)
        self.config = config
        self.on_folders_changed = on_folders_changed
        self.theme = theme or getattr(parent, "theme", None) or get_theme("liquid_glass")

        self.title("Monitored Folders - Dastavej Sanghralya")
        self.geometry("640x500")
        self.resizable(False, False)
        self.configure(fg_color=self.theme["desktop_bg"])
        
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate_list()

    def _build_ui(self):
        t = self.theme
        radius = t.get("corner_radius", 14)
        btn_rad = 8 if radius > 0 else 0

        # Window Title Bar Strip
        dlg_titlebar = ctk.CTkFrame(self, fg_color=t["titlebar_bg"], corner_radius=radius, height=28)
        dlg_titlebar.pack(fill="x", padx=4, pady=(4, 8))

        dlg_title_lbl = ctk.CTkLabel(
            dlg_titlebar,
            text=f"{t.get('titlebar_icon', '📁')} DIRECTORY REPOSITORY MANAGER",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=t["titlebar_fg"]
        )
        dlg_title_lbl.pack(side="left", padx=8, pady=3)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(0, 6))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Monitored Folders",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=t["preview_title_fg"]
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Dastavej Sanghralya watches these directories and continuously indexes every .docx document.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=t["preview_path_fg"]
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        # Scrollable list of folders
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=t["results_bg"],
            border_width=t["border_width"],
            border_color=t["results_border"],
            corner_radius=radius,
            height=270
        )
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=8)

        # Bottom Button Bar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(6, 16))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="＋ Add Monitored Folder",
            fg_color=t["btn_primary_bg"],
            hover_color=t["btn_primary_hover"],
            border_width=t["border_width"],
            border_color=t["btn_primary_border"],
            text_color=t["btn_primary_fg"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=36,
            corner_radius=btn_rad,
            command=self._on_add_folder
        )
        add_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            fg_color=t["btn_secondary_bg"],
            hover_color=t["btn_secondary_hover"],
            border_width=t["border_width"],
            border_color=t["btn_secondary_border"],
            text_color=t["btn_secondary_fg"],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=36,
            width=90,
            corner_radius=btn_rad,
            command=self.destroy
        )
        close_btn.pack(side="right")

    def _populate_list(self):
        t = self.theme
        radius = t.get("corner_radius", 14)
        btn_rad = 6 if radius > 0 else 0

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        folders = self.config.monitored_folders
        if not folders:
            empty_lbl = ctk.CTkLabel(
                self.list_frame,
                text="No folders configured. Click '＋ Add Monitored Folder' below.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=t["preview_path_fg"]
            )
            empty_lbl.pack(pady=50)
            return

        for folder_path in folders:
            item_card = ctk.CTkFrame(
                self.list_frame,
                fg_color=t["card_bg"],
                border_width=1,
                border_color=t["card_border"],
                corner_radius=btn_rad
            )
            item_card.pack(fill="x", pady=4, padx=2)

            icon_lbl = ctk.CTkLabel(item_card, text="📁", font=ctk.CTkFont(size=14))
            icon_lbl.pack(side="left", padx=(10, 4), pady=8)

            path_lbl = ctk.CTkLabel(
                item_card,
                text=folder_path,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=t["card_title_fg"]
            )
            path_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=8)

            del_btn = ctk.CTkButton(
                item_card,
                text="Remove",
                width=76,
                height=28,
                fg_color=t["btn_secondary_bg"],
                hover_color=t["btn_secondary_hover"],
                border_width=1,
                border_color=t["btn_secondary_border"],
                text_color="#e0574f" if t["appearance_mode"] == "dark" else "#800000",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                corner_radius=btn_rad,
                command=lambda p=folder_path: self._on_remove_folder(p)
            )
            del_btn.pack(side="right", padx=10, pady=8)

    def _on_add_folder(self):
        chosen = filedialog.askdirectory(parent=self, title="Select Directory with Word Documents")
        if chosen:
            added = self.config.add_folder(chosen)
            if added:
                self._populate_list()
                self.on_folders_changed(self.config.monitored_folders)
            else:
                messagebox.showinfo("Already Monitored", "This folder is already in the monitored list.", parent=self)

    def _on_remove_folder(self, folder_path: str):
        confirm = messagebox.askyesno(
            "Remove Folder",
            f"Are you sure you want to stop monitoring this folder?\n\n{folder_path}",
            parent=self
        )
        if confirm:
            self.config.remove_folder(folder_path)
            self._populate_list()
            self.on_folders_changed(self.config.monitored_folders)
