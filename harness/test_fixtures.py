"""Second local page, L3 blocking, and a three-task batch."""

from __future__ import annotations

import asyncio
import csv
import json
import unittest
from pathlib import Path

from harness.batch import run_configs
from harness.config import load_config
from harness.serve_local import LocalServer
from harness.summary import aggregate, write_csv

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "configs" / "fixtures" / "local-web-fixture.json"
L3 = ROOT / "configs" / "fixtures" / "arg-l3-fixture.json"
SET = [
    "configs/fixtures/static-fixture.json",
    "configs/fixtures/local-web-fixture.json",
    "configs/fixtures/arg-l2-fixture.json",
]


class FixtureTests(unittest.TestCase):
    def test_l3_blocks_other_hosts_and_guides(self) -> None:
        asyncio.run(_l3_block())

    def test_three_tasks_aggregate_without_mixing_layers(self) -> None:
        failed = asyncio.run(run_configs(SET, policy="script", obs_mode=None, headless=True, repo_root=ROOT))
        self.assertEqual(failed, 0)
        steps = (_latest(ROOT / "runs" / "local-web-fixture" / "B") / "steps.jsonl").read_text(encoding="utf-8")
        self.assertIn('"op": "click"', steps)
        self.assertIn('"result": "ok"', steps)
        l2 = json.loads((_latest(ROOT / "runs" / "arg-l2-fixture" / "B") / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(l2["arg_layer"], "L2")
        rows = aggregate(ROOT / "runs")
        self.assertIn(("arg", "L2"), {(row["category"], row["arg_layer"]) for row in rows})
        self.assertTrue(all(row["arg_layer"] != "ALL" for row in rows))
        out = ROOT / "runs" / "fixture-aggregate.csv"
        write_csv(rows, out)
        with out.open(encoding="utf-8-sig", newline="") as handle:
            header = csv.DictReader(handle).fieldnames
        self.assertEqual(
            list(header or []),
            [
                "category",
                "arg_layer",
                "obs_mode",
                "model",
                "runs",
                "checkpoints_reached",
                "checkpoints_total",
                "endings",
                "steps",
                "tokens_total",
            ],
        )


async def _l3_block() -> None:
    cfg = load_config(L3)
    server = LocalServer()
    server.start(cfg, ROOT)
    from harness.browser_harness import BrowserHarness

    harness = BrowserHarness(cfg, ROOT / "runs" / "_l3", headless=True)
    try:
        await harness.start()
        await harness.reset()
        await harness.page.evaluate(
            """() => Promise.all([
              fetch('https://example.com/').catch(() => null),
              fetch('https://walkthrough.example/guide').catch(() => null)
            ])"""
        )
        blocked = harness.blocked
        hosts = {item.get("host") for item in blocked}
        if "example.com" not in hosts:
            raise AssertionError(f"非白名单没有被拦截：{blocked}")
        if not any(item.get("why") == "guide" for item in blocked):
            raise AssertionError(f"攻略站没有被拦截：{blocked}")
        if any(item.get("host") == "127.0.0.1:8767" for item in blocked):
            raise AssertionError(f"白名单页面被拦截：{blocked}")
    finally:
        await harness.close()
        server.stop()


def _latest(root: Path) -> Path:
    return max((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime)


if __name__ == "__main__":
    unittest.main()
