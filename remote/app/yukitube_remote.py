#!/usr/bin/env python3
"""YukiTube remote — the compact retrowave remote of YukiTube (formerly NeonTube).

The player talks to YouTube tabs through the "YukiTube Bridge" userscript
(Violentmonkey, preinstalled in YukiTube) or the browser extension, over a
local WebSocket / HTTP server on 127.0.0.1:8975.

YukiTube's launcher starts it with YUKITUBE_OPEN set to its own path, so links
the remote opens land in the YukiTube window instead of the default browser.
"""
import math
import os
import sys
import time

from PySide6.QtCore import (QByteArray, QEasingCurve, QPoint, QPointF, QProcess, QRectF, QSettings, QSize, Qt,
                            QTimer, QUrl, Signal)
from PySide6.QtGui import (QAction, QBrush, QColor, QDesktopServices, QFont, QFontDatabase,
                           QFontMetrics, QGuiApplication, QKeySequence, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient, QStandardItem,
                           QStandardItemModel)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QListView, QMenu, QMessageBox, QSizePolicy,
                               QStyle, QStyledItemDelegate, QSystemTrayIcon, QVBoxLayout, QWidget)

import icons
import ytsearch
from logo import logo_icon, logo_pixmap
from dock import Docker
from wsserver import HTTP_CID, WsServer

APP_NAME = "YukiTube"
VERSION = "0.4.2"
PORT = int(os.environ.get("YUKITUBE_PORT") or os.environ.get("NEONTUBE_PORT") or "8975")
WIDTH = 460

PINK = "#ff2a6d"
CYAN = "#05d9e8"
MAGENTA = "#d300c5"
PURPLE = "#7b2fff"
YELLOW = "#ffd319"
ORANGE = "#ff901f"
TEXT = "#f6ecff"
MUTED = "#bfa3e0"

# The account button's pages, opened in the YukiTube window. After signing in
# Google comes back to YouTube.
_BACK = "https%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26next%3D%252F"
SIGNIN_URL = f"https://accounts.google.com/ServiceLogin?service=youtube&passive=true&continue={_BACK}"
SWITCH_URL = f"https://accounts.google.com/AccountChooser?service=youtube&continue={_BACK}"
SIGNOUT_URL = "https://www.youtube.com/logout"
AVATAR_HOSTS = (".ggpht.com", ".googleusercontent.com", ".ytimg.com")

FONT_UI = "Sans Serif"
FONT_DISPLAY = "Orbitron"
FONT_MONO = "Share Tech Mono"


def resource_dir():
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets")


# The YukiTube launcher (Linux script or Windows YukiTube.exe), when started by it.
YUKITUBE_OPEN = os.environ.get("YUKITUBE_OPEN", "")


def userscript_bytes():
    """The bridge userscript: built into assets/ for releases, assembled from
    ../browser/ when running from a checkout. It talks to this remote's port
    (YUKITUBE_PORT), not always the default one."""
    built = os.path.join(resource_dir(), "yukitube.user.js")
    data = b""
    if os.path.isfile(built):
        with open(built, "rb") as f:
            data = f.read()
    else:
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "browser")
        parts = ("userscript-header.js", "agent-core.js", "userscript-glue.js")
        try:
            data = b"".join(open(os.path.join(src, p), "rb").read() for p in parts)
        except OSError:
            return b""
    return data.replace(b"127.0.0.1:8975", f"127.0.0.1:{PORT}".encode())


def remote_settings():
    """~/.config/YukiTube/remote.conf (Windows: HKCU\\Software\\YukiTube\\remote).
    The first time, carries over the settings NeonTube kept."""
    s = QSettings("YukiTube", "remote")
    if not s.allKeys():
        old = QSettings("NeonTube", "NeonTube")
        for k in old.allKeys():
            s.setValue(k, old.value(k))
        s.sync()
    return s


def fmt_time(t):
    if not t or t < 0 or not math.isfinite(t):
        t = 0
    t = int(t)
    h, m, s = t // 3600, (t // 60) % 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def browser_name(st):
    ua = st.get("ua", "") or ""
    brands = st.get("brands", "") or ""
    if st.get("brave") or "Brave" in brands:
        return "Brave"
    for key, name in (("Edg/", "Edge"), ("OPR/", "Opera"), ("Vivaldi", "Vivaldi"), ("YaBrowser", "Yandex"),
                      ("Firefox/", "Firefox"), ("Chromium", "Chromium"), ("Chrome/", "Chrome"), ("Safari/", "Safari")):
        if key in ua:
            return name
    return "Browser"


def qcolor(c, a=None):
    col = QColor(c)
    if a is not None:
        col.setAlphaF(a)
    return col


# ======================================================================= widgets
class IconButton(QAbstractButton):
    def __init__(self, icon, size=30, icon_size=18, tip="", checkable=False, parent=None,
                 color=TEXT, hover=CYAN, checked_color=PINK):
        super().__init__(parent)
        self._icon = icon
        self._isz = icon_size
        self.color, self.hover_color, self.checked_color = color, hover, checked_color
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(checkable)
        self.setFocusPolicy(Qt.NoFocus)
        if tip:
            self.setToolTip(tip)
        self._hover = False

    def set_icon(self, name):
        if name != self._icon:
            self._icon = name
            self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        c = QPointF(w / 2, h / 2)
        if not self.isEnabled():
            p.setOpacity(0.35)
        if self.isEnabled() and (self._hover or self.isDown()):
            g = QRadialGradient(c, w / 2)
            g.setColorAt(0, qcolor(CYAN, 0.32 if self.isDown() else 0.22))
            g.setColorAt(1, qcolor(CYAN, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawEllipse(c, w / 2, h / 2)
        col = self.color
        if self.isChecked():
            col = self.checked_color
        elif self._hover and self.isEnabled():
            col = self.hover_color
        pm = icons.pixmap(self._icon, col, self._isz, self.devicePixelRatioF())
        p.drawPixmap(QPointF((w - self._isz) / 2, (h - self._isz) / 2), pm)
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(qcolor(self.checked_color))
            p.drawEllipse(QPointF(w / 2, h - 3), 1.6, 1.6)


class PlayButton(IconButton):
    def __init__(self, parent=None):
        super().__init__("play", size=50, icon_size=26, tip="Play / Pauză  (Space)", parent=parent)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        c = QPointF(w / 2, w / 2)
        if not self.isEnabled():
            p.setOpacity(0.45)
        glow = QRadialGradient(c, w / 2)
        glow.setColorAt(0.55, qcolor(PINK, 0.55 if self._hover else 0.35))
        glow.setColorAt(1, qcolor(PINK, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(c, w / 2, w / 2)
        r = w / 2 - 6
        g = QLinearGradient(0, c.y() - r, 0, c.y() + r)
        g.setColorAt(0, QColor(ORANGE) if self._hover else QColor(PINK))
        g.setColorAt(1, QColor(MAGENTA) if not self.isDown() else QColor(PURPLE))
        p.setBrush(g)
        p.setPen(QPen(qcolor(CYAN, 0.9), 1.6))
        p.drawEllipse(c, r, r)
        pm = icons.pixmap(self._icon, "#ffffff", self._isz, self.devicePixelRatioF())
        dx = 1.5 if self._icon == "play" else 0
        p.drawPixmap(QPointF((w - self._isz) / 2 + dx, (w - self._isz) / 2), pm)


class AccountButton(IconButton):
    """The Google account: the account's avatar when YouTube is signed in,
    a person outline (with a pink ring) when it is not."""

    def __init__(self, parent=None):
        super().__init__("account", 26, 18, parent=parent)
        self.avatar = None
        self.logged_in = None

    def set_account(self, logged_in, avatar):
        if (logged_in, avatar) != (self.logged_in, self.avatar):
            self.logged_in, self.avatar = logged_in, avatar
            self.update()

    def paintEvent(self, e):
        if not self.avatar or self.avatar.isNull():
            super().paintEvent(e)
            if self.logged_in is False:
                p = QPainter(self)
                p.setRenderHint(QPainter.Antialiasing)
                p.setPen(QPen(qcolor(PINK, 0.9), 1.2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QRectF(self.rect()).adjusted(3, 3, -3, -3))
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        path = QPainterPath()
        path.addEllipse(r)
        p.save()
        p.setClipPath(path)
        p.drawPixmap(r, self.avatar, QRectF(self.avatar.rect()))
        p.restore()
        p.setPen(QPen(QColor(CYAN if self._hover else PINK), 1.4))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(r)


class NeonSlider(QWidget):
    """Horizontal slider with a gradient fill and a glowing knob. Value in [0, 1]."""
    moved = Signal(float)
    released = Signal(float)

    def __init__(self, height=18, knob=6, parent=None):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setMinimumWidth(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._v = 0.0
        self._buf = 0.0
        self._drag = False
        self._hover = False
        self._knob = knob
        self.tip_fn = None

    def value(self):
        return self._v

    def dragging(self):
        return self._drag

    def set_value(self, v):
        if self._drag:
            return
        v = max(0.0, min(1.0, v))
        if abs(v - self._v) > 1e-4:
            self._v = v
            self.update()

    def _pos_to_v(self, x):
        m = self._knob + 2
        return max(0.0, min(1.0, (x - m) / max(1, self.width() - 2 * m)))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = True
            self._v = self._pos_to_v(e.position().x())
            self.moved.emit(self._v)
            self.update()

    def mouseMoveEvent(self, e):
        if self._drag:
            self._v = self._pos_to_v(e.position().x())
            self.moved.emit(self._v)
            self.update()
        if self.tip_fn:
            txt = self.tip_fn(self._pos_to_v(e.position().x()))
            self.setToolTip(txt)

    def mouseReleaseEvent(self, e):
        if self._drag and e.button() == Qt.LeftButton:
            self._drag = False
            self._v = self._pos_to_v(e.position().x())
            self.released.emit(self._v)
            self.update()

    def wheelEvent(self, e):
        step = 0.05 if e.angleDelta().y() > 0 else -0.05
        self._v = max(0.0, min(1.0, self._v + step))
        self.moved.emit(self._v)
        self.released.emit(self._v)
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m = self._knob + 2
        w = self.width() - 2 * m
        cy = self.height() / 2
        th = 5 if (self._hover or self._drag) else 4
        groove = QRectF(m, cy - th / 2, w, th)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 38))
        p.drawRoundedRect(groove, th / 2, th / 2)
        x = m + w * self._v
        if self._v > 0:
            g = QLinearGradient(m, 0, m + w, 0)
            g.setColorAt(0, QColor(PINK))
            g.setColorAt(0.6, QColor(MAGENTA))
            g.setColorAt(1, QColor(CYAN))
            p.setBrush(g)
            p.drawRoundedRect(QRectF(m, cy - th / 2, x - m, th), th / 2, th / 2)
        kr = self._knob + (1.5 if (self._hover or self._drag) else 0)
        glow = QRadialGradient(QPointF(x, cy), kr * 2.4)
        glow.setColorAt(0, qcolor(CYAN, 0.55))
        glow.setColorAt(1, qcolor(CYAN, 0))
        p.setBrush(glow)
        p.drawEllipse(QPointF(x, cy), kr * 2.4, kr * 2.4)
        p.setBrush(QColor("#ffffff"))
        p.setPen(QPen(QColor(CYAN), 1.4))
        p.drawEllipse(QPointF(x, cy), kr, kr)


class Marquee(QWidget):
    """Single-line label that scrolls when the text does not fit."""

    def __init__(self, font, color=TEXT, parent=None, glow=None):
        super().__init__(parent)
        self.setFont(font)
        self._text = ""
        self._color = QColor(color)
        self._glow = glow
        self._off = 0.0
        self._pause = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        fm = QFontMetrics(font)
        self.setFixedHeight(fm.height() + 4)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def text(self):
        return self._text

    def set_text(self, t):
        if t == self._text:
            return
        self._text = t
        self.setToolTip(t)
        self._off = 0
        self._pause = 60
        self._sync()
        self.update()

    def resizeEvent(self, e):
        self._sync()

    def _sync(self):
        need = QFontMetrics(self.font()).horizontalAdvance(self._text) > self.width()
        if need and not self._timer.isActive() and self.isVisible():
            self._timer.start(33)
        elif not need:
            self._timer.stop()
            self._off = 0

    def showEvent(self, e):
        self._sync()

    def hideEvent(self, e):
        self._timer.stop()

    def _tick(self):
        if self._pause > 0:
            self._pause -= 1
            return
        tw = QFontMetrics(self.font()).horizontalAdvance(self._text) + 48
        self._off += 1.0
        if self._off >= tw:
            self._off = 0
            self._pause = 60
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing)
        fm = QFontMetrics(self.font())
        tw = fm.horizontalAdvance(self._text)
        y = (self.height() + fm.ascent() - fm.descent()) / 2
        scrolling = tw > self.width()
        xs = [-self._off, -self._off + tw + 48] if scrolling else [0]
        if self._glow:
            p.setPen(qcolor(self._glow, 0.45))
            for x in xs:
                p.drawText(QPointF(x + 0.8, y + 0.8), self._text)
        p.setPen(self._color)
        for x in xs:
            p.drawText(QPointF(x, y), self._text)
        if scrolling:  # fade the edges
            p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            for x0, x1 in ((0, 14), (self.width(), self.width() - 14)):
                g = QLinearGradient(x0, 0, x1, 0)
                g.setColorAt(0, QColor(0, 0, 0, 255))
                g.setColorAt(1, QColor(0, 0, 0, 0))
                p.fillRect(QRectF(min(x0, x1), 0, 14, self.height()), g)


class ElideLabel(QLabel):
    """A label that ends in "…" instead of being cut when space runs out."""

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def paintEvent(self, e):
        p = QPainter(self)
        p.setPen(self.palette().color(self.foregroundRole()))
        text = self.fontMetrics().elidedText(self.text(), Qt.ElideRight, self.width())
        p.drawText(self.rect(), int(self.alignment()), text)


class Thumb(QWidget):
    clicked = Signal()

    def __init__(self, w=128, h=72, parent=None):
        super().__init__(parent)
        self.setFixedSize(w, h)
        self._pm = None
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Arată tab-ul în browser")

    def set_pixmap(self, pm):
        self._pm = pm
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        path = QPainterPath()
        path.addRoundedRect(r, 8, 8)
        p.save()
        p.setClipPath(path)
        if self._pm and not self._pm.isNull():
            src = self._pm
            sc = max(r.width() / src.width(), r.height() / src.height())
            sw, sh = src.width() * sc, src.height() * sc
            p.drawPixmap(QRectF(r.center().x() - sw / 2, r.center().y() - sh / 2, sw, sh), src,
                         QRectF(src.rect()))
        else:
            p.fillRect(r, QColor(15, 3, 35, 200))
            lp = logo_pixmap(int(r.height() * 0.7 * self.devicePixelRatioF()))
            lp.setDevicePixelRatio(self.devicePixelRatioF())
            s = r.height() * 0.7
            p.drawPixmap(QRectF(r.center().x() - s / 2, r.center().y() - s / 2, s, s), lp, QRectF(lp.rect()))
        p.restore()
        g = QLinearGradient(0, 0, self.width(), self.height())
        g.setColorAt(0, QColor(PINK))
        g.setColorAt(1, QColor(CYAN))
        p.setPen(QPen(QBrush(g), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)


class Logo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        f = QFont(FONT_DISPLAY, 11)
        f.setWeight(QFont.Black)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
        self.setFont(f)
        fm = QFontMetrics(f)
        self.setFixedSize(fm.horizontalAdvance("YUKITUBE") + 30, 24)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.drawPixmap(QRectF(0, 2, 20, 20), logo_pixmap(int(20 * self.devicePixelRatioF())), QRectF(0, 0, int(20 * self.devicePixelRatioF()), int(20 * self.devicePixelRatioF())))
        fm = QFontMetrics(self.font())
        y = (self.height() + fm.ascent() - fm.descent()) / 2
        path = QPainterPath()
        path.addText(QPointF(26, y), self.font(), "YUKITUBE")
        p.setPen(QPen(qcolor(PINK, 0.35), 3))
        p.drawPath(path)
        g = QLinearGradient(26, 0, self.width(), 0)
        g.setColorAt(0, QColor(PINK))
        g.setColorAt(0.5, QColor("#ff7ad9"))
        g.setColorAt(1, QColor(CYAN))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawPath(path)


class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._on = False
        self._phase = 0.0
        self._t = QTimer(self)
        self._t.timeout.connect(self._tick)
        self._t.start(80)

    def set_on(self, on):
        self._on = on
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.12) % (2 * math.pi)
        if not self._on:
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QPointF(6, 6)
        col = QColor("#39ff9f") if self._on else QColor(PINK)
        a = 1.0 if self._on else 0.45 + 0.55 * (0.5 + 0.5 * math.sin(self._phase))
        g = QRadialGradient(c, 6)
        g.setColorAt(0, qcolor(col.name(), 0.7 * a))
        g.setColorAt(1, qcolor(col.name(), 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(c, 6, 6)
        p.setBrush(qcolor(col.name(), a))
        p.drawEllipse(c, 2.8, 2.8)


# ================================================================ search list
ROLE_DATA = Qt.UserRole + 1


class ResultDelegate(QStyledItemDelegate):
    H = 62

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.f_title = QFont(FONT_UI, 9)
        self.f_title.setWeight(QFont.DemiBold)
        self.f_meta = QFont(FONT_UI, 8)
        self.f_dur = QFont(FONT_MONO, 8)

    def sizeHint(self, opt, idx):
        return QSize(opt.rect.width(), self.H)

    @staticmethod
    def _two_lines(text, fm, width):
        words = text.split()
        lines, cur = [], ""
        for i, w in enumerate(words):
            t = (cur + " " + w).strip()
            if fm.horizontalAdvance(t) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
                if len(lines) == 1:
                    rest = " ".join(words[i:])
                    lines.append(fm.elidedText(rest, Qt.ElideRight, width))
                    return lines
        if cur:
            lines.append(fm.elidedText(cur, Qt.ElideRight, width))
        return lines[:2]

    def paint(self, p, opt, idx):
        d = idx.data(ROLE_DATA) or {}
        r = QRectF(opt.rect).adjusted(4, 2, -4, -2)
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        hover = bool(opt.state & QStyle.State_MouseOver)
        sel = bool(opt.state & QStyle.State_Selected)
        playing = d.get("id") and d.get("id") == self.win.cur_state.get("id")
        if hover or sel:
            g = QLinearGradient(r.left(), 0, r.right(), 0)
            g.setColorAt(0, qcolor(PINK, 0.30 if sel else 0.22))
            g.setColorAt(1, qcolor(PURPLE, 0.05))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawRoundedRect(r, 8, 8)
            p.setBrush(QColor(CYAN if hover else PINK))
            p.drawRoundedRect(QRectF(r.left(), r.top() + 8, 3, r.height() - 16), 1.5, 1.5)
        # thumbnail
        tr = QRectF(r.left() + 8, r.top() + 3, 88, r.height() - 6)
        path = QPainterPath()
        path.addRoundedRect(tr, 6, 6)
        pm = self.win.thumbs.get(d.get("id", ""))
        p.save()
        p.setClipPath(path)
        if pm:
            sc = max(tr.width() / pm.width(), tr.height() / pm.height())
            sw, sh = pm.width() * sc, pm.height() * sc
            p.drawPixmap(QRectF(tr.center().x() - sw / 2, tr.center().y() - sh / 2, sw, sh), pm, QRectF(pm.rect()))
        else:
            p.fillRect(tr, QColor(30, 6, 60, 200))
            self.win.request_thumb(d.get("id", ""), lambda *_: self.win.results_view.viewport().update())
        dur = d.get("duration", "")
        if dur:
            p.setFont(self.f_dur)
            fm = QFontMetrics(self.f_dur)
            dw = fm.horizontalAdvance(dur) + 8
            dr = QRectF(tr.right() - dw - 3, tr.bottom() - fm.height() - 3, dw, fm.height())
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(10, 0, 25, 210))
            p.drawRoundedRect(dr, 3, 3)
            p.setPen(QColor(YELLOW if dur == "LIVE" else TEXT))
            p.drawText(dr, Qt.AlignCenter, dur)
        p.restore()
        p.setPen(QPen(qcolor(PINK if playing else CYAN, 0.8 if playing else 0.35), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        # text
        x = tr.right() + 10
        w = r.right() - x - 6
        p.setFont(self.f_title)
        fm = QFontMetrics(self.f_title)
        y = r.top() + 4 + fm.ascent()
        p.setPen(QColor(PINK if playing else TEXT))
        for ln in self._two_lines(d.get("title", ""), fm, w):
            p.drawText(QPointF(x, y), ln)
            y += fm.height()
        p.setFont(self.f_meta)
        fm2 = QFontMetrics(self.f_meta)
        meta = d.get("channel", "")
        if d.get("views"):
            meta += "  ·  " + d["views"]
        p.setPen(QColor(CYAN))
        p.drawText(QPointF(x, r.bottom() - 5), fm2.elidedText(meta, Qt.ElideRight, w))
        p.restore()


# ===================================================================== window
SS = f"""
QWidget {{ color: {TEXT}; }}
QToolTip {{ background: #1a0533; color: {TEXT}; border: 1px solid {PINK}; padding: 4px 6px; border-radius: 4px; }}
QLineEdit#search {{
  background: rgba(10, 2, 26, 170); border: 1px solid rgba(255, 42, 109, 140); border-radius: 15px;
  padding: 5px 12px 5px 34px; color: {TEXT}; selection-background-color: {PINK}; font-size: 10pt;
}}
QLineEdit#search:focus {{ border: 1px solid {CYAN}; background: rgba(10, 2, 26, 210); }}
QLabel#time {{ color: {MUTED}; }}
QLabel#channel {{ color: {CYAN}; }}
QLabel#hint {{ color: {MUTED}; }}
QLabel#badge {{ color: #1a0533; background: {YELLOW}; border-radius: 4px; padding: 0 5px; font-weight: bold; }}
QAbstractButton#chip {{
  color: {TEXT}; background: rgba(255, 42, 109, 38); border: 1px solid rgba(255, 42, 109, 120);
  border-radius: 9px; padding: 1px 8px; font-size: 8pt;
}}
QAbstractButton#chip:hover {{ border-color: {CYAN}; color: {CYAN}; }}
QAbstractButton#chip:checked {{ background: rgba(255, 42, 109, 160); color: white; }}
QListView {{ background: transparent; border: none; outline: none; }}
QScrollBar:vertical {{ background: transparent; width: 6px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: rgba(255, 42, 109, 140); border-radius: 3px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {CYAN}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: none; }}
QMenu {{ background: rgba(22, 5, 44, 245); border: 1px solid {PINK}; border-radius: 8px; padding: 5px; color: {TEXT}; }}
QMenu::item {{ padding: 5px 22px 5px 18px; border-radius: 5px; }}
QMenu::item:selected {{ background: rgba(255, 42, 109, 110); }}
QMenu::item:disabled {{ color: {MUTED}; }}
QMenu::separator {{ height: 1px; background: rgba(5, 217, 232, 90); margin: 4px 8px; }}
QMenu::indicator {{ width: 10px; height: 10px; left: 4px; }}
QMenu::indicator:checked {{ background: {CYAN}; border-radius: 5px; }}
"""


class Chip(QAbstractButton):
    """Small pill-shaped text button."""

    def __init__(self, text, tip="", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setObjectName("chip")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setToolTip(tip)
        self.setFont(QFont(FONT_MONO, 8))
        self._hover = False
        self._update_size()

    def _update_size(self):
        fm = QFontMetrics(self.font())
        self.setFixedSize(fm.horizontalAdvance(self.text()) + 18, 18)

    def setText(self, t):
        super().setText(t)
        if hasattr(self, "_hover"):
            self._update_size()
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if not self.isEnabled():
            p.setOpacity(0.4)
        on = self.isChecked()
        p.setBrush(qcolor(PINK, 0.65 if on else 0.15))
        p.setPen(QPen(QColor(CYAN) if self._hover else qcolor(PINK, 0.6), 1))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        p.setPen(QColor("#ffffff") if on else (QColor(CYAN) if self._hover else QColor(TEXT)))
        p.drawText(r, Qt.AlignCenter, self.text())


class Player(QWidget):
    PANEL_MARGIN = 10

    def __init__(self):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(logo_icon())
        self.setStyleSheet(SS)
        self.settings = remote_settings()
        self.opacity = float(self.settings.value("opacity", 0.72))
        self.anim_on = self.settings.value("anim", "true") in (True, "true")
        self.mini = self.settings.value("mini", "false") in (True, "true")
        self.on_top = self.settings.value("ontop", "true") in (True, "true")

        # state
        self.tabs = {}         # key -> {conn, state, seen, recv, agent}
        self.bridges = {}      # conn id -> agent kind
        self.selected = None   # user-chosen tab key
        self.cur_key = None
        self.cur_state = {}
        self.hold_time_until = 0
        self.hold_vol_until = 0
        self.search_req = 0
        self.thumbs = {}
        self._thumb_wait = {}
        self.avatars = {}      # url -> QPixmap (null while it loads)
        self.grid_phase = 0.0
        self.player_h = 0

        self.net = QNetworkAccessManager(self)
        self.ws = WsServer(self)
        self.ws.userscript = userscript_bytes()
        self.ws.ping = {"app": "yukitube-remote", "version": VERSION, "tabs": 0}
        self.ws.message.connect(self.on_message)
        self.old_bridge_seen = 0.0
        self.ws.old_bridge.connect(lambda: setattr(self, "old_bridge_seen", time.monotonic()))
        self.ws.disconnected.connect(self.on_disconnect)
        self.ws.open_request.connect(self.handle_open)
        self.host = None       # FirefoxHost, when the remote runs YukiTube's Firefox

        self._build()
        # The window is resized by its edges (see mousePressEvent): any width
        # from the original one up, and any height while the search is open.
        self.setMouseTracking(True)
        for w in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            w.installEventFilter(self)
        self.resize(max(WIDTH + 2 * self.PANEL_MARGIN, int(self.settings.value("width", 0) or 0)), 100)
        self._apply_mini()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.on_top)

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self._tick)
        self.ui_timer.start(250)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._anim)
        self.anim_timer.start(50)
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(lambda: self.ws.broadcast({"type": "ping"}))
        self.ping_timer.start(15000)
        self.vol_timer = QTimer(self)
        self.vol_timer.setSingleShot(True)
        self.vol_timer.timeout.connect(self._send_volume)
        self.docker = Docker(self)

        self.refresh_ui()

    # ------------------------------------------------------------- building
    def _build(self):
        m = self.PANEL_MARGIN
        root = QVBoxLayout(self)
        root.setContentsMargins(m + 12, m + 8, m + 12, m + 10)
        root.setSpacing(6)

        # header
        hdr = QHBoxLayout()
        hdr.setSpacing(4)
        self.logo = Logo()
        hdr.addWidget(self.logo)
        hdr.addSpacing(6)
        self.dot = StatusDot()
        hdr.addWidget(self.dot)
        self.status = ElideLabel()
        self.status.setObjectName("hint")
        self.status.setFont(QFont(FONT_UI, 8))
        self.status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        hdr.addWidget(self.status, 1)
        self.btn_tab = Chip("TAB 1/1", "Schimbă tab-ul YouTube controlat")
        self.btn_tab.clicked.connect(self.tab_menu)
        hdr.addWidget(self.btn_tab)
        self.btn_account = AccountButton()
        self.btn_account.setToolTip("Conectează contul Google")
        self.btn_account.clicked.connect(self.account_menu)
        hdr.addWidget(self.btn_account)
        self.btn_dock = IconButton("dock", 26, 16, "Lipește telecomanda de fereastra YouTube  (D)", checkable=True)
        self.btn_dock.toggled.connect(self.set_docked)
        self.btn_search = IconButton("search", 26, 16, "Caută  (Ctrl+F)", checkable=True)
        self.btn_search.toggled.connect(self.toggle_search)
        self.btn_mini = IconButton("collapse", 26, 16, "Mod compact")
        self.btn_mini.clicked.connect(self.toggle_mini)
        self.btn_menu = IconButton("menu", 26, 16, "Meniu")
        self.btn_menu.clicked.connect(lambda: self.show_menu(self.btn_menu.mapToGlobal(QPoint(0, 26))))
        self.btn_minw = IconButton("min", 26, 14, "Minimizează")
        self.btn_minw.clicked.connect(self.showMinimized)
        self.btn_close = IconButton("close", 26, 15, "Închide", hover=PINK)
        self.btn_close.clicked.connect(self.close)
        for b in (self.btn_dock, self.btn_search, self.btn_mini, self.btn_menu, self.btn_minw, self.btn_close):
            hdr.addWidget(b)
        root.addLayout(hdr)

        # info
        info = QHBoxLayout()
        info.setSpacing(12)
        self.thumb = Thumb()
        self.thumb.clicked.connect(lambda: self.cmd("focus"))
        info.addWidget(self.thumb)
        col = QVBoxLayout()
        col.setSpacing(2)
        ft = QFont(FONT_UI, 11)
        ft.setWeight(QFont.Bold)
        self.title = Marquee(ft, TEXT, glow=PINK)
        col.addWidget(self.title)
        self.channel = QLabel("")
        self.channel.setObjectName("channel")
        self.channel.setFont(QFont(FONT_UI, 9))
        self.channel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        col.addWidget(self.channel)
        col.addStretch(1)
        chips = QHBoxLayout()
        chips.setSpacing(5)
        self.btn_like = IconButton("like", 24, 14, "Like", checkable=True)
        self.btn_like.clicked.connect(lambda: self.cmd("like"))
        chips.addWidget(self.btn_like)
        self.btn_speed = Chip("1.0×", "Viteza de redare")
        self.btn_speed.clicked.connect(self.speed_menu)
        chips.addWidget(self.btn_speed)
        self.badge_ad = QLabel("AD")
        self.badge_ad.setObjectName("badge")
        self.badge_ad.setFont(QFont(FONT_MONO, 8))
        chips.addWidget(self.badge_ad)
        self.btn_skip = Chip("SKIP ▸", "Sari peste reclamă (dacă se poate)")
        self.btn_skip.clicked.connect(lambda: self.cmd("skipAd"))
        chips.addWidget(self.btn_skip)
        chips.addStretch(1)
        self.btn_open = IconButton("open", 24, 14, "Arată / ascunde fereastra YouTube")
        self.btn_open.clicked.connect(self.toggle_youtube)
        chips.addWidget(self.btn_open)
        col.addLayout(chips)
        info.addLayout(col, 1)
        self.info_w = QWidget()
        self.info_w.setLayout(info)
        info.setContentsMargins(0, 2, 0, 0)
        root.addWidget(self.info_w)

        # mini title (only in compact mode)
        fmini = QFont(FONT_UI, 9)
        fmini.setWeight(QFont.DemiBold)
        self.mini_title = Marquee(fmini, TEXT, glow=PINK)
        root.addWidget(self.mini_title)

        # seek
        seek = QHBoxLayout()
        seek.setSpacing(8)
        fmono = QFont(FONT_MONO, 9)
        self.t_cur = QLabel("0:00")
        self.t_cur.setObjectName("time")
        self.t_cur.setFont(fmono)
        self.t_cur.setMinimumWidth(42)
        self.t_dur = QLabel("0:00")
        self.t_dur.setObjectName("time")
        self.t_dur.setFont(fmono)
        self.t_dur.setMinimumWidth(42)
        self.t_dur.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.seek = NeonSlider()
        self.seek.tip_fn = lambda v: fmt_time(v * (self.cur_state.get("duration") or 0))
        self.seek.moved.connect(lambda v: self.t_cur.setText(fmt_time(v * (self.cur_state.get("duration") or 0))))
        self.seek.released.connect(self.on_seek)
        seek.addWidget(self.t_cur)
        seek.addWidget(self.seek, 1)
        seek.addWidget(self.t_dur)
        self.seek_w = QWidget()
        self.seek_w.setLayout(seek)
        seek.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.seek_w)

        # controls
        ctl = QHBoxLayout()
        ctl.setSpacing(2)
        self.btn_loop = IconButton("loop", 32, 18, "Repetă videoclipul  (L)", checkable=True)
        self.btn_loop.clicked.connect(lambda: self.cmd("loop", self.btn_loop.isChecked()))
        self.btn_prev = IconButton("prev", 34, 22, "Anterior  (P)")
        self.btn_prev.clicked.connect(lambda: self.cmd("prev"))
        self.btn_rew = IconButton("rew", 34, 20, "Înapoi 10 s  (←)")
        self.btn_rew.clicked.connect(lambda: self.cmd("seekRel", -10))
        self.btn_play = PlayButton()
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_fwd = IconButton("fwd", 34, 20, "Înainte 10 s  (→)")
        self.btn_fwd.clicked.connect(lambda: self.cmd("seekRel", 10))
        self.btn_next = IconButton("next", 34, 22, "Următorul  (N)")
        self.btn_next.clicked.connect(lambda: self.cmd("next"))
        self.btn_stop = IconButton("stop", 32, 20, "Stop  (S)")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_vol = IconButton("vol", 30, 18, "Mut  (M)")
        self.btn_vol.clicked.connect(lambda: self.cmd("mute"))
        self.vol = NeonSlider(height=16, knob=5)
        self.vol.setFixedWidth(92)
        self.vol.tip_fn = lambda v: f"Volum {int(round(v * 100))}%"
        self.vol.moved.connect(self.on_volume)
        self.vol.released.connect(self.on_volume)
        for b in (self.btn_loop, self.btn_prev, self.btn_rew):
            ctl.addWidget(b)
        ctl.addSpacing(2)
        ctl.addWidget(self.btn_play)
        ctl.addSpacing(2)
        for b in (self.btn_fwd, self.btn_next, self.btn_stop):
            ctl.addWidget(b)
        ctl.addStretch(1)
        ctl.addWidget(self.btn_vol)
        ctl.addWidget(self.vol)
        self.ctl_w = QWidget()
        self.ctl_w.setLayout(ctl)
        ctl.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.ctl_w)

        # search panel
        self.search_panel = QWidget()
        sp = QVBoxLayout(self.search_panel)
        sp.setContentsMargins(0, 8, 0, 0)
        sp.setSpacing(6)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("search")
        self.search_edit.setPlaceholderText("Caută pe YouTube…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.returnPressed.connect(self.do_search)
        sp.addWidget(self.search_edit)
        self._search_icon = QLabel(self.search_edit)
        self._search_icon.setPixmap(icons.pixmap("search", PINK, 16, self.devicePixelRatioF()))
        self._search_icon.move(12, 8)
        self._search_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.search_status = QLabel("")
        self.search_status.setObjectName("hint")
        self.search_status.setFont(QFont(FONT_UI, 8))
        self.search_status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        sp.addWidget(self.search_status)
        self.results_model = QStandardItemModel(self)
        self.results_view = QListView()
        self.results_view.setModel(self.results_model)
        self.results_view.setItemDelegate(ResultDelegate(self))
        self.results_view.setMouseTracking(True)
        self.results_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.results_view.verticalScrollBar().setSingleStep(16)
        self.results_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_view.setMinimumHeight(ResultDelegate.H * 2 + 4)
        self.results_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_view.setCursor(Qt.PointingHandCursor)
        self.results_view.clicked.connect(self.on_result_clicked)
        self.results_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_view.customContextMenuRequested.connect(self.result_menu)
        self.results_view.viewport().installEventFilter(self)
        sp.addWidget(self.results_view)
        self.search_panel.hide()
        # A taller window means more results, not a taller player.
        root.addWidget(self.search_panel, 1)

        # tray
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(logo_icon(), self)
            self.tray.setToolTip(APP_NAME)
            tm = QMenu()
            tm.setStyleSheet(SS)
            tm.addAction("Play / Pauză", self.toggle_play)
            tm.addAction("Următorul", lambda: self.cmd("next"))
            tm.addAction("Anterior", lambda: self.cmd("prev"))
            tm.addSeparator()
            tm.addAction("Arată / ascunde telecomanda", self.toggle_visible)
            tm.addAction("Arată / ascunde fereastra YouTube", self.toggle_youtube)
            tm.addAction("Ieșire", QApplication.quit)
            self.tray.setContextMenu(tm)
            self.tray.activated.connect(
                lambda r: self.toggle_visible() if r == QSystemTrayIcon.Trigger else None)
            self.tray.show()
            self._tray_menu = tm

    # ------------------------------------------------------------- painting
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m = self.PANEL_MARGIN
        r = QRectF(self.rect()).adjusted(m, m, -m, -m)
        rad = 18
        a = self.opacity

        # soft outer glow
        p.setBrush(Qt.NoBrush)
        for i in range(m, 0, -2):
            p.setPen(QPen(qcolor(PINK, 0.05 * (1 - i / m) * (0.4 + a)), 2))
            p.drawRoundedRect(r.adjusted(-i, -i, i, i), rad + i, rad + i)

        panel = QPainterPath()
        panel.addRoundedRect(r, rad, rad)
        bg = QLinearGradient(0, r.top(), 0, r.bottom())
        bg.setColorAt(0, QColor(14, 3, 34, int(255 * a)))
        bg.setColorAt(0.55, QColor(34, 6, 62, int(255 * a)))
        bg.setColorAt(1, QColor(22, 3, 40, int(255 * min(1, a + 0.1))))
        p.fillPath(panel, bg)

        p.save()
        p.setClipPath(panel)
        ph = self.player_h or r.height()
        horizon = r.top() + ph * (0.60 if not self.mini else 0.55)
        bottom = r.top() + ph + 4

        # sun
        sr = min(70.0, ph * 0.42)
        cx = r.right() - 92
        sun = QRectF(cx - sr, horizon - sr * 1.15, sr * 2, sr * 2)
        sg = QLinearGradient(0, sun.top(), 0, horizon)
        sg.setColorAt(0, qcolor(YELLOW, 0.55))
        sg.setColorAt(0.55, qcolor(ORANGE, 0.45))
        sg.setColorAt(1, qcolor(PINK, 0.40))
        sunp = QPainterPath()
        sunp.addEllipse(sun)
        top = QPainterPath()
        top.addRect(QRectF(r.left(), r.top(), r.width(), horizon - r.top()))
        stripes = QPainterPath()
        y, h = horizon - sr * 0.62, 1.6
        while y < horizon:
            stripes.addRect(QRectF(r.left(), y, r.width(), h))
            y += h * 2.4
            h *= 1.3
        halo = QRadialGradient(QPointF(cx, horizon - sr * 0.15), sr * 1.8)
        halo.setColorAt(0, qcolor(PINK, 0.20))
        halo.setColorAt(1, qcolor(PINK, 0))
        p.fillRect(QRectF(cx - sr * 2, horizon - sr * 2, sr * 4, sr * 2), halo)
        p.fillPath(sunp.intersected(top).subtracted(stripes), sg)

        # perspective grid
        if bottom > horizon:
            fade = QLinearGradient(0, horizon, 0, bottom)
            fade.setColorAt(0, QColor(30, 2, 50, int(120 * a)))
            fade.setColorAt(1, QColor(10, 0, 25, int(200 * a)))
            p.fillRect(QRectF(r.left(), horizon, r.width(), bottom - horizon), fade)
            vx = r.center().x()
            gh = bottom - horizon
            for i in range(-14, 15):
                x0 = vx + i * 14
                x1 = vx + i * 90
                p.setPen(QPen(qcolor(MAGENTA, 0.30), 1))
                p.drawLine(QPointF(x0, horizon), QPointF(x1, bottom + gh * 0.4))
            n = 9
            for k in range(n):
                t = ((k + self.grid_phase) / n)
                yy = horizon + gh * t * t
                p.setPen(QPen(qcolor(MAGENTA, 0.12 + 0.30 * t), 1))
                p.drawLine(QPointF(r.left(), yy), QPointF(r.right(), yy))
            hg = QLinearGradient(r.left(), 0, r.right(), 0)
            hg.setColorAt(0, qcolor(CYAN, 0.0))
            hg.setColorAt(0.5, qcolor(CYAN, 0.75))
            hg.setColorAt(1, qcolor(PINK, 0.0))
            p.setPen(QPen(QBrush(hg), 1.4))
            p.drawLine(QPointF(r.left(), horizon), QPointF(r.right(), horizon))

        # search area gets a calmer, darker backdrop
        if self.search_panel.isVisible():
            sr2 = QRectF(r.left(), bottom, r.width(), r.bottom() - bottom)
            p.fillRect(sr2, QColor(8, 1, 20, int(150 * a + 40)))
            sep = QLinearGradient(r.left(), 0, r.right(), 0)
            sep.setColorAt(0, qcolor(PINK, 0))
            sep.setColorAt(0.5, qcolor(PINK, 0.8))
            sep.setColorAt(1, qcolor(PINK, 0))
            p.setPen(QPen(QBrush(sep), 1))
            p.drawLine(QPointF(r.left() + 20, bottom), QPointF(r.right() - 20, bottom))

        # scanlines
        p.setPen(QPen(QColor(0, 0, 0, 22), 1))
        y = r.top()
        while y < r.bottom():
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
            y += 3
        p.restore()

        border = QLinearGradient(r.topLeft(), r.bottomRight())
        border.setColorAt(0, QColor(PINK))
        border.setColorAt(0.5, QColor(PURPLE))
        border.setColorAt(1, QColor(CYAN))
        p.setPen(QPen(QBrush(border), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(panel)

    def resizeEvent(self, e):
        self._measure()
        super().resizeEvent(e)

    def _fit(self):
        """Size limits from the layout: the width never below the original
        one; the height fixed to the player alone, or free (down to two
        results) while the search is open, where the height last chosen for
        it comes back."""
        lay = self.layout()
        lay.invalidate()
        lay.activate()
        need = lay.totalMinimumSize()
        minw = max(WIDTH + 2 * self.PANEL_MARGIN, need.width())
        minh = need.height()
        if self.search_panel.isVisible():
            h = int(self.settings.value("search_h", 0) or 0) or minh + ResultDelegate.H * 3
            self.setMinimumSize(minw, minh)
            self.setMaximumSize(16777215, 16777215)
        else:
            h = minh
            self.setMinimumSize(minw, minh)
            self.setMaximumSize(16777215, minh)
        self.resize(max(self.width(), minw), max(h, minh))
        self._measure()
        self.update()

    def save_size(self):
        self.settings.setValue("width", self.width())
        if self.search_panel.isVisible():
            self.settings.setValue("search_h", self.height())

    GRIP = 6  # px of the panel's edge, beyond the glow margin, that resize

    def _edges(self, pos):
        g = self.PANEL_MARGIN + self.GRIP
        edges = Qt.Edge(0)
        if pos.x() < g:
            edges |= Qt.LeftEdge
        elif pos.x() >= self.width() - g:
            edges |= Qt.RightEdge
        if self.minimumHeight() != self.maximumHeight():
            if pos.y() < g:
                edges |= Qt.TopEdge
            elif pos.y() >= self.height() - g:
                edges |= Qt.BottomEdge
        return edges

    @staticmethod
    def _edge_cursor(edges):
        horiz = edges & (Qt.LeftEdge | Qt.RightEdge)
        vert = edges & (Qt.TopEdge | Qt.BottomEdge)
        if horiz and vert:
            fdiag = edges in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge)
            return Qt.SizeFDiagCursor if fdiag else Qt.SizeBDiagCursor
        if horiz:
            return Qt.SizeHorCursor
        if vert:
            return Qt.SizeVerCursor
        return None

    def mouseMoveEvent(self, e):
        if not e.buttons():
            cur = self._edge_cursor(self._edges(e.position().toPoint()))
            if cur is None:
                self.unsetCursor()
            else:
                self.setCursor(cur)
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self.unsetCursor()
        super().leaveEvent(e)

    def _measure(self):
        # height of the "player" part (everything above the search panel)
        g = self.ctl_w.geometry()
        self.player_h = g.bottom() + 8 - self.PANEL_MARGIN

    def _anim(self):
        playing = self.cur_state and not self.cur_state.get("paused", True)
        if self.anim_on and playing and self.isVisible() and not self.isMinimized():
            self.grid_phase = (self.grid_phase + 0.04) % 1.0
            self.update(0, 0, self.width(), self.PANEL_MARGIN + self.player_h + 10)

    # ------------------------------------------------------------- window ui
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            wh = self.windowHandle()
            edges = self._edges(e.position().toPoint())
            if edges and wh is not None and wh.startSystemResize(edges):
                return
            # Moving the remote by hand takes it off the YouTube window.
            if self.btn_dock.isChecked():
                self.btn_dock.setChecked(False)
            if wh is not None:
                wh.startSystemMove()
        elif e.button() == Qt.RightButton:
            self.show_menu(e.globalPosition().toPoint())

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.toggle_mini()

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            self.set_opacity(self.opacity + (0.05 if e.angleDelta().y() > 0 else -0.05))
        else:
            self.vol.wheelEvent(e)

    def set_opacity(self, v):
        self.opacity = max(0.15, min(1.0, v))
        self.settings.setValue("opacity", self.opacity)
        self.update()

    def toggle_visible(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def toggle_mini(self):
        self.mini = not self.mini
        self.settings.setValue("mini", self.mini)
        self._apply_mini()

    def _apply_mini(self):
        self.info_w.setVisible(not self.mini)
        self.mini_title.setVisible(self.mini)
        self.btn_mini.set_icon("expand" if self.mini else "collapse")
        self.btn_mini.setToolTip("Mod complet" if self.mini else "Mod compact")
        for w in (self.t_cur, self.t_dur):
            w.setVisible(not self.mini)
        self._fit()

    def set_on_top(self, on):
        self.on_top = on
        self.settings.setValue("ontop", on)
        vis = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on)
        if vis:
            self.show()

    def toggle_search(self, on):
        if not on:
            self.save_size()
        self.search_panel.setVisible(on)
        if on:
            self.search_edit.setFocus()
            self.search_edit.selectAll()
        self._fit()

    def show_menu(self, pos):
        m = QMenu(self)
        a = m.addAction("Mereu deasupra")
        a.setCheckable(True)
        a.setChecked(self.on_top)
        a.toggled.connect(self.set_on_top)
        a = m.addAction("Mod compact")
        a.setCheckable(True)
        a.setChecked(self.mini)
        a.triggered.connect(self.toggle_mini)
        a = m.addAction("Animație grilă")
        a.setCheckable(True)
        a.setChecked(self.anim_on)
        a.toggled.connect(lambda v: (setattr(self, "anim_on", v), self.settings.setValue("anim", v)))
        om = m.addMenu("Transparență")
        for pct in (100, 85, 70, 55, 40, 25):
            act = om.addAction(f"{pct}% opac")
            act.setCheckable(True)
            act.setChecked(abs(self.opacity - pct / 100) < 0.026)
            act.triggered.connect(lambda _=False, v=pct / 100: self.set_opacity(v))
        m.addSeparator()
        if self.host:
            m.addAction("Ascunde fereastra YouTube" if self.youtube_shown() else "Arată fereastra YouTube",
                        self.toggle_youtube)
        else:
            m.addAction("Deschide YouTube", self.open_youtube)
        m.addAction("Conectează YukiTube (instalează puntea)", self.install_bridge)
        m.addAction("Cum conectez browserul?", self.show_help)
        m.addSeparator()
        m.addAction(f"Despre {APP_NAME} {VERSION}", self.show_about)
        m.addAction("Ieșire", QApplication.quit)
        m.exec(pos)

    def show_help(self):
        QMessageBox.information(
            self, f"{APP_NAME} — conectare",
            "În YukiTube: meniul ⋮ → „Conectează YukiTube (instalează puntea)”,\n"
            "apoi apasă „Install” / „Instalează” în pagina Violentmonkey.\n"
            "YukiTube face asta singur la prima pornire.\n\n"
            "Alt browser (Chrome, Edge, Firefox obișnuit…): instalează Violentmonkey\n"
            "sau Tampermonkey, apoi deschide în acel browser\n"
            f"http://127.0.0.1:{PORT}/yukitube.user.js și apasă Install.\n"
            "(Pentru Chrome/Edge există și extensia din remote/browser/extension\n"
            "din sursele YukiTube: „Load unpacked” în modul dezvoltator.)\n\n"
            "Apoi reîncarcă tab-ul YouTube. Punctul din colț devine verde.")

    def show_about(self):
        QMessageBox.about(
            self, APP_NAME,
            f"<b>{APP_NAME} {VERSION}</b><br>Telecomanda retrowave a YukiTube.<br><br>"
            f"Port local: 127.0.0.1:{PORT}<br>"
            "Scurtături: Space, S (stop), ←/→, ↑/↓, M, L, N, P, D (lipește), Ctrl+F, Ctrl+rotiță = transparență")

    def keyPressEvent(self, e):
        k = e.key()
        ctrl = e.modifiers() & Qt.ControlModifier
        if (ctrl and k == Qt.Key_F) or k == Qt.Key_Slash:
            self.btn_search.setChecked(True)
            self.search_edit.setFocus()
            self.search_edit.selectAll()
        elif k == Qt.Key_Escape:
            if self.search_panel.isVisible():
                self.btn_search.setChecked(False)
        elif k in (Qt.Key_Space, Qt.Key_K, Qt.Key_MediaPlay, Qt.Key_MediaTogglePlayPause):
            self.toggle_play()
        elif k == Qt.Key_Left or k == Qt.Key_J:
            self.cmd("seekRel", -10 if k == Qt.Key_J else -5)
        elif k == Qt.Key_Right:
            self.cmd("seekRel", 5)
        elif k == Qt.Key_Up:
            self.nudge_volume(5)
        elif k == Qt.Key_Down:
            self.nudge_volume(-5)
        elif k == Qt.Key_M:
            self.cmd("mute")
        elif k == Qt.Key_L:
            self.btn_loop.setChecked(not self.btn_loop.isChecked())
            self.cmd("loop", self.btn_loop.isChecked())
        elif k in (Qt.Key_S, Qt.Key_MediaStop):
            self.stop()
        elif k == Qt.Key_D:
            self.btn_dock.toggle()
        elif k in (Qt.Key_N, Qt.Key_MediaNext):
            self.cmd("next")
        elif k in (Qt.Key_P, Qt.Key_MediaPrevious):
            self.cmd("prev")
        else:
            super().keyPressEvent(e)

    def eventFilter(self, obj, ev):
        # Leaving the resize edge for a child widget: back to the arrow.
        if ev.type() == ev.Type.Enter and obj.parent() is self:
            self.unsetCursor()
        if obj is self.results_view.viewport() and ev.type() == ev.Type.MouseButtonRelease:
            if ev.button() == Qt.MiddleButton:
                idx = self.results_view.indexAt(ev.position().toPoint())
                if idx.isValid():
                    self.open_in_browser(idx.data(ROLE_DATA))
                    return True
        return super().eventFilter(obj, ev)

    def closeEvent(self, e):
        self.settings.setValue("pos", self.pos())
        self.save_size()
        QApplication.quit()

    # ----------------------------------------------------------- networking
    def on_message(self, cid, msg):
        t = msg.get("type")
        key = msg.get("tab")
        if t == "hello" and not key:
            self.bridges[cid] = msg.get("agent", "extension")
            self.refresh_ui()
            return
        if t == "pong":
            return
        if cid == HTTP_CID and key not in self.tabs and t not in ("hello", "state", "alive"):
            return
        if not key:
            return
        if t == "bye":
            if self.tabs.pop(key, None) is not None:
                self.refresh_ui()
            return
        if cid != HTTP_CID:
            self.bridges.setdefault(cid, msg.get("agent", "extension"))
        tab = self.tabs.get(key)
        if tab is None:
            tab = self.tabs[key] = {"conn": cid, "state": {}, "seen": time.monotonic(), "recv": time.monotonic(),
                                    "agent": msg.get("agent", "")}
        tab["conn"] = cid
        tab["seen"] = time.monotonic()
        if t == "state":
            tab["state"] = msg.get("state") or {}
            tab["recv"] = time.monotonic()
            self.refresh_ui()
        elif t == "search_results":
            self.on_agent_results(msg)
        elif t == "hello":
            self.refresh_ui()
        elif t == "alive" and not tab["state"]:
            self.refresh_ui()

    def on_disconnect(self, cid):
        self.bridges.pop(cid, None)
        for k in [k for k, t in self.tabs.items() if t["conn"] == cid]:
            del self.tabs[k]
        self.refresh_ui()

    def pick_tab(self):
        if self.selected in self.tabs:
            return self.selected
        if not self.tabs:
            return None
        playing = [k for k, t in self.tabs.items() if t["state"] and not t["state"].get("paused", True)]
        if playing:
            if self.cur_key in playing:
                return self.cur_key
            return max(playing, key=lambda k: self.tabs[k]["state"].get("lastPlayed", 0))
        if self.cur_key in self.tabs:
            return self.cur_key
        withvid = [k for k in self.tabs if self.tabs[k]["state"].get("hasVideo")]
        pool = withvid or list(self.tabs)
        return max(pool, key=lambda k: (self.tabs[k]["state"].get("lastPlayed", 0), self.tabs[k]["seen"]))

    def cmd(self, action, value=None, extra=None):
        key = self.cur_key
        if not key or key not in self.tabs:
            return False
        msg = {"type": "cmd", "tab": key, "action": action}
        if value is not None:
            msg["value"] = value
        if extra:
            msg.update(extra)
        return self.ws.send(self.tabs[key]["conn"], msg)

    # ------------------------------------------------------------ actions
    def stop(self):
        if self.cmd("stop"):
            self.cur_state["paused"] = True
            self.cur_state["time"] = 0
            self.btn_play.set_icon("play")
            self.hold_time_until = time.monotonic() + 1.5

    def set_docked(self, on):
        if on and not self.docker.available():
            self.btn_dock.setChecked(False)
            QMessageBox.information(
                self, APP_NAME,
                "Lipirea de fereastra YouTube merge pe Hyprland și pe Windows.\n"
                "Pe acest desktop telecomanda nu poate afla unde e fereastra YouTube.")
            return
        self.settings.setValue("docked", on)
        self.docker.set_enabled(on)

    def toggle_play(self):
        if self.cmd("toggle"):
            st = self.cur_state
            st["paused"] = not st.get("paused", True)
            self.btn_play.set_icon("play" if st["paused"] else "pause")
            tab = self.tabs.get(self.cur_key)
            if tab:
                tab["recv"] = time.monotonic()

    def on_seek(self, v):
        d = self.cur_state.get("duration") or 0
        if d > 0:
            t = v * d
            self.cmd("seek", t)
            self.cur_state["time"] = t
            tab = self.tabs.get(self.cur_key)
            if tab:
                tab["recv"] = time.monotonic()
            self.hold_time_until = time.monotonic() + 1.2

    def on_volume(self, v):
        self.hold_vol_until = time.monotonic() + 1.5
        self._pending_vol = int(round(v * 100))
        self._update_vol_icon(self._pending_vol, False)
        if not self.vol_timer.isActive():
            self.vol_timer.start(70)

    def _send_volume(self):
        self.cmd("volume", getattr(self, "_pending_vol", 50))

    def nudge_volume(self, d):
        cur = int(round(self.vol.value() * 100))
        v = max(0, min(100, cur + d))
        self.vol.set_value(v / 100)
        self.on_volume(v / 100)

    def _update_vol_icon(self, vol, muted):
        self.btn_vol.set_icon("mute" if muted or vol == 0 else ("vol_low" if vol < 50 else "vol"))

    def speed_menu(self):
        m = QMenu(self)
        cur = self.cur_state.get("rate", 1)
        for r in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0):
            a = m.addAction(f"{r:g}×")
            a.setCheckable(True)
            a.setChecked(abs(cur - r) < 0.01)
            a.triggered.connect(lambda _=False, r=r: self.cmd("rate", r))
        m.exec(self.btn_speed.mapToGlobal(QPoint(0, self.btn_speed.height())))

    def tab_menu(self):
        m = QMenu(self)
        a = m.addAction("Automat (tab-ul care cântă)")
        a.setCheckable(True)
        a.setChecked(self.selected is None)
        a.triggered.connect(lambda: self._select_tab(None))
        m.addSeparator()
        for i, (k, t) in enumerate(self.tabs.items(), 1):
            st = t["state"]
            name = st.get("title") or st.get("host") or k
            if len(name) > 48:
                name = name[:47] + "…"
            icon = "▶ " if not st.get("paused", True) else "   "
            a = m.addAction(f"{icon}{i}. {name}  —  {browser_name(st)}")
            a.setCheckable(True)
            a.setChecked(k == self.cur_key)
            a.triggered.connect(lambda _=False, k=k: self._select_tab(k))
        m.exec(self.btn_tab.mapToGlobal(QPoint(0, self.btn_tab.height())))

    def _select_tab(self, key):
        self.selected = key
        self.refresh_ui()

    # ------------------------------------------------------ YukiTube Firefox
    def host_firefox(self, firefox, profile, arg=""):
        from firefox_host import FirefoxHost
        self.host = FirefoxHost(firefox, profile, userscript_bytes().decode("utf-8"), self)
        self.host.state_changed.connect(self.refresh_ui)
        self.host.prepared.connect(lambda ok: self.refresh_ui())
        url = self._watch_url(arg)
        self.host.start(url)
        if arg and not url:
            QTimer.singleShot(0, lambda: self.handle_open(arg))

    @staticmethod
    def _watch_url(arg):
        """A link to one video, as a watch URL; "" for anything else."""
        u = QUrl(arg if "://" in arg else "https://" + arg)
        host = u.host().lower()
        from PySide6.QtCore import QUrlQuery
        vid = QUrlQuery(u).queryItemValue("v") if u.path() == "/watch" else ""
        if host == "youtu.be":
            vid = u.path().strip("/")
        elif u.path().startswith(("/shorts/", "/live/")):
            vid = u.path().split("/")[2]
        if vid and (host.endswith("youtube.com") or host == "youtu.be"):
            return f"https://www.youtube.com/watch?v={vid}"
        return ""

    def handle_open(self, arg):
        """YukiTube launched with a link or words (or again, while running)."""
        arg = (arg or "").strip()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if not arg:
            return
        from PySide6.QtCore import QUrlQuery
        u = QUrl(arg)
        q = QUrlQuery(u).queryItemValue("search_query", QUrl.FullyDecoded) if u.path() == "/results" else ""
        is_link = "://" in arg or arg.startswith(("www.", "youtube.com", "youtu.be", "m.youtube.com"))
        if q or not is_link:
            # Searches happen in the remote.
            self.btn_search.setChecked(True)
            self.search_edit.setText(q or arg)
            self.do_search()
            return
        watch = self._watch_url(arg)
        if watch:
            vid = watch.rsplit("=", 1)[1]
            if self.cur_key and self.cmd("open", {"id": vid}):
                return
            if self.host:
                self.host.navigate_headless(watch)
                return
        self.open_url(arg)

    def youtube_shown(self):
        return bool(self.host and self.host.visible and self.host.running())

    def _here_url(self):
        """What plays now, to carry over when Firefox restarts."""
        st = self.cur_state
        if st.get("hasVideo") and st.get("id"):
            t = int(self._cur_time())
            return f"https://www.youtube.com/watch?v={st['id']}" + (f"&t={t}s" if t > 2 else "")
        return None

    def toggle_youtube(self):
        if not self.host:
            self.open_youtube()
        elif self.youtube_shown():
            self.host.hide(self._here_url())
        else:
            self.host.show(self._here_url())

    def open_youtube(self):
        if self.host:
            if not self.youtube_shown():
                self.host.show(self._here_url())
            return
        if self.cur_key:
            self.cmd("focus")
            return
        self.open_url("https://www.youtube.com/")

    def open_url(self, url):
        # In YukiTube, pages to look at (sign-in, a new video page) get the
        # Firefox window.
        if self.host:
            self.host.show(url)
            return
        for cid, kind in self.bridges.items():
            if kind == "extension":
                if self.ws.send(cid, {"type": "newtab", "url": url}):
                    return
        if YUKITUBE_OPEN and QProcess.startDetached(YUKITUBE_OPEN, [url]):
            return
        QDesktopServices.openUrl(QUrl(url))

    # ------------------------------------------------------------- account
    def account_menu(self):
        acc = self.cur_state.get("account") or {}
        if not acc.get("loggedIn"):
            self.open_url(SIGNIN_URL)
            if self.host and self.tray:
                self.tray.showMessage(APP_NAME, "După ce te autentifici, închide fereastra YouTube: "
                                      "YukiTube continuă în telecomandă.", logo_icon(), 8000)
            return
        m = QMenu(self)
        a = m.addAction("✓ Conectat cu contul Google")
        a.setEnabled(False)
        m.addSeparator()
        m.addAction("Schimbă contul", lambda: self.open_url(SWITCH_URL))
        m.addAction("Deconectare", lambda: self.open_url(SIGNOUT_URL))
        m.exec(self.btn_account.mapToGlobal(QPoint(0, self.btn_account.height())))

    def _sync_account(self, connected):
        acc = (self.cur_state.get("account") or {}) if connected else {}
        logged_in = acc.get("loggedIn")
        url = acc.get("avatar") or ""
        host = QUrl(url).host()
        if not (url.startswith("https://") and host.endswith(AVATAR_HOSTS)):
            url = ""
        if url and url not in self.avatars:
            self.avatars[url] = QPixmap()
            rep = self.net.get(QNetworkRequest(QUrl(url)))
            rep.finished.connect(lambda: self._on_avatar(rep, url))
        self.btn_account.set_account(logged_in, self.avatars.get(url) if url else None)
        self.btn_account.setToolTip("Cont Google conectat" if logged_in else "Conectează contul Google")

    def _on_avatar(self, rep, url):
        rep.deleteLater()
        pm = QPixmap()
        if rep.error() == QNetworkReply.NoError:
            pm.loadFromData(bytes(rep.readAll().data()))
        self.avatars[url] = pm
        self.refresh_ui()

    def install_bridge(self):
        # Violentmonkey (in YukiTube's Firefox) catches *.user.js links and
        # shows its Install page.
        self.open_url(f"http://127.0.0.1:{PORT}/yukitube.user.js")

    def open_in_browser(self, d):
        if d and d.get("id"):
            self.open_url(f"https://www.youtube.com/watch?v={d['id']}")

    def play_result(self, d):
        if not d or not d.get("id"):
            return
        if self.cur_key and self.cmd("open", {"id": d["id"]}):
            self.title.set_text(d.get("title", ""))
            self.mini_title.set_text(d.get("title", ""))
            self.channel.setText(d.get("channel", ""))
            return
        self.open_in_browser(d)

    def on_result_clicked(self, idx):
        d = idx.data(ROLE_DATA)
        if QGuiApplication.keyboardModifiers() & Qt.ControlModifier:
            self.open_in_browser(d)
        else:
            self.play_result(d)

    def result_menu(self, pos):
        idx = self.results_view.indexAt(pos)
        if not idx.isValid():
            return
        d = idx.data(ROLE_DATA)
        m = QMenu(self)
        a = m.addAction("Redă în tab-ul curent", lambda: self.play_result(d))
        a.setEnabled(bool(self.cur_key))
        m.addAction("Deschide într-un tab nou", lambda: self.open_in_browser(d))
        m.addAction("Copiază link-ul", lambda: QGuiApplication.clipboard().setText(
            f"https://www.youtube.com/watch?v={d['id']}"))
        m.exec(self.results_view.viewport().mapToGlobal(pos))

    # -------------------------------------------------------------- search
    def do_search(self):
        q = self.search_edit.text().strip()
        if not q:
            return
        self.search_req += 1
        req = self.search_req
        self.search_status.setText(f"Caut „{q}”…")
        self._search_direct(q, req)

    def _search_direct(self, q, req):
        url = QUrl("https://www.youtube.com/results")
        from PySide6.QtCore import QUrlQuery
        qq = QUrlQuery()
        qq.addQueryItem("search_query", q)
        qq.addQueryItem("hl", "en")
        url.setQuery(qq)
        r = QNetworkRequest(url)
        r.setRawHeader(b"User-Agent", ytsearch._UA.encode())
        r.setRawHeader(b"Accept-Language", b"en-US,en;q=0.8")
        r.setRawHeader(b"Cookie", b"SOCS=CAI; CONSENT=YES+")
        r.setTransferTimeout(12000)
        rep = self.net.get(r)
        rep.finished.connect(lambda: self._on_direct(rep, q, req))

    def _on_direct(self, rep, q, req):
        rep.deleteLater()
        if req != self.search_req:
            return
        items, err = [], ""
        if rep.error() == QNetworkReply.NoError:
            try:
                items = ytsearch.parse_results(bytes(rep.readAll().data()).decode("utf-8", "replace"))
            except Exception as ex:  # noqa: BLE001
                err = str(ex)
        else:
            err = rep.errorString()
        if items:
            self.show_results(items, q)
            return
        # fall back to searching through a connected www.youtube.com tab
        for k, t in self.tabs.items():
            if t["state"].get("host") == "www.youtube.com":
                self.ws.send(t["conn"], {"type": "cmd", "tab": k, "action": "search", "value": q, "reqId": req})
                self._pending_q = q
                QTimer.singleShot(8000, lambda: self._search_timeout(req))
                return
        self.search_status.setText(f"Căutarea a eșuat: {err or 'niciun rezultat'}")

    def _search_timeout(self, req):
        if req == self.search_req and self.search_status.text().startswith("Caut"):
            self.search_status.setText("Căutarea a eșuat (timeout).")

    def on_agent_results(self, msg):
        if msg.get("reqId") != self.search_req:
            return
        items = msg.get("items") or []
        if items:
            self.show_results(items, getattr(self, "_pending_q", ""))
        else:
            self.search_status.setText(f"Niciun rezultat. {msg.get('error', '')}")

    def show_results(self, items, q):
        self.results_model.clear()
        for it in items:
            si = QStandardItem()
            si.setData(it, ROLE_DATA)
            si.setToolTip(it.get("title", ""))
            self.results_model.appendRow(si)
        self.results_view.scrollToTop()
        hint = "click = redă în tab · Ctrl/mijloc = tab nou" if self.cur_key else "click = deschide în browser"
        self.search_status.setText(f"{len(items)} rezultate pentru „{q}”  ·  {hint}")

    # ---------------------------------------------------------- thumbnails
    def request_thumb(self, vid, cb=None):
        if not vid:
            return
        if vid in self.thumbs:
            if cb:
                cb(self.thumbs[vid])
            return
        if vid in self._thumb_wait:
            if cb:
                self._thumb_wait[vid].append(cb)
            return
        self._thumb_wait[vid] = [cb] if cb else []
        rep = self.net.get(QNetworkRequest(QUrl(f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg")))
        rep.finished.connect(lambda: self._on_thumb(rep, vid))

    def _on_thumb(self, rep, vid):
        rep.deleteLater()
        pm = QPixmap()
        if rep.error() == QNetworkReply.NoError:
            pm.loadFromData(bytes(rep.readAll().data()))
        cbs = self._thumb_wait.pop(vid, [])
        if pm.isNull():
            return
        self.thumbs[vid] = pm
        for cb in cbs:
            cb(pm)

    # ------------------------------------------------------------ ui sync
    def _tick(self):
        now = time.monotonic()
        stale = [k for k, t in self.tabs.items() if now - t["seen"] > 9]
        for k in stale:
            del self.tabs[k]
        if stale:
            self.refresh_ui()
        else:
            self._update_time()

    def _cur_time(self):
        st = self.cur_state
        tab = self.tabs.get(self.cur_key)
        t = st.get("time", 0) or 0
        if tab and not st.get("paused", True):
            t += (time.monotonic() - tab["recv"]) * (st.get("rate", 1) or 1)
        d = st.get("duration") or 0
        return min(t, d) if d else t

    def _update_time(self):
        st = self.cur_state
        d = st.get("duration") or 0
        if not self.seek.dragging():
            t = self._cur_time()
            self.t_cur.setText(fmt_time(t))
            self.seek.set_value(t / d if d else 0)
        self.t_dur.setText(fmt_time(d) if d else ("LIVE" if st.get("hasVideo") and not d else "0:00"))

    def refresh_ui(self):
        self.cur_key = self.pick_tab()
        tab = self.tabs.get(self.cur_key)
        st = dict(tab["state"]) if tab else {}
        now = time.monotonic()
        if tab and now < self.hold_time_until and self.cur_state.get("id") == st.get("id"):
            st["time"] = self.cur_state.get("time", st.get("time"))
        self.cur_state = st
        connected = tab is not None
        has_video = bool(st.get("hasVideo"))

        self.dot.set_on(connected)
        n = len(self.tabs)
        self.ws.ping["tabs"] = n
        if connected:
            self.status.setText(f"{browser_name(st)} · {n} tab{'uri' if n != 1 else ''}")
        elif self.bridges:
            self.status.setText("Browser conectat · deschide YouTube")
        else:
            self.status.setText("Aștept browserul…")
        self.btn_tab.setVisible(n > 1)
        if n > 1:
            idx = list(self.tabs).index(self.cur_key) + 1 if self.cur_key in self.tabs else 0
            self.btn_tab.setText(f"TAB {idx}/{n}" + ("" if self.selected else " ·A"))

        if connected and has_video:
            title = st.get("title") or "YouTube"
            self.title.set_text(title)
            self.mini_title.set_text(title)
            self.channel.setText(st.get("channel", ""))
        elif connected:
            self.title.set_text("Niciun videoclip deschis")
            self.mini_title.set_text("Niciun videoclip deschis")
            self.channel.setText("Caută ceva și apasă pe rezultat ✦")
        elif self.host and (self.host.preparing or self.host.running()):
            first = self.host.preparing
            self.title.set_text("Pregătesc YukiTube…" if first else "Pornesc YouTube…")
            self.mini_title.set_text(self.title.text())
            self.channel.setText("Prima pornire: durează câteva secunde" if first else "O clipă…")
        else:
            self.title.set_text("Niciun tab YouTube conectat")
            self.mini_title.set_text("Niciun tab YouTube conectat")
            if now - self.old_bridge_seen < 10:
                self.channel.setText("Punte veche NeonTube: meniul ⋮ → Conectează YukiTube")
            else:
                self.channel.setText("Instalează puntea YukiTube (meniul ⋮)" if not self.bridges
                                     else "Deschide YouTube în browser")

        vid = st.get("id")
        if has_video and vid:
            if vid in self.thumbs:
                self.thumb.set_pixmap(self.thumbs[vid])
            else:
                self.request_thumb(vid, lambda pm, v=vid: self.thumb.set_pixmap(pm) if self.cur_state.get("id") == v else None)
        else:
            self.thumb.set_pixmap(None)

        for b in (self.btn_play, self.btn_prev, self.btn_next, self.btn_rew, self.btn_fwd, self.btn_loop,
                  self.btn_stop, self.btn_vol, self.btn_like, self.btn_speed):
            b.setEnabled(connected and (has_video or b in (self.btn_vol, self.btn_next)))
        self.seek.setEnabled(has_video)
        self.btn_play.set_icon("play" if st.get("paused", True) else "pause")
        self.btn_loop.setChecked(bool(st.get("loop")))
        liked = st.get("liked")
        self.btn_like.setChecked(bool(liked))
        self.btn_like.setVisible(liked is not None or not connected)
        rate = st.get("rate", 1) or 1
        self.btn_speed.setText(f"{rate:g}×")
        self.btn_speed.setChecked(abs(rate - 1) > 0.01)
        ad = bool(st.get("ad"))
        self.badge_ad.setVisible(ad)
        self.btn_skip.setVisible(ad)
        if connected and now >= self.hold_vol_until:
            vol = st.get("volume", 100)
            self.vol.set_value((vol or 0) / 100)
            self._update_vol_icon(vol, st.get("muted"))
        self._sync_account(connected)
        self._update_time()
        self.results_view.viewport().update()


def load_fonts():
    global FONT_UI
    d = os.path.join(resource_dir(), "fonts")
    for f in ("Orbitron.ttf", "ShareTechMono-Regular.ttf"):
        QFontDatabase.addApplicationFont(os.path.join(d, f))
    fams = set(QFontDatabase.families())
    for cand in ("Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans", "Cantarell", "Ubuntu",
                 "DejaVu Sans", "Liberation Sans"):
        if cand in fams:
            FONT_UI = cand
            break
    else:
        FONT_UI = QApplication.font().family()


def parse_args(argv):
    """--firefox <exe> --profile <dir>: run YouTube in that Firefox, hidden.
    --quiet-if-running: no error when the remote already runs.
    Anything else: a YouTube link or words to search."""
    opts = {"firefox": "", "profile": "", "quiet": False, "arg": ""}
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--firefox", "--profile") and i + 1 < len(argv):
            opts[a[2:]] = argv[i + 1]
            i += 2
            continue
        if a == "--quiet-if-running":
            opts["quiet"] = True
        elif a == "--bridge-marker" and i + 1 < len(argv):
            i += 1  # from launchers before 0.4.0
        else:
            rest.append(a)
        i += 1
    opts["arg"] = " ".join(rest).strip()
    return opts


def forward_to_running(arg):
    import json
    import urllib.request
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/nt/open", data=json.dumps({"arg": arg}).encode(),
        headers={"Content-Type": "application/json", "X-NeonTube": "1"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except OSError:
        return False


def main():
    # Prepares a profile and exits (kept for testing; the remote does it
    # itself on the first launch).
    if len(sys.argv) == 4 and sys.argv[1] == "--prepare-profile":
        import provision
        code = userscript_bytes().decode("utf-8")
        return 0 if provision.install_bridge(sys.argv[2], sys.argv[3], code) else 1
    opts = parse_args(sys.argv[1:])

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setDesktopFileName("yukitube-remote")
    app.setWindowIcon(logo_icon())
    app.setQuitOnLastWindowClosed(True)
    load_fonts()
    f = QFont(FONT_UI, 9)
    app.setFont(f)

    w = Player()
    app.aboutToQuit.connect(w.save_size)
    if not w.ws.listen(PORT):
        # Started by the YukiTube launcher while one is already running: the
        # running one takes the link or search (or just comes to the front).
        if forward_to_running(opts["arg"]) or opts["quiet"]:
            return 0
        QMessageBox.critical(None, APP_NAME,
                             f"Nu pot porni serverul local pe portul {PORT}.\n"
                             f"Probabil telecomanda YukiTube rulează deja.\n\n{w.ws.error_string()}")
        return 1
    pos = w.settings.value("pos")
    if isinstance(pos, QPoint):
        scr = QGuiApplication.screenAt(pos)
        if scr is not None:
            w.move(pos)
    # Shown at a fixed size, so window managers that tile (Hyprland) float
    # it from the start; then the size limits are loosened for resizing.
    w.setFixedSize(w.size())
    w.show()
    if opts["firefox"] and opts["profile"]:
        w.host_firefox(opts["firefox"], opts["profile"], opts["arg"])
        app.aboutToQuit.connect(w.host.stop)
    elif opts["arg"]:
        QTimer.singleShot(0, lambda: w.handle_open(opts["arg"]))

    def loosen():
        w.docker.float_self()
        w._fit()
    QTimer.singleShot(400, loosen)
    if w.settings.value("docked", "false") in (True, "true") and w.docker.available():
        QTimer.singleShot(600, lambda: w.btn_dock.setChecked(True))
    if os.environ.get("NEONTUBE_SCREENSHOT"):
        QTimer.singleShot(int(os.environ.get("NEONTUBE_SCREENSHOT_DELAY", "800")),
                          lambda: (w.grab().save(os.environ["NEONTUBE_SCREENSHOT"]), app.quit()))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
