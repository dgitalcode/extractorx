"""
D-GITALCODE ExtractorX - Logging service.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Central logging configuration with file, console and optional UI handlers.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

import config

UiLogCallback = Callable[[str, str], None]

_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class _UiHandler(logging.Handler):
    """Forward log records to a GUI callback as (message, level)."""

    def __init__(self, callback: UiLogCallback) -> None:
        super().__init__(level=logging.INFO)
        self._callback = callback
        self.setFormatter(logging.Formatter("%(asctime)s - %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._callback(self.format(record), record.levelname.lower())
        except Exception:
            self.handleError(record)


class LoggingService:
    """Application-wide logger factory (singleton-style)."""

    _logger: Optional[logging.Logger] = None
    _ui_handler: Optional[_UiHandler] = None

    @classmethod
    def setup(cls, log_dir: Optional[Path] = None) -> logging.Logger:
        """Initialize the central logger with file and console handlers."""
        if cls._logger is not None:
            return cls._logger

        log_dir = Path(log_dir or config.LOGS_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(config.BRAND)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()

        file_handler = logging.FileHandler(
            log_dir / config.LOG_FILENAME, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(_FORMATTER)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(_FORMATTER)
        logger.addHandler(console_handler)

        cls._logger = logger
        return logger

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Return the central logger, configuring it on first use."""
        return cls._logger if cls._logger is not None else cls.setup()

    @classmethod
    def attach_ui_handler(cls, callback: UiLogCallback) -> None:
        """Stream INFO+ log records to the GUI via ``callback(message, level)``."""
        logger = cls.get_logger()
        if cls._ui_handler is not None:
            logger.removeHandler(cls._ui_handler)
        cls._ui_handler = _UiHandler(callback)
        logger.addHandler(cls._ui_handler)

    @classmethod
    def detach_ui_handler(cls) -> None:
        """Remove the GUI handler (e.g. on window close)."""
        if cls._logger is not None and cls._ui_handler is not None:
            cls._logger.removeHandler(cls._ui_handler)
            cls._ui_handler = None
