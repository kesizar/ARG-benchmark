"""Async Playwright session. One fresh context per episode."""

from __future__ import annotations

import asyncio
import os
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
        self._strict_generation = 0
        self._strict_transitioning = False
        self._dialog_ready = asyncio.Event()
        self._action_tasks: set[asyncio.Task] = set()
        self._deferred_actions: set[asyncio.Task] = set()
        self._deferred_results: list[str] = []
        self._last_observation: dict[str, Any] = {}
        self._bound_pages: set = set()
        self.step = 0
        self.shot_index = 0
        self.last_screenshot = ""
        self.settle_ms = int(cfg.get("settle_ms") or 0)
        self.judge_init_script = ""

    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()
        last_error: Exception | None = None
        channel = os.environ.get("BENCHMARK_BROWSER_CHANNEL", "auto")
        if channel not in {"auto", "chromium", "msedge", "chrome"}:
            raise ValueError("BENCHMARK_BROWSER_CHANNEL must be auto/chromium/msedge/chrome")
        choices = ({"channel": "msedge"}, {"channel": "chrome"}, {}) if channel == "auto" else (
            {} if channel == "chromium" else {"channel": channel},
        )
        for kwargs in choices:
            try:
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless, args=self.cfg.get("browser_launch_args") or [], **kwargs)
                return
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.browser = None
        raise RuntimeError(f"没有可用的浏览器: {last_error}")

    async def close(self) -> None:
        self._strict_generation += 1
        self._strict_transitioning = True
        await self._cancel_actions()
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
        self._strict_generation += 1
        self._strict_transitioning = True
        await self._cancel_actions()
        self.pending = None
        self._dialog_ready.clear()
        self._last_observation = {}
        self.elements = []
        self._bound_pages.clear()
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
        await self.context.add_init_script(INPUT_WATCH_JS)
        if self.judge_init_script:
            await self.context.add_init_script(self.judge_init_script)
        await self.context.route("**/*", self._route)
        self.context.on("page", self._on_page)
        self.page = await self.context.new_page()
        self._bind_page(self.page)
        entry = self.cfg.get("entry_url")
        if entry:
            await self.page.goto(entry, wait_until="domcontentloaded", timeout=45000)
            await self._settle()
        self._strict_transitioning = False

    async def _screenshot(self, path) -> None:
        from playwright.async_api import TimeoutError as PlaywrightTimeout

        last: Exception | None = None
        for _ in range(3):
            try:
                await self.page.screenshot(
                    path=str(path),
                    full_page=False,
                    animations="disabled",
                    timeout=20000,
                )
                return
            except PlaywrightTimeout as exc:
                last = exc
        assert last is not None
        raise last

    async def observe(self, label: str | None = None) -> dict[str, Any]:
        assert self.page is not None
        if self.pending:
            # JavaScript and screenshot requests may block behind a native
            # dialog. Reuse the last game image and report the live dialog.
            raw = dict(self._last_observation)
            raw.update({"url": self.page.url if self.cfg.get("show_url", True) else "",
                        "visible_text": raw.get("visible_text", ""), "elements": [],
                        "tabs": raw.get("tabs", []), "dialogs": list(self.step_dialogs),
                        "pending_dialog": self._pending_view()})
            self.elements = []
            return raw
        self.shot_index += 1
        name = label or f"step_{self.shot_index:03d}.png"
        path = self.run_dir / name
        await self._screenshot(path)
        self.last_screenshot = name
        text = ""
        elements: list[dict] = []
        if self.cfg.get("obs_text") or self.cfg.get("obs_elements"):
            if self.cfg.get("obs_text"):
                text = await self._evaluate(
                    self.page,
                    TEXT_JS,
                    {"limit": int(self.cfg.get("text_limit") or 6000), "scope": self.cfg.get("text_scope") or "page"},
                )
            if self.cfg.get("obs_elements"):
                elements = await self._evaluate(self.page, ELEMENTS_JS)
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
        self._last_observation = dict(raw)
        return raw

    async def act(self, action: dict[str, Any]) -> str:
        from playwright.async_api import Error

        if self.pending and action.get("op") not in {"dialog", "wait"}:
            return "请先用 dialog 动作处理待回应的对话框"

        async def execute():
            try:
                return await self._dispatch(action)
            except (Error, TypeError, ValueError, KeyError) as exc:
                detail = str(exc).splitlines()[0].strip()
                return f"无法执行：{detail[:180]}"

        self._dialog_ready.clear()
        task = asyncio.create_task(execute())
        self._action_tasks.add(task)
        task.add_done_callback(self._action_finished)
        waiter = asyncio.create_task(self._dialog_ready.wait())
        try:
            done, _ = await asyncio.wait({task, waiter}, return_when=asyncio.FIRST_COMPLETED)
            if task in done:
                result = await task
            else:
                # Keep the triggering click alive until the player's next
                # dialog action accepts/dismisses the native dialog.
                self._deferred_actions.add(task)
                result = "ok"
            if self._deferred_results:
                result += "；先前动作：" + "；".join(self._deferred_results)
                self._deferred_results.clear()
            return result
        finally:
            waiter.cancel()
            await asyncio.gather(waiter, return_exceptions=True)

    def _action_finished(self, task) -> None:
        self._action_tasks.discard(task)
        deferred = task in self._deferred_actions
        self._deferred_actions.discard(task)
        if task.cancelled():
            return
        try:
            result = task.result()
        except Exception as exc:
            result = f"无法执行：{str(exc)[:180]}"
        if deferred and result != "ok":
            self._deferred_results.append(result)

    async def _cancel_actions(self) -> None:
        tasks = list(self._action_tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._action_tasks.clear()
        self._deferred_actions.clear()
        self._deferred_results.clear()

    async def input_hashes(self, selector: str | None = None) -> set[str]:
        from harness.judge import answer_sha256

        found: set[str] = set()
        if not self.context:
            return found
        for page in self.context.pages:
            for frame in page.frames:
                await self._evaluate(frame, INPUT_WATCH_JS)
                values = await self._evaluate(frame, INPUT_READ_JS, selector or "")
                if not isinstance(values, list):
                    continue
                for value in values:
                    if isinstance(value, str) and value.strip():
                        found.add(answer_sha256(value))
        return found

    async def page_expr(self, expr: str) -> bool:
        if not self.context or not expr:
            return False
        for page in self.context.pages:
            for frame in page.frames:
                if await self._evaluate(frame, PAGE_EXPR_JS, expr):
                    return True
        return False

    async def strict_page_expr(self, expr: str) -> bool:
        """Private judge read: unavailable state is an error, never a false score."""
        page, context = self.page, self.context
        generation = self._strict_generation
        if self.pending or context is None or page is None or not expr or self._strict_transitioning:
            raise RuntimeError("strict judge page unavailable")
        try:
            value = await asyncio.wait_for(page.evaluate("(expr) => eval(expr)", expr), 15)
        except Exception as exc:
            raise RuntimeError("strict judge evaluation unavailable") from exc
        if (self.pending or self.page is not page or self.context is not context
                or self._strict_generation != generation or self._strict_transitioning):
            raise RuntimeError("strict judge page changed during evaluation")
        if type(value) is not bool:
            raise RuntimeError("strict judge returned non-boolean")
        return value

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
                text = await self._evaluate(frame, "() => document.body ? document.body.innerText : ''")
                if isinstance(text, str):
                    texts.append(text)
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
                data = await self._evaluate(frame,
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
        before = len(self.blocked)
        if op in {"click", "dblclick"}:
            x, y = self._resolve_point(action)
            if op == "dblclick":
                await self.page.mouse.dblclick(x, y)
            else:
                await self.page.mouse.click(x, y)
            return await self._done(before)
        if op == "hover":
            x, y = self._resolve_point(action)
            await self.page.mouse.move(x, y)
            return await self._done(before)
        if op == "long_press":
            x, y = self._resolve_point(action)
            await self.page.mouse.move(x, y)
            await self.page.mouse.down()
            await self.page.wait_for_timeout(int(action.get("ms") or 0))
            await self.page.mouse.up()
            return await self._done(before)
        if op == "drag":
            await self.page.mouse.move(action["x1"], action["y1"])
            await self.page.mouse.down()
            await self.page.mouse.move(action["x2"], action["y2"], steps=15)
            await self.page.mouse.up()
            return await self._done(before)
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
            return await self._done(before)
        if op == "key":
            await self.page.keyboard.press(action["key"])
            return await self._done(before)
        if op == "scroll":
            if "x" in action and "y" in action:
                await self.page.mouse.move(action["x"], action["y"])
            if action.get("dir"):
                dx, dy = SCROLL[action["dir"]]
            else:
                dx, dy = float(action.get("dx") or 0), float(action.get("dy") or 0)
            await self.page.mouse.wheel(dx, dy)
            return await self._done(before)
        if op == "back":
            await self.page.go_back(wait_until="domcontentloaded", timeout=15000)
            return await self._done(before)
        if op == "goto":
            await self.page.goto(action["url"], wait_until="domcontentloaded", timeout=45000)
            return await self._done(before)
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
            return await self._done(before)
        return "动作未启用"

    async def _evaluate(self, target, script: str, arg: Any | None = None, timeout: float = 15) -> Any:
        if self.pending:
            return None
        try:
            call = target.evaluate(script) if arg is None else target.evaluate(script, arg)
            return await asyncio.wait_for(call, timeout)
        except Exception:  # noqa: BLE001
            return None

    async def _page_title(self, page) -> str:
        try:
            title = await asyncio.wait_for(page.title(), 8)
        except Exception:  # noqa: BLE001
            return ""
        return title or ""

    async def _done(self, before: int) -> str:
        await self._settle()
        return inaccessible_result(self.blocked[before:])

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
            title = await self._page_title(page)
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
        if page in self._bound_pages:
            return
        self._bound_pages.add(page)
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
        self._dialog_ready.set()

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
        if self.pending:
            return
        if self.settle_ms:
            await self.page.wait_for_timeout(self.settle_ms)
        await self._drop_blocked_pages()

    async def _drop_blocked_pages(self) -> None:
        """A refused site used to leave the player on the error tab. Close it and stay on the game."""
        if not self.context:
            return
        for page in list(self.context.pages):
            if not str(page.url or "").startswith("chrome-error:"):
                continue
            if len(self.context.pages) > 1:
                await page.close()
                continue
            try:
                await page.go_back(wait_until="domcontentloaded", timeout=15000)
            except Exception:
                pass
        open_pages = [page for page in self.context.pages if not str(page.url or "").startswith("chrome-error:")]
        if not open_pages:
            return
        if self.page not in open_pages:
            self.page = open_pages[-1]
        await self.page.bring_to_front()


def inaccessible_result(blocked: list[dict]) -> str:
    """Tell the player a document navigation was refused, after the view has returned."""
    hosts: list[str] = []
    for item in blocked:
        if item.get("type") != "document":
            continue
        host = str(item.get("host") or "")
        if host and host not in hosts:
            hosts.append(host)
    if not hosts:
        return "ok"
    return f"该页面不可访问：{'、'.join(hosts)}。已回到原页面。"


INPUT_WATCH_JS = r"""
(() => {
  if (window.__argInputWatch) return;
  window.__argInputWatch = true;
  window.__argInputLatch = [];
  const take = (el) => {
    if (!el || el.nodeType !== 1) return;
    const tag = el.tagName;
    let value = "";
    if (tag === "INPUT" || tag === "TEXTAREA") {
      const type = (el.getAttribute("type") || "text").toLowerCase();
      if (["button", "submit", "reset", "checkbox", "radio", "file", "image", "hidden"].includes(type)) return;
      value = el.value || "";
    } else if (el.isContentEditable) {
      value = el.innerText || "";
    } else {
      return;
    }
    if (!value) return;
    window.__argInputLatch.push({value, el});
    if (window.__argInputLatch.length > 200) window.__argInputLatch.shift();
  };
  document.addEventListener("input", (event) => take(event.target), true);
  document.addEventListener("change", (event) => take(event.target), true);
})();
"""

INPUT_READ_JS = r"""
(selector) => {
  const out = [];
  const ok = (el) => {
    if (!selector) return true;
    try { return !!el.matches(selector); } catch (e) { return false; }
  };
  const read = (el) => {
    if (!el || el.nodeType !== 1 || !ok(el)) return;
    const tag = el.tagName;
    let value = "";
    if (tag === "INPUT" || tag === "TEXTAREA") {
      const type = (el.getAttribute("type") || "text").toLowerCase();
      if (["button", "submit", "reset", "checkbox", "radio", "file", "image", "hidden"].includes(type)) return;
      value = el.value || "";
    } else if (el.isContentEditable) {
      value = el.innerText || "";
    }
    if (value) out.push(value);
  };
  document.querySelectorAll("input, textarea, [contenteditable='true']").forEach(read);
  (window.__argInputLatch || []).forEach((item) => {
    if (item && item.value && item.el && ok(item.el)) out.push(item.value);
  });
  return out;
}
"""

PAGE_EXPR_JS = r"""
(expr) => {
  try { return !!eval(expr); } catch (e) { return false; }
}
"""


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
