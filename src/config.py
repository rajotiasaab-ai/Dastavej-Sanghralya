"""Configuration manager for the DOCX Database application."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

def get_app_data_dir() -> Path:
    """Determine writable data directory (local data folder or %LOCALAPPDATA%/DOCX_Database)."""
    app_root = Path(__file__).resolve().parent.parent
    local_data = app_root / "data"
    if local_data.exists():
        try:
            test_file = local_data / ".write_test"
            test_file.touch()
            test_file.unlink()
            return local_data
        except Exception:
            pass

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        target = Path(local_app_data) / "Dastavej_Sanghralya"
    else:
        target = Path.home() / ".dastavej_sanghralya"
    target.mkdir(parents=True, exist_ok=True)
    return target

DATA_DIR = get_app_data_dir()
CONFIG_FILE = DATA_DIR / "config.json"
DEFAULT_DB_PATH = DATA_DIR / "docx_index.db"

def get_default_monitored_folders() -> List[str]:
    """Get standard user folders that exist on this Windows machine."""
    home = Path.home()
    folders = []
    
    candidates = [
        home / "Documents",
        home / "Downloads",
        home / "Desktop",
    ]
    
    onedrive = os.environ.get("OneDrive")
    if onedrive and Path(onedrive).exists():
        candidates.append(Path(onedrive))
        
    for candidate in candidates:
        if candidate.exists() and str(candidate) not in folders:
            folders.append(str(candidate.resolve()))
            
    return folders

class ConfigManager:
    """Manages persistent application configuration."""
    
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.config_path = CONFIG_FILE
        self.data: Dict[str, Any] = self._load_default_config()
        self.load()

    def _load_default_config(self) -> Dict[str, Any]:
        return {
            "monitored_folders": get_default_monitored_folders(),
            "excluded_patterns": [
                "~$*",            # Temporary Word lock files
                "*.tmp",
                str(DATA_DIR.resolve()) # Exclude app's own data directory
            ],
            "theme": "dark",      # "dark" or "light" or "system"
            "auto_watch": True,   # Real-time background file watching
            "db_path": str(DEFAULT_DB_PATH.resolve()),
            "max_preview_length": 100000,
        }

    def load(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.data.update(saved)
            except Exception as e:
                print(f"[Config] Error loading config, using defaults: {e}")
        else:
            self.save()

    def save(self) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    @property
    def monitored_folders(self) -> List[str]:
        return self.data.get("monitored_folders", [])

    @monitored_folders.setter
    def monitored_folders(self, folders: List[str]):
        # Ensure all paths are normalized and unique
        clean = []
        for f in folders:
            norm = str(Path(f).resolve())
            if norm not in clean and Path(norm).exists():
                clean.append(norm)
        self.data["monitored_folders"] = clean
        self.save()

    def add_folder(self, folder_path: str) -> bool:
        norm = str(Path(folder_path).resolve())
        if not Path(norm).is_dir():
            return False
        current = self.monitored_folders
        if norm not in current:
            current.append(norm)
            self.monitored_folders = current
            return True
        return False

    def remove_folder(self, folder_path: str) -> bool:
        norm = str(Path(folder_path).resolve())
        current = self.monitored_folders
        if norm in current:
            current.remove(norm)
            self.monitored_folders = current
            return True
        return False

    @property
    def theme(self) -> str:
        return self.data.get("theme", "dark")

    @theme.setter
    def theme(self, theme_name: str):
        self.data["theme"] = theme_name
        self.save()

    @property
    def db_path(self) -> str:
        return self.data.get("db_path", str(DEFAULT_DB_PATH.resolve()))

    @property
    def auto_watch(self) -> bool:
        return self.data.get("auto_watch", True)

    @auto_watch.setter
    def auto_watch(self, value: bool):
        self.data["auto_watch"] = bool(value)
        self.save()

