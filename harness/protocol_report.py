"""Target-v1 per-task reporting against an explicit frozen manifest."""

from __future__ import annotations

from collections import defaultdict
from math import comb, prod
import re

from harness.summary import _exclusion_reason
from harness.protocol_identity import manifest_sha256, expected_profile_sha256


def _good_observed(row: dict) -> bool:
    """An unranked or contradictory ending is unknown, never a negative."""
    good = row.get("good_ending")
    reached = row.get("ending_reached")
    if type(good) is not bool or type(reached) is not bool:
        return False
    if not reached:
        return not good
    tier = row.get("ending_tier")
    return isinstance(tier, str) and tier in {"good", "normal", "bad"} and good == (tier == "good")


def report(manifest: dict, summaries: list[dict]) -> dict:
    tasks = manifest.get("tasks")
    repeats = manifest.get("repeats", 3)
    if not isinstance(manifest.get("id"), str) or not manifest["id"] or manifest.get("obs_mode") not in {"A", "B", "C"}:
        raise ValueError("清单必须指定非空 id 和观测档")
    if not isinstance(tasks, list) or not tasks or type(repeats) is not int or repeats < 3:
        raise ValueError("清单必须指定非空 tasks 及至少三次重复")
    if not all(isinstance(t, dict) and isinstance(t.get("id"), str) and t["id"] for t in tasks):
        raise ValueError("每题必须提供非空字符串 id")
    by_id = {t["id"]: t for t in tasks}
    if len(by_id) != len(tasks):
        raise ValueError("题目 id 重复")
    if any(type(t.get("progress_scored")) is not bool for t in tasks):
        raise ValueError("每题必须明确 progress_scored")
    for t in tasks:
        if t.get("obs_mode", manifest["obs_mode"]) not in {"A", "B", "C"}:
            raise ValueError("逐题观察档必须为 A、B 或 C")
        for key in ("good_ending_scored", "terminal_failure_scored"):
            if key in t and type(t[key]) is not bool:
                raise ValueError(f"{key} 必须为布尔值")
    if any(not isinstance(t.get(k), str) or not re.fullmatch(r"[0-9a-f]{64}", t[k]) for t in tasks for k in ("config_sha256", "judge_sha256")):
        raise ValueError("每题必须包含配置和裁判 SHA-256")
    expected_models = manifest.get("models")
    if not isinstance(expected_models, list) or not expected_models or any(
        not isinstance(m, dict) or any(not isinstance(m.get(k), str) or not m[k] for k in ("provider", "name", "profile_id", "profile_sha256"))
        or not re.fullmatch(r"[0-9a-f]{64}", m.get("profile_sha256", ""))
        for m in expected_models
    ):
        raise ValueError("清单必须明确每个模型、服务商和参数档案")
    expected = {(m["provider"], m["name"], m["profile_id"]) for m in expected_models}
    model_specs = {(m["provider"], m["name"], m["profile_id"]): m for m in expected_models}
    if len(expected) != len(expected_models):
        raise ValueError("模型和参数档案重复")
    for model in expected_models:
        if "task_profile_sha256" in model:
            profiles = model["task_profile_sha256"]
            if not isinstance(profiles, dict) or set(profiles) != set(by_id) or any(
                    not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in profiles.values()):
                raise ValueError("逐题模型档案必须完整且包含合法 SHA-256")
    for t in tasks:
        if not isinstance(t.get("capabilities", []), list) or not all(
            isinstance(a, str) and a for a in t.get("capabilities", [])
        ) or len(set(t.get("capabilities", []))) != len(t.get("capabilities", [])):
            raise ValueError("capabilities 必须为无重复的非空字符串列表")
    groups = {key: defaultdict(list) for key in expected}
    seen_ids = set()
    excluded = []
    for row in summaries:
        identity = row.get("protocol_identity") or {}
        evaluation_id = identity.get("evaluation_id", row.get("task_id"))
        reason = _exclusion_reason(row)
        if not reason and row.get("scoring_protocol") != "target_v1":
            reason = "incompatible_scoring_protocol"
        if not reason and type(row.get("target_success")) is not bool:
            reason = "missing_target_success"
        if not reason and evaluation_id not in by_id:
            reason = "outside_manifest"
        task = by_id.get(evaluation_id, {})
        if not reason and row.get("obs_mode") != task.get("obs_mode", manifest.get("obs_mode")):
            reason = "observation_mismatch"
        if not reason and (identity.get("manifest_id") != manifest["id"] or identity.get("manifest_sha256") != manifest_sha256(manifest)):
            reason = "manifest_mismatch"
        if not reason and (identity.get("config_sha256") != task.get("config_sha256") or identity.get("judge_sha256") != task.get("judge_sha256")):
            reason = "version_mismatch"
        if not reason and (not isinstance(identity.get("run_id"), str) or not identity["run_id"] or
                           type(identity.get("repetition")) is not int or not 1 <= identity["repetition"] <= repeats or
                           type(identity.get("attempt")) is not int or not 1 <= identity["attempt"] <= 3):
            reason = "invalid_run_identity"
        model = row.get("model") or {}
        key = (model.get("provider"), model.get("name"), identity.get("profile_id"))
        if not reason and key not in expected:
            reason = "model_profile_mismatch"
        if not reason and identity.get("profile_sha256") != expected_profile_sha256(model_specs[key], evaluation_id):
            reason = "model_profile_hash_mismatch"
        if reason:
            excluded.append({"task_id": row.get("task_id"), "reason": reason})
            continue
        if identity["run_id"] in seen_ids:
            raise ValueError("重复 run_id，拒绝重复计分")
        seen_ids.add(identity["run_id"])
        if any(x["protocol_identity"]["repetition"] == identity["repetition"] for x in groups[key][evaluation_id]):
            raise ValueError("同一模型、题目和重复局存在多个有效结果，禁止自动挑选")
        groups[key][evaluation_id].append(row)
    models = []
    for (provider, model, profile_id), per_task in sorted(groups.items()):
        detail = []
        for t in tasks:
            episodes = per_task.get(t["id"], [])
            if len(episodes) > repeats:
                raise ValueError(f"{provider}/{model}/{t['id']} 的有效局超过计划次数，禁止自动挑选")
            n = len(episodes)
            c = sum(x["target_success"] for x in episodes)
            complete = n == repeats
            progresses = [x.get("progress") for x in episodes]
            valid_progress = all(type(x) in (int, float) and 0 <= x <= 1 for x in progresses)
            good_values = [x.get("good_ending") for x in episodes]
            # Missing/untiered endings are unknown, not evidence of a bad ending.
            good_valid = all(_good_observed(x) for x in episodes)
            failures = [x.get("failure_reached") for x in episodes]
            failure_valid = all(type(x) is bool for x in failures)
            detail.append({
                "task_id": t["id"], "valid_runs": n, "planned_runs": repeats,
                "successes": c, "sr": c / n if complete else None,
                "progress": sum(progresses) / n if complete and t["progress_scored"] and valid_progress else None,
                "pass3": comb(c, 3) / comb(n, 3) if complete else None,
                "good_ending_scored": t.get("good_ending_scored", False),
                "good_ending_observed_runs": sum(_good_observed(x) for x in episodes),
                "good_ending_rate": sum(good_values) / n if complete and t.get("good_ending_scored") is True and good_valid else None,
                "terminal_failure_scored": t.get("terminal_failure_scored", False),
                "terminal_failure_observed_runs": sum(type(x) is bool for x in failures),
                "terminal_failure_rate": sum(failures) / n if complete and t.get("terminal_failure_scored") is True and failure_valid else None,
            })
        complete = all(x["sr"] is not None for x in detail)
        progress_rows = [x for x in detail if by_id[x["task_id"]]["progress_scored"]]
        progress_complete = bool(progress_rows) and all(x["progress"] is not None for x in progress_rows)
        good_rows = [x for x in detail if x["good_ending_scored"]]
        failure_rows = [x for x in detail if x["terminal_failure_scored"]]
        good_complete = bool(good_rows) and all(x["good_ending_rate"] is not None for x in good_rows)
        failure_complete = bool(failure_rows) and all(x["terminal_failure_rate"] is not None for x in failure_rows)
        caps = manifest.get("required_capabilities")
        if not isinstance(caps, list) or not all(isinstance(a, str) and a for a in caps) or len(set(caps)) != len(caps):
            raise ValueError("清单必须明确 required_capabilities")
        sub = {}
        for cap in caps:
            subset = [x for x in detail if cap in by_id[x["task_id"]].get("capabilities", [])]
            sub[cap] = {"tasks": len(subset), "sr": sum(x["sr"] for x in subset) / len(subset)
                        if subset and all(x["sr"] is not None for x in subset) else None}
        models.append({
            "provider": provider, "model": model, "profile_id": profile_id, "complete": complete,
            "tasks": len(tasks), "completed_tasks": sum(x["sr"] is not None for x in detail),
            "sr_macro": sum(x["sr"] for x in detail) / len(detail) if complete else None,
            "progress_tasks": len(progress_rows),
            "progress_macro": sum(x["progress"] for x in progress_rows) / len(progress_rows) if progress_complete else None,
            "pass3_macro": sum(x["pass3"] for x in detail) / len(detail) if complete else None,
            "good_ending_tasks": len(good_rows),
            "good_ending_completed_tasks": sum(x["good_ending_rate"] is not None for x in good_rows),
            "good_ending_rate_macro": sum(x["good_ending_rate"] for x in good_rows) / len(good_rows) if good_complete else None,
            "terminal_failure_tasks": len(failure_rows),
            "terminal_failure_completed_tasks": sum(x["terminal_failure_rate"] is not None for x in failure_rows),
            "terminal_failure_rate_macro": sum(x["terminal_failure_rate"] for x in failure_rows) / len(failure_rows) if failure_complete else None,
            "capabilities": sub,
            "balance": prod(v["sr"] for v in sub.values()) ** (1 / len(sub))
                       if sub and all(v["sr"] is not None for v in sub.values()) else None,
            "per_task": detail,
        })
    return {"manifest_id": manifest.get("id"), "obs_mode": manifest.get("obs_mode"),
            "task_observation_modes": {t["id"]: t.get("obs_mode", manifest.get("obs_mode")) for t in tasks},
            "repeats": repeats, "models": models, "excluded": excluded}
