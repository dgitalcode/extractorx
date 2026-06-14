"""
Capture portfolio screenshots from the rebranded ExtractorX desktop UI.

Usage:
    python scripts/capture_portfolio_screenshots.py

Requires a visible Windows desktop session (ImageGrab).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageGrab

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from scripts.create_demo_samples import SAMPLES_DIR, main as create_samples  # noqa: E402

SCREENSHOT_DIR = ROOT / "docs" / "screenshots"
CAPTURE_SIZE = (1280, 820)


def focus_window(app) -> None:
    """Bring the application window to the foreground before capture."""
    app.deiconify()
    app.lift()
    app.attributes("-topmost", True)
    app.update()
    app.focus_force()
    time.sleep(0.2)
    app.attributes("-topmost", False)
    app.update()


def capture_window(app, filename: str) -> Path:
    """Grab the application window bounding box."""
    focus_window(app)
    app.update_idletasks()
    app.update()
    time.sleep(0.8)
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    target = SCREENSHOT_DIR / filename
    image.save(target, format="PNG", optimize=True)
    print(f"Saved {target}")
    return target


def save_output_structure(folder: Path) -> None:
    """Render a branded output-tree preview for portfolio docs."""
    lines = [f"{config.OUTPUT_FOLDER_NAME}/", f"  {folder.name}/"]
    for child in sorted(folder.iterdir()):
        if child.is_dir():
            lines.append(f"    {child.name}/")
            for img in sorted(child.glob("*"))[:4]:
                lines.append(f"      {img.name}")
        else:
            lines.append(f"    {child.name}")

    img = Image.new("RGB", CAPTURE_SIZE, (18, 24, 30))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("consola.ttf", 18)
        title_font = ImageFont.truetype("segoeui.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
        title_font = font

    draw.text(
        (48, 40),
        "D-GITALCODE ExtractorX — Output Structure",
        fill=(37, 211, 102),
        font=title_font,
    )
    y = 110
    for line in lines:
        draw.text((64, y), line, fill=(220, 225, 230), font=font)
        y += 30

    target = SCREENSHOT_DIR / "output-structure.png"
    img.save(target, format="PNG", optimize=True)
    print(f"Saved {target}")


def run_portfolio_capture() -> None:
    config.ensure_app_directories()
    config.Translator.load()
    create_samples()

    from gui.app import MainApplication

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for old in SCREENSHOT_DIR.glob("*.png"):
        old.unlink()

    app = MainApplication()
    app.geometry(f"{CAPTURE_SIZE[0]}x{CAPTURE_SIZE[1]}")
    app.update()

    samples = sorted(SAMPLES_DIR.glob("demo.*"))
    if not samples:
        raise RuntimeError("Demo samples were not created")

    app._set_documents(samples)
    capture_window(app, "extract-workflow.png")

    app._on_start()
    deadline = time.time() + 90
    progress_captured = False
    while app._batch.is_running and time.time() < deadline:
        app.update()
        if not progress_captured:
            capture_window(app, "extract-progress.png")
            progress_captured = True
        time.sleep(0.05)

    while app._ui_queue.qsize() > 0:
        app.update()
        time.sleep(0.05)
    app.update()
    time.sleep(0.5)

    capture_window(app, "results-output.png")
    app.navigate("dashboard")
    capture_window(app, "dashboard.png")
    app.navigate("history")
    capture_window(app, "history.png")
    app.navigate("settings")
    capture_window(app, "settings.png")

    if app._output_dir:
        for folder in sorted(app._output_dir.iterdir()):
            if folder.is_dir():
                save_output_structure(folder)
                break

    app.destroy()


if __name__ == "__main__":
    run_portfolio_capture()
