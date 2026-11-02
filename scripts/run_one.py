"""Run one episode.

    python scripts/run_one.py --config configs/involuntary-appetite.json --policy script --obs-mode B
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.loop import run  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="跑一局解谜评测")
    parser.add_argument("--config", required=True)
    parser.add_argument("--policy", choices=["script", "llm"], default="script")
    parser.add_argument("--obs-mode", choices=["A", "B", "C"], default=None)
    parser.add_argument("--show", action="store_true", help="打开可见浏览器")
    parser.add_argument("--run-kind", choices=["test", "official"], default="test", help="正式评测须显式指定 official")
    parser.add_argument("--manifest", help="正式运行的冻结评分清单")
    parser.add_argument("--repetition", type=int, help="正式运行的重复局编号，从 1 开始")
    parser.add_argument("--attempt", type=int, default=1, help="同一局的重跑序号，从 1 开始")
    args = parser.parse_args()
    if args.run_kind == "official" and (not args.manifest or args.repetition is None):
        parser.error("正式运行须提供 --manifest 和 --repetition")
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8-sig")) if args.manifest else None
    try:
        summary = asyncio.run(
            run(
                args.config,
                policy=args.policy,
                obs_mode=args.obs_mode,
                headless=not args.show,
                repo_root=ROOT,
                run_kind=args.run_kind,
                manifest=manifest,
                repetition=args.repetition,
                attempt=args.attempt,
            )
        )
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(exc)
            raise SystemExit(1) from exc
        raise
    if summary.get("ended_reason") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
