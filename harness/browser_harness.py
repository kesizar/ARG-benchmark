"""Async Playwright session. One fresh context per episode."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from harness.network import block_reason
from harness.observe import ELEMENTS_JS, TEXT_JS, model_view

SCROLL = {"down": (0, 480), "up": (0, -480), "left": (-480, 0), "right": (480, 0)}


class BrowserHarness:
    def __init__(self, cfg: dict, run_dir: Path, headless: bool = True) -> None:
        self.cfg = cfg
        self.run_dir = run_dir
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.elements: list[dict] = []
        self.blocked: list[dict] = []
        self.all_requests: list[dict] = []
        self.step_requests: list[dict] = []
        self.step_dialogs: list[dict] = []
        self.pending = None
        self.step = 0
        self.shot_index = 0
        self.last_screenshot = ""
        self.settle_ms = int(cfg.get("settle_ms") or 0)

    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()
        last_error: Exception | None = None
        for kwargs in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
            try:
                self.browser = await self.playwright.chromium.launch(headless=self.headless, **kwargs)
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.browser = None
        raise RuntimeError(f"没有可用的浏览器: {last_error}")

    async def close(self) -> None:
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    async def reset(self) -> None:
        if self.context:
            await self.context.close()
        viewport = self.cfg.get("viewport") or {"width": 1366, "height": 900}
        options = dict(
            viewport={"width": int(viewport["width"]), "height": int(viewport["height"])},
            locale=self.cfg.get("locale") or "zh-CN",
            timezone_id=self.cfg.get("timezone") or "Asia/Shanghai",
            device_scale_factor=1,
            accept_downloads=False,
            service_workers="block",
        )
        try:
            self.context = await self.browser.new_context(**options)
        except TypeError:
            options.pop("service_workers", None)
            self.context = await self.browser.new_context(**options)
        await self.context.add_init_script(_seed_script(int(self.cfg.get("seed") or 1)))
        await self.context.route("**/*", self._route)
        self.context.on("page", self._on_page)
        self.page = await self.context.new_page()
        self._bind_page(self.page)
        entry = self.cfg.get("entry_url")
        if entry:
            await self.page.goto(entry, wait_until="domcontentloaded", timeout=45000)
            await self._settle()

    async def observe(self, label: str | None = None) -> dict[str, Any]:
        assert self.page is not None
        self.shot_index += 1
        name = label or f"step_{self.shot_index:03d}.png"
        path = self.run_dir / name
        await self.page.screenshot(path=str(path), full_page=False)
        self.last_screenshot = name
        text = ""
        elements: list[dict] = []
        if self.cfg.get("obs_text") or self.cfg.get("obs_elements"):
            if self.cfg.get("obs_text"):
                text = await self.page.evaluate(
                    TEXT_JS,
                    {"limit": int(self.cfg.get("text_limit") or 6000), "scope": self.cfg.get("text_scope") or "page"},
                )
            if self.cfg.get("obs_elements"):
                elements = await self.page.evaluate(ELEMENTS_JS)
        self.elements = elements or []
        raw = {
            "url": self.page.url if self.cfg.get("show_url", True) else "",
            "visible_text": text or "",
            "elements": self.elements,
            "tabs": await self._tabs(),
            "dialogs": list(self.step_dialogs),
            "pending_dialog": self._pending_view(),
            "screenshot": str(path),
        }
        return raw

    async def act(self, action: dict[str, Any]) -> str:
        from playwright.async_api import Error

        try:
            return await self._dispatch(action)
        except (Error, TypeError, ValueError, KeyError) as exc:
            detail = str(exc).splitlines()[0].strip()
            return f"无法执行：{detail[:180]}"

    async def urls(self) -> list[str]:
        if not self.context:
            return []
        return [page.url for page in self.context.pages]

    async def dom_texts(self) -> list[str]:
        texts = []
        if not self.context:
            return texts
        for page in self.context.pages:
            for frame in page.frames:
                try:
                    texts.append(await frame.evaluate("() => document.body ? document.body.innerText : ''"))
                except Exception:  # noqa: BLE001
                    continue
        return texts

    async def local_storage(self, frame_url_regex: str | None = None) -> dict[str, str]:
        import re

        pattern = re.compile(frame_url_regex) if frame_url_regex else None
        merged: dict[str, str] = {}
        if not self.page:
            return merged
        for frame in self.page.frames:
            if pattern and not pattern.search(frame.url or ""):
                continue
            try:
                data = await frame.evaluate(
                    """() => {
                      const out = {};
                      for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        out[key] = localStorage.getItem(key);
                      }
                      return out;
                    }"""
                )
            except Exception:  # noqa: BLE001
                continue
            merged.update(data or {})
        return merged

    def dialogs_step(self) -> list[dict]:
        return list(self.step_dialogs)

    def tab_count(self) -> int:
        return len(self.context.pages) if self.context else 0

    def requests(self, scope: str = "all") -> list[dict]:
        return self.step_requests if scope == "step" else self.all_requests

    def if_status(self) -> dict:
        return {}

    def consume_step(self) -> None:
        self.step_requests = []
        self.step_dialogs = []

    async def _dispatch(self, action: dict[str, Any]) -> str:
        op = action["op"]
        if op in {"click", "dblclick"}:
            x, y = self._resolve_point(action)
            if op == "dblclick":
                await self.page.mouse.dblclick(x, y)
            else:
                await self.page.mouse.click(x, y)
            await self._settle()
            return "ok"
        if op == "hover":
            x, y = self._resolve_point(action)
            await self.page.mouse.move(x, y)
            await self._settle()
            return "ok"
        if op == "long_press":
            x, y = self._resolve_point(action)
            await self.page.mouse.move(x, y)
            await self.page.mouse.down()
            await self.page.wait_for_timeout(int(action.get("ms") or 0))
            await self.page.mouse.up()
            await self._settle()
            return "ok"
        if op == "drag":
            await self.page.mouse.move(action["x1"], action["y1"])
            await self.page.mouse.down()
            await self.page.mouse.move(action["x2"], action["y2"], steps=15)
            await self.page.mouse.up()
            await self._settle()
            return "ok"
        if op == "type":
            if "n" in action:
                x, y = self._resolve_point(action)
                await self.page.mouse.click(x, y)
            if action.get("clear") and "n" in action:
                x, y = self._resolve_point(action)
                await self.page.mouse.click(x, y, click_count=3)
                await self.page.keyboard.press("Backspace")
            await self.page.keyboard.type(action.get("text") or "")
            if action.get("enter"):
                await self.page.keyboard.press("Enter")
            await self._settle()
            return "ok"
        if op == "key":
            await self.page.keyboard.press(action["key"])
            await self._settle()
            return "ok"
        if op == "scroll":
            if "x" in action and "y" in action:
                await self.page.mouse.move(action["x"], action["y"])
            if action.get("dir"):
                dx, dy = SCROLL[action["dir"]]
            else:
                dx, dy = float(action.get("dx") or 0), float(action.get("dy") or 0)
            await self.page.mouse.wheel(dx, dy)
            await self._settle()
            return "ok"
        if op == "back":
            await self.page.go_back(wait_until="domcontentloaded", timeout=15000)
            await self._settle()
            return "ok"
        if op == "goto":
            await self.page.goto(action["url"], wait_until="domcontentloaded", timeout=45000)
            await self._settle()
            return "ok"
        if op == "wait":
            await self.page.wait_for_timeout(int(action.get("ms") or 0))
            return "ok"
        if op == "switch_tab":
            pages = self.context.pages
            page = pages[int(action["i"])]
            await page.bring_to_front()
            self.page = page
            return "ok"
        if op == "close_tab":
            pages = self.context.pages
            await pages[int(action["i"])].close()
            if self.context.pages:
                self.page = self.context.pages[-1]
            return "ok"
        if op == "dialog":
            if not self.pending:
                return "没有待处理对话框"
            dialog = self.pending
            self.pending = None
            if action.get("accept", True):
                await dialog.accept(action.get("text") or "")
            else:
                await dialog.dismiss()
            await self._settle()
            return "ok"
        return "动作未启用"

    def _resolve_point(self, action: dict[str, Any]) -> tuple[float, float]:
        if "n" in action:
            number = int(action["n"])
            for item in self.elements:
                if int(item["n"]) == number:
                    return float(item["x"]), float(item["y"])
            raise ValueError(f"没有元素 {number}")
        return float(action["x"]), float(action["y"])

    async def _tabs(self) -> list[dict]:
        if not self.context:
            return []
        hide_url = (not self.cfg.get("show_url", True)) or self.cfg.get("obs_mode") == "C"
        tabs = []
        for index, page in enumerate(self.context.pages):
            try:
                title = await page.title()
            except Exception:  # noqa: BLE001
                title = ""
            item = {"i": index, "title": title, "active": page == self.page}
            if not hide_url:
                item["url"] = page.url
            tabs.append(item)
        return tabs

    def _pending_view(self) -> dict | None:
        if not self.pending:
            return None
        return {"type": self.pending.type, "message": self.pending.message}

    def _bind_page(self, page) -> None:
        page.on("dialog", self._on_dialog)

    def _on_page(self, page) -> None:
        self._bind_page(page)
        self.page = page

    async def _on_dialog(self, dialog) -> None:
        self.step_dialogs.append({"type": dialog.type, "message": dialog.message})
        if dialog.type == "alert":
            await dialog.accept()
            return
        self.pending = dialog

    async def _route(self, route) -> None:
        request = route.request
        row = {"url": request.url, "resource_type": request.resource_type}
        self.all_requests.append(row)
        self.step_requests.append(row)
        reason = block_reason(request.url, self.cfg)
        if reason:
            why, rule = reason
            self.blocked.append(
                {
                    "step": self.step,
                    "why": why,
                    "host": urlparse(request.url).netloc,
                    "rule": rule,
                    "type": request.resource_type,
                }
            )
            await route.abort("blockedbyclient")
            return
        await route.continue_()

    async def _settle(self) -> None:
        if self.settle_ms:
            await self.page.wait_for_timeout(self.settle_ms)


def _seed_script(seed: int) -> str:
    return f"""
(() => {{
  let state = {seed} >>> 0;
  Math.random = function() {{
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  }};
}})();
"""


def pack_observation(raw: dict, cfg: dict, *, last_result: str, budget: dict, notebook: str = "") -> dict:
    raw = dict(raw)
    raw["last_result"] = last_result
    raw["budget"] = budget
    raw["notebook"] = notebook
    return model_view(raw, cfg)
