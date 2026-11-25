"""Prepares YukiTube's Firefox profile, out of sight.

The remote talks to YouTube through the "YukiTube Bridge" userscript, which
lives in Violentmonkey. Installing a userscript normally means a Violentmonkey
tab with an Install button. Instead, the remote calls this before it starts
YouTube, on the first launch and whenever the bridge has a new version:
Firefox starts headless (no window at all) on the profile with Marionette,
its automation interface, switched on; the script hands the userscript
straight to Violentmonkey from one of Violentmonkey's own pages, removes
bridges left from older versions, and Firefox quits. Only the standard
library is used.

    yukitube-remote --prepare-profile <firefox> <profile>
"""
import json
import os
import socket
import subprocess
import sys
import time

VIOLENTMONKEY = "{aecec67f-0d10-4fa7-b7c7-609a2db280cf}"
PORT = os.environ.get("YUKITUBE_PORT") or "8975"
USERSCRIPT_URL = f"http://127.0.0.1:{PORT}/yukitube.user.js"
MARKER = ".yukitube-bridge-installed"  # holds the installed bridge's version
TIMEOUT = 60
WIN = sys.platform == "win32"
_NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW: no console flashing up on Windows

# On Windows, firefox.exe is a small launcher that starts the real browser as
# a separate process and exits at once. With -wait-for-browser it stays until
# the browser exits, so the process started is the one to watch.
WIN_ARGS = ["-wait-for-browser"] if WIN else []


def win_kill_tree(pid, force=True):
    """Windows: ends a process and everything it started. Without force, the
    windows get a normal close (the browser saves and exits)."""
    if not pid:
        return
    cmd = ["taskkill", "/PID", str(pid), "/T"] + (["/F"] if force else [])
    try:
        subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=_NO_WINDOW, timeout=15)
    except (OSError, subprocess.SubprocessError):
        pass


def win_free_profile(profile):
    """Windows: ends any Firefox still running on `profile` (one left behind
    when the remote did not exit cleanly). Only processes whose command line
    names this profile are touched, never the user's own Firefox."""
    prof = os.path.normcase(os.path.abspath(profile)).replace("'", "''")
    script = (
        "Get-CimInstance Win32_Process -Filter \"Name='firefox.exe'\" | "
        f"Where-Object {{ $_.CommandLine -and $_.CommandLine.ToLower().Contains('{prof.lower()}') }} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=_NO_WINDOW, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass
    for _ in range(50):  # the lock goes with the process
        if not profile_in_use(profile):
            return
        time.sleep(0.1)


def bridge_version(code):
    for line in code.splitlines():
        if line.startswith("// @version"):
            return line.split()[-1]
    return ""


def is_current(profile, code):
    """True when the profile already has this version of the bridge."""
    try:
        with open(os.path.join(profile, MARKER)) as f:
            return f.readline().strip() == bridge_version(code)
    except OSError:
        return False


class Marionette:
    """The few Marionette commands needed, over its JSON-on-TCP protocol."""

    def __init__(self, port):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=20)
        self.buf = b""
        self.msg_id = 0
        self._read()  # the server's greeting

    def _read(self):
        while b":" not in self.buf:
            self._fill()
        size, _, self.buf = self.buf.partition(b":")
        size = int(size)
        while len(self.buf) < size:
            self._fill()
        data, self.buf = self.buf[:size], self.buf[size:]
        return json.loads(data)

    def _fill(self):
        chunk = self.sock.recv(65536)
        if not chunk:
            raise ConnectionError("Firefox closed the connection")
        self.buf += chunk

    def call(self, name, params=None):
        self.msg_id += 1
        data = json.dumps([0, self.msg_id, name, params or {}]).encode()
        self.sock.sendall(str(len(data)).encode() + b":" + data)
        while True:
            reply = self._read()
            if reply[0] == 1 and reply[1] == self.msg_id:
                break
        if reply[2]:
            raise RuntimeError(f"{name}: {reply[2].get('error')}: {reply[2].get('message')}")
        result = reply[3]
        return result.get("value") if isinstance(result, dict) and "value" in result else result

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def profile_in_use(profile):
    """True while another Firefox has the profile open."""
    lock = os.path.join(profile, "lock")
    if os.path.islink(lock):  # Linux: "lock" -> "<ip>:+<pid>"
        try:
            pid = int(os.readlink(lock).rsplit("+", 1)[1])
            os.kill(pid, 0)
            return True
        except (ValueError, IndexError, ProcessLookupError):
            return False
        except PermissionError:
            return True
        except OSError:
            return False
    lock = os.path.join(profile, "parent.lock")
    if sys.platform == "win32" and os.path.exists(lock):
        try:  # Firefox holds it open without sharing while it runs
            with open(lock, "a"):
                return False
        except OSError:
            return True
    return False


def _wait_port(profile, proc, deadline):
    path = os.path.join(profile, "MarionetteActivePort")
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Firefox exited early ({proc.returncode})")
        try:
            with open(path) as f:
                port = int(f.read().strip() or 0)
            if port:
                return port
        except (OSError, ValueError):
            pass
        time.sleep(0.2)
    raise TimeoutError("Firefox did not start Marionette")


# Runs inside Violentmonkey's own options page, the one place its internal
# "ParseScript" command (what its Install button calls) can be sent from.
_INSTALL_JS = """
const [code, url, done] = arguments;
const page = window.wrappedJSObject || window;
let msg = { cmd: "ParseScript", data: { code, url, from: url, message: "" } };
if (typeof cloneInto === "function") msg = cloneInto(msg, page);
page.browser.runtime.sendMessage(msg).then(
  (r) => done({ ok: true, result: r === undefined ? null : JSON.parse(page.JSON.stringify(r)) }),
  (e) => done({ ok: false, error: String(e && e.message || e) }));
"""

# Bridges from older versions (another namespace, or the old name) go: two
# bridges in one tab would compete for it.
_CLEANUP_JS = """
const [keepNamespace, done] = arguments;
const page = window.wrappedJSObject || window;
const send = (cmd, data) => {
  let msg = { cmd, data };
  if (typeof cloneInto === "function") msg = cloneInto(msg, page);
  return page.browser.runtime.sendMessage(msg).then((r) => r === undefined ? null : JSON.parse(page.JSON.stringify(r)));
};
(async () => {
  const data = await send("GetData", {});
  const list = Object.values(data || {}).find((v) => Array.isArray(v) && v.length && v[0] && v[0].props) || [];
  const old = list.filter((s) => {
    const m = s.meta || {};
    const name = String(m.name || "");
    return (m.namespace !== keepNamespace && /YukiTube Bridge/i.test(name)) || /neontube/i.test(name + " " + (m.namespace || ""));
  }).map((s) => s.props.id);
  for (const id of old) await send("MarkRemoved", { id, removed: true });
  if (old.length) await send("RemoveScripts", old);
  done({ ok: true, removed: old.length });
})().catch((e) => done({ ok: false, error: String(e && e.message || e) }));
"""

_HOST_JS = """
const p = WebExtensionPolicy.getByID(arguments[0]);
return p ? p.mozExtensionHostname : null;
"""


def install_bridge(firefox, profile, code, log=print):
    """Installs the userscript into Violentmonkey in `profile`. Returns True
    when it is installed (or already was), False when it could not be."""
    if is_current(profile, code):
        return True
    if profile_in_use(profile) and WIN:
        win_free_profile(profile)
    if profile_in_use(profile):
        log("profile in use; skipping")
        return False
    port_file = os.path.join(profile, "MarionetteActivePort")
    try:
        os.remove(port_file)
    except OSError:
        pass
    deadline = time.monotonic() + TIMEOUT
    # Newer Firefox (160+) gives Marionette chrome-context access only with
    # this variable; the --remote-allow-system-access flag alone is refused.
    env = dict(os.environ, MOZ_HEADLESS="1", MOZ_REMOTE_ALLOW_SYSTEM_ACCESS="1")
    env.pop("MOZ_MARIONETTE", None)
    flags = _NO_WINDOW if WIN else 0
    proc = subprocess.Popen(
        [firefox] + WIN_ARGS + ["--headless", "--marionette", "--remote-allow-system-access", "--new-instance",
                                "--profile", profile, "about:blank"],
        env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags)
    mn = None
    try:
        mn = Marionette(_wait_port(profile, proc, deadline))
        mn.call("WebDriver:NewSession", {"capabilities": {}})

        # Add-ons start a moment after the browser.
        mn.call("Marionette:SetContext", {"value": "chrome"})
        host = None
        while time.monotonic() < deadline:
            host = mn.call("WebDriver:ExecuteScript", {"script": _HOST_JS, "args": [VIOLENTMONKEY]})
            if host:
                break
            time.sleep(0.3)
        if not host:
            raise RuntimeError("Violentmonkey is not enabled in the profile")

        mn.call("Marionette:SetContext", {"value": "content"})
        mn.call("WebDriver:Navigate", {"url": f"moz-extension://{host}/options/index.html"})
        last = None
        while time.monotonic() < deadline:
            r = mn.call("WebDriver:ExecuteAsyncScript",
                        {"script": _INSTALL_JS, "args": [code, USERSCRIPT_URL], "scriptTimeout": 15000})
            if r and r.get("ok"):
                last = None
                break
            last = (r or {}).get("error")
            time.sleep(0.5)  # Violentmonkey's background is still loading
        if last is not None:
            raise RuntimeError(f"Violentmonkey refused the script: {last}")
        log("bridge installed")
        namespace = next((ln.split()[-1] for ln in code.splitlines() if ln.startswith("// @namespace")), "")
        r = mn.call("WebDriver:ExecuteAsyncScript",
                    {"script": _CLEANUP_JS, "args": [namespace], "scriptTimeout": 15000})
        log(f"old bridges removed: {(r or {}).get('removed', (r or {}).get('error'))}")
        try:
            mn.call("Marionette:Quit", {"flags": ["eAttemptQuit"]})
        except (RuntimeError, OSError):
            pass
        proc.wait(timeout=max(5, deadline - time.monotonic()))
        with open(os.path.join(profile, MARKER), "w") as f:
            f.write(bridge_version(code) + "\n" + time.strftime("%Y-%m-%d %H:%M:%S\n"))
        return True
    except Exception as ex:  # noqa: BLE001 - never keep YukiTube from opening
        log(f"could not install the bridge: {ex}")
        return False
    finally:
        if mn:
            mn.close()
        if WIN:
            # The browser may outlive the launcher; nothing may keep the profile.
            win_kill_tree(proc.pid)
            win_free_profile(profile) if profile_in_use(profile) else None
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        try:
            os.remove(port_file)
        except OSError:
            pass
