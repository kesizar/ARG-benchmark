#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Annotate DAG JSON with "source_init" information.

What counts as "needs initialization":
1) Any node input port that has NO incoming edge targeting (node_id, input_name).
2) "Drop nodes": if a node has any input whose type is ITEM or HIDDEN_ITEM,
   then for each of its output ports that:
     - output type is NOT ITEM/HIDDEN_ITEM, AND
     - that output port is actually used by some outgoing edge,
   we mark that output port as needing initialization (init_outputs).

Output:
- Adds metadata["source_init"] = {
    "source_nodes": [...],
    "by_node": {
       "<node_id>": {
           "node_name": "...",
           "node_type": "...",
           "template_id": "...",
           "init_inputs": { "<input_port>": {"type": "...", "description": "..."} , ... },
           "init_outputs": { "<output_port>": {"type": "...", "description": "..."} , ... }
       },
       ...
    }
  }

Usage:
  python annotate_dag_sources.py --input dag.json --output dag_with_sources.json
  python annotate_dag_sources.py --input dag.json --inplace
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set, Optional

# 这些工具的输出不依赖真实文件/真实执行，你要把它们的输出当作"外部可预置"的信息源头
SPECIAL_OUTPUT_SOURCE_TEMPLATES = {
    "zip_unzip",  # ZIP 解压工具
    "zip_unzip_item",
    "zip_unzip_file",
    "csv_query",
    "json_get",
    "graph_shortest_path",  # 图最短路径查找，读取 JSON 文件
    "regex_search",  # 正则搜索工具，读取文件内容
}
def _is_special_output_source(template_id: str) -> bool:
    t = (template_id or "").strip().lower()
    return t in SPECIAL_OUTPUT_SOURCE_TEMPLATES

def _is_terminal_like_template(template_id: str) -> bool:
    """
    终端模板：TERMINAL_TEMPLATE / MATH_TERMINAL_TEMPLATE
    由于你没给出 JSON 中确切 template_id 字符串，这里用前缀匹配保证命中：
      - terminal_*
      - math_terminal_*
    如果你知道确切值，建议改成集合精确匹配，更严谨。
    """
    t = (template_id or "").strip().lower()
    return t.startswith("terminal") or t.startswith("math_terminal")
def _mark_used_outputs_as_init(
    node_id: str,
    node: Dict[str, Any],
    outgoing: Dict[Tuple[str, str], List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    把该节点“确实被下游使用”的输出端口标为需要初始化。
    注意：这里不排除 ITEM/HIDDEN_ITEM 类型输出——因为你现在希望这些节点的输出都可被预置。
    """
    init_outputs: Dict[str, Any] = {}
    for outp in node.get("outputs", []) or []:
        out_name = outp.get("name")
        if not out_name:
            continue
        # 只标记真正被下游消费的输出（存在出边）
        if (node_id, out_name) in outgoing:
            init_outputs[out_name] = {
                "type": outp.get("type", ""),
                "description": outp.get("description", "")
            }
    return init_outputs
def _mark_all_outputs_as_init(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    把该节点的"所有输出端口"标为需要初始化（不要求有出边消费）。
    """
    init_outputs: Dict[str, Any] = {}
    for outp in node.get("outputs", []) or []:
        out_name = outp.get("name")
        if not out_name:
            continue
        init_outputs[out_name] = {
            "type": outp.get("type", ""),
            "description": outp.get("description", "")
        }
    return init_outputs

def _mark_non_item_outputs_as_init(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    把该节点的"所有非 ITEM/HIDDEN_ITEM 类型输出端口"标为需要初始化（不要求有出边消费）。
    用于模拟执行的工具（文件处理工具、terminal 工具），它们的非 ITEM/HIDDEN_ITEM 输出需要预置。
    """
    init_outputs: Dict[str, Any] = {}
    for outp in node.get("outputs", []) or []:
        out_name = outp.get("name")
        if not out_name:
            continue
        
        out_type_norm = _norm_type(outp.get("type"))
        if out_type_norm in ITEM_TYPE_SET:
            continue  # 跳过 ITEM/HIDDEN_ITEM 类型的输出
        
        init_outputs[out_name] = {
            "type": outp.get("type", ""),
            "description": outp.get("description", "")
        }
    return init_outputs




def _norm_type(t: Optional[str]) -> str:
    if not t:
        return ""
    # Normalize to reduce schema variance: "Hex_String" -> "HEX_STRING"
    return t.strip().upper().replace("-", "_").replace(" ", "")


ITEM_TYPE_SET = {"ITEM", "HIDDEN_ITEM"}


def _index_edges(edges: List[Dict[str, Any]]) -> Tuple[Dict[Tuple[str, str], List[Dict[str, Any]]],
                                                      Dict[Tuple[str, str], List[Dict[str, Any]]]]:
    """
    Build:
      incoming[(target_id, target_port)] -> [edge...]
      outgoing[(source_id, source_port)] -> [edge...]
    """
    incoming: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    outgoing: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    for e in edges or []:
        s_id = e.get("source_id")
        t_id = e.get("target_id")
        s_port = e.get("source_port")
        t_port = e.get("target_port")
        if not (s_id and t_id and s_port and t_port):
            # Skip malformed edges
            continue

        incoming.setdefault((t_id, t_port), []).append(e)
        outgoing.setdefault((s_id, s_port), []).append(e)

    return incoming, outgoing


def _node_has_item_input(node: Dict[str, Any], incoming: Dict[Tuple[str, str], List[Dict[str, Any]]]) -> bool:
    """
    检查节点是否有实际连接的 ITEM/HIDDEN_ITEM 入边。
    不仅检查输入端口定义，还要检查是否有实际的入边连接。
    """
    node_id = node.get("id")
    for inp in node.get("inputs", []) or []:
        if _norm_type(inp.get("type")) in ITEM_TYPE_SET:
            # 检查这个端口是否有实际的入边
            port_name = inp.get("name")
            if port_name and (node_id, port_name) in incoming:
                return True
    return False


def annotate_sources(dag: Dict[str, Any]) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = dag.get("nodes", []) or []
    edges: List[Dict[str, Any]] = dag.get("edges", []) or []

    incoming, outgoing = _index_edges(edges)

    by_node: Dict[str, Any] = {}
    source_nodes: List[str] = []

    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            continue

        # 1) Missing inputs (no incoming edge for that specific target port)
        init_inputs: Dict[str, Any] = {}
        for inp in node.get("inputs", []) or []:
            port_name = inp.get("name")
            if not port_name:
                continue
            if (node_id, port_name) not in incoming: # 没有入边
                # 特殊处理：如果输入端口类型是 ITEM 或 HIDDEN_ITEM，且没有上游节点，
                # 则不标记为信息源头（这种节点应该在 server 中直接设置为初始可见）
                inp_type_norm = _norm_type(inp.get("type"))
                if inp_type_norm in ITEM_TYPE_SET:
                    continue  # 跳过，不标记为需要初始化
                
                # 其他类型的输入端口：标记为需要初始化
                init_inputs[port_name] = {
                    "type": inp.get("type", ""),
                    "description": inp.get("description", "")
                }

        # # 2) Drop-node outputs to initialize
        # init_outputs: Dict[str, Any] = {}
        # if _node_has_item_input(node):  # 如果这个节点的输入类型是ITEM、HIDDEN_ITEM
        #     for outp in node.get("outputs", []) or []:
        #         out_name = outp.get("name")
        #         if not out_name:
        #             continue

        #         out_type_norm = _norm_type(outp.get("type"))
        #         if out_type_norm in ITEM_TYPE_SET:
        #             continue  # item-like outputs do not need initialization per your rule

        #         # Only mark if downstream actually consumes it
        #         if (node_id, out_name) in outgoing:
        #             init_outputs[out_name] = {
        #                 "type": outp.get("type", ""),
        #                 "description": outp.get("description", "")
        #             }
        # 2) Outputs to initialize
        init_outputs: Dict[str, Any] = {}
        
        node_type = node.get("type", "")
        template_id = node.get("template_id", "")

        # 2.1 Item 节点的输出处理
        # 所有 Item 节点的有出边的非 ITEM/HIDDEN_ITEM 输出都需要预置（无论是否有入边）
        if node_type == "Item":
            for outp in node.get("outputs", []) or []:
                out_name = outp.get("name")
                if not out_name:
                    continue

                out_type_norm = _norm_type(outp.get("type"))
                if out_type_norm in ITEM_TYPE_SET:
                    continue  # ITEM/HIDDEN_ITEM 输出不标记

                if (node_id, out_name) in outgoing:  # 被下游消费
                    init_outputs[out_name] = {
                        "type": outp.get("type", ""),
                        "description": outp.get("description", "")
                    }

        # 2.2 特殊工具和 terminal 工具：无论是否有 ITEM/HIDDEN_ITEM 入边，所有非 ITEM/HIDDEN_ITEM 输出都需要预置
        # 因为这些工具是模拟执行的，它们的输出结果需要在运行时直接提供
        if _is_special_output_source(template_id) or _is_terminal_like_template(template_id):
            init_outputs.update(_mark_non_item_outputs_as_init(node))
        
        # 2.4 Item 节点：如果输出端口没有出边，应该标记为 init_outputs（无论输出类型是什么）
        if node_type == "Item":
            for outp in node.get("outputs", []) or []:
                out_name = outp.get("name")
                if not out_name:
                    continue
                
                # Item 节点的输出如果没有出边，就是信息源头
                if (node_id, out_name) not in outgoing:
                    init_outputs.setdefault(out_name, {
                        "type": outp.get("type", ""),
                        "description": outp.get("description", "")
                    })
        
        # 2.5 特殊情况：任何节点的 ITEM/HIDDEN_ITEM 输出端口如果没有出边，都要视为信息源头
        for outp in node.get("outputs", []) or []:
            out_name = outp.get("name")
            if not out_name:
                continue

            out_type_norm = _norm_type(outp.get("type"))
            if out_type_norm in ITEM_TYPE_SET:
                if (node_id, out_name) not in outgoing:  # 没有出边，未连接任何输入
                    init_outputs.setdefault(out_name, {
                        "type": outp.get("type", ""),
                        "description": outp.get("description", "")
                    })



        if init_inputs or init_outputs:
            source_nodes.append(node_id)
            by_node[node_id] = {
                "node_name": node.get("name", ""),
                "node_type": node.get("type", ""),
                "template_id": node.get("template_id", ""),
                "init_inputs": init_inputs,
                "init_outputs": init_outputs
            }
        


    dag.setdefault("metadata", {})
    dag["metadata"]["source_init"] = {
        "source_nodes": source_nodes,
        "by_node": by_node
    }
    return dag


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", "-i", help="Path to input DAG json", default="./skeletons/skeleton_6e8116a6.json")
    ap.add_argument("--output", "-o", default="./sources/skeleton_6e8116a6_source_revized_2.json", help="Path to output json (optional if --inplace)")
    ap.add_argument("--inplace", action="store_true", help="Overwrite input file")
    ap.add_argument("--indent", type=int, default=2, help="JSON indent spaces")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"Input json not found: {in_path}")

    if not args.inplace and not args.output:
        raise ValueError("Either --output must be provided, or use --inplace.")

    with in_path.open("r", encoding="utf-8") as f:
        dag = json.load(f)

    dag = annotate_sources(dag)

    out_path = in_path if args.inplace else Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(dag, f, ensure_ascii=False, indent=args.indent)

    print(f"[OK] Wrote: {out_path}")
    si = dag.get("metadata", {}).get("source_init", {})
    print(f"[INFO] source_nodes = {len(si.get('source_nodes', []))}")


if __name__ == "__main__":
    main()