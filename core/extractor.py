"""
D-GITALCODE ExtractorX - Extraction engine.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Modular extractor system:

    BaseExtractor
    ├── WordExtractor        (.docx / .doc)
    ├── PowerPointExtractor  (.pptx / .ppt)
    └── PDFExtractor         (.pdf)

Each document gets its own output folder, format subfolders are created
lazily (only when at least one image of that format exists) and duplicates
are detected via hashing.
"""

from __future__ import annotations

import logging
import time
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, ClassVar, Dict, List, Optional, Tuple, Type

import config
from core.file_handler import FileHandler
from core.image_utils import detect_image_format
from utils.hash_utils import DuplicateDetector
from utils.path_utils import ensure_directory, sanitize_filename, unique_path

ProgressCallback = Callable[[int], None]

# Binary signatures used to carve images out of legacy OLE files (.doc/.ppt).
_LEGACY_SIGNATURES: Tuple[Tuple[bytes, Tuple[bytes, ...]], ...] = (
    (b"\xff\xd8\xff", (b"\xff\xd9",)),                     # JPEG
    (b"\x89PNG\r\n\x1a\n", (b"IEND\xaeB`\x82",)),          # PNG
    (b"GIF89a", (b"\x00;",)),                              # GIF
    (b"GIF87a", (b"\x00;",)),
)


# ================================================================== models

#: Duplicate handling modes: route to DUPLICATES/, skip saving, or keep inline.
DUPLICATE_MODES: Tuple[str, ...] = ("separate", "skip", "keep")


@dataclass(frozen=True)
class ExtractedImage:
    """A single image extracted from a document.

    ``saved_path`` is None when the image was a duplicate and the
    duplicate handling mode is ``"skip"``.
    """

    saved_path: Optional[Path]
    format_folder: str
    size_bytes: int
    sha256: str
    is_duplicate: bool
    source_document: str
    width: int = 0
    height: int = 0


@dataclass
class ExtractionResult:
    """Outcome of extracting a single document."""

    source: Path
    success: bool = False
    images: List[ExtractedImage] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0
    output_folder: Optional[Path] = None

    @property
    def total_images(self) -> int:
        return len(self.images)

    @property
    def duplicate_count(self) -> int:
        return sum(1 for img in self.images if img.is_duplicate)

    @property
    def format_breakdown(self) -> Dict[str, int]:
        """Per-format count of unique images found in this document."""
        breakdown: Dict[str, int] = {}
        for image in self.images:
            if not image.is_duplicate:
                breakdown[image.format_folder] = (
                    breakdown.get(image.format_folder, 0) + 1
                )
        return breakdown


@dataclass
class ExtractionSummary:
    """Aggregated statistics over one or more extraction results."""

    results: List[ExtractionResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    output_dir: Optional[Path] = None

    def add(self, result: ExtractionResult) -> None:
        self.results.append(result)

    @property
    def files_processed(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def files_failed(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def total_images(self) -> int:
        return sum(r.total_images for r in self.results)

    @property
    def duplicate_count(self) -> int:
        return sum(r.duplicate_count for r in self.results)

    @property
    def total_size_bytes(self) -> int:
        return sum(img.size_bytes for r in self.results for img in r.images)

    @property
    def processing_time_seconds(self) -> float:
        return sum(r.duration_seconds for r in self.results)

    @property
    def format_breakdown(self) -> Dict[str, int]:
        breakdown: Dict[str, int] = {}
        for result in self.results:
            for fmt, count in result.format_breakdown.items():
                breakdown[fmt] = breakdown.get(fmt, 0) + count
        return breakdown


# ============================================================== extractors

class BaseExtractor(ABC):
    """Common extraction pipeline for all document types.

    Subclasses only implement :meth:`_read_payloads`, which yields raw
    image bytes for their specific file format.
    """

    #: File extensions handled by the extractor (lowercase, with dot).
    extensions: ClassVar[Tuple[str, ...]] = ()

    def __init__(
        self,
        output_root: Path,
        logger: logging.Logger,
        duplicate_detector: Optional[DuplicateDetector] = None,
        duplicate_mode: str = "separate",
    ) -> None:
        if duplicate_mode not in DUPLICATE_MODES:
            raise ValueError(f"Invalid duplicate mode: {duplicate_mode}")
        self._output_root = Path(output_root)
        self._logger = logger
        self._files = FileHandler(logger)
        self._duplicates = duplicate_detector or DuplicateDetector(
            config.HASH_ALGORITHM
        )
        self._duplicate_mode = duplicate_mode

    # ------------------------------------------------------------- public

    def extract(
        self,
        document: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ExtractionResult:
        """Extract all images from ``document`` into its own subfolder.

        Returns:
            An :class:`ExtractionResult`; failures are captured in
            ``result.error`` rather than raised.
        """
        document = Path(document)
        result = ExtractionResult(source=document)
        start = time.perf_counter()

        try:
            if document.suffix.lower() not in self.extensions:
                raise ValueError(
                    f"{type(self).__name__} cannot handle '{document.suffix}'"
                )
            if not document.is_file():
                raise ValueError(f"File not found: {document}")

            # Dedicated folder per source file (collision-safe).
            doc_folder = unique_path(
                self._output_root / sanitize_filename(document.stem)
            )
            ensure_directory(doc_folder)
            result.output_folder = doc_folder

            for payload in self._read_payloads(document):
                image = self._store_image(
                    payload, doc_folder, document.name,
                    index=len(result.images) + 1,
                )
                if image is not None:
                    result.images.append(image)
                    if progress_callback:
                        progress_callback(len(result.images))

            result.success = True
            self._logger.info(
                "Extracted %d image(s) (%d duplicate(s)) from %s -> %s",
                result.total_images, result.duplicate_count,
                document.name, doc_folder.name,
            )
        except Exception as exc:
            result.error = str(exc)
            self._logger.error("Extraction failed for %s: %s", document, exc)
        finally:
            result.duration_seconds = time.perf_counter() - start

        return result

    # ----------------------------------------------------------- abstract

    @abstractmethod
    def _read_payloads(self, document: Path) -> List[bytes]:
        """Return the raw bytes of every image embedded in ``document``."""

    # ------------------------------------------------------------ shared

    def _read_archive_media(self, document: Path, media_prefix: str) -> List[bytes]:
        """Read media parts from an OOXML ZIP archive (DOCX/PPTX)."""
        if not self._files.validate_office_archive(document):
            raise ValueError(f"Corrupted or invalid file: {document.name}")

        payloads: List[bytes] = []
        with zipfile.ZipFile(document) as archive:
            for entry in archive.namelist():
                if entry.startswith(media_prefix):
                    try:
                        payloads.append(archive.read(entry))
                    except (zipfile.BadZipFile, OSError) as exc:
                        self._logger.warning(
                            "Skipping media part %s: %s", entry, exc
                        )
        return payloads

    def _carve_legacy_payloads(self, document: Path) -> List[bytes]:
        """Scan a legacy OLE binary (.doc/.ppt) for embedded image signatures."""
        try:
            blob = document.read_bytes()
        except OSError as exc:
            raise ValueError(f"Cannot read file: {exc}") from exc

        payloads: List[bytes] = []
        for header, terminators in _LEGACY_SIGNATURES:
            start = 0
            while (start := blob.find(header, start)) != -1:
                end = -1
                for terminator in terminators:
                    end = blob.find(terminator, start + len(header))
                    if end != -1:
                        end += len(terminator)
                        break
                if end == -1:
                    break
                payloads.append(blob[start:end])
                start = end
        self._logger.info(
            "Signature scan found %d candidate image(s) in %s",
            len(payloads), document.name,
        )
        return payloads

    def _store_image(
        self, payload: bytes, doc_folder: Path, source_name: str, index: int
    ) -> Optional[ExtractedImage]:
        """Classify, deduplicate and persist one image payload.

        Format folders are created lazily by ``save_bytes`` - only formats
        that actually occur produce a folder.
        """
        info = detect_image_format(payload)
        if info is None:
            self._logger.warning(
                "Skipping unrecognized media payload (%d bytes) from %s",
                len(payload), source_name,
            )
            return None

        digest, is_duplicate = self._duplicates.register(payload)

        saved_path: Optional[Path] = None
        if is_duplicate and self._duplicate_mode == "skip":
            self._logger.debug("Skipped duplicate image from %s", source_name)
        else:
            if is_duplicate and self._duplicate_mode == "separate":
                folder = config.DUPLICATES_FOLDER
            else:
                folder = info.folder
            filename = f"image_{index:04d}{info.extension}"
            try:
                saved_path = self._files.save_bytes(
                    doc_folder / folder / filename, payload
                )
            except OSError as exc:
                self._logger.error("Failed to save %s: %s", filename, exc)
                return None
            self._logger.debug(
                "Saved %s -> %s/%s (%s)", filename, doc_folder.name, folder,
                "duplicate" if is_duplicate else "unique",
            )

        return ExtractedImage(
            saved_path=saved_path,
            format_folder=info.folder,
            size_bytes=len(payload),
            sha256=digest,
            is_duplicate=is_duplicate,
            source_document=source_name,
            width=info.width,
            height=info.height,
        )


class WordExtractor(BaseExtractor):
    """Extract images from Microsoft Word documents (.docx / .doc)."""

    extensions = (".docx", ".doc")

    def _read_payloads(self, document: Path) -> List[bytes]:
        if document.suffix.lower() == ".docx":
            return self._read_archive_media(document, "word/media/")
        return self._carve_legacy_payloads(document)


class PowerPointExtractor(BaseExtractor):
    """Extract images from PowerPoint presentations (.pptx / .ppt)."""

    extensions = (".pptx", ".ppt")

    def _read_payloads(self, document: Path) -> List[bytes]:
        if document.suffix.lower() == ".pptx":
            return self._read_archive_media(document, "ppt/media/")
        return self._carve_legacy_payloads(document)


class PDFExtractor(BaseExtractor):
    """Extract images from PDF documents via PyMuPDF."""

    extensions = (".pdf",)

    def _read_payloads(self, document: Path) -> List[bytes]:
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise ValueError(
                "PyMuPDF is required for PDF extraction "
                "(pip install PyMuPDF)"
            ) from exc

        payloads: List[bytes] = []
        try:
            with fitz.open(document) as pdf:
                seen_xrefs: set[int] = set()
                for page in pdf:
                    for image_info in page.get_images(full=True):
                        xref = image_info[0]
                        if xref in seen_xrefs:
                            continue
                        seen_xrefs.add(xref)
                        try:
                            extracted = pdf.extract_image(xref)
                        except Exception as exc:
                            self._logger.warning(
                                "Skipping PDF image xref %d: %s", xref, exc
                            )
                            continue
                        if extracted and extracted.get("image"):
                            payloads.append(extracted["image"])
        except Exception as exc:
            raise ValueError(f"Corrupted or unreadable PDF: {exc}") from exc
        return payloads


# ================================================================= factory

_EXTRACTOR_CLASSES: Tuple[Type[BaseExtractor], ...] = (
    WordExtractor,
    PowerPointExtractor,
    PDFExtractor,
)


def supported_extensions() -> Tuple[str, ...]:
    """All file extensions handled by the registered extractors."""
    return tuple(
        ext for cls in _EXTRACTOR_CLASSES for ext in cls.extensions
    )


def create_extractor(
    document: Path,
    output_root: Path,
    logger: logging.Logger,
    duplicate_detector: Optional[DuplicateDetector] = None,
    duplicate_mode: str = "separate",
) -> BaseExtractor:
    """Instantiate the extractor matching ``document``'s file type.

    Raises:
        ValueError: When no registered extractor supports the extension.
    """
    suffix = Path(document).suffix.lower()
    for extractor_class in _EXTRACTOR_CLASSES:
        if suffix in extractor_class.extensions:
            return extractor_class(
                output_root, logger, duplicate_detector, duplicate_mode
            )
    raise ValueError(f"No extractor available for '{suffix}' files")
