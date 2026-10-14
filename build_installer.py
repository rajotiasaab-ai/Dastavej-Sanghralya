"""Builds the single Windows Installer .exe for DOCX Database using Inno Setup."""

import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def find_iscc() -> Path:
    # 1. PATH
    which_iscc = shutil.which("iscc") or shutil.which("ISCC.exe")
    if which_iscc:
        return Path(which_iscc)

    # 2. LocalAppData
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        cand = Path(local_appdata) / "Programs" / "Inno Setup 6" / "ISCC.exe"
        if cand.exists():
            return cand

    # 3. Standard Program Files
    for pf in ["ProgramFiles(x86)", "ProgramFiles", "ProgramW6432"]:
        p = os.environ.get(pf)
        if p:
            cand = Path(p) / "Inno Setup 6" / "ISCC.exe"
            if cand.exists():
                return cand

    return None

def build_installer():
    iscc_path = find_iscc()
    if not iscc_path or not iscc_path.exists():
        print("[ERROR] Inno Setup Compiler (ISCC.exe) was not found.")
        sys.exit(1)

    print(f"Using Inno Setup Compiler: {iscc_path}")

    # Check that dist/Dastavej_Sanghralya exists
    dist_dir = ROOT_DIR / "dist" / "Dastavej_Sanghralya"
    if not dist_dir.exists() or not (dist_dir / "Dastavej_Sanghralya.exe").exists():
        print("[INFO] Application binary not found. Running PyInstaller first...")
        subprocess.run([sys.executable, str(ROOT_DIR / "build_exe.py")], check=True, cwd=str(ROOT_DIR))

    iss_file = ROOT_DIR / "installer.iss"
    output_dir = ROOT_DIR / "installer_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Compiling Windows Installer from {iss_file}...")
    cmd = [str(iscc_path), str(iss_file)]
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))

    if res.returncode == 0:
        installer_exe = output_dir / "Dastavej_Sanghralya_Setup_v1.0.exe"
        size_mb = installer_exe.stat().st_size / (1024 * 1024) if installer_exe.exists() else 0
        print("\n=======================================================")
        print(" [SUCCESS] Single Windows Installer created successfully!")
        print(f" File: {installer_exe}")
        print(f" Size: {size_mb:.2f} MB")
        print("=======================================================\n")
    else:
        print(f"\n[ERROR] Inno Setup compilation failed with code {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build_installer()

