#!/usr/bin/env python3
"""
DAG Validation Script
验证生成的 DAG 文件是否符合要求（支持可掉落工具机制）：
1. 对于输入端口：除了没有边连接的 ITEM/HIDDEN_ITEM 端口，其他都要有 value
2. 对于输出端口：除了有边连接的 ITEM/HIDDEN_ITEM 端口，其他都要有 value
"""

import json
import sys
import os
import shutil
from pathlib import Path


def load_json(file_path: str) -> dict:
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_edge_index(data: dict) -> tuple[dict, dict]:
    """构建边的索引
    
    Returns:
        (edges_by_source, edges_by_target): 按源节点和目标节点索引的边
    """
    edges_by_source = {}
    edges_by_target = {}
    
    for edge in data.get('edges', []):
        src_node = edge.get('source_id') or edge.get('source_node_id')
        src_port = edge.get('source_port')
        tgt_node = edge.get('target_id') or edge.get('target_node_id')
        tgt_port = edge.get('target_port')
        
        if src_node and src_port:
            edges_by_source.setdefault(src_node, {})[src_port] = (tgt_node, tgt_port)
        
        if tgt_node and tgt_port:
            edges_by_target.setdefault(tgt_node, {})[tgt_port] = (src_node, src_port)
    
    return edges_by_source, edges_by_target


def validate_dag(file_path: str) -> tuple[bool, list]:
    """验证 DAG 文件
    
    Returns:
        (is_valid, error_messages): 是否合格和错误信息列表
    """
    try:
        data = load_json(file_path)
    except Exception as e:
        return False, [f"无法读取文件: {str(e)}"]
    
    errors = []
    edges_by_source, edges_by_target = build_edge_index(data)
    
    # 遍历所有节点
    for node in data.get('nodes', []):
        node_id = node.get('id', 'unknown')
        node_type = node.get('type', 'unknown')
        
        # 检查输入端口
        for i, input_port in enumerate(node.get('inputs', [])):
            port_name = input_port.get('name', f'input_{i}')
            port_type = input_port.get('type', '')
            
            # ITEM/HIDDEN_ITEM 类型的输入端口，无论是否有边连接，都允许没有 value
            if port_type in ['Item', 'Hidden_Item']:
                continue
            
            # 非 ITEM/HIDDEN_ITEM 类型，必须有 value
            if 'value' not in input_port:
                errors.append(
                    f"节点 {node_id} ({node_type}) 的输入端口 {port_name} ({port_type}) 缺少 value 字段"
                )
            elif input_port.get('value') is None:
                errors.append(
                    f"节点 {node_id} ({node_type}) 的输入端口 {port_name} ({port_type}) 的 value 为 None"
                )
        
        # 检查输出端口
        for i, output_port in enumerate(node.get('outputs', [])):
            port_name = output_port.get('name', f'output_{i}')
            port_type = output_port.get('type', '')
            
            # ITEM/HIDDEN_ITEM 类型的输出端口
            if port_type in ['Item', 'Hidden_Item']:
                # 如果有边连接，不需要 value（触发边不传递值）
                has_edge = port_name in edges_by_source.get(node_id, {})
                if has_edge:
                    continue
                # 如果没有边连接，需要有 value（这是输出内容）
            
            # 非 ITEM/HIDDEN_ITEM 类型，或没有边连接的 ITEM/HIDDEN_ITEM，都必须有 value
            if 'value' not in output_port:
                errors.append(
                    f"节点 {node_id} ({node_type}) 的输出端口 {port_name} ({port_type}) 缺少 value 字段"
                )
            elif output_port.get('value') is None:
                errors.append(
                    f"节点 {node_id} ({node_type}) 的输出端口 {port_name} ({port_type}) 的 value 为 None"
                )
    
    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python3 validate_dag.py <json_file> [--no-move]")
        print("  --no-move: 验证失败时不移动文件")
        sys.exit(1)
    
    file_path = sys.argv[1]
    no_move = '--no-move' in sys.argv
    
    if not os.path.exists(file_path):
        print(f"❌ 错误: 文件不存在: {file_path}")
        sys.exit(1)
    
    print(f"🔍 验证 DAG 文件: {file_path}")
    
    is_valid, errors = validate_dag(file_path)
    
    if is_valid:
        print("✅ 数据合格")
        sys.exit(0)
    else:
        print("❌ 数据不合格")
        print(f"\n发现 {len(errors)} 个错误:")
        for error in errors:
            print(f"  - {error}")
        
        # 将不合格的文件移动到 wrongs4 目录（带阶段标识）
        if not no_move:
            try:
                # 获取文件所在的基础目录（假设结构是 .../data/narrative4/xxx.json）
                file_path_obj = Path(file_path)
                base_dir = file_path_obj.parent.parent  # 从 data/narrative4/ 回到 data/
                wrongs_dir = base_dir / "wrongs4"
                
                # 创建 wrongs4 目录（如果不存在）
                wrongs_dir.mkdir(parents=True, exist_ok=True)
                
                # 添加 _narrative 后缀以与其他阶段文件保持一致
                file_stem = file_path_obj.stem  # skeleton_xxx
                new_name = f"{file_stem}_narrative.json"
                destination = wrongs_dir / new_name
                
                shutil.move(str(file_path), str(destination))
                print(f"\n📦 已将不合格文件移动到: {destination}")
            except Exception as e:
                print(f"\n⚠️  无法移动文件: {str(e)}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()