"""Updates from GitHub releases.

At start the remote asks GitHub for the latest release. When it is newer,
the player offers it; the user only clicks Download. The file for this kind
of install (see integration.install_kind) is downloaded beside the others
and checked against the release's SHA256SUMS. It is installed when the user
restarts YukiTube from the offer, or else at the player's next start: the
remote hands the file to a small helper script and quits; the helper waits
for it, installs, and starts YukiTube again.

  win-setup     the setup .exe, silently (/S) — Windows asks for admin rights
  win-portable  the .zip, unpacked over the folder (Data\\ stays)
  arch          the .pkg.tar.zst, with pkexec pacman -U (asks for the password)
  linux-tar     the .tar.xz, through its install.sh

All network traffic goes through Qt (the Windows remote's Python has no SSL).
"""
import json
import os
import re
import subprocess
import sys

from PySide6.QtCore import QCryptographicHash, QIODevice, QObject, QSaveFile, QUrl, Signal
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest

import integration

REPO = "eudunitrwe/yukitube"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"
WIN = sys.platform == "win32"
_NO_WINDOW = 0x08000000           # CREATE_NO_WINDOW
_NEW_GROUP = 0x00000200           # CREATE_NEW_PROCESS_GROUP
MAX_TRIES_AT_START = 2            # a failed install is retried once at start


def parse_version(v):
    nums = re.findall(r"\d+", (v or "").split("-")[0])
    return tuple(int(n) for n in nums[:4]) or (0,)


def newer(a, b):
    return parse_version(a) > parse_version(b)


def asset_name(kind, version):
    return {
        "win-setup": f"yukitube-{version}-windows-x64-setup.exe",
        "win-portable": f"yukitube-{version}-windows-x64.zip",
        "arch": f"yukitube-{version}-1-any.pkg.tar.zst",
        "linux-tar": f"yukitube-{version}-linux-x86_64.tar.xz",
    }.get(kind, "")


def update_dir(kind):
    if WIN:
        if kind == "win-portable":
            return os.path.join(integration.win_root(), "Data", "updates")
        return os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "YukiTube", "updates")
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "yukitube", "updates")


class Updater(QObject):
    # {"version", "page", "asset", "url", "sums", "size"}; {} when up to date
    checked = Signal(dict)
    check_failed = Signal(str)
    progress = Signal(int, int)         # bytes received, total
    downloaded = Signal(str)            # version
    download_failed = Signal(str)

    def __init__(self, net, settings, current, parent=None):
        super().__init__(parent)
        self.net = net
        self.settings = settings
        self.current = current
        self.kind = integration.install_kind()
        self.latest = {}
        self._reply = None
        self._file = None
        self._hash = None
        self._expected = ""
        self.downloading = False

    # ----------------------------------------------------------- settings
    def auto_check(self):
        return self.settings.value("update/auto", "true") in (True, "true")

    def set_auto_check(self, on):
        self.settings.setValue("update/auto", bool(on))

    def can_install(self):
        return self.kind != "dev"

    def pending(self):
        """The downloaded update waiting to be installed, or None. One that
        is not newer than this version (already installed) is cleared."""
        ver = str(self.settings.value("update/pending_version", "") or "")
        path = str(self.settings.value("update/pending_file", "") or "")
        if not ver or not path:
            return None
        if not newer(ver, self.current) or not os.path.isfile(path):
            self.clear_pending(remove=True)
            return None
        return {"version": ver, "file": path}

    def clear_pending(self, remove=False):
        path = str(self.settings.value("update/pending_file", "") or "")
        if remove and path:
            try:
                os.remove(path)
            except OSError:
                pass
        for k in ("pending_version", "pending_file", "tries"):
            self.settings.remove("update/" + k)

    def apply_at_start(self):
        """At the player's start: True when a downloaded update should be
        installed now (the caller then calls apply() and exits)."""
        p = self.pending()
        if not p or not self.can_install():
            return False
        tries = int(self.settings.value("update/tries", 0) or 0)
        return tries < MAX_TRIES_AT_START

    # -------------------------------------------------------------- check
    def _request(self, url, accept="application/octet-stream"):
        r = QNetworkRequest(QUrl(url))
        r.setRawHeader(b"User-Agent", f"YukiTube/{self.current}".encode())
        r.setRawHeader(b"Accept", accept.encode())
        r.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.NoLessSafeRedirectPolicy)
        return r

    def check(self):
        r = self._request(API_LATEST, "application/vnd.github+json")
        r.setTransferTimeout(15000)
        rep = self.net.get(r)
        rep.finished.connect(lambda: self._on_checked(rep))

    def _on_checked(self, rep):
        rep.deleteLater()
        if rep.error() != QNetworkReply.NoError:
            self.check_failed.emit(rep.errorString())
            return
        try:
            data = json.loads(bytes(rep.readAll().data()).decode("utf-8"))
        except ValueError as ex:
            self.check_failed.emit(str(ex))
            return
        ver = str(data.get("tag_name") or "").lstrip("vV")
        if not ver or data.get("draft") or data.get("prerelease") or not newer(ver, self.current):
            self.latest = {}
            self.checked.emit({})
            return
        assets = {a.get("name"): a for a in data.get("assets") or []}
        name = asset_name(self.kind, ver)
        a = assets.get(name) or {}
        sums = assets.get(f"yukitube-{ver}-SHA256SUMS") or {}
        self.latest = {
            "version": ver,
            "page": data.get("html_url") or RELEASES_PAGE,
            "asset": name if a else "",
            "url": a.get("browser_download_url", ""),
            "sums": sums.get("browser_download_url", ""),
            "size": int(a.get("size") or 0),
        }
        self.checked.emit(dict(self.latest))

    # ----------------------------------------------------------- download
    def download(self):
        info = self.latest
        if self.downloading or not info.get("url") or not info.get("sums"):
            if not self.downloading:
                self.download_failed.emit("no file for this system in the release")
            return
        self.downloading = True
        rep = self.net.get(self._request(info["sums"]))
        rep.finished.connect(lambda: self._on_sums(rep, info))
        self._reply = rep

    def _on_sums(self, rep, info):
        rep.deleteLater()
        self._reply = None
        if not self.downloading:
            return
        if rep.error() != QNetworkReply.NoError:
            return self._fail(rep.errorString())
        self._expected = ""
        for line in bytes(rep.readAll().data()).decode("utf-8", "replace").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].lstrip("*") == info["asset"]:
                self._expected = parts[0].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", self._expected):
            return self._fail("no checksum for " + info["asset"])
        d = update_dir(self.kind)
        try:
            os.makedirs(d, exist_ok=True)
        except OSError as ex:
            return self._fail(str(ex))
        # Older downloads are not needed any more.
        for f in os.listdir(d):
            if f.startswith("yukitube-") and f != info["asset"]:
                try:
                    os.remove(os.path.join(d, f))
                except OSError:
                    pass
        self._file = QSaveFile(os.path.join(d, info["asset"]))
        if not self._file.open(QIODevice.WriteOnly):
            return self._fail(self._file.errorString())
        self._hash = QCryptographicHash(QCryptographicHash.Sha256)
        rep = self.net.get(self._request(info["url"]))
        rep.readyRead.connect(lambda: self._on_data(rep))
        rep.downloadProgress.connect(lambda got, total: self.progress.emit(got, total if total > 0 else info["size"]))
        rep.finished.connect(lambda: self._on_downloaded(rep, info))
        self._reply = rep

    def _on_data(self, rep):
        if self._file is None:
            return
        chunk = rep.readAll()
        self._hash.addData(chunk)
        self._file.write(chunk)

    def _on_downloaded(self, rep, info):
        rep.deleteLater()
        self._reply = None
        if not self.downloading or self._file is None:
            return
        if rep.error() != QNetworkReply.NoError:
            return self._fail(rep.errorString())
        self._on_data(rep)
        got = bytes(self._hash.result().toHex().data()).decode()
        if got != self._expected:
            return self._fail("checksum mismatch")
        path = self._file.fileName()
        if not self._file.commit():
            return self._fail(self._file.errorString())
        self._file = None
        self.downloading = False
        self.settings.setValue("update/pending_version", info["version"])
        self.settings.setValue("update/pending_file", path)
        self.settings.setValue("update/tries", 0)
        self.settings.sync()
        self.downloaded.emit(info["version"])

    def cancel(self):
        if not self.downloading:
            return
        self.downloading = False
        if self._reply is not None:
            self._reply.abort()
        if self._file is not None:
            self._file.cancelWriting()
            self._file = None

    def _fail(self, err):
        self.downloading = False
        if self._file is not None:
            self._file.cancelWriting()
            self._file = None
        self.download_failed.emit(err)

    # -------------------------------------------------------------- apply
    def apply(self):
        """Starts the helper that installs the pending update once this
        process exits, then starts YukiTube again. The caller quits right
        after. False when there is nothing to install or no helper started."""
        p = self.pending()
        if not p or not self.can_install():
            return False
        self.settings.setValue("update/tries", int(self.settings.value("update/tries", 0) or 0) + 1)
        self.settings.sync()
        d = os.path.dirname(p["file"])
        try:
            if WIN:
                helper = os.path.join(d, "apply-update.ps1")
                with open(helper, "w", encoding="utf-8-sig") as f:
                    f.write(_PS_HELPER)
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
                     "-File", helper, "-ProcId", str(os.getpid()), "-Kind", self.kind,
                     "-Package", p["file"], "-Root", integration.win_root()],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=_NO_WINDOW | _NEW_GROUP, close_fds=True)
            else:
                helper = os.path.join(d, "apply-update.sh")
                with open(helper, "w", encoding="utf-8") as f:
                    f.write(_SH_HELPER)
                env = dict(os.environ)
                # PyInstaller points the libraries at its own; the tools the
                # helper runs need the system's.
                if "LD_LIBRARY_PATH_ORIG" in env:
                    env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
                else:
                    env.pop("LD_LIBRARY_PATH", None)
                log = open(os.path.join(d, "apply-update.log"), "ab")
                subprocess.Popen(
                    ["bash", helper, str(os.getpid()), self.kind, p["file"], integration.launcher()],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log, env=env, start_new_session=True,
                    close_fds=True)
        except OSError:
            return False
        return True


_SH_HELPER = r"""#!/bin/bash
# Installs a downloaded YukiTube update once the player has exited, then
# starts YukiTube again. Written by the YukiTube player (updater.py).
pid=$1 kind=$2 pkg=$3 launcher=$4
echo "== $(date) installing $pkg ($kind)"
for _ in $(seq 150); do kill -0 "$pid" 2>/dev/null || break; sleep 0.2; done
ok=0
case $kind in
  arch)
    pkexec pacman -U --noconfirm "$pkg" && ok=1 ;;
  linux-tar)
    tmp=$(mktemp -d)
    if tar -xJf "$pkg" -C "$tmp"; then
      dir=$(find "$tmp" -mindepth 1 -maxdepth 1 -type d -name 'yukitube-*' | head -1)
      [[ -n $dir ]] && (cd "$dir" && ./install.sh) && ok=1
    fi
    rm -rf "$tmp" ;;
esac
if ((ok)); then
  rm -f "$pkg"
  echo "installed"
else
  echo "not installed"
fi
[[ -n $launcher ]] && exec "$launcher"
"""

_PS_HELPER = r"""# Installs a downloaded YukiTube update once the player has exited, then
# starts YukiTube again. Written by the YukiTube player (updater.py).
param([int]$ProcId, [string]$Kind, [string]$Package, [string]$Root)
$ErrorActionPreference = 'Stop'
try { Wait-Process -Id $ProcId -Timeout 30 -ErrorAction SilentlyContinue } catch {}
# Whatever of YukiTube still runs from its folder (its Firefox) would keep
# files locked.
try {
  Get-Process | Where-Object { $_.Path -and $_.Path.StartsWith("$Root\", [StringComparison]::OrdinalIgnoreCase) } |
    Stop-Process -Force -ErrorAction SilentlyContinue
} catch {}
Start-Sleep -Seconds 1
$ok = $false
if ($Kind -eq 'win-setup') {
  try {
    $p = Start-Process -FilePath $Package -ArgumentList "/S /D=$Root" -Verb RunAs -Wait -PassThru
    $ok = ($p.ExitCode -eq 0)
  } catch {}
} elseif ($Kind -eq 'win-portable') {
  $tmp = Join-Path $env:TEMP ('yukitube-update-' + [guid]::NewGuid())
  $app = Join-Path $Root 'App'
  $old = Join-Path $Root 'App.old'
  try {
    Expand-Archive -LiteralPath $Package -DestinationPath $tmp -Force
    $src = Join-Path $tmp 'YukiTube'
    if (Test-Path -LiteralPath $old) { Remove-Item -LiteralPath $old -Recurse -Force }
    Rename-Item -LiteralPath $app -NewName 'App.old'
    try {
      Copy-Item -Path (Join-Path $src '*') -Destination $Root -Recurse -Force
      Remove-Item -LiteralPath $old -Recurse -Force -ErrorAction SilentlyContinue
      $ok = $true
    } catch {
      if (Test-Path -LiteralPath $app) { Remove-Item -LiteralPath $app -Recurse -Force -ErrorAction SilentlyContinue }
      Rename-Item -LiteralPath $old -NewName 'App'
    }
  } catch {} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
  }
}
if ($ok) { Remove-Item -LiteralPath $Package -Force -ErrorAction SilentlyContinue }
Start-Process -FilePath (Join-Path $Root 'YukiTube.exe')
"""
