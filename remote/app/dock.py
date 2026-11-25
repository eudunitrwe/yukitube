"""Docking: keeps the remote in the bottom-right corner of the YukiTube
window and follows it when that window moves, resizes, or changes workspace.

A Qt app cannot see other apps' windows on its own (and on Wayland not even
place its own), so each platform asks its window manager:

  Hyprland   the IPC socket ($XDG_RUNTIME_DIR/hypr/<signature>/.socket.sock):
             j/clients to find both windows, dispatch to float and move ours
             (Lua dispatchers on Hyprland 0.56+, the classic ones before).
  Windows    user32: the Firefox window running YukiTube's firefox.exe
             (YUKITUBE_FIREFOX, set by YukiTube.exe), and its frame bounds.
"""
import json
import os
import socket
import sys

from PySide6.QtCore import QObject, QPoint, QTimer
from PySide6.QtGui import QGuiApplication

MARGIN = 18          # px between the remote and the window's edges
BROWSER_CLASS = "yukitube"


class _Hyprland:
    def __init__(self, pid=None):
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
        runtime = os.environ.get("XDG_RUNTIME_DIR", "")
        self.pid = pid or os.getpid()
        self.lua = None  # Hyprland 0.56+ takes Lua dispatchers; older ones the classic syntax
        self.path = None
        for base in (os.path.join(runtime, "hypr") if runtime else "", "/tmp/hypr"):
            p = os.path.join(base, sig, ".socket.sock") if base and sig else ""
            if p and os.path.exists(p):
                self.path = p
                break

    def ok(self):
        return self.path is not None

    def _ask(self, cmd):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(self.path)
            s.sendall(cmd.encode())
            out = bytearray()
            while True:
                chunk = s.recv(65536)
                if not chunk:
                    break
                out += chunk
        return out.decode("utf-8", "replace")

    def _dispatch(self, addr, lua, classic):
        if self.lua is None:
            # Find out once, on our own window: floating it is harmless.
            r = self._ask(f'dispatch hl.dsp.window.float({{ action = "enable", window = "address:{addr}" }})')
            self.lua = not r.startswith("error")
        if self.lua:
            return self._ask("dispatch " + lua.replace("@W", f'window = "address:{addr}"'))
        return self._ask("dispatch " + classic.replace("@W", f"address:{addr}"))

    def float_self(self):
        """The remote is resizable, so Hyprland would tile it like any other
        window; it floats instead, as it did when its size was fixed."""
        clients = json.loads(self._ask("j/clients"))
        me = next((c for c in clients if c.get("pid") == self.pid and c.get("mapped")), None)
        if me and not me.get("floating"):
            self._dispatch(me["address"], 'hl.dsp.window.float({ action = "enable", @W })', "setfloating @W")

    def follow(self, widget):
        clients = json.loads(self._ask("j/clients"))
        me = next((c for c in clients if c.get("pid") == self.pid and c.get("mapped")), None)
        browsers = [c for c in clients if c.get("class") == BROWSER_CLASS and c.get("mapped")
                    and not c.get("hidden")]
        if not me or not browsers:
            return
        fx = min(browsers, key=lambda c: c.get("focusHistoryID", 1 << 30))
        addr = me["address"]
        if not me.get("floating"):
            self._dispatch(addr, 'hl.dsp.window.float({ action = "enable", @W })', "setfloating @W")
        ws = fx["workspace"]["id"]
        if me["workspace"]["id"] != ws:
            self._dispatch(addr, f'hl.dsp.window.move({{ workspace = "{ws}", follow = false, @W }})',
                           f"movetoworkspacesilent {ws},@W")
        x = fx["at"][0] + fx["size"][0] - me["size"][0] - MARGIN
        y = fx["at"][1] + fx["size"][1] - me["size"][1] - MARGIN
        if [x, y] != list(me["at"]):
            self._dispatch(addr, f"hl.dsp.window.move({{ x = {x}, y = {y}, @W }})",
                           f"movewindowpixel exact {x} {y},@W")


class _Windows:
    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.ct, self.wt = ctypes, wintypes
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        try:
            self.dwm = ctypes.windll.dwmapi
        except OSError:
            self.dwm = None
        exe = os.environ.get("YUKITUBE_FIREFOX", "")
        self.firefox = os.path.normcase(os.path.abspath(exe)) if exe else ""

    def ok(self):
        return True

    def _image(self, hwnd):
        ct, wt = self.ct, self.wt
        pid = wt.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ct.byref(pid))
        h = self.kernel32.OpenProcess(0x1000, False, pid.value)  # QUERY_LIMITED_INFORMATION
        if not h:
            return ""
        try:
            buf = ct.create_unicode_buffer(1024)
            size = wt.DWORD(len(buf))
            if self.kernel32.QueryFullProcessImageNameW(h, 0, buf, ct.byref(size)):
                return os.path.normcase(buf.value)
            return ""
        finally:
            self.kernel32.CloseHandle(h)

    def _browser(self):
        """The topmost visible top-level Firefox window of YukiTube."""
        ct, wt = self.ct, self.wt
        found = []

        @ct.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
        def each(hwnd, _):
            if not self.user32.IsWindowVisible(hwnd) or self.user32.GetWindow(hwnd, 4):  # GW_OWNER
                return True
            cls = ct.create_unicode_buffer(64)
            self.user32.GetClassNameW(hwnd, cls, 64)
            if cls.value != "MozillaWindowClass" or self.user32.GetWindowTextLengthW(hwnd) == 0:
                return True
            if self.firefox and self._image(hwnd) != self.firefox:
                return True
            found.append(hwnd)
            return False  # EnumWindows goes top to bottom: the first one is in front
        self.user32.EnumWindows(each, 0)
        return found[0] if found else None

    def _rect(self, hwnd):
        ct, wt = self.ct, self.wt
        r = wt.RECT()
        # The visible frame, without the invisible resize borders.
        if not (self.dwm and self.dwm.DwmGetWindowAttribute(hwnd, 9, ct.byref(r), ct.sizeof(r)) == 0):
            self.user32.GetWindowRect(hwnd, ct.byref(r))
        return r.left, r.top, r.right, r.bottom

    def follow(self, widget):
        hwnd = self._browser()
        if not hwnd or self.user32.IsIconic(hwnd):
            return
        left, top, right, bottom = self._rect(hwnd)
        # Qt places windows in device-independent pixels; on Windows a
        # screen's origin is the same in both, only distances scale.
        screen = QGuiApplication.screenAt(QPoint(right - 1, bottom - 1)) or widget.screen()
        origin = screen.geometry().topLeft()
        dpr = screen.devicePixelRatio() or 1.0
        to_logical = lambda px, py: (origin.x() + (px - origin.x()) / dpr,  # noqa: E731
                                     origin.y() + (py - origin.y()) / dpr)
        rx, ry = to_logical(right, bottom)
        x = int(rx - widget.width() - MARGIN)
        y = int(ry - widget.height() - MARGIN)
        if widget.pos() != QPoint(x, y):
            widget.move(x, y)


def backend():
    if sys.platform == "win32":
        return _Windows()
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        h = _Hyprland()
        if h.ok():
            return h
    return None


class Docker(QObject):
    """Follows the YukiTube window while enabled."""

    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.impl = backend()
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.tick)

    def available(self):
        return self.impl is not None

    def set_enabled(self, on):
        if on and self.impl:
            self.tick()
            self.timer.start()
        else:
            self.timer.stop()

    def float_self(self):
        f = getattr(self.impl, "float_self", None)
        if f:
            try:
                f()
            except Exception as e:  # noqa: BLE001
                print("dock:", e, file=sys.stderr)

    def tick(self):
        try:
            self.impl.follow(self.widget)
        except Exception as e:  # a window manager hiccup must not stop the remote
            print("dock:", e, file=sys.stderr)
