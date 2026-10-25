#!/usr/bin/env python3
"""
DAG 同构检查工具

检查新生成的 DAG 是否与已存在的 DAG 同构。
同构定义：
1. 节点数量相同
2. 节点的 template_id 分布相同
3. 边的连接模式相同（基于 template_id 和端口类型）
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def load_dag(file_path: str) -> dict:
    """加载 DAG 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_dag_signature(dag_data: dict) -> Tuple[str, Dict]:
    """
    获取 DAG 的签名，用于同构检查
    
    返回：
    - signature: 字符串形式的签名（用于快速比较）
    - structure: 详细的结构信息（用于精确比较）
    """
    nodes = dag_data.get('nodes', [])
    edges = dag_data.get('edges', [])
    
    # 1. 构建节点 ID 到 template_id 的映射
    node_to_template = {}
    for node in nodes:
        node_to_template[node['id']] = node.get('template_id', node['id'])
    
    # 2. 统计 template_id 的出现次数（包括类型信息）
    template_counts = defaultdict(int)
    template_types = defaultdict(str)
    for node in nodes:
        template_id = node.get('template_id', node['id'])
        node_type = node.get('type', 'Tool')
        key = f"{template_id}:{node_type}"
        template_counts[key] += 1
        template_types[template_id] = node_type
    
    # 3. 构建边的模式（基于 template_id 和端口）
    # 格式: (source_template, source_port, target_template, target_port, connection_type)
    edge_patterns = []
    for edge in edges:
        source_id = edge['source_id']
        target_id = edge['target_id']
        source_template = node_to_template.get(source_id, source_id)
        target_template = node_to_template.get(target_id, target_id)
        
        pattern = (
            source_template,
            edge.get('source_port', ''),
            target_template,
            edge.get('target_port', ''),
            edge.get('connection_type', '')
        )
        edge_patterns.append(pattern)
    
    # 4. 对边模式排序（用于标准化比较）
    edge_patterns.sort()
    
    # 5. 构建签名字符串
    # 格式: node_count|template_counts_sorted|edge_patterns_sorted
    template_count_str = '|'.join(sorted([f"{k}:{v}" for k, v in template_counts.items()]))
    edge_pattern_str = '|'.join([f"{s_t}.{s_p}->{t_t}.{t_p}({ct})" for s_t, s_p, t_t, t_p, ct in edge_patterns])
    
    signature = f"{len(nodes)}#{template_count_str}#{edge_pattern_str}"
    
    structure = {
        'node_count': len(nodes),
        'edge_count': len(edges),
        'template_counts': dict(template_counts),
        'edge_patterns': edge_patterns
    }
    
    return signature, structure


def are_dags_isomorphic(dag1: dict, dag2: dict) -> bool:
    """
    检查两个 DAG 是否同构
    
    返回：
    - True: 同构
    - False: 不同构
    """
    sig1, struct1 = get_dag_signature(dag1)
    sig2, struct2 = get_dag_signature(dag2)
    
    # 快速检查：签名是否相同
    if sig1 == sig2:
        return True
    
    # 详细检查（以防哈希冲突）
    if struct1['node_count'] != struct2['node_count']:
        return False
    
    if struct1['edge_count'] != struct2['edge_count']:
        return False
    
    if struct1['template_counts'] != struct2['template_counts']:
        return False
    
    if struct1['edge_patterns'] != struct2['edge_patterns']:
        return False
    
    return True


def check_isomorphism_in_directory(new_dag_file: str, existing_dag_dir: str) -> Tuple[bool, str]:
    """
    检查新 DAG 是否与目录中已存在的 DAG 同构
    
    参数：
    - new_dag_file: 新生成的 DAG 文件路径
    - existing_dag_dir: 已存在 DAG 文件的目录路径
    
    返回：
    - (is_isomorphic, isomorphic_file): 如果同构，返回 (True, 同构文件名)；否则返回 (False, '')
    """
    # 加载新 DAG
    new_dag = load_dag(new_dag_file)
    new_sig, _ = get_dag_signature(new_dag)
    
    # 遍历目录中的所有 DAG 文件
    dag_dir = Path(existing_dag_dir)
    if not dag_dir.exists():
        return False, ''
    
    for existing_file in dag_dir.glob('skeleton_*.json'):
        # 跳过新文件本身
        if existing_file.resolve() == Path(new_dag_file).resolve():
            continue
        
        try:
            existing_dag = load_dag(str(existing_file))
            if are_dags_isomorphic(new_dag, existing_dag):
                return True, existing_file.name
        except Exception as e:
            print(f"⚠️  警告: 无法读取文件 {existing_file.name}: {e}", file=sys.stderr)
            continue
    
    return False, ''


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 check_dag_isomorphism.py <new_dag_file> [existing_dag_dir]")
        print("\n示例:")
        print("  python3 check_dag_isomorphism.py data_debug/dag/skeleton_new.json data_debug/dag")
        print("\n说明:")
        print("  检查 new_dag_file 是否与 existing_dag_dir 中的任何 DAG 同构")
        print("  如果同构，返回退出码 1；否则返回退出码 0")
        sys.exit(2)
    
    new_dag_file = sys.argv[1]
    existing_dag_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(new_dag_file)
    
    if not os.path.exists(new_dag_file):
        print(f"❌ 错误: 文件不存在: {new_dag_file}")
        sys.exit(2)
    
    print(f"🔍 检查 DAG 同构性...")
    print(f"  新文件: {new_dag_file}")
    print(f"  检查目录: {existing_dag_dir}")
    
    is_isomorphic, isomorphic_file = check_isomorphism_in_directory(new_dag_file, existing_dag_dir)
    
    if is_isomorphic:
        print(f"\n⚠️  发现同构 DAG: {isomorphic_file}")
        print(f"  新文件与已存在的 {isomorphic_file} 同构")
        print(f"  建议删除新文件以避免重复")
        sys.exit(1)  # 退出码 1 表示发现同构
    else:
        print(f"\n✅ 未发现同构 DAG")
        print(f"  新文件是唯一的，可以保留")
        sys.exit(0)  # 退出码 0 表示未发现同构


if __name__ == "__main__":
    main()