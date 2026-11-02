"""Release integrity, archive isolation and common-runner regression tests."""
import argparse
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from harness import delivery

ROOT = Path(__file__).resolve().parents[1]


class DeliveryTests(unittest.TestCase):
    def make_archive(self, path, require_images=True, extra=None, config_path="configs/example.json"):
        cfg = {"id": "example", "category": "static", "runtime_layer": "L1", "obs_mode": "B",
               "model_visible": {"title": "Example", "intro": "Test"}, "actions_enabled": ["give_up"],
               "limits": {"max_steps": 60, "max_seconds": 3600, "max_answer_submits": 10},
               "judge_path": "judge/example.json", "require_images": require_images}
        spec = {"tasks": [{"id": "example", "config": config_path, "reference_steps": 10,
                            "reference_evidence": "reference.json", "max_answer_submits": 10}]}
        with zipfile.ZipFile(path, "w") as z:
            z.writestr(config_path, json.dumps(cfg))
            z.writestr("judge/example.json", json.dumps({"scoring_protocol": "target_v1", "target_success": {"answer": True}}))
            z.writestr("protocol-task-spec.json", json.dumps(spec))
            for name, value in (extra or {}).items():
                z.writestr(name, value)

    def test_rejects_traversal_and_absolute_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ["../outside", "/absolute", "C:/absolute", "foo:stream", "a/../../outside"]:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    delivery.inside(Path(directory), name)

    def test_zip_traversal_never_writes_outside(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_archive(root / "bad.zip", extra={"../outside.txt": "bad"})
            with self.assertRaises(ValueError):
                delivery.extract(root / "bad.zip", root / "extract")
            self.assertFalse((root / "outside.txt").exists())

    def test_release_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            delivery.write_json(root / "catalogue.json", {"tasks": []})
            release = {"files": {"catalogue.json": delivery.sha256(root / "catalogue.json")}}
            delivery.write_json(root / "RELEASE.json", release)
            (root / "RELEASE.json.sha256").write_text(delivery.sha256(root / "RELEASE.json"), encoding="ascii")
            delivery.load_release(root)
            delivery.write_json(root / "catalogue.json", {"tasks": ["tampered"]})
            with self.assertRaisesRegex(ValueError, "catalogue"):
                delivery.load_release(root)
            delivery.write_json(root / "RELEASE.json", {})
            with self.assertRaisesRegex(ValueError, "RELEASE.json"):
                delivery.load_release(root)

    def test_selected_archive_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.zip").write_bytes(b"original")
            task = {"archive": "sample.zip", "archive_sha256": delivery.sha256(root / "sample.zip")}
            self.assertEqual(delivery.verify(root, {"files": {}}, [task]), [])
            (root / "sample.zip").write_bytes(b"changed")
            self.assertEqual(len(delivery.verify(root, {"files": {}}, [task])), 1)

    def test_declared_root_config_is_found_and_missing_images_is_formal_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.zip"
            self.make_archive(path, require_images=False, config_path="config-unit.json",
                              extra={"configs/irrelevant-test.json": "{}"})
            rows = delivery.inspect_archive(path, delivery.read_json(ROOT / "configs/schema/task.schema.json"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["config"], "config-unit.json")
            self.assertEqual(rows[0]["errors"], [])
            self.assertIn("B/C official mode requires require_images=true", rows[0]["official_blockers"])

    def test_secret_env_inside_archive_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.zip"
            self.make_archive(path, extra={"nested/.env": "FAKE_SECRET=do-not-print"})
            with self.assertRaisesRegex(ValueError, "contains a .env"):
                delivery.inspect_archive(path, {})

    def test_ambiguous_task_selector_rejected(self):
        catalogue = {"tasks": [{"key": "r::a", "record_id": "r", "task_id": "a"},
                                {"key": "r::b", "record_id": "r", "task_id": "b"}]}
        with self.assertRaises(ValueError):
            delivery.select(catalogue, "r")
        self.assertEqual(delivery.select(catalogue, "r::b")["task_id"], "b")

    def test_batch_excludes_online_and_blocked_entries(self):
        catalogue = {"tasks": [
            {"key": "local", "record_id": "local", "errors": [], "runtime_layer": "L1"},
            {"key": "online", "record_id": "online", "errors": [], "runtime_layer": "L3"},
            {"key": "blocked", "record_id": "blocked", "errors": ["missing"], "runtime_layer": "L1"}]}
        args = argparse.Namespace(official=False, all_local=True, task=None, repeats=2)
        tasks, repeats = delivery.batch_tasks(catalogue, args)
        self.assertEqual([t["key"] for t in tasks], ["local"])
        self.assertEqual(repeats, 2)

    def test_official_batch_uses_frozen_repeats(self):
        catalogue = {"tasks": [{"key": "local", "task_id": "local", "record_id": "local",
                                "errors": [], "official_blockers": []}]}
        args = argparse.Namespace(official=True, policy="llm", all_local=False, task=None, repeats=1, manifest="unused.json")
        with patch.object(delivery, "read_json", return_value={"tasks": [{"id": "local"}], "repeats": 3}):
            with self.assertRaisesRegex(ValueError, "Repeats"):
                delivery.batch_tasks(catalogue, args)

    def test_report_finds_nested_sessions_and_records_missing_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            delivery.write_json(root / "manifest.json", {"id": "test"})
            delivery.write_json(root / "work/first/bundle/runs/t/B/one/summary.json", {"task_id": "t"})
            delivery.write_json(root / "work/second/receipt.json", {"status": "error"})
            with patch("harness.protocol_report.report", return_value={"models": []}) as score:
                result = delivery.report_runs(root, root / "manifest.json", root / "report.json")
            self.assertEqual(score.call_args.args[1], [{"task_id": "t"}])
            self.assertEqual(len(result["unreadable"]), 1)
            self.assertTrue((root / "report.json").exists())

    def test_common_env_and_smoke_never_load_model_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "example.zip"
            self.make_archive(archive)
            (root / ".env").write_text("DELIVERY_TEST_MARKER=loaded\n", encoding="utf-8")
            task = {"key": "r", "archive": archive.name, "archive_sha256": delivery.sha256(archive),
                    "config": "configs/example.json", "errors": [], "official_blockers": []}
            received = []

            async def fake_run(config, **kwargs):
                received.append((delivery.read_json(config), kwargs, os.environ.get("DELIVERY_TEST_MARKER")))
                return {"ended_reason": "give_up"}

            with patch.dict(os.environ, {}, clear=True), patch("harness.delivery.environment", return_value={}), \
                 patch("harness.loop.run", side_effect=fake_run), patch("sys.stdout", new_callable=io.StringIO):
                args = argparse.Namespace(command="smoke", show=False)
                result = delivery.run_task(root, {"id": "test-release", "files": {}}, task, args)
            self.assertEqual(result, 0)
            self.assertEqual(received[0][0]["policy_script"], [{"op": "give_up"}])
            self.assertEqual(received[0][1]["policy"], "script")
            self.assertEqual(received[0][1]["run_kind"], "test")
            self.assertEqual(received[0][2], "loaded")
            self.assertEqual(delivery.sha256(archive), task["archive_sha256"])


if __name__ == "__main__":
    unittest.main()
