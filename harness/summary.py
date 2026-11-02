"""Episode summary and split aggregate tables."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from harness.config import resolve_runtime_layer


SUMMARY_FIELDS = [
    "task_id",
    "category",
    "runtime_layer",
    "obs_mode",
    "computer_use",
    "model",
    "ended_reason",
    "steps",
    "seconds",
    "checkpoints_reached",
    "checkpoints_total",
    "progress",
    "route_progress",
    "reasoning_progress",
    "answer_correct",
    "route_id",
    "ending_reached",
    "failure_reached",
    "failure_id",
    "failure_step",
    "ending_tier",
    "good_ending",
    "events",
    "blocked_requests",
    "blocked_hosts",
    "shortcut_blocks",
    "tokens",
    "history_k",
    "notebook_enabled",
    "notes_for_report",
]


def build_summary(cfg: dict, *, model: dict, ended_reason: str, steps: int, seconds: float, score: dict, blocked: list[dict], tokens: dict) -> dict:
    hosts = []
    shortcuts = []
    for item in blocked:
        if item.get("why") == "shortcut":
            shortcuts.append(item.get("rule"))
        host = item.get("host")
        if host and host not in hosts:
            hosts.append(host)
    protocol = score.get("scoring_protocol", "legacy")
    route_progress = score.get("route_progress")
    total = score.get("checkpoints_total", 0)
    answer_correct = bool(score.get("answer_correct"))
    reasoning_progress = _progress(score.get("checkpoints_reached", 0), total)
    if reasoning_progress is None and answer_correct:
        reasoning_progress = 1.0
    progress = route_progress if "route_progress" in score else reasoning_progress
    if protocol != "target_v1" and int(total or 0) <= 0 and not answer_correct:
        progress = None
    return {
        "task_id": cfg.get("id"),
        "category": cfg.get("category"),
        "runtime_layer": resolve_runtime_layer(cfg),
        "obs_mode": cfg.get("obs_mode"),
        "computer_use": bool(cfg.get("computer_use")),
        "model": model,
        "ended_reason": ended_reason,
        "steps": steps,
        "seconds": round(seconds, 2),
        "checkpoints_reached": score.get("checkpoints_reached", 0),
        "checkpoints_total": score.get("checkpoints_total", 0),
        "progress": progress,
        "route_progress": route_progress,
        "reasoning_progress": reasoning_progress,
        "answer_correct": answer_correct,
        "route_id": score.get("route_id"),
        "scoring_protocol": score.get("scoring_protocol", "legacy"),
        "target_success": score.get("target_success"),
        "ending_reached": bool(score.get("ending_reached")),
        "failure_reached": bool(score.get("failure_reached")),
        "failure_id": score.get("failure_id"),
        "failure_step": score.get("failure_step"),
        "ending_tier": score.get("ending_tier"),
        "good_ending": bool(score.get("good_ending")),
        "events": [item.get("id") for item in score.get("events") or []],
        "blocked_requests": len(blocked),
        "blocked_hosts": hosts,
        "shortcut_blocks": shortcuts,
        "tokens": tokens,
        "history_k": (cfg.get("history") or {}).get("full_obs_k", 4),
        "notebook_enabled": bool((cfg.get("notebook") or {}).get("enabled", False)),
        "notes_for_report": list(cfg.get("notes_for_report") or []),
    }


def _episode_progress(item: dict) -> float | None:
    # Old summaries can contain route completion 1.0 with zero critical gates.
    # Missing totals are unknown, not evidence of a scored denominator.
    if (item.get("scoring_protocol", "legacy") != "target_v1"
            and (item.get("checkpoints_total") is None or int(item["checkpoints_total"]) <= 0)
            and not item.get("answer_correct")):
        return None
    if "progress" in item or "route_progress" in item:
        value = item.get("progress") if "progress" in item else item.get("route_progress")
        if value is None or value == "":
            return None
        return float(value)
    total = int(item.get("checkpoints_total") or 0)
    if total <= 0:
        return None
    return int(item.get("checkpoints_reached") or 0) / total


def _episode_reasoning_progress(item: dict) -> float | None:
    if "reasoning_progress" in item:
        value = item["reasoning_progress"]
        return None if value is None or value == "" else float(value)
    total = item.get("checkpoints_total")
    if total is not None and int(total) > 0:
        return _progress(item.get("checkpoints_reached", 0), total)
    return 1.0 if item.get("answer_correct") is True else None


def _progress(reached: int, total: int) -> float | None:
    if int(total or 0) <= 0:
        return None
    return round(int(reached or 0) / int(total), 4)


def snapshot_config(cfg: dict) -> dict:
    data = json.loads(json.dumps(cfg))
    data.pop("hooks", None)
    data.pop("checkpoints", None)
    data.pop("ending", None)
    data.pop("events", None)
    data.pop("terminal_failures", None)
    return data


def aggregate(runs_root: Path, *, official_only: bool = False, exclusions: list[dict] | None = None) -> list[dict]:
    """Group finished episodes. Runtime layers stay on separate rows; old reports retain their historical labels."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    paths = sorted(Path(runs_root).glob("*/*/*/summary.json"))
    if official_only and exclusions is not None:
        for directory in sorted(Path(runs_root).glob("*/*/*")):
            if directory.is_dir() and not (directory / "summary.json").is_file():
                exclusions.append({"path": str(directory), "reason": "missing_summary"})
    for path in paths:
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError, OSError):
            if exclusions is not None:
                exclusions.append({"path": str(path), "reason": "unreadable_summary"})
            continue
        if not isinstance(summary, dict):
            if exclusions is not None:
                exclusions.append({"path": str(path), "reason": "invalid_summary"})
            continue
        if official_only:
            reason = _exclusion_reason(summary)
            if reason:
                if exclusions is not None:
                    exclusions.append({"path": str(path), "reason": reason})
                continue
        model = summary.get("model") or {}
        key = (
            summary.get("category"),
            summary.get("runtime_layer", summary.get("arg_layer")),
            summary.get("obs_mode"),
            model.get("name"),
            summary.get("scoring_protocol", "legacy"),
        )
        groups[key].append(summary)
    rows = []
    for key, items in groups.items():
        reached = sum(int(item.get("checkpoints_reached") or 0) for item in items)
        total = sum(int(item.get("checkpoints_total") or 0) for item in items)
        endings = sum(1 for item in items if item.get("ending_reached"))
        failure_observed = [item for item in items if "failure_reached" in item]
        failures = sum(1 for item in failure_observed if item.get("failure_reached"))
        good_endings = sum(1 for item in items if item.get("good_ending"))
        progressed = [value for value in (_episode_progress(item) for item in items) if value is not None]
        reasoning = [value for value in (_episode_reasoning_progress(item) for item in items) if value is not None]
        mean_progress = ""
        if progressed:
            mean_progress = round(sum(progressed) / len(progressed), 4)
        steps = sum(int(item.get("steps") or 0) for item in items)
        tokens = sum(int((item.get("tokens") or {}).get("total") or 0) for item in items)
        rows.append(
            {
                "category": key[0],
                "runtime_layer": key[1] if key[1] is not None else "",
                "obs_mode": key[2],
                "model": key[3],
                "scoring_protocol": key[4],
                "runs": len(items),
                "checkpoints_reached": reached,
                "checkpoints_total": total,
                "endings": endings,
                "endings_rate": round(endings / len(items), 4),
                "failure_observed_runs": len(failure_observed),
                "failures": failures,
                "failure_rate": round(failures / len(failure_observed), 4) if failure_observed else "",
                "good_endings": good_endings,
                "good_endings_rate": round(good_endings / len(items), 4),
                "mean_progress": mean_progress,
                "progress_observed_runs": len(progressed),
                "mean_reasoning_progress": round(sum(reasoning) / len(reasoning), 4) if reasoning else "",
                "reasoning_observed_runs": len(reasoning),
                "steps": steps,
                "tokens_total": tokens,
            }
        )
    return rows


def _exclusion_reason(summary: dict) -> str | None:
    if summary.get("run_kind") != "official":
        return "test_run" if summary.get("run_kind") == "test" else "unclassified_run"
    if (summary.get("model") or {}).get("provider") in (None, "", "script"):
        return "invalid_model"
    if summary.get("ended_reason") == "error":
        return "runtime_error"
    if summary.get("ended_reason") not in {"ending", "target_success", "failure", "give_up", "max_steps", "max_seconds"}:
        return "unknown_end_reason"
    if "judge_error" not in summary:
        return "unknown_judge_status"
    if summary.get("judge_error"):
        return "judge_error"
    return None


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "category",
        "runtime_layer",
        "obs_mode",
        "model",
        "scoring_protocol",
        "runs",
        "checkpoints_reached",
        "checkpoints_total",
        "endings",
        "endings_rate",
        "failure_observed_runs",
        "failures",
        "failure_rate",
        "good_endings",
        "good_endings_rate",
        "mean_progress",
        "progress_observed_runs",
        "mean_reasoning_progress",
        "reasoning_observed_runs",
        "steps",
        "tokens_total",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "category",
        "runtime_layer",
        "obs_mode",
        "model",
        "scoring_protocol",
        "runs",
        "checkpoints_reached",
        "checkpoints_total",
        "endings",
        "endings_rate",
        "failure_observed_runs",
        "failures",
        "failure_rate",
        "good_endings",
        "good_endings_rate",
        "mean_progress",
        "progress_observed_runs",
        "mean_reasoning_progress",
        "reasoning_observed_runs",
        "steps",
        "tokens_total",
    ]
    lines = [
        "# 评测汇总",
        "",
        "按游戏类别、运行层级、观测模式和模型分列；历史 L2 标签保持原样。",
        "",
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        cells = [str(row.get(field, "")) for field in fields]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
