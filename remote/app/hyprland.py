"""Hyprland: the remote floats instead of being tiled like other windows.

Asked over Hyprland's IPC socket ($XDG_RUNTIME_DIR/hypr/<signature>/
.socket.sock): j/clients finds the remote's own window, and a dispatch
floats it (Lua dispatchers on Hyprland 0.56+, the classic ones before).
Elsewhere this does nothing.
"""
import json
import os
import socket
import sys


def _socket_path():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    if not sig:
        return None
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    for base in (os.path.join(runtime, "hypr") if runtime else "", "/tmp/hypr"):
        p = os.path.join(base, sig, ".socket.sock") if base else ""
        if p and os.path.exists(p):
            return p
    return None


def _ask(path, cmd):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        s.connect(path)
        s.sendall(cmd.encode())
        out = bytearray()
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            out += chunk
    return out.decode("utf-8", "replace")


def float_window(pid=None):
    path = _socket_path()
    if not path:
        return
    try:
        pid = pid or os.getpid()
        me = next((c for c in json.loads(_ask(path, "j/clients"))
                   if c.get("pid") == pid and c.get("mapped")), None)
        if not me or me.get("floating"):
            return
        addr = me["address"]
        r = _ask(path, f'dispatch hl.dsp.window.float({{ action = "enable", window = "address:{addr}" }})')
        if r.startswith("error"):
            _ask(path, f"dispatch setfloating address:{addr}")
    except Exception as e:  # noqa: BLE001 - a window manager hiccup must not stop the remote
        print("hyprland:", e, file=sys.stderr)
