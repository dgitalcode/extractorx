"""
D-GITALCODE ExtractorX - Extraction history service.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Stores extraction history locally so users can reopen previous results.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from typing import List

import config
from core.extractor import ExtractionSummary

_MAX_ENTRIES = 50


@dataclass
class HistoryEntry:
    """One past extraction run."""

    date: str = ""
    files: List[str] = field(default_factory=list)
    total_images: int = 0
    duplicates: int = 0
    output_dir: str = ""


class HistoryService:
    """Persist and query the local extraction history (JSON file)."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._entries = self._load()

    @property
    def entries(self) -> List[HistoryEntry]:
        """History entries, most recent first."""
        return list(self._entries)

    def add(self, summary: ExtractionSummary) -> HistoryEntry:
        """Record a finished extraction run and persist the history."""
        entry = HistoryEntry(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            files=[result.source.name for result in summary.results],
            total_images=summary.total_images,
            duplicates=summary.duplicate_count,
            output_dir=str(summary.output_dir) if summary.output_dir else "",
        )
        self._entries.insert(0, entry)
        del self._entries[_MAX_ENTRIES:]
        self._save()
        return entry

    def clear(self) -> None:
        """Erase the stored history."""
        self._entries.clear()
        self._save()

    # ------------------------------------------------------------ internals

    def _load(self) -> List[HistoryEntry]:
        if not config.HISTORY_FILE.exists():
            return []
        try:
            data = json.loads(config.HISTORY_FILE.read_text(encoding="utf-8"))
            valid_fields = {f.name for f in fields(HistoryEntry)}
            return [
                HistoryEntry(**{k: v for k, v in item.items() if k in valid_fields})
                for item in data
            ]
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            self._logger.warning("Could not load history: %s", exc)
            return []

    def _save(self) -> None:
        try:
            config.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            config.HISTORY_FILE.write_text(
                json.dumps([asdict(e) for e in self._entries], indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self._logger.error("Failed to save history: %s", exc)
