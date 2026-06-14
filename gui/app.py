"""
D-GITALCODE ExtractorX - Main application window.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Professional desktop shell: left sidebar navigation, compact header,
swappable workspace pages and a discreet status bar. All extraction work
runs on the BatchService worker thread; UI updates are marshalled back
through ``Tk.after`` so the interface never blocks. Supports drag & drop
of documents via tkinterdnd2 when available.
"""

from __future__ import annotations

import queue
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Dict, List, Optional

import customtkinter as ctk

import config
from core.extractor import ExtractionSummary
from gui.components import Header, Sidebar, StatusBar, show_error_dialog
from gui.pages import (
    DashboardPage,
    ExtractPage,
    HistoryPage,
    ReportsPage,
    SettingsPage,
)
from gui.theme import COLOR, ThemeManager
from services.batch_service import BatchCallbacks, BatchService
from services.history_service import HistoryEntry, HistoryService
from services.logging_service import LoggingService
from services.settings_service import SettingsService
from utils.format_utils import format_duration
from utils.path_utils import open_in_file_explorer

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    class _AppBase(ctk.CTk, TkinterDnD.DnDWrapper):
        """CTk window with native drag & drop support."""

    _DND_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _AppBase = ctk.CTk  # type: ignore[assignment,misc]
    _DND_AVAILABLE = False

_NAV_ITEMS = (
    ("dashboard", "\u25a4", "Dashboard"),
    ("extract", "\u2913", "Extract Images"),
    ("history", "\u21ba", "History"),
    ("reports", "\u25a6", "Reports"),
    ("settings", "\u2699", "Settings"),
)

_PAGE_TITLES = {
    "dashboard": "Dashboard",
    "extract": "Extract Images",
    "history": "History",
    "reports": "Reports",
    "settings": "Settings",
}


class MainApplication(_AppBase):
    """Top-level window of the D-GITALCODE ExtractorX."""

    def __init__(self) -> None:
        self._logger = LoggingService.get_logger()
        self._settings_service = SettingsService(self._logger)
        settings = self._settings_service.settings
        config.Translator.set_language(settings.language)

        self._theme = ThemeManager(settings.theme)
        self._theme.apply()
        super().__init__()

        self.title(f"{config.APP_NAME} {config.APP_DISPLAY_VERSION}")
        self.geometry("1160x780")
        self.minsize(980, 680)
        self.configure(fg_color=COLOR["bg"])
        self._apply_window_icon()
        self._setup_drag_and_drop()

        self._batch = BatchService(self._logger)
        self._history_service = HistoryService(self._logger)
        self._documents: List[Path] = []
        self._output_dir: Optional[Path] = None

        # Thread-safe bridge: worker threads enqueue UI actions, the main
        # loop drains the queue. Never touch Tk from a worker thread.
        self._ui_queue: "queue.Queue[Callable[[], None]]" = queue.Queue()
        self._poll_ui_queue()

        self._build_shell()
        self.navigate("extract")
        LoggingService.attach_ui_handler(self._on_log_record)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._logger.info(
            "%s %s started%s",
            config.APP_NAME, config.APP_DISPLAY_VERSION,
            "" if _DND_AVAILABLE else " (drag & drop unavailable)",
        )

    # ------------------------------------------------------------ UI setup

    def _apply_window_icon(self) -> None:
        """Set the D-GITALCODE logo as window/taskbar icon.

        CustomTkinter re-applies its own icon ~200 ms after startup on
        Windows, so ours is scheduled right after that.
        """
        if not config.LOGO_ICO.exists():
            return

        def set_icon() -> None:
            try:
                self.iconbitmap(str(config.LOGO_ICO))
            except Exception:
                self._logger.warning("Could not apply window icon")

        set_icon()
        self.after(300, set_icon)

    def _setup_drag_and_drop(self) -> None:
        """Register the whole window as a drop target for documents."""
        if not _DND_AVAILABLE:
            return
        try:
            self.TkdndVersion = TkinterDnD._require(self)
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception as exc:
            self._logger.warning("Drag & drop initialization failed: %s", exc)

    def _build_shell(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._sidebar = Sidebar(self, _NAV_ITEMS, on_navigate=self.navigate)
        self._sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")

        self._header = Header(
            self,
            on_theme_toggle=self._on_theme_toggle,
            on_open_settings=lambda: self.navigate("settings"),
        )
        self._header.grid(row=0, column=1, sticky="ew")

        workspace = ctk.CTkFrame(self, fg_color=COLOR["bg"], corner_radius=0)
        workspace.grid(row=1, column=1, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(0, weight=1)

        self._status_bar = StatusBar(self)
        self._status_bar.grid(row=2, column=1, sticky="ew")

        # Pages stacked in the same cell; navigation lifts the active one.
        self._pages: Dict[str, ctk.CTkFrame] = {}

        self._dashboard = DashboardPage(workspace)
        self._extract = ExtractPage(
            workspace,
            on_browse_files=self._on_browse_files,
            on_browse_folder=self._on_browse_folder,
            on_start=self._on_start,
            on_cancel=self._on_cancel,
            on_clear=self._on_clear,
            on_open_output=self._on_open_output,
        )
        self._history_page = HistoryPage(
            workspace,
            on_open=self._on_open_history_entry,
            on_clear=self._on_clear_history,
        )
        self._history_page.set_entries(self._history_service.entries)
        self._reports = ReportsPage(workspace, on_open_path=self._open_path)
        self._settings_page = SettingsPage(
            workspace,
            settings=self._settings_service.settings,
            languages=config.Translator.available_languages(),
            on_change=self._on_setting_changed,
            on_browse_output=self._browse_output_directory,
        )

        for key, page in (
            ("dashboard", self._dashboard),
            ("extract", self._extract),
            ("history", self._history_page),
            ("reports", self._reports),
            ("settings", self._settings_page),
        ):
            page.grid(row=0, column=0, sticky="nsew",
                      padx=24, pady=(16, 16))
            self._pages[key] = page

    # ---------------------------------------------------------- navigation

    def navigate(self, key: str) -> None:
        """Show the page identified by ``key``."""
        page = self._pages.get(key)
        if page is None:
            return
        page.lift()
        self._sidebar.set_active(key)
        self._header.set_title(_PAGE_TITLES.get(key, ""))

    # ----------------------------------------------------------- selection

    def _on_browse_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select Documents",
            filetypes=[
                ("Supported Documents", "*.docx *.doc *.pptx *.ppt *.pdf"),
                ("Word Documents", "*.docx *.doc"),
                ("PowerPoint Presentations", "*.pptx *.ppt"),
                ("PDF Documents", "*.pdf"),
                ("All Files", "*.*"),
            ],
        )
        if paths:
            self._set_documents([Path(p) for p in paths])

    def _on_browse_folder(self) -> None:
        path = filedialog.askdirectory(title="Select Folder of Documents")
        if not path:
            return
        documents = self._batch.collect_documents(Path(path))
        if not documents:
            self._header.set_status("No supported documents found in folder")
            return
        self._set_documents(documents)

    def _on_drop(self, event: object) -> None:
        """Handle files dropped onto the window."""
        if self._batch.is_running:
            return
        try:
            raw_paths = self.tk.splitlist(event.data)  # type: ignore[attr-defined]
        except Exception:
            return

        documents: List[Path] = []
        for raw in raw_paths:
            path = Path(raw)
            if path.is_dir():
                documents.extend(self._batch.collect_documents(path))
            elif path.suffix.lower() in config.SUPPORTED_DOC_EXTENSIONS:
                documents.append(path)
            else:
                self._logger.warning("Ignored unsupported drop: %s", path.name)

        if not documents:
            self._header.set_status("Dropped items contain no supported documents")
            return
        self._logger.info("%d document(s) received via drag & drop",
                          len(documents))
        self._set_documents(documents)

    def _set_documents(self, documents: List[Path]) -> None:
        self._documents = documents
        self._extract.set_files(documents)
        self._extract.start_button.configure(state="normal")
        self._header.set_status(f"{len(documents)} file(s) ready")
        self.navigate("extract")

    # ----------------------------------------------------------- execution

    def _on_start(self) -> None:
        if not self._documents or self._batch.is_running:
            return

        settings = self._settings_service.settings
        self._output_dir = (
            Path(settings.output_dir) / config.OUTPUT_FOLDER_NAME
        )
        self._set_busy(True)
        self._extract.progress.reset()
        self._header.set_status("Extracting\u2026", busy=True)

        started = self._batch.start(
            documents=self._documents,
            output_dir=self._output_dir,
            callbacks=BatchCallbacks(
                on_file_progress=self._on_file_progress,
                on_image_extracted=self._on_image_extracted,
                on_complete=self._on_batch_complete,
            ),
            duplicate_mode=settings.duplicate_mode,
            report_formats=settings.report_formats,
        )
        if not started:
            self._set_busy(False)
            self._header.set_status("Ready")

    def _on_cancel(self) -> None:
        self._batch.cancel()
        self._header.set_status("Cancelling\u2026", busy=True)

    def _on_clear(self) -> None:
        if self._batch.is_running:
            return
        self._documents = []
        self._extract.clear_files()
        self._extract.start_button.configure(state="disabled")
        self._extract.open_output_button.configure(state="disabled")
        self._extract.progress.reset()
        self._extract.log.clear()
        self._reports.clear()
        self._header.set_status("Ready")

    def _on_open_output(self) -> None:
        if self._output_dir is None or not open_in_file_explorer(self._output_dir):
            show_error_dialog("Output folder not found.", title="Not Found")

    def _open_path(self, path: Path) -> None:
        if not open_in_file_explorer(path):
            show_error_dialog("File not found.", title="Not Found")

    def _on_close(self) -> None:
        if self._batch.is_running:
            self._batch.cancel()
        LoggingService.detach_ui_handler()
        self.destroy()

    # ------------------------------------------------------------ settings

    def _on_theme_toggle(self) -> None:
        mode = self._theme.toggle()
        self._settings_service.update(theme=mode)
        self._dashboard.refresh_theme()
        self._logger.info("Theme switched to %s mode", mode)

    def _on_setting_changed(self, key: str, value: object) -> None:
        self._settings_service.update(**{key: value})
        if key == "theme" and isinstance(value, str):
            self._theme.set_mode(value)
            self._dashboard.refresh_theme()

    def _browse_output_directory(self) -> Optional[str]:
        return filedialog.askdirectory(title="Select Output Directory") or None

    # ------------------------------------------------------------- history

    def _on_open_history_entry(self, entry: HistoryEntry) -> None:
        if not entry.output_dir or not open_in_file_explorer(Path(entry.output_dir)):
            show_error_dialog(
                "The output folder of this run no longer exists.",
                title="Not Found",
            )

    def _on_clear_history(self) -> None:
        self._history_service.clear()
        self._history_page.set_entries([])

    # -------------------------------------------- worker thread callbacks
    # These run on the BatchService worker thread and must marshal UI
    # updates onto the Tk main loop via the UI queue.

    def _poll_ui_queue(self) -> None:
        """Drain pending UI actions posted from worker threads."""
        try:
            while True:
                action = self._ui_queue.get_nowait()
                try:
                    action()
                except Exception as exc:
                    self._logger.error("UI update failed: %s", exc)
        except queue.Empty:
            pass
        self.after(50, self._poll_ui_queue)

    def _post(self, action: Callable[[], None]) -> None:
        """Schedule ``action`` to run on the Tk main loop (thread-safe)."""
        self._ui_queue.put(action)

    def _on_log_record(self, message: str, level: str) -> None:
        self._post(lambda: self._extract.log.append(message, level))

    def _on_file_progress(self, current: int, total: int, filename: str) -> None:
        def update() -> None:
            self._extract.progress.start_file(current, total, filename)
            self._extract.file_table.set_status(
                current - 1, "Processing\u2026", "processing"
            )
            if current >= 2:
                self._extract.file_table.set_status(current - 2, "Done", "done")
            self._header.set_status(
                f"Extracting {current}/{total}\u2026", busy=True
            )

        self._post(update)

    def _on_image_extracted(self, count: int) -> None:
        self._post(lambda: self._extract.progress.set_image_count(count))

    def _on_batch_complete(self, summary: ExtractionSummary) -> None:
        def finish() -> None:
            self._set_busy(False)
            self._extract.open_output_button.configure(state="normal")
            self._extract.progress.complete(
                f"Completed \u2014 {summary.total_images} image(s), "
                f"{summary.duplicate_count} duplicate(s) in "
                f"{format_duration(summary.processing_time_seconds)}"
            )
            self._header.set_status(
                f"Done \u00b7 {summary.total_images} images extracted"
            )

            # Per-file statuses in the table
            for index, result in enumerate(summary.results):
                if result.success:
                    self._extract.file_table.set_status(
                        index, f"\u2713 {result.total_images} image(s)", "done"
                    )
                else:
                    self._extract.file_table.set_status(
                        index, "Failed", "failed"
                    )

            self._extract.log.append(self._build_summary_text(summary), "info")
            self._dashboard.update_stats(summary)
            self._reports.set_results(summary, self._output_dir)
            self._history_service.add(summary)
            self._history_page.set_entries(self._history_service.entries)

            if summary.files_failed and not summary.files_processed:
                show_error_dialog(
                    "Extraction failed. Check the activity log for details."
                )
            else:
                self.navigate("reports")

        self._post(finish)

    # ------------------------------------------------------------- helpers

    @staticmethod
    def _build_summary_text(summary: ExtractionSummary) -> str:
        """Render the post-extraction summary appended to the activity log."""
        lines = [
            "",
            "\u2014" * 48,
            f"Extraction summary \u00b7 {summary.files_processed} file(s)"
            + (f" ({summary.files_failed} failed)" if summary.files_failed else "")
            + f" \u00b7 {summary.total_images} image(s)"
            + f" \u00b7 {summary.duplicate_count} duplicate(s)"
            + f" \u00b7 {format_duration(summary.processing_time_seconds)}",
        ]
        for result in summary.results:
            if result.success:
                formats = ", ".join(
                    f"{fmt}: {count}"
                    for fmt, count in sorted(result.format_breakdown.items())
                )
                if not formats:
                    formats = ("duplicates only" if result.total_images
                               else "no images")
                lines.append(
                    f"  {result.source.name} \u2192 "
                    f"{result.total_images} image(s) ({formats})"
                )
            else:
                lines.append(
                    f"  {result.source.name} \u2192 FAILED: {result.error}"
                )
        lines.append("\u2014" * 48)
        return "\n".join(lines)

    def _set_busy(self, busy: bool) -> None:
        self._extract.start_button.configure(
            state="disabled" if busy else "normal"
        )
        self._extract.cancel_button.configure(
            state="normal" if busy else "disabled"
        )
