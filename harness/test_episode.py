"""One scripted browser episode of the local exhibition, plus a blocked off-site request."""

from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from harness.config import load_config
from harness.loop import run
from harness.serve_local import LocalServer

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "involuntary-appetite.json"


class EpisodeTests(unittest.TestCase):
    def test_scripted_episode_and_whitelist(self) -> None:
        summary = asyncio.run(run(CONFIG, policy="script", obs_mode="B", repo_root=ROOT))
        self.assertEqual(summary["ended_reason"], "give_up")
        self.assertGreaterEqual(summary["steps"], 3)
        self.assertGreaterEqual(summary["checkpoints_reached"], 1)
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
