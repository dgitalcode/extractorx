"""
D-GITALCODE ExtractorX - Settings service.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Persistent user preferences, auto-saved to ``settings.json``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field, fields
from typing import Any, List

import config

REPORT_FORMAT_CHOICES = ("txt", "pdf", "xlsx", "metadata")
DUPLICATE_MODE_CHOICES = ("separate", "skip", "keep")


@dataclass
class AppSettings:
    """User-configurable application settings."""

    output_dir: str = str(config.DEFAULT_OUTPUT_PARENT)
    theme: str = "dark"
    language: str = config.DEFAULT_LANGUAGE
    duplicate_mode: str = "separate"
    report_formats: List[str] = field(
        default_factory=lambda: list(REPORT_FORMAT_CHOICES)
    )


class SettingsService:
    """Load, validate and auto-save application settings."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._settings = self._load()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def update(self, **changes: Any) -> None:
        """Apply ``changes`` to the settings and persist immediately."""
        valid_fields = {f.name for f in fields(AppSettings)}
        for key, value in changes.items():
            if key not in valid_fields:
                self._logger.warning("Unknown setting ignored: %s", key)
                continue
            setattr(self._settings, key, value)
        self._validate()
        self.save()

    def save(self) -> None:
        """Persist settings to disk."""
        try:
            config.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            config.SETTINGS_FILE.write_text(
                json.dumps(asdict(self._settings), indent=2),
                encoding="utf-8",
            )
            self._logger.debug("Settings saved to %s", config.SETTINGS_FILE)
        except OSError as exc:
            self._logger.error("Failed to save settings: %s", exc)

    # ------------------------------------------------------------ internals

    def _load(self) -> AppSettings:
        if not config.SETTINGS_FILE.exists():
            return AppSettings()
        try:
            data = json.loads(config.SETTINGS_FILE.read_text(encoding="utf-8"))
            valid_fields = {f.name for f in fields(AppSettings)}
            self._settings = AppSettings(
                **{k: v for k, v in data.items() if k in valid_fields}
            )
            self._validate()
            return self._settings
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            self._logger.warning("Could not load settings (%s) - using defaults", exc)
            return AppSettings()

    def _validate(self) -> None:
        s = self._settings
        if s.theme not in ("dark", "light"):
            s.theme = "dark"
        if s.duplicate_mode not in DUPLICATE_MODE_CHOICES:
            s.duplicate_mode = "separate"
        s.report_formats = [
            fmt for fmt in s.report_formats if fmt in REPORT_FORMAT_CHOICES
        ]
        if not s.output_dir:
            s.output_dir = str(config.DEFAULT_OUTPUT_PARENT)
