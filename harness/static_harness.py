"""Static puzzle surface: the model sees the prompt and may submit an answer."""

from __future__ import annotations

from pathlib import Path


class StaticHarness:
    def __init__(self, cfg: dict, run_dir: Path) -> None:
        self.cfg = cfg
        self.run_dir = run_dir
        visible = cfg.get("model_visible") or {}
        static = cfg.get("static") or {}
        self.prompt = str(static.get("prompt") or visible.get("intro") or "")

    async def start(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def reset(self) -> None:
        return None

    async def observe(self, label: str | None = None) -> dict:
        del label
        return {
            "url": "",
            "visible_text": self.prompt,
            "elements": [],
            "tabs": [],
            "dialogs": [],
            "pending_dialog": None,
            "screenshot": "",
        }

    async def act(self, action: dict) -> str:
        op = action.get("op")
        if op in {"wait", "scroll", "back"}:
            return "ok"
        return "动作未启用"

    async def urls(self) -> list[str]:
        return []

    async def dom_texts(self) -> list[str]:
        return [self.prompt]

    async def local_storage(self, frame_url_regex: str | None = None) -> dict:
        return {}

    def dialogs_step(self) -> list:
        return []

    def tab_count(self) -> int:
        return 0

    def requests(self, scope: str = "all") -> list:
        return []

    def if_status(self) -> dict:
        return {}

    def consume_step(self) -> None:
        return None
