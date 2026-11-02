"""Formal identity, model profile and resumable execution regressions."""
import argparse
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from harness.experiment import canonical_hash, execute, model_environment, seal, read_sealed
from harness.protocol_identity import validate_identity, file_sha256
from harness.protocol_report import report


def manifest():
    return {"schema": "arg-official-experiment-v1", "id": "formal-model", "delivery": {"id": "release"},
            "obs_mode": "B", "repeats": 3, "required_capabilities": [],
            "model_settings": {"id": "m", "provider": "openai", "model": "m", "base_url": "https://example.invalid/v1", "api_key_env": "UNIT_KEY"},
            "models": [{"provider": "openai", "name": "m", "profile_id": "p", "profile_sha256": "d" * 64,
                        "task_profile_sha256": {"record:1": "e" * 64}}],
            "tasks": [{"id": "record:1", "selector": "record:1", "task_id": "same-name", "obs_mode": "A",
                       "config_sha256": "a" * 64, "judge_sha256": "b" * 64, "progress_scored": True, "capabilities": []}]}


def episode(doc, repetition, attempt=1, success=False):
    return {"task_id": "same-name", "obs_mode": "A", "run_kind": "official", "ended_reason": "give_up",
            "model": {"provider": "openai", "name": "m"}, "judge_error": None, "scoring_protocol": "target_v1",
            "target_success": success, "progress": 1.0 if success else 0.0,
            "protocol_identity": {"evaluation_id": "record:1", "manifest_id": doc["id"], "manifest_sha256": canonical_hash(doc),
                                  "config_sha256": "a" * 64, "judge_sha256": "b" * 64, "profile_id": "p",
                                  "profile_sha256": "e" * 64, "run_id": f"{repetition}-{attempt}", "repetition": repetition, "attempt": attempt}}


class ExperimentTests(unittest.TestCase):
    def test_frozen_plan_rejects_overwrite_and_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            seal(path, {"id": "v1"})
            with self.assertRaises(ValueError): seal(path, {"id": "v2"})
            path.write_text('{"id":"modified"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum changed"): read_sealed(path)

    def test_task_specific_mode_profile_and_empty_capabilities(self):
        doc = manifest()
        rows = [episode(doc, n) for n in (1, 2, 3)]
        result = report(doc, rows)["models"][0]
        self.assertTrue(result["complete"])
        self.assertEqual(result["sr_macro"], 0)
        self.assertEqual(result["capabilities"], {})
        self.assertIsNone(result["balance"])
        wrong = copy.deepcopy(rows[0]); wrong["obs_mode"] = "B"
        self.assertEqual(report(doc, [wrong])["excluded"][0]["reason"], "observation_mismatch")
        wrong = copy.deepcopy(rows[0]); wrong["protocol_identity"]["profile_sha256"] = "d" * 64
        self.assertEqual(report(doc, [wrong])["excluded"][0]["reason"], "model_profile_hash_mismatch")

    def test_reject_partial_per_task_profiles(self):
        doc = manifest(); doc["models"][0]["task_profile_sha256"] = {}
        with self.assertRaises(ValueError): report(doc, [])

    def test_same_named_games_resolve_by_exact_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); cfg = root / "config.json"; judge = root / "judge.json"
            cfg.write_text("current", encoding="utf-8"); judge.write_text("judge", encoding="utf-8")
            task = {"id": "record:1", "task_id": "same-name", "obs_mode": "A", "reference_steps": 10,
                    "reference_evidence": "evidence.json", "max_answer_submits": 10,
                    "config_sha256": file_sha256(cfg), "judge_sha256": file_sha256(judge)}
            doc = {"id": "cohort", "obs_mode": "B", "tasks": [task, {**task, "id": "record:2", "config_sha256": "0" * 64}]}
            identity = validate_identity(doc, "same-name", cfg, judge, "A",
                                         {"limits": {"max_steps": 60, "max_seconds": 3600, "max_answer_submits": 10}})
            self.assertEqual(identity["evaluation_id"], "record:1")

    def test_model_credentials_are_isolated_and_restored(self):
        settings = manifest()["model_settings"]
        with patch.dict(os.environ, {"UNIT_KEY": "unit-secret", "OPENAI_API_KEY": "other-secret", "AGENT_MODEL": "other"}, clear=True):
            with model_environment(settings, require_key=True):
                self.assertEqual(os.environ["OPENAI_API_KEY"], "unit-secret")
                self.assertNotIn("AGENT_MODEL", os.environ)
                self.assertEqual(os.environ["LLM_MAX_OUTPUT_TOKENS"], "32768")
            self.assertEqual(os.environ["OPENAI_API_KEY"], "other-secret")
            self.assertEqual(os.environ["AGENT_MODEL"], "other")

    def test_valid_failures_are_not_rerun_and_resume_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); doc = manifest(); path = root / "models/m/manifest.json"; seal(path, doc)
            calls = []
            def fake_run(repo, release, task, args):
                calls.append((args.repetition, args.attempt))
                session = repo / "work" / args.session_name
                result = session / "bundle/runs/game/A/result"; result.mkdir(parents=True)
                (result / "summary.json").write_text(json.dumps(episode(doc, args.repetition, args.attempt)), encoding="utf-8")
                (session / "receipt.json").write_text(json.dumps({"status": "completed", "manifest_id": doc["id"]}), encoding="utf-8")
                return 0
            catalogue = {"tasks": [{"key": "record:1", "record_id": "record:1", "task_id": "same-name"}]}
            with patch.dict(os.environ, {"UNIT_KEY": "unit-secret"}, clear=True), \
                 patch("harness.delivery.load_release", return_value=({"id": "release"}, catalogue)), \
                 patch("harness.delivery.verify", return_value=[]), patch("harness.delivery.run_task", side_effect=fake_run):
                self.assertEqual(execute(root, path), 0)
                self.assertEqual(execute(root, path), 0)
            self.assertEqual(calls, [(1, 1), (2, 1), (3, 1)])

    def test_nonretryable_error_stops_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); doc = manifest(); path = root / "models/m/manifest.json"; seal(path, doc)
            def fake_run(repo, release, task, args):
                session = repo / "work" / args.session_name; session.mkdir(parents=True)
                (session / "receipt.json").write_text(json.dumps({"status": "error", "retryable": False, "http_status": 401}), encoding="utf-8")
                return 1
            catalogue = {"tasks": [{"key": "record:1", "record_id": "record:1", "task_id": "same-name"}]}
            with patch.dict(os.environ, {"UNIT_KEY": "unit-secret"}, clear=True), \
                 patch("harness.delivery.load_release", return_value=({"id": "release"}, catalogue)), \
                 patch("harness.delivery.verify", return_value=[]), patch("harness.delivery.run_task", side_effect=fake_run) as run:
                with self.assertRaisesRegex(ValueError, "Model stopped"):
                    execute(root, path)
                self.assertEqual(run.call_count, 1)

    def test_exhausted_transport_attempts_are_missing_not_valid_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); doc = manifest(); path = root / "models/m/manifest.json"; seal(path, doc)
            def fake_run(repo, release, task, args):
                session = repo / "work" / args.session_name; session.mkdir(parents=True)
                (session / "receipt.json").write_text(json.dumps({"status": "error", "retryable": True}), encoding="utf-8")
                return 1
            catalogue = {"tasks": [{"key": "record:1", "record_id": "record:1", "task_id": "same-name"}]}
            with patch.dict(os.environ, {"UNIT_KEY": "unit-secret"}, clear=True), \
                 patch("harness.delivery.load_release", return_value=({"id": "release"}, catalogue)), \
                 patch("harness.delivery.verify", return_value=[]), patch("harness.delivery.run_task", side_effect=fake_run) as run:
                self.assertEqual(execute(root, path), 1)
                self.assertEqual(run.call_count, 9)
            ledger = json.loads((path.parent / "execution.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["status"], "complete_with_missing_slots")
            self.assertTrue(all(slot["status"] == "missing" for slot in ledger["slots"]))


if __name__ == "__main__":
    unittest.main()
