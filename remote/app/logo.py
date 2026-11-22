"""The YukiTube logo: a striped retrowave sun over a neon grid with a play mark."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QIcon, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPixmap, QRadialGradient)


def draw_logo(p: QPainter, s: float):
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(0, 0, s, s)
    rad = s * 0.22
    clip = QPainterPath()
    clip.addRoundedRect(r.adjusted(s * .02, s * .02, -s * .02, -s * .02), rad, rad)

    bg = QLinearGradient(0, 0, 0, s)
    bg.setColorAt(0, QColor("#12022b"))
    bg.setColorAt(0.55, QColor("#3a0a5e"))
    bg.setColorAt(1, QColor("#14031f"))
    p.fillPath(clip, bg)
    p.setClipPath(clip)

    horizon = s * 0.64
    # sun
    sun = QRectF(s * .5 - s * .30, horizon - s * .44, s * .60, s * .60)
    g = QLinearGradient(0, sun.top(), 0, horizon)
    g.setColorAt(0, QColor("#ffd319"))
    g.setColorAt(0.5, QColor("#ff901f"))
    g.setColorAt(1, QColor("#ff2a6d"))
    sunp = QPainterPath()
    sunp.addEllipse(sun)
    cut = QPainterPath()
    cut.addRect(QRectF(0, 0, s, horizon))
    stripes = QPainterPath()
    y = horizon - s * .20
    h = s * .018
    while y < horizon:
        stripes.addRect(QRectF(0, y, s, h))
        y += h * 2.6
        h *= 1.25
    p.fillPath(sunp.intersected(cut).subtracted(stripes), g)

    # grid
    p.fillRect(QRectF(0, horizon, s, s - horizon), QColor(20, 2, 40, 230))
    pen = QPen(QColor("#ff2a6d"), max(1.0, s * .012))
    p.setPen(pen)
    for i in range(-6, 7):
        p.drawLine(QPointF(s / 2 + i * s * .04, horizon), QPointF(s / 2 + i * s * .26, s))
    k = 0.0
    step = s * .03
    yy = horizon
    while yy < s:
        p.drawLine(QPointF(0, yy), QPointF(s, yy))
        k += 1
        yy = horizon + step * k * k * .9
    hp = QPen(QColor("#05d9e8"), max(1.0, s * .02))
    p.setPen(hp)
    p.drawLine(QPointF(0, horizon), QPointF(s, horizon))

    # play mark
    tri = QPainterPath()
    cx, cy, t = s * .52, s * .44, s * .20
    tri.moveTo(cx - t * .75, cy - t)
    tri.lineTo(cx + t, cy)
    tri.lineTo(cx - t * .75, cy + t)
    tri.closeSubpath()
    glow = QRadialGradient(QPointF(cx, cy), t * 2)
    glow.setColorAt(0, QColor(5, 217, 232, 120))
    glow.setColorAt(1, QColor(5, 217, 232, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(glow))
    p.drawEllipse(QPointF(cx, cy), t * 2, t * 2)
    p.setBrush(QColor("#ffffff"))
    p.setPen(QPen(QColor("#05d9e8"), max(1.0, s * .025), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPath(tri)

    p.setClipping(False)
    border = QLinearGradient(0, 0, s, s)
    border.setColorAt(0, QColor("#ff2a6d"))
    border.setColorAt(1, QColor("#05d9e8"))
    p.setPen(QPen(QBrush(border), max(1.0, s * .03)))
    p.setBrush(Qt.NoBrush)
    p.drawPath(clip)
    p.restore()


def logo_pixmap(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    draw_logo(p, size)
    p.end()
    return pm


def logo_icon() -> QIcon:
    ic = QIcon()
    for sz in (16, 24, 32, 48, 64, 128, 256):
        ic.addPixmap(logo_pixmap(sz))
    return ic
