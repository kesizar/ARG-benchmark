#!/usr/bin/env python3
"""
DAG 复杂度统计脚本

统计指标：
1. 节点数量
2. 输入数量（边的数量 + init_inputs端口数量）
3. 理论上边数量的上限（DAG中所有节点输入端口之和）
4. 掉落数量（ITEM和HIDDEN_ITEM类型的边数量之和）
5. 有初始化输入的节点数
6. 输入依赖上游节点的节点数（有一个依赖就算，掉落的边除外）
7. 完全没有初始化输入的节点数量（总节点数减去有初始化输入的节点数）
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


def analyze_dag_file(filepath: str) -> Dict:
    """分析单个DAG文件的复杂度指标"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])
    metadata = data.get('metadata', {})
    
    # 1. 节点数量
    node_count = len(nodes)
    
    # 2. 计算各种输入相关指标
    # 统计每个节点的init_inputs数量
    nodes_with_init_inputs = 0
    total_init_input_ports = 0
    total_input_ports = 0  # 理论上边数量的上限
    
    # 构建节点ID到节点对象的映射
    node_map = {node['id']: node for node in nodes}
    
    # 统计每个节点的输入端口和初始化输入
    for node in nodes:
        init_inputs = node.get('init', {}).get('inputs', {})
        inputs = node.get('inputs', [])
        
        # 统计输入端口总数（理论边数上限）
        total_input_ports += len(inputs)
        
        # 统计初始化输入的端口数
        if init_inputs:
            nodes_with_init_inputs += 1
            total_init_input_ports += len(init_inputs)
    
    # 3. 边的统计
    edge_count = len(edges)
    item_edge_count = 0  # ITEM类型的边
    hidden_item_edge_count = 0  # HIDDEN_ITEM类型的边
    
    # 统计每个节点有多少非掉落类型的入边（依赖边）
    node_dependency_edges = defaultdict(set)  # node_id -> set of source_node_ids
    
    for edge in edges:
        conn_type = edge.get('connection_type', '')
        target_id = edge.get('target_id', '')
        source_id = edge.get('source_id', '')
        
        if conn_type == 'Item':
            item_edge_count += 1
        elif conn_type == 'Hidden_Item':
            hidden_item_edge_count += 1
        else:
            # 非掉落类型的边，记录依赖关系
            if target_id:
                node_dependency_edges[target_id].add(source_id)
    
    # 4. 掉落数量（ITEM + HIDDEN_ITEM）
    drop_count = item_edge_count + hidden_item_edge_count
    
    # 5. 输入依赖上游节点的节点数（有一个依赖就算，掉落的边除外）
    nodes_with_dependencies = len([node_id for node_id, deps in node_dependency_edges.items() if deps])
    
    # 6. 输入数量 = 边的数量 + init_inputs端口数量
    total_inputs = edge_count + total_init_input_ports
    
    # 7. 完全没有初始化输入的节点数量
    nodes_without_init_inputs = node_count - nodes_with_init_inputs
    
    return {
        'filename': os.path.basename(filepath),
        'node_count': node_count,
        'total_inputs': total_inputs,
        'edge_count': edge_count,
        'init_input_ports': total_init_input_ports,
        'max_possible_edges': total_input_ports,
        'drop_count': drop_count,
        'item_edges': item_edge_count,
        'hidden_item_edges': hidden_item_edge_count,
        'nodes_with_init_inputs': nodes_with_init_inputs,
        'nodes_with_dependencies': nodes_with_dependencies,
        'nodes_without_init_inputs': nodes_without_init_inputs,
    }


def print_statistics(stats: Dict):
    """打印单个文件的统计信息"""
    print(f"\n{'='*80}")
    print(f"文件: {stats['filename']}")
    print(f"{'='*80}")
    print(f"1. 节点数量: {stats['node_count']}")
    print(f"2. 输入数量（边数量 + init_inputs端口数量）: {stats['total_inputs']}")
    print(f"   - 边数量: {stats['edge_count']}")
    print(f"   - init_inputs端口数量: {stats['init_input_ports']}")
    print(f"3. 理论上边数量的上限（所有节点输入端口之和）: {stats['max_possible_edges']}")
    print(f"4. 掉落数量（ITEM + HIDDEN_ITEM）: {stats['drop_count']}")
    print(f"   - ITEM边: {stats['item_edges']}")
    print(f"   - HIDDEN_ITEM边: {stats['hidden_item_edges']}")
    print(f"5. 有初始化输入的节点数: {stats['nodes_with_init_inputs']}")
    print(f"6. 输入依赖上游节点的节点数（掉落边除外）: {stats['nodes_with_dependencies']}")
    print(f"7. 完全没有初始化输入的节点数量: {stats['nodes_without_init_inputs']}")
    print(f"{'='*80}\n")


def print_summary(all_stats: List[Dict]):
    """打印汇总统计信息"""
    if not all_stats:
        print("没有找到任何数据文件")
        return
    
    print(f"\n{'#'*80}")
    print(f"{'汇总统计':^76}")
    print(f"{'#'*80}\n")
    print(f"总文件数: {len(all_stats)}\n")
    
    # 计算各项指标的平均值、最小值、最大值
    metrics = [
        ('节点数量', 'node_count'),
        ('输入数量', 'total_inputs'),
        ('边数量', 'edge_count'),
        ('init_inputs端口数量', 'init_input_ports'),
        ('理论边数上限', 'max_possible_edges'),
        ('掉落数量', 'drop_count'),
        ('ITEM边', 'item_edges'),
        ('HIDDEN_ITEM边', 'hidden_item_edges'),
        ('有初始化输入的节点数', 'nodes_with_init_inputs'),
        ('输入依赖上游节点的节点数', 'nodes_with_dependencies'),
        ('完全没有初始化输入的节点数', 'nodes_without_init_inputs'),
    ]
    
    print(f"{'指标':<30} {'最小值':>10} {'最大值':>10} {'平均值':>10} {'总和':>12}")
    print(f"{'-'*80}")
    
    for label, key in metrics:
        values = [s[key] for s in all_stats]
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        sum_val = sum(values)
        print(f"{label:<30} {min_val:>10} {max_val:>10} {avg_val:>10.2f} {sum_val:>12}")
    
    print(f"{'-'*80}\n")
    
    # 计算一些衍生指标
    avg_edge_density = sum(s['edge_count'] / s['max_possible_edges'] if s['max_possible_edges'] > 0 else 0 
                           for s in all_stats) / len(all_stats)
    avg_drop_ratio = sum(s['drop_count'] / s['edge_count'] if s['edge_count'] > 0 else 0 
                        for s in all_stats) / len(all_stats)
    avg_init_node_ratio = sum(s['nodes_with_init_inputs'] / s['node_count'] if s['node_count'] > 0 else 0
                             for s in all_stats) / len(all_stats)
    
    print("衍生指标:")
    print(f"  - 平均边密度（实际边数/理论上限）: {avg_edge_density:.2%}")
    print(f"  - 平均掉落边占比（掉落数/边总数）: {avg_drop_ratio:.2%}")
    print(f"  - 平均初始化节点占比: {avg_init_node_ratio:.2%}")
    print(f"\n{'#'*80}\n")


def export_csv(all_stats: List[Dict], output_file: str):
    """导出统计结果到CSV文件"""
    if not all_stats:
        return
    
    import csv
    
    fieldnames = [
        'filename',
        'node_count',
        'total_inputs',
        'edge_count',
        'init_input_ports',
        'max_possible_edges',
        'drop_count',
        'item_edges',
        'hidden_item_edges',
        'nodes_with_init_inputs',
        'nodes_with_dependencies',
        'nodes_without_init_inputs',
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_stats)
    
    print(f"统计结果已导出到: {output_file}")


def main():
    # 处理命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print(__doc__)
            print("\n使用方法:")
            print("  python3 analyze_complexity.py [目录路径]")
            print("\n参数:")
            print("  目录路径  - 包含skeleton_*.json文件的目录（可选）")
            print("            默认: ../data_debug6_prompt2/narrative4")
            print("\n输出:")
            print("  - 控制台：每个文件的详细统计和汇总信息")
            print("  - CSV文件：complexity_statistics.csv（保存在当前脚本目录）")
            print("\n示例:")
            print("  python3 analyze_complexity.py")
            print("  python3 analyze_complexity.py /path/to/narrative4")
            sys.exit(0)
        target_dir = sys.argv[1]
    else:
        # 默认为 narrative4 目录
        script_dir = Path(__file__).parent.parent
        target_dir = script_dir / "data_debug6_prompt2" / "narrative4"
    
    target_dir = Path(target_dir)
    
    if not target_dir.exists():
        print(f"错误: 目录不存在: {target_dir}")
        print(f"\n使用 --help 查看帮助信息")
        sys.exit(1)
    
    print(f"正在分析目录: {target_dir}")
    print(f"查找所有 skeleton_*.json 文件...\n")
    
    # 查找所有skeleton文件
    json_files = sorted(target_dir.glob("skeleton_*.json"))
    
    if not json_files:
        print(f"未找到任何 skeleton_*.json 文件")
        sys.exit(1)
    
    print(f"找到 {len(json_files)} 个文件\n")
    
    # 分析所有文件
    all_stats = []
    for json_file in json_files:
        try:
            stats = analyze_dag_file(str(json_file))
            all_stats.append(stats)
            print_statistics(stats)
        except Exception as e:
            print(f"错误: 无法分析文件 {json_file}: {e}")
    
    # 打印汇总
    print_summary(all_stats)
    
    # 导出CSV
    output_csv = Path(__file__).parent / "complexity_statistics_15.csv"
    export_csv(all_stats, str(output_csv))


if __name__ == "__main__":
    main()