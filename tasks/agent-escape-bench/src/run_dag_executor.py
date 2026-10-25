#!/usr/bin/env python3
"""
DAG Executor Runner
执行 DAG 并填充所有节点的缺失值
"""

import json
import sys
import os
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import GraphScenario, Node, Port, Edge, InterfaceType
from simulator import ToolSimulator
from dag_executor import DAGExecutor


def load_dag_from_file(file_path: str) -> dict:
    """从 JSON 文件加载 DAG 定义"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

'''一个node字段的示例
"nodes": [
    {
      "id": "text_xor_hex",
      "name": "Hex XOR",
      "description": "XOR two hex strings.",
      "type": "Tool",
      "template_id": "text_xor_hex",
      "initial_visible": true,
      "is_revealed": true,
      "inputs": [
        {
          "name": "hex_a",
          "type": "Hex_String",
          "description": "Hex A"
        },
        {
          "name": "hex_b",
          "type": "Hex_String",
          "description": "Hex B"
        }
      ],
      "outputs": [
        {
          "name": "hex",
          "type": "Hex_String",
          "description": "XOR Result Hex"
        }
      ]
    }
]
'''

def convert_to_graph_scenario(dag_data: dict, file_path: str = None) -> tuple:
    """将 DAG JSON 数据转换为 GraphScenario 对象，返回 (scenario, raw_nodes_data)
    
    Args:
        dag_data: DAG 数据字典
        file_path: 输入文件路径，用于生成 case_id 和 title
    """

    # 提取基本信息
    metadata = dag_data.get('metadata', {})
    
    # 从文件名生成 case_id（如果提供了文件路径）
    if file_path:
        file_name = Path(file_path).stem  # 获取不带扩展名的文件名
        case_id = file_name
    else:
        # 如果没有文件路径，使用 win_node_id 生成
        case_id = f"case_{metadata.get('win_node_id', 'unknown')}"
    
    # 生成标题和介绍（基于实际存在的字段）
    win_node_id = metadata.get('win_node_id', '')
    title = f'Escape Room Challenge: {case_id}'
    intro_narrative = f'Solve this puzzle by reaching the win condition at node "{win_node_id}".'
    
    # 难度使用 total_nodes（这个字段确实存在于 metadata 中）
    difficulty = metadata.get('total_nodes', 5)

    # 转换节点
    nodes = {}
    raw_nodes_data = {}  # 保存原始节点数据

    for node_data in dag_data.get('nodes', []):
        raw_nodes_data[node_data['id']] = node_data  # 保存原始数据

        # 转换输入端口
        inputs = []
        for input_port in node_data.get('inputs', []):
            port = Port(
                name=input_port['name'],
                type=InterfaceType(input_port['type']),
                description=input_port.get('description', '')
            )
            inputs.append(port)

        # 转换输出端口
        outputs = []
        for output_port in node_data.get('outputs', []):
            port = Port(
                name=output_port['name'],
                type=InterfaceType(output_port['type']),
                description=output_port.get('description', '')
            )
            outputs.append(port)

        # 创建节点
        # 注意: content 和 if_success 是运行时字段，不应该从文件中读取
        # 它们会在服务器初始化或执行时设置
        node = Node(
            id=node_data['id'],
            name=node_data.get('name', ''),
            description=node_data.get('description', ''),
            type=node_data.get('type', 'Tool'),
            inputs=inputs,
            outputs=outputs,
            content=node_data.get('content', None),  # 运行时字段，默认 None
            if_success=node_data.get('if_success', False),  # 运行时字段，默认 False
            initial_visible=node_data.get('initial_visible', False),
            is_revealed=node_data.get('is_revealed', False)
        )

        nodes[node_data['id']] = node

    # 转换边
    edges = []
    for edge_data in dag_data.get('edges', []):
        edge = Edge(
            source_id=edge_data['source_id'],
            target_id=edge_data['target_id'],
            connection_type=InterfaceType(edge_data['connection_type']),
            source_port=edge_data.get('source_port'),
            target_port=edge_data.get('target_port')
        )
        edges.append(edge)

    # 创建 GraphScenario
    scenario = GraphScenario(
        case_id=case_id,
        title=title,
        intro_narrative=intro_narrative,
        nodes=nodes,
        edges=edges,
        difficulty=difficulty,
        win_node_id=win_node_id
    )

    return scenario, raw_nodes_data


def extract_initial_values_from_dag_data(dag_data: dict) -> dict:
    """从 DAG 数据的 metadata.initial_values 中提取初始值
    
    数据结构：
    {
        "metadata": {
            "initial_values": {
                "node_id": {
                    "init_inputs": {...},
                    "init_outputs": {...}
                }
            }
        }
    }
    
    返回格式（只返回 init_inputs，用于设置节点的初始输入值）：
    {
        "node_id": {
            "port_name": "value"
        }
    }
    """
    initial_values = {}
    
    # 从 metadata.initial_values 提取
    metadata = dag_data.get('metadata', {})
    initial_values_data = metadata.get('initial_values', {})
    '''
    initial_values字段的一个例子
    "initial_values": {
      "terminal_1": {
        "init_inputs": {
          "slot_b": "8888888888888888"
        },
        "init_outputs": {
          "text_output": "Initiating sequence... Target: ALPHA_PRO.",
          "hex_output": "48656c6c6f576f726c64",
          "item_dispenser": "掉落了一张纸条，上面写着不要相信机器的判断"
        }
      },
      "regex_search": {
        "init_inputs": {
          "pattern": "ALPHA_[A-Z]+",
          "file_id": "logs_backup.txt"
        },
        "init_outputs": {}
      }
    }
    '''
    
    for node_id, node_init_data in initial_values_data.items():
        # 只提取 init_inputs（用于设置节点的初始输入）
        # init_outputs 会在 simulator 执行时通过 raw_nodes_data 传递
        init_inputs = node_init_data.get('init_inputs', {})
        if init_inputs:
            initial_values[node_id] = init_inputs
    
    return initial_values


def save_results(output_file: str, dag_data: dict, execution_result):
    """保存执行结果到文件
    
    将 DAG 执行后的值直接保存到每个端口的 value 字段中。
    保持 metadata.initial_values 不变，只包含真正的信息源头。
    """

    # 更新节点的输入输出端口值
    for node_data in dag_data.get('nodes', []):
        node_id = node_data['id']
        if node_id in execution_result.node_values:
            node_values = execution_result.node_values[node_id]

            # 将输入值写入每个输入端口的 value 字段
            if 'input_values' in node_values and node_values['input_values']:
                input_vals = node_values['input_values']
                for input_port in node_data.get('inputs', []):
                    port_name = input_port['name']
                    if port_name in input_vals:
                        input_port['value'] = input_vals[port_name]

            # 将输出值写入每个输出端口的 value 字段
            if 'output_values' in node_values and node_values['output_values']:
                output_vals = node_values['output_values']
                for output_port in node_data.get('outputs', []):
                    port_name = output_port['name']
                    if port_name in output_vals:
                        output_port['value'] = output_vals[port_name]

    # 保存到文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dag_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 结果已保存到: {output_file}")


def main():
    """主函数
    
    支持两种使用方式：
    1. 单文件模式：python3 run_dag_executor.py <merged_file> [output_file]
       merged_file 包含完整的 DAG 结构和 metadata.initial_values
    
    2. 双文件模式：python3 run_dag_executor.py <dag_structure_file> <init_values_file> <output_file>
       dag_structure_file: 包含 DAG 结构（nodes, edges, metadata）
       init_values_file: 包含初始值（init_values 或 metadata.initial_values）
    """

    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  单文件模式: python3 run_dag_executor.py <merged_file> [output_file]")
        print("  双文件模式: python3 run_dag_executor.py <dag_structure_file> <init_values_file> <output_file>")
        print("\n示例:")
        print("  python3 run_dag_executor.py dag_init_value/skeleton_6e8116a6.json")
        print("  python3 run_dag_executor.py dag_2026_sources/skeleton.json dag_2026_init/skeleton_init.json output.json")
        sys.exit(1)

    # 解析命令行参数
    input_file = sys.argv[1]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误: 输入文件不存在: {input_file}")
        sys.exit(1)

    print(f"📂 加载 DAG 文件: {input_file}")
    dag_data = load_dag_from_file(input_file)
    
    # 检查第一个文件是否包含完整的 DAG 结构
    has_dag_structure = 'nodes' in dag_data and 'edges' in dag_data
    
    # 判断模式
    if len(sys.argv) == 2:
        # 单文件模式
        init_file = None
        output_file = input_file.replace('.json', '_filled.json')
    elif len(sys.argv) == 3:
        # 需要判断：单文件+输出 or 双文件
        second_arg = sys.argv[2]
        if not has_dag_structure and second_arg.endswith('.json') and os.path.exists(second_arg):
            # 第一个文件缺少 DAG 结构，第二个是 JSON 文件，可能搞反了
            print(f"⚠️  警告: 第一个文件缺少 nodes/edges，请确保第一个参数是 DAG 结构文件")
            print(f"   建议: python3 run_dag_executor.py <dag_structure_file> <init_values_file> <output_file>")
            sys.exit(1)
        elif second_arg.endswith('.json') and os.path.exists(second_arg):
            # 第二个是存在的 JSON 文件，可能是初始值文件
            # 读取检查是否包含 init_values
            try:
                second_data = load_dag_from_file(second_arg)
                if 'init_values' in second_data or ('metadata' in second_data and 'initial_values' in second_data['metadata']):
                    # 确实是初始值文件，双文件模式
                    init_file = second_arg
                    output_file = input_file.replace('.json', '_filled.json')
                else:
                    # 不是初始值文件，可能是输出路径
                    init_file = None
                    output_file = second_arg
            except:
                # 读取失败，当作输出文件
                init_file = None
                output_file = second_arg
        else:
            # 第二个不是 JSON 文件，当作输出路径
            init_file = None
            output_file = second_arg
    else:
        # len(sys.argv) >= 4: 双文件+输出
        init_file = sys.argv[2]
        output_file = sys.argv[3]
    
    # 如果提供了独立的初始值文件，加载并合并
    if init_file:
        if not os.path.exists(init_file):
            print(f"❌ 错误: 初始值文件不存在: {init_file}")
            sys.exit(1)
        
        print(f"📂 加载初始值文件: {init_file}")
        init_data = load_dag_from_file(init_file)
        
        # 合并初始值到 dag_data
        # init_data 可能有两种格式：
        # 1. {"init_values": {...}}
        # 2. {"metadata": {"initial_values": {...}}}
        if 'init_values' in init_data:
            # 格式1：直接使用 init_values
            if 'metadata' not in dag_data:
                dag_data['metadata'] = {}
            dag_data['metadata']['initial_values'] = init_data['init_values']
            print(f"  合并初始值: {len(init_data['init_values'])} 个节点")
        elif 'metadata' in init_data and 'initial_values' in init_data['metadata']:
            # 格式2：从 metadata.initial_values 读取
            if 'metadata' not in dag_data:
                dag_data['metadata'] = {}
            dag_data['metadata']['initial_values'] = init_data['metadata']['initial_values']
            print(f"  合并初始值: {len(init_data['metadata']['initial_values'])} 个节点")
        else:
            print(f"⚠️  警告: 初始值文件格式不正确，未找到 init_values 或 metadata.initial_values")

    # 转换为 GraphScenario
    print("🔄 转换 DAG 数据...")
    scenario, raw_nodes_data = convert_to_graph_scenario(dag_data, input_file)

    # 从 metadata.initial_values 提取初始值
    print("📋 提取初始值...")
    initial_values = extract_initial_values_from_dag_data(dag_data)

    # 将完整的 init 数据（inputs + outputs）添加到 raw_nodes_data
    # 这样 dag_executor 和 simulator 可以访问 _init_outputs
    metadata = dag_data.get('metadata', {})
    initial_values_full = metadata.get('initial_values', {})
    
    for node_id, node_init_data in initial_values_full.items():
        if node_id in raw_nodes_data:
            # 将 init_inputs 和 init_outputs 合并到 raw_nodes_data[node_id]['init']
            if 'init' not in raw_nodes_data[node_id]:
                raw_nodes_data[node_id]['init'] = {}
            
            raw_nodes_data[node_id]['init']['inputs'] = node_init_data.get('init_inputs', {})
            raw_nodes_data[node_id]['init']['outputs'] = node_init_data.get('init_outputs', {})

    # 将初始值设置到节点的输入端口（用于 DAG executor 的初始值解析）
    for node_id, init_vals in initial_values.items():
        if node_id in scenario.nodes:
            node = scenario.nodes[node_id]
            for port in node.inputs:
                if port.name in init_vals:
                    # 使用 __dict__ 直接设置属性
                    port.__dict__['init_value'] = init_vals[port.name]

    print(f"  找到 {len(initial_values)} 个节点有初始值")

    # 创建模拟器
    print("🛠️  初始化工具模拟器...")
    simulator = ToolSimulator()

    # 创建 DAG 执行器（传入 raw_nodes_data 以支持 init_outputs）
    print("⚙️  创建 DAG 执行器...")
    executor = DAGExecutor(scenario, simulator, raw_nodes_data)

    # 执行 DAG
    print("\n" + "="*60)
    print("🚀 开始执行 DAG...")
    print("="*60 + "\n")

    execution_result = executor.execute()

    # 打印执行结果摘要
    print("\n" + "="*60)
    print("📊 执行结果摘要")
    print("="*60)
    print(f"总节点数: {execution_result.total_nodes}")
    print(f"成功执行: {execution_result.executed_nodes}")
    print(f"失败节点: {len(execution_result.failed_nodes)}")
    print(f"执行成功: {execution_result.success}")

    if execution_result.failed_nodes:
        print(f"\n❌ 失败的节点: {execution_result.failed_nodes}")

    # 打印节点值
    print("\n" + "="*60)
    print("📋 节点值详情")
    print("="*60)
    for node_id, values in execution_result.node_values.items():
        print(f"\n节点: {node_id}")
        if values.get('input_values'):
            print(f"  输入值: {values['input_values']}")
        if values.get('output_values'):
            print(f"  输出值: {values['output_values']}")

    # 保存结果
    print("\n" + "="*60)
    save_results(output_file, dag_data, execution_result)
    print("="*60)

    # 返回状态码
    sys.exit(0 if execution_result.success else 1)


if __name__ == "__main__":
    main()