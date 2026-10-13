"""Serve one task mirror directory. Port and root come from the task config."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="托管一个任务目录")
    parser.add_argument("--root", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    directory = str(Path(args.root).resolve())

    class Handler(QuietHandler):
        def __init__(self, *handler_args, **kwargs):
            super().__init__(*handler_args, directory=directory, **kwargs)

    class Server(ThreadingHTTPServer):
        allow_reuse_address = True

    server = Server((args.host, args.port), Handler)
    print(f"http://{args.host}:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
