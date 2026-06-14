# ExtractorX — System Architecture

**Product:** D-GITALCODE ExtractorX v2.0.0  
**Type:** Desktop application (local processing)  
**Repository:** [github.com/dgitalcode/extractorx](https://github.com/dgitalcode/extractorx)

---

## 1. High-level overview

ExtractorX is a layered Python desktop application. All document processing happens **locally on the user's machine**. There is no network API, no cloud storage integration, and no external upload pipeline in v2.0.

```text
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Desktop)                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ drag & drop / file picker
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  GUI LAYER (CustomTkinter)                                      │
│  app.py · pages.py · components.py · theme.py                   │
│  - Navigation, forms, progress bars, gallery thumbnails         │
│  - Marshals worker-thread callbacks via Tk.after()              │
└───────────────────────────────┬─────────────────────────────────┘
                                │ BatchCallbacks
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  SERVICES LAYER                                                 │
│  batch_service.py · report_service.py · settings_service.py     │
│  history_service.py · logging_service.py                        │
│  - Threaded queue, report generation, persistence               │
└───────────────────────────────┬─────────────────────────────────┘
                                │ create_extractor()
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  CORE LAYER                                                     │
│  extractor.py · file_handler.py · image_utils.py                │
│  - Format-specific engines, safe I/O, image validation          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ SHA-256, paths
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  UTILS LAYER                                                    │
│  hash_utils.py · path_utils.py · format_utils.py                │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LOCAL FILESYSTEM                                               │
│  output/Extracted_Images_ExtractorX/<document>/PNG|JPG|...      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer responsibilities

| Layer | Package | May import | Must not import |
|-------|---------|------------|-----------------|
| GUI | `gui/` | `services/`, `config`, `utils` | — |
| Services | `services/` | `core/`, `utils/`, `config` | `gui/` |
| Core | `core/` | `utils/`, `config` | `gui/`, `services/` |
| Utils | `utils/` | `config` | `gui/`, `services/`, `core/` |

This separation keeps extraction logic testable without launching the GUI.

---

## 3. Frontend / backend separation

ExtractorX uses a **desktop MVC-style split**:

| Concern | Location | Description |
|---------|----------|-------------|
| **View** | `gui/pages.py`, `gui/components.py` | Pages, widgets, tables, gallery |
| **Controller** | `gui/app.py` | Wires UI events to `BatchService`, handles thread → UI marshalling |
| **Model / logic** | `core/`, `services/` | Extraction, batching, reports, settings |

There is no HTTP frontend/backend. The GUI thread is the presentation layer; the batch worker thread is the processing backend.

---

## 4. File processing flow

### 4.1 Single document

```text
Document path
    │
    ▼
create_extractor()          ← selects Word / PowerPoint / PDF engine by extension
    │
    ▼
BaseExtractor.extract()
    │
    ├─ Create per-document output folder (collision-safe name)
    │
    ├─ _read_payloads()     ← format-specific: ZIP media / binary carve / PyMuPDF
    │       │
    │       └── List[bytes] raw image payloads
    │
    └─ For each payload:
            detect_image_format()     ← Pillow validation
            DuplicateDetector.register()  ← SHA-256
            FileHandler.save_bytes()  ← lazy format folder creation
            │
            └── ExtractedImage record
    │
    ▼
ExtractionResult (success/error, images, timing, output_folder)
```

### 4.2 Batch queue

```text
User selects N documents
    │
    ▼
BatchService.start()
    │
    ├─ Spawn daemon worker thread ("ExtractorX-BatchWorker")
    ├─ Shared DuplicateDetector across entire batch
    │
    └─ For each document in queue:
            on_file_progress(current, total, filename)
            extractor.extract() + on_image_extracted(count)
            ReportService.generate_all() per successful document
            (respect cancel_event between documents)
    │
    ▼
on_complete(ExtractionSummary)
    │
    ├─ GUI updates Dashboard + Reports gallery
    └─ HistoryService records the run
```

---

## 5. Extractor engines

| Engine | Extensions | Strategy |
|--------|------------|----------|
| `WordExtractor` | `.docx`, `.doc` | OOXML `word/media/` ZIP entries; legacy binary signature scan |
| `PowerPointExtractor` | `.pptx`, `.ppt` | OOXML `ppt/media/` ZIP entries; legacy binary scan |
| `PDFExtractor` | `.pdf` | PyMuPDF `page.get_images()` + `extract_image(xref)` |

Factory function: `core/extractor.py → create_extractor()`

---

## 6. Output data flow

```text
Upload (local file selection)
    │
    ▼
Processing (in-memory payloads → validated images)
    │
    ▼
Output (filesystem)
    Extracted_Images_ExtractorX/
    └── <document_stem>/
        ├── PNG/  JPG/  GIF/  ...     ← unique images by format
        ├── DUPLICATES/               ← when mode = "separate"
        ├── Extraction_Report.txt
        ├── PDF_Report.pdf
        ├── Excel_Report.xlsx
        └── Metadata.xlsx
```

---

## 7. Cloud integration (future)

**v2.0 has no Cloudinary or cloud storage integration.** All assets are written to the local filesystem.

Planned integrations (see roadmap):

| Integration | Purpose |
|-------------|---------|
| Google Drive / OneDrive | Export output folders to cloud |
| ExtractorX Web API | Remote upload → process → download |
| Object storage (S3/R2) | Backend for web edition |

When a web API is added, the recommended architecture is:

```text
Client → HTTPS upload → API route (Vercel/Node or Python worker)
                              │
                              ▼
                     Object storage (temporary)
                              │
                              ▼
                     Extraction worker (core/ reuse)
                              │
                              ▼
                     ZIP download or storage URL
```

The existing `core/` and `services/` layers are designed to be reusable in a headless/CLI context without the GUI.

---

## 8. Persistence

| File | Location | Contents |
|------|----------|----------|
| `settings.json` | App directory | Theme, language, output path, duplicate mode, report formats |
| `history.json` | `logs/` | Previous extraction runs with timestamps and paths |
| `extraction.log` | `logs/` | Runtime log file |

---

## 9. Threading model

| Thread | Responsibility |
|--------|----------------|
| **Main (Tk)** | UI rendering, user input, `Tk.after()` callbacks from worker |
| **Batch worker** | Document queue, extraction, report generation |

The worker never touches Tk widgets directly. Progress is communicated through `BatchCallbacks` dataclass observers.

---

## 10. Configuration sources

| Source | Priority | Use case |
|--------|----------|----------|
| GUI Settings page | Highest | User preferences |
| `settings.json` | High | Persisted settings |
| `EXTRACTORX_*` env vars | Low | Dev/CI overrides |
| `config.py` constants | Default | Built-in defaults |

---

## 11. Error handling strategy

- **Per-document errors** are captured in `ExtractionResult.error` — the batch continues.
- **Corrupt OOXML** fails `validate_office_archive()` before extraction.
- **Unrecognized image payloads** are skipped with a warning log.
- **Fatal GUI errors** are caught in `main.py` and logged as critical.

---

<p align="center">
  <strong>D-GITALCODE</strong> — <a href="https://dgitalcode.ma">dgitalcode.ma</a>
</p>
