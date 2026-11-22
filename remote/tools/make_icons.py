"""Render the YukiTube logo (a striped retrowave sun over a neon grid with a
play mark) to every icon file the app ships:

  remote/app/assets/yukitube.png, yukitube-512.png, yukitube.ico   the remote
  remote/browser/extension/icons/icon*.png                          the extension
  windows/yukitube.ico                                              YukiTube.exe, shortcuts
  pkgbuild/yukitube.svg                                             Linux app icon

The PNG/ICO files come from logo.py (Qt); the SVG is the same drawing written
out as vectors, so the Linux icon stays sharp at any size.

  python remote/tools/make_icons.py      (needs PySide6)
"""
import io
import math
import os
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


def svg(s=64.0):
    """logo.draw_logo, as SVG."""
    f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")  # noqa: E731
    inset, rad = s * .02, s * .22
    horizon = s * .64
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(s)} {f(s)}" width="{f(s)}" height="{f(s)}">',
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#12022b"/><stop offset=".55" stop-color="#3a0a5e"/>'
        '<stop offset="1" stop-color="#14031f"/></linearGradient>',
        f'<linearGradient id="sun" gradientUnits="userSpaceOnUse" x1="0" y1="{f(horizon - s * .44)}" x2="0" y2="{f(horizon)}">'
        '<stop offset="0" stop-color="#ffd319"/><stop offset=".5" stop-color="#ff901f"/>'
        '<stop offset="1" stop-color="#ff2a6d"/></linearGradient>',
        '<linearGradient id="border" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#ff2a6d"/><stop offset="1" stop-color="#05d9e8"/></linearGradient>',
        '<radialGradient id="glow"><stop offset="0" stop-color="#05d9e8" stop-opacity=".47"/>'
        '<stop offset="1" stop-color="#05d9e8" stop-opacity="0"/></radialGradient>',
        f'<clipPath id="clip"><rect x="{f(inset)}" y="{f(inset)}" width="{f(s - 2 * inset)}" '
        f'height="{f(s - 2 * inset)}" rx="{f(rad)}"/></clipPath>',
    ]
    # The sun's stripes, cut out with a mask.
    parts.append(f'<mask id="stripes"><rect width="{f(s)}" height="{f(horizon)}" fill="#fff"/>')
    y, h = horizon - s * .20, s * .018
    while y < horizon:
        parts.append(f'<rect y="{f(y)}" width="{f(s)}" height="{f(h)}" fill="#000"/>')
        y += h * 2.6
        h *= 1.25
    parts.append("</mask></defs>")

    parts.append(f'<g clip-path="url(#clip)"><rect width="{f(s)}" height="{f(s)}" fill="url(#bg)"/>')
    parts.append(f'<circle cx="{f(s * .5)}" cy="{f(horizon - s * .14)}" r="{f(s * .30)}" '
                 'fill="url(#sun)" mask="url(#stripes)"/>')
    parts.append(f'<rect y="{f(horizon)}" width="{f(s)}" height="{f(s - horizon)}" fill="#140228" fill-opacity=".9"/>')
    lines = []
    for i in range(-6, 7):
        lines.append(f'<line x1="{f(s / 2 + i * s * .04)}" y1="{f(horizon)}" x2="{f(s / 2 + i * s * .26)}" y2="{f(s)}"/>')
    k, step, yy = 0, s * .03, horizon
    while yy < s:
        lines.append(f'<line x1="0" y1="{f(yy)}" x2="{f(s)}" y2="{f(yy)}"/>')
        k += 1
        yy = horizon + step * k * k * .9
    parts.append(f'<g stroke="#ff2a6d" stroke-width="{f(max(1.0, s * .012))}">{"".join(lines)}</g>')
    parts.append(f'<line x1="0" y1="{f(horizon)}" x2="{f(s)}" y2="{f(horizon)}" stroke="#05d9e8" '
                 f'stroke-width="{f(max(1.0, s * .02))}"/>')
    cx, cy, t = s * .52, s * .44, s * .20
    parts.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(t * 2)}" fill="url(#glow)"/>')
    parts.append(f'<path d="M{f(cx - t * .75)} {f(cy - t)}L{f(cx + t)} {f(cy)}L{f(cx - t * .75)} {f(cy + t)}Z" '
                 f'fill="#fff" stroke="#05d9e8" stroke-width="{f(max(1.0, s * .025))}" stroke-linejoin="round"/>')
    parts.append("</g>")
    parts.append(f'<rect x="{f(inset)}" y="{f(inset)}" width="{f(s - 2 * inset)}" height="{f(s - 2 * inset)}" '
                 f'rx="{f(rad)}" fill="none" stroke="url(#border)" stroke-width="{f(max(1.0, s * .03))}"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


assets = os.path.join(ROOT, "app", "assets")
ext = os.path.join(ROOT, "browser", "extension", "icons")
for s in (16, 32, 48, 128):
    logo_pixmap(s).save(os.path.join(ext, f"icon{s}.png"))
logo_pixmap(256).save(os.path.join(assets, "yukitube.png"))
logo_pixmap(512).save(os.path.join(assets, "yukitube-512.png"))
write_ico(os.path.join(assets, "yukitube.ico"))
write_ico(os.path.join(REPO, "windows", "yukitube.ico"))
with open(os.path.join(REPO, "pkgbuild", "yukitube.svg"), "w") as f:
    f.write(svg(256.0))
print("icons written")
