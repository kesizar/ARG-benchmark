"""Scaffold a task. Fill in the mirror or story file before a real run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.scaffold import scaffold_task  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="生成一道题的配置、裁判和目录")
    parser.add_argument("--id", required=True)
    parser.add_argument("--category", required=True, choices=["web_puzzle", "escape_room", "arg", "static", "text_adventure"])
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--runtime-layer", "--layer", choices=["L1", "L3"], default="L1")
    args = parser.parse_args()
    written = scaffold_task(ROOT, args.id, args.category, port=args.port, runtime_layer=args.runtime_layer)
    for path in written:
        print(path.relative_to(ROOT))
    print("下一步：换上真题材料，再执行")
    print(f"  python scripts/validate_config.py configs/{args.id}.json")
    print(f"  python scripts/run_one.py --config configs/{args.id}.json --policy script")


if __name__ == "__main__":
    main()
