#!/usr/bin/env python3
"""
检查并删除同构 DAG（单文件版本）

用于在生成新 DAG 后立即检查是否与已存在的 DAG 同构，如果同构则自动删除。
这个脚本通常在 dag_skeleton_generator.py 之后调用。
"""

import sys
import os
from pathlib import Path
from check_dag_isomorphism import check_isomorphism_in_directory


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python3 check_and_remove_isomorphic.py <new_dag_file> [existing_dag_dir]")
        print("\n示例:")
        print("  python3 check_and_remove_isomorphic.py data_debug/dag/skeleton_new.json data_debug/dag")
        print("\n说明:")
        print("  检查新生成的 DAG 是否与已存在的 DAG 同构")
        print("  如果同构，自动删除新 DAG 文件")
        sys.exit(0)
    
    new_dag_file = sys.argv[1]
    existing_dag_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(new_dag_file)
    
    if not os.path.exists(new_dag_file):
        print(f"❌ 错误: 文件不存在: {new_dag_file}")
        sys.exit(1)
    
    print(f"🔍 检查新生成的 DAG: {Path(new_dag_file).name}")
    
    is_isomorphic, isomorphic_file = check_isomorphism_in_directory(new_dag_file, existing_dag_dir)
    
    if is_isomorphic:
        print(f"⚠️  发现同构: 与 {isomorphic_file} 同构")
        print(f"🗑️  删除同构文件: {Path(new_dag_file).name}")
        
        try:
            os.remove(new_dag_file)
            print(f"✅ 已删除同构 DAG")
            sys.exit(0)  # 成功删除
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            sys.exit(1)
    else:
        print(f"✅ 未发现同构，保留新 DAG")
        sys.exit(0)


if __name__ == "__main__":
    main()