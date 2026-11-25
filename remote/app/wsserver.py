"""Minimal WebSocket server built on QTcpServer (RFC 6455, text frames only).

Only listens on 127.0.0.1. Browser agents (the extension background or the
userscript) connect here and exchange JSON messages with the player.
"""
import base64
import hashlib
import json
import struct

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QHostAddress, QTcpServer

_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Origins allowed to talk to the player. Anything else is refused at handshake.
_ALLOWED_PREFIXES = (
    "chrome-extension://",
    "moz-extension://",
    "safari-web-extension://",
    "https://www.youtube.com",
    "https://youtube.com",
    "https://m.youtube.com",
    "https://music.youtube.com",
)


HTTP_CID = -1  # pseudo connection id for userscripts talking plain HTTP


class _Conn:
    __slots__ = ("sock", "buf", "open", "frag", "frag_op", "cid")

    def __init__(self, cid, sock):
        self.cid = cid
        self.sock = sock
        self.buf = bytearray()
        self.open = False
        self.frag = bytearray()
        self.frag_op = 0


class WsServer(QObject):
    message = Signal(int, dict)       # connection id, decoded JSON
    old_bridge = Signal()             # a NeonTube-era userscript called in
    open_request = Signal(str)        # a second YukiTube launch: link, search or ""
    connected = Signal(int)
    disconnected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._srv = QTcpServer(self)
        self._srv.newConnection.connect(self._on_new)
        self._conns = {}
        self._next = 1
        self._http_q = {}  # tab key -> queued commands for HTTP agents
        self.userscript = b""  # served at /yukitube.user.js
        self.ping = {"app": "yukitube-remote"}

    def listen(self, port):
        return self._srv.listen(QHostAddress(QHostAddress.LocalHost), port)

    def error_string(self):
        return self._srv.errorString()

    # ------------------------------------------------------------------ io
    def _on_new(self):
        while self._srv.hasPendingConnections():
            sock = self._srv.nextPendingConnection()
            cid = self._next
            self._next += 1
            c = _Conn(cid, sock)
            self._conns[cid] = c
            sock.readyRead.connect(lambda c=c: self._on_read(c))
            sock.disconnected.connect(lambda c=c: self._drop(c))

    def _drop(self, c):
        if self._conns.pop(c.cid, None) is None:
            return
        was_open = c.open
        c.open = False
        try:
            c.sock.deleteLater()
        except RuntimeError:
            pass
        if was_open:
            try:
                self.disconnected.emit(c.cid)
            except RuntimeError:  # server already destroyed (app quitting)
                pass

    def _on_read(self, c):
        c.buf += bytes(c.sock.readAll().data())
        if not c.open:
            end = c.buf.find(b"\r\n\r\n")
            if end < 0:
                if len(c.buf) > 16384:
                    c.sock.abort()
                return
            head = bytes(c.buf[:end]).decode("latin-1")
            if head.startswith(("POST /nt/", "OPTIONS /nt/")):
                self._http(c, head, end)
                return
            if head.startswith(("GET /nt/ping ", "GET /yukitube.user.js", "GET /neontube.user.js")):
                del c.buf[: end + 4]
                self._http_get(c, head.split(" ", 2)[1])
                return
            del c.buf[: end + 4]
            if not self._handshake(c, head):
                return
        self._parse_frames(c)

    # ----------------------------------------------------- HTTP transport
    def _http(self, c, head, end):
        """POST /nt/up  {tab, agent, msgs:[...]}  ->  {cmds:[...]}

        Used by the userscript through GM_xmlhttpRequest, which is not subject
        to the browser's local-network restrictions for web pages. A custom
        header is required, so ordinary web pages cannot call it (CORS preflight
        is never answered)."""
        lines = head.split("\r\n")
        hdr = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                hdr[k.strip().lower()] = v.strip()
        try:
            n = int(hdr.get("content-length", "0"))
        except ValueError:
            n = -1
        if n < 0 or n > 4 * 1024 * 1024:
            return self._http_reply(c, 400, {})
        if len(c.buf) < end + 4 + n:
            return  # wait for the rest of the body
        body = bytes(c.buf[end + 4:end + 4 + n])
        del c.buf[: end + 4 + n]
        if lines[0].startswith("OPTIONS") or hdr.get("x-neontube") != "1":
            return self._http_reply(c, 403, {})
        # POST /nt/open {arg}: YukiTube launched again while the remote runs.
        if lines[0].startswith("POST /nt/open "):
            try:
                arg = json.loads(body.decode("utf-8")).get("arg", "")
            except (ValueError, AttributeError, UnicodeDecodeError):
                return self._http_reply(c, 400, {})
            self.open_request.emit(str(arg or ""))
            return self._http_reply(c, 200, {})
        try:
            obj = json.loads(body.decode("utf-8"))
            tab = str(obj["tab"])
            msgs = obj.get("msgs") or []
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            return self._http_reply(c, 400, {})
        # Bridges from before YukiTube 0.3.1 (NeonTube's own, and the first
        # YukiTube ones) control YouTube in ways that fail in YukiTube's
        # Firefox, and would take commands meant for the current bridge.
        if not obj.get("bridge"):
            self.old_bridge.emit()
            return self._http_reply(c, 200, {"cmds": []})
        for m in msgs:
            if isinstance(m, dict):
                m["tab"] = tab
                m.setdefault("agent", obj.get("agent", "userscript"))
                self.message.emit(HTTP_CID, m)
        if not msgs:
            self.message.emit(HTTP_CID, {"type": "alive", "tab": tab, "agent": obj.get("agent", "userscript")})
        self._http_reply(c, 200, {"cmds": self._http_q.pop(tab, [])})

    def _http_get(self, c, path):
        """GET /nt/ping: lets the YukiTube launcher see the remote is up.
        GET /yukitube.user.js: the bridge userscript, for Violentmonkey to
        install (and later update) from this address. /neontube.user.js is
        where bridges installed before the rename look for updates."""
        if path.startswith(("/yukitube.user.js", "/neontube.user.js")) and self.userscript:
            data, ctype = self.userscript, "text/javascript; charset=utf-8"
        elif path == "/nt/ping":
            data, ctype = json.dumps(self.ping).encode(), "application/json"
        else:
            return self._http_reply(c, 403, {})
        c.sock.write(
            f"HTTP/1.1 200 OK\r\nContent-Type: {ctype}\r\nCache-Control: no-store\r\n"
            f"Content-Length: {len(data)}\r\nConnection: close\r\n\r\n".encode() + data)
        c.sock.disconnectFromHost()

    def _http_reply(self, c, code, obj):
        data = json.dumps(obj).encode()
        reason = {200: "OK", 400: "Bad Request", 403: "Forbidden"}.get(code, "OK")
        c.sock.write(
            f"HTTP/1.1 {code} {reason}\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(data)}\r\nConnection: close\r\n\r\n".encode() + data)
        c.sock.disconnectFromHost()

    def _handshake(self, c, head):
        lines = head.split("\r\n")
        hdr = {}
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                hdr[k.strip().lower()] = v.strip()
        key = hdr.get("sec-websocket-key")
        origin = hdr.get("origin", "")
        if not lines[0].startswith("GET ") or not key or "websocket" not in hdr.get("upgrade", "").lower():
            c.sock.write(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
            c.sock.disconnectFromHost()
            return False
        if origin and not origin.startswith(_ALLOWED_PREFIXES):
            c.sock.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
            c.sock.disconnectFromHost()
            return False
        accept = base64.b64encode(hashlib.sha1(key.encode() + _GUID).digest()).decode()
        c.sock.write(
            (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode()
        )
        c.open = True
        self.connected.emit(c.cid)
        return True

    def _parse_frames(self, c):
        buf = c.buf
        while True:
            if len(buf) < 2:
                return
            b0, b1 = buf[0], buf[1]
            fin = b0 & 0x80
            op = b0 & 0x0F
            masked = b1 & 0x80
            ln = b1 & 0x7F
            pos = 2
            if ln == 126:
                if len(buf) < 4:
                    return
                ln = struct.unpack(">H", buf[2:4])[0]
                pos = 4
            elif ln == 127:
                if len(buf) < 10:
                    return
                ln = struct.unpack(">Q", buf[2:10])[0]
                pos = 10
            if ln > 8 * 1024 * 1024:
                c.sock.abort()
                return
            mask = b""
            if masked:
                if len(buf) < pos + 4:
                    return
                mask = bytes(buf[pos:pos + 4])
                pos += 4
            if len(buf) < pos + ln:
                return
            payload = bytearray(buf[pos:pos + ln])
            del buf[: pos + ln]
            if masked:
                for i in range(ln):
                    payload[i] ^= mask[i & 3]

            if op == 0x8:  # close
                self._send_raw(c, 0x8, bytes(payload[:2]))
                c.sock.disconnectFromHost()
                return
            if op == 0x9:  # ping
                self._send_raw(c, 0xA, bytes(payload))
                continue
            if op == 0xA:  # pong
                continue
            if op in (0x1, 0x2):
                c.frag = payload
                c.frag_op = op
            elif op == 0x0:
                c.frag += payload
            else:
                continue
            if fin and c.frag_op == 0x1:
                data, c.frag = bytes(c.frag), bytearray()
                try:
                    obj = json.loads(data.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    continue
                if isinstance(obj, dict):
                    self.message.emit(c.cid, obj)

    def _send_raw(self, c, op, payload):
        n = len(payload)
        if n < 126:
            head = struct.pack(">BB", 0x80 | op, n)
        elif n < 65536:
            head = struct.pack(">BBH", 0x80 | op, 126, n)
        else:
            head = struct.pack(">BBQ", 0x80 | op, 127, n)
        c.sock.write(head + payload)

    # ------------------------------------------------------------- public
    def send(self, cid, obj):
        if cid == HTTP_CID:
            q = self._http_q.setdefault(str(obj.get("tab")), [])
            q.append(obj)
            del q[:-30]
            return True
        c = self._conns.get(cid)
        if not c or not c.open:
            return False
        self._send_raw(c, 0x1, json.dumps(obj, separators=(",", ":")).encode())
        return True

    def broadcast(self, obj):
        for cid in list(self._conns):
            self.send(cid, obj)

    def connection_ids(self):
        return [cid for cid, c in self._conns.items() if c.open]
