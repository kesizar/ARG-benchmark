"""Serve one task mirror directory. Port and root come from the task config."""

from __future__ import annotations

import argparse
import html
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote

_HIDDEN = {"directoryHeader.html", "htaccess.txt", "readme.txt"}


class QuietHandler(SimpleHTTPRequestHandler):
    allow_listing = False

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def list_directory(self, path):  # noqa: A003
        if not self.allow_listing:
            self.send_error(404, "No listing")
            return None
        folder = Path(path)
        try:
            entries = [item for item in folder.iterdir() if item.name not in _HIDDEN]
        except OSError:
            self.send_error(404, "No listing")
            return None
        entries.sort(key=lambda item: (not item.is_dir(), item.name.lower()))
        display = html.escape(unquote(self.path))
        rows = []
        if self.path not in ("/", ""):
            rows.append('<li><a href="../">Parent Directory</a></li>')
        for item in entries:
            suffix = "/" if item.is_dir() else ""
            href = html.escape(quote(item.name) + suffix)
            label = html.escape(item.name + suffix)
            rows.append(f'<li><a href="{href}">{label}</a></li>')
        story = ""
        header = folder / "directoryHeader.html"
        if header.is_file():
            raw = header.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"<body[^>]*>(.*)</body>", raw, flags=re.IGNORECASE | re.DOTALL)
            story = match.group(1) if match else raw
        body = (
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
            f"<title>Index of {display}</title></head><body>"
            f"<h1>Index of {display}</h1><ul>{''.join(rows)}</ul><hr>{story}"
            "</body></html>"
        )
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="托管一个任务目录")
    parser.add_argument("--root", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--listing", action="store_true")
    args = parser.parse_args()
    directory = str(Path(args.root).resolve())

    class Handler(QuietHandler):
        allow_listing = args.listing

        def __init__(self, *handler_args, **kwargs):
            super().__init__(*handler_args, directory=directory, **kwargs)

    class Server(ThreadingHTTPServer):
        allow_reuse_address = True

    server = Server((args.host, args.port), Handler)
    print(f"http://{args.host}:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
