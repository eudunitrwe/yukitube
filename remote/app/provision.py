"""Prepares YukiTube's Firefox profile on the first launch, out of sight.

The remote talks to YouTube through the "YukiTube Bridge" userscript, which
lives in Violentmonkey. Installing a userscript normally means a Violentmonkey
tab with an Install button. Instead, the launcher calls this once, before it
opens the YukiTube window: Firefox starts headless (no window at all) on the
profile with Marionette, its automation interface, switched on; the script
hands the userscript straight to Violentmonkey from one of Violentmonkey's
own pages; and Firefox quits. Only the standard library is used.

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
MARKER = ".yukitube-bridge-installed"
TIMEOUT = 60


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

_HOST_JS = """
const p = WebExtensionPolicy.getByID(arguments[0]);
return p ? p.mozExtensionHostname : null;
"""


def install_bridge(firefox, profile, code, log=print):
    """Installs the userscript into Violentmonkey in `profile`. Returns True
    when it is installed (or already was), False when it could not be."""
    if os.path.exists(os.path.join(profile, MARKER)):
        return True
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
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    proc = subprocess.Popen(
        [firefox, "--headless", "--marionette", "--remote-allow-system-access", "--new-instance", "--profile", profile, "about:blank"],
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
        try:
            mn.call("Marionette:Quit", {"flags": ["eAttemptQuit"]})
        except (RuntimeError, OSError):
            pass
        proc.wait(timeout=max(5, deadline - time.monotonic()))
        with open(os.path.join(profile, MARKER), "w") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S\n"))
        return True
    except Exception as ex:  # noqa: BLE001 - never keep YukiTube from opening
        log(f"could not install the bridge: {ex}")
        return False
    finally:
        if mn:
            mn.close()
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
