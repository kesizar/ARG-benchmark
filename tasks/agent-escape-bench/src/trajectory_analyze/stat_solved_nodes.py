#!/usr/bin/env python3
"""
统计每个模型每个难度的平均节点解决数。

判定"节点被解决"的规则:
  - Tool 节点: trajectory 中某次 tool_call 返回了 parameter_feedback.status=="correct"，
               或者 output_values 与题目 JSON 中的 golden outputs 完全匹配
  - Item 节点（有 content 值）: investigate 返回了 content，或 use_item 返回了 content
  - Item 节点（Hidden_Item，无 content 值）: investigate 触发了 newly_revealed

用法:
    python stat_solved_nodes.py <结果文件夹> <题目文件夹>

    结果文件夹结构: <root>/model_name/difficulty/result.json
    题目文件夹结构: <root>/difficulty/narrative/skeleton_xxx_narrative.json
"""

import argparse
import json
import os
import sys
from collections import defaultdict


def _extract_skeleton_id(filename: str) -> str:
    """从结果文件名中提取 skeleton ID，例如 skeleton_310eae83"""
    # skeleton_310eae83_narrative_result.json -> skeleton_310eae83
    parts = filename.replace("_narrative_result.json", "").replace("_result.json", "")
    return parts


def _load_narrative(narrative_dir: str, skeleton_id: str) -> dict | None:
    """加载题目 narrative JSON"""
    fname = f"{skeleton_id}_narrative.json"
    fpath = os.path.join(narrative_dir, fname)
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _build_golden_map(narr: dict) -> dict:
    """从 narrative JSON 构建 {node_id: {type, golden_outputs, has_content_value}} 映射"""
    golden = {}
    for node in narr.get("nodes", []):
        nid = node["id"]
        ntype = node["type"]
        gout = {}
        has_content_value = False
        for out in node.get("outputs", []):
            if "value" in out:
                gout[out["name"]] = out["value"]
                has_content_value = True
        golden[nid] = {
            "type": ntype,
            "golden_outputs": gout,
            "has_content_value": has_content_value,
        }
    return golden


def _count_solved(result: dict, golden: dict) -> tuple[int, int]:
    """
    从 trajectory 分析有多少节点被解决。
    返回 (solved_count, total_count)
    """
    solved = set()
    trajectory = result.get("trajectory", [])

    for step in trajectory:
        action = step.get("action", "")
        node_id = step.get("node_id", "")
        res = step.get("result", {})

        if not res.get("ok"):
            continue

        if node_id not in golden:
            continue

        node_info = golden[node_id]

        if action == "tool_call" and node_info["type"] == "Tool":
            # 方式1: parameter_feedback 明确标记 correct（源节点）
            pf = res.get("parameter_feedback", {})
            if pf.get("status") == "correct":
                solved.add(node_id)
                continue

            # 方式2: output_values 与 golden_outputs 完全匹配
            ov = res.get("output_values", {})
            gout = node_info["golden_outputs"]
            if gout and ov:
                match = all(
                    str(ov.get(k)) == str(v) for k, v in gout.items()
                )
                if match:
                    solved.add(node_id)

        elif action == "investigate" and node_info["type"] == "Item":
            if node_info["has_content_value"]:
                # 有内容的 Item: investigate 返回了 content
                if "content" in res:
                    solved.add(node_id)
            else:
                # Hidden Item（无值）: investigate 触发了 newly_revealed 或返回了 narrative
                if "newly_revealed" in res or "content" in res:
                    solved.add(node_id)

        elif action == "use_item" and node_info["type"] == "Item":
            if "content" in res:
                solved.add(node_id)

    return len(solved), len(golden)


def main():
    parser = argparse.ArgumentParser(description="统计每个模型每个难度的平均节点解决数")
    parser.add_argument("result_root", help="结果文件夹路径 (root/model/difficulty/result.json)")
    parser.add_argument("narrative_root", help="题目文件夹路径 (root/difficulty/narrative/*.json)")
    parser.add_argument("--models", nargs="+", default=None, help="只统计指定的模型（不指定则统计全部）")
    parser.add_argument("--diffs", nargs="+", default=None, help="只统计指定的难度（不指定则统计全部）")
    args = parser.parse_args()

    result_root = args.result_root
    narrative_root = args.narrative_root
    filter_models = set(args.models) if args.models else None
    filter_diffs = set(args.diffs) if args.diffs else None

    # {model: {diff: [(solved, total), ...]}}
    data = defaultdict(lambda: defaultdict(list))
    all_diffs = set()

    for model_name in sorted(os.listdir(result_root)):
        if filter_models and model_name not in filter_models:
            continue
        model_dir = os.path.join(result_root, model_name)
        if not os.path.isdir(model_dir):
            continue

        for diff in sorted(os.listdir(model_dir)):
            if filter_diffs and diff not in filter_diffs:
                continue
            diff_dir = os.path.join(model_dir, diff)
            if not os.path.isdir(diff_dir):
                continue
            all_diffs.add(diff)

            narrative_dir = os.path.join(narrative_root, diff, "narrative")

            for fname in sorted(os.listdir(diff_dir)):
                if not fname.endswith(".json"):
                    continue

                fpath = os.path.join(diff_dir, fname)
                skeleton_id = _extract_skeleton_id(fname)

                # 加载结果
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        result = json.load(f)
                except Exception as e:
                    print(f"[WARN] 读取结果失败: {fpath}: {e}", file=sys.stderr)
                    continue

                # 加载对应题目
                narr = _load_narrative(narrative_dir, skeleton_id)
                if narr is None:
                    print(f"[WARN] 未找到题目文件: {skeleton_id} (难度 {diff})", file=sys.stderr)
                    continue

                golden = _build_golden_map(narr)
                solved, total = _count_solved(result, golden)
                data[model_name][diff].append((solved, total))

    # 输出
    diffs_sorted = sorted(all_diffs, key=lambda x: int(x) if x.isdigit() else x)

    header = f"{'模型':<40}" + "".join(f"{'难度'+d:>16}" for d in diffs_sorted)
    print(header)
    print("-" * len(header))

    for model in sorted(data.keys()):
        row = f"{model:<40}"
        for diff in diffs_sorted:
            entries = data[model].get(diff, [])
            if entries:
                avg_solved = sum(s for s, t in entries) / len(entries)
                avg_total = sum(t for s, t in entries) / len(entries)
                ratio = avg_solved / avg_total if avg_total > 0 else 0
                row += f"  {avg_solved:4.1f}/{avg_total:4.1f}({ratio:4.0%})"
            else:
                row += f"{'—':>16}"
        print(row)


if __name__ == "__main__":
    main()
