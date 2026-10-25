#!/usr/bin/env python3
"""
批量删除同构 DAG 工具

遍历指定目录中的所有 DAG 文件，删除同构的 DAG，只保留每组同构 DAG 中的第一个。
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
from check_dag_isomorphism import get_dag_signature, load_dag


def find_and_remove_isomorphic_dags(dag_dir: str, dry_run: bool = False) -> None:
    """
    查找并删除同构的 DAG
    
    参数：
    - dag_dir: DAG 文件所在目录
    - dry_run: 如果为 True，只显示将要删除的文件，不实际删除
    """
    dag_path = Path(dag_dir)
    if not dag_path.exists():
        print(f"❌ 错误: 目录不存在: {dag_dir}")
        sys.exit(1)
    
    # 收集所有 DAG 文件
    dag_files = sorted(dag_path.glob('skeleton_*.json'))
    
    if not dag_files:
        print(f"⚠️  警告: 目录中没有找到 DAG 文件: {dag_dir}")
        return
    
    print(f"📂 扫描目录: {dag_dir}")
    print(f"📄 找到 {len(dag_files)} 个 DAG 文件\n")
    
    # 按签名分组
    signature_groups = defaultdict(list)
    file_signatures = {}
    
    for dag_file in dag_files:
        try:
            dag_data = load_dag(str(dag_file))
            signature, structure = get_dag_signature(dag_data)
            signature_groups[signature].append(dag_file)
            file_signatures[dag_file] = {
                'signature': signature,
                'node_count': structure['node_count'],
                'edge_count': structure['edge_count']
            }
        except Exception as e:
            print(f"⚠️  警告: 无法处理文件 {dag_file.name}: {e}")
            continue
    
    # 统计和删除
    total_files = len(dag_files)
    unique_dags = len(signature_groups)
    files_to_remove = []
    
    print("="*60)
    print("🔍 同构检查结果")
    print("="*60)
    
    for signature, files in signature_groups.items():
        if len(files) > 1:
            # 发现同构的 DAG
            print(f"\n⚠️  发现 {len(files)} 个同构 DAG:")
            keeper = files[0]
            print(f"  ✅ 保留: {keeper.name}")
            
            for duplicate in files[1:]:
                print(f"  ❌ 删除: {duplicate.name}")
                files_to_remove.append(duplicate)
    
    if not files_to_remove:
        print("\n✅ 没有发现同构 DAG，所有文件都是唯一的")
    else:
        print(f"\n{'='*60}")
        print(f"📊 统计信息")
        print(f"{'='*60}")
        print(f"总文件数: {total_files}")
        print(f"唯一 DAG 数: {unique_dags}")
        print(f"将删除文件数: {len(files_to_remove)}")
        print(f"保留文件数: {unique_dags}")
        
        if dry_run:
            print(f"\n🔍 [预览模式] 以上文件将被删除（使用 --execute 参数实际删除）")
        else:
            print(f"\n🗑️  正在删除同构 DAG...")
            deleted_count = 0
            for file_to_remove in files_to_remove:
                try:
                    os.remove(file_to_remove)
                    print(f"  ✓ 已删除: {file_to_remove.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ✗ 删除失败: {file_to_remove.name} - {e}")
            
            print(f"\n✅ 完成！成功删除 {deleted_count} 个同构 DAG")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 remove_isomorphic_dags.py <dag_directory> [--execute]")
        print("\n示例:")
        print("  python3 remove_isomorphic_dags.py data_debug/dag")
        print("  python3 remove_isomorphic_dags.py data_debug/dag --execute")
        print("\n说明:")
        print("  默认为预览模式，只显示将要删除的文件")
        print("  使用 --execute 参数实际删除同构的 DAG 文件")
        sys.exit(0)
    
    dag_dir = sys.argv[1]
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("🔍 运行模式: 预览模式（不会实际删除文件）")
        print("   使用 --execute 参数进行实际删除\n")
    else:
        print("⚠️  运行模式: 执行模式（将实际删除文件）\n")
    
    find_and_remove_isomorphic_dags(dag_dir, dry_run)


if __name__ == "__main__":
    main()