"""Regression coverage for the target protocol, identities, and clock."""

import unittest
from unittest import mock
from tempfile import TemporaryDirectory
from pathlib import Path

from harness.judge import Judge, answer_sha256
from harness.protocol_clock import EffectiveClockExpired, ProtocolClock, WallClockExpired
from harness.protocol_budget import reference_limits, validate_budget
from harness.protocol_identity import manifest_sha256
from harness.protocol_report import report
from harness.policy_llm import LLMPolicy, ModelRefusal, _post_with_retry
from harness.loop import _episode, _propose
from harness.static_harness import StaticHarness
from harness.policy_script import ScriptedPolicy


class ProtocolJudgeTests(unittest.TestCase):
    def config(self):
        return {"scoring_protocol": "target_v1", "target_success": {"route_ids": ["goal"]},
                "checkpoints": [{"id": "a", "hook": "a"}, {"id": "b", "hook": "b"},
                                {"id": "c", "hook": "c", "role": "optional"}],
                "routes": [{"id": "goal", "tier": "good", "gates": ["a", "b"],
                            "ending": {"hook": "success", "op": "truthy"}},
                           {"id": "other", "tier": "normal", "gates": ["a"],
                            "ending": {"hook": "other", "op": "truthy"}}]}

    def test_progress_excludes_optional_and_requires_success(self):
        j = Judge(self.config(), "task")
        j.values = {"a": True, "b": True, "c": True}
        j.update(1)
        self.assertEqual(j.score()["route_progress"], 2 / 3)
        self.assertFalse(j.score()["target_success"])
        j.values["success"] = True
        j.update(2)
        self.assertEqual(j.score()["route_progress"], 1)
        self.assertTrue(j.score()["target_success"])

    def test_normal_ending_does_not_succeed(self):
        j = Judge(self.config(), "task")
        j.values = {"other": True}
        j.update(1)
        self.assertFalse(j.score()["target_success"])
        self.assertTrue(j.score()["ending_reached"])

    def test_non_target_route_still_contributes_to_progress(self):
        cfg = self.config()
        cfg['routes'][0]['gates'] = ['a', 'b']
        cfg['routes'][1]['gates'] = ['a']
        j = Judge(cfg, 'task')
        j.values = {'a': True}
        j.update(1)
        self.assertFalse(j.score()['target_success'])
        self.assertEqual(j.score()['route_progress'], 1 / 2)

    def test_answer_is_not_unrelated_ending(self):
        cfg = {"scoring_protocol": "target_v1", "target_success": {"ending": True},
               "ending": {"hook": "done", "op": "truthy"}, "answer_sha256": answer_sha256("yes")}
        j = Judge(cfg, "task")
        j.check_answer("yes")
        self.assertFalse(j.score()["target_success"])

    def test_bad_success_route_rejected(self):
        cfg = self.config()
        cfg["routes"][0]["tier"] = "bad"
        with self.assertRaises(ValueError):
            Judge(cfg, "task")

    def test_threshold_and_alternate_routes_are_monotonic(self):
        cfg = self.config()
        cfg["target_success"]["route_ids"] = ["goal", "other"]
        cfg["routes"][0]["gates"] = []
        cfg["routes"][0]["gate_groups"] = [{"ids": ["a", "b"], "required": 1}]
        j = Judge(cfg, "task")
        self.assertEqual(j.score()["route_progress"], 0)
        j.values = {"a": True}
        j.update(1)
        self.assertEqual(j.score()["route_progress"], .5)
        j.values = {"a": False, "b": False}
        j.update(2)
        self.assertEqual(j.score()["route_progress"], .5)
        j.values = {"other": True}
        j.update(3)
        self.assertTrue(j.score()["target_success"])
        self.assertEqual(j.score()["route_progress"], 1)


class ClockTests(unittest.TestCase):
    def test_effective_and_wall(self):
        now = [0.0]
        clock = ProtocolClock(10, lambda: now[0])
        now[0] = 7
        clock.add_infrastructure_delay(4)
        self.assertEqual(clock.effective, 3)
        now[0] = 14
        with self.assertRaises(EffectiveClockExpired):
            clock.check()
        clock.add_infrastructure_delay(6)
        now[0] = 20
        with self.assertRaises(WallClockExpired):
            clock.check()


class BudgetTests(unittest.TestCase):
    def test_tier_boundaries_and_evidence(self):
        self.assertEqual(reference_limits(20)["max_steps"], 60)
        self.assertEqual(reference_limits(21)["max_steps"], 150)
        self.assertEqual(reference_limits(50)["max_steps"], 150)
        self.assertEqual(reference_limits(51)["max_steps"], 300)
        cfg = {"limits": reference_limits(21)}
        validate_budget({"reference_steps": 21, "reference_evidence": "trace.json"}, cfg)
        with self.assertRaises(ValueError):
            validate_budget({"reference_steps": 21}, cfg)
        with self.assertRaises(ValueError):
            validate_budget({"reference_steps": 51, "reference_evidence": "trace.json"}, cfg)


class ReportTests(unittest.TestCase):
    def manifest(self):
        return {"id": "fixture", "obs_mode": "B", "repeats": 3,
                "required_capabilities": ["state", "plan"],
                "models": [{"provider": "mock", "name": "m", "profile_id": "p", "profile_sha256": "d" * 64},
                           {"provider": "mock", "name": "missing", "profile_id": "p", "profile_sha256": "e" * 64}],
                "tasks": [{"id": "t", "config_sha256": "a" * 64, "judge_sha256": "b" * 64,
                           "progress_scored": True, "capabilities": ["state"]}]}

    def episode(self, m, rep, success):
        return {"task_id": "t", "run_kind": "official", "model": {"provider": "mock", "name": "m"},
                "obs_mode": "B", "ended_reason": "ending", "judge_error": None,
                "scoring_protocol": "target_v1", "target_success": success, "progress": 1 if success else .5,
                "protocol_identity": {"manifest_id": "fixture", "manifest_sha256": manifest_sha256(m),
                                      "config_sha256": "a" * 64, "judge_sha256": "b" * 64,
                                      "run_id": str(rep), "repetition": rep, "attempt": 1, "profile_id": "p", "profile_sha256": "d" * 64}}

    def test_partial_coverage_and_complete_scores(self):
        m = self.manifest()
        rows = [self.episode(m, i, i <= 2) for i in range(1, 4)]
        r = report(m, rows)
        model = next(x for x in r["models"] if x["model"] == "m")
        self.assertAlmostEqual(model["sr_macro"], 2 / 3)
        self.assertEqual(model["pass3_macro"], 0)
        self.assertIsNone(model["balance"])
        missing = next(x for x in r["models"] if x["model"] == "missing")
        self.assertIsNone(missing["sr_macro"])

    def test_reject_duplicate_slot_and_version(self):
        m = self.manifest()
        row = self.episode(m, 1, True)
        duplicate = self.episode(m, 1, False)
        duplicate["protocol_identity"]["run_id"] = "other"
        with self.assertRaises(ValueError):
            report(m, [row, duplicate])
        row["protocol_identity"]["judge_sha256"] = "c" * 64
        self.assertEqual(report(m, [row])["excluded"][0]["reason"], "version_mismatch")

    def test_profile_hash_mismatch_and_duplicate_run_id(self):
        m = self.manifest()
        row = self.episode(m, 1, True)
        row["protocol_identity"]["profile_sha256"] = "f" * 64
        self.assertEqual(report(m, [row])["excluded"][0]["reason"], "model_profile_hash_mismatch")
        row = self.episode(m, 1, True)
        duplicate = self.episode(m, 2, True)
        duplicate["protocol_identity"]["run_id"] = row["protocol_identity"]["run_id"]
        with self.assertRaises(ValueError):
            report(m, [row, duplicate])


class ProviderTests(unittest.TestCase):
    def test_official_profile_omits_temperature_and_uses_configured_limit(self):
        with TemporaryDirectory(dir=Path.cwd()) as tmp, mock.patch.dict("os.environ", {"LLM_PROVIDER": "openai", "OPENAI_MODEL": "example"}, clear=True):
            policy = LLMPolicy({"_run_kind": "official", "obs_mode": "B", "require_images": True}, Path(tmp))
            self.assertIsNone(policy.temperature)
            self.assertEqual(policy.max_tokens, 32768)
            self.assertEqual(len(policy.profile_sha256()), 64)

    def test_infrastructure_error_is_not_an_invalid_action(self):
        policy = mock.Mock()
        policy.act.side_effect = RuntimeError("missing API key")
        with self.assertRaises(RuntimeError):
            _propose(policy, {})
        policy.act.side_effect = ValueError("bad format")
        self.assertEqual(_propose(policy, {})[0], {"op": "_invalid"})
        policy.act.side_effect = ModelRefusal("declined")
        self.assertEqual(_propose(policy, {}), ({"op": "give_up"}, "模型拒绝"))

    def test_screenshot_required_cannot_silently_fall_back(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            policy = LLMPolicy({"_run_kind": "official", "obs_mode": "B", "require_images": True}, Path.cwd())
            with self.assertRaises(RuntimeError):
                policy.act({})

    def test_openai_and_anthropic_request_parameters(self):
        import httpx
        request = httpx.Request("POST", "https://example.invalid")
        openai_response = httpx.Response(200, request=request, json={"model": "gpt-6-astra", "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]})
        env = {"LLM_PROVIDER": "openai", "OPENAI_MODEL": "gpt-6-astra", "OPENAI_API_KEY": "dummy"}
        with mock.patch.dict("os.environ", env, clear=True), mock.patch("harness.policy_llm._post_with_retry", return_value=openai_response) as post:
            policy = LLMPolicy({"_run_kind": "official", "obs_mode": "A"}, Path.cwd())
            policy._openai([])
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["reasoning_effort"], "medium")
            self.assertEqual(payload["max_completion_tokens"], 32768)
            self.assertNotIn("temperature", payload)
        anthropic_response = httpx.Response(200, request=request, json={"model": "claude-opus-5-5", "content": [{"type": "text", "text": "{}"}], "stop_reason": "end_turn"})
        env = {"LLM_PROVIDER": "anthropic", "ANTHROPIC_MODEL": "claude-opus-5-5", "ANTHROPIC_API_KEY": "dummy"}
        with mock.patch.dict("os.environ", env, clear=True), mock.patch("harness.policy_llm._post_with_retry", return_value=anthropic_response) as post:
            policy = LLMPolicy({"_run_kind": "official", "obs_mode": "A"}, Path.cwd())
            policy._anthropic([])
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["thinking"], {"type": "adaptive"})
            self.assertEqual(payload["output_config"], {"effort": "medium"})
            self.assertNotIn("temperature", payload)

    def test_request_retry_limit_and_log(self):
        import httpx
        request = httpx.Request("POST", "https://example.invalid")
        responses = [httpx.Response(429, request=request, headers={"Retry-After": "7"}),
                     httpx.Response(503, request=request), httpx.Response(200, request=request)]
        client = mock.MagicMock()
        client.__enter__.return_value.post.side_effect = responses
        with TemporaryDirectory(dir=Path.cwd()) as tmp, mock.patch("httpx.Client", return_value=client), mock.patch("time.sleep") as sleep:
            output = _post_with_retry("https://example.invalid", attempts=3, timeout=10, log_path=Path(tmp) / "requests.jsonl")
            self.assertEqual(output.status_code, 200)
            self.assertEqual([x.args[0] for x in sleep.call_args_list], [7, 15])
            self.assertEqual(len((Path(tmp) / "requests.jsonl").read_text().splitlines()), 6)

    def test_failed_request_at_remaining_budget_is_infrastructure_error(self):
        import httpx
        now = [0.0]
        clock = ProtocolClock(10, lambda: now[0])
        def timeout(*args, **kwargs):
            now[0] += 10
            raise httpx.ReadTimeout('timeout')
        with mock.patch('harness.policy_llm._post_with_deadline', side_effect=timeout), mock.patch('time.monotonic', side_effect=lambda: now[0]):
            with self.assertRaises(httpx.ReadTimeout):
                _post_with_retry('https://example.invalid', timeout=900, attempts=1, clock=clock)
        self.assertEqual(clock.effective, 0)
        self.assertEqual(clock.paused, 10)

    def test_total_deadline_interrupts_slow_stream(self):
        import http.server
        import threading
        import time
        import httpx
        from harness.policy_llm import _post_with_deadline
        seen = threading.Event()
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.send_header('Content-Length', '500')
                self.end_headers()
                seen.set()
                try:
                    for _ in range(500):
                        self.wfile.write(b'x')
                        self.wfile.flush()
                        time.sleep(.1)
                except (BrokenPipeError, ConnectionResetError):
                    pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        started = time.monotonic()
        try:
            with self.assertRaises(httpx.ReadTimeout):
                _post_with_deadline(f'http://127.0.0.1:{server.server_port}/', 8.0, False, {'json': {'test': True}})
            self.assertTrue(seen.is_set(), 'server must have begun streaming')
            self.assertLess(time.monotonic() - started, 12.0)
        finally:
            server.shutdown()
            server.server_close()

    def test_deadline_worker_returns_response_and_request_id(self):
        import http.server
        import threading
        import gzip
        from harness.policy_llm import _post_with_deadline
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                data = gzip.compress(b'{"ok":true}')
                self.send_response(200)
                self.send_header('Content-Encoding', 'gzip')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('x-request-id', 'local-id')
                self.end_headers()
                self.wfile.write(data)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            response = _post_with_deadline(f'http://127.0.0.1:{server.server_port}/', 10, False, {'json': {'test': True}})
            self.assertEqual(response.json(), {'ok': True})
            self.assertEqual(response.headers['x-request-id'], 'local-id')
        finally:
            server.shutdown()
            server.server_close()


class EpisodeIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_startup_failure_is_audited(self):
        import json
        from harness.loop import _run_episode
        cfg = {'id': 'startup', 'obs_mode': 'A'}
        with TemporaryDirectory(dir=Path.cwd()) as tmp:
            root = Path(tmp)
            with mock.patch('harness.loop.LocalServer'), mock.patch('harness.loop.make_harness', side_effect=RuntimeError('startup failure')):
                with self.assertRaises(RuntimeError):
                    await _run_episode(cfg, root, 'llm', True, 'test')
            run_dir = next((root / 'runs' / 'startup' / 'A').iterdir())
            state = json.loads((run_dir / 'run_state.json').read_text(encoding='utf-8'))
            self.assertEqual(state['status'], 'error')
            self.assertEqual(state['error_type'], 'RuntimeError')
            self.assertFalse((run_dir / 'summary.json').exists())

    async def test_target_answer_episode_records_identity_and_clock(self):
        cfg = {"id": "fixture", "category": "static", "runtime_layer": "L1", "obs_mode": "A",
               "obs_text": True, "actions_enabled": ["submit_answer"], "model_visible": {"intro": "question"},
               "limits": {"max_steps": 3, "max_seconds": 30, "max_answer_submits": 2},
               "_protocol_identity": {"run_id": "fixture-run"}}
        judge = Judge({"scoring_protocol": "target_v1", "target_success": {"answer": True},
                       "answer_sha256": answer_sha256("yes")}, "fixture")
        with TemporaryDirectory(dir=Path.cwd()) as tmp:
            harness = StaticHarness(cfg, Path(tmp))
            harness.blocked = []
            policy = ScriptedPolicy([{"op": "submit_answer", "text": "yes"}])
            summary = await _episode(cfg, harness, judge, policy, "script", Path(tmp), run_kind="official")
        self.assertTrue(summary["target_success"])
        self.assertEqual(summary["progress"], 1)
        self.assertEqual(summary["ended_reason"], "ending")
        self.assertEqual(summary["protocol_identity"]["run_id"], "fixture-run")
        self.assertIn("effective_seconds", summary)

    async def test_cancelled_episode_is_not_recorded_as_valid(self):
        import asyncio
        import json
        cfg = {"id": "fixture", "category": "static", "runtime_layer": "L1", "obs_mode": "A",
               "obs_text": True, "actions_enabled": ["submit_answer"], "model_visible": {"intro": "question"},
               "limits": {"max_steps": 3, "max_seconds": 30, "max_answer_submits": 2},
               "_protocol_identity": {"run_id": "cancelled"}}
        judge = Judge({"scoring_protocol": "target_v1", "target_success": {"answer": True},
                       "answer_sha256": answer_sha256("yes")}, "fixture")
        with TemporaryDirectory(dir=Path.cwd()) as tmp:
            harness = StaticHarness(cfg, Path(tmp)); harness.blocked = []
            policy = ScriptedPolicy([])
            policy.act = mock.Mock(side_effect=asyncio.CancelledError())
            with self.assertRaises(asyncio.CancelledError):
                await _episode(cfg, harness, judge, policy, "script", Path(tmp), run_kind="official")
            summary = json.loads((Path(tmp) / 'summary.json').read_text(encoding='utf-8'))
        self.assertEqual(summary['ended_reason'], 'error')
        self.assertEqual(summary['error'], 'CancelledError')


if __name__ == "__main__":
    unittest.main()
