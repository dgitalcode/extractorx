"""
D-GITALCODE ExtractorX - Reusable UI widgets.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Component library for the application shell and pages: sidebar navigation,
compact header, flat cards, drop zone, file table, progress panel and log
console. Presentation only - components expose callbacks and update methods.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import customtkinter as ctk
from PIL import Image

import config
from gui.theme import (
    COLOR,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_H1,
    FONT_H2,
    FONT_LOG,
    FONT_SMALL,
    FONT_STAT,
    FONT_TINY,
    RADIUS,
    RADIUS_SM,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    SPACE_XS,
)
from utils.format_utils import format_size

_FILE_TYPE_LABELS = {
    ".docx": "Word",
    ".doc": "Word (legacy)",
    ".pptx": "PowerPoint",
    ".ppt": "PowerPoint (legacy)",
    ".pdf": "PDF",
}


def load_logo(size: int = 28) -> Optional[ctk.CTkImage]:
    """Load the D-GITALCODE logo as a CTkImage, or None if missing."""
    if not config.LOGO_PNG.exists():
        return None
    image = Image.open(config.LOGO_PNG)
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))


# ============================================================ shell widgets

class Sidebar(ctk.CTkFrame):
    """Left navigation rail with discreet branding."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        items: Sequence[Tuple[str, str, str]],
        on_navigate: Callable[[str], None],
    ) -> None:
        """
        Args:
            items: Sequence of (key, glyph, label).
            on_navigate: Called with the item key when a nav entry is clicked.
        """
        super().__init__(
            master, width=200, corner_radius=0,
            fg_color=COLOR["surface"],
            border_width=0,
        )
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        self._buttons: Dict[str, ctk.CTkButton] = {}
        self._active: Optional[str] = None

        # Brand block
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=SPACE_LG, pady=(SPACE_LG, SPACE_XS))
        logo = load_logo(26)
        if logo is not None:
            ctk.CTkLabel(brand, image=logo, text="").pack(side="left")
        ctk.CTkLabel(
            brand, text=config.BRAND, font=FONT_BODY_BOLD,
            text_color=COLOR["text"],
        ).pack(side="left", padx=(SPACE_SM, 0))

        ctk.CTkFrame(self, height=1, fg_color=COLOR["border"]).pack(
            fill="x", padx=SPACE_LG, pady=(SPACE_MD, SPACE_MD)
        )

        for key, glyph, label in items:
            button = ctk.CTkButton(
                self,
                text=f"  {glyph}   {label}",
                anchor="w",
                height=34,
                corner_radius=RADIUS_SM,
                fg_color="transparent",
                hover_color=COLOR["surface_2"],
                text_color=COLOR["text_muted"],
                font=FONT_BODY,
                command=lambda k=key: self._on_navigate(k),
            )
            button.pack(fill="x", padx=SPACE_SM, pady=1)
            self._buttons[key] = button

        # Company credit at the bottom of the navigation sidebar.
        credit = ctk.CTkFrame(self, fg_color="transparent")
        credit.pack(side="bottom", fill="x", padx=SPACE_LG, pady=SPACE_LG)
        ctk.CTkLabel(
            credit,
            text=f"{config.BRAND}\n{config.COMPANY_SITE.replace('https://', '')}",
            font=FONT_TINY,
            text_color=COLOR["text_muted"],
            justify="left",
            anchor="w",
        ).pack(fill="x")

    def set_active(self, key: str) -> None:
        """Highlight the active navigation entry."""
        if self._active and self._active in self._buttons:
            self._buttons[self._active].configure(
                fg_color="transparent", text_color=COLOR["text_muted"],
            )
        self._active = key
        self._buttons[key].configure(
            fg_color=COLOR["accent_soft"], text_color=COLOR["accent"],
        )


class Header(ctk.CTkFrame):
    """Compact top header: page title, status, theme + settings shortcuts."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_theme_toggle: Callable[[], None],
        on_open_settings: Callable[[], None],
    ) -> None:
        super().__init__(
            master, height=48, corner_radius=0, fg_color=COLOR["surface"],
        )
        self.pack_propagate(False)

        self._title = ctk.CTkLabel(
            self, text="", font=FONT_H1, text_color=COLOR["text"],
        )
        self._title.pack(side="left", padx=SPACE_LG)

        # Right-side controls
        ctk.CTkButton(
            self, text="\u2699", width=34, height=30,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface_2"], text_color=COLOR["text_muted"],
            font=(FONT_BODY[0], 15), command=on_open_settings,
        ).pack(side="right", padx=(0, SPACE_LG))
        ctk.CTkButton(
            self, text="\u25d0", width=34, height=30,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface_2"], text_color=COLOR["text_muted"],
            font=(FONT_BODY[0], 15), command=on_theme_toggle,
        ).pack(side="right", padx=SPACE_XS)

        self._status = ctk.CTkLabel(
            self, text="Ready", font=FONT_SMALL,
            text_color=COLOR["text_muted"],
        )
        self._status.pack(side="right", padx=SPACE_LG)

    def set_title(self, title: str) -> None:
        self._title.configure(text=title)

    def set_status(self, text: str, busy: bool = False) -> None:
        self._status.configure(
            text=text,
            text_color=COLOR["accent"] if busy else COLOR["text_muted"],
        )


class StatusBar(ctk.CTkFrame):
    """Bottom status bar with discreet branding and version."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(
            master, height=26, corner_radius=0, fg_color=COLOR["surface"],
        )
        self.pack_propagate(False)
        ctk.CTkLabel(
            self, text=config.COPYRIGHT, font=FONT_TINY,
            text_color=COLOR["text_muted"],
        ).pack(side="left", padx=SPACE_LG)
        ctk.CTkLabel(
            self, text=config.APP_DISPLAY_VERSION, font=FONT_TINY,
            text_color=COLOR["text_muted"],
        ).pack(side="right", padx=SPACE_LG)


# ============================================================ page widgets

class Card(ctk.CTkFrame):
    """Flat surface card with a hairline border (no shadows)."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs: object) -> None:
        defaults = dict(
            fg_color=COLOR["surface"],
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLOR["border"],
        )
        defaults.update(kwargs)  # type: ignore[arg-type]
        super().__init__(master, **defaults)  # type: ignore[arg-type]


class StatCard(Card):
    """Dashboard statistic: large value with a muted caption."""

    def __init__(self, master: ctk.CTkBaseClass, caption: str) -> None:
        super().__init__(master)
        self._value = ctk.CTkLabel(
            self, text="\u2013", font=FONT_STAT, text_color=COLOR["text"],
        )
        self._value.pack(anchor="w", padx=SPACE_LG, pady=(SPACE_LG, 0))
        ctk.CTkLabel(
            self, text=caption, font=FONT_SMALL,
            text_color=COLOR["text_muted"],
        ).pack(anchor="w", padx=SPACE_LG, pady=(0, SPACE_LG))

    def set(self, value: str) -> None:
        self._value.configure(text=value)


class SectionTitle(ctk.CTkLabel):
    """Consistent section heading."""

    def __init__(self, master: ctk.CTkBaseClass, text: str) -> None:
        super().__init__(
            master, text=text, font=FONT_H2,
            text_color=COLOR["text"], anchor="w",
        )


class DropZone(Card):
    """Drag & drop target with inline browse actions."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_browse_files: Callable[[], None],
        on_browse_folder: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color=COLOR["surface_2"])

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(pady=SPACE_LG)
        ctk.CTkLabel(
            inner, text="\u2913", font=(FONT_BODY[0], 22),
            text_color=COLOR["text_muted"],
        ).pack()
        ctk.CTkLabel(
            inner,
            text="Drop DOCX, PPTX or PDF files here",
            font=FONT_BODY, text_color=COLOR["text"],
        ).pack(pady=(SPACE_XS, SPACE_SM))
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack()
        ctk.CTkButton(
            row, text="Browse files", width=110, height=30,
            corner_radius=RADIUS_SM,
            fg_color=COLOR["accent"], hover_color=COLOR["accent_hover"],
            text_color="#ffffff", font=FONT_SMALL,
            command=on_browse_files,
        ).pack(side="left", padx=SPACE_XS)
        ctk.CTkButton(
            row, text="Select folder", width=110, height=30,
            corner_radius=RADIUS_SM, fg_color="transparent",
            hover_color=COLOR["surface"], border_width=1,
            border_color=COLOR["border"], text_color=COLOR["text"],
            font=FONT_SMALL, command=on_browse_folder,
        ).pack(side="left", padx=SPACE_XS)


class FileTable(Card):
    """Clean file table: Name / Type / Size / Status."""

    _STATUS_COLORS = {
        "pending": "text_muted",
        "processing": "accent",
        "done": "text",
        "failed": "danger",
    }

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACE_LG, pady=(SPACE_MD, SPACE_XS))
        for text, width, expand in (
            ("Name", 260, True), ("Type", 130, False),
            ("Size", 80, False), ("Status", 150, False),
        ):
            ctk.CTkLabel(
                header, text=text, width=width, anchor="w",
                font=(FONT_TINY[0], 10, "bold"),
                text_color=COLOR["text_muted"],
            ).pack(side="left", fill="x" if expand else None,
                   expand=expand, padx=(0, SPACE_SM))

        ctk.CTkFrame(self, height=1, fg_color=COLOR["border"]).pack(
            fill="x", padx=SPACE_LG
        )

        self._body = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=170,
        )
        self._body.pack(fill="both", expand=True, padx=SPACE_SM,
                        pady=(0, SPACE_SM))
        self._status_labels: List[ctk.CTkLabel] = []
        self._placeholder: Optional[ctk.CTkLabel] = None
        self.clear()

    def set_files(self, paths: Sequence[Path]) -> None:
        self._reset()
        if not paths:
            self.clear()
            return
        for path in paths:
            row = ctk.CTkFrame(self._body, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row, text=path.name, width=260, anchor="w",
                font=FONT_BODY, text_color=COLOR["text"],
            ).pack(side="left", fill="x", expand=True, padx=(SPACE_SM, SPACE_SM))
            ctk.CTkLabel(
                row,
                text=_FILE_TYPE_LABELS.get(path.suffix.lower(), path.suffix),
                width=130, anchor="w", font=FONT_SMALL,
                text_color=COLOR["text_muted"],
            ).pack(side="left", padx=(0, SPACE_SM))
            try:
                size_text = format_size(path.stat().st_size)
            except OSError:
                size_text = "\u2013"
            ctk.CTkLabel(
                row, text=size_text, width=80, anchor="w",
                font=FONT_SMALL, text_color=COLOR["text_muted"],
            ).pack(side="left", padx=(0, SPACE_SM))
            status = ctk.CTkLabel(
                row, text="Pending", width=150, anchor="w",
                font=FONT_SMALL, text_color=COLOR["text_muted"],
            )
            status.pack(side="left", padx=(0, SPACE_SM))
            self._status_labels.append(status)

    def set_status(self, index: int, text: str, kind: str = "done") -> None:
        """Update the status cell of row ``index``."""
        if 0 <= index < len(self._status_labels):
            color_key = self._STATUS_COLORS.get(kind, "text")
            self._status_labels[index].configure(
                text=text, text_color=COLOR[color_key],
            )

    def clear(self) -> None:
        self._reset()
        self._placeholder = ctk.CTkLabel(
            self._body, text="No files selected",
            font=FONT_SMALL, text_color=COLOR["text_muted"],
        )
        self._placeholder.pack(pady=40)

    def _reset(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()
        self._status_labels = []
        self._placeholder = None


class ProgressPanel(Card):
    """Progress bar with percentage, current file and remaining count."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=SPACE_LG, pady=(SPACE_MD, SPACE_XS))
        self._label = ctk.CTkLabel(
            top, text="Idle", font=FONT_SMALL,
            text_color=COLOR["text_muted"], anchor="w",
        )
        self._label.pack(side="left", fill="x", expand=True)
        self._percent = ctk.CTkLabel(
            top, text="0%", font=FONT_BODY_BOLD, text_color=COLOR["text"],
        )
        self._percent.pack(side="right")

        self._bar = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            fg_color=COLOR["surface_2"], progress_color=COLOR["accent"],
        )
        self._bar.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_XS))
        self._bar.set(0)

        self._detail = ctk.CTkLabel(
            self, text="", font=FONT_TINY,
            text_color=COLOR["text_muted"], anchor="w",
        )
        self._detail.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_MD))

    def start_file(self, current: int, total: int, filename: str) -> None:
        fraction = (current - 1) / total if total else 0
        self._bar.set(fraction)
        self._percent.configure(text=f"{fraction * 100:.0f}%")
        self._label.configure(text=f"Processing  {filename}")
        remaining = total - current
        self._detail.configure(
            text=f"File {current} of {total}  \u00b7  {remaining} remaining"
        )

    def set_image_count(self, count: int) -> None:
        self._detail.configure(text=f"{count} image(s) extracted so far")

    def complete(self, message: str) -> None:
        self._bar.set(1)
        self._percent.configure(text="100%")
        self._label.configure(text=message)
        self._detail.configure(text="")

    def reset(self) -> None:
        self._bar.set(0)
        self._percent.configure(text="0%")
        self._label.configure(text="Idle")
        self._detail.configure(text="")


class LogConsole(Card):
    """Compact, read-only activity log."""

    def __init__(self, master: ctk.CTkBaseClass, height: int = 140) -> None:
        super().__init__(master)
        self._textbox = ctk.CTkTextbox(
            self, fg_color="transparent",
            text_color=COLOR["text_muted"], font=FONT_LOG,
            wrap="word", height=height, activate_scrollbars=True,
        )
        self._textbox.pack(fill="both", expand=True,
                           padx=SPACE_SM, pady=SPACE_SM)
        self._textbox.tag_config("error", foreground=COLOR["danger"][1])
        self._textbox.tag_config("warning", foreground="#b88a3c")
        self.append("Ready.", "info")
        self._textbox.configure(state="disabled")

    def append(self, message: str, level: str = "info") -> None:
        self._textbox.configure(state="normal")
        tag = level if level in ("error", "warning") else None
        self._textbox.insert("end", message + "\n", tag)
        self._textbox.see("end")
        self._textbox.configure(state="disabled")

    def clear(self) -> None:
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")
        self.append("Ready.", "info")


def show_error_dialog(message: str, title: str = "Error") -> None:
    """Display a modal error dialog (used sparingly)."""
    from tkinter import messagebox

    messagebox.showerror(title, message)
