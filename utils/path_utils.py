"""
D-GITALCODE ExtractorX - Path utilities.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Path normalization, unique-name generation and safe filesystem helpers.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def ensure_directory(directory: Path) -> Path:
    """Create ``directory`` (and parents) if needed and return it."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Strip characters that are invalid in filenames on common platforms."""
    cleaned = _INVALID_FILENAME_CHARS.sub(replacement, name).strip(". ")
    return cleaned or "unnamed"


def unique_path(path: Path) -> Path:
    """Return ``path`` unchanged if free, else append ``_1``, ``_2``, ..."""
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def open_in_file_explorer(directory: Path) -> bool:
    """Open ``directory`` in the platform file explorer.

    Returns:
        True when the command was dispatched successfully.
    """
    directory = Path(directory)
    if not directory.exists():
        return False
    try:
        if sys.platform == "win32":
            os.startfile(directory)  # noqa: S606 - intended behaviour
        elif sys.platform == "darwin":
            subprocess.run(["open", str(directory)], check=False)
        else:
            subprocess.run(["xdg-open", str(directory)], check=False)
        return True
    except OSError:
        return False
