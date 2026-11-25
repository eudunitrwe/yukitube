"""Render the YukiTube logo (remote/app/assets/logo.svg: Yuki the cat in front
of the retrowave sun) to every icon file the app ships:

  remote/app/assets/yukitube.png, yukitube-512.png, yukitube.ico   the remote
  remote/browser/extension/icons/icon*.png                          the extension
  windows/yukitube.ico                                              YukiTube.exe, shortcuts
  pkgbuild/yukitube.svg                                             Linux app icon

The PNG/ICO files are rendered by logo.py (Qt); the Linux icon is logo.svg
itself, so it stays sharp at any size.

  python remote/tools/make_icons.py      (needs PySide6)
"""
import io
import os
import shutil
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "app"))

from PySide6.QtCore import QBuffer, QIODevice  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

app = QGuiApplication.instance() or QGuiApplication(["x", "-platform", "offscreen"])
from logo import logo_pixmap  # noqa: E402


def png_bytes(size):
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    logo_pixmap(size).save(buf, "PNG")
    return bytes(buf.data())


def write_ico(path, sizes=(16, 20, 24, 32, 40, 48, 64, 128, 256)):
    """A multi-size ICO with PNG entries (Windows Vista and later)."""
    images = [png_bytes(s) for s in sizes]
    out = io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, len(sizes)))
    offset = 6 + 16 * len(sizes)
    for s, data in zip(sizes, images):
        out.write(struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    for data in images:
        out.write(data)
    with open(path, "wb") as f:
        f.write(out.getvalue())


assets = os.path.join(ROOT, "app", "assets")
ext = os.path.join(ROOT, "browser", "extension", "icons")
for s in (16, 32, 48, 128):
    logo_pixmap(s).save(os.path.join(ext, f"icon{s}.png"))
logo_pixmap(256).save(os.path.join(assets, "yukitube.png"))
logo_pixmap(512).save(os.path.join(assets, "yukitube-512.png"))
write_ico(os.path.join(assets, "yukitube.ico"))
write_ico(os.path.join(REPO, "windows", "yukitube.ico"))
shutil.copyfile(os.path.join(assets, "logo.svg"), os.path.join(REPO, "pkgbuild", "yukitube.svg"))
print("icons written")
