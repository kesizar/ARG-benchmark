"""Text view of a Baba Is You gym level. No window is opened."""

from __future__ import annotations

import os
import sys
from pathlib import Path


class GridHarness:
    def __init__(self, cfg: dict, run_dir: Path) -> None:
        self.cfg = cfg
        self.run_dir = run_dir
        self.env = None
        self.blocked: list = []

    async def start(self) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        grid = self.cfg.get("grid") or {}
        root = Path(grid.get("root") or "tasks/baba-is-ai/src")
        if not root.is_absolute():
            root = Path.cwd() / root
        source = str(root.resolve())
        if source not in sys.path:
            sys.path.insert(0, source)
        from baba.registration import make
        import baba.envs  # noqa: F401

        self.env = make(str(grid.get("env_id") or "env/two_room-break_stop-make_win"))
        self.env.reset(seed=int(self.cfg.get("seed") or 0))

    async def close(self) -> None:
        self.env = None

    async def reset(self) -> None:
        if self.env is not None:
            from baba.registration import make
            grid = self.cfg.get("grid") or {}
            self.env = make(str(grid.get("env_id") or "env/two_room-break_stop-make_win"))
            self.env.reset(seed=int(self.cfg.get("seed") or 0))

    async def observe(self, label: str | None = None) -> dict:
        del label
        return self._obs()

    async def act(self, action: dict) -> str:
        op = action.get("op")
        if op in {"wait", "scroll", "back"}:
            return "ok"
        if op != "key" or self.env is None:
            return "动作未启用"
        code = {"ArrowUp": 1, "ArrowRight": 2, "ArrowDown": 3, "ArrowLeft": 4}.get(str(action.get("key") or ""))
        if code is None:
            return "这个方向不能走"
        self.env.step(code)
        return "ok"

    def state(self) -> dict:
        if self.env is None:
            return {"stop_broken": False, "win_made": False, "won": False, "lost": False}
        rules = getattr(self.env._ruleset, "ruleset_dict", {}) or {}
        stop = rules.get("is_stop") or {}
        win = rules.get("is_win") or {}
        return {
            "stop_broken": not bool(stop.get("fwall") or stop.get("wall")),
            "win_made": bool(win),
            "won": bool(getattr(self.env, "is_win", False)),
            "lost": bool(getattr(self.env, "is_lose", False)),
        }

    def _obs(self) -> dict:
        return {
            "url": "",
            "visible_text": self._board(),
            "elements": [],
            "tabs": [],
            "dialogs": [],
            "pending_dialog": None,
            "screenshot": "",
        }

    def _board(self) -> str:
        if self.env is None:
            return ""
        lines = ["当前规则：" + self._rule_line()]
        for y in range(self.env.height):
            row = []
            for x in range(self.env.width):
                cells = [item for item in (self.env.grid.get(x, y, "all") or []) if item is not None]
                names = [getattr(item, "name", None) or item.type for item in cells]
                row.append("+".join(names) if names else ".")
            lines.append(" ".join(row))
        status = self.state()
        if status["won"]:
            lines.append("你赢了。")
        elif status["lost"]:
            lines.append("这一步失败了。可以继续改规则。")
        return "\n".join(lines)

    def _rule_line(self) -> str:
        rules = getattr(self.env._ruleset, "ruleset_dict", {}) or {}
        parts = []
        for item in rules.get("_rule_") or []:
            if isinstance(item, dict):
                parts.append(f"{item.get('object')} is {item.get('property')}")
        return "；".join(parts)

    async def urls(self) -> list[str]:
        return []

    async def dom_texts(self) -> list[str]:
        return [self._board()]

    async def local_storage(self, frame_url_regex: str | None = None) -> dict:
        del frame_url_regex
        return {}

    def dialogs_step(self) -> list:
        return []

    def tab_count(self) -> int:
        return 0

    def requests(self, scope: str = "all") -> list:
        del scope
        return []

    def if_status(self) -> dict:
        return {}

    def consume_step(self) -> None:
        return None
