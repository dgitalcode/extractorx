"""
D-GITALCODE ExtractorX - Formatting helpers.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional


def bytes_to_mb(size_bytes: int) -> float:
    """Convert a byte count to megabytes."""
    return size_bytes / (1024 * 1024)


def format_size(size_bytes: int) -> str:
    """Render a byte count as a human readable string (KB / MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{bytes_to_mb(size_bytes):.2f} MB"


def format_duration(seconds: float) -> str:
    """Render a duration in seconds as a compact human readable string."""
    if seconds < 60:
        return f"{seconds:.2f} s"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)} min {secs:.0f} s"


def format_timestamp(moment: Optional[datetime] = None) -> str:
    """Render a datetime (default: now) as ``YYYY-MM-DD HH:MM:SS``."""
    return (moment or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


def timestamp_slug(moment: Optional[datetime] = None) -> str:
    """Render a datetime (default: now) as a filename-safe slug."""
    return (moment or datetime.now()).strftime("%Y%m%d_%H%M%S")
