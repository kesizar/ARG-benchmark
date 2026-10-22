"""Episode summary and split aggregate tables."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


SUMMARY_FIELDS = [
    "task_id",
    "category",
    "arg_layer",
    "obs_mode",
    "computer_use",
    "model",
    "ended_reason",
    "steps",
    "seconds",
    "checkpoints_reached",
    "checkpoints_total",
    "progress",
    "route_id",
    "ending_reached",
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
    return {
        "task_id": cfg.get("id"),
        "category": cfg.get("category"),
        "arg_layer": cfg.get("arg_layer"),
        "obs_mode": cfg.get("obs_mode"),
        "computer_use": bool(cfg.get("computer_use")),
        "model": model,
        "ended_reason": ended_reason,
        "steps": steps,
        "seconds": round(seconds, 2),
        "checkpoints_reached": score.get("checkpoints_reached", 0),
        "checkpoints_total": score.get("checkpoints_total", 0),
        "progress": score.get("route_progress") if "route_progress" in score else _progress(score.get("checkpoints_reached", 0), score.get("checkpoints_total", 0)),
        "route_id": score.get("route_id"),
        "ending_reached": bool(score.get("ending_reached")),
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
    if "route_progress" in item:
        value = item.get("route_progress")
        if value is None or value == "":
            return None
        return float(value)
    total = int(item.get("checkpoints_total") or 0)
    if total <= 0:
        return None
    return int(item.get("checkpoints_reached") or 0) / total


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
    return data


def aggregate(runs_root: Path) -> list[dict]:
    """Group finished episodes. ARG layers stay on separate rows."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for path in sorted(Path(runs_root).glob("*/*/*/summary.json")):
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        model = summary.get("model") or {}
        key = (
            summary.get("category"),
            summary.get("arg_layer"),
            summary.get("obs_mode"),
            model.get("name"),
        )
        groups[key].append(summary)
    rows = []
    for key, items in groups.items():
        reached = sum(int(item.get("checkpoints_reached") or 0) for item in items)
        total = sum(int(item.get("checkpoints_total") or 0) for item in items)
        endings = sum(1 for item in items if item.get("ending_reached"))
        good_endings = sum(1 for item in items if item.get("good_ending"))
        progressed = [value for value in (_episode_progress(item) for item in items) if value is not None]
        mean_progress = ""
        if progressed:
            mean_progress = round(sum(progressed) / len(progressed), 4)
        steps = sum(int(item.get("steps") or 0) for item in items)
        tokens = sum(int((item.get("tokens") or {}).get("total") or 0) for item in items)
        rows.append(
            {
                "category": key[0],
                "arg_layer": key[1] if key[1] is not None else "",
                "obs_mode": key[2],
                "model": key[3],
                "runs": len(items),
                "checkpoints_reached": reached,
                "checkpoints_total": total,
                "endings": endings,
                "endings_rate": round(endings / len(items), 4),
                "good_endings": good_endings,
                "good_endings_rate": round(good_endings / len(items), 4),
                "mean_progress": mean_progress,
                "steps": steps,
                "tokens_total": tokens,
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "category",
        "arg_layer",
        "obs_mode",
        "model",
        "runs",
        "checkpoints_reached",
        "checkpoints_total",
        "endings",
        "endings_rate",
        "good_endings",
        "good_endings_rate",
        "mean_progress",
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
        "arg_layer",
        "obs_mode",
        "model",
        "runs",
        "checkpoints_reached",
        "checkpoints_total",
        "endings",
        "endings_rate",
        "good_endings",
        "good_endings_rate",
        "mean_progress",
        "steps",
        "tokens_total",
    ]
    lines = [
        "# 评测汇总",
        "",
        "ARG 的 L1、L2、L3 分列，这里没有合并成一个总分。",
        "",
        "| " + " | ".join(fields) + " |",
        "| " + " | ".join("---" for _ in fields) + " |",
    ]
    for row in rows:
        cells = [str(row.get(field, "")) for field in fields]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
