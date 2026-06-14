"""
D-GITALCODE ExtractorX - Application pages.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Workspace pages: Dashboard, Extract, History, Reports and Settings.
Presentation only - all state changes flow through callbacks.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

import customtkinter as ctk
from PIL import Image

from core.extractor import ExtractedImage, ExtractionSummary
from gui.components import (
    Card,
    DropZone,
    FileTable,
    LogConsole,
    ProgressPanel,
    SectionTitle,
    StatCard,
)
from gui.theme import (
    COLOR,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_TINY,
    RADIUS_SM,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    SPACE_XL,
    SPACE_XS,
    palette,
)
from services.history_service import HistoryEntry
from services.settings_service import (
    AppSettings,
    DUPLICATE_MODE_CHOICES,
    REPORT_FORMAT_CHOICES,
)
from utils.format_utils import format_duration

_THUMBNAIL_LIMIT = 120
_THUMBNAIL_SIZE = 104


class _Page(ctk.CTkFrame):
    """Base class for workspace pages."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color="transparent")


# =============================================================== Dashboard

class DashboardPage(_Page):
    """Overview statistics with a format-distribution chart."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master)

        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, SPACE_LG))
        self._cards: dict[str, StatCard] = {}
        for key, caption in (
            ("files", "Files processed"),
            ("images", "Images extracted"),
            ("duplicates", "Duplicates found"),
            ("time", "Processing time"),
        ):
            card = StatCard(cards_row, caption)
            card.pack(side="left", expand=True, fill="x",
                      padx=(0, SPACE_MD) if key != "time" else 0)
            self._cards[key] = card

        chart_card = Card(self)
        chart_card.pack(fill="x")
        SectionTitle(chart_card, "Images by format").pack(
            anchor="w", padx=SPACE_LG, pady=(SPACE_LG, SPACE_SM)
        )
        self._canvas = tk.Canvas(chart_card, height=240, highlightthickness=0)
        self._canvas.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_LG))
        self._breakdown: dict[str, int] = {}
        self._canvas.bind("<Configure>", lambda _e: self._draw_chart())
        self._draw_chart()

    def update_stats(self, summary: ExtractionSummary) -> None:
        self._cards["files"].set(str(summary.files_processed))
        self._cards["images"].set(str(summary.total_images))
        self._cards["duplicates"].set(str(summary.duplicate_count))
        self._cards["time"].set(
            format_duration(summary.processing_time_seconds)
        )
        self._breakdown = summary.format_breakdown
        self._draw_chart()

    def refresh_theme(self) -> None:
        self._draw_chart()

    def _draw_chart(self) -> None:
        colors = palette()
        canvas = self._canvas
        canvas.configure(bg=colors.surface)
        canvas.delete("all")

        width = max(canvas.winfo_width(), 320)
        height = max(canvas.winfo_height(), 160)
        if not self._breakdown:
            canvas.create_text(
                width // 2, height // 2,
                text="Run an extraction to see statistics",
                fill=colors.text_muted, font=FONT_SMALL,
            )
            return

        items = sorted(self._breakdown.items(), key=lambda kv: -kv[1])
        max_count = max(count for _, count in items) or 1
        margin, bottom = 24, 32
        zone = width - 2 * margin
        bar_width = min(56, zone // max(len(items), 1) - 16)

        for index, (fmt, count) in enumerate(items):
            x_center = margin + (index + 0.5) * (zone / len(items))
            bar_height = (height - bottom - 28) * (count / max_count)
            x0, x1 = x_center - bar_width / 2, x_center + bar_width / 2
            y0, y1 = height - bottom - bar_height, height - bottom
            canvas.create_rectangle(x0, y0, x1, y1,
                                    fill=colors.accent, outline="")
            canvas.create_text(x_center, y0 - 10, text=str(count),
                               fill=colors.text, font=FONT_TINY)
            canvas.create_text(x_center, height - bottom + 12, text=fmt,
                               fill=colors.text_muted, font=FONT_TINY)


# ================================================================= Extract

class ExtractPage(_Page):
    """Main extraction workflow: drop zone, file table, progress, log."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_browse_files: Callable[[], None],
        on_browse_folder: Callable[[], None],
        on_start: Callable[[], None],
        on_cancel: Callable[[], None],
        on_clear: Callable[[], None],
        on_open_output: Callable[[], None],
    ) -> None:
        super().__init__(master)

        self.drop_zone = DropZone(self, on_browse_files, on_browse_folder)
        self.drop_zone.pack(fill="x", pady=(0, SPACE_MD))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, SPACE_XS))
        self._files_title = SectionTitle(toolbar, "Files")
        self._files_title.pack(side="left")
        ctk.CTkButton(
            toolbar, text="Clear", width=70, height=26,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface_2"], border_width=1,
            border_color=COLOR["border"], text_color=COLOR["text_muted"],
            font=FONT_SMALL, command=on_clear,
        ).pack(side="right")

        self.file_table = FileTable(self)
        self.file_table.pack(fill="both", expand=True, pady=(0, SPACE_MD))

        self.progress = ProgressPanel(self)
        self.progress.pack(fill="x", pady=(0, SPACE_MD))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", pady=(0, SPACE_MD))
        self.start_button = ctk.CTkButton(
            actions, text="Start extraction", width=150, height=34,
            corner_radius=RADIUS_SM,
            fg_color=COLOR["accent"], hover_color=COLOR["accent_hover"],
            text_color="#ffffff", font=FONT_BODY_BOLD,
            state="disabled", command=on_start,
        )
        self.start_button.pack(side="left")
        self.cancel_button = ctk.CTkButton(
            actions, text="Cancel", width=90, height=34,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface_2"], border_width=1,
            border_color=COLOR["border"], text_color=COLOR["danger"],
            font=FONT_BODY, state="disabled", command=on_cancel,
        )
        self.cancel_button.pack(side="left", padx=SPACE_SM)
        self.open_output_button = ctk.CTkButton(
            actions, text="Open output folder", width=140, height=34,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface_2"], border_width=1,
            border_color=COLOR["border"], text_color=COLOR["text"],
            font=FONT_BODY, state="disabled", command=on_open_output,
        )
        self.open_output_button.pack(side="right")

        self.log = LogConsole(self, height=120)
        self.log.pack(fill="x")

    def set_files(self, paths: Sequence[Path]) -> None:
        self.file_table.set_files(paths)
        self._files_title.configure(
            text=f"Files ({len(paths)})" if paths else "Files"
        )

    def clear_files(self) -> None:
        self.file_table.clear()
        self._files_title.configure(text="Files")


# ================================================================= History

class HistoryPage(_Page):
    """Past extraction runs with one-click reopening."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_open: Callable[[HistoryEntry], None],
        on_clear: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._on_open = on_open

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, SPACE_SM))
        SectionTitle(toolbar, "Extraction history").pack(side="left")
        ctk.CTkButton(
            toolbar, text="Clear history", width=100, height=26,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface_2"], border_width=1,
            border_color=COLOR["border"], text_color=COLOR["text_muted"],
            font=FONT_SMALL, command=on_clear,
        ).pack(side="right")

        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.pack(fill="both", expand=True)

    def set_entries(self, entries: Sequence[HistoryEntry]) -> None:
        for child in self._list.winfo_children():
            child.destroy()
        if not entries:
            ctk.CTkLabel(
                self._list, text="No extraction history yet",
                font=FONT_SMALL, text_color=COLOR["text_muted"],
            ).pack(pady=48)
            return

        for entry in entries:
            row = Card(self._list)
            row.pack(fill="x", pady=SPACE_XS)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True,
                      padx=SPACE_LG, pady=SPACE_SM)
            files_text = ", ".join(entry.files[:3])
            if len(entry.files) > 3:
                files_text += f"  +{len(entry.files) - 3} more"
            ctk.CTkLabel(
                info, text=files_text, font=FONT_BODY_BOLD,
                text_color=COLOR["text"], anchor="w",
            ).pack(fill="x")
            ctk.CTkLabel(
                info,
                text=f"{entry.date}   \u00b7   {entry.total_images} images, "
                     f"{entry.duplicates} duplicates",
                font=FONT_TINY, text_color=COLOR["text_muted"], anchor="w",
            ).pack(fill="x")
            ctk.CTkButton(
                row, text="Open", width=70, height=28,
                corner_radius=RADIUS_SM, fg_color="transparent",
                hover_color=COLOR["surface_2"], border_width=1,
                border_color=COLOR["border"], text_color=COLOR["accent"],
                font=FONT_SMALL,
                command=lambda e=entry: self._on_open(e),
            ).pack(side="right", padx=SPACE_LG)


# ================================================================= Reports

class ReportsPage(_Page):
    """Extraction results: summary, report files and thumbnail gallery."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_open_path: Callable[[Path], None],
    ) -> None:
        super().__init__(master)
        self._on_open_path = on_open_path
        self._items: List[Tuple[ExtractedImage, ctk.CTkImage, str]] = []

        # Summary strip
        summary_card = Card(self)
        summary_card.pack(fill="x", pady=(0, SPACE_MD))
        self._summary_label = ctk.CTkLabel(
            summary_card, text="No extraction results yet",
            font=FONT_BODY, text_color=COLOR["text_muted"], anchor="w",
        )
        self._summary_label.pack(side="left", padx=SPACE_LG, pady=SPACE_MD)
        self._reports_row = ctk.CTkFrame(summary_card, fg_color="transparent")
        self._reports_row.pack(side="right", padx=SPACE_LG)

        # Search
        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", pady=(0, SPACE_SM))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._render())
        ctk.CTkEntry(
            search_row, textvariable=self._search_var, height=32,
            corner_radius=RADIUS_SM, border_color=COLOR["border"],
            fg_color=COLOR["surface"],
            placeholder_text="Filter images by name, format or source\u2026",
            font=FONT_SMALL,
        ).pack(side="left", fill="x", expand=True)
        self._count_label = ctk.CTkLabel(
            search_row, text="", font=FONT_TINY,
            text_color=COLOR["text_muted"],
        )
        self._count_label.pack(side="left", padx=SPACE_SM)

        self._grid = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._grid.pack(fill="both", expand=True)
        self._render()

    def set_results(
        self, summary: ExtractionSummary, output_dir: Optional[Path]
    ) -> None:
        formats = ", ".join(
            f"{fmt} ({count})"
            for fmt, count in sorted(summary.format_breakdown.items())
        ) or "\u2013"
        self._summary_label.configure(
            text=f"{summary.total_images} images   \u00b7   "
                 f"{summary.duplicate_count} duplicates   \u00b7   "
                 f"Formats: {formats}",
            text_color=COLOR["text"],
        )

        # Every document is self-contained: link each document's own folder
        # (images + TXT/PDF/Excel/Metadata reports inside).
        for child in self._reports_row.winfo_children():
            child.destroy()
        folders = [
            result.output_folder
            for result in summary.results
            if result.success and result.output_folder is not None
        ]
        for folder in folders[:5]:
            ctk.CTkButton(
                self._reports_row, text=f"\U0001f4c1 {folder.name}",
                height=26, corner_radius=RADIUS_SM, fg_color="transparent",
                hover_color=COLOR["surface_2"], border_width=1,
                border_color=COLOR["border"],
                text_color=COLOR["accent"], font=FONT_TINY,
                command=lambda f=folder: self._on_open_path(f),
            ).pack(side="left", padx=2)
        if len(folders) > 5:
            ctk.CTkLabel(
                self._reports_row, text=f"+{len(folders) - 5} more",
                font=FONT_TINY, text_color=COLOR["text_muted"],
            ).pack(side="left", padx=SPACE_XS)

        # Thumbnails
        self._items.clear()
        saved = [
            image
            for result in summary.results
            for image in result.images
            if image.saved_path is not None
        ]
        for record in saved[:_THUMBNAIL_LIMIT]:
            try:
                with Image.open(record.saved_path) as img:
                    img.thumbnail((_THUMBNAIL_SIZE, _THUMBNAIL_SIZE))
                    thumb = ctk.CTkImage(
                        light_image=img.copy(), dark_image=img.copy(),
                        size=img.size,
                    )
            except Exception:
                continue
            haystack = " ".join((
                record.saved_path.name,
                record.format_folder,
                record.source_document,
            )).lower()
            self._items.append((record, thumb, haystack))
        self._render()

    def clear(self) -> None:
        self._items.clear()
        self._summary_label.configure(
            text="No extraction results yet",
            text_color=COLOR["text_muted"],
        )
        for child in self._reports_row.winfo_children():
            child.destroy()
        self._render()

    def _render(self) -> None:
        for child in self._grid.winfo_children():
            child.destroy()

        query = self._search_var.get().strip().lower()
        matches = [item for item in self._items if not query or query in item[2]]
        self._count_label.configure(
            text=f"{len(matches)}/{len(self._items)}" if self._items else ""
        )
        if not matches:
            ctk.CTkLabel(
                self._grid,
                text="No images to display" if not self._items
                else "No images match the filter",
                font=FONT_SMALL, text_color=COLOR["text_muted"],
            ).grid(row=0, column=0, pady=48, padx=SPACE_LG)
            return

        columns = 5
        for index, (record, thumb, _) in enumerate(matches):
            card = Card(self._grid)
            card.grid(row=index // columns, column=index % columns,
                      padx=SPACE_XS, pady=SPACE_XS, sticky="n")
            ctk.CTkLabel(card, image=thumb, text="").pack(
                padx=SPACE_SM, pady=(SPACE_SM, 2)
            )
            assert record.saved_path is not None
            ctk.CTkLabel(
                card,
                text=f"{record.saved_path.name}\n"
                     f"{record.format_folder} \u00b7 "
                     f"{record.width}\u00d7{record.height}",
                font=FONT_TINY, text_color=COLOR["text_muted"],
                justify="center",
            ).pack(padx=SPACE_SM, pady=(0, SPACE_SM))


# ================================================================ Settings

class SettingsPage(_Page):
    """Settings organized in General / Extraction / Reports sections."""

    _DUPLICATE_LABELS = {
        "separate": "Move to DUPLICATES folder",
        "skip": "Skip duplicates",
        "keep": "Keep in format folders",
    }
    _REPORT_LABELS = {
        "txt": "TXT summary",
        "pdf": "PDF report",
        "xlsx": "Excel report",
        "metadata": "Image metadata (XLSX)",
    }

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        settings: AppSettings,
        languages: Sequence[str],
        on_change: Callable[[str, object], None],
        on_browse_output: Callable[[], Optional[str]],
    ) -> None:
        super().__init__(master)
        self._on_change = on_change
        self._on_browse_output = on_browse_output

        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # ----- General
        general = self._section(container, "General")
        self._form_row(general, "Theme")
        self._theme_menu = self._option_menu(
            general, ["dark", "light"], settings.theme,
            lambda value: self._on_change("theme", value),
        )
        self._form_row(general, "Language", "Applies after restart")
        self._option_menu(
            general, list(languages) or ["EN"], settings.language,
            lambda value: self._on_change("language", value),
        )

        # ----- Extraction
        extraction = self._section(container, "Extraction")
        self._form_row(extraction, "Duplicate handling")
        self._option_menu(
            extraction,
            [self._DUPLICATE_LABELS[m] for m in DUPLICATE_MODE_CHOICES],
            self._DUPLICATE_LABELS[settings.duplicate_mode],
            lambda value: self._on_change(
                "duplicate_mode",
                next(k for k, v in self._DUPLICATE_LABELS.items() if v == value),
            ),
            width=230,
        )
        self._form_row(extraction, "Output location")
        out_row = ctk.CTkFrame(extraction, fg_color="transparent")
        out_row.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_MD))
        self._output_var = tk.StringVar(value=settings.output_dir)
        self._output_var.trace_add(
            "write",
            lambda *_: self._on_change("output_dir", self._output_var.get()),
        )
        ctk.CTkEntry(
            out_row, textvariable=self._output_var, height=30,
            corner_radius=RADIUS_SM, border_color=COLOR["border"],
            fg_color=COLOR["surface_2"], font=FONT_SMALL,
        ).pack(side="left", fill="x", expand=True, padx=(0, SPACE_SM))
        ctk.CTkButton(
            out_row, text="Browse", width=80, height=30,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface_2"], border_width=1,
            border_color=COLOR["border"], text_color=COLOR["text"],
            font=FONT_SMALL, command=self._browse_output,
        ).pack(side="left")

        # ----- Reports
        reports = self._section(container, "Reports")
        self._report_vars: dict[str, tk.BooleanVar] = {}
        for fmt in REPORT_FORMAT_CHOICES:
            var = tk.BooleanVar(value=fmt in settings.report_formats)
            var.trace_add("write", lambda *_: self._reports_changed())
            self._report_vars[fmt] = var
            ctk.CTkCheckBox(
                reports, text=self._REPORT_LABELS[fmt], variable=var,
                font=FONT_BODY, checkbox_height=18, checkbox_width=18,
                corner_radius=4, border_width=2,
                border_color=COLOR["border"],
                fg_color=COLOR["accent"], hover_color=COLOR["accent_hover"],
            ).pack(anchor="w", padx=SPACE_LG, pady=SPACE_XS)
        ctk.CTkFrame(reports, fg_color="transparent", height=SPACE_SM).pack()

    # ------------------------------------------------------------- helpers

    @staticmethod
    def _section(master: ctk.CTkBaseClass, title: str) -> Card:
        SectionTitle(master, title).pack(
            anchor="w", pady=(SPACE_MD, SPACE_XS)
        )
        card = Card(master)
        card.pack(fill="x", pady=(0, SPACE_SM))
        return card

    @staticmethod
    def _form_row(master: ctk.CTkBaseClass, label: str,
                  hint: str = "") -> None:
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", padx=SPACE_LG, pady=(SPACE_MD, 2))
        ctk.CTkLabel(
            row, text=label, font=FONT_BODY, text_color=COLOR["text"],
            anchor="w",
        ).pack(side="left")
        if hint:
            ctk.CTkLabel(
                row, text=hint, font=FONT_TINY,
                text_color=COLOR["text_muted"], anchor="w",
            ).pack(side="left", padx=SPACE_SM)

    @staticmethod
    def _option_menu(
        master: ctk.CTkBaseClass,
        values: List[str],
        current: str,
        command: Callable[[str], None],
        width: int = 160,
    ) -> ctk.CTkOptionMenu:
        menu = ctk.CTkOptionMenu(
            master, values=values, command=command, width=width, height=30,
            corner_radius=RADIUS_SM, font=FONT_SMALL,
            fg_color=COLOR["surface_2"], button_color=COLOR["surface_2"],
            button_hover_color=COLOR["border"], text_color=COLOR["text"],
            dropdown_font=FONT_SMALL,
        )
        menu.set(current)
        menu.pack(anchor="w", padx=SPACE_LG, pady=(0, SPACE_MD))
        return menu

    def _browse_output(self) -> None:
        chosen = self._on_browse_output()
        if chosen:
            self._output_var.set(chosen)

    def _reports_changed(self) -> None:
        selected = [fmt for fmt, var in self._report_vars.items() if var.get()]
        self._on_change("report_formats", selected)
