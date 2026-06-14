# ExtractorX — Service API Reference

**D-GITALCODE ExtractorX** is a desktop application. There is **no public HTTP/REST API** in v2.0.

This document describes the **internal service contracts** used between the GUI and processing layers. These interfaces are stable extension points for a future CLI or web API.

---

## Overview

| Service | Module | Purpose |
|---------|--------|---------|
| `BatchService` | `services/batch_service.py` | Threaded multi-document queue |
| `create_extractor` | `core/extractor.py` | Factory for format-specific engines |
| `ReportService` | `services/report_service.py` | TXT/PDF/XLSX report generation |
| `SettingsService` | `services/settings_service.py` | `settings.json` persistence |
| `HistoryService` | `services/history_service.py` | Extraction run history |
| `FileHandler` | `core/file_handler.py` | Safe filesystem operations |

---

## BatchService

### `start(documents, output_dir, callbacks, duplicate_mode, report_formats) → bool`

Queue documents and start the background worker.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `documents` | `Sequence[Path]` | Files to process |
| `output_dir` | `Path` | Parent output directory |
| `callbacks` | `BatchCallbacks` | Progress observers |
| `duplicate_mode` | `str` | `"separate"` \| `"skip"` \| `"keep"` |
| `report_formats` | `Sequence[str]` \| `None` | `"txt"`, `"pdf"`, `"xlsx"`, `"metadata"`; `None` = all |

**Returns:** `False` if a batch is already running or the queue is empty.

**Example:**

```python
from pathlib import Path
from services.batch_service import BatchService, BatchCallbacks
from core.extractor import ExtractionSummary

def on_complete(summary: ExtractionSummary) -> None:
    print(f"Done: {summary.total_images} images")

callbacks = BatchCallbacks(on_complete=on_complete)
service = BatchService(logger)
service.start(
    documents=[Path("report.docx"), Path("slides.pptx")],
    output_dir=Path("output"),
    callbacks=callbacks,
    duplicate_mode="separate",
)
```

### `BatchCallbacks`

| Callback | Signature | When fired |
|----------|-----------|------------|
| `on_file_progress` | `(current: int, total: int, filename: str)` | Before each document |
| `on_image_extracted` | `(count: int)` | After each image saved |
| `on_complete` | `(summary: ExtractionSummary)` | Batch finished |

### `cancel()`

Request graceful cancellation. The current document completes before stopping.

---

## create_extractor

### `create_extractor(document, output_root, logger, duplicate_detector, duplicate_mode) → BaseExtractor`

Select and instantiate the correct extractor by file extension.

**Raises:** `ValueError` if the extension is unsupported.

| Extension | Engine |
|-----------|--------|
| `.docx`, `.doc` | `WordExtractor` |
| `.pptx`, `.ppt` | `PowerPointExtractor` |
| `.pdf` | `PDFExtractor` |

---

## BaseExtractor.extract

### `extract(document, progress_callback=None) → ExtractionResult`

Extract all images from a single document.

**Response structure (`ExtractionResult`):**

```python
@dataclass
class ExtractionResult:
    source: Path
    success: bool
    images: List[ExtractedImage]
    error: Optional[str]       # Set on failure; batch continues
    duration_seconds: float
    output_folder: Optional[Path]
```

**`ExtractedImage` fields:**

| Field | Type | Description |
|-------|------|-------------|
| `saved_path` | `Path \| None` | Disk path; `None` if skipped duplicate |
| `format_folder` | `str` | e.g. `"PNG"`, `"JPG"` |
| `size_bytes` | `int` | Payload size |
| `sha256` | `str` | Content hash |
| `is_duplicate` | `bool` | Duplicate within batch |
| `source_document` | `str` | Original filename |
| `width`, `height` | `int` | Pixel dimensions |

---

## ExtractionSummary

Aggregated batch statistics returned by `on_complete`:

| Property | Type | Description |
|----------|------|-------------|
| `files_processed` | `int` | Successful documents |
| `files_failed` | `int` | Failed documents |
| `total_images` | `int` | All images (incl. duplicates) |
| `duplicate_count` | `int` | Duplicate images detected |
| `processing_time_seconds` | `float` | Sum of per-file durations |
| `format_breakdown` | `Dict[str, int]` | Count per format folder |

---

## ReportService

### `generate_all(summary, output_folder, formats=None) → None`

Generate per-document reports inside `output_folder`.

| Format key | Output file |
|------------|-------------|
| `txt` | `Extraction_Report.txt` |
| `pdf` | `PDF_Report.pdf` |
| `xlsx` | `Excel_Report.xlsx` |
| `metadata` | `Metadata.xlsx` |

---

## SettingsService

### `update(**changes) → None`

Persist settings immediately to `settings.json`.

**Valid fields (`AppSettings`):**

| Field | Type | Default |
|-------|------|---------|
| `output_dir` | `str` | `output/` |
| `theme` | `str` | `"dark"` |
| `language` | `str` | `"EN"` |
| `duplicate_mode` | `str` | `"separate"` |
| `report_formats` | `List[str]` | all formats |

---

## Error handling

| Error type | Behavior |
|------------|----------|
| Unsupported extension | `ValueError` in `create_extractor`; logged; batch continues |
| Corrupt document | `ExtractionResult.error` set; batch continues |
| Unrecognized image payload | Skipped with warning; not added to results |
| Disk write failure | `OSError` logged; image omitted |
| Worker already running | `start()` returns `False` |

Errors are **never silently swallowed** — check `extraction.log` and `ExtractionResult.error`.

---

## Authentication

**Not applicable.** ExtractorX v2.0 has no authentication layer. All processing is local.

A future web API edition would require:

- API key or session auth on upload endpoints
- Rate limiting per tenant
- Temporary signed URLs for download

---

## Future HTTP API (planned)

When implemented, the recommended surface:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/extract` | `POST` | Upload document(s), return job ID |
| `/api/v1/jobs/{id}` | `GET` | Job status and progress |
| `/api/v1/jobs/{id}/download` | `GET` | ZIP of extracted output |

The existing `core/` and `services/` modules are designed to back these endpoints without restructuring.

---

<p align="center">
  <strong>D-GITALCODE</strong> — <a href="https://dgitalcode.ma">dgitalcode.ma</a>
</p>
