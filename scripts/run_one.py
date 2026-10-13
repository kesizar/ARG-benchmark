"""Run one episode.

    python scripts/run_one.py --config configs/involuntary-appetite.json --policy script --obs-mode B
"""

from __future__ import annotations

import argparse
import asyncio
import logging
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
    args = parser.parse_args()
    try:
        summary = asyncio.run(
            run(
                args.config,
                policy=args.policy,
                obs_mode=args.obs_mode,
                headless=not args.show,
                repo_root=ROOT,
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
