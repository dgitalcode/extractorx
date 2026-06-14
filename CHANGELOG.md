# Changelog

All notable changes to **D-GITALCODE ExtractorX** are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [2.0.1] — 2026-06-14

### Changed

- Updated README and portfolio docs with official website: [d-gitalcodema.vercel.app](https://d-gitalcodema.vercel.app/)
- `COMPANY_SITE` in `config.py` aligned with live D-GITALCODE platform URL

---

## [2.0.0] — 2026-06-14

### Added

- Multi-format extraction: DOCX, DOC, PPTX, PPT, PDF
- Layered architecture: GUI → Services → Core → Utils
- Batch processing with threaded worker and cancellation
- SHA-256 duplicate detection with three handling modes
- Per-document output folders with lazy format subdirectories
- Reports: TXT, PDF, Excel, metadata XLSX
- Dashboard with format distribution chart
- Reports gallery with searchable thumbnails
- Extraction history with one-click folder reopen
- Settings persistence (`settings.json`)
- Multilingual UI: EN, FR, AR
- Dark / light themes
- Windows EXE build script (`build_exe.bat`)
- Product documentation suite (`docs/`)

### Changed

- Rebranded from Document Media Extractor Pro to **D-GITALCODE ExtractorX**
- Repository target: [github.com/dgitalcode/extractorx](https://github.com/dgitalcode/extractorx)
- Output folder naming: `Extracted_Images_ExtractorX`
- Company branding: D-GITALCODE / dgitalcode.ma

### Documentation

- Complete README rewrite
- Added `docs/ARCHITECTURE.md`, `docs/SETUP.md`, `docs/API.md`, `docs/SECURITY.md`
- Portfolio screenshots in `docs/screenshots/`

---

## [1.x] — Legacy

Earlier versions were distributed as **D-GITALCODE Document Media Extractor Pro** under a personal GitHub account. See git history after migration for prior changes.

---

<p align="center">
  <strong>D-GITALCODE</strong> — <a href="https://dgitalcode.ma">dgitalcode.ma</a>
</p>
