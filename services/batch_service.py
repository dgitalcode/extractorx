"""
D-GITALCODE ExtractorX - Batch service.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Queued, threaded processing of one or many Word documents so the GUI
never blocks.
"""

from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

import config
from core.extractor import ExtractionResult, ExtractionSummary, create_extractor
from core.file_handler import FileHandler
from services.report_service import ReportService
from utils.hash_utils import DuplicateDetector
from utils.path_utils import ensure_directory

FileProgressCallback = Callable[[int, int, str], None]
ImageProgressCallback = Callable[[int], None]
CompletionCallback = Callable[[ExtractionSummary], None]


@dataclass(frozen=True)
class BatchCallbacks:
    """Observer callbacks fired from the worker thread."""

    on_file_progress: Optional[FileProgressCallback] = None
    on_image_extracted: Optional[ImageProgressCallback] = None
    on_complete: Optional[CompletionCallback] = None


class BatchService:
    """Run extraction jobs from a queue on a background worker thread."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._files = FileHandler(logger)
        self._queue: "queue.Queue[Path]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._cancel_event = threading.Event()

    # ------------------------------------------------------------- public

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def collect_documents(self, folder: Path) -> list[Path]:
        """List all supported documents inside ``folder`` (recursive)."""
        return self._files.find_documents(folder)

    def start(
        self,
        documents: Sequence[Path],
        output_dir: Path,
        callbacks: BatchCallbacks,
        duplicate_mode: str = "separate",
        report_formats: Optional[Sequence[str]] = None,
    ) -> bool:
        """Queue ``documents`` and start the background worker.

        Args:
            duplicate_mode: "separate", "skip" or "keep".
            report_formats: Report formats to generate (None = all,
                empty sequence = none).

        Returns:
            False when a batch is already running or nothing was queued.
        """
        if self.is_running:
            self._logger.warning("Batch already in progress - request ignored")
            return False
        if not documents:
            self._logger.warning("No documents to process")
            return False

        self._cancel_event.clear()
        while not self._queue.empty():
            self._queue.get_nowait()
        for document in documents:
            self._queue.put(Path(document))

        self._worker = threading.Thread(
            target=self._run,
            args=(
                len(documents), Path(output_dir), callbacks,
                duplicate_mode, report_formats,
            ),
            daemon=True,
            name="ExtractorX-BatchWorker",
        )
        self._worker.start()
        return True

    def cancel(self) -> None:
        """Request cancellation; the current document finishes first."""
        self._cancel_event.set()
        self._logger.info("Batch cancellation requested")

    # ------------------------------------------------------------ internals

    def _run(
        self,
        total: int,
        output_dir: Path,
        callbacks: BatchCallbacks,
        duplicate_mode: str,
        report_formats: Optional[Sequence[str]],
    ) -> None:
        summary = ExtractionSummary(output_dir=output_dir)
        duplicate_detector = DuplicateDetector(config.HASH_ALGORITHM)
        ensure_directory(output_dir)

        wants_reports = report_formats is None or len(report_formats) > 0
        report_service = ReportService(self._logger) if wants_reports else None

        processed = 0
        extracted_total = 0
        while not self._queue.empty() and not self._cancel_event.is_set():
            document = self._queue.get_nowait()
            processed += 1
            if callbacks.on_file_progress:
                callbacks.on_file_progress(processed, total, document.name)

            def on_image(count_in_file: int, base: int = extracted_total) -> None:
                if callbacks.on_image_extracted:
                    callbacks.on_image_extracted(base + count_in_file)

            try:
                # Route each document to the correct extractor (Word / PPT / PDF).
                extractor = create_extractor(
                    document, output_dir, self._logger,
                    duplicate_detector, duplicate_mode,
                )
            except ValueError as exc:
                self._logger.error("%s", exc)
                summary.add(ExtractionResult(source=document, error=str(exc)))
                continue

            result = extractor.extract(document, progress_callback=on_image)
            extracted_total += result.total_images
            summary.add(result)

            # Per-document reports are written inside each output subfolder
            # so every source file remains a self-contained deliverable package.
            if (
                report_service is not None
                and result.success
                and result.output_folder is not None
            ):
                file_summary = ExtractionSummary(
                    results=[result],
                    started_at=summary.started_at,
                    output_dir=result.output_folder,
                )
                report_service.generate_all(
                    file_summary, result.output_folder, report_formats
                )

        self._logger.info(
            "Batch finished: %d file(s), %d image(s), %d duplicate(s)",
            summary.files_processed, summary.total_images, summary.duplicate_count,
        )
        if callbacks.on_complete:
            callbacks.on_complete(summary)
