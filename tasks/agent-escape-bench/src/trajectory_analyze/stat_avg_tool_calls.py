#!/usr/bin/env python3
"""
统计不同模型每个难度所有题目的平均工具调用次数。

与 stat_avg_steps.py 的区别：
  - stat_avg_steps.py 统计的是 total_steps（LLM 回合数，一个 step 中模型可能并行调用多个工具）
  - 本脚本统计的是 trajectory 中的条目数（实际工具调用次数，包括 investigate、tool_call、use_item、submit_answer）

用法:
    python stat_avg_tool_calls.py <结果文件夹路径>

文件夹结构:
    <root>/
        model_name_1/
            5/
                result1.json
                result2.json
            10/
                ...
        model_name_2/
            ...
"""

import json
import os
import sys
from collections import defaultdict


def stat_avg_tool_calls(root_dir: str):
    # {model: {difficulty: [tool_call_count, ...]}}
    data = defaultdict(lambda: defaultdict(list))
    all_diffs = set()

    for model_name in sorted(os.listdir(root_dir)):
        model_dir = os.path.join(root_dir, model_name)
        if not os.path.isdir(model_dir):
            continue

        for diff in sorted(os.listdir(model_dir)):
            diff_dir = os.path.join(model_dir, diff)
            if not os.path.isdir(diff_dir):
                continue
            all_diffs.add(diff)

            for fname in sorted(os.listdir(diff_dir)):
                if not fname.endswith(".json"):
                    continue
                fpath = os.path.join(diff_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        result = json.load(f)
                    trajectory = result.get("trajectory", [])
                    tool_calls = len(trajectory)
                    if tool_calls > 0:
                        data[model_name][diff].append(tool_calls)
                except Exception as e:
                    print(f"[WARN] 读取失败: {fpath}: {e}", file=sys.stderr)

    # 按数字排序难度
    diffs_sorted = sorted(all_diffs, key=lambda x: int(x) if x.isdigit() else x)

    # 打印表头
    header = f"{'模型':<30}" + "".join(f"{'难度'+d:>14}" for d in diffs_sorted)
    print(header)
    print("-" * len(header))

    for model in sorted(data.keys()):
        row = f"{model:<30}"
        for diff in diffs_sorted:
            calls_list = data[model].get(diff, [])
            if calls_list:
                avg = sum(calls_list) / len(calls_list)
                row += f"{avg:>10.1f}({len(calls_list):>2})"
            else:
                row += f"{'—':>14}"
        print(row)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: python {sys.argv[0]} <结果文件夹路径>")
        sys.exit(1)

    root = sys.argv[1]
    if not os.path.isdir(root):
        print(f"错误: {root} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    stat_avg_tool_calls(root)
