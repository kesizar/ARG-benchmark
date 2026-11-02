"""Run a list of task configs one after another."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.batch import run_configs  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="按清单串行评测")
    parser.add_argument("--set", required=True, dest="pilot")
    parser.add_argument("--policy", choices=["script", "llm"], default="script")
    parser.add_argument("--obs-mode", choices=["A", "B", "C"], default=None)
    parser.add_argument("--fixtures", action="store_true", help="跑清单里的 fixtures，而不是正式 tasks")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--run-kind", choices=["test", "official"], default="test", help="正式评测须显式指定 official")
    parser.add_argument("--repeats", type=int, default=None, help="每题重复次数；正式运行默认 3，测试默认 1")
    parser.add_argument("--manifest", help="正式运行的冻结评分清单 JSON")
    args = parser.parse_args()
    if args.fixtures and args.run_kind == "official":
        parser.error("fixtures 不能作为正式评测")
    if args.run_kind == "official" and not args.manifest:
        parser.error("正式运行须提供 --manifest")
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8-sig")) if args.manifest else None
    if manifest and args.repeats is not None and args.repeats != manifest.get("repeats", 3):
        parser.error("重复次数必须与冻结清单一致")
    document = json.loads((ROOT / args.pilot).read_text(encoding="utf-8"))
    key = "fixtures" if args.fixtures else "tasks"
    configs = list(document.get(key) or [])
    if not configs and not args.fixtures:
        configs = list(document.get("configs") or [])
    if not configs:
        raise SystemExit(f"{args.pilot} 里没有 {key}")
    failed = asyncio.run(
        run_configs(configs, policy=args.policy, obs_mode=args.obs_mode, headless=not args.show, repo_root=ROOT, run_kind=args.run_kind,
                    repeats=args.repeats if args.repeats is not None else (manifest.get("repeats", 3) if manifest else 1),
                    manifest=manifest)
    )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
