"""Create the files a new task needs. Puzzle content is filled in afterwards."""

from __future__ import annotations

import json
import re
from pathlib import Path

from harness.network import GUIDE_HOSTS

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def scaffold_task(root: Path, task_id: str, category: str, *, port: int = 8770, runtime_layer: str = "L1") -> list[Path]:
    if not _SLUG.match(task_id):
        raise ValueError("任务 id 只能用小写字母、数字和连字符")
    if category not in {"web_puzzle", "escape_room", "arg", "static", "text_adventure"}:
        raise ValueError(f"不支持的类别 {category}")
    if runtime_layer not in {"L1", "L3"}:
        raise ValueError("运行层级必须是 L1 或 L3")
    if runtime_layer == "L3" and category in {"static", "text_adventure"}:
        raise ValueError("当前静态题和解释器模板仅支持本地 L1")
    root = Path(root)
    config_path = root / "configs" / f"{task_id}.json"
    if config_path.exists():
        raise FileExistsError(f"已经有配置 {config_path}")
    judge = {
        "hooks": {},
        "checkpoints": [],
        "events": {},
        "ending": None,
        "answer_hash_file": None,
        "request_milestones": [],
        "submit_conclusion": {"enabled": False, "schema": None},
        "rubric_path": None,
    }
    cfg: dict = {
        "id": task_id,
        "category": category,
        "runtime_layer": runtime_layer,
        "account_requirement": "unknown",
        "obs_mode": "A" if category in {"static", "text_adventure"} else "B",
        "computer_use": False,
        "model_visible": {
            "title": task_id,
            "intro": "在这里写给模型看的题面。不要写裁判钩子、答案或攻略。",
        },
        "allow_model_goto": False,
        "goto_scope": "none",
        "actions_enabled": ["give_up"],
        "limits": {"max_steps": 40, "max_seconds": 900, "max_answer_submits": 5},
        "history": {"full_obs_k": 4, "screenshot_k": 2},
        "judge_path": f"judge/{task_id}/judge.json",
        "policy_script": [{"op": "give_up"}],
        "notes_for_report": ["由 new_task 生成，题面和裁判钩子尚未填写"],
        "isolation": {"container": False},
    }
    written = [config_path, root / "judge" / task_id / "judge.json", root / "tasks" / task_id / "README.md"]
    task_dir = root / "tasks" / task_id
    if category in {"web_puzzle", "escape_room", "arg"}:
        cfg["entry_url"] = f"http://127.0.0.1:{port}/"
        cfg["allow_hosts"] = [f"127.0.0.1:{port}"]
        cfg["local_serve"] = {
            "enabled": True,
            "command": ["python", "scripts/serve_static.py", "--root", f"tasks/{task_id}/mirror", "--port", str(port)],
            "cwd": ".",
            "ready_url": f"http://127.0.0.1:{port}/",
            "ready_timeout_s": 30,
            "port": port,
        }
        cfg["settle_ms"] = 400
        cfg["actions_enabled"] = ["click", "type", "key", "scroll", "back", "wait", "give_up"]
        cfg["shortcut_block"] = []
        cfg["guide_block_hosts"] = list(GUIDE_HOSTS) if runtime_layer == "L3" else []
        judge["hooks"] = {"on_entry": {"type": "url_regex", "pattern": rf"127\\.0\\.0\\.1:{port}/"}}
        judge["checkpoints"] = [{"id": "entered", "hook": "on_entry", "op": "truthy"}]
        mirror = task_dir / "mirror"
        page = mirror / "index.html"
        if runtime_layer == "L1":
            written.extend([task_dir / "serve.json", page])
            _write(page, _placeholder_page(task_id))
            _write(
                task_dir / "serve.json",
                json.dumps({"command": cfg["local_serve"]["command"], "cwd": ".", "ready_url": cfg["entry_url"], "port": port}, ensure_ascii=False, indent=2) + "\n",
            )
        if runtime_layer == "L3":
            # Explicitly incomplete online template; never silently call a
            # locally served placeholder an online game.
            cfg["entry_url"] = "https://replace-with-game-host.invalid/"
            cfg["allow_hosts"] = ["replace-with-game-host.invalid"]
            cfg["local_serve"] = {"enabled": False}
            judge["hooks"] = {}
            judge["checkpoints"] = []
    elif category == "text_adventure":
        cfg["entry_url"] = None
        cfg["local_serve"] = {"enabled": False}
        cfg["actions_enabled"] = ["type", "give_up"]
        cfg["if"] = {"story_file": f"tasks/{task_id}/story.z8", "interpreter": "jericho", "max_command_chars": 200}
        cfg["policy_script"] = [{"op": "type", "text": "look"}, {"op": "give_up"}]
        judge["hooks"] = {
            "score": {"type": "if_score"},
            "victory": {"type": "if_victory"},
        }
        judge["checkpoints"] = []
        judge["events"] = {"scored": {"hook": "score", "op": "gte", "value": 1}}
        judge["ending"] = {"hook": "victory", "op": "truthy"}
        written.append(task_dir / "README.md")
    else:
        cfg["entry_url"] = None
        cfg["local_serve"] = {"enabled": False}
        cfg["actions_enabled"] = ["submit_answer", "give_up"]
        cfg["static"] = {"prompt": "在这里写静态题面。"}
        cfg["model_visible"]["intro"] = "根据题面提交答案。"
    _write(config_path, json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    _write(root / "judge" / task_id / "judge.json", json.dumps(judge, ensure_ascii=False, indent=2) + "\n")
    _write(task_dir / "README.md", f"# {task_id}\n\n把真题材料放在这个目录。模型只能看到配置里的 model_visible。裁判只放在 judge/{task_id}/。\n")
    return written


def _placeholder_page(task_id: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>{task_id}</title></head>
<body>
<h1>{task_id}</h1>
<p>用作品镜像替换 tasks/{task_id}/mirror 里的文件。</p>
</body>
</html>
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
