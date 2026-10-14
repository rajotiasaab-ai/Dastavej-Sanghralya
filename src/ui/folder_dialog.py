"""Hard aesthetic folder management dialog for Dastavej Sanghralya."""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable, List
from src.config import ConfigManager

class FolderManagerDialog(ctk.CTkToplevel):
    """Modal dialog allowing users to add/remove monitored folders with dark aesthetic styling."""

    def __init__(self, parent, config: ConfigManager, on_folders_changed: Callable[[List[str]], None]):
        super().__init__(parent)
        self.config = config
        self.on_folders_changed = on_folders_changed

        self.title("Monitored Folders - Dastavej Sanghralya")
        self.geometry("620x460")
        self.resizable(False, False)
        self.configure(fg_color="#0a0d14")
        
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate_list()

    def _build_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 8))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="📁 Monitored Directories",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#f8fafc"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Dastavej Sanghralya watches these directories and continuously syncs every .docx document.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#64748b"
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        # Scrollable list of folders
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#0d111a",
            border_width=1,
            border_color="#182030",
            corner_radius=10,
            height=260
        )
        self.list_frame.pack(fill="both", expand=True, padx=24, pady=10)

        # Bottom Button Bar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(5, 20))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="＋ Add Monitored Folder",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=36,
            corner_radius=6,
            command=self._on_add_folder
        )
        add_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            fg_color="#1e293b",
            hover_color="#334155",
            text_color="#cbd5e1",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=36,
            width=90,
            corner_radius=6,
            command=self.destroy
        )
        close_btn.pack(side="right")

    def _populate_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        folders = self.config.monitored_folders
        if not folders:
            empty_lbl = ctk.CTkLabel(
                self.list_frame,
                text="No folders configured. Click '＋ Add Monitored Folder' below.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#64748b"
            )
            empty_lbl.pack(pady=50)
            return

        for folder_path in folders:
            item_card = ctk.CTkFrame(
                self.list_frame,
                fg_color="#121622",
                border_width=1,
                border_color="#1e2638",
                corner_radius=8
            )
            item_card.pack(fill="x", pady=4, padx=4)

            icon_lbl = ctk.CTkLabel(item_card, text="📁", font=ctk.CTkFont(size=14))
            icon_lbl.pack(side="left", padx=(12, 4), pady=10)

            path_lbl = ctk.CTkLabel(
                item_card,
                text=folder_path,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#f1f5f9"
            )
            path_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=10)

            del_btn = ctk.CTkButton(
                item_card,
                text="Remove",
                width=72,
                height=26,
                fg_color="#450a0a",
                hover_color="#7f1d1d",
                text_color="#fca5a5",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                corner_radius=4,
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
