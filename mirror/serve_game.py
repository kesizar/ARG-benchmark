"""Serve the local exhibition. The netdisk folder asks for an extraction code first."""

from __future__ import annotations

import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent / "involuntary-appetite"
CODE_DIGEST = "ed73aa5fbb8f0e9f11bd3d931b066c008c9e92d21531b9de73f5f75b1ac91608"
COOKIE = f"netdisk={CODE_DIGEST}"
HOST = "127.0.0.1"
PORT = 8766


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _authed(self) -> bool:
        return COOKIE in (self.headers.get("Cookie") or "")

    def _netdisk_locked(self) -> bool:
        path = urlparse(self.path).path
        return path.startswith("/step2/netdisk") and not self._authed()

    def _redirect(self, location: str, cookie: str | None = None) -> None:
        self.send_response(302)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Location", location)
        self.end_headers()

    def do_HEAD(self) -> None:  # noqa: N802
        if self._netdisk_locked():
            self._redirect("/live/netdisk.html")
            return
        super().do_HEAD()

    def do_GET(self) -> None:  # noqa: N802
        if self._netdisk_locked():
            self._redirect("/live/netdisk.html")
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/live/netdisk-unlock":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        code = parse_qs(body).get("code", [""])[0].strip()
        digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
        if digest == CODE_DIGEST:
            self._redirect("/step2/netdisk/", f"{COOKIE}; Path=/; HttpOnly")
            return
        self._redirect("/live/netdisk.html?error=1")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"http://{HOST}:{PORT}/live/index.html", flush=True)
    server.serve_forever()
