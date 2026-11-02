"""One scripted browser episode of the local exhibition, plus a blocked off-site request."""

from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from harness.config import load_config
from harness.loop import run
from harness.observe import ELEMENTS_JS
from harness.serve_local import LocalServer

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "involuntary-appetite.json"


class EpisodeTests(unittest.TestCase):
    def test_scripted_episode_and_whitelist(self) -> None:
        summary = asyncio.run(run(CONFIG, policy="script", obs_mode="B", repo_root=ROOT))
        self.assertEqual(summary["ended_reason"], "give_up")
        self.assertGreaterEqual(summary["steps"], 3)
        self.assertEqual(summary["checkpoints_reached"], 0)
        self.assertIn("entered_live", summary["events"])
        run_dir = _latest(ROOT / "runs" / "involuntary-appetite" / "B")
        steps = (run_dir / "steps.jsonl").read_text(encoding="utf-8")
        prompt = (run_dir / "model_prompt.json").read_text(encoding="utf-8")
        self.assertIn('"op": "click"', steps)
        self.assertNotIn("entered_live", steps)
        self.assertNotIn("entered_live", prompt)
        self.assertTrue((run_dir / "summary.json").is_file())
        self.assertTrue(any('"result": "ok"' in line and '"op": "click"' in line for line in steps.splitlines()))
        for mode, present in (("A", True), ("C", False)):
            asyncio.run(run(CONFIG, policy="script", obs_mode=mode, repo_root=ROOT))
            last = json.loads((_latest(ROOT / "runs" / "involuntary-appetite" / mode) / "last_obs.json").read_text(encoding="utf-8"))
            self.assertEqual("visible_text" in last, present)
            self.assertEqual("elements" in last, present)
            if mode == "A":
                self.assertNotIn("screenshot", last)
        asyncio.run(_blocked_fetch())

    def test_click_targets_include_canvas_and_role_button(self) -> None:
        elements = asyncio.run(_clickable_kinds())
        kinds = {item["kind"] for item in elements}
        labels = {item["label"] for item in elements}
        self.assertIn("button", kinds)
        self.assertIn("canvas", kinds)
        self.assertIn("div", kinds)
        self.assertIn("确定", labels)
        self.assertIn("砖", labels)
        self.assertIn("块", labels)
        self.assertNotIn("藏起来", labels)


async def _clickable_kinds() -> list[dict]:
    from playwright.async_api import async_playwright

    html = """
    <div style="position:fixed;inset:0;cursor:pointer;z-index:0"></div>
    <button style="position:relative;z-index:1">确定</button>
    <div role="button" style="position:relative;z-index:1;width:48px;height:32px">砖</div>
    <canvas width="80" height="40" style="position:relative;z-index:1;background:#ccc"></canvas>
    <div style="position:relative;z-index:1;width:36px;height:36px;cursor:pointer">块</div>
    <div style="display:none"><button>藏起来</button></div>
    """
    async with async_playwright() as playwright:
        browser = None
        last_error: Exception | None = None
        for kwargs in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
            try:
                browser = await playwright.chromium.launch(headless=True, **kwargs)
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        if browser is None:
            raise RuntimeError(f"没有可用的浏览器: {last_error}")
        page = await browser.new_page(viewport={"width": 1366, "height": 900})
        try:
            await page.set_content(html)
            return await page.evaluate(ELEMENTS_JS)
        finally:
            await browser.close()


async def _blocked_fetch() -> None:
    cfg = load_config(CONFIG)
    server = LocalServer()
    server.start(cfg, ROOT)
    from harness.browser_harness import BrowserHarness

    harness = BrowserHarness(cfg, ROOT / "runs" / "_whitelist", headless=True)
    try:
        await harness.start()
        await harness.reset()
        await harness.page.evaluate("() => fetch('https://example.com/').catch(() => null)")
        hosts = {item.get("host") for item in harness.blocked}
        if "example.com" not in hosts:
            raise AssertionError(f"站外请求没有被拦截：{harness.blocked}")
    finally:
        await harness.close()
        server.stop()


def _latest(root: Path) -> Path:
    folders = [path for path in root.iterdir() if path.is_dir()]
    return max(folders, key=lambda path: path.stat().st_mtime)


if __name__ == "__main__":
    unittest.main()
