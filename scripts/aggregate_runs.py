"""Write a split table. ARG L1/L2/L3 stay on separate rows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.summary import aggregate, write_csv, write_markdown  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="汇总 runs，ARG 分层分列")
    parser.add_argument("--runs", default="runs")
    parser.add_argument("--out", default="runs/aggregate.csv")
    args = parser.parse_args()
    rows = aggregate(ROOT / args.runs)
    out = ROOT / args.out
    write_csv(rows, out)
    markdown = out.with_suffix(".md")
    write_markdown(rows, markdown)
    print(out)
    print(markdown)
    for row in rows:
        print(
            f"{row['category']}\t{row['arg_layer']}\t{row['obs_mode']}\t{row['model']}\t"
            f"runs={row['runs']}\tendings={row['endings']}"
        )


if __name__ == "__main__":
    main()
