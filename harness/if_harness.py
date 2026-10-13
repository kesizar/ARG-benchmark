"""Interactive-fiction adapter. Valid-action lists are never observed."""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path


class IFHarness:
    def __init__(self, cfg: dict, run_dir: Path, env=None) -> None:
        self.cfg = cfg
        self.run_dir = run_dir
        self.env = env
        self.output = ""
        self.turn = 0
        self.score = 0
        self.victory = False
        self.game_over = False
        self.blocked: list[dict] = []

    async def start(self) -> None:
        return None

    async def close(self) -> None:
        closer = getattr(self.env, "close", None)
        if closer:
            closer()
        self.env = None

    async def reset(self) -> None:
        spec = self.cfg.get("if") or {}
        if self.env is None:
            story = _story_path(spec.get("story_file"))
            interpreter = spec.get("interpreter") or "jericho"
            if interpreter == "frotz":
                self.env = FrotzSession(
                    story,
                    binary=spec.get("frotz_bin"),
                    extra=list(spec.get("frotz_args") or []),
                )
            elif interpreter == "jericho":
                try:
                    import jericho
                except ImportError as exc:
                    raise RuntimeError("未安装 jericho。在评测虚拟环境里执行 python -m pip install jericho 后再测。") from exc
                self.env = jericho.FrotzEnv(str(story))
            else:
                raise RuntimeError(f"不支持的解释器 {interpreter}")
        observation, _info = self.env.reset()
        self.output = str(observation or "")
        self.turn = 0
        self.score = _safe(self.env, "get_score", 0)
        self.victory = bool(_safe(self.env, "victory", False))
        self.game_over = bool(_safe(self.env, "game_over", False))

    async def observe(self, label: str | None = None) -> dict:
        del label
        return {
            "url": "",
            "visible_text": self.output,
            "elements": [],
            "tabs": [],
            "dialogs": [],
            "pending_dialog": None,
            "screenshot": "",
            "turn": self.turn,
        }

    async def act(self, action: dict) -> str:
        if action.get("op") != "type":
            return "动作未启用"
        command = str(action.get("text") or "")
        limit = int((self.cfg.get("if") or {}).get("max_command_chars") or 200)
        command = command[:limit]
        if command.strip().lower() in {"save", "restore", "undo"} and not (self.cfg.get("if") or {}).get("allow_save"):
            return "该动作在本评测中禁用"
        observation, _reward, done, _info = self.env.step(command)
        self.output = str(observation or "")
        self.turn += 1
        self.score = _safe(self.env, "get_score", self.score)
        self.victory = bool(_safe(self.env, "victory", False))
        self.game_over = bool(done or _safe(self.env, "game_over", False))
        return "ok"

    async def urls(self) -> list[str]:
        return []

    async def dom_texts(self) -> list[str]:
        return [self.output]

    async def local_storage(self, frame_url_regex: str | None = None) -> dict:
        return {}

    def dialogs_step(self) -> list:
        return []

    def tab_count(self) -> int:
        return 0

    def requests(self, scope: str = "all") -> list:
        return []

    def if_status(self) -> dict:
        return {"score": self.score, "victory": self.victory, "game_over": self.game_over, "turn": self.turn}

    def consume_step(self) -> None:
        return None


class FrotzSession:
    """Line-oriented dfrotz/frotz session. The prompt is a line containing only '>'."""

    def __init__(self, story: Path, binary: str | None = None, extra: list[str] | None = None) -> None:
        program = binary or shutil.which("dfrotz") or shutil.which("frotz")
        if not program:
            raise RuntimeError("未找到 dfrotz 或 frotz。文字冒险默认用 jericho。")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        self.proc = subprocess.Popen(
            [program, *(extra or []), str(story)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()
        self.banner = self._collect(3)

    def reset(self):
        return self.banner, {}

    def step(self, command: str):
        assert self.proc.stdin is not None
        self.proc.stdin.write(command + "\n")
        self.proc.stdin.flush()
        return self._collect(3), 0, False, {}

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stdout:
            self.proc.stdout.close()

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self._lines.put(line)
        self._lines.put(None)

    def _collect(self, timeout: float) -> str:
        found: list[str] = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                item = self._lines.get(timeout=0.2)
            except queue.Empty:
                if found and found[-1].strip() == ">":
                    break
                continue
            if item is None:
                break
            found.append(item)
            if item.strip() == ">":
                break
        return "".join(found)


def _story_path(story: str | None) -> Path:
    if not story:
        raise RuntimeError("文字冒险缺少 if.story_file。把 .z5 或 .z8 路径写进配置后再测。")
    path = Path(story)
    if not path.is_file():
        path = Path.cwd() / story
    if not path.is_file():
        raise RuntimeError(f"找不到故事文件 {story}。把 .z5 或 .z8 放到该路径后即可开测。")
    return path


def _safe(env, name: str, default):
    method = getattr(env, name, None)
    if method is None:
        return default
    try:
        return method()
    except Exception:  # noqa: BLE001
        return default
