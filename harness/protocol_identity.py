"""Frozen-file identities used to keep benchmark episodes comparable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from harness.protocol_budget import validate_budget


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_sha256(manifest: dict) -> str:
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def expected_profile_sha256(model: dict, evaluation_id: str) -> str:
    """A model can have task-specific observation/history fingerprints."""
    per_task = model.get("task_profile_sha256")
    if per_task is None:
        return model.get("profile_sha256", "")
    if not isinstance(per_task, dict) or evaluation_id not in per_task:
        raise ValueError("模型档案缺少该正式评测 ID 的参数指纹")
    return per_task[evaluation_id]


def validate_identity(manifest: dict, task_id: str, config_path: Path, judge_path: Path, obs_mode: str, cfg: dict) -> dict:
    if not isinstance(manifest.get("id"), str) or not manifest["id"]:
        raise ValueError("冻结清单必须包含 id")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("冻结清单缺少 tasks")
    config_hash, judge_hash = file_sha256(config_path), file_sha256(judge_path)
    matches = [item for item in tasks if isinstance(item, dict) and item.get("task_id", item.get("id")) == task_id]
    if len(matches) > 1:
        matches = [item for item in matches if item.get("config_sha256") == config_hash and item.get("judge_sha256") == judge_hash]
    if len(matches) != 1:
        raise ValueError("任务不在清单中，或同名任务无法按配置和裁判哈希唯一定位")
    item = matches[0]
    if item.get("obs_mode", manifest.get("obs_mode")) != obs_mode:
        raise ValueError("观测档与冻结清单不一致")
    validate_budget(item, cfg)
    if item.get("config_sha256") != config_hash or item.get("judge_sha256") != judge_hash:
        raise ValueError("配置或裁判文件哈希与冻结清单不一致")
    return {"manifest_id": manifest["id"], "manifest_sha256": manifest_sha256(manifest),
            "config_sha256": config_hash, "judge_sha256": judge_hash,
            "evaluation_id": item["id"]}
