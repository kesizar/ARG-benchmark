"""Start and stop the task's local web server."""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def url_ready(url: str, timeout: float = 2) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


class LocalServer:
    def __init__(self) -> None:
        self.proc: subprocess.Popen | None = None
        self.owned = False
        self._log = None
        self.ready_url = ""

    def start(self, cfg: dict, root: Path, log_path: Path | None = None) -> None:
        spec = cfg.get("local_serve") or {}
        if not spec.get("enabled"):
            return
        ready = spec.get("ready_url") or cfg.get("entry_url") or ""
        self.ready_url = ready
        if ready and url_ready(ready):
            return
        command = list(spec.get("command") or [])
        if not command:
            raise RuntimeError("local_serve.command 为空")
        if command[0] in {"python", "python.exe", "python3"}:
            command[0] = sys.executable
        cwd = root / spec.get("cwd", ".")
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._log = log_path.open("w", encoding="utf-8")
        self.proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=self._log or subprocess.DEVNULL,
            stderr=subprocess.STDOUT if self._log else subprocess.DEVNULL,
        )
        self.owned = True
        deadline = time.time() + float(spec.get("ready_timeout_s") or 30)
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"本地服务已退出，代码 {self.proc.returncode}")
            if ready and url_ready(ready):
                return
            time.sleep(0.3)
        self.stop()
        raise RuntimeError(f"本地服务在时限内没有就绪：{ready}")

    def stop(self) -> None:
        if self.owned and self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self._log:
            self._log.close()
            self._log = None
        ready = self.ready_url
        owned = self.owned
        self.owned = False
        self.proc = None
        if owned and ready:
            _wait_until_down(ready)


def _wait_until_down(url: str, timeout: float = 5) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not url_ready(url):
            return
        time.sleep(0.2)


def check_server(cfg: dict, root: Path) -> None:
    """Start the configured server, confirm it answers, then stop it."""
    server = LocalServer()
    server.start(cfg, root)
    ready = server.ready_url
    try:
        if not ready or not url_ready(ready):
            raise RuntimeError(f"本地服务没有就绪：{ready}")
    finally:
        server.stop()
    if ready and url_ready(ready):
        raise RuntimeError(f"停止后端口仍在应答：{ready}")
