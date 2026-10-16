"""Drop-in task scaffolding, IF, and LLM accounting. No live model."""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from harness.actions import normalize
from harness.batch import run_configs
from harness.config import load_config
from harness.if_harness import IFHarness
from harness.loop import run
from harness.policy_llm import LLMPolicy, to_anthropic_messages
from harness.scaffold import scaffold_task
from harness.serve_local import check_server
from harness.validate import validate_file

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "configs" / "fixtures" / "static-fixture.json"
WEB = ROOT / "configs" / "fixtures" / "local-web-fixture.json"
STORY = ROOT / "configs" / "examples" / "text-adventure.template.json"


class ReadyTests(unittest.TestCase):
    def test_configs_validate(self) -> None:
        for name in (
            "configs/fixtures/static-fixture.json",
            "configs/fixtures/local-web-fixture.json",
            "configs/fixtures/arg-l2-fixture.json",
            "configs/fixtures/arg-l3-fixture.json",
            "configs/examples/text-adventure.template.json",
        ):
            self.assertEqual(validate_file(ROOT / name, ROOT), [], name)

    def test_scaffold_is_runnable_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold_task(root, "sample-game", "web_puzzle", port=8791)
            schema_dir = root / "configs" / "schema"
            schema_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / "configs" / "schema" / "task.schema.json", schema_dir / "task.schema.json")
            errors = validate_file(root / "configs" / "sample-game.json", root)
            self.assertEqual(errors, [])
            page = (root / "tasks" / "sample-game" / "mirror" / "index.html").read_text(encoding="utf-8")
            self.assertIn("sample-game", page)

    def test_container_flag_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "exclude").mkdir()
            (root / "exclude" / "sites.txt").write_text("ae27ff\n", encoding="utf-8")
            scaffold_task(root, "boxed", "static")
            path = root / "configs" / "boxed.json"
            cfg = json.loads(path.read_text(encoding="utf-8"))
            cfg["isolation"] = {"container": True}
            path.write_text(json.dumps(cfg), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                asyncio.run(run(path, policy="script", repo_root=root))

    def test_server_starts_and_stops(self) -> None:
        check_server(load_config(WEB), ROOT)

    def test_if_command_needs_no_element_number(self) -> None:
        cfg = load_config(STORY)
        action, error = normalize({"op": "type", "text": "look"}, cfg)
        self.assertIsNone(error)
        self.assertEqual(action["op"], "type")

    def test_two_commands_record_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "exclude").mkdir()
            (root / "exclude" / "sites.txt").write_text("ae27ff\n", encoding="utf-8")
            story = root / "story.z8"
            story.write_bytes(b"not a real story")
            judge = {
                "hooks": {"score": {"type": "if_score"}},
                "checkpoints": [{"id": "scored", "hook": "score", "op": "gte", "value": 1}],
                "events": {},
                "ending": None,
            }
            (root / "judge").mkdir()
            (root / "judge" / "judge.json").write_text(json.dumps(judge), encoding="utf-8")
            config = {
                "id": "if-smoke",
                "category": "text_adventure",
                "arg_layer": None,
                "obs_mode": "A",
                "model_visible": {"title": "烟测", "intro": "空故事。"},
                "entry_url": None,
                "local_serve": {"enabled": False},
                "actions_enabled": ["type", "give_up"],
                "limits": {"max_steps": 2, "max_seconds": 30, "max_answer_submits": 0},
                "history": {"full_obs_k": 4, "screenshot_k": 0},
                "if": {"story_file": "story.z8", "interpreter": "jericho", "max_command_chars": 40},
                "judge_path": "judge/judge.json",
                "policy_script": [{"op": "type", "text": "look"}, {"op": "type", "text": "inventory"}],
            }
            path = root / "if.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            _FakeJericho.valid_calls = 0
            module = _FakeJericho()
            sys.modules["jericho"] = module
            try:
                summary = asyncio.run(run(path, policy="script", repo_root=root))
            finally:
                sys.modules.pop("jericho", None)
            self.assertEqual(module.valid_calls, 0)
            self.assertGreaterEqual(summary["checkpoints_reached"], 1)
            self.assertEqual(summary["if_score"], 2)
            last = json.loads(next((root / "runs" / "if-smoke" / "A").glob("*/last_obs.json")).read_text(encoding="utf-8"))
            self.assertNotIn("zxq-verb", json.dumps(last))

    def test_frotz_session_reads_banner(self) -> None:
        story = ROOT / "harness" / "testdata" / "fake_frotz.py"
        cfg = {
            "category": "text_adventure",
            "if": {
                "story_file": str(story),
                "interpreter": "frotz",
                "frotz_bin": sys.executable,
                "frotz_args": [str(story)],
                "max_command_chars": 40,
            },
        }
        harness = IFHarness(cfg, ROOT)

        async def go():
            await harness.reset()
            opening = harness.if_status()["score"]
            banner = harness.output
            result = await harness.act({"op": "type", "text": "look"})
            seen = harness.output
            await harness.close()
            return banner, result, seen, opening

        banner, result, seen, opening = asyncio.run(go())
        self.assertIn("Room.", banner)
        self.assertNotIn("***MORE***", banner)
        self.assertEqual(opening, 4)
        self.assertEqual(result, "ok")
        self.assertIn("look", seen)
        self.assertEqual(harness.if_status()["score"], 2)
        self.assertFalse(harness.if_status()["victory"])

    def test_llm_records_tokens_without_a_second_parse_call(self) -> None:
        replies = ["不是 json", '{"op":"give_up"}']
        calls: list[str] = []
        original = LLMPolicy._complete

        def fake(self, messages):
            raw = replies[len(calls)]
            calls.append(raw)
            return raw, {"prompt": 11, "completion": 3}

        LLMPolicy._complete = fake
        try:
            summary = asyncio.run(run(STATIC, policy="llm", repo_root=ROOT))
        finally:
            LLMPolicy._complete = original
        self.assertEqual(calls, replies)
        self.assertEqual(summary["ended_reason"], "give_up")
        self.assertEqual(summary["tokens"]["total"], 28)
        self.assertEqual(summary["history_k"], 4)
        raw_path = _latest(ROOT / "runs" / "static-fixture" / "A") / "model_raw.jsonl"
        lines = [line for line in raw_path.read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual(len(lines), 2)
        steps = (_latest(ROOT / "runs" / "static-fixture" / "A") / "steps.jsonl").read_text(encoding="utf-8")
        self.assertIn("动作格式错误", steps)

    def test_history_window_keeps_four_full_observations(self) -> None:
        cfg = load_config(STATIC)
        policy = LLMPolicy(cfg, ROOT)
        for index in range(6):
            policy.note_result({"url": f"http://local/{index}", "visible_text": f"full-{index}", "screenshot": ""}, {"op": "wait"}, "ok")
        messages = policy._messages({"url": "http://local/now", "visible_text": "current", "screenshot": ""})
        full = [item for item in messages if "visible_text" in json.dumps(item)]
        short = [item for item in messages if item.get("role") == "user" and "visible_text" not in json.dumps(item)]
        self.assertEqual(len(full), 5)
        self.assertEqual(len(short), 2)
        past = [item for item in full if "full-" in json.dumps(item)]
        self.assertTrue(past)
        self.assertTrue(all('"op": "wait"' in item["content"][0]["text"] for item in past))
        roles = [item["role"] for item in messages if item["role"] != "system"]
        self.assertEqual(roles[0], "user")
        self.assertEqual(roles[-1], "user")
        self.assertEqual(roles[1:-1:2], ["assistant"] * ((len(roles) - 1) // 2))
        _system, converted = to_anthropic_messages(messages)
        converted_roles = [item["role"] for item in converted]
        self.assertEqual(converted_roles, roles)
        policy.note_result(
            {"url": "http://local/reply", "visible_text": "full-reply", "screenshot": ""},
            {"op": "wait"},
            "ok",
            "先看海报。\n{\"op\":\"wait\"}",
        )
        replied = policy._messages({"url": "http://local/now", "visible_text": "current", "screenshot": ""})
        assistant = [item["content"] for item in replied if item["role"] == "assistant"]
        self.assertIn("先看海报", assistant[-1])
        current = policy._messages({"url": "http://local/now", "visible_text": "current", "screenshot": "", "notebook": "记下了"})
        self.assertIn("记下了", current[-1]["content"][0]["text"])
        self.assertTrue(all("记下了" not in json.dumps(item) for item in current[:-1]))

    def test_notebook_replace_rejects_text_over_the_limit(self) -> None:
        cfg = json.loads(STATIC.read_text(encoding="utf-8"))
        cfg["notebook"] = {"enabled": True, "max_chars": 20}
        cfg["policy_script"] = [
            {"op": "note", "text": "门口的数字是 4815"},
            {"op": "note", "text": "超" * 21},
            {"op": "give_up"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            path.write_text(json.dumps(cfg), encoding="utf-8")
            summary = asyncio.run(run(path, policy="script", repo_root=ROOT))
        self.assertTrue(summary["notebook_enabled"])
        self.assertEqual(summary["ended_reason"], "give_up")
        run_dir = _latest(ROOT / "runs" / "static-fixture" / "A")
        self.assertEqual((run_dir / "notebook.txt").read_text(encoding="utf-8"), "门口的数字是 4815")
        last = json.loads((run_dir / "last_obs.json").read_text(encoding="utf-8"))
        self.assertEqual(last["notebook"], "门口的数字是 4815")
        steps = (run_dir / "steps.jsonl").read_text(encoding="utf-8")
        self.assertIn("已记下", steps)
        self.assertIn("笔记超过长度上限", steps)


class _FakeJericho:
    valid_calls = 0

    class FrotzEnv:
        def __init__(self, path: str) -> None:
            self.path = path
            self.commands: list[str] = []

        def reset(self):
            return "You are in a room.", {}

        def step(self, command: str):
            self.commands.append(command)
            return f"done {command}", 0, False, {}

        def get_score(self):
            return 2 if self.commands else 0

        def victory(self):
            return False

        def game_over(self):
            return False

        def get_valid_actions(self):
            _FakeJericho.valid_calls += 1
            return ["zxq-verb"]


def _latest(root: Path) -> Path:
    return max((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime)


class BatchImportTests(unittest.TestCase):
    def test_three_fixture_configs_are_listed(self) -> None:
        listed = json.loads((ROOT / "configs" / "fixture_set.json").read_text(encoding="utf-8"))["tasks"]
        self.assertEqual(len(listed), 3)
        failed_import = run_configs
        self.assertTrue(callable(failed_import))


if __name__ == "__main__":
    unittest.main()
