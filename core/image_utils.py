"""
D-GITALCODE ExtractorX - Image utilities.

Product: D-GITALCODE ExtractorX | https://dgitalcode.ma

Image validation, format detection and conversion helpers built on Pillow.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

from PIL import Image, UnidentifiedImageError

#: Mapping of PIL format identifiers to (extension, output folder name).
_PIL_FORMAT_MAP: dict[str, tuple[str, str]] = {
    "JPEG": (".jpg", "JPG"),
    "PNG": (".png", "PNG"),
    "GIF": (".gif", "GIF"),
    "BMP": (".bmp", "BMP"),
    "TIFF": (".tiff", "TIFF"),
    "WEBP": (".webp", "WEBP"),
}


@dataclass(frozen=True)
class ImageInfo:
    """Detected properties of an in-memory image."""

    extension: str
    folder: str
    width: int = 0
    height: int = 0


def detect_image_format(image_data: bytes) -> Optional[ImageInfo]:
    """Detect the format of raw image bytes.

    Args:
        image_data: Raw image payload (e.g. a DOCX media part blob).

    Returns:
        An :class:`ImageInfo` describing extension/folder/dimensions, or
        ``None`` when the payload is not a supported raster image.
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            mapped = _PIL_FORMAT_MAP.get(img.format or "")
            if mapped is None:
                return None
            extension, folder = mapped
            return ImageInfo(extension, folder, img.width, img.height)
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def is_valid_image(image_data: bytes) -> bool:
    """Return True when ``image_data`` decodes as an intact image."""
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            img.verify()
        return True
    except Exception:  # Pillow raises a variety of errors on corrupt data
        return False


def convert_image(image_data: bytes, target_format: str) -> bytes:
    """Convert raw image bytes to ``target_format`` (PIL format name).

    Args:
        image_data: Source image bytes.
        target_format: PIL format name, e.g. ``"PNG"`` or ``"JPEG"``.

    Returns:
        The converted image bytes.

    Raises:
        ValueError: If the source cannot be decoded.
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            if target_format.upper() == "JPEG" and img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format=target_format.upper())
            return buffer.getvalue()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Cannot convert image: {exc}") from exc
