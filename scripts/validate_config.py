"""Validate one task config. Exit 0 when it passes, 1 otherwise."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.validate import validate_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="校验任务配置")
    parser.add_argument("config")
    args = parser.parse_args()
    errors = validate_file(Path(args.config), ROOT)
    if errors:
        for item in errors:
            print(item)
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
