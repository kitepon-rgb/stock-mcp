"""System tray icon for ms2-bridge.

Runs on the calling thread (must be the main thread on Windows). Provides
visual confirmation that the bridge is alive and a 'Quit' menu item that
hands control back to bridge.py for graceful shutdown.
"""

from __future__ import annotations

import os
import webbrowser
from typing import Callable

import pystray
from PIL import Image, ImageDraw, ImageFont


def _make_icon() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill=(46, 139, 87, 255))
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    text = "MS"
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    d.text(
        ((64 - w) / 2 - bbox[0], (64 - h) / 2 - bbox[1]),
        text,
        fill=(255, 255, 255, 255),
        font=font,
    )
    return img


def run_tray(
    *,
    port: int,
    workbook_path: str | None,
    on_quit: Callable[[], None],
) -> None:
    """Block on the system tray loop until the user picks 'Quit'."""
    icon_ref: dict[str, pystray.Icon] = {}

    def _open_health(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        webbrowser.open(f"http://localhost:{port}/healthz")

    def _open_workbook_dir(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        if workbook_path and os.path.exists(workbook_path):
            os.startfile(os.path.dirname(workbook_path))  # type: ignore[attr-defined]

    def _quit(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        try:
            on_quit()
        finally:
            ic = icon_ref.get("icon")
            if ic is not None:
                ic.stop()

    menu = pystray.Menu(
        pystray.MenuItem(f"ms2-bridge :{port}", None, enabled=False),
        pystray.MenuItem("ヘルスチェックを開く", _open_health),
        pystray.MenuItem(
            "ワークブックの場所を開く",
            _open_workbook_dir,
            enabled=bool(workbook_path and os.path.exists(workbook_path or "")),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("終了", _quit),
    )
    icon = pystray.Icon(
        "ms2-bridge",
        _make_icon(),
        f"ms2-bridge listening on :{port}",
        menu,
    )
    icon_ref["icon"] = icon
    icon.run()
