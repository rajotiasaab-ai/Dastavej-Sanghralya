"""Build script to create a standalone Windows .exe using PyInstaller."""

import subprocess
import sys
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def build():
    print("Building standalone Windows executable for Dastavej Sanghralya...")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",                # Onedir mode starts up faster and is more reliable with assets
        "--windowed",              # No console window
        "--name=Dastavej_Sanghralya",
        "--icon=assets/app_icon.ico",
        "--collect-all=customtkinter",
        "--add-data=src;src",
        "--add-data=assets;assets",
        str(ROOT_DIR / "run.py")
    ]
    
    print("Running command:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode == 0:
        dist_path = ROOT_DIR / "dist" / "Dastavej_Sanghralya"
        print(f"\n[SUCCESS] Build completed successfully!")
        print(f"Executable location: {dist_path / 'Dastavej_Sanghralya.exe'}")
    else:
        print(f"\n[ERROR] PyInstaller failed with code {res.returncode}")

if __name__ == "__main__":
    build()

