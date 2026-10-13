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
    args = parser.parse_args()
    document = json.loads((ROOT / args.pilot).read_text(encoding="utf-8"))
    key = "fixtures" if args.fixtures else "tasks"
    configs = list(document.get(key) or [])
    if not configs and not args.fixtures:
        configs = list(document.get("configs") or [])
    if not configs:
        raise SystemExit(f"{args.pilot} 里没有 {key}")
    failed = asyncio.run(
        run_configs(configs, policy=args.policy, obs_mode=args.obs_mode, headless=not args.show, repo_root=ROOT)
    )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
