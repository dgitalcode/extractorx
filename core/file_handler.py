"""
D-GITALCODE ExtractorX - File handling.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Safe file reading/writing, output structure creation and directory traversal.
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from typing import List

import config
from utils.path_utils import ensure_directory, unique_path


class FileHandler:
    """Filesystem operations used by the extraction pipeline."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    # ------------------------------------------------------------- output

    def save_bytes(self, target: Path, data: bytes) -> Path:
        """Write ``data`` to ``target``, avoiding name collisions.

        This is the final persistence step in the upload/processing pipeline.
        Parent folders (e.g. ``PNG/``, ``DUPLICATES/``) are created on demand
        so empty format directories are never written.

        Returns:
            The final path the data was written to.

        Raises:
            OSError: If the file cannot be written.
        """
        target = unique_path(target)
        ensure_directory(target.parent)
        target.write_bytes(data)
        return target

    # ------------------------------------------------------------ documents

    def is_supported_document(self, path: Path) -> bool:
        """True when ``path`` is an existing supported Word document."""
        return (
            path.is_file()
            and path.suffix.lower() in config.SUPPORTED_DOC_EXTENSIONS
        )

    def find_documents(self, folder: Path, recursive: bool = True) -> List[Path]:
        """Collect all supported Word documents inside ``folder``."""
        folder = Path(folder)
        if not folder.is_dir():
            self._logger.error("Not a directory: %s", folder)
            return []
        pattern = folder.rglob("*") if recursive else folder.glob("*")
        documents = sorted(
            p for p in pattern
            if self.is_supported_document(p) and not p.name.startswith("~$")
        )
        self._logger.info("Found %d document(s) in %s", len(documents), folder)
        return documents

    def validate_office_archive(self, path: Path) -> bool:
        """Integrity check for OOXML files (DOCX/PPTX): readable ZIP archive."""
        try:
            with zipfile.ZipFile(path) as archive:
                return "[Content_Types].xml" in archive.namelist()
        except (zipfile.BadZipFile, OSError) as exc:
            self._logger.error("Corrupted or unreadable file %s: %s", path, exc)
            return False
