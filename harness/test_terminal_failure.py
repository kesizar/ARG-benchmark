"""A failure must stop an episode without being counted as completion."""

import tempfile
import unittest
import json
from pathlib import Path

from harness.judge import Judge
from harness.loop import _episode
from harness.policy_script import ScriptedPolicy
from harness.static_harness import StaticHarness
from harness.summary import aggregate


class FailureSurface(StaticHarness):
    async def reset(self):
        self.failed = False

    async def act(self, action):
        self.failed = True
        return "ok"

    async def dom_texts(self):
        return ["FAILED" if self.failed else "PLAYING"]


class TerminalFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_episode_stops_at_failure_without_completion(self):
        cfg = {
            "id": "failure-fixture", "category": "static", "runtime_layer": "L1",
            "obs_mode": "A", "actions_enabled": ["wait", "give_up"],
            "limits": {"max_steps": 3, "max_seconds": 30, "max_answer_submits": 1},
        }
        judge = Judge({
            "hooks": {"fail": {"type": "dom_regex", "pattern": "FAILED"}},
            "terminal_failures": [{"id": "timeout", "hook": "fail", "op": "truthy"}],
        }, "failure-fixture")
        policy = ScriptedPolicy([{"op": "wait", "ms": 1}, {"op": "wait", "ms": 1}])
        with tempfile.TemporaryDirectory() as directory:
            harness = FailureSurface(cfg, Path(directory))
            summary = await _episode(cfg, harness, judge, policy, "script", Path(directory))
        self.assertEqual(summary["ended_reason"], "failure")
        self.assertEqual(summary["steps"], 1)
        self.assertTrue(summary["failure_reached"])
        self.assertEqual(summary["failure_id"], "timeout")
        self.assertFalse(summary["ending_reached"])
        self.assertFalse(summary["good_ending"])

    async def test_failure_is_opt_in_and_not_a_false_positive(self):
        judge = Judge({"terminal_failures": [{"id": "death", "hook": "dead", "op": "truthy"}]}, "test")
        judge.values = {"dead": False}
        judge.update(1)
        self.assertFalse(judge.score()["failure_reached"])
        judge.values = {"dead": True}
        judge.update(2)
        self.assertEqual(judge.score()["failure_step"], 2)
        judge.answer_correct = True  # Simultaneous answer and failure must not count as completion.
        self.assertFalse(judge.score()["ending_reached"])
        self.assertFalse(judge.score()["good_ending"])
        legacy = Judge({}, "legacy")
        legacy.values = {"dead": True}
        legacy.update(1)
        self.assertFalse(legacy.score()["failure_reached"])

    async def test_aggregate_does_not_relabel_legacy_runs_as_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, item in enumerate([
                {"category": "static", "obs_mode": "A", "failure_reached": True},
                {"category": "static", "obs_mode": "A", "failure_reached": False},
                {"category": "static", "obs_mode": "A"},
            ]):
                target = root / "task" / "A" / str(index)
                target.mkdir(parents=True)
                (target / "summary.json").write_text(json.dumps(item), encoding="utf-8")
            row = aggregate(root)[0]
        self.assertEqual(row["runs"], 3)
        self.assertEqual(row["failure_observed_runs"], 2)
        self.assertEqual(row["failures"], 1)
        self.assertEqual(row["failure_rate"], 0.5)
