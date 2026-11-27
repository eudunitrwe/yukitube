#!/usr/bin/env python3
"""YukiTube remote — the compact player of YukiTube.

The player talks to YouTube tabs through the "YukiTube Bridge" userscript
(Violentmonkey, preinstalled in YukiTube) or the browser extension, over a
local WebSocket / HTTP server on 127.0.0.1:8975.

YukiTube's launcher starts it with YUKITUBE_OPEN set to its own path, so links
the remote opens land in the YukiTube window instead of the default browser.
"""
import math
import os
import re
import signal
import sys
import time

from PySide6.QtCore import (QByteArray, QEasingCurve, QPoint, QPointF, QProcess, QRectF, QSettings, QSize, Qt,
                            QTimer, QUrl, Signal)
from PySide6.QtGui import (QAction, QBrush, QColor, QDesktopServices, QFont, QFontDatabase,
                           QCursor, QFontMetrics, QGuiApplication, QKeySequence, QLinearGradient, QPainter,
                           QImage, QPainterPath, QPen, QPixmap, QRadialGradient, QStandardItem,
                           QStandardItemModel)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog,
                               QFrame, QHBoxLayout, QLabel, QLineEdit, QListView, QMenu, QMessageBox,
                               QPushButton, QSizePolicy, QStyle, QStyledItemDelegate, QSystemTrayIcon,
                               QVBoxLayout, QWidget)

import icons
import i18n
import integration
import recommend
import updater
import ytsearch
from i18n import LANGS, T, set_lang
from logo import logo_icon, logo_pixmap
import hyprland
from wsserver import HTTP_CID, WsServer

APP_NAME = "YukiTube"
VERSION = "0.5.11"
PORT = int(os.environ.get("YUKITUBE_PORT") or "8975")
# Wide enough for most titles to fit on two lines in the search results.
WIDTH = 580

# Skins. The colors below are the current skin's; set_skin() swaps them, and
# everything paints from them, so a new skin is a new palette (plus, for a
# different look, its own drawing where classic() is checked).
SKINS = {
    "retrowave": {
        "PINK": "#ff2a6d", "CYAN": "#05d9e8", "MAGENTA": "#d300c5", "PURPLE": "#7b2fff",
        "YELLOW": "#ffd319", "ORANGE": "#ff901f", "TEXT": "#f6ecff", "MUTED": "#bfa3e0",
    },
    # A 90s desktop music player: brushed dark-steel case, bevelled grey
    # buttons, a black display with green LCD text.
    "classic": {
        "PINK": "#e8c547", "CYAN": "#3cff3c", "MAGENTA": "#b8962a", "PURPLE": "#5a5a80",
        "YELLOW": "#ffe36b", "ORANGE": "#ff9b2f", "TEXT": "#22ff22", "MUTED": "#a7aac2",
    },
    # Flat skins (STYLE "flat"): a plain rounded panel, no glow. PINK is the
    # accent, CYAN its hover shade; BG/BG2 the panel (top/bottom), LAYER the
    # area under the player, CARD raised surfaces (fields, menus), LINE
    # borders and dividers, TRACK slider rails, SHADE empty thumbnails,
    # ON_ACCENT text and icons on the accent, GOOD the "connected" dot.
    # Windows 11, light: Mica grey, white cards, the default blue accent.
    "win11_light": {
        "STYLE": "flat", "RADIUS": 8,
        "PINK": "#005fb8", "CYAN": "#0067c0", "MAGENTA": "#005fb8", "PURPLE": "#003e92",
        "YELLOW": "#fce100", "ORANGE": "#ca5010", "TEXT": "#1b1b1b", "MUTED": "#5d5d5d",
        "BG": "#f3f3f3", "BG2": "#eeeeee", "LAYER": "#f9f9f9", "CARD": "#ffffff", "LINE": "#dcdcdc",
        "TRACK": "#8a8a8a", "SHADE": "#e3e3e3", "ON_ACCENT": "#ffffff", "GOOD": "#0f7b0f",
    },
    # Windows 11, dark.
    "win11_dark": {
        "STYLE": "flat", "RADIUS": 8,
        "PINK": "#4cc2ff", "CYAN": "#99ebff", "MAGENTA": "#4cc2ff", "PURPLE": "#0078d4",
        "YELLOW": "#fce100", "ORANGE": "#f7630c", "TEXT": "#ffffff", "MUTED": "#c5c5c5",
        "BG": "#202020", "BG2": "#1c1c1c", "LAYER": "#272727", "CARD": "#2d2d2d", "LINE": "#3a3a3a",
        "TRACK": "#9a9a9a", "SHADE": "#333333", "ON_ACCENT": "#000000", "GOOD": "#6ccb5f",
    },
    # Nord: Polar Night panels, Frost accents, a cold aurora along the top.
    "nord": {
        "STYLE": "flat", "RADIUS": 12,
        "PINK": "#88c0d0", "CYAN": "#8fbcbb", "MAGENTA": "#81a1c1", "PURPLE": "#5e81ac",
        "YELLOW": "#ebcb8b", "ORANGE": "#d08770", "TEXT": "#eceff4", "MUTED": "#a4afc2",
        "BG": "#323a48", "BG2": "#2a303c", "LAYER": "#2e3440", "CARD": "#3b4252", "LINE": "#434c5e",
        "TRACK": "#4c566a", "SHADE": "#3b4252", "ON_ACCENT": "#2e3440", "GOOD": "#a3be8c",
    },
    # Arch_D: Everforest's warm grey-green panels, moss-green accent, a soft
    # forest glow and a green-to-aqua band along the top.
    "arch_d": {
        "STYLE": "flat", "RADIUS": 10,
        "PINK": "#a7c080", "CYAN": "#bcd29a", "MAGENTA": "#83c092", "PURPLE": "#5d7a52",
        "YELLOW": "#dbbc7f", "ORANGE": "#e69875", "TEXT": "#d3c6aa", "MUTED": "#9da9a0",
        "BG": "#2d353b", "BG2": "#272e33", "LAYER": "#232a2e", "CARD": "#343f44", "LINE": "#475258",
        "TRACK": "#6f7d75", "SHADE": "#3d484d", "ON_ACCENT": "#232a2e", "GOOD": "#83c092",
    },
}
SKIN = "retrowave"
PINK = CYAN = MAGENTA = PURPLE = YELLOW = ORANGE = TEXT = MUTED = ""
STYLE = "neon"
RADIUS = 18
BG = BG2 = LAYER = CARD = LINE = TRACK = SHADE = ON_ACCENT = GOOD = ""


def set_skin(name):
    global SKIN
    SKIN = name if name in SKINS else "retrowave"
    globals().update({k: v for k, v in SKINS[SKIN].items() if k.isupper()})
    if "STYLE" not in SKINS[SKIN]:
        globals().update(STYLE="classic" if SKIN == "classic" else "neon", RADIUS=18)


def classic():
    return SKIN == "classic"


def flat():
    return STYLE == "flat"


def rgba(c, a):
    """A colour for Qt stylesheets, with alpha a in [0, 1]."""
    q = QColor(c)
    return f"rgba({q.red()}, {q.green()}, {q.blue()}, {int(round(a * 255))})"


set_skin("retrowave")

# The Arch_D skin's animation: real lines of YukiTube's own code (Python,
# the bridge's JS, the Go launcher, the installers), the ones that name it,
# scrolling behind the player like a terminal.
CODE_LINES = (
    'APP_NAME = "YukiTube"',
    '# ------------------------------------------------------ YukiTube Firefox',
    'return QSettings("YukiTube", "remote")',
    'r.setRawHeader(b"User-Agent", f"YukiTube/{self.current}".encode())',
    'headers={"Content-Type": "application/json", "X-YukiTube": "1"}, method="POST")',
    's.setValue("YukiTube", f\'"{exe}"\')',
    'exe = os.path.join(win_root(), "YukiTube.exe")',
    '"""YukiTube launched with a link or words (or again, while running)."""',
    "self.host = None       # FirefoxHost, when the remote runs YukiTube's Firefox",
    'except Exception as ex:  # noqa: BLE001 - never keep YukiTube from opening',
    '"Name=YukiTube\\n"',
    '/* YukiTube bridge agent — runs inside the YouTube page.',
    'headers: { "Content-Type": "application/json", "X-YukiTube": "1" },',
    '// @name         YukiTube Bridge',
    '"short_name": "YukiTube",',
    'req.Header.Set("X-YukiTube", "1")',
    'return filepath.Join(local, "YukiTube")',
    'title, _ := syscall.UTF16PtrFromString("YukiTube")',
    'key, _ := syscall.UTF16PtrFromString(`Software\\YukiTube\\remote`)',
    '//\tYukiTube.exe <link|words>    play a link or search YouTube in the remote',
    '((${#remote[@]})) || fail "The YukiTube remote is not installed."',
    'InstallDir "$PROGRAMFILES32\\YukiTube"',
    '!define MUI_FINISHPAGE_RUN "$INSTDIR\\YukiTube.exe"',
    "Start-Process -FilePath (Join-Path $Root 'YukiTube.exe')",
)

# The classic skin's metal and bevels.
STEEL_HI, STEEL, STEEL_LO = "#c9c9d6", "#9d9db0", "#6c6c82"
BEVEL_LIGHT, BEVEL_DARK = "#e9e9f2", "#22222c"
ICON_DARK = "#15151c"

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
    """~/.config/YukiTube/remote.conf (Windows: HKCU\\Software\\YukiTube\\remote)."""
    return QSettings("YukiTube", "remote")


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


def draw_bevel(p, r, sunken=False, face=None, radius=1.5):
    """A 90s bevelled face: light top-left, dark bottom-right (swapped when
    pressed)."""
    g = QLinearGradient(0, r.top(), 0, r.bottom())
    if face is None:
        g.setColorAt(0, QColor(STEEL_HI if not sunken else STEEL))
        g.setColorAt(1, QColor(STEEL if not sunken else STEEL_HI))
        p.setBrush(g)
    else:
        p.setBrush(QColor(face))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(r, radius, radius)
    hi, lo = (BEVEL_DARK, BEVEL_LIGHT) if sunken else (BEVEL_LIGHT, BEVEL_DARK)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(hi), 1))
    p.drawLine(QPointF(r.left() + 0.5, r.bottom() - 1), QPointF(r.left() + 0.5, r.top() + 0.5))
    p.drawLine(QPointF(r.left() + 0.5, r.top() + 0.5), QPointF(r.right() - 1, r.top() + 0.5))
    p.setPen(QPen(QColor(lo), 1))
    p.drawLine(QPointF(r.right() - 0.5, r.top() + 1), QPointF(r.right() - 0.5, r.bottom() - 0.5))
    p.drawLine(QPointF(r.right() - 0.5, r.bottom() - 0.5), QPointF(r.left() + 1, r.bottom() - 0.5))


def draw_inset(p, r, fill="#000000"):
    """A sunken black display, like an LCD set into the case."""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(fill))
    p.drawRect(r)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(BEVEL_DARK), 1))
    p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.left(), r.top()))
    p.drawLine(QPointF(r.left(), r.top()), QPointF(r.right(), r.top()))
    p.setPen(QPen(QColor("#8a8aa0"), 1))
    p.drawLine(QPointF(r.right(), r.top()), QPointF(r.right(), r.bottom()))
    p.drawLine(QPointF(r.right(), r.bottom()), QPointF(r.left(), r.bottom()))


# ======================================================================= widgets
class IconButton(QAbstractButton):
    def __init__(self, icon, size=30, icon_size=18, tip="", checkable=False, parent=None,
                 color=None, hover=None, checked_color=None):
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
        if classic():
            r = QRectF(1, 1, w - 2, h - 2)
            down = self.isDown() or self.isChecked()
            draw_bevel(p, r, sunken=down, face="#d8d8e4" if self._hover and not down else None)
            col = "#0f6f0f" if self.isChecked() else ICON_DARK
            isz = self._isz - 2
            pm = icons.pixmap(self._icon, col, isz, self.devicePixelRatioF())
            off = 1 if down else 0
            p.drawPixmap(QPointF((w - isz) / 2 + off, (h - isz) / 2 + off), pm)
            return
        if flat():
            if self.isEnabled() and (self._hover or self.isDown()):
                p.setPen(Qt.NoPen)
                p.setBrush(qcolor(TEXT, 0.06 if self.isDown() else 0.10))
                p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 5, 5)
            col = self.color or TEXT
            if self.isChecked():
                col = self.checked_color or PINK
            elif self._hover and self.isEnabled() and self.hover_color:
                col = self.hover_color
            pm = icons.pixmap(self._icon, col, self._isz, self.devicePixelRatioF())
            p.drawPixmap(QPointF((w - self._isz) / 2, (h - self._isz) / 2), pm)
            if self.isChecked():
                p.setPen(Qt.NoPen)
                p.setBrush(qcolor(self.checked_color or PINK))
                p.drawRoundedRect(QRectF(w / 2 - 4, h - 3, 8, 2), 1, 1)
            return
        if self.isEnabled() and (self._hover or self.isDown()):
            g = QRadialGradient(c, w / 2)
            g.setColorAt(0, qcolor(CYAN, 0.32 if self.isDown() else 0.22))
            g.setColorAt(1, qcolor(CYAN, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawEllipse(c, w / 2, h / 2)
        col = self.color or TEXT
        if self.isChecked():
            col = self.checked_color or PINK
        elif self._hover and self.isEnabled():
            col = self.hover_color or CYAN
        pm = icons.pixmap(self._icon, col, self._isz, self.devicePixelRatioF())
        p.drawPixmap(QPointF((w - self._isz) / 2, (h - self._isz) / 2), pm)
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(qcolor(self.checked_color or PINK))
            p.drawEllipse(QPointF(w / 2, h - 3), 1.6, 1.6)


class PlayButton(IconButton):
    def __init__(self, parent=None):
        super().__init__("play", size=50, icon_size=26, tip=T("play_tip"), parent=parent)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        c = QPointF(w / 2, w / 2)
        if not self.isEnabled():
            p.setOpacity(0.45)
        if classic():
            r = QRectF(5, 7, w - 10, w - 14)
            draw_bevel(p, r, sunken=self.isDown(), face="#d8d8e4" if self._hover and not self.isDown() else None,
                       radius=2)
            isz = self._isz - 4
            pm = icons.pixmap(self._icon, ICON_DARK, isz, self.devicePixelRatioF())
            off = 1 if self.isDown() else 0
            p.drawPixmap(QPointF((w - isz) / 2 + off + (1 if self._icon == "play" else 0), (w - isz) / 2 + off), pm)
            return
        if flat():
            r = w / 2 - 6
            p.setPen(Qt.NoPen)
            p.setBrush(qcolor(PURPLE if self.isDown() else (CYAN if self._hover else PINK)))
            p.drawEllipse(c, r, r)
            isz = self._isz - 4
            pm = icons.pixmap(self._icon, ON_ACCENT, isz, self.devicePixelRatioF())
            dx = 1.5 if self._icon == "play" else 0
            p.drawPixmap(QPointF((w - isz) / 2 + dx, (w - isz) / 2), pm)
            return
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
        if classic():
            th = 6
            groove = QRectF(m, cy - th / 2, w, th)
            draw_inset(p, groove, "#0b0b10")
            x = m + w * self._v
            if self._v > 0:
                g = QLinearGradient(m, 0, m + w, 0)
                g.setColorAt(0, QColor("#1fa81f"))
                g.setColorAt(0.7, QColor(YELLOW))
                g.setColorAt(1, QColor(ORANGE))
                p.fillRect(QRectF(m + 1, cy - th / 2 + 1, x - m - 1, th - 2), g)
            kw, kh = 9, min(self.height() - 2, 14)
            draw_bevel(p, QRectF(x - kw / 2, cy - kh / 2, kw, kh), sunken=self._drag)
            return
        if flat():
            th = 4
            p.setPen(Qt.NoPen)
            p.setBrush(qcolor(TRACK, 0.55))
            p.drawRoundedRect(QRectF(m, cy - th / 2, w, th), th / 2, th / 2)
            x = m + w * self._v
            if self._v > 0:
                p.setBrush(QColor(PINK))
                p.drawRoundedRect(QRectF(m, cy - th / 2, x - m, th), th / 2, th / 2)
            kr = self._knob + 1
            p.setBrush(QColor(CARD))
            p.setPen(QPen(QColor(LINE), 1))
            p.drawEllipse(QPointF(x, cy), kr, kr)
            inner = kr * (0.62 if (self._hover or self._drag) else 0.48)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(PINK))
            p.drawEllipse(QPointF(x, cy), inner, inner)
            return
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

    def restyle(self, font, color, glow):
        self.setFont(font)
        self.setFixedHeight(QFontMetrics(font).height() + 4)
        self._color = QColor(color)
        self._glow = glow
        self._sync()
        self.update()

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
        if scrolling and classic():  # fade into the black display
            for x0, x1 in ((0, 14), (self.width(), self.width() - 14)):
                g = QLinearGradient(x0, 0, x1, 0)
                g.setColorAt(0, QColor(0, 0, 0, 255))
                g.setColorAt(1, QColor(0, 0, 0, 0))
                p.fillRect(QRectF(min(x0, x1), 0, 14, self.height()), g)
        elif scrolling:  # fade the edges
            p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
            for x0, x1 in ((0, 14), (self.width(), self.width() - 14)):
                g = QLinearGradient(x0, 0, x1, 0)
                g.setColorAt(0, QColor(0, 0, 0, 255))
                g.setColorAt(1, QColor(0, 0, 0, 0))
                p.fillRect(QRectF(min(x0, x1), 0, 14, self.height()), g)


class Thumb(QWidget):
    clicked = Signal()

    def __init__(self, w=128, h=72, parent=None):
        super().__init__(parent)
        self.setFixedSize(w, h)
        self._pm = None
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(T("thumb_tip"))

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
        rad = 1 if classic() else (6 if flat() else 8)
        path.addRoundedRect(r, rad, rad)
        p.save()
        p.setClipPath(path)
        if self._pm and not self._pm.isNull():
            src = self._pm
            sc = max(r.width() / src.width(), r.height() / src.height())
            sw, sh = src.width() * sc, src.height() * sc
            p.drawPixmap(QRectF(r.center().x() - sw / 2, r.center().y() - sh / 2, sw, sh), src,
                         QRectF(src.rect()))
        else:
            p.fillRect(r, QColor(0, 0, 0) if classic() else (QColor(SHADE) if flat() else QColor(15, 3, 35, 200)))
            lp = logo_pixmap(int(r.height() * 0.7 * self.devicePixelRatioF()))
            lp.setDevicePixelRatio(self.devicePixelRatioF())
            s = r.height() * 0.7
            p.drawPixmap(QRectF(r.center().x() - s / 2, r.center().y() - s / 2, s, s), lp, QRectF(lp.rect()))
        p.restore()
        if classic():
            p.setRenderHint(QPainter.Antialiasing, False)
            draw_inset(p, QRectF(0, 0, self.width() - 1, self.height() - 1), QColor(0, 0, 0, 0))
            return
        if flat():
            p.setPen(QPen(QColor(LINE), 1))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
            return
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
        if classic():
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(BEVEL_DARK))
            p.drawPath(path.translated(1, 1))
            p.setBrush(QColor("#e6e6f0"))
            p.drawPath(path)
            return
        if flat():
            p.setPen(Qt.NoPen)
            if SKIN in ("nord", "arch_d"):  # a frost / moss-to-aqua gradient
                g = QLinearGradient(26, 0, self.width(), 0)
                g.setColorAt(0, QColor(PINK))
                g.setColorAt(1, QColor(MAGENTA))
                p.setBrush(g)
            else:
                p.setBrush(QColor(TEXT))
            p.drawPath(path)
            return
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
        if flat():
            col = QColor(GOOD) if self._on else QColor("#c42b1c" if SKIN == "win11_light" else
                                                         {"nord": "#bf616a", "arch_d": "#e67e80"}.get(SKIN, "#ff99a4"))
        else:
            col = QColor("#39ff9f") if self._on else QColor("#ff3b3b" if classic() else PINK)
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
    def songs_rect(rect):
        """Where a playlist row's ☰ (show the songs) button is."""
        r = QRectF(rect).adjusted(4, 2, -4, -2)
        return QRectF(r.right() - 34, r.center().y() - 14, 28, 28)

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
        if d.get("list"):
            playing = d["list"] == self.win.cur_list()
        else:
            playing = d.get("id") and d.get("id") == self.win.cur_state.get("id")
        if (hover or sel) and flat():
            p.setPen(Qt.NoPen)
            p.setBrush(qcolor(TEXT, 0.09 if sel else 0.06))
            p.drawRoundedRect(r, 6, 6)
            p.setBrush(QColor(PINK))
            p.drawRoundedRect(QRectF(r.left(), r.top() + 14, 3, r.height() - 28), 1.5, 1.5)
        elif hover or sel:
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
            p.fillRect(tr, QColor(28, 28, 38) if classic() else (QColor(SHADE) if flat() else QColor(30, 6, 60, 200)))
            view = opt.widget
            self.win.request_thumb(d.get("id", ""), lambda *_, v=view: v.viewport().update() if v else None)
        dur = d.get("duration", "")
        if dur:
            p.setFont(self.f_dur)
            fm = QFontMetrics(self.f_dur)
            dw = fm.horizontalAdvance(dur) + 8
            dr = QRectF(tr.right() - dw - 3, tr.bottom() - fm.height() - 3, dw, fm.height())
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(10, 0, 25, 210))
            p.drawRoundedRect(dr, 3, 3)
            p.setPen(QColor(YELLOW if dur == "LIVE" else ("#ffffff" if flat() else TEXT)))
            p.drawText(dr, Qt.AlignCenter, dur)
        p.restore()
        if flat():
            p.setPen(QPen(QColor(PINK) if playing else QColor(LINE), 1.2 if playing else 1))
        else:
            p.setPen(QPen(qcolor(PINK if playing else CYAN, 0.8 if playing else 0.35), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        # a playlist's ☰ button: its songs
        songs_btn = bool(d.get("list"))
        if songs_btn:
            br = self.songs_rect(opt.rect)
            under = hover and br.contains(QPointF(self.win.lists_view.viewport().mapFromGlobal(QCursor.pos())))
            p.setPen(Qt.NoPen)
            if under:
                p.setBrush(qcolor(PINK if flat() else CYAN, 0.25))
                p.drawRoundedRect(br, 4 if flat() or classic() else 14, 4 if flat() or classic() else 14)
            col = (PINK if flat() else CYAN) if under else (MUTED if flat() else TEXT)
            pm = icons.pixmap("playlist", col, 18, p.device().devicePixelRatioF())
            p.drawPixmap(QPointF(br.center().x() - 9, br.center().y() - 9), pm)
        # text
        x = tr.right() + 10
        w = r.right() - x - 6 - (36 if songs_btn else 0)
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
def stylesheet():
    """The Qt stylesheet for the current skin."""
    if classic():
        return f"""
QWidget {{ color: {TEXT}; }}
QToolTip {{ background: #ffffe1; color: #000000; border: 1px solid #000000; padding: 3px 5px; }}
QLineEdit#search {{
  background: #000000; border: 2px inset #6c6c82; border-radius: 0; padding: 4px 10px 4px 32px;
  color: {TEXT}; selection-background-color: #1fa81f; selection-color: #000000; font-size: 10pt;
}}
QLineEdit#search:focus {{ border: 2px inset {STEEL_HI}; }}
QLabel#time {{ color: #e6e6f0; }}
QLabel#channel {{ color: {CYAN}; }}
QLabel#hint {{ color: #e6e6f0; }}
QLabel#badge {{ color: #000000; background: {YELLOW}; border-radius: 0; padding: 0 5px; font-weight: bold; }}
QLabel#recs_title {{ color: #e6e6f0; }}
QLabel#update_text {{ color: {TEXT}; }}
QListView {{ background: transparent; border: none; outline: none; }}
QScrollBar:vertical {{ background: #2a2a36; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {STEEL}; border: 1px outset {STEEL_HI}; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: none; }}
QMenu {{ background: #d4d0c8; border: 2px outset #f0f0f0; padding: 2px; color: #000000; }}
QMenu::item {{ padding: 4px 22px 4px 20px; }}
QMenu::item:selected {{ background: #0a246a; color: #ffffff; }}
QMenu::item:disabled {{ color: #808080; }}
QMenu::separator {{ height: 1px; background: #808080; margin: 3px 4px; }}
QMenu::indicator {{ width: 8px; height: 8px; left: 6px; }}
QMenu::indicator:checked {{ background: #000000; }}
"""
    if flat():
        return f"""
QWidget {{ color: {TEXT}; }}
QToolTip {{ background: {CARD}; color: {TEXT}; border: 1px solid {LINE}; padding: 4px 6px; border-radius: 4px; }}
QLineEdit#search {{
  background: {CARD}; border: 1px solid {LINE}; border-bottom: 1px solid {TRACK}; border-radius: 6px;
  padding: 5px 12px 5px 34px; color: {TEXT}; selection-background-color: {PINK}; selection-color: {ON_ACCENT};
  font-size: 10pt;
}}
QLineEdit#search:focus {{ border-bottom: 2px solid {PINK}; }}
QLabel#time {{ color: {MUTED}; }}
QLabel#channel {{ color: {MUTED}; }}
QLabel#hint {{ color: {MUTED}; }}
QLabel#badge {{ color: #000000; background: {YELLOW}; border-radius: 4px; padding: 0 5px; font-weight: bold; }}
QLabel#recs_title {{ color: {PINK}; }}
QLabel#update_text {{ color: {TEXT}; }}
QListView {{ background: transparent; border: none; outline: none; }}
QScrollBar:vertical {{ background: transparent; width: 6px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {rgba(TRACK, 0.6)}; border-radius: 3px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {TRACK}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; background: none; }}
QMenu {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 8px; padding: 4px; color: {TEXT}; }}
QMenu::item {{ padding: 5px 22px 5px 22px; border-radius: 4px; }}
QMenu::item:selected {{ background: {rgba(TEXT, 0.08)}; }}
QMenu::item:disabled {{ color: {MUTED}; }}
QMenu::separator {{ height: 1px; background: {LINE}; margin: 4px 6px; }}
QMenu::indicator {{ width: 8px; height: 8px; left: 7px; }}
QMenu::indicator:checked {{ background: {PINK}; border-radius: 4px; }}
"""
    return f"""
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
QLabel#recs_title {{ color: {PINK}; }}
QLabel#update_text {{ color: {TEXT}; }}
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
        if classic():
            draw_bevel(p, r, sunken=on or self.isDown(), face="#d8d8e4" if self._hover else None)
            p.setPen(QColor(ICON_DARK))
            p.drawText(r, Qt.AlignCenter, self.text())
            return
        if flat():
            p.setBrush(QColor(PINK) if on else (qcolor(TEXT, 0.08) if self._hover else QColor(CARD)))
            p.setPen(QPen(QColor(PINK) if on else QColor(LINE), 1))
            p.drawRoundedRect(r, 4, 4)
            p.setPen(QColor(ON_ACCENT) if on else QColor(TEXT))
            p.drawText(r, Qt.AlignCenter, self.text())
            return
        p.setBrush(qcolor(PINK, 0.65 if on else 0.15))
        p.setPen(QPen(QColor(CYAN) if self._hover else qcolor(PINK, 0.6), 1))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        p.setPen(QColor("#ffffff") if on else (QColor(CYAN) if self._hover else QColor(TEXT)))
        p.drawText(r, Qt.AlignCenter, self.text())


class RecTile(QWidget):
    """One recommendation: a small thumbnail with its length, the title
    under it."""
    TW, TH = 104, 58
    activated = Signal(dict)
    menu_requested = Signal(dict, QPoint)

    def __init__(self, win, parent=None):
        super().__init__(parent)
        self.win = win
        self.d = None
        self._hover = False
        self.f_title = QFont(FONT_UI, 8)
        self.f_dur = QFont(FONT_MONO, 7)
        self.setFixedSize(self.TW, self.TH + QFontMetrics(self.f_title).height() + 4)
        self.setCursor(Qt.PointingHandCursor)

    def set_item(self, d):
        self.d = d
        if d:
            tip = d.get("title", "")
            if d.get("channel"):
                tip += "\n" + d["channel"]
            self.setToolTip(tip)
            self.win.request_thumb(d.get("id", ""), lambda *_: self.update())
        else:
            self.setToolTip("")
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        # Taken here: passed on, the press would start moving the window
        # (Player.mousePressEvent), which swallows the click.
        e.accept()

    def mouseReleaseEvent(self, e):
        if not self.d:
            return
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self.activated.emit(self.d)
        elif e.button() == Qt.MiddleButton:
            self.win.open_in_browser(self.d)

    def contextMenuEvent(self, e):
        if self.d:
            self.menu_requested.emit(self.d, e.globalPos())

    def paintEvent(self, e):
        if not self.d:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        tr = QRectF(1, 1, self.TW - 2, self.TH - 2)
        rad = 1 if classic() else (4 if flat() else 6)
        path = QPainterPath()
        path.addRoundedRect(tr, rad, rad)
        p.save()
        p.setClipPath(path)
        pm = self.win.thumbs.get(self.d.get("id", ""))
        if pm:
            sc = max(tr.width() / pm.width(), tr.height() / pm.height())
            sw, sh = pm.width() * sc, pm.height() * sc
            p.drawPixmap(QRectF(tr.center().x() - sw / 2, tr.center().y() - sh / 2, sw, sh), pm, QRectF(pm.rect()))
        else:
            p.fillRect(tr, QColor(28, 28, 38) if classic() else (QColor(SHADE) if flat() else QColor(30, 6, 60, 200)))
        if self._hover:
            p.fillRect(tr, QColor(255, 255, 255, 28))
        dur = self.d.get("duration", "")
        if dur:
            p.setFont(self.f_dur)
            fm = QFontMetrics(self.f_dur)
            dw = fm.horizontalAdvance(dur) + 6
            dr = QRectF(tr.right() - dw - 2, tr.bottom() - fm.height() - 2, dw, fm.height())
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(10, 0, 25, 210))
            p.drawRoundedRect(dr, 2, 2)
            p.setPen(QColor(YELLOW if dur == "LIVE" else "#ffffff"))
            p.drawText(dr, Qt.AlignCenter, dur)
        p.restore()
        p.setBrush(Qt.NoBrush)
        if classic():
            p.setPen(QPen(QColor(CYAN if self._hover else "#3a3a4a"), 1))
        elif flat():
            p.setPen(QPen(QColor(PINK) if self._hover else QColor(LINE), 1.2 if self._hover else 1))
        else:
            p.setPen(QPen(qcolor(CYAN, 0.9) if self._hover else qcolor(PINK, 0.45), 1.2))
        p.drawPath(path)
        p.setFont(self.f_title)
        fm = QFontMetrics(self.f_title)
        p.setPen(QColor((PINK if flat() else CYAN) if self._hover else TEXT))
        p.drawText(QPointF(1, self.TH + 2 + fm.ascent()), fm.elidedText(self.d.get("title", ""), Qt.ElideRight, self.TW - 2))


class NextLine(QWidget):
    """"Up next: …" under the channel; a click plays it now."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        self._hover = False
        self.font_ = QFont(FONT_UI, 8)
        self.setFixedHeight(QFontMetrics(self.font_).height() + 2)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(T("up_next_tip"))

    def set_text(self, text):
        if text != self.text:
            self.text = text
            self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

    def mousePressEvent(self, e):
        e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()

    def paintEvent(self, e):
        if not self.text:
            return
        p = QPainter(self)
        p.setFont(self.font_)
        fm = QFontMetrics(self.font_)
        p.setPen(QColor((PINK if flat() else CYAN) if self._hover else MUTED))
        p.drawText(QPointF(0, fm.ascent() + 1), fm.elidedText("▸ " + self.text, Qt.ElideRight, self.width()))


class VideoView(QWidget):
    """The video mode's picture: frames of the playing video, sent by the
    bridge. Click: play / pause; double-click: full screen and back."""

    def __init__(self, win, full=False, parent=None):
        super().__init__(parent)
        self.win = win
        self.full = full
        self.img = None
        self._click = QTimer(self)
        self._click.setSingleShot(True)
        self._click.timeout.connect(win.toggle_play)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(T("tv_view_tip"))
        self.setMouseTracking(True)
        self._over_btn = False
        if full:
            self.setWindowTitle(APP_NAME)
            self.setAttribute(Qt.WA_DeleteOnClose)
            self.setStyleSheet("background: #000000;")

    def set_frame(self, img):
        self.img = img
        self.update()

    def mousePressEvent(self, e):
        e.accept()  # not passed on: it would start moving the window

    def full_rect(self):
        """The full-screen button, in the bottom right corner."""
        s = 44 if self.full else 30
        m = 16 if self.full else 8
        return QRectF(self.width() - s - m, self.height() - s - m, s, s)

    def mouseMoveEvent(self, e):
        over = self.full_rect().contains(e.position())
        if over != self._over_btn:
            self._over_btn = over
            self.setToolTip(T("tv_full_exit" if self.full else "tv_full") if over else T("tv_view_tip"))
            self.update()

    def leaveEvent(self, e):
        if self._over_btn:
            self._over_btn = False
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.full_rect().contains(e.position()):
            self._click.stop()
            self.win.toggle_video_full()
            return
        self._click.start(QApplication.doubleClickInterval())

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton and not self.full_rect().contains(e.position()):
            self._click.stop()
            self.win.toggle_video_full()

    def keyPressEvent(self, e):
        if self.full and e.key() in (Qt.Key_Escape, Qt.Key_F):
            self.close()
        elif self.full:
            self.win.keyPressEvent(e)
        else:
            super().keyPressEvent(e)

    def closeEvent(self, e):
        if self.full:
            self.win._video_full_closed()
        super().closeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        r = QRectF(self.rect())
        rad = 0 if self.full or classic() else (6 if flat() else 8)
        path = QPainterPath()
        path.addRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)
        p.fillPath(path, QColor(0, 0, 0))
        img = self.img
        if img is not None and not img.isNull():
            sc = min(r.width() / img.width(), r.height() / img.height())
            w, h = img.width() * sc, img.height() * sc
            p.save()
            p.setClipPath(path)
            p.drawImage(QRectF(r.center().x() - w / 2, r.center().y() - h / 2, w, h), img)
            p.restore()
        else:
            p.setPen(QColor("#9a9ab0"))
            p.setFont(QFont(FONT_UI, 10))
            p.drawText(r, Qt.AlignCenter, T("tv_waiting") if self.win.cur_key else T("tv_no_tab"))
        # the full-screen button
        br = self.full_rect()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 170 if self._over_btn else 110))
        p.drawRoundedRect(br, 6, 6)
        col = "#ffffff" if self._over_btn else "#d8d8e8"
        isz = int(br.width() * 0.7)
        pm = icons.pixmap("fullscreen_exit" if self.full else "fullscreen", col, isz, self.devicePixelRatioF())
        p.drawPixmap(QPointF(br.center().x() - isz / 2, br.center().y() - isz / 2), pm)
        if not self.full:
            p.setBrush(Qt.NoBrush)
            if classic():
                p.setPen(QPen(QColor("#3a3a4a"), 1))
            elif flat():
                p.setPen(QPen(QColor(LINE), 1))
            else:
                p.setPen(QPen(qcolor(PINK, 0.5), 1.2))
            p.drawPath(path)


class Divider(QWidget):
    """A thin horizontal line in the current skin's style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, e):
        p = QPainter(self)
        w, y = self.width(), self.height() / 2
        if classic():  # an etched groove
            p.setPen(QPen(QColor(BEVEL_DARK), 1))
            p.drawLine(QPointF(0, y - 0.5), QPointF(w, y - 0.5))
            p.setPen(QPen(QColor("#8a8aa0"), 1))
            p.drawLine(QPointF(0, y + 0.5), QPointF(w, y + 0.5))
            return
        if flat():
            p.setPen(QPen(QColor(LINE), 1))
            p.drawLine(QPointF(0, y), QPointF(w, y))
            return
        g = QLinearGradient(0, 0, w, 0)
        g.setColorAt(0, qcolor(PINK, 0))
        g.setColorAt(0.25, qcolor(PINK, 0.8))
        g.setColorAt(0.75, qcolor(CYAN, 0.8))
        g.setColorAt(1, qcolor(CYAN, 0.1))
        p.setPen(QPen(QBrush(g), 1))
        p.drawLine(QPointF(0, y), QPointF(w, y))


class RecsStrip(QWidget):
    """The small strip of recommendations at the bottom of the player."""
    COUNT = 5

    def __init__(self, win, parent=None):
        super().__init__(parent)
        self.win = win
        self.items = []
        self.page = 0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 0)
        lay.setSpacing(4)
        hdr = QHBoxLayout()
        hdr.setSpacing(6)
        self.title = QLabel(T("recs_title"))
        self.title.setObjectName("recs_title")
        f = QFont(FONT_DISPLAY, 7)
        f.setWeight(QFont.Bold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
        self.title.setFont(f)
        hdr.addWidget(self.title)
        self.source = QLabel("")
        self.source.setObjectName("hint")
        self.source.setFont(QFont(FONT_UI, 8))
        self.source.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        hdr.addWidget(self.source, 1)
        self.btn_more = IconButton("refresh", 22, 14, T("recs_more"))
        hdr.addWidget(self.btn_more)
        lay.addLayout(hdr)
        self.row = QHBoxLayout()
        self.row.setSpacing(0)
        self.tiles = []
        for i in range(self.COUNT):
            t = RecTile(win)
            self.tiles.append(t)
            if i:
                self.row.addStretch(1)
            self.row.addWidget(t)
        self.tiles_w = QWidget()
        self.tiles_w.setLayout(self.row)
        self.row.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.tiles_w)
        self.status = QLabel("")
        self.status.setObjectName("hint")
        self.status.setFont(QFont(FONT_UI, 8))
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setFixedHeight(self.tiles[0].height())
        lay.addWidget(self.status)
        self.set_status(T("recs_loading"))

    def set_status(self, text):
        self.status.setText(text)
        self.status.setVisible(True)
        self.tiles_w.setVisible(False)

    def set_items(self, items, source):
        self.items = items
        self.page = 0
        self.source.setText("· " + source if source else "")
        self._show()

    def next_page(self):
        """True while there are more pages; False after the last one."""
        if (self.page + 1) * self.COUNT >= len(self.items):
            return False
        self.page += 1
        self._show()
        return True

    def _show(self):
        chunk = self.items[self.page * self.COUNT:(self.page + 1) * self.COUNT]
        if not chunk:
            self.set_status(T("recs_empty"))
            return
        for i, t in enumerate(self.tiles):
            t.set_item(chunk[i] if i < len(chunk) else None)
        self.status.setVisible(False)
        self.tiles_w.setVisible(True)

    def retranslate(self):
        self.title.setText(T("recs_title"))
        self.btn_more.setToolTip(T("recs_more"))


class UpdateBar(QWidget):
    """A line in the player about a new version: offered, downloading,
    ready to install."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 6, 4)
        lay.setSpacing(6)
        self.icon = QLabel()
        lay.addWidget(self.icon)
        self.text = QLabel("")
        self.text.setObjectName("update_text")
        self.text.setFont(QFont(FONT_UI, 9))
        self.text.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lay.addWidget(self.text, 1)
        self.btn_a = Chip("")
        self.btn_b = Chip("")
        lay.addWidget(self.btn_a)
        lay.addWidget(self.btn_b)
        self.progress = 0.0
        self.a = self.b = None
        self.btn_a.clicked.connect(lambda: self.a and self.a())
        self.btn_b.clicked.connect(lambda: self.b and self.b())

    def show_state(self, text, a=None, b=None, tip="", progress=None):
        """a, b: (label, callback) for the two buttons, or None."""
        self.text.setText(text)
        self.setToolTip(tip)
        self.icon.setPixmap(icons.pixmap("download", ICON_DARK if classic() else (PINK if flat() else CYAN), 16,
                                         self.devicePixelRatioF()))
        for btn, spec, attr in ((self.btn_a, a, "a"), (self.btn_b, b, "b")):
            btn.setVisible(bool(spec))
            setattr(self, attr, spec[1] if spec else None)
            if spec:
                btn.setText(spec[0])
        self.progress = progress if progress is not None else -1
        self.show()
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if classic():
            draw_inset(p, r)
            if self.progress >= 0:
                p.fillRect(QRectF(r.left() + 1, r.bottom() - 3, (r.width() - 2) * self.progress, 2), QColor(CYAN))
            return
        if flat():
            p.setPen(QPen(QColor(LINE), 1))
            p.setBrush(QColor(CARD))
            p.drawRoundedRect(r, 6, 6)
            if self.progress >= 0:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(PINK))
                p.drawRoundedRect(QRectF(r.left() + 8, r.bottom() - 4, (r.width() - 16) * self.progress, 2.5), 1, 1)
            return
        p.setPen(QPen(qcolor(CYAN, 0.7), 1))
        p.setBrush(qcolor(PURPLE, 0.28))
        p.drawRoundedRect(r, 9, 9)
        if self.progress >= 0:
            g = QLinearGradient(r.left(), 0, r.right(), 0)
            g.setColorAt(0, QColor(PINK))
            g.setColorAt(1, QColor(CYAN))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawRoundedRect(QRectF(r.left() + 8, r.bottom() - 4, (r.width() - 16) * self.progress, 2.5), 1, 1)


class SettingsDialog(QDialog):
    """Language, starting with the computer, the desktop shortcut,
    recommendations, updates."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setWindowTitle(f"{APP_NAME} — {T('settings')}")
        self.setObjectName("settings")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(settings_stylesheet())
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 14)
        lay.setSpacing(10)
        head = QLabel(T("settings"))
        head.setObjectName("settings_head")
        f = QFont(FONT_DISPLAY, 12)
        f.setWeight(QFont.Bold)
        head.setFont(f)
        lay.addWidget(head)

        row = QHBoxLayout()
        row.addWidget(QLabel(T("settings_language")))
        self.lang = QComboBox()
        for code, name in LANGS.items():
            self.lang.addItem(name, code)
        self.lang.setCurrentIndex(list(LANGS).index(i18n.LANG))
        self.lang.currentIndexChanged.connect(self._lang)
        row.addWidget(self.lang, 1)
        lay.addLayout(row)

        self.autostart = QCheckBox(T("settings_autostart"))
        self.autostart.setChecked(integration.autostart_enabled())
        self.autostart.toggled.connect(lambda on: self._apply(integration.set_autostart, on, self.autostart))
        lay.addWidget(self.autostart)

        self.shortcut = QCheckBox(T("settings_shortcut"))
        exists, removable = integration.shortcut_state()
        self.shortcut.setChecked(exists)
        if not removable:
            self.shortcut.setEnabled(False)
            self.shortcut.setToolTip(T("settings_shortcut_all"))
        self.shortcut.toggled.connect(lambda on: self._apply(integration.set_shortcut, on, self.shortcut))
        lay.addWidget(self.shortcut)

        self.recs = QCheckBox(T("settings_recs"))
        self.recs.setChecked(win.recs_on)
        self.recs.toggled.connect(win.set_recs_on)
        lay.addWidget(self.recs)

        sep = QFrame()
        sep.setObjectName("sep")
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        upd = QLabel(T("settings_updates"))
        upd.setObjectName("settings_sub")
        lay.addWidget(upd)
        self.auto_update = QCheckBox(T("settings_auto_update"))
        self.auto_update.setChecked(win.updater.auto_check())
        self.auto_update.toggled.connect(win.updater.set_auto_check)
        lay.addWidget(self.auto_update)
        row = QHBoxLayout()
        ver = QLabel(T("settings_version", app=APP_NAME, v=VERSION))
        ver.setObjectName("hint")
        row.addWidget(ver, 1)
        self.check = QPushButton(T("settings_check_now"))
        self.check.setCursor(Qt.PointingHandCursor)
        self.check.clicked.connect(self._check)
        row.addWidget(self.check)
        # Update now: downloads the new version and restarts into it
        self.update_now = QPushButton(T("settings_update_now"))
        self.update_now.setCursor(Qt.PointingHandCursor)
        self.update_now.clicked.connect(self._update_now)
        row.addWidget(self.update_now)
        lay.addLayout(row)
        self.upd_status = QLabel("")
        self.upd_status.setObjectName("hint")
        self.upd_status.setWordWrap(True)
        self.upd_status.setMinimumHeight(2 * QFontMetrics(self.upd_status.font()).height())
        self.upd_status.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lay.addWidget(self.upd_status)

        lay.addSpacing(4)
        close = QPushButton(T("settings_close"))
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        close.setDefault(True)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        lay.addLayout(row)
        self.setMinimumWidth(420)
        self.adjustSize()
        # A fixed size: a tiling window manager cannot stretch it.
        self.setFixedSize(self.sizeHint())
        win.update_status.connect(self._on_update_status)
        win.update_changed.connect(self._sync_update)
        self._sync_update(initial=True)

    def _lang(self, i):
        self.win.set_language(self.lang.itemData(i))
        # Rebuilt in the new language, where it was.
        pos = self.pos()
        self.accept()
        QTimer.singleShot(0, lambda: self.win.show_settings(pos))

    def _apply(self, fn, on, box):
        if fn(on):
            return
        box.blockSignals(True)
        box.setChecked(not on)
        box.blockSignals(False)
        QMessageBox.warning(self, APP_NAME, T("settings_failed"))

    def _check(self):
        self.check.setEnabled(False)
        self.upd_status.setText(T("upd_checking"))
        self.win.check_updates(manual=True)

    def _on_update_status(self, text):
        self.check.setEnabled(True)
        self.upd_status.setText(text)
        self._sync_update()

    def _sync_update(self, initial=False):
        """The Update now button: shown while a newer version is known (or
        downloaded); busy while it downloads."""
        up = self.win.updater
        pending = up.pending()
        latest = up.latest.get("version")
        if up.downloading:
            self.update_now.setText(T("settings_updating"))
            self.update_now.setEnabled(False)
            self.update_now.show()
            self.upd_status.setText(T("upd_downloading", v=latest or "", pct=self.win._upd_pct))
        elif pending or latest:
            self.update_now.setText(T("settings_update_now") if pending or up.can_install() and up.latest.get("url")
                                    else T("upd_open_page"))
            self.update_now.setEnabled(True)
            self.update_now.show()
            if initial or self.win._upd_state == "failed":
                self.upd_status.setText(
                    T("upd_dl_failed", err=self.win._upd_err) if self.win._upd_state == "failed"
                    else T("upd_ready", v=pending["version"]) if pending else T("upd_available", v=latest))
        else:
            self.update_now.hide()

    def _update_now(self):
        self.update_now.setEnabled(False)
        self.win.update_now()


def settings_stylesheet():
    if classic():
        return """
QDialog#settings { background: #d4d0c8; }
QDialog#settings QLabel, QDialog#settings QCheckBox { color: #000000; }
QLabel#settings_head { color: #0a246a; }
QLabel#settings_sub { font-weight: bold; }
QLabel#hint { color: #404040; }
QFrame#sep { background: #808080; }
QPushButton { background: #d4d0c8; color: #000000; border: 2px outset #f0f0f0; padding: 3px 14px; }
QPushButton:pressed { border-style: inset; }
QComboBox { background: #ffffff; color: #000000; border: 2px inset #808080; padding: 2px 6px; }
QComboBox QAbstractItemView { background: #ffffff; color: #000000; selection-background-color: #0a246a;
  selection-color: #ffffff; }
QToolTip { background: #ffffe1; color: #000000; border: 1px solid #000000; }
"""
    if flat():
        return f"""
QDialog#settings {{ background: {BG}; }}
QDialog#settings QLabel, QDialog#settings QCheckBox {{ color: {TEXT}; }}
QLabel#settings_head {{ color: {TEXT}; }}
QLabel#settings_sub {{ color: {PINK}; font-weight: bold; }}
QLabel#hint {{ color: {MUTED}; }}
QFrame#sep {{ background: {LINE}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid {TRACK}; border-radius: 4px; background: {CARD}; }}
QCheckBox::indicator:checked {{ background: {PINK}; border-color: {PINK}; }}
QCheckBox::indicator:disabled {{ border-color: {LINE}; }}
QPushButton {{ background: {CARD}; color: {TEXT}; border: 1px solid {LINE}; border-radius: 5px; padding: 4px 14px; }}
QPushButton:hover {{ background: {LAYER}; border-color: {TRACK}; }}
QPushButton:default {{ background: {PINK}; color: {ON_ACCENT}; border-color: {PINK}; }}
QPushButton:disabled {{ color: {MUTED}; }}
QComboBox {{ background: {CARD}; color: {TEXT}; border: 1px solid {LINE}; border-radius: 5px; padding: 3px 8px; }}
QComboBox:hover {{ border-color: {TRACK}; }}
QComboBox QAbstractItemView {{ background: {CARD}; color: {TEXT}; border: 1px solid {LINE};
  selection-background-color: {PINK}; selection-color: {ON_ACCENT}; }}
QToolTip {{ background: {CARD}; color: {TEXT}; border: 1px solid {LINE}; padding: 4px 6px; }}
"""
    return f"""
QDialog#settings {{ background: #16052c; }}
QDialog#settings QLabel, QDialog#settings QCheckBox {{ color: {TEXT}; }}
QLabel#settings_head {{ color: {PINK}; }}
QLabel#settings_sub {{ color: {CYAN}; font-weight: bold; }}
QLabel#hint {{ color: {MUTED}; }}
QFrame#sep {{ background: rgba(5, 217, 232, 90); }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid {PINK}; border-radius: 4px;
  background: rgba(10, 2, 26, 200); }}
QCheckBox::indicator:checked {{ background: {PINK}; border-color: {CYAN}; }}
QCheckBox::indicator:disabled {{ border-color: {MUTED}; }}
QPushButton {{ background: rgba(255, 42, 109, 60); color: {TEXT}; border: 1px solid {PINK}; border-radius: 10px;
  padding: 4px 14px; }}
QPushButton:hover {{ border-color: {CYAN}; color: {CYAN}; }}
QPushButton:disabled {{ color: {MUTED}; border-color: {MUTED}; }}
QComboBox {{ background: rgba(10, 2, 26, 220); color: {TEXT}; border: 1px solid {PINK}; border-radius: 8px;
  padding: 3px 8px; }}
QComboBox:hover {{ border-color: {CYAN}; }}
QComboBox QAbstractItemView {{ background: #1a0533; color: {TEXT}; border: 1px solid {PINK};
  selection-background-color: {PINK}; }}
QToolTip {{ background: #1a0533; color: {TEXT}; border: 1px solid {PINK}; padding: 4px 6px; }}
"""


class Player(QWidget):
    PANEL_MARGIN = 10
    update_status = Signal(str)   # for the settings window: the last check's outcome
    update_changed = Signal()     # an update was found, is downloading, downloaded or failed

    def __init__(self):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(logo_icon())
        self.settings = remote_settings()
        set_skin(str(self.settings.value("skin", "retrowave")))
        set_lang(str(self.settings.value("lang", "en")))  # English unless chosen
        self.setStyleSheet(stylesheet())
        self.opacity = float(self.settings.value("opacity", 0.55))
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
        self.code_phase = 0.0
        self.player_h = 0

        self.net = QNetworkAccessManager(self)
        self.started = time.monotonic()
        # updates
        self.updater = updater.Updater(self.net, self.settings, VERSION, self)
        self.updater.checked.connect(self._on_update_checked)
        self.updater.check_failed.connect(self._on_update_check_failed)
        self.updater.progress.connect(self._on_update_progress)
        self.updater.downloaded.connect(self._on_update_downloaded)
        self._install_when_downloaded = False
        self.updater.download_failed.connect(self._on_update_download_failed)
        self._upd_state = None
        self._upd_err = ""
        self._upd_pct = 0
        self._manual_check = False
        # recommendations
        self.history = recommend.History(self.settings)
        self.recs_on = self.settings.value("recs", "true") in (True, "true")
        self.recs_req = 0
        self.recs_key = None       # "google" or "local": where the shown ones came from
        self.recs_loaded_at = 0.0
        self._recs_vid = None
        self._recs_done = True
        self._heard_vid = None
        self._heard_done = False
        # playlists
        self.pl_kind = str(self.settings.value("lists/kind", "") or "")  # "mine" / "suggested"; "" = by account
        self.pl_req = 0
        self.pl_cache = {}         # kind -> {"items": [...], "acc": signed in when loaded}
        self.pl_open = None        # the playlist whose songs are shown
        self.pl_wait = False       # waiting for a YouTube tab to ask
        self.pl_shown_acc = None
        self.video_full = None    # the full-screen video window
        self.q_req = 0
        self.q_key = None          # (video, list) the queue shown was loaded for
        self.q_list = ""
        self.q_index = -1
        self.tv_on = False
        self.ws = WsServer(self)
        self.ws.frame.connect(self.on_frame)
        self.ws.userscript = userscript_bytes()
        self.ws.ping = {"app": "yukitube-remote", "version": VERSION, "tabs": 0}
        self.ws.message.connect(self.on_message)
        self.ws.disconnected.connect(self.on_disconnect)
        self.ws.open_request.connect(self.handle_open)
        self.host = None       # FirefoxHost, when the remote runs YukiTube's Firefox

        self._build()
        self.apply_skin(SKIN, save=False)
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
        self.tv_timer = QTimer(self)
        self.tv_timer.timeout.connect(self._ask_video)
        if self.settings.value("tv", "false") in (True, "true"):
            self.btn_tv.setChecked(True)
        self.vol_timer = QTimer(self)
        self.vol_timer.setSingleShot(True)
        self.vol_timer.timeout.connect(self._send_volume)

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
        # The dot is the only status on the bar; its tooltip says more.
        hdr.addStretch(1)
        self.btn_tab = Chip("TAB 1/1", T("tab_chip_tip"))
        self.btn_tab.clicked.connect(self.tab_menu)
        hdr.addWidget(self.btn_tab)
        self.btn_account = AccountButton()
        self.btn_account.setToolTip(T("account_signin"))
        self.btn_account.clicked.connect(self.account_menu)
        hdr.addWidget(self.btn_account)
        self.btn_settings = IconButton("settings", 26, 16, T("settings"))
        self.btn_settings.clicked.connect(lambda: self.show_settings())
        hdr.addWidget(self.btn_settings)
        self.btn_skin = IconButton("palette", 26, 16, T("skin_tip"))
        self.btn_skin.clicked.connect(lambda: self.skin_menu(self.btn_skin.mapToGlobal(QPoint(0, 26))))
        self.btn_tv = IconButton("tv", 26, 16, T("tv_tip"), checkable=True)
        self.btn_tv.toggled.connect(self.toggle_tv)
        self.btn_lists = IconButton("playlist", 26, 16, T("lists_tip"), checkable=True)
        self.btn_lists.toggled.connect(self.toggle_lists)
        self.btn_queue = IconButton("queue", 26, 16, T("queue_tip"), checkable=True)
        self.btn_queue.toggled.connect(self.toggle_queue)
        self.btn_search = IconButton("search", 26, 16, T("search_tip"), checkable=True)
        self.btn_search.toggled.connect(self.toggle_search)
        self.btn_mini = IconButton("collapse", 26, 16, T("compact"))
        self.btn_mini.clicked.connect(self.toggle_mini)
        self.btn_menu = IconButton("menu", 26, 16, T("menu"))
        self.btn_menu.clicked.connect(lambda: self.show_menu(self.btn_menu.mapToGlobal(QPoint(0, 26))))
        self.btn_minw = IconButton("min", 26, 14, T("minimize"))
        self.btn_minw.clicked.connect(self.showMinimized)
        self.btn_close = IconButton("close", 26, 15, T("close"), hover=PINK)
        self.btn_close.clicked.connect(self.close)
        for b in (self.btn_skin, self.btn_tv, self.btn_queue, self.btn_lists, self.btn_search, self.btn_mini, self.btn_menu, self.btn_minw, self.btn_close):
            hdr.addWidget(b)
        root.addLayout(hdr)

        # video mode: the video, under the header; the window grows to fit it
        self.video = VideoView(self)
        vw = WIDTH - 24
        self.video.setFixedSize(vw, round(vw * 9 / 16))
        self.video.hide()
        root.addWidget(self.video)

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
        self.next_line = NextLine()
        self.next_line.clicked.connect(lambda: self.cmd("next"))
        self.next_line.hide()
        col.addWidget(self.next_line)
        col.addStretch(1)
        chips = QHBoxLayout()
        chips.setSpacing(5)
        self.btn_like = IconButton("like", 24, 14, T("like"), checkable=True)
        self.btn_like.clicked.connect(lambda: self.cmd("like"))
        chips.addWidget(self.btn_like)
        self.btn_speed = Chip("1.0×", T("speed_tip"))
        self.btn_speed.clicked.connect(self.speed_menu)
        chips.addWidget(self.btn_speed)
        self.badge_ad = QLabel("AD")
        self.badge_ad.setObjectName("badge")
        self.badge_ad.setFont(QFont(FONT_MONO, 8))
        chips.addWidget(self.badge_ad)
        self.btn_skip = Chip("SKIP ▸", T("skip_tip"))
        self.btn_skip.clicked.connect(lambda: self.cmd("skipAd"))
        chips.addWidget(self.btn_skip)
        chips.addStretch(1)
        col.addLayout(chips)
        info.addLayout(col, 1)
        self.info_w = QWidget()
        self.info_w.setLayout(info)
        info.setContentsMargins(0, 2, 0, 0)
        self.info_w.setFixedWidth(WIDTH - 24)
        root.addWidget(self.info_w)

        # mini title (only in compact mode)
        fmini = QFont(FONT_UI, 9)
        fmini.setWeight(QFont.DemiBold)
        self.mini_title = Marquee(fmini, TEXT, glow=PINK)
        self.mini_title.setFixedWidth(WIDTH - 24)
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
        self.seek_w.setFixedWidth(WIDTH - 24)
        root.addWidget(self.seek_w)

        # controls
        ctl = QHBoxLayout()
        ctl.setSpacing(2)
        self.btn_loop = IconButton("loop", 32, 18, T("loop_tip"), checkable=True)
        self.btn_loop.clicked.connect(lambda: self.cmd("loop", self.btn_loop.isChecked()))
        self.btn_prev = IconButton("prev", 34, 22, T("prev_tip"))
        self.btn_prev.clicked.connect(lambda: self.cmd("prev"))
        self.btn_rew = IconButton("rew", 34, 20, T("rew_tip"))
        self.btn_rew.clicked.connect(lambda: self.cmd("seekRel", -10))
        self.btn_play = PlayButton()
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_fwd = IconButton("fwd", 34, 20, T("fwd_tip"))
        self.btn_fwd.clicked.connect(lambda: self.cmd("seekRel", 10))
        self.btn_next = IconButton("next", 34, 22, T("next_tip"))
        self.btn_next.clicked.connect(lambda: self.cmd("next"))
        self.btn_stop = IconButton("stop", 32, 20, T("stop_tip"))
        self.btn_stop.clicked.connect(self.stop)
        self.btn_vol = IconButton("vol", 30, 18, T("mute_tip"))
        self.btn_vol.clicked.connect(lambda: self.cmd("mute"))
        self.vol = NeonSlider(height=16, knob=5)
        self.vol.setFixedWidth(92)
        self.vol.tip_fn = lambda v: T("volume_tip", v=int(round(v * 100)))
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
        self.ctl_w.setFixedWidth(WIDTH - 24)
        root.addWidget(self.ctl_w)

        # a new version: offered, downloading, ready
        self.update_bar = UpdateBar()
        self.update_bar.setFixedWidth(WIDTH - 24)
        self.update_bar.hide()
        root.addWidget(self.update_bar)

        # recommendations
        self.recs = RecsStrip(self)
        self.recs.setFixedWidth(WIDTH - 24)
        self.recs.btn_more.clicked.connect(self.more_recs)
        for t in self.recs.tiles:
            t.activated.connect(self.play_rec)
            t.menu_requested.connect(self.rec_menu)
        root.addWidget(self.recs)

        # queue panel: what plays next
        self.queue_panel = QWidget()
        qp = QVBoxLayout(self.queue_panel)
        qp.setContentsMargins(0, 2, 0, 0)
        qp.setSpacing(6)
        div = QHBoxLayout()
        div.setContentsMargins(0, 0, 0, 0)
        div.setSpacing(6)
        self.queue_head = QLabel(T("queue_title"))
        self.queue_head.setObjectName("recs_title")
        f = QFont(FONT_DISPLAY, 7)
        f.setWeight(QFont.Bold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
        self.queue_head.setFont(f)
        div.addWidget(self.queue_head)
        div.addWidget(Divider(), 1)
        self.btn_queue_reload = IconButton("refresh", 20, 12, T("lists_reload"))
        self.btn_queue_reload.clicked.connect(self.load_queue)
        div.addWidget(self.btn_queue_reload)
        self.btn_queue_close = IconButton("close", 20, 12, T("queue_close"))
        self.btn_queue_close.clicked.connect(lambda: self.btn_queue.setChecked(False))
        div.addWidget(self.btn_queue_close)
        qp.addLayout(div)
        self.queue_status = QLabel("")
        self.queue_status.setObjectName("hint")
        self.queue_status.setFont(QFont(FONT_UI, 8))
        self.queue_status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        qp.addWidget(self.queue_status)
        self.queue_model = QStandardItemModel(self)
        self.queue_view = QListView()
        self.queue_view.setModel(self.queue_model)
        self.queue_view.setItemDelegate(ResultDelegate(self))
        self.queue_view.setMouseTracking(True)
        self.queue_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.queue_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.queue_view.verticalScrollBar().setSingleStep(16)
        self.queue_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.queue_view.setFixedHeight(ResultDelegate.H * 5 + 4)
        self.queue_view.setCursor(Qt.PointingHandCursor)
        self.queue_view.clicked.connect(self.on_queue_clicked)
        self.queue_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_view.customContextMenuRequested.connect(self.queue_menu)
        qp.addWidget(self.queue_view)
        self.queue_panel.hide()
        self.queue_panel.setFixedWidth(WIDTH - 24)
        root.addWidget(self.queue_panel)

        # playlists panel: the account's own and the ones YouTube suggests
        self.lists_panel = QWidget()
        lp = QVBoxLayout(self.lists_panel)
        lp.setContentsMargins(0, 2, 0, 0)
        lp.setSpacing(6)
        div = QHBoxLayout()
        div.setContentsMargins(0, 0, 0, 0)
        div.setSpacing(6)
        div.addWidget(Divider(), 1)
        self.btn_lists_close = IconButton("close", 20, 12, T("lists_close"))
        self.btn_lists_close.clicked.connect(lambda: self.btn_lists.setChecked(False))
        div.addWidget(self.btn_lists_close)
        lp.addLayout(div)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        self.chip_mine = Chip(T("lists_mine"))
        self.chip_sugg = Chip(T("lists_suggested"))
        for c, kind in ((self.chip_mine, "mine"), (self.chip_sugg, "suggested")):
            c.setCheckable(True)
            c.clicked.connect(lambda _=False, k=kind: self.set_lists_kind(k))
            row.addWidget(c)
        self.chip_back = Chip(T("lists_back"))
        self.chip_back.clicked.connect(self.lists_back)
        self.chip_back.hide()
        row.addWidget(self.chip_back)
        row.addStretch(1)
        self.btn_lists_reload = IconButton("refresh", 22, 14, T("lists_reload"))
        self.btn_lists_reload.clicked.connect(self.reload_lists)
        row.addWidget(self.btn_lists_reload)
        lp.addLayout(row)
        self.lists_status = QLabel("")
        self.lists_status.setObjectName("hint")
        self.lists_status.setFont(QFont(FONT_UI, 8))
        self.lists_status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        lp.addWidget(self.lists_status)
        self.lists_model = QStandardItemModel(self)
        self.lists_view = QListView()
        self.lists_view.setModel(self.lists_model)
        self.lists_view.setItemDelegate(ResultDelegate(self))
        self.lists_view.setMouseTracking(True)
        self.lists_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lists_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.lists_view.verticalScrollBar().setSingleStep(16)
        self.lists_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lists_view.setFixedHeight(ResultDelegate.H * 5 + 4)
        self.lists_view.setCursor(Qt.PointingHandCursor)
        self.lists_view.clicked.connect(self.on_list_clicked)
        self.lists_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lists_view.customContextMenuRequested.connect(self.list_menu)
        self._lists_vp = self.lists_view.viewport()
        self._lists_vp.installEventFilter(self)
        lp.addWidget(self.lists_view)
        self.lists_panel.hide()
        self.lists_panel.setFixedWidth(WIDTH - 24)
        root.addWidget(self.lists_panel)

        # search panel
        self.search_panel = QWidget()
        sp = QVBoxLayout(self.search_panel)
        sp.setContentsMargins(0, 2, 0, 0)
        sp.setSpacing(6)
        # a line between the recommendations and the search, with a button
        # that closes the search (back to the plain player)
        div = QHBoxLayout()
        div.setContentsMargins(0, 0, 0, 0)
        div.setSpacing(6)
        div.addWidget(Divider(), 1)
        self.btn_search_close = IconButton("close", 20, 12, T("search_close"))
        self.btn_search_close.clicked.connect(lambda: self.btn_search.setChecked(False))
        div.addWidget(self.btn_search_close)
        sp.addLayout(div)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("search")
        self.search_edit.setPlaceholderText(T("search_placeholder"))
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
        self.results_view.setFixedHeight(ResultDelegate.H * 5 + 4)
        self.results_view.setCursor(Qt.PointingHandCursor)
        self.results_view.clicked.connect(self.on_result_clicked)
        self.results_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_view.customContextMenuRequested.connect(self.result_menu)
        self._results_vp = self.results_view.viewport()
        self._results_vp.installEventFilter(self)
        sp.addWidget(self.results_view)
        self.search_panel.hide()
        self.search_panel.setFixedWidth(WIDTH - 24)
        root.addWidget(self.search_panel)

        # tray
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(logo_icon(), self)
            self.tray.setToolTip(APP_NAME)
            tm = QMenu()
            tm.setStyleSheet(stylesheet())
            self.tray.setContextMenu(tm)
            self._tray_menu = tm
            self._fill_tray_menu()
            self.tray.activated.connect(
                lambda r: self.toggle_visible() if r == QSystemTrayIcon.Trigger else None)
            self.tray.show()
            self._tray_menu = tm

    def _fill_tray_menu(self):
        tm = self._tray_menu
        tm.clear()
        tm.addAction(T("play_pause"), self.toggle_play)
        tm.addAction(T("next"), lambda: self.cmd("next"))
        tm.addAction(T("prev"), lambda: self.cmd("prev"))
        tm.addSeparator()
        tm.addAction(T("toggle_remote"), self.toggle_visible)
        tm.addAction(T("youtube_window_tip"), self.toggle_youtube)
        tm.addAction(T("quit"), QApplication.quit)

    def retranslate(self):
        """Puts every fixed text in the current language."""
        for w, key in ((self.btn_tab, "tab_chip_tip"), (self.btn_skin, "skin_tip"), (self.btn_search, "search_tip"),
                       (self.btn_menu, "menu"), (self.btn_minw, "minimize"), (self.btn_close, "close"),
                       (self.btn_like, "like"), (self.btn_speed, "speed_tip"), (self.btn_skip, "skip_tip"),
                       (self.btn_loop, "loop_tip"), (self.btn_prev, "prev_tip"),
                       (self.btn_rew, "rew_tip"), (self.btn_fwd, "fwd_tip"), (self.btn_next, "next_tip"),
                       (self.btn_stop, "stop_tip"), (self.btn_vol, "mute_tip"), (self.btn_play, "play_tip"),
                       (self.thumb, "thumb_tip")):
            w.setToolTip(T(key))
        self.btn_mini.setToolTip(T("full") if self.mini else T("compact"))
        self.btn_settings.setToolTip(T("settings"))
        self.btn_search_close.setToolTip(T("search_close"))
        self.btn_lists.setToolTip(T("lists_tip"))
        self.btn_tv.setToolTip(T("tv_tip"))
        self.btn_queue.setToolTip(T("queue_tip"))
        self.btn_queue_close.setToolTip(T("queue_close"))
        self.btn_queue_reload.setToolTip(T("lists_reload"))
        self.queue_head.setText(T("queue_title"))
        self.next_line.setToolTip(T("up_next_tip"))
        if self.queue_panel.isVisible():
            self.load_queue()
        self.video.setToolTip(T("tv_view_tip"))
        self.btn_lists_close.setToolTip(T("lists_close"))
        self.btn_lists_reload.setToolTip(T("lists_reload"))
        self.chip_mine.setText(T("lists_mine"))
        self.chip_sugg.setText(T("lists_suggested"))
        self.chip_back.setText(T("lists_back"))
        if self.lists_panel.isVisible():
            self._show_lists_status()
        self.search_edit.setPlaceholderText(T("search_placeholder"))
        self.recs.retranslate()
        if self.recs_key:
            self.load_recs()
        if self._upd_state:
            self._show_update(self._upd_state)
        if self.tray:
            self._fill_tray_menu()
        self.refresh_ui()

    def set_language(self, code):
        set_lang(code)
        self.settings.setValue("lang", code)
        self.retranslate()

    # ------------------------------------------------------------- painting
    def paintEvent(self, e):
        if classic():
            self._paint_classic()
            return
        if flat():
            self._paint_flat()
            return
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
            p.save()
            p.setClipRect(QRectF(r.left(), horizon - 1, r.width(), bottom - horizon + 1), Qt.IntersectClip)
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
            p.restore()

        # the area under the player (update, recommendations, search) gets a
        # calmer, darker backdrop
        if r.bottom() - bottom > 6:
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

    def _paint_flat(self):
        """The flat skins (Windows 11, Nord): a rounded panel with a soft
        shadow, a second layer under the player, a thin border."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m = self.PANEL_MARGIN
        r = QRectF(self.rect()).adjusted(m, m, -m, -m)
        rad = RADIUS
        a = 0.6 + 0.4 * self.opacity  # the panel stays readable

        p.setBrush(Qt.NoBrush)
        for i in range(m, 0, -1):  # soft shadow
            p.setPen(QPen(QColor(0, 0, 0, int(14 * (1 - i / m) ** 2 * (0.5 + a))), 1))
            p.drawRoundedRect(r.adjusted(-i, -i + 2, i, i + 2), rad + i, rad + i)

        panel = QPainterPath()
        panel.addRoundedRect(r, rad, rad)
        bg = QLinearGradient(0, r.top(), 0, r.bottom())
        bg.setColorAt(0, qcolor(BG, a))
        bg.setColorAt(1, qcolor(BG2, a))
        p.fillPath(panel, bg)

        p.save()
        p.setClipPath(panel)
        if SKIN == "nord":
            # a cold aurora: frost glows behind the header
            for cx, col, rr in ((r.left() + r.width() * 0.2, PURPLE, 170), (r.right() - 120, PINK, 150)):
                g = QRadialGradient(QPointF(cx, r.top() - 30), rr)
                g.setColorAt(0, qcolor(col, 0.22 * a))
                g.setColorAt(1, qcolor(col, 0))
                p.fillRect(QRectF(cx - rr, r.top(), rr * 2, rr), g)
            band = QLinearGradient(r.left(), 0, r.right(), 0)
            band.setColorAt(0, qcolor(PURPLE, 0.0))
            band.setColorAt(0.3, qcolor(MAGENTA, 0.9))
            band.setColorAt(0.7, qcolor(PINK, 0.9))
            band.setColorAt(1, qcolor(CYAN, 0.0))
            p.fillRect(QRectF(r.left(), r.top(), r.width(), 2), band)
        elif SKIN == "arch_d":
            # a forest glow: moss and aqua light filtering in behind the header
            for cx, col, rr in ((r.left() + r.width() * 0.25, PINK, 190), (r.right() - 110, MAGENTA, 150)):
                g = QRadialGradient(QPointF(cx, r.top() - 40), rr)
                g.setColorAt(0, qcolor(col, 0.16 * a))
                g.setColorAt(1, qcolor(col, 0))
                p.fillRect(QRectF(cx - rr, r.top(), rr * 2, rr), g)
            band = QLinearGradient(r.left(), 0, r.right(), 0)
            band.setColorAt(0, qcolor(PURPLE, 0.0))
            band.setColorAt(0.3, qcolor(PINK, 0.9))
            band.setColorAt(0.7, qcolor(MAGENTA, 0.9))
            band.setColorAt(1, qcolor(MAGENTA, 0.0))
            p.fillRect(QRectF(r.left(), r.top(), r.width(), 2), band)
        ph = self.player_h or r.height()
        bottom = r.top() + ph + 4
        if SKIN == "arch_d":
            self._paint_code_rain(p, QRectF(r.left(), r.top() + 2, r.width(), bottom - r.top() - 2), a)
        if r.bottom() - bottom > 6:
            p.fillRect(QRectF(r.left(), bottom, r.width(), r.bottom() - bottom), qcolor(LAYER, a))
            p.setPen(QPen(QColor(LINE), 1))
            p.drawLine(QPointF(r.left(), bottom), QPointF(r.right(), bottom))
        p.restore()

        p.setPen(QPen(QColor(LINE), 1))
        p.setBrush(Qt.NoBrush)
        p.drawPath(panel)

    def _paint_code_rain(self, p, area, a):
        """Arch_D: YukiTube's own code lines scroll up behind the player,
        faint, with the name picked out in the accent colour."""
        if area.height() <= 0:
            return
        p.save()
        p.setClipRect(area, Qt.IntersectClip)
        f = QFont(FONT_MONO, 8)
        p.setFont(f)
        fm = p.fontMetrics()
        lh = fm.height() + 3
        off = self.code_phase
        first = int(off // lh)
        y = area.top() - (off % lh) + fm.ascent()
        n = len(CODE_LINES)
        k = first
        while y - fm.ascent() < area.bottom():
            line = CODE_LINES[(k * 7) % n]  # a stride, so neighbours differ in language
            x = area.left() + 14 + (k * 37 % 5) * 12
            # fade in at the bottom, out at the top, like a terminal scrolling by
            t = (y - area.top()) / max(1.0, area.height())
            fade = min(1.0, t / 0.25, (1 - t) / 0.2) if 0 < t < 1 else 0.0
            if fade > 0:
                i = line.find(APP_NAME)
                head, tail = line[:i], line[i + len(APP_NAME):]
                p.setPen(qcolor(MUTED, 0.145 * fade * a))
                p.drawText(QPointF(x, y), head)
                x2 = x + fm.horizontalAdvance(head)
                p.setPen(qcolor(PINK, 0.34 * fade * a))
                p.drawText(QPointF(x2, y), APP_NAME)
                p.setPen(qcolor(MUTED, 0.145 * fade * a))
                p.drawText(QPointF(x2 + fm.horizontalAdvance(APP_NAME), y), tail)
            y += lh
            k += 1
        p.restore()

    def _paint_classic(self):
        """The classic skin: a dark brushed-steel case, a ridged title strip
        behind the header, and black LCD displays for the song and the
        search results."""
        p = QPainter(self)
        m = self.PANEL_MARGIN
        r = QRectF(self.rect()).adjusted(m, m, -m, -m)
        alpha = int(255 * max(0.35, self.opacity))
        case = QLinearGradient(0, r.top(), 0, r.bottom())
        case.setColorAt(0, QColor(70, 70, 94, alpha))
        case.setColorAt(0.5, QColor(46, 46, 64, alpha))
        case.setColorAt(1, QColor(30, 30, 42, alpha))
        p.fillRect(r, case)
        # brushed metal: faint horizontal hairlines
        p.setPen(QPen(QColor(255, 255, 255, 10), 1))
        y = r.top() + 1
        while y < r.bottom():
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
            y += 2
        # outer bevel, twice, like the old cases
        p.setBrush(Qt.NoBrush)
        for inset, hi, lo in ((0, "#9a9ab4", "#08080c"), (1, "#5c5c78", "#14141c")):
            rr = r.adjusted(inset, inset, -inset - 1, -inset - 1)
            p.setPen(QPen(QColor(hi), 1))
            p.drawLine(rr.bottomLeft(), rr.topLeft())
            p.drawLine(rr.topLeft(), rr.topRight())
            p.setPen(QPen(QColor(lo), 1))
            p.drawLine(rr.topRight(), rr.bottomRight())
            p.drawLine(rr.bottomRight(), rr.bottomLeft())

        # title strip with ridges, behind the header row
        hb = self.logo.geometry().bottom() + 4
        strip = QRectF(r.left() + 3, r.top() + 3, r.width() - 6, hb - r.top() - 3)
        sg = QLinearGradient(0, strip.top(), 0, strip.bottom())
        sg.setColorAt(0, QColor(36, 36, 52, alpha))
        sg.setColorAt(1, QColor(20, 20, 30, alpha))
        p.fillRect(strip, sg)
        x0 = self.dot.geometry().right() + 12
        x1 = min(w.geometry().left() for w in (self.btn_tab, self.btn_account) if w.isVisible()) - 8
        if x1 - x0 > 12:
            cy = strip.center().y()
            for k in range(-2, 3):
                yy = cy + k * 3
                p.setPen(QPen(QColor("#8f8fae"), 1))
                p.drawLine(QPointF(x0, yy), QPointF(x1, yy))
                p.setPen(QPen(QColor("#101018"), 1))
                p.drawLine(QPointF(x0, yy + 1), QPointF(x1, yy + 1))

        # the LCD: the song (or the one-line title in compact mode)
        lcd_w = self.info_w if self.info_w.isVisible() else self.mini_title
        lcd = QRectF(lcd_w.geometry()).adjusted(-6, -4, 6, 4)
        draw_inset(p, lcd)
        p.setPen(QPen(QColor(0, 255, 0, 14), 1))  # faint LCD lines
        y = lcd.top() + 2
        while y < lcd.bottom() - 1:
            p.drawLine(QPointF(lcd.left() + 1, y), QPointF(lcd.right() - 1, y))
            y += 3

        # the recommendations and the results get a display of their own
        if self.recs.isVisible():
            inner = self.recs.tiles_w if self.recs.tiles_w.isVisible() else self.recs.status
            draw_inset(p, QRectF(inner.geometry().translated(self.recs.pos())).adjusted(-5, -3, 5, 3))
        if self.search_panel.isVisible():
            rv = self.results_view.geometry().translated(self.search_panel.pos())
            draw_inset(p, QRectF(rv).adjusted(-3, -3, 3, 3))
        if self.queue_panel.isVisible():
            rv = self.queue_view.geometry().translated(self.queue_panel.pos())
            draw_inset(p, QRectF(rv).adjusted(-3, -3, 3, 3))
        if self.lists_panel.isVisible():
            rv = self.lists_view.geometry().translated(self.lists_panel.pos())
            draw_inset(p, QRectF(rv).adjusted(-3, -3, 3, 3))

    def resizeEvent(self, e):
        self._measure()
        super().resizeEvent(e)

    def _fit(self):
        """The window's size is fixed: the player, plus the results while the
        search is open."""
        lay = self.layout()
        lay.invalidate()
        lay.activate()
        self.setFixedSize(WIDTH + 2 * self.PANEL_MARGIN, lay.totalMinimumSize().height())
        self._measure()
        self.update()

    def _measure(self):
        # height of the "player" part (everything above the search panel)
        g = self.ctl_w.geometry()
        self.player_h = g.bottom() + 8 - self.PANEL_MARGIN

    def _anim(self):
        if STYLE != "neon" and SKIN != "arch_d":
            return
        playing = self.cur_state and not self.cur_state.get("paused", True)
        if self.anim_on and playing and self.isVisible() and not self.isMinimized():
            self.grid_phase = (self.grid_phase + 0.04) % 1.0
            self.code_phase = (self.code_phase + 0.7) % 1e6
            self.update(0, 0, self.width(), self.PANEL_MARGIN + self.player_h + 10)

    # ------------------------------------------------------------- window ui
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            wh = self.windowHandle()
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
        self.btn_mini.setToolTip(T("full") if self.mini else T("compact"))
        for w in (self.t_cur, self.t_dur):
            w.setVisible(not self.mini)
        self.recs.setVisible(self.recs_on and not self.mini)
        self._fit()
        if self.recs.isVisible() and self.recs_key:
            self._maybe_recs()

    # --------------------------------------------------------------- skins
    def skin_menu(self, pos):
        m = QMenu(self)
        self._add_skin_actions(m)
        m.exec(pos)

    def _add_skin_actions(self, m):
        for key, sk in SKINS.items():
            a = m.addAction(T("skin_" + key))
            a.setCheckable(True)
            a.setChecked(key == SKIN)
            a.triggered.connect(lambda _=False, k=key: self.apply_skin(k))

    def apply_skin(self, name, save=True):
        set_skin(name)
        if save:
            self.settings.setValue("skin", SKIN)
        ss = stylesheet()
        self.setStyleSheet(ss)
        if self.tray:
            self._tray_menu.setStyleSheet(ss)
        if classic():
            ft = QFont(FONT_MONO, 12)
            fmini = QFont(FONT_MONO, 10)
            glow = None
        else:
            ft = QFont(FONT_UI, 11)
            ft.setWeight(QFont.Bold)
            fmini = QFont(FONT_UI, 9)
            fmini.setWeight(QFont.DemiBold)
            glow = None if flat() else PINK
        self.title.restyle(ft, TEXT, glow)
        self.mini_title.restyle(fmini, TEXT, glow)
        self._search_icon.setPixmap(icons.pixmap("search", MUTED if flat() else PINK, 16, self.devicePixelRatioF()))
        for w in self.findChildren(QWidget):
            w.update()
        self._fit()

    def set_on_top(self, on):
        self.on_top = on
        self.settings.setValue("ontop", on)
        vis = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on)
        if vis:
            self.show()

    def toggle_search(self, on):
        if on:
            self.btn_lists.setChecked(False)
            self.btn_queue.setChecked(False)
        self.search_panel.setVisible(on)
        if on:
            self.search_edit.setFocus()
            self.search_edit.selectAll()
        self._fit()

    def show_menu(self, pos):
        m = QMenu(self)
        a = m.addAction(T("always_on_top"))
        a.setCheckable(True)
        a.setChecked(self.on_top)
        a.toggled.connect(self.set_on_top)
        a = m.addAction(T("compact"))
        a.setCheckable(True)
        a.setChecked(self.mini)
        a.triggered.connect(self.toggle_mini)
        sm = m.addMenu(T("skin"))
        self._add_skin_actions(sm)
        lm = m.addMenu("Language / Limba / Язык")
        for code, name in LANGS.items():
            act = lm.addAction(name)
            act.setCheckable(True)
            act.setChecked(code == i18n.LANG)
            act.triggered.connect(lambda _=False, c=code: self.set_language(c))
        a = m.addAction(T("code_anim" if SKIN == "arch_d" else "grid_anim"))
        a.setCheckable(True)
        a.setChecked(self.anim_on)
        a.toggled.connect(lambda v: (setattr(self, "anim_on", v), self.settings.setValue("anim", v)))
        om = m.addMenu(T("transparency"))
        for pct in (100, 85, 70, 55, 40, 25):
            act = om.addAction(T("opaque", pct=pct))
            act.setCheckable(True)
            act.setChecked(abs(self.opacity - pct / 100) < 0.026)
            act.triggered.connect(lambda _=False, v=pct / 100: self.set_opacity(v))
        m.addSeparator()
        if self.host:
            m.addAction(T("hide_youtube") if self.youtube_shown() else T("show_youtube"),
                        self.toggle_youtube)
        else:
            m.addAction(T("open_youtube"), self.open_youtube)
        m.addAction(T("install_bridge"), self.install_bridge)
        m.addAction(T("how_connect"), self.show_help)
        m.addSeparator()
        m.addAction(T("settings_menu"), lambda: self.show_settings())
        m.addAction(T("check_updates"), lambda: self.check_updates(manual=True))
        m.addAction(T("about", app=APP_NAME, version=VERSION), self.show_about)
        m.addAction(T("quit"), QApplication.quit)
        m.exec(pos)

    def show_help(self):
        QMessageBox.information(
            self, T("connect_title", app=APP_NAME), T("connect_help", port=PORT))

    def show_about(self):
        QMessageBox.about(
            self, APP_NAME, T("about_text", app=APP_NAME, version=VERSION, port=PORT))

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
            elif self.queue_panel.isVisible():
                self.btn_queue.setChecked(False)
            elif self.lists_panel.isVisible():
                if self.pl_open:
                    self.lists_back()
                else:
                    self.btn_lists.setChecked(False)
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
        elif k in (Qt.Key_N, Qt.Key_MediaNext):
            self.cmd("next")
        elif k in (Qt.Key_P, Qt.Key_MediaPrevious):
            self.cmd("prev")
        else:
            super().keyPressEvent(e)

    def eventFilter(self, obj, ev):
        if (obj is getattr(self, "_lists_vp", None) and ev.type() == ev.Type.MouseButtonRelease
                and ev.button() == Qt.LeftButton and not self.pl_open):
            pos = ev.position().toPoint()
            idx = self.lists_view.indexAt(pos)
            d = idx.data(ROLE_DATA) if idx.isValid() else None
            if d and d.get("list") and ResultDelegate.songs_rect(self.lists_view.visualRect(idx)).contains(
                    QPointF(pos)):
                self.show_songs(d)
                return True
        if obj is getattr(self, "_lists_vp", None) and ev.type() == ev.Type.MouseMove:
            self._lists_vp.update()
        if obj is getattr(self, "_lists_vp", None) and ev.type() == ev.Type.MouseButtonRelease:
            if ev.button() == Qt.MiddleButton:
                idx = self.lists_view.indexAt(ev.position().toPoint())
                if idx.isValid():
                    self.open_list_in_browser(idx.data(ROLE_DATA))
                    return True
        if obj is getattr(self, "_results_vp", None) and ev.type() == ev.Type.MouseButtonRelease:
            if ev.button() == Qt.MiddleButton:
                idx = self.results_view.indexAt(ev.position().toPoint())
                if idx.isValid():
                    self.open_in_browser(idx.data(ROLE_DATA))
                    return True
        return super().eventFilter(obj, ev)

    def closeEvent(self, e):
        self.settings.setValue("pos", self.pos())
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
                                    "agent": msg.get("agent", ""), "born": time.monotonic()}
        tab["conn"] = cid
        tab["seen"] = time.monotonic()
        if t == "state":
            tab["state"] = msg.get("state") or {}
            tab["recv"] = time.monotonic()
            self.refresh_ui()
            self._check_account(tab)
        elif t == "search_results":
            self.on_agent_results(msg)
        elif t == "recommendations":
            self.on_agent_recs(msg)
        elif t == "queue":
            self.on_agent_queue(msg)
        elif t == "frame":
            self.on_frame(key, str(msg.get("data") or "").encode())
        elif t == "playlists":
            self.on_agent_lists(msg)
        elif t == "playlist_items":
            self.on_agent_list_items(msg)
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
        a = m.addAction(T("auto_tab"))
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
        self.host.state_changed.connect(self._on_host_state)
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
            self._account_window(SIGNIN_URL, True)
            if self.host and self.tray:
                self.tray.showMessage(APP_NAME, T("signin_hint"), logo_icon(), 8000)
            return
        m = QMenu(self)
        a = m.addAction(T("signed_in_as"))
        a.setEnabled(False)
        m.addSeparator()
        m.addAction(T("switch_account"), lambda: self._account_window(SWITCH_URL, True))
        m.addAction(T("sign_out"), lambda: self._account_window(SIGNOUT_URL, False))
        m.exec(self.btn_account.mapToGlobal(QPoint(0, self.btn_account.height())))

    def _account_window(self, url, want):
        """Shows Google's page in the YouTube window. Once YouTube in that
        window reports the account as wanted (signed in, or out), the window
        goes away by itself and YouTube carries on hidden."""
        self._account_wait = {"want": want, "since": time.monotonic(), "shown": False} if self.host else None
        self.open_url(url)

    def _on_host_state(self):
        w = getattr(self, "_account_wait", None)
        if not w or not self.host:
            return
        if self.host.visible:
            w["shown"] = True
        elif w["shown"]:
            self._account_wait = None  # the user closed the window first

    def _check_account(self, tab):
        w = getattr(self, "_account_wait", None)
        if not w or not self.youtube_shown() or tab.get("born", 0) < w["since"]:
            return  # only a tab of the window opened for the account counts
        if (tab["state"].get("account") or {}).get("loggedIn") is not w["want"]:
            return
        self._account_wait = None
        # A moment, so Firefox has the new sign-in cookies stored.
        QTimer.singleShot(1500, lambda: self.host.hide(self._here_url()) if self.youtube_shown() else None)

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
        self.btn_account.setToolTip(T("account_signed_in") if logged_in else T("account_signin"))

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
        a = m.addAction(T("play_here"), lambda: self.play_result(d))
        a.setEnabled(bool(self.cur_key))
        m.addAction(T("open_new_tab"), lambda: self.open_in_browser(d))
        m.addAction(T("copy_link"), lambda: QGuiApplication.clipboard().setText(
            f"https://www.youtube.com/watch?v={d['id']}"))
        m.exec(self.results_view.viewport().mapToGlobal(pos))

    # -------------------------------------------------------------- search
    def do_search(self):
        q = self.search_edit.text().strip()
        if not q:
            return
        self.search_req += 1
        req = self.search_req
        self._searching = True
        self.search_status.setText(T("searching", q=q))
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
        self._searching = False
        self.search_status.setText(T("search_failed", err=err or T("no_results_err")))

    def _search_timeout(self, req):
        if req == self.search_req and getattr(self, "_searching", False):
            self._searching = False
            self.search_status.setText(T("search_timeout"))

    def on_agent_results(self, msg):
        if msg.get("reqId") != self.search_req:
            return
        items = msg.get("items") or []
        if items:
            self.show_results(items, getattr(self, "_pending_q", ""))
        else:
            self._searching = False
            self.search_status.setText(T("no_results", err=msg.get("error", "")))

    def show_results(self, items, q):
        self.results_model.clear()
        for it in items:
            si = QStandardItem()
            si.setData(it, ROLE_DATA)
            si.setToolTip(it.get("title", ""))
            self.results_model.appendRow(si)
        self.results_view.scrollToTop()
        self._searching = False
        hint = T("hint_tab") if self.cur_key else T("hint_browser")
        self.search_status.setText(T("results_for", n=len(items), q=q, hint=hint))

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

    # ------------------------------------------------------------ settings
    def show_settings(self, pos=None):
        dlg = SettingsDialog(self)
        if pos is not None:
            dlg.move(pos)
        dlg.exec()

    def set_recs_on(self, on):
        self.recs_on = bool(on)
        self.settings.setValue("recs", self.recs_on)
        self._apply_mini()

    # ------------------------------------------------------------- updates
    def check_updates(self, manual=False):
        self._manual_check = manual
        if self.updater.downloading:
            self.update_status.emit(T("upd_downloading", v=self.updater.latest.get("version", ""),
                                      pct=self._upd_pct))
            return
        self.updater.check()

    def _on_update_checked(self, info):
        manual, self._manual_check = self._manual_check, False
        if not info:
            self.update_status.emit(T("upd_none", v=VERSION))
            if self._upd_state == "available":
                self._hide_update()
            return
        pending = self.updater.pending()
        if pending and pending["version"] == info["version"]:
            self._show_update("ready")
            self.update_status.emit(T("upd_ready", v=info["version"]))
            return
        self._show_update("available")
        self.update_status.emit(T("upd_available", v=info["version"]))
        if not manual and self.tray:
            self.tray.showMessage(APP_NAME, T("upd_notify", v=info["version"]), logo_icon(), 10000)

    def _on_update_check_failed(self, err):
        self._manual_check = False
        self.update_status.emit(T("upd_failed", err=err))

    def _on_update_progress(self, got, total):
        pct = int(got * 100 / total) if total > 0 else 0
        if pct != self._upd_pct or self._upd_state != "downloading":
            self._upd_pct = pct
            self._show_update("downloading")

    def _on_update_download_failed(self, err):
        self._install_when_downloaded = False
        if err == "Operation canceled":
            self.update_changed.emit()
            return
        self._upd_err = err
        self._show_update("failed")

    def _show_update(self, state):
        self._upd_state = state
        b = self.update_bar
        v = self.updater.latest.get("version") or (self.updater.pending() or {}).get("version", "")
        later = (T("upd_later"), self._hide_update)
        if state == "available":
            if self.updater.can_install() and self.updater.latest.get("url"):
                b.show_state(T("upd_available", v=v), (T("upd_download"), self._download_update), later)
            else:
                b.show_state(T("upd_available", v=v), (T("upd_open_page"), self._open_release_page), later,
                             tip=T("upd_page_tip"))
        elif state == "downloading":
            b.show_state(T("upd_downloading", v=v, pct=self._upd_pct), (T("upd_cancel"), self._cancel_update),
                         progress=self._upd_pct / 100)
        elif state == "ready":
            tries = int(self.settings.value("update/tries", 0) or 0)
            b.show_state(T("upd_ready", v=v), (T("upd_restart"), self._restart_to_update),
                         (T("upd_next_start"), self._hide_update),
                         tip=T("upd_retry_tip") if tries else T("upd_ready_tip"))
        elif state == "failed":
            b.show_state(T("upd_dl_failed", err=self._upd_err), (T("upd_retry"), self._download_update), later)
        self._fit()
        self.update_changed.emit()

    def _hide_update(self):
        self._upd_state = None
        self.update_bar.hide()
        self._fit()
        self.update_changed.emit()

    def _on_update_downloaded(self, v):
        self._show_update("ready")
        if self._install_when_downloaded:
            self._install_when_downloaded = False
            self._restart_to_update()

    def update_now(self):
        """The settings window's Update now: installs what is downloaded,
        or downloads the new version and then installs it (YukiTube
        restarts); a copy that cannot update itself opens the release page."""
        up = self.updater
        if up.pending():
            self._restart_to_update()
        elif up.latest.get("version") and up.can_install() and up.latest.get("url"):
            self._install_when_downloaded = True
            if not up.downloading:
                self._download_update()
        elif up.latest.get("version"):
            self._open_release_page()
        else:
            self.check_updates(manual=True)

    def _download_update(self):
        self._upd_pct = 0
        self._show_update("downloading")
        self.updater.download()

    def _cancel_update(self):
        self._install_when_downloaded = False
        self.updater.cancel()
        self._show_update("available")

    def _open_release_page(self):
        QDesktopServices.openUrl(QUrl(self.updater.latest.get("page") or updater.RELEASES_PAGE))
        self._hide_update()

    def _restart_to_update(self):
        if self.updater.apply():
            QApplication.quit()
        else:
            QMessageBox.warning(self, APP_NAME, T("upd_restart_failed"))

    # ----------------------------------------------------- recommendations
    def _count_play(self, st):
        """A video counts as played after half a minute of playing."""
        vid = st.get("id")
        if vid != self._heard_vid:
            self._heard_vid, self._heard_done = vid, False
        if (vid and not self._heard_done and not st.get("paused", True) and not st.get("ad")
                and (st.get("time") or 0) >= recommend.PLAYED_AFTER):
            self._heard_done = True
            self.history.add(vid, st.get("title", ""), st.get("channel", ""))

    def _signed_in(self):
        """True/False once YouTube says; None while it cannot tell yet."""
        if not self.cur_key:
            return None
        return (self.cur_state.get("account") or {}).get("loggedIn")

    def _maybe_recs(self):
        """Loads recommendations when there are none yet, when the account
        changes, and again for a new video after ten minutes."""
        if not self.recs.isVisible():
            return
        acc = self._signed_in()
        now = time.monotonic()
        if acc is None and now - self.started < 8:
            return  # YouTube is still starting
        want = "google" if acc else "local"
        vid = self.cur_state.get("id")
        if want != self.recs_key:
            self.load_recs()
        elif vid and vid != self._recs_vid and now - self.recs_loaded_at > 600:
            self.load_recs()

    def _youtube_tab(self):
        for k, t in self.tabs.items():
            if t["state"].get("host") == "www.youtube.com":
                return k, t
        return None, None

    def load_recs(self):
        self.recs_req += 1
        req = self.recs_req
        self.recs_loaded_at = time.monotonic()
        self._recs_vid = self.cur_state.get("id")
        acc = self._signed_in()
        self.recs_key = "google" if acc else "local"
        if not self.recs.items:
            self.recs.set_status(T("recs_loading"))
        key, tab = self._youtube_tab()
        if acc and tab:
            self.ws.send(tab["conn"], {"type": "cmd", "tab": key, "action": "recommend", "reqId": req,
                                       "value": {"seeds": self.history.seeds(3)}})
            QTimer.singleShot(30000, lambda: self._recs_local(req) if req == self.recs_req and
                              not self._recs_done else None)
            self._recs_done = False
            return
        self._recs_local(req)

    def on_agent_recs(self, msg):
        req = msg.get("reqId")
        if req != self.recs_req or self._recs_done:
            return
        self._recs_done = True
        cur = self.cur_state.get("id")
        items = [it for it in msg.get("items") or [] if it.get("id") != cur]
        if items:
            self.recs.set_items(items, T("recs_for_you"))
            self._fit()
        else:  # no Music tab for this account (yet): mixes of what plays here
            self._recs_local(req)

    def _yt_request(self, url):
        r = QNetworkRequest(QUrl(url))
        r.setRawHeader(b"User-Agent", ytsearch._UA.encode())
        r.setRawHeader(b"Accept-Language", b"en-US,en;q=0.8")
        r.setRawHeader(b"Cookie", b"SOCS=CAI; CONSENT=YES+")
        r.setTransferTimeout(12000)
        return r

    def _recs_local(self, req):
        """Music like what is played most here (and what plays now): the
        YouTube Mix of each, songs only."""
        self._recs_done = True
        cur = self.cur_state.get("id")
        seeds = self.history.seeds(3)
        if cur and cur not in seeds:
            seeds = [cur] + seeds[:2]
        if not seeds:
            self.recs.items = []
            self.recs.set_status(T("recs_empty"))
            return
        got = {}

        def done(rep, seed):
            rep.deleteLater()
            items = []
            if rep.error() == QNetworkReply.NoError:
                try:
                    items = ytsearch.parse_mix(bytes(rep.readAll().data()).decode("utf-8", "replace"), 25)
                except Exception:  # noqa: BLE001 — a page YouTube changed: no recommendations from it
                    items = []
            got[seed] = items
            if len(got) < len(seeds) or req != self.recs_req:
                return
            merged = recommend.merge([got[s] for s in seeds], exclude=seeds + [cur], limit=30)
            if merged:
                self.recs.set_items(merged, T("recs_history"))
            elif not self.recs.items:
                self.recs.set_status(T("recs_failed"))
            self._fit()

        for seed in seeds:
            rep = self.net.get(self._yt_request(f"https://www.youtube.com/watch?v={seed}&list=RD{seed}&hl=en"))
            rep.finished.connect(lambda rep=rep, seed=seed: done(rep, seed))

    def more_recs(self):
        if not self.recs.next_page():
            self.load_recs()

    def play_rec(self, d):
        if self.cur_key and self.cmd("open", {"id": d["id"]}):
            self.title.set_text(d.get("title", ""))
            self.mini_title.set_text(d.get("title", ""))
            self.channel.setText(d.get("channel", ""))
        elif self.host:
            self.host.navigate_headless(f"https://www.youtube.com/watch?v={d['id']}")
        else:
            self.open_in_browser(d)

    def rec_menu(self, d, pos):
        m = QMenu(self)
        m.addAction(T("play_here"), lambda: self.play_rec(d))
        m.addAction(T("open_new_tab"), lambda: self.open_in_browser(d))
        m.addAction(T("copy_link"), lambda: QGuiApplication.clipboard().setText(
            f"https://www.youtube.com/watch?v={d['id']}"))
        m.exec(pos)

    # ---------------------------------------------------------- video mode
    def toggle_tv(self, on):
        """The video mode: the window grows and shows the video playing in
        the hidden YouTube (frames sent by the bridge)."""
        self.tv_on = bool(on)
        self.settings.setValue("tv", self.tv_on)
        self.ws.want_frames = self.tv_on
        self.video.setVisible(self.tv_on)
        self._fit()
        if self.tv_on:
            self.video.set_frame(None)
            self._ask_video()
            self.tv_timer.start(2500)
        else:
            self.tv_timer.stop()
            self.cmd("video", {"on": False})
            if self.video_full:
                self.video_full.close()

    def _ask_video(self):
        w = self.video.width() * self.devicePixelRatioF()
        if self.video_full:
            w = max(w, self.video_full.width() * self.video_full.devicePixelRatioF())
        self.cmd("video", {"on": True, "w": int(min(1920, w)), "fps": 25})

    def on_frame(self, tab, data):
        if not self.tv_on or tab != self.cur_key:
            return
        img = QImage.fromData(QByteArray.fromBase64(QByteArray(data)), "JPG")
        if img.isNull():
            return
        self.video.set_frame(img)
        if self.video_full:
            self.video_full.set_frame(img)

    def toggle_video_full(self):
        if self.video_full:
            self.video_full.close()
            return
        self.video_full = VideoView(self, full=True)
        self.video_full.set_frame(self.video.img)
        scr = self.screen() or QGuiApplication.primaryScreen()
        if scr is not None:
            self.video_full.setGeometry(scr.geometry())
        self.video_full.showFullScreen()
        self.video_full.activateWindow()
        # The player stays on top of other windows: it would cover the
        # video. It is hidden while the video is full screen.
        self._pos_before_full = self.pos()
        self.hide()
        QTimer.singleShot(200, self._ask_video)

    def _video_full_closed(self):
        self.video_full = None
        if not self.isVisible():
            self.showNormal()
            pos = getattr(self, "_pos_before_full", None)
            if pos is not None:
                self.move(pos)
            self.raise_()
            self.activateWindow()
            QTimer.singleShot(300, hyprland.float_window)

    # --------------------------------------------------------------- queue
    @staticmethod
    def _queue_key(st):
        nx = st.get("next") if isinstance(st.get("next"), dict) else {}
        return st.get("id"), st.get("list") or "", nx.get("id")

    def toggle_queue(self, on):
        if on:
            self.btn_search.setChecked(False)
            self.btn_lists.setChecked(False)
        self.queue_panel.setVisible(on)
        self._fit()
        if on:
            self.queue_view.setFocus()
            self.load_queue()

    def load_queue(self):
        """Asks the YouTube tab for what plays next."""
        st = self.cur_state
        self.q_key = self._queue_key(st)
        self.q_req += 1
        if not self.cur_key or not st.get("hasVideo"):
            self.queue_model.clear()
            self.queue_status.setText(T("queue_empty"))
            return
        if not self.queue_model.rowCount():
            self.queue_status.setText(T("queue_loading"))
        req = self.q_req
        self.cmd("queue", extra={"reqId": req})
        QTimer.singleShot(30000, lambda: self._queue_timeout(req))

    def _queue_timeout(self, req):
        if req == self.q_req and not self.queue_model.rowCount() and self.queue_panel.isVisible():
            self.queue_status.setText(T("lists_failed", err="timeout"))

    def on_agent_queue(self, msg):
        if msg.get("reqId") != self.q_req:
            return
        items = [dict(it) for it in msg.get("items") or [] if isinstance(it, dict) and it.get("id")]
        if not items:
            self.queue_model.clear()
            self.queue_status.setText(T("lists_failed", err=msg["error"]) if msg.get("error") else T("queue_empty"))
            return
        self.q_list = msg.get("list") or ""
        idx = msg.get("index", -1)
        self.q_index = idx if isinstance(idx, int) else -1
        for i, it in enumerate(items):
            it["index"] = i
            tag = ""
            if i == self.q_index:
                tag = T("queue_now")
            elif it.get("upNext") or (self.q_list and self.q_index >= 0 and i == self.q_index + 1):
                tag = T("queue_next")
            if tag:
                it["views"] = "▸ " + tag + ("  ·  " + it["views"] if it.get("views") else "")
        self.queue_model.clear()
        for it in items:
            si = QStandardItem()
            si.setData(it, ROLE_DATA)
            si.setToolTip(it.get("title", "") + ("\n" + it["channel"] if it.get("channel") else ""))
            self.queue_model.appendRow(si)
        if self.q_list:
            self.queue_status.setText(T("queue_list", i=max(1, self.q_index + 1), n=len(items)))
        else:
            self.queue_status.setText(T("queue_single") if msg.get("auto", True) else T("queue_no_autoplay"))
        if self.q_index > 0:
            self.queue_view.scrollTo(self.queue_model.index(self.q_index, 0), QAbstractItemView.PositionAtTop)
        else:
            self.queue_view.scrollToTop()

    def play_queue_item(self, d):
        if not d or d.get("id") == self.cur_state.get("id"):
            return
        if self.q_list:
            self.cmd("openList", {"list": self.q_list, "id": d["id"], "index": d.get("index", 0)})
        else:
            self.cmd("open", {"id": d["id"]})
        self.title.set_text(d.get("title", ""))
        self.mini_title.set_text(d.get("title", ""))
        self.channel.setText(d.get("channel", ""))

    def on_queue_clicked(self, idx):
        d = idx.data(ROLE_DATA)
        if QGuiApplication.keyboardModifiers() & Qt.ControlModifier:
            self.open_in_browser(d)
        else:
            self.play_queue_item(d)

    def queue_menu(self, pos):
        idx = self.queue_view.indexAt(pos)
        if not idx.isValid():
            return
        d = idx.data(ROLE_DATA)
        m = QMenu(self)
        m.addAction(T("play_here"), lambda: self.play_queue_item(d))
        m.addAction(T("open_new_tab"), lambda: self.open_in_browser(d))
        m.addAction(T("copy_link"), lambda: QGuiApplication.clipboard().setText(
            f"https://www.youtube.com/watch?v={d['id']}"))
        m.exec(self.queue_view.viewport().mapToGlobal(pos))

    # ----------------------------------------------------------- playlists
    def cur_list(self):
        """The playlist playing now (the list= of the watch page), or ""."""
        m = re.search(r"[?&]list=([\w-]+)", self.cur_state.get("url") or "")
        return m.group(1) if m else ""

    def toggle_lists(self, on):
        if on:
            self.btn_search.setChecked(False)
            self.btn_queue.setChecked(False)
        self.lists_panel.setVisible(on)
        self._fit()
        if on:
            self.lists_view.setFocus()
            if self.pl_open:
                self._show_songs_status()
            else:
                self.load_lists()

    def _lists_kind(self):
        if self.pl_kind in ("mine", "suggested"):
            return self.pl_kind
        return "mine" if self._signed_in() else "suggested"

    def set_lists_kind(self, kind):
        self.pl_kind = kind
        self.settings.setValue("lists/kind", kind)
        self.pl_open = None
        self.load_lists()

    def reload_lists(self):
        if self.pl_open:
            self.show_songs(self.pl_open)
        else:
            self.pl_cache.pop(self._lists_kind(), None)
            self.load_lists()

    def lists_back(self):
        self.pl_open = None
        self.load_lists()

    def _lists_header(self):
        kind = self._lists_kind()
        songs = self.pl_open is not None
        self.chip_mine.setChecked(kind == "mine")
        self.chip_sugg.setChecked(kind == "suggested")
        self.chip_mine.setVisible(not songs)
        self.chip_sugg.setVisible(not songs)
        self.chip_back.setVisible(songs)

    def _fill_lists(self, items):
        self.lists_model.clear()
        for it in items:
            si = QStandardItem()
            si.setData(it, ROLE_DATA)
            tip = it.get("title", "")
            if it.get("channel"):
                tip += "\n" + it["channel"]
            si.setToolTip(tip)
            self.lists_model.appendRow(si)
        self.lists_view.scrollToTop()

    def load_lists(self):
        """Shows the playlists of the chosen kind: from the cache, or asked
        for through the YouTube tab."""
        self.pl_open = None
        self._lists_header()
        kind = self._lists_kind()
        acc = self._signed_in()
        self.pl_shown_acc = acc
        self.pl_wait = False
        self.pl_req += 1
        cached = self.pl_cache.get(kind)
        if cached and cached["acc"] == bool(acc):
            self._fill_lists(cached["items"])
            self._show_lists_status()
            return
        self.lists_model.clear()
        if kind == "mine" and acc is False:
            self.lists_status.setText(T("lists_signin"))
            return
        key, tab = self._youtube_tab()
        if not tab:
            self.pl_wait = True
            self.lists_status.setText(T("lists_wait"))
            return
        req = self.pl_req
        seeds = []
        for vid in self.history.seeds(6):
            e = self.history.items.get(vid) or {}
            seeds.append({"id": vid, "title": e.get("title", ""), "channel": e.get("channel", "")})
        cur = self.cur_state
        if cur.get("id") and all(x["id"] != cur["id"] for x in seeds):
            seeds.insert(0, {"id": cur["id"], "title": cur.get("title", ""), "channel": cur.get("channel", "")})
        self.lists_status.setText(T("lists_loading"))
        self.ws.send(tab["conn"], {"type": "cmd", "tab": key, "action": "playlists", "reqId": req,
                                   "value": {"kind": kind, "seeds": seeds[:6]}})
        QTimer.singleShot(45000, lambda: self._lists_timeout(req))

    def _lists_timeout(self, req):
        if req == self.pl_req and not self.lists_model.rowCount() and self.lists_panel.isVisible():
            self.lists_status.setText(T("lists_failed", err="timeout"))

    def _maybe_lists(self):
        """Asks again once YouTube is up, or when the account changed."""
        if not self.lists_panel.isVisible() or self.pl_open:
            return
        acc = self._signed_in()
        if self.pl_wait and self._youtube_tab()[1]:
            self.load_lists()
        elif acc is not None and acc != self.pl_shown_acc:
            self.load_lists()

    def _show_lists_status(self):
        if self.pl_open:
            return self._show_songs_status()
        kind = self._lists_kind()
        n = self.lists_model.rowCount()
        if n:
            self.lists_status.setText(T("lists_count_" + kind, n=n))
        elif kind == "mine" and self._signed_in() is False:
            self.lists_status.setText(T("lists_signin"))
        else:
            self.lists_status.setText(T("lists_none_mine" if kind == "mine" else "lists_none"))

    def on_agent_lists(self, msg):
        if msg.get("reqId") != self.pl_req:
            return
        kind = msg.get("kind")
        err = msg.get("error") or ""
        items = [dict(it) for it in msg.get("items") or [] if isinstance(it, dict) and it.get("list")]
        for it in items:
            if it["list"] == "LL":
                it["title"] = it.get("title") or T("lists_liked")
            elif it["list"] == "WL":
                it["title"] = it.get("title") or T("lists_watch_later")
        if err and not items:
            if err == "signed out":
                self.lists_status.setText(T("lists_signin"))
            else:
                self.lists_status.setText(T("lists_failed", err=err))
            return
        self.pl_cache[kind] = {"items": items, "acc": bool(msg.get("loggedIn"))}
        if kind == self._lists_kind() and not self.pl_open:
            self._fill_lists(items)
            self._show_lists_status()

    def show_songs(self, d):
        """The songs of a playlist, in the panel."""
        self.pl_open = d
        self._lists_header()
        self.lists_model.clear()
        self.pl_req += 1
        req = self.pl_req
        key, tab = self._youtube_tab()
        if not tab:
            self.lists_status.setText(T("lists_wait"))
            return
        self.lists_status.setText(T("lists_songs_loading", t=d.get("title", "")))
        self.ws.send(tab["conn"], {"type": "cmd", "tab": key, "action": "playlistItems", "reqId": req,
                                   "value": {"list": d["list"], "id": d.get("id", "")}})
        QTimer.singleShot(45000, lambda: self._lists_timeout(req))

    def on_agent_list_items(self, msg):
        if msg.get("reqId") != self.pl_req or not self.pl_open:
            return
        items = []
        for i, it in enumerate(msg.get("items") or []):
            if isinstance(it, dict) and it.get("id"):
                items.append(dict(it, index=i))
        if not items and msg.get("error"):
            self.lists_status.setText(T("lists_failed", err=msg["error"]))
            return
        self._fill_lists(items)
        self._show_songs_status()

    def _show_songs_status(self):
        t = (self.pl_open or {}).get("title", "")
        n = self.lists_model.rowCount()
        self.lists_status.setText(T("lists_songs", n=n, t=t) if n else T("lists_songs_none", t=t))

    def play_list(self, pl, song=None):
        """Plays a playlist, from its start or from one of its songs; next and
        previous then go through it."""
        if not pl or not pl.get("list"):
            return
        vid = (song or pl).get("id", "")
        index = song.get("index", 0) if song else 0
        if self.cur_key and self.cmd("openList", {"list": pl["list"], "id": vid, "index": index}):
            shown = song or pl
            self.title.set_text(shown.get("title", ""))
            self.mini_title.set_text(shown.get("title", ""))
            self.channel.setText(shown.get("channel", ""))
        elif self.host and vid:
            self.host.navigate_headless(f"https://www.youtube.com/watch?v={vid}&list={pl['list']}"
                                        + (f"&index={index + 1}" if index else ""))
        else:
            self.open_list_in_browser(song or pl)

    def on_list_clicked(self, idx):
        d = idx.data(ROLE_DATA)
        if not d:
            return
        if QGuiApplication.keyboardModifiers() & Qt.ControlModifier:
            self.open_list_in_browser(d)
        elif self.pl_open:
            self.play_list(self.pl_open, d)
        else:
            self.play_list(d)

    def _list_url(self, d):
        if self.pl_open and not d.get("list"):  # a song of the open playlist
            return f"https://www.youtube.com/watch?v={d['id']}&list={self.pl_open['list']}"
        if d.get("list", "").startswith("RD") or d.get("list") in ("LL", "WL"):
            return f"https://www.youtube.com/watch?v={d.get('id', '')}&list={d['list']}"
        return f"https://www.youtube.com/playlist?list={d['list']}"

    def open_list_in_browser(self, d):
        if d and (d.get("list") or d.get("id")):
            self.open_url(self._list_url(d))

    def list_menu(self, pos):
        idx = self.lists_view.indexAt(pos)
        if not idx.isValid():
            return
        d = idx.data(ROLE_DATA)
        m = QMenu(self)
        if self.pl_open:
            pl = self.pl_open
            m.addAction(T("lists_play_from"), lambda: self.play_list(pl, d))
        else:
            m.addAction(T("lists_play"), lambda: self.play_list(d))
            m.addAction(T("lists_show_songs"), lambda: self.show_songs(d))
        m.addAction(T("open_new_tab"), lambda: self.open_list_in_browser(d))
        m.addAction(T("copy_link"), lambda: QGuiApplication.clipboard().setText(self._list_url(d)))
        m.exec(self.lists_view.viewport().mapToGlobal(pos))

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
            self._maybe_recs()
            self._maybe_lists()

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
            self.dot.setToolTip(T("dot_connected", browser=browser_name(st), n=n))
        elif self.bridges:
            self.dot.setToolTip(T("dot_browser"))
        else:
            self.dot.setToolTip(T("dot_waiting"))
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
            self.title.set_text(T("no_video"))
            self.mini_title.set_text(T("no_video"))
            self.channel.setText(T("search_hint"))
        elif self.host and (self.host.preparing or self.host.running()):
            first = self.host.preparing
            self.title.set_text(T("preparing") if first else T("starting"))
            self.mini_title.set_text(self.title.text())
            self.channel.setText(T("first_start") if first else T("one_moment"))
        else:
            self.title.set_text(T("no_tab"))
            self.mini_title.set_text(T("no_tab"))
            self.channel.setText(T("install_bridge_hint") if not self.bridges else T("open_in_browser"))

        vid = st.get("id")
        if has_video and vid:
            if vid in self.thumbs:
                self.thumb.set_pixmap(self.thumbs[vid])
            else:
                self.request_thumb(vid, lambda pm, v=vid: self.thumb.set_pixmap(pm) if self.cur_state.get("id") == v else None)
        else:
            self.thumb.set_pixmap(None)

        nx = st.get("next") if connected and has_video else None
        nx_text = ""
        if isinstance(nx, dict) and nx.get("title"):
            nx_text = nx["title"] + (f" — {nx['channel']}" if nx.get("channel") else "")
        self.next_line.set_text(T("up_next", t=nx_text) if nx_text else "")
        self.next_line.setVisible(bool(nx_text))
        self.btn_next.setToolTip(T("next_tip") + ("\n" + T("up_next", t=nx_text) if nx_text else ""))
        if self.queue_panel.isVisible():
            self.queue_view.viewport().update()
            if self._queue_key(st) != self.q_key and has_video:
                self.load_queue()

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
        self.lists_view.viewport().update()
        self._count_play(st)
        self._maybe_recs()


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
        f"http://127.0.0.1:{PORT}/yt/open", data=json.dumps({"arg": arg}).encode(),
        headers={"Content-Type": "application/json", "X-YukiTube": "1"}, method="POST")
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
    # A SIGTERM, SIGHUP or Ctrl+C (pkill, logging out, a closed terminal)
    # quits like the Quit menu does, so the hidden Firefox is stopped too.
    # Python runs signal handlers only between bytecodes, never while Qt's
    # event loop waits, so a timer gives it a moment now and then.
    for name in ("SIGTERM", "SIGHUP", "SIGINT"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), lambda *_: QApplication.quit())
    sig_tick = QTimer()
    sig_tick.timeout.connect(lambda: None)
    sig_tick.start(500)
    load_fonts()
    f = QFont(FONT_UI, 9)
    app.setFont(f)

    w = Player()
    if not w.ws.listen(PORT):
        # Started by the YukiTube launcher while one is already running: the
        # running one takes the link or search (or just comes to the front).
        if forward_to_running(opts["arg"]) or opts["quiet"]:
            return 0
        QMessageBox.critical(None, APP_NAME,
                             T("port_busy", port=PORT, err=w.ws.error_string()))
        return 1
    # A downloaded update is installed now: a helper does it once this
    # process exits, then starts YukiTube again.
    if w.updater.apply_at_start() and w.updater.apply():
        return 0
    if w.updater.pending():
        w._show_update("ready")  # it did not install at the last start
    elif w.updater.auto_check() and not os.environ.get("YUKITUBE_SCREENSHOT"):
        QTimer.singleShot(4000, w.check_updates)
    pos = w.settings.value("pos")
    if isinstance(pos, QPoint):
        scr = QGuiApplication.screenAt(pos)
        if scr is not None:
            w.move(pos)
    w.show()
    if opts["firefox"] and opts["profile"]:
        w.host_firefox(opts["firefox"], opts["profile"], opts["arg"])
        app.aboutToQuit.connect(w.host.stop)
    elif opts["arg"]:
        QTimer.singleShot(0, lambda: w.handle_open(opts["arg"]))

    # Hyprland would tile it like any other window; it floats.
    QTimer.singleShot(400, hyprland.float_window)
    if os.environ.get("YUKITUBE_SCREENSHOT"):
        QTimer.singleShot(int(os.environ.get("YUKITUBE_SCREENSHOT_DELAY", "800")),
                          lambda: (w.grab().save(os.environ["YUKITUBE_SCREENSHOT"]), app.quit()))
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
