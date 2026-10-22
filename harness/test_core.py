"""Core harness checks. No browser and no live model."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from harness.actions import last_json_object, normalize
from harness.browser_harness import inaccessible_result
from harness.config import apply_defaults, apply_obs_mode, load_config
from harness.if_harness import IFHarness
from harness.judge import Judge, answer_sha256
from harness.policy_llm import LLMPolicy
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

    def test_blocked_document_is_reported_before_return(self) -> None:
        notice = inaccessible_result(
            [
                {"type": "document", "host": "ginga-light.top"},
                {"type": "document", "host": "ginga-light.top"},
                {"type": "script", "host": "stats.example"},
            ]
        )
        self.assertEqual(notice, "该页面不可访问：ginga-light.top。已回到原页面。")
        self.assertEqual(inaccessible_result([{"type": "image", "host": "cdn.example"}]), "ok")

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

    def test_if_observation_keeps_turn(self) -> None:
        cfg = load_config(TASK, obs_mode="A")
        view = model_view(
            {"visible_text": "你在一间屋子里。", "turn": 2, "url": "", "tabs": [], "dialogs": [], "pending_dialog": None},
            cfg,
        )
        self.assertEqual(view["turn"], 2)
        self.assertIn("visible_text", view)

    def test_notebook_is_off_by_default_and_visible_when_enabled(self) -> None:
        self.assertNotIn("note", load_config(TASK)["actions_enabled"])
        raw = {
            "visible_text": "画面",
            "notebook": "门口的数字是 4815",
            "url": "http://x",
            "screenshot": "a.png",
            "tabs": [],
            "dialogs": [],
            "pending_dialog": None,
        }
        hidden = model_view(raw, load_config(TASK))
        self.assertNotIn("notebook", hidden)
        enabled = {"category": "static", "arg_layer": None, "actions_enabled": ["give_up"], "notebook": {"enabled": True}}
        apply_defaults(enabled)
        self.assertIn("note", enabled["actions_enabled"])
        self.assertIn("你有一本笔记", model_prompt(enabled))
        for mode in ("A", "B", "C"):
            enabled["obs_mode"] = mode
            apply_obs_mode(enabled)
            view = model_view(raw, enabled)
            self.assertEqual(view["notebook"], "门口的数字是 4815")

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
        self.assertIsNone(block_reason("https://tips.example/walkthrough/1", guided))
        self.assertIsNone(block_reason("https://tips.example/guide/page", guided))
        self.assertEqual(block_reason("https://walkthrough.example/page", guided)[0], "guide")

    def test_l3_rejects_local_search_and_guides(self) -> None:
        from harness.validate import l3_problems

        base = {
            "category": "arg",
            "arg_layer": "L3",
            "entry_url": "https://game.example/",
            "allow_hosts": ["game.example"],
            "local_serve": {"enabled": False},
            "isolation": {"container": False},
            "guide_block_hosts": [],
        }
        self.assertEqual(l3_problems(base), [])
        closed = dict(
            base,
            entry_url="http://127.0.0.1:8767/",
            allow_hosts=["127.0.0.1:8767"],
            local_serve={"enabled": True},
        )
        text = " ".join(l3_problems(closed))
        self.assertIn("本地服务", text)
        self.assertIn("https", text)
        self.assertIn("本机地址", text)
        leaked = dict(base, allow_hosts=["game.example", "*.google.com", "*.bilibili.com"])
        text = " ".join(l3_problems(leaked))
        self.assertIn("搜索引擎", text)
        self.assertIn("攻略站", text)
        boxed = dict(base, isolation={"container": True})
        self.assertTrue(any("容器" in item for item in l3_problems(boxed)))
        local_layer = dict(base, arg_layer="L2", entry_url="http://127.0.0.1/", local_serve={"enabled": True})
        self.assertEqual(l3_problems(local_layer), [])


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

    def test_list_membership_counts_only_solved_items(self) -> None:
        judge = Judge(
            {
                "hooks": {},
                "checkpoints": [
                    {"id": "station_1", "hook": "stations", "op": "includes", "value": 0},
                    {"id": "station_3", "hook": "stations", "op": "includes", "value": 3},
                ],
                "events": {},
                "ending": None,
            },
            "sample",
        )
        judge.values = {"stations": [0, 1, 2]}
        judge.update(1)
        score = judge.score()
        self.assertEqual(score["checkpoints_reached"], 1)
        self.assertEqual(score["checkpoints_total"], 2)
        self.assertIn("station_1", score["checkpoints"])
        self.assertNotIn("station_3", score["checkpoints"])

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

    def test_examples_follow_obs_mode(self) -> None:
        mode_a = model_prompt(load_config(TASK, obs_mode="A"))
        mode_c = model_prompt(load_config(TASK, obs_mode="C"))
        self.assertIn('{"op":"click","n":0}', mode_a)
        self.assertNotIn('{"op":"click","x":100,"y":200}', mode_a)
        self.assertIn('{"op":"click","x":100,"y":200}', mode_c)
        self.assertNotIn('{"op":"click","n":0}', mode_c)
        story = model_prompt(load_config(ROOT / "configs" / "examples" / "text-adventure.template.json"))
        self.assertIn('{"op":"type","text":"look","enter":true}', story)
        self.assertNotIn('{"op":"click"', story)
        self.assertNotIn("你有一本笔记", mode_a)
        self.assertIn("整段回复都会保留", mode_a)
        self.assertIn("进程、思路和假设", mode_a)
        self.assertIn("最近", mode_a)

    def test_rejected_images_fall_back_to_fewer_shots(self) -> None:
        policy = LLMPolicy(load_config(TASK), Path("."))
        policy.history = [
            {"obs": {"url": "http://local/old", "screenshot": "old.png"}, "action": {"op": "wait"}, "result": "ok"}
        ]
        obs = {"url": "http://local/now", "screenshot": "now.png", "notebook": ""}

        def shots(mode: str) -> list[str]:
            found = []
            for message in policy._messages(obs, images=mode):
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                found.extend(part.get("path") for part in content if part.get("type") == "image_path")
            return found

        self.assertEqual(shots("all"), ["old.png", "now.png"])
        self.assertEqual(shots("current"), ["now.png"])
        self.assertEqual(shots("none"), [])

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


class TranscriptStatusTests(unittest.TestCase):
    def test_score_layouts_from_dfrotz(self) -> None:
        from harness.if_harness import read_transcript_status

        labeled = read_transcript_status("   Outside                                                     Score: 0\n")
        paired = read_transcript_status("   Computer Site                                               3/2\n")
        clock = read_transcript_status("   Bedroom                                        Time:  9:05 am\n")
        won = read_transcript_status("The end.\n*** You have won ***\n")
        self.assertEqual(labeled["score"], 0)
        self.assertEqual(paired["score"], 3)
        self.assertIsNone(clock["score"])
        self.assertTrue(won["victory"])
        self.assertTrue(won["game_over"])


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
            self.assertEqual(rows[0]["mean_progress"], 0.5)
            self.assertEqual(rows[0]["endings_rate"], 0.0)

    def test_page_turn_is_not_main_progress(self) -> None:
        from harness.judge import Judge

        judge = Judge(
            {
                "hooks": {},
                "checkpoints": [
                    {"id": "saw_page_number", "hook": "page_no", "op": "gte", "value": 1, "role": "diagnostic"},
                    {"id": "solved_gate", "hook": "gate", "op": "truthy"},
                ],
                "events": {"opened_cover": {"hook": "cover", "op": "truthy"}},
                "ending": {"hook": "done", "op": "truthy"},
            },
            "sample",
            Path("."),
        )
        judge.values = {"page_no": 4, "cover": True, "gate": False, "done": False}
        judge.update(1)
        browsing = judge.score()
        self.assertEqual(browsing["checkpoints_reached"], 0)
        self.assertEqual(browsing["checkpoints_total"], 1)
        self.assertFalse(browsing["ending_reached"])
        self.assertEqual(browsing["diagnostic"]["saw_page_number"], 1)
        self.assertEqual(browsing["events"][0]["id"], "opened_cover")
        judge.values = {"page_no": 8, "cover": True, "gate": True, "done": True}
        judge.update(2)
        solved = judge.score()
        self.assertEqual(solved["checkpoints_reached"], 1)
        self.assertTrue(solved["ending_reached"])
        self.assertEqual(solved["ending_tier"], "good")
        self.assertTrue(solved["good_ending"])
        self.assertEqual(solved["route_progress"], 1.0)

    def test_answer_only_task_scores_when_the_answer_is_correct(self) -> None:
        judge = Judge({"checkpoints": [], "ending": None, "answer_sha256": []}, "sample", Path("."))
        self.assertIsNone(judge.score()["route_progress"])
        self.assertFalse(judge.score()["ending_reached"])
        judge.answer_correct = True
        judge.ending_reached = True
        scored = judge.score()
        self.assertEqual(scored["route_progress"], 1.0)
        self.assertTrue(scored["ending_reached"])
        self.assertEqual(scored["ending_tier"], "good")
        self.assertTrue(scored["good_ending"])

    def test_short_route_does_not_raise_progress_before_its_ending(self) -> None:
        from harness.judge import Judge

        judge = Judge(
            {
                "checkpoints": [
                    {"id": "spine", "hook": "spine", "op": "truthy"},
                    {"id": "last", "hook": "last", "op": "truthy"},
                ],
                "routes": [
                    {
                        "id": "good",
                        "tier": "good",
                        "gates": ["spine", "last"],
                        "ending": {"hook": "good_end", "op": "truthy"},
                    },
                    {
                        "id": "bad_early",
                        "tier": "bad",
                        "gates": ["spine"],
                        "ending": {"hook": "bad_end", "op": "truthy"},
                    },
                ],
            },
            "sample",
            Path("."),
        )
        judge.values = {"spine": True, "last": False, "good_end": False, "bad_end": False}
        judge.update(1)
        mid = judge.score()
        self.assertEqual(mid["route_id"], "good")
        self.assertEqual(mid["route_progress"], 0.5)
        self.assertFalse(mid["ending_reached"])
        judge.values = {"spine": True, "last": False, "good_end": False, "bad_end": True}
        judge.update(2)
        bad = judge.score()
        self.assertTrue(bad["ending_reached"])
        self.assertEqual(bad["route_id"], "bad_early")
        self.assertEqual(bad["ending_tier"], "bad")
        self.assertFalse(bad["good_ending"])
        self.assertEqual(bad["route_progress"], 1.0)

    def test_mean_progress_skips_tasks_without_critical_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bare = root / "bare" / "B" / "20261015_000001"
            gated = root / "gated" / "B" / "20261015_000001"
            bare.mkdir(parents=True)
            gated.mkdir(parents=True)
            (bare / "summary.json").write_text(
                json.dumps(
                    {
                        "category": "web_puzzle",
                        "arg_layer": None,
                        "obs_mode": "B",
                        "model": {"name": "scripted"},
                        "checkpoints_reached": 0,
                        "checkpoints_total": 0,
                        "ending_reached": False,
                        "steps": 2,
                        "tokens": {"total": 0},
                    }
                ),
                encoding="utf-8",
            )
            (gated / "summary.json").write_text(
                json.dumps(
                    {
                        "category": "web_puzzle",
                        "arg_layer": None,
                        "obs_mode": "B",
                        "model": {"name": "scripted"},
                        "checkpoints_reached": 1,
                        "checkpoints_total": 2,
                        "ending_reached": True,
                        "steps": 4,
                        "tokens": {"total": 0},
                    }
                ),
                encoding="utf-8",
            )
            rows = aggregate(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["runs"], 2)
            self.assertEqual(rows[0]["mean_progress"], 0.5)
            self.assertEqual(rows[0]["endings_rate"], 0.5)

    def test_real_config_validates(self) -> None:
        self.assertEqual(validate_file(TASK, ROOT), [])


if __name__ == "__main__":
    unittest.main()
