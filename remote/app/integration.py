"""How YukiTube is installed, and its place in the desktop: starting with
the computer, and a shortcut on the desktop.

Install kinds (they decide which release file an update uses):
  win-setup     Windows, installed by the setup .exe (App\\installed exists)
  win-portable  Windows, the portable folder from the .zip
  arch          the Arch Linux package (/usr/share/yukitube)
  linux-tar     the Linux .tar.xz, installed per user by install.sh
  dev           run from a checkout: updates are only announced
"""
import os
import shutil
import subprocess
import sys

from PySide6.QtCore import QSettings, QStandardPaths

WIN = sys.platform == "win32"
_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW
_RUN_KEY = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
APP_DIR = os.path.dirname(os.path.abspath(__file__))


def win_root():
    """Windows: the YukiTube folder (YukiTube.exe, App\\). The remote's Python
    is App\\Remote\\runtime\\pythonw.exe."""
    return os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "..", ".."))


def install_kind():
    if WIN:
        root = win_root()
        if not os.path.isfile(os.path.join(root, "YukiTube.exe")):
            return "dev"
        return "win-setup" if os.path.isfile(os.path.join(root, "App", "installed")) else "win-portable"
    if getattr(sys, "frozen", False):
        return "linux-tar"
    if APP_DIR.startswith("/usr/share/yukitube/"):
        return "arch"
    return "dev"


def launcher():
    """The command that starts YukiTube (the launcher, not the remote alone)."""
    env = os.environ.get("YUKITUBE_LAUNCHER") or os.environ.get("YUKITUBE_OPEN")
    if env and os.path.isfile(env):
        return env
    if WIN:
        exe = os.path.join(win_root(), "YukiTube.exe")
        return exe if os.path.isfile(exe) else ""
    kind = install_kind()
    if kind == "arch":
        return "/usr/bin/yukitube"
    if kind == "linux-tar":
        home = os.path.expanduser("~/.local/bin/yukitube")
        if os.path.isfile(home):
            return home
    checkout = os.path.normpath(os.path.join(APP_DIR, "..", "..", "bin", "yukitube"))
    if os.path.isfile(checkout):
        return checkout
    return shutil.which("yukitube") or ""


# ------------------------------------------------------------- autostart
def _autostart_file():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "autostart", "yukitube.desktop")


def autostart_enabled():
    if WIN:
        return bool(QSettings(_RUN_KEY, QSettings.NativeFormat).value("YukiTube"))
    return os.path.isfile(_autostart_file())


def set_autostart(on):
    """Starts YukiTube with the computer (Windows: the Run key; Linux: an XDG
    autostart entry, which GNOME, KDE, Xfce and systemd/uwsm sessions read).
    Returns True when done."""
    exe = launcher()
    if WIN:
        s = QSettings(_RUN_KEY, QSettings.NativeFormat)
        if on:
            if not exe:
                return False
            s.setValue("YukiTube", f'"{exe}"')
        else:
            s.remove("YukiTube")
        s.sync()
        return s.status() == QSettings.NoError
    path = _autostart_file()
    if not on:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except OSError:
            return False
        return True
    if not exe:
        return False
    return _write_desktop_file(path, exe, executable=False)


# ------------------------------------------------------- desktop shortcut
def _desktop_dir():
    if not WIN:
        try:
            out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True, timeout=5)
            d = out.stdout.strip()
            if out.returncode == 0 and d:
                return d
        except (OSError, subprocess.SubprocessError):
            pass
    return QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)


def _shortcut_path():
    return os.path.join(_desktop_dir(), "YukiTube.lnk" if WIN else "yukitube.desktop")


def _public_shortcut():
    """Windows: the shortcut the installer puts on everyone's desktop."""
    pub = os.environ.get("PUBLIC")
    return os.path.join(pub, "Desktop", "YukiTube.lnk") if WIN and pub else ""


def shortcut_state():
    """(exists, removable): removable is False for the installer's shortcut
    for all users, which only the uninstaller takes away."""
    if os.path.isfile(_shortcut_path()):
        return True, True
    pub = _public_shortcut()
    if pub and os.path.isfile(pub):
        return True, False
    return False, True


def set_shortcut(on):
    path = _shortcut_path()
    if not on:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except OSError:
            return False
        return True
    exe = launcher()
    if not exe:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if WIN:
        icon = os.path.join(win_root(), "App", "Remote", "app", "assets", "yukitube.ico")
        q = lambda s: s.replace("'", "''")  # noqa: E731
        script = (
            "$s = New-Object -ComObject WScript.Shell; "
            f"$l = $s.CreateShortcut('{q(path)}'); "
            f"$l.TargetPath = '{q(exe)}'; "
            f"$l.WorkingDirectory = '{q(os.path.dirname(exe))}'; "
            f"$l.IconLocation = '{q(icon if os.path.isfile(icon) else exe)},0'; "
            "$l.Description = 'YukiTube'; $l.Save()")
        try:
            subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=_NO_WINDOW, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return False
        return os.path.isfile(path)
    if not _write_desktop_file(path, exe, executable=True):
        return False
    # GNOME's desktop icons start only launchers marked as trusted.
    if shutil.which("gio"):
        subprocess.run(["gio", "set", path, "metadata::trusted", "true"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def _icon():
    """The installed icon's name, or the logo's full path from a checkout."""
    for d in ("/usr/share/icons/hicolor/scalable/apps",
              os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps")):
        if os.path.isfile(os.path.join(d, "yukitube.svg")):
            return "yukitube"
    return os.path.join(APP_DIR, "assets", "yukitube-512.png")


def _write_desktop_file(path, exe, executable):
    text = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=YukiTube\n"
        "Comment=A retrowave YouTube player, without ads\n"
        "Comment[ro]=Player YouTube retrowave, fără reclame\n"
        f'Exec="{exe}"\n'
        f"Icon={_icon()}\n"
        "Terminal=false\n"
        "Categories=AudioVideo;Video;\n"
        "StartupWMClass=yukitube-remote\n"
    )
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, 0o755 if executable else 0o644)
        os.replace(tmp, path)
    except OSError:
        return False
    return True
