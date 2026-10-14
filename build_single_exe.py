"""Builds a 100% single standalone portable Windows .exe file (no installer needed)."""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def build_single_exe():
    print("=================================================================")
    print(" Wrapping Dastavej Sanghralya into a Single Standalone .exe file")
    print("=================================================================")
    
    output_dir = ROOT_DIR / "dist"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",                                   # Single standalone portable executable
        "--windowed",                                  # No console window
        "--name=Dastavej_Sanghralya",                  # Output file: Dastavej_Sanghralya.exe
        "--icon=assets/app_icon.ico",
        "--collect-all=customtkinter",
        "--add-data=src;src",
        "--add-data=assets;assets",
        str(ROOT_DIR / "run.py")
    ]
    
    print("Executing command:\n", " ".join(cmd), "\n")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    
    if res.returncode == 0:
        single_exe = output_dir / "Dastavej_Sanghralya.exe"
        if single_exe.exists():
            size_mb = single_exe.stat().st_size / (1024 * 1024)
            print("\n=================================================================")
            print(" [SUCCESS] Single standalone .exe file created successfully!")
            print(f" File: {single_exe}")
            print(f" Size: {size_mb:.2f} MB")
            print(" You can copy this single .exe file anywhere and double-click to run!")
            print("=================================================================\n")
        else:
            print("[WARNING] Build finished but Dastavej_Sanghralya.exe not found in dist.")
    else:
        print(f"\n[ERROR] PyInstaller failed with exit code {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build_single_exe()

