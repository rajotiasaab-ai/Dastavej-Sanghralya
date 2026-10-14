# 📑 Dastavej Sanghralya (दस्तावेज़ संग्रहालय)

A 100% offline, high-performance desktop application for Windows that indexes and searches all Microsoft Word (`.docx`) documents across your computer like a personal document museum/archive.

---

## 🌟 Key Features

1. **Instant Offline Full-Text Search**:
   - Searches across both **filename** and **full body text** written inside `.docx` files.
   - Built on SQLite **FTS5 (Full-Text Search)** engine with BM25 relevance ranking.
   - Non-blocking background worker thread (zero freezing, smooth 60fps).
   - Rotating processing circle spinner while searching and loading previews.
   - Search term highlighting with contextual snippets.

2. **In-App Document Preview & Quick Actions**:
   - Split-view interface: View full text content without opening Microsoft Word.
   - **Open in Word**: One-click launch in Microsoft Word (`os.startfile`).
   - **Show in Folder**: Opens Windows File Explorer with the exact document selected.
   - **Copy Path**: Copies the full path to clipboard.

3. **High-Speed Streaming XML Parser**:
   - Directly streams `word/document.xml` and metadata from the `.docx` archive.
   - Bypasses slow Office COM automation and runs 15x–30x faster.
   - Extracts Word metadata (Author, Title, Created Date, Word count, File size).

4. **Background Auto-Sync & Real-Time Watching**:
   - Uses `watchdog` to monitor user directories in real time.
   - When a `.docx` file is saved, modified, created, or deleted, the index updates automatically.
   - Incremental caching avoids re-indexing unchanged documents.

5. **Folder Management**:
   - Pre-configured with standard Windows directories (`Documents`, `Downloads`, `Desktop`, `OneDrive`).
   - Interactive dialog to add or remove any custom directory or drive.

6. **Modern Dark & Light Theme**:
   - Powered by **CustomTkinter** for a crisp, responsive native Windows appearance.

---

## 🚀 How to Run

### 1. Single Portable Standalone (.exe) - No Installation Needed
A single, self-contained portable executable:
- **File**: [`dist/Dastavej_Sanghralya.exe`](file:///c:/Users/rajiv/Documents/word%20database/dist/Dastavej_Sanghralya.exe)
- Simply double-click this `.exe` file anywhere on your computer to run immediately.
- Rebuild anytime via [`build_single_exe.bat`](file:///c:/Users/rajiv/Documents/word%20database/build_single_exe.bat) or `python build_single_exe.py`.

---

### 2. Windows Setup Installer (.exe)
If you want to install it with Start Menu and Desktop shortcuts:
- **Installer File**: [`installer_output/Dastavej_Sanghralya_Setup_v1.0.exe`](file:///c:/Users/rajiv/Documents/word%20database/installer_output/Dastavej_Sanghralya_Setup_v1.0.exe)
- Launches the Windows Setup wizard and adds uninstaller in Windows Settings.
- Rebuild anytime via [`build_installer.bat`](file:///c:/Users/rajiv/Documents/word%20database/build_installer.bat) or `python build_installer.py`.

---

### 3. Run Directly from Source (Python)
Double-click [`launch.bat`](file:///c:/Users/rajiv/Documents/word%20database/launch.bat) or run:
```powershell
python run.py
```

---

## 📂 Project Structure

```
word database/
├── src/
│   ├── config.py           # User preferences and default directory configs
│   ├── parser.py           # High-speed XML/ZIP .docx text & metadata extractor
│   ├── database.py         # SQLite connection, FTS5 schema, indexing & search queries
│   ├── scanner.py          # Multi-threaded directory crawler & incremental sync
│   ├── watcher.py          # Real-time watchdog file observer
│   └── ui/
│       ├── app.py          # Main CustomTkinter desktop window & coordinator
│       ├── results_view.py # Document cards list with snippet highlights
│       ├── preview_pane.py # Text preview panel with Word & Explorer action buttons
│       └── folder_dialog.py# Monitored folders configuration modal
├── tests/
│   ├── test_core.py        # Core parser and FTS5 database tests
│   └── test_integration.py # Full integration and real-time watcher test suite
├── data/
│   └── docx_index.db       # Local SQLite FTS5 database file (created automatically)
├── requirements.txt        # Python dependencies
├── run.py                  # Main application launch script
├── launch.bat              # Windows double-click launcher
├── build_exe.py            # PyInstaller build script
└── build_exe.bat           # Windows double-click .exe builder
```

