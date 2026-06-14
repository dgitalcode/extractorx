"""
D-GITALCODE ExtractorX - Design system.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Minimal, professional design system: restrained palette with a single
accent color, a 4px spacing scale and a consistent type hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import customtkinter as ctk

# ------------------------------------------------------------------ palette


@dataclass(frozen=True)
class Palette:
    """Resolved colors for one appearance mode."""

    bg: str
    surface: str
    surface_2: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_soft: str
    danger: str


LIGHT = Palette(
    bg="#f7f7f8",
    surface="#ffffff",
    surface_2="#f0f0f1",
    border="#e4e4e7",
    text="#1b1b1f",
    text_muted="#71717a",
    accent="#0a9d6c",
    accent_hover="#08855b",
    accent_soft="#e7f4ef",
    danger="#c93b3b",
)

DARK = Palette(
    bg="#161618",
    surface="#1e1e21",
    surface_2="#27272b",
    border="#2e2e33",
    text="#ededef",
    text_muted="#94949c",
    accent="#19b683",
    accent_hover="#13a173",
    accent_soft="#1c2b25",
    danger="#e0564e",
)

#: CustomTkinter dual-mode color tuples (light, dark).
COLOR: dict[str, Tuple[str, str]] = {
    "bg": (LIGHT.bg, DARK.bg),
    "surface": (LIGHT.surface, DARK.surface),
    "surface_2": (LIGHT.surface_2, DARK.surface_2),
    "border": (LIGHT.border, DARK.border),
    "text": (LIGHT.text, DARK.text),
    "text_muted": (LIGHT.text_muted, DARK.text_muted),
    "accent": (LIGHT.accent, DARK.accent),
    "accent_hover": (LIGHT.accent_hover, DARK.accent_hover),
    "accent_soft": (LIGHT.accent_soft, DARK.accent_soft),
    "danger": (LIGHT.danger, DARK.danger),
}


def palette() -> Palette:
    """Resolved palette for the current appearance mode (for tk widgets)."""
    return DARK if ctk.get_appearance_mode() == "Dark" else LIGHT


# ----------------------------------------------------------------- spacing
# 4px-based spacing scale used everywhere for consistent rhythm.

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_2XL = 32

RADIUS = 8
RADIUS_SM = 6

# -------------------------------------------------------------- typography

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

FONT_H1 = (FONT_FAMILY, 18, "bold")        # page titles
FONT_H2 = (FONT_FAMILY, 13, "bold")        # section titles
FONT_STAT = (FONT_FAMILY, 24, "bold")      # dashboard stat values
FONT_BODY = (FONT_FAMILY, 12)              # default text
FONT_BODY_BOLD = (FONT_FAMILY, 12, "bold")
FONT_SMALL = (FONT_FAMILY, 11)             # secondary text
FONT_TINY = (FONT_FAMILY, 10)              # captions, metadata
FONT_LOG = (FONT_MONO, 10)


class ThemeManager:
    """Apply and switch the application appearance mode."""

    def __init__(self, initial_mode: str = "dark") -> None:
        self._mode = initial_mode if initial_mode in ("dark", "light") else "dark"

    @property
    def mode(self) -> str:
        return self._mode

    def apply(self) -> None:
        ctk.set_appearance_mode(self._mode)
        ctk.set_default_color_theme("green")

    def toggle(self) -> str:
        """Switch between dark and light mode; returns the new mode."""
        self._mode = "light" if self._mode == "dark" else "dark"
        ctk.set_appearance_mode(self._mode)
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode in ("dark", "light"):
            self._mode = mode
            ctk.set_appearance_mode(mode)
