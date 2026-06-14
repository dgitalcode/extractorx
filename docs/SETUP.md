# ExtractorX — Setup Guide

Step-by-step instructions to run **D-GITALCODE ExtractorX** locally.

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.11+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any recent | `git --version` |
| OS | Windows 10+, macOS 12+, Linux | — |

### Windows notes

- Install Python from [python.org](https://www.python.org/downloads/) with **"Add to PATH"** enabled.
- For drag-and-drop, `tkinterdnd2` requires a standard Python install (not minimal/embeddable).

---

## 1. Clone the repository

```bash
git clone https://github.com/dgitalcode/extractorx.git
cd extractorx
```

---

## 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```bat
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

---

## 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Dependency overview

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern Tkinter UI |
| `tkinterdnd2` | Drag-and-drop support |
| `Pillow` | Image format detection |
| `PyMuPDF` | PDF image extraction |
| `openpyxl` | Excel reports |
| `reportlab` | PDF reports |
| `python-docx` | DOCX metadata helpers |

---

## 4. Environment variables (optional)

```bash
cp .env.example .env   # macOS/Linux
copy .env.example .env # Windows
```

| Variable | Example | Effect |
|----------|---------|--------|
| `EXTRACTORX_OUTPUT_DIR` | `C:\ExtractorX\output` | Default output parent |
| `EXTRACTORX_LOG_LEVEL` | `DEBUG` | Verbose logging |

Most settings are configured in the GUI **Settings** page and saved to `settings.json`.

---

## 5. Run the application

```bash
python main.py
```

Expected behavior:

1. Application window opens with D-GITALCODE branding.
2. Default page: **Dashboard** (empty until first extraction).
3. Navigate to **Extract Images** to add documents.

---

## 6. First extraction test

1. Go to **Extract Images**.
2. Drop a sample `.docx` or `.pdf` file.
3. Click **Start extraction**.
4. When complete, open **Reports** to view thumbnails.
5. Click **Open output folder** to verify filesystem output.

Output location (default):

```text
extractorx/output/Extracted_Images_ExtractorX/<document_name>/
```

---

## 7. Build Windows executable

```bat
build_exe.bat
```

Requirements:

- Virtual environment activated (or system Python with PyInstaller)
- `resources/icons/logo.ico` present

Output: `dist\ExtractorX.exe`

Run the EXE from any location. Writable data (`settings.json`, `logs/`, `output/`) is created next to the executable.

---

## 8. Project directories

| Path | Created by | Gitignored |
|------|------------|------------|
| `venv/` | You | Yes |
| `logs/` | App on first run | Contents yes |
| `output/` | App on extraction | Contents yes |
| `settings.json` | App on first settings save | Yes |
| `dist/`, `build/` | PyInstaller | Yes |

---

## Debugging common issues

### `ModuleNotFoundError: No module named 'customtkinter'`

```bash
pip install -r requirements.txt
```

Ensure the virtual environment is activated.

### Drag-and-drop not working

`tkinterdnd2` may be unavailable on some Linux setups. Use **Browse files** instead. Check install:

```bash
pip show tkinterdnd2
```

### PDF extraction fails

```bash
pip install PyMuPDF
```

Verify: `python -c "import fitz; print(fitz.__doc__)"`

### `PermissionError` on output folder

- Choose a writable path in **Settings → Output location**.
- Avoid system-protected directories (e.g. `C:\Program Files`).

### Blank window / Tk errors on Linux

Install Tk bindings:

```bash
# Ubuntu/Debian
sudo apt install python3-tk
```

### Settings not persisting

Check write permissions on the app directory. `settings.json` must be writable.

### Logs

Check `logs/extraction.log` for detailed error traces.

---

## Developer commands

```bash
# Run app
python main.py

# Build EXE (Windows)
build_exe.bat

# Install dev dependency for packaging
pip install pyinstaller
```

---

## Next steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
- Read [API.md](./API.md) for service contracts
- Read [SECURITY.md](./SECURITY.md) before production distribution

---

<p align="center">
  Questions? <a href="mailto:dgitalcode@gmail.com">dgitalcode@gmail.com</a>
</p>
