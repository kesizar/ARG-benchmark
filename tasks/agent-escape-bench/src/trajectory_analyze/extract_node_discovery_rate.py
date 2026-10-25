#!/usr/bin/env python3
"""
从 metrics 结果文件夹中提取所有模型、所有难度的 node_discovery_rate 平均值。

用法:
    python extract_node_discovery_rate.py <metrics结果文件夹>

文件夹结构:
    <root>/
        model_name/
            metrics_output_5.json
            metrics_output_10.json
            ...
"""

import json
import os
import sys
from collections import defaultdict


def main():
    if len(sys.argv) < 2:
        print(f"用法: python {sys.argv[0]} <metrics结果文件夹>")
        sys.exit(1)

    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"错误: {root} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    # {model: {diff: [rate, ...]}}
    data = defaultdict(lambda: defaultdict(list))
    all_diffs = set()

    for model_name in sorted(os.listdir(root)):
        model_dir = os.path.join(root, model_name)
        if not os.path.isdir(model_dir):
            continue

        for fname in sorted(os.listdir(model_dir)):
            if not fname.startswith("metrics_output_") or not fname.endswith(".json"):
                continue

            # metrics_output_5.json -> "5"
            diff = fname.replace("metrics_output_", "").replace(".json", "")
            all_diffs.add(diff)

            fpath = os.path.join(model_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    cases = json.load(f)
            except Exception as e:
                print(f"[WARN] 读取失败: {fpath}: {e}", file=sys.stderr)
                continue

            for case in cases:
                if case.get("case_id") == "__summary__":                                                                                                                    
                    continue 
                rate = case.get("graph_reasoning", {}).get("node_discovery_rate")
                if rate is not None:
                    data[model_name][diff].append(rate)

    diffs_sorted = sorted(all_diffs, key=lambda x: int(x) if x.isdigit() else x)

    # 打印表头
    header = f"{'模型':<45}" + "".join(f"{'难度'+d:>12}" for d in diffs_sorted)
    print(header)
    print("-" * len(header))

    for model in sorted(data.keys()):
        row = f"{model:<45}"
        for diff in diffs_sorted:
            rates = data[model].get(diff, [])
            if rates:
                avg = sum(rates) / len(rates)
                row += f"  {avg:>5.3f}({len(rates):>2})"
            else:
                row += f"{'—':>12}"
        print(row)


if __name__ == "__main__":
    main()
