"""
D-GITALCODE ExtractorX — Application configuration.

Product: D-GITALCODE ExtractorX
Site:    https://dgitalcode.ma

Central configuration: application metadata, filesystem layout, supported
formats, and translation loading.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Final, Tuple

# ---------------------------------------------------------------- metadata

APP_NAME: Final[str] = "D-GITALCODE ExtractorX"
PRODUCT_NAME: Final[str] = "ExtractorX"
APP_VERSION: Final[str] = "2.0.0"
APP_DISPLAY_VERSION: Final[str] = "v2.0.0"
BRAND: Final[str] = "D-GITALCODE"
COMPANY_SITE: Final[str] = "https://dgitalcode.ma"
COMPANY_EMAIL: Final[str] = "dgitalcode@gmail.com"
COPYRIGHT: Final[str] = f"{BRAND} © 2026 | {COMPANY_SITE}"

# Optional environment overrides (desktop app — settings.json is primary).
ENV_OUTPUT_DIR: Final[str] = "EXTRACTORX_OUTPUT_DIR"
ENV_LOG_LEVEL: Final[str] = "EXTRACTORX_LOG_LEVEL"

# ---------------------------------------------------------------- filesystem
# When frozen as a PyInstaller EXE, bundled resources live in _MEIPASS while
# writable data (settings, logs, output) sits next to the executable.

_IS_FROZEN: Final[bool] = bool(getattr(sys, "frozen", False))
BASE_DIR: Final[Path] = (
    Path(getattr(sys, "_MEIPASS", "")) if _IS_FROZEN
    else Path(__file__).resolve().parent
)
APP_DIR: Final[Path] = (
    Path(sys.executable).resolve().parent if _IS_FROZEN
    else Path(__file__).resolve().parent
)

RESOURCES_DIR: Final[Path] = BASE_DIR / "resources"
ICONS_DIR: Final[Path] = RESOURCES_DIR / "icons"
LANGUAGES_DIR: Final[Path] = RESOURCES_DIR / "languages"
LOGO_PNG: Final[Path] = ICONS_DIR / "logo.png"
LOGO_ICO: Final[Path] = ICONS_DIR / "logo.ico"
LOGS_DIR: Final[Path] = APP_DIR / "logs"
DEFAULT_OUTPUT_PARENT: Final[Path] = Path(
    os.environ.get(ENV_OUTPUT_DIR, str(APP_DIR / "output"))
)
SETTINGS_FILE: Final[Path] = APP_DIR / "settings.json"
HISTORY_FILE: Final[Path] = LOGS_DIR / "history.json"

OUTPUT_FOLDER_NAME: Final[str] = "Extracted_Images_ExtractorX"
DUPLICATES_FOLDER: Final[str] = "DUPLICATES"
LOG_FILENAME: Final[str] = "extraction.log"

# Per-document report filenames (each source file gets its own reports).
REPORT_TXT_FILENAME: Final[str] = "Extraction_Report.txt"
REPORT_PDF_FILENAME: Final[str] = "PDF_Report.pdf"
REPORT_XLSX_FILENAME: Final[str] = "Excel_Report.xlsx"
REPORT_METADATA_FILENAME: Final[str] = "Metadata.xlsx"

# ---------------------------------------------------------------- formats

SUPPORTED_IMAGE_FORMATS: Final[Tuple[str, ...]] = (
    "JPG", "PNG", "GIF", "BMP", "TIFF", "WEBP",
)
SUPPORTED_DOC_EXTENSIONS: Final[Tuple[str, ...]] = (
    ".docx", ".doc", ".pptx", ".ppt", ".pdf",
)
HASH_ALGORITHM: Final[str] = "sha256"

DEFAULT_LANGUAGE: Final[str] = "EN"


def ensure_app_directories() -> None:
    """Create all directories the application relies on at startup."""
    for directory in (
        RESOURCES_DIR, ICONS_DIR, LANGUAGES_DIR, LOGS_DIR, DEFAULT_OUTPUT_PARENT
    ):
        directory.mkdir(parents=True, exist_ok=True)


class Translator:
    """Load and serve UI translations from ``resources/languages/*.json``."""

    _translations: Dict[str, Dict[str, str]] = {}
    _current: str = DEFAULT_LANGUAGE

    @classmethod
    def load(cls) -> None:
        """Load every available language file into memory."""
        cls._translations.clear()
        for lang_file in sorted(LANGUAGES_DIR.glob("*.json")):
            try:
                data = json.loads(lang_file.read_text(encoding="utf-8"))
                cls._translations[lang_file.stem.upper()] = data
            except (OSError, json.JSONDecodeError):
                continue

    @classmethod
    def set_language(cls, code: str) -> None:
        if code.upper() in cls._translations:
            cls._current = code.upper()

    @classmethod
    def available_languages(cls) -> Tuple[str, ...]:
        return tuple(cls._translations.keys()) or (DEFAULT_LANGUAGE,)

    @classmethod
    def text(cls, key: str) -> str:
        """Return the translation for ``key`` (falls back to EN, then key)."""
        lang = cls._translations.get(cls._current, {})
        fallback = cls._translations.get(DEFAULT_LANGUAGE, {})
        return lang.get(key, fallback.get(key, key))
