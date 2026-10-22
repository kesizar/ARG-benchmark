"""Episode loop: reset, observe, act, judge, log."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SHANGHAI = timezone(timedelta(hours=8))

from harness.actions import normalize
from harness.browser_harness import BrowserHarness, pack_observation
from harness.config import entry_allowed, exclusion_hit, load_config, load_exclude, repo_root_from
from harness.env import load_env
from harness.grid_harness import GridHarness
from harness.if_harness import IFHarness
from harness.scenario_harness import ScenarioHarness
from harness.judge import Judge
from harness.observe import obs_summary
from harness.policy_llm import LLMPolicy
from harness.policy_script import ScriptedPolicy
from harness.prompts import model_prompt
from harness.sandbox import assert_isolation
from harness.serve_local import LocalServer
from harness.static_harness import StaticHarness
from harness.summary import build_summary, snapshot_config
from harness.tokens import TokenLedger


def make_harness(cfg: dict, run_dir: Path, headless: bool):
    if cfg.get("grid"):
        return GridHarness(cfg, run_dir)
    if cfg.get("scenario"):
        return ScenarioHarness(cfg, run_dir)
    category = cfg.get("category")
    if category == "text_adventure":
        return IFHarness(cfg, run_dir)
    if category == "static":
        return StaticHarness(cfg, run_dir)
    return BrowserHarness(cfg, run_dir, headless=headless)


def make_policy(kind: str, cfg: dict, run_dir: Path):
    if kind == "llm":
        return LLMPolicy(cfg, run_dir)
    if kind != "script":
        raise ValueError(f"未知策略 {kind}")
    return ScriptedPolicy(cfg.get("policy_script"))


async def run(
    cfg_path: str | Path,
    *,
    policy: str = "script",
    obs_mode: str | None = None,
    headless: bool = True,
    repo_root: Path | None = None,
) -> dict:
    path = Path(cfg_path)
    root = Path(repo_root) if repo_root else repo_root_from(path.resolve().parent)
    load_env(root)
    cfg = load_config(path, obs_mode)
    banned = exclusion_hit(cfg, load_exclude(root))
    if banned:
        raise SystemExit(f"任务命中排除列表：{banned}")
    if not entry_allowed(cfg):
        raise SystemExit("entry_url 不在 allow_hosts 里")
    assert_isolation(cfg)
    previous = os.getcwd()
    os.chdir(root)
    try:
        return await _run_episode(cfg, root, policy, headless)
    finally:
        os.chdir(previous)


async def _run_episode(cfg: dict, root: Path, policy: str, headless: bool) -> dict:
    stamp = datetime.now(SHANGHAI).strftime("%Y%m%d_%H%M%S")
    run_dir = root / "runs" / str(cfg["id"]) / str(cfg["obs_mode"]) / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "model_prompt.json").write_text(
        json.dumps({"system": model_prompt(cfg)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "config.snapshot.json").write_text(
        json.dumps(snapshot_config(cfg), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "model_raw.jsonl").write_text("", encoding="utf-8")
    server = LocalServer()
    harness = None
    try:
        server.start(cfg, root, run_dir / "server.log")
        harness = make_harness(cfg, run_dir, headless)
        await harness.start()
        judge_path = root / cfg["judge_path"] if cfg.get("judge_path") else None
        judge = Judge.load(judge_path, cfg["id"], root) if judge_path else Judge(None, cfg["id"], root)
        return await _episode(cfg, harness, judge, make_policy(policy, cfg, run_dir), policy, run_dir)
    finally:
        if harness is not None:
            await harness.close()
        server.stop()


async def _episode(cfg: dict, harness, judge: Judge, policy, policy_name: str, run_dir: Path) -> dict:
    limits = cfg["limits"]
    max_steps = int(limits["max_steps"])
    max_seconds = float(limits["max_seconds"])
    max_submits = int(limits["max_answer_submits"])
    started = time.monotonic()
    ledger = TokenLedger()
    steps_path = run_dir / "steps.jsonl"
    judge_path = run_dir / "judge.jsonl"
    raw_path = run_dir / "model_raw.jsonl"
    ended = "max_steps"
    steps = 0
    submits = 0
    model_obs: dict = {}
    error = ""
    book = cfg.get("notebook") or {}
    notebook_enabled = bool(book.get("enabled", False))
    notebook_limit = int(book.get("max_chars") or 4000)
    notebook = ""

    def budget(done: int) -> dict:
        elapsed = time.monotonic() - started
        return {"steps_left": max(0, max_steps - done), "seconds_left": max(0, int(max_seconds - elapsed))}

    def model_info() -> dict:
        if policy_name == "llm":
            import os

            return {
                "provider": os.environ.get("LLM_PROVIDER") or "openai",
                "name": os.environ.get("OPENAI_MODEL") or os.environ.get("ANTHROPIC_MODEL") or os.environ.get("AGENT_MODEL") or "",
                "temperature": float(os.environ.get("LLM_TEMPERATURE") or 0),
                "preserve_reasoning": (os.environ.get("PRESERVE_REASONING") or "").strip().lower() in {"1", "true", "yes"},
            }
        return {"provider": "script", "name": "scripted", "temperature": 0}

    try:
        await harness.reset()
        harness.consume_step()
        raw = await harness.observe("step_000.png")
        model_obs = pack_observation(raw, cfg, last_result="", budget=budget(0), notebook=notebook)
        _write_json(run_dir / "last_obs.json", model_obs)
        for step in range(1, max_steps + 1):
            if time.monotonic() - started >= max_seconds:
                ended = "max_seconds"
                break
            harness.step = step
            decision_obs = model_obs
            while True:
                try:
                    proposed, early = _propose(policy, decision_obs)
                    break
                except Exception as exc:
                    if not _model_link_down(exc) or time.monotonic() - started >= max_seconds:
                        raise
                    print("模型连接仍中断，20s 后从这一步再试", flush=True)
                    await asyncio.sleep(20)
            reply = str(getattr(policy, "last_raw", "") or "")
            reasoning = str(getattr(policy, "last_reasoning", "") or "")
            step_tokens = _take_usage(policy, ledger, raw_path, step)
            if early:
                action = proposed
                result = early
            else:
                action, failure = normalize(proposed, cfg)
                if failure:
                    action = proposed
                    result = failure
                else:
                    result, notebook = _take_note(action, notebook, notebook_enabled, notebook_limit)
                    if result == "":
                        result = await _apply(action, harness, judge, submits, max_submits)
                        if action.get("op") == "submit_answer" and result != "提交次数已用尽":
                            submits += 1
            state = await judge.read(harness)
            fresh = judge.update(step)
            raw = await harness.observe(f"step_{step:03d}.png")
            model_obs = pack_observation(raw, cfg, last_result=result, budget=budget(step), notebook=notebook)
            if hasattr(policy, "note_result"):
                policy.note_result(decision_obs, action if isinstance(action, dict) else {}, result, reply, reasoning)
            record = {
                "step": step,
                "t": round(time.monotonic() - started, 2),
                "action": action,
                "result": result,
                "obs": obs_summary(model_obs, getattr(harness, "last_screenshot", "")),
                "tokens": step_tokens,
            }
            _append_jsonl(steps_path, record)
            _append_jsonl(
                judge_path,
                {"step": step, "state": state, "new": fresh, "blocked": list(getattr(harness, "blocked", [])), "score": judge.score()},
            )
            _write_json(run_dir / "last_obs.json", model_obs)
            harness.consume_step()
            steps = step
            _print_step({"step": step, "action": action, "result": result})
            if judge.ending_reached or judge.answer_correct:
                ended = "ending"
                break
            if isinstance(action, dict) and action.get("op") == "give_up" and result == "已放弃":
                ended = "give_up"
                break
        else:
            ended = "max_steps"
    except Exception as exc:  # noqa: BLE001
        ended = "error"
        error = str(exc).splitlines()[0][:300]
        raise
    finally:
        score = judge.score()
        summary = build_summary(
            cfg,
            model=model_info(),
            ended_reason=ended,
            steps=steps,
            seconds=time.monotonic() - started,
            score=score,
            blocked=list(getattr(harness, "blocked", [])),
            tokens=ledger.as_dict(),
        )
        if error:
            summary["error"] = error
        status = harness.if_status() if harness is not None else {}
        if status:
            summary["if_score"] = status.get("score")
            summary["if_victory"] = bool(status.get("victory"))
            summary["if_game_over"] = bool(status.get("game_over"))
        if notebook_enabled:
            (run_dir / "notebook.txt").write_text(notebook, encoding="utf-8")
        _write_json(run_dir / "summary.json", summary)
        print(run_dir / "summary.json", flush=True)
    return summary


def _model_link_down(exc: Exception) -> bool:
    try:
        import httpx
    except ImportError:
        return False
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return False


def _propose(policy, obs: dict) -> tuple[dict, str]:
    try:
        proposed = policy.act(obs)
    except ValueError:
        return {"op": "_invalid"}, "动作格式错误"
    except RuntimeError as exc:
        return {"op": "_invalid"}, f"模型请求失败：{exc}"[:180]
    if not isinstance(proposed, dict):
        return {"op": "_invalid"}, "动作格式错误"
    return proposed, ""


def _take_note(action: dict, notebook: str, enabled: bool, limit: int) -> tuple[str, str]:
    if not enabled or action.get("op") != "note":
        return "", notebook
    text = str(action.get("text") or "")
    if len(text) > limit:
        return "笔记超过长度上限", notebook
    return "已记下", text


async def _apply(action: dict, harness, judge: Judge, submits: int, max_submits: int) -> str:
    op = action.get("op")
    if op == "give_up":
        return "已放弃"
    if op == "submit_answer":
        if submits >= max_submits:
            return "提交次数已用尽"
        return judge.check_answer(str(action.get("text") or ""))
    if op == "submit_conclusion":
        return judge.record_conclusion(action.get("object") or {})
    return await harness.act(action)


def _take_usage(policy, ledger: TokenLedger, raw_path: Path, step: int) -> dict:
    usage = getattr(policy, "last_usage", None)
    recorded = {"prompt": 0, "completion": 0}
    if isinstance(usage, dict):
        recorded = {"prompt": int(usage.get("prompt") or 0), "completion": int(usage.get("completion") or 0)}
        if recorded["prompt"] or recorded["completion"]:
            ledger.add(recorded["prompt"], recorded["completion"])
        policy.last_usage = {"prompt": 0, "completion": 0}
    raw = getattr(policy, "last_raw", "")
    if raw:
        _append_jsonl(raw_path, {"step": step, "raw": raw[:32768], "tokens": recorded})
        policy.last_raw = ""
    return recorded


def _print_step(payload: dict) -> None:
    line = json.dumps(payload, ensure_ascii=False)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode(encoding, errors="replace").decode(encoding, errors="replace"), flush=True)


def _append_jsonl(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
