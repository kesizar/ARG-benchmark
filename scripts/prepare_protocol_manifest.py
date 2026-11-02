"""Create a frozen manifest from an explicit task/model specification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.config import load_config  # noqa: E402
from harness.judge import Judge  # noqa: E402
from harness.protocol_identity import file_sha256, manifest_sha256  # noqa: E402
from harness.protocol_budget import validate_budget  # noqa: E402
from harness.protocol_report import report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="包含 id、obs_mode、models 和任务 config 路径的 JSON")
    parser.add_argument("--out", required=True, help="写入的新清单路径，不覆盖现有文件")
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    tasks = []
    for task in spec.get("tasks", []):
        config_path = (ROOT / task["config"]).resolve()
        cfg = load_config(config_path, spec.get("obs_mode"))
        judge_path = (ROOT / cfg["judge_path"]).resolve()
        judge = Judge.load(judge_path, cfg["id"], ROOT)
        if not judge.available or judge.protocol != "target_v1":
            raise ValueError(f"{cfg.get('id')} 尚未配置 target_v1 裁判")
        validate_budget(task, cfg)
        tasks.append({"id": cfg["id"], "config": task["config"], "config_sha256": file_sha256(config_path),
                      "judge_sha256": file_sha256(judge_path), "progress_scored": task["progress_scored"],
                      "capabilities": task.get("capabilities", []),
                      **{key: task[key] for key in ("reference_steps", "reference_evidence", "max_answer_submits", "required_answer_submits", "answer_budget_evidence") if key in task}})
    manifest = {"id": spec["id"], "obs_mode": spec["obs_mode"], "repeats": spec.get("repeats", 3),
                "required_capabilities": spec["required_capabilities"], "models": spec["models"], "tasks": tasks}
    report(manifest, [])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"{out}\nmanifest_sha256={manifest_sha256(manifest)}")


if __name__ == "__main__":
    main()
