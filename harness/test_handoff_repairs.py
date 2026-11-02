"""Regressions for compatibility repairs, with no model calls."""
import asyncio
import hashlib
import io
import json
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from harness.browser_harness import BrowserHarness
from harness.judge import Judge
from scripts.repair_delivery_blockers import repair_config, refresh_manifests


class HandoffRepairTests(unittest.TestCase):
    def test_outer_manifest_references_updated_inner_manifest(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("PROTOCOL-OVERLAY-MANIFEST.json", json.dumps({"files": [{"path": "runtime.py", "sha256": "old"}]}))
            archive.writestr("BUNDLE-MANIFEST.json", json.dumps({"files": [{"path": "PROTOCOL-OVERLAY-MANIFEST.json", "sha256": "old"}]}))
        replacements = {"runtime.py": b"new runtime", "HANDOFF-REPAIR.json": b"{}"}
        with zipfile.ZipFile(buffer) as archive:
            refresh_manifests(archive, replacements)
        outer = json.loads(replacements["BUNDLE-MANIFEST.json"])
        self.assertEqual(outer["files"][0]["sha256"], hashlib.sha256(replacements["PROTOCOL-OVERLAY-MANIFEST.json"]).hexdigest())

    def judge(self):
        return Judge({"scoring_protocol": "target_v1", "target_success": {"hook_condition": {"hook": "goal", "op": "truthy"}},
                      "hooks": {"goal": {"type": "js_truthy", "expr": "false"}}, "routes": [], "checkpoints": [],
                      "terminal_failures": [{"id": "dead", "hook": "dead", "op": "truthy"}]}, "test")

    def test_goal_latches_without_becoming_game_ending(self):
        judge = self.judge()
        judge.values = {"goal": False}
        judge.update(0)
        self.assertFalse(judge.score()["target_success"])
        judge.values = {"goal": True}
        judge.update(1)
        score = judge.score()
        self.assertTrue(score["target_success"])
        self.assertEqual(score["route_progress"], 1)
        self.assertFalse(score["ending_reached"])
        self.assertFalse(score["good_ending"])
        judge.values = {"goal": False}
        judge.update(2)
        self.assertTrue(judge.score()["target_success"])

    def test_failure_prevents_goal_success(self):
        judge = self.judge()
        judge.values = {"goal": True, "dead": True}
        judge.update(1)
        self.assertFalse(judge.score()["target_success"])
        self.assertTrue(judge.score()["failure_reached"])

    def test_unknown_goal_hook_rejected(self):
        with self.assertRaisesRegex(ValueError, "known truthy hook"):
            Judge({"scoring_protocol": "target_v1", "target_success": {"hook_condition": {"hook": "missing", "op": "truthy"}}}, "t")

    def test_strict_read_errors_are_not_false_scores(self):
        browser = BrowserHarness({}, Path("."))
        browser.context = object()
        browser.page = SimpleNamespace(evaluate=AsyncMock(return_value=True))
        self.assertTrue(asyncio.run(browser.strict_page_expr("true")))
        browser.page.evaluate = AsyncMock(return_value="true")
        with self.assertRaisesRegex(RuntimeError, "non-boolean"):
            asyncio.run(browser.strict_page_expr("true"))
        browser.page.evaluate = AsyncMock(side_effect=RuntimeError("unavailable"))
        with self.assertRaisesRegex(RuntimeError, "evaluation unavailable"):
            asyncio.run(browser.strict_page_expr("true"))

    def test_strict_read_rejects_context_changed_during_await(self):
        browser = BrowserHarness({}, Path("."))
        browser.context = object()
        async def evaluate(*args):
            browser._strict_generation += 1
            return True
        browser.page = SimpleNamespace(evaluate=evaluate)
        with self.assertRaisesRegex(RuntimeError, "changed during"):
            asyncio.run(browser.strict_page_expr("true"))

    def test_unused_submit_cap_changes_neither_actions_nor_ui_rules(self):
        cfg = {"id": "t", "category": "web_arg", "obs_mode": "B", "actions_enabled": ["click", "type"],
               "limits": {"max_steps": 300, "max_answer_submits": 0}, "native_limit": 1}
        spec = {"id": "old", "max_answer_submits": 0}
        repair_config(cfg, spec)
        self.assertEqual(cfg["actions_enabled"], ["click", "type"])
        self.assertEqual(cfg["native_limit"], 1)
        self.assertEqual(cfg["limits"]["max_answer_submits"], 10)
        self.assertEqual(spec["max_answer_submits"], 10)
        self.assertEqual(cfg["category"], "arg")
        self.assertTrue(cfg["require_images"])
        self.assertEqual(spec["id"], "t")

    def test_enabled_submit_cap_cannot_be_generically_repaired(self):
        cfg = {"id": "t", "actions_enabled": ["submit_answer"], "limits": {"max_answer_submits": 12}}
        with self.assertRaisesRegex(ValueError, "task-specific evidence"):
            repair_config(cfg, {})


if __name__ == "__main__":
    unittest.main()
