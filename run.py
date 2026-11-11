"""Main launch script for the DOCX Database Windows Application.
100% Offline.
"""

import sys
import os
from pathlib import Path

# Ensure root folder is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Enable Per-Monitor High-DPI awareness on Windows for crystal-clear, non-blurry fonts and graphics
if sys.platform.startswith("win"):
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
    except Exception:
        pass

from src.ui.app import DocxDatabaseApp

def main():
    try:
        app = DocxDatabaseApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(err_msg)
        try:
            from tkinter import messagebox
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Dastavej Sanghralya - Startup Error", f"An error occurred:\n\n{err_msg}")
            root.destroy()
        except Exception:
            pass
        if sys.stdin and not getattr(sys.stdin, "closed", True):
            try:
                input("Press Enter to exit...")
            except Exception:
                pass

if __name__ == "__main__":
    main()

