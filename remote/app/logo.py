"""The YukiTube logo: Yuki the cat in front of the retrowave sun, over the
neon grid (assets/logo.svg).

Qt's SVG renderer leaves out clip paths, so the rounded frame is clipped here
with the painter; the frame's border lies inside that clip.
"""
import os
import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtSvg import QSvgRenderer

_renderer = None
_cache = {}


def _svg_path():
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", "logo.svg")


def draw_logo(p: QPainter, s: float):
    global _renderer
    if _renderer is None:
        _renderer = QSvgRenderer(_svg_path())
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    # The border's outer edge: 5/1024 in, a radius of 240/1024 (logo.svg).
    k = s / 1024.0
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(5 * k, 5 * k, s - 10 * k, s - 10 * k), 240 * k, 240 * k)
    p.setClipPath(clip)
    _renderer.render(p, QRectF(0, 0, s, s))
    p.restore()


def logo_pixmap(size: int) -> QPixmap:
    pm = _cache.get(size)
    if pm is None:
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        draw_logo(p, size)
        p.end()
        _cache[size] = pm
    return QPixmap(pm)  # a copy: callers may change its device pixel ratio


def logo_icon() -> QIcon:
    ic = QIcon()
    for sz in (16, 24, 32, 48, 64, 128, 256):
        ic.addPixmap(logo_pixmap(sz))
    return ic
