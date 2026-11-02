"""Write a split table. Runtime layers stay on separate rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.summary import aggregate, write_csv, write_markdown  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="汇总 runs，按类别与运行层级分列")
    parser.add_argument("--runs", default="runs")
    parser.add_argument("--out", default="runs/aggregate.csv")
    args = parser.parse_args()
    exclusions = []
    rows = aggregate(ROOT / args.runs, official_only=True, exclusions=exclusions)
    out = ROOT / args.out
    write_csv(rows, out)
    markdown = out.with_suffix(".md")
    write_markdown(rows, markdown)
    excluded_path = out.with_suffix(".excluded.json")
    excluded_path.write_text(json.dumps(exclusions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    print(markdown)
    print(f"排除记录 {len(exclusions)}: {excluded_path}")
    for row in rows:
        print(
            f"{row['category']}\t{row['runtime_layer']}\t{row['obs_mode']}\t{row['model']}\t"
            f"runs={row['runs']}\tendings={row['endings']}"
        )


if __name__ == "__main__":
    main()
