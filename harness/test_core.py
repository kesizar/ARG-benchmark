"""Core harness checks. No browser and no live model."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from harness.actions import last_json_object, normalize
from harness.config import apply_obs_mode, load_config
from harness.if_harness import IFHarness
from harness.judge import Judge, answer_sha256
from harness.loop import run
from harness.network import block_reason
from harness.observe import model_view, public_elements
from harness.prompts import model_prompt
from harness.summary import aggregate
from harness.validate import validate_file

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "configs" / "involuntary-appetite.json"


class ActionTests(unittest.TestCase):
    def test_last_object_wins(self) -> None:
        raw = '先看 {"op":"wait","ms":1} 然后 {"op":"give_up"}'
        self.assertEqual(last_json_object(raw)["op"], "give_up")

    def test_combo_and_goto_rejected(self) -> None:
        cfg = load_config(TASK)
        action, error = normalize({"op": "key", "key": "Control+u"}, cfg)
        self.assertIsNone(action)
        self.assertEqual(error, "动作格式错误")
        action, error = normalize({"op": "goto", "url": "https://example.com/walkthrough"}, cfg)
        self.assertIsNone(action)
        self.assertEqual(error, "动作未启用")

    def test_legacy_done_maps_to_give_up(self) -> None:
        cfg = load_config(TASK)
        action, error = normalize({"tool": "done", "note": "停"}, cfg)
        self.assertEqual(error, None)
        self.assertEqual(action["op"], "give_up")


class ObsTests(unittest.TestCase):
    def test_mode_table_overrides_flags(self) -> None:
        cfg = {"obs_mode": "C", "obs_text": True, "obs_elements": True, "obs_screenshot": False}
        apply_obs_mode(cfg)
        self.assertFalse(cfg["obs_text"])
        self.assertFalse(cfg["obs_elements"])
        self.assertTrue(cfg["obs_screenshot"])

    def test_mode_c_view_has_no_text_or_elements(self) -> None:
        cfg = load_config(TASK, obs_mode="C")
        view = model_view(
            {"visible_text": "秘密", "elements": [{"n": 0, "kind": "a", "label": "A", "x": 1, "y": 2, "href": "nope"}], "url": "http://x", "screenshot": "a.png", "tabs": [], "dialogs": [], "pending_dialog": None},
            cfg,
        )
        self.assertNotIn("visible_text", view)
        self.assertNotIn("elements", view)
        self.assertIn("screenshot", view)

    def test_elements_drop_private_fields(self) -> None:
        cleaned = public_elements([{"n": 0, "kind": "a", "label": "A", "x": 1, "y": 2, "href": "secret", "id": "x"}])
        self.assertEqual(set(cleaned[0]), {"n", "kind", "label", "x", "y"})


class NetworkTests(unittest.TestCase):
    def test_allow_shortcut_and_guide(self) -> None:
        cfg = {
            "allow_hosts": ["127.0.0.1:8766"],
            "shortcut_block": [{"type": "url_param", "name": "debug", "label": "调试参数"}],
            "guide_block_hosts": ["*walkthrough*", "*spoiler*"],
        }
        self.assertIsNone(block_reason("http://127.0.0.1:8766/live/index.html", cfg))
        self.assertEqual(block_reason("http://127.0.0.1:8766/live/index.html?debug=1", cfg)[0], "shortcut")
        self.assertEqual(block_reason("https://example.com/a", cfg)[0], "host")
        self.assertIsNone(block_reason("data:text/plain,hi", cfg))
        guided = dict(cfg, allow_hosts=["127.0.0.1:8766", "tips.example"])
        self.assertEqual(block_reason("https://tips.example/walkthrough/1", guided)[0], "guide")


class JudgeTests(unittest.TestCase):
    def test_checkpoint_and_answer_hash(self) -> None:
        digest = answer_sha256(" Ｎorth\n")
        self.assertEqual(digest, answer_sha256("north"))
        judge = Judge(
            {
                "hooks": {"on_entry": {"type": "url_regex", "pattern": "live/"}},
                "checkpoints": [{"id": "entered_live", "hook": "on_entry", "op": "truthy"}],
                "events": {},
                "ending": None,
                "answer_sha256": [digest],
            },
            "sample",
        )

        class Fake:
            async def urls(self):
                return ["http://127.0.0.1:8766/live/index.html"]

            async def dom_texts(self):
                return ["看得见的字"]

            async def local_storage(self, frame_url_regex=None):
                return {}

            def dialogs_step(self):
                return []

            def tab_count(self):
                return 1

            def requests(self, scope="all"):
                return []

            def if_status(self):
                return {}

        async def go():
            await judge.read(Fake())
            return judge.update(1)

        fresh = asyncio.run(go())
        self.assertIn(("checkpoint", "entered_live"), fresh)
        self.assertEqual(judge.check_answer("north"), "正确")
        self.assertTrue(judge.score()["ending_reached"])

    def test_distinct_dom_count(self) -> None:
        judge = Judge(
            {
                "hooks": {
                    "words": {
                        "type": "dom_regex",
                        "pattern": r"词\w",
                        "agg": "count",
                        "accumulate": "distinct",
                        "exclude": ["词噪"],
                    }
                },
                "checkpoints": [],
                "events": {},
            },
            "sample",
        )

        class Fake:
            def __init__(self, text):
                self.text = text

            async def urls(self):
                return []

            async def dom_texts(self):
                return [self.text]

            async def local_storage(self, frame_url_regex=None):
                return {}

            def dialogs_step(self):
                return []

            def tab_count(self):
                return 1

            def requests(self, scope="all"):
                return []

            def if_status(self):
                return {}

        async def read(text):
            return await judge.read(Fake(text))

        first = asyncio.run(read("词甲 词噪"))
        second = asyncio.run(read("词甲 词乙"))
        self.assertEqual(first["words"], 1)
        self.assertEqual(second["words"], 2)


class PromptTests(unittest.TestCase):
    def test_prompt_does_not_include_judge_markers(self) -> None:
        cfg = load_config(TASK)
        prompt = model_prompt(cfg)
        judge_text = (ROOT / cfg["judge_path"]).read_text(encoding="utf-8")
        self.assertIn("entered_live", judge_text)
        self.assertNotIn("entered_live", prompt)
        self.assertNotIn("on_entry", prompt)
        source = (ROOT / "harness" / "prompts.py").read_text(encoding="utf-8")
        self.assertNotIn("read_text", source)
        self.assertNotIn("open(", source)

    def test_missing_judge_still_finishes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "exclude").mkdir()
            (root / "exclude" / "sites.txt").write_text("ae27ff\n", encoding="utf-8")
            config_dir = root / "configs"
            config_dir.mkdir()
            path = config_dir / "solo.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "solo",
                        "category": "static",
                        "arg_layer": None,
                        "obs_mode": "A",
                        "model_visible": {"title": "空题", "intro": "只有题面。"},
                        "entry_url": None,
                        "local_serve": {"enabled": False},
                        "actions_enabled": ["give_up"],
                        "limits": {"max_steps": 3, "max_seconds": 30, "max_answer_submits": 1},
                        "history": {"full_obs_k": 4, "screenshot_k": 0},
                        "judge_path": "judge/missing/judge.json",
                        "policy_script": [{"op": "give_up"}],
                    }
                ),
                encoding="utf-8",
            )
            summary = asyncio.run(run(path, policy="script", repo_root=root))
            self.assertEqual(summary["ended_reason"], "give_up")
            self.assertEqual(summary["checkpoints_total"], 0)
            saved = json.loads((root / "runs" / "solo" / "A").glob("*/model_prompt.json").__iter__().__next__().read_text(encoding="utf-8"))
            self.assertNotIn("entered_live", saved["system"])

    def test_excluded_site_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "exclude").mkdir()
            (root / "exclude" / "sites.txt").write_text("ae27ff\n", encoding="utf-8")
            path = root / "bad.json"
            path.write_text(
                json.dumps(
                    {
                        "id": "ae27ff-demo",
                        "category": "static",
                        "arg_layer": None,
                        "obs_mode": "A",
                        "model_visible": {"title": "不收", "intro": "不收。"},
                        "actions_enabled": ["give_up"],
                        "limits": {"max_steps": 1, "max_seconds": 10, "max_answer_submits": 0},
                        "judge_path": "judge/missing.json",
                        "policy_script": [{"op": "give_up"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                asyncio.run(run(path, policy="script", repo_root=root))


class IFTests(unittest.TestCase):
    def test_valid_actions_are_not_observed(self) -> None:
        class Env:
            def __init__(self):
                self.valid_calls = 0

            def reset(self):
                return "你在一间屋子里。", {}

            def step(self, command):
                return f"执行了 {command}", 3, False, {}

            def get_score(self):
                return 3

            def victory(self):
                return False

            def game_over(self):
                return False

            def get_valid_actions(self):
                self.valid_calls += 1
                return ["zxq-verb"]

        env = Env()
        cfg = {
            "if": {"max_command_chars": 50},
            "obs_mode": "A",
            "obs_text": True,
            "obs_elements": False,
            "obs_screenshot": False,
            "show_url": False,
            "text_limit": 1000,
        }
        harness = IFHarness(cfg, Path("."))
        harness.env = env

        async def go():
            await harness.reset()
            obs = await harness.observe()
            saved = await harness.act({"op": "type", "text": "save"})
            moved = await harness.act({"op": "type", "text": "look"})
            return obs, saved, moved

        obs, saved, moved = asyncio.run(go())
        blob = json.dumps(obs, ensure_ascii=False)
        self.assertNotIn("zxq-verb", blob)
        self.assertEqual(env.valid_calls, 0)
        self.assertEqual(saved, "该动作在本评测中禁用")
        self.assertEqual(moved, "ok")
        self.assertEqual(harness.if_status()["score"], 3)


class ReportTests(unittest.TestCase):
    def test_layers_stay_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for layer in ("L1", "L2"):
                folder = root / "sample" / "B" / f"20261013_00000{layer[-1]}"
                folder.mkdir(parents=True)
                (folder / "summary.json").write_text(
                    json.dumps(
                        {
                            "task_id": "sample",
                            "category": "arg",
                            "arg_layer": layer,
                            "obs_mode": "B",
                            "model": {"name": "scripted"},
                            "checkpoints_reached": 1,
                            "checkpoints_total": 2,
                            "ending_reached": False,
                            "steps": 3,
                            "tokens": {"total": 0},
                        }
                    ),
                    encoding="utf-8",
                )
            rows = aggregate(root)
            self.assertEqual({row["arg_layer"] for row in rows}, {"L1", "L2"})
            self.assertTrue(all(row["category"] == "arg" for row in rows))

    def test_real_config_validates(self) -> None:
        self.assertEqual(validate_file(TASK, ROOT), [])


if __name__ == "__main__":
    unittest.main()
