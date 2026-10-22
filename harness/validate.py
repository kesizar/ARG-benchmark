"""Check a task config against the schema, the exclude list, and judge path."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from harness.config import entry_allowed, exclusion_hit, load_config, load_exclude
from harness.network import allow_rule_problem, is_local_host, rule_host


def validate_file(path: Path, root: Path | None = None) -> list[str]:
    root = root or Path(path).resolve().parents[1]
    errors: list[str] = []
    schema_path = root / "configs" / "schema" / "task.schema.json"
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"JSON 无法解析：{exc}"]
    try:
        import jsonschema
    except ImportError:
        errors.append("未安装 jsonschema")
    else:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for item in sorted(validator.iter_errors(document), key=lambda err: list(err.path)):
            place = "/".join(str(part) for part in item.path) or "(root)"
            errors.append(f"{place}: {item.message}")
    try:
        cfg = load_config(path)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        return errors
    banned = exclusion_hit(cfg, load_exclude(root))
    if banned:
        errors.append(f"命中排除列表：{banned}")
    judge_path = cfg.get("judge_path")
    if not judge_path or not (root / judge_path).is_file():
        errors.append(f"裁判文件不存在：{judge_path}")
    if not entry_allowed(cfg):
        errors.append("entry_url 不在 allow_hosts 里")
    errors.extend(l3_problems(cfg))
    return errors


def l3_problems(cfg: dict) -> list[str]:
    """L3 is a live site on an explicit host list. Reject a config that is still local."""
    if cfg.get("category") != "arg" or cfg.get("arg_layer") != "L3":
        return []
    errors: list[str] = []
    if (cfg.get("local_serve") or {}).get("enabled"):
        errors.append("L3 不能启用本地服务")
    if (cfg.get("isolation") or {}).get("container"):
        errors.append("L3 不能启用容器隔离")
    entry = str(cfg.get("entry_url") or "")
    parsed = urlparse(entry)
    if parsed.scheme != "https":
        errors.append("L3 的入口必须是 https 网址")
    elif is_local_host(rule_host(parsed.hostname or "")):
        errors.append("L3 的入口不能是本机地址")
    hosts = [str(item) for item in (cfg.get("allow_hosts") or [])]
    if not hosts:
        errors.append("L3 的 allow_hosts 不能为空")
    guide_patterns = cfg.get("guide_block_hosts")
    for rule in hosts:
        reason = allow_rule_problem(rule, guide_patterns)
        if reason:
            errors.append(f"L3 的白名单不能包含{reason}：{rule}")
    return errors
