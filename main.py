"""
D-GITALCODE ExtractorX — Application entry point.

Usage:
    python main.py
"""

from __future__ import annotations

import sys
import traceback

import config
from services.logging_service import LoggingService


def main() -> int:
    """Initialize configuration, logging, and launch the desktop GUI."""
    config.ensure_app_directories()
    config.Translator.load()
    logger = LoggingService.setup(config.LOGS_DIR)

    try:
        from gui.app import MainApplication

        app = MainApplication()
        app.mainloop()
        return 0
    except Exception as exc:
        logger.critical("Fatal error: %s\n%s", exc, traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
