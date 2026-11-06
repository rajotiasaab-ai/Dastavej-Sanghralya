"""Retro Design Folder Management Dialog for Dastavej Sanghralya."""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable, List
from src.config import ConfigManager

class FolderManagerDialog(ctk.CTkToplevel):
    """Modal dialog allowing users to add/remove monitored folders with Retro styling."""

    def __init__(self, parent, config: ConfigManager, on_folders_changed: Callable[[List[str]], None]):
        super().__init__(parent)
        self.config = config
        self.on_folders_changed = on_folders_changed

        self.title("Monitored Folders - Dastavej Sanghralya")
        self.geometry("620x480")
        self.resizable(False, False)
        self.configure(fg_color="#d4d4d4")
        
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._populate_list()

    def _build_ui(self):
        # Retro Window Title Bar Strip
        dlg_titlebar = ctk.CTkFrame(self, fg_color="#000080", corner_radius=0, height=24)
        dlg_titlebar.pack(fill="x", padx=4, pady=(4, 8))

        dlg_title_lbl = ctk.CTkLabel(
            dlg_titlebar,
            text="📁 DIRECTORY REPOSITORY MANAGER",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#ffffff"
        )
        dlg_title_lbl.pack(side="left", padx=8, pady=2)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(0, 6))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Monitored Folders",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#000000"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Dastavej Sanghralya watches these directories and continuously indexes every .docx document.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#444444"
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # Scrollable list of folders (White Inset Reading Well)
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#ffffff",
            border_width=2,
            border_color="#808080",
            corner_radius=0,
            height=260
        )
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=8)

        # Bottom Button Bar (Raised 3D Retro Keys)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(6, 16))

        add_btn = ctk.CTkButton(
            btn_frame,
            text="＋ Add Monitored Folder",
            fg_color="#000080",
            hover_color="#0000a0",
            border_width=2,
            border_color="#808080",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=32,
            corner_radius=0,
            command=self._on_add_folder
        )
        add_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            fg_color="#d4d4d4",
            hover_color="#e0e0e0",
            border_width=2,
            border_color="#808080",
            text_color="#000000",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            height=32,
            width=90,
            corner_radius=0,
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
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#666666"
            )
            empty_lbl.pack(pady=50)
            return

        for folder_path in folders:
            item_card = ctk.CTkFrame(
                self.list_frame,
                fg_color="#f8f8f8",
                border_width=1,
                border_color="#808080",
                corner_radius=0
            )
            item_card.pack(fill="x", pady=3, padx=2)

            icon_lbl = ctk.CTkLabel(item_card, text="📁", font=ctk.CTkFont(size=13))
            icon_lbl.pack(side="left", padx=(10, 4), pady=6)

            path_lbl = ctk.CTkLabel(
                item_card,
                text=folder_path,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#000000"
            )
            path_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=6)

            del_btn = ctk.CTkButton(
                item_card,
                text="Remove",
                width=72,
                height=24,
                fg_color="#d4d4d4",
                hover_color="#e0e0e0",
                border_width=2,
                border_color="#808080",
                text_color="#800000",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                corner_radius=0,
                command=lambda p=folder_path: self._on_remove_folder(p)
            )
            del_btn.pack(side="right", padx=8, pady=6)

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
