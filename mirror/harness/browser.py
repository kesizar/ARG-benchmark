"""Browser session for the local exhibition. External sites are refused."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import Browser, Error, Page, Playwright, sync_playwright

HOME = "http://127.0.0.1:8766"


class GameBrowser:
    def __init__(self, runs: Path, headless: bool = True) -> None:
        self.runs = runs
        self.headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self.page: Page | None = None
        self.step = 0

    def start(self) -> None:
        self.runs.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        last_error: Exception | None = None
        for kwargs in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
            try:
                self._browser = self._playwright.chromium.launch(headless=self.headless, **kwargs)
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self._browser = None
        if self._browser is None:
            raise RuntimeError(f"没有可用的浏览器: {last_error}")
        context = self._browser.new_context(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        self.page = context.new_page()
        self.page.on("popup", self._adopt)

    def close(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _adopt(self, page: Page) -> None:
        if not self._allowed(page.url or HOME):
            page.close()
            return
        self.page = page
        page.on("popup", self._adopt)

    def _allowed(self, url: str) -> bool:
        if url in {"about:blank", ""}:
            return True
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and parsed.netloc == "127.0.0.1:8766"

    def goto(self, url: str) -> str:
        assert self.page is not None
        target = url if url.startswith("http") else HOME + (url if url.startswith("/") else "/" + url)
        if not self._allowed(target):
            return "已拒绝打开站外地址"
        self.page.goto(target, wait_until="domcontentloaded")
        self.page.wait_for_timeout(300)
        return self.page.url

    def back(self) -> str:
        assert self.page is not None
        self.page.go_back(wait_until="domcontentloaded")
        return self.page.url

    def observe(self) -> dict[str, Any]:
        assert self.page is not None
        self.page.wait_for_timeout(200)
        payload = self.page.evaluate(
            """() => {
              document.querySelectorAll("[data-harness-id],[data-harness-tile]").forEach((node) => {
                node.removeAttribute("data-harness-id");
                node.removeAttribute("data-harness-tile");
              });
              const visible = (node) => {
                const rect = node.getBoundingClientRect();
                const style = getComputedStyle(node);
                return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
              };
              const controls = [];
              let index = 1;
              for (const node of document.querySelectorAll("a, button, input, textarea, select")) {
                if (!visible(node) || index > 60) continue;
                const id = "c" + index++;
                node.setAttribute("data-harness-id", id);
                controls.push({
                  id,
                  tag: node.tagName.toLowerCase(),
                  text: (node.innerText || node.getAttribute("aria-label") || node.getAttribute("placeholder") || node.value || "").trim().slice(0, 80),
                  type: node.getAttribute("type") || "",
                  href: node.getAttribute("href") || ""
                });
              }
              const tiles = [];
              let tileIndex = 0;
              for (const tile of document.querySelectorAll(".breadcrumb-tile")) {
                const id = "t" + tileIndex++;
                tile.setAttribute("data-harness-tile", id);
                const image = tile.querySelector("img");
                tiles.push({
                  id,
                  alt: image ? image.alt : "",
                  x: Number(image && image.dataset.x || 0),
                  y: Number(image && image.dataset.y || 0),
                  scale: Number(image && image.dataset.scale || 1),
                  rotate: Number(image && image.dataset.rotate || 0)
                });
              }
              return {
                url: location.href,
                title: document.title,
                text: (document.body.innerText || "").replace(/\\s+/g, " ").trim().slice(0, 3500),
                controls,
                tiles
              };
            }"""
        )
        self.step += 1
        shot = self.runs / f"step-{self.step:03d}.png"
        self.page.screenshot(path=str(shot), full_page=False)
        payload["screenshot"] = str(shot)
        return payload

    def click(self, control_id: str) -> str:
        assert self.page is not None
        locator = self.page.locator(f'[data-harness-id="{control_id}"]')
        if locator.count() == 0:
            return f"没有控件 {control_id}"
        locator.click()
        self.page.wait_for_timeout(300)
        return self.page.url

    def type_text(self, control_id: str, text: str, submit: bool = False) -> str:
        assert self.page is not None
        locator = self.page.locator(f'[data-harness-id="{control_id}"]')
        if locator.count() == 0:
            return f"没有输入框 {control_id}"
        locator.fill(text)
        if submit:
            locator.press("Enter")
            self.page.wait_for_timeout(300)
        return "已输入"

    def drag(self, tile_id: str, mode: str, dx: float, dy: float) -> str:
        assert self.page is not None
        if mode not in {"move", "zoom", "rotate"}:
            return "mode 只能是 move、zoom 或 rotate"
        if mode == "move":
            selector = f'[data-harness-tile="{tile_id}"] img'
        else:
            action = "zoom" if mode == "zoom" else "rotate"
            selector = f'[data-harness-tile="{tile_id}"] [data-action="{action}"]'
        locator = self.page.locator(selector)
        if locator.count() == 0:
            return f"没有拼图块 {tile_id}"
        box = locator.bounding_box()
        if not box:
            return "拼图块不在画面里"
        start_x = box["x"] + box["width"] / 2
        start_y = box["y"] + box["height"] / 2
        self.page.mouse.move(start_x, start_y)
        self.page.mouse.down()
        self.page.mouse.move(start_x + dx, start_y + dy, steps=20)
        self.page.mouse.up()
        return f"已拖动 {tile_id} {mode}"

    def scroll(self, dy: float) -> str:
        assert self.page is not None
        self.page.mouse.wheel(0, dy)
        return "已滚动"

    def act(self, action: dict[str, Any]) -> str:
        try:
            return self._dispatch(action)
        except (Error, TypeError, ValueError) as exc:
            detail = str(exc).splitlines()[0].strip()
            return f"无法执行：{detail[:300]}"

    def _dispatch(self, action: dict[str, Any]) -> str:
        tool = action.get("tool")
        if tool == "click":
            return self.click(str(action.get("control_id") or ""))
        if tool == "type":
            return self.type_text(
                str(action.get("control_id") or ""),
                str(action.get("text") or ""),
                bool(action.get("submit")),
            )
        if tool == "drag":
            return self.drag(
                str(action.get("tile_id") or ""),
                str(action.get("mode") or "move"),
                float(action.get("dx") or 0),
                float(action.get("dy") or 0),
            )
        if tool == "scroll":
            return self.scroll(float(action.get("dy") or 400))
        if tool == "back":
            return self.back()
        if tool == "goto":
            return self.goto(str(action.get("url") or "/live/index.html"))
        if tool == "done":
            return str(action.get("note") or "结束")
        return "未知动作"
