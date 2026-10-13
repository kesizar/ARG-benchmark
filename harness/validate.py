"""Check a task config against the schema, the exclude list, and judge path."""

from __future__ import annotations

import json
from pathlib import Path

from harness.config import entry_allowed, exclusion_hit, load_config, load_exclude


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
    return errors
