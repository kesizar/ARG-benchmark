#!/usr/bin/env python3
"""
细粒度指标计算脚本
基于评测轨迹进行离线分析，计算精确、客观、可量化的能力指标
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any
import statistics


# 对称工具模板映射：template_id -> 对称端口对列表
# 每个元素是一对可互换的端口名 (port_a, port_b)，
# 即将 port_a 和 port_b 的值互换后，工具输出结果不变（满足交换律）
SYMMETRIC_TOOL_TEMPLATES: Dict[str, List[Tuple[str, str]]] = {
    'text_xor_hex': [('hex_a', 'hex_b')],   # XOR: a^b == b^a
    'calc_gcd':     [('a', 'b')],            # GCD: gcd(a,b) == gcd(b,a)
    'calc_gcd_int': [('a', 'b')],            # GCD（整数版）
    'calc_bigmul':  [('a', 'b')],            # 乘法: a*b == b*a
}


class MetricsComputer:
    """指标计算器"""
    
    def __init__(self, problem_file: str, result_file: str):
        """
        初始化
        
        Args:
            problem_file: 题目文件路径
            result_file: 评测结果文件路径
        """
        with open(problem_file, 'r', encoding='utf-8') as f:
            self.problem = json.load(f)
        
        with open(result_file, 'r', encoding='utf-8') as f:
            self.result = json.load(f)
        
        self.case_id = self.result['case_id']
        
        # 解析题目信息
        self._parse_problem()
        
        # 解析评测消息上下文
        self._parse_messages()
    
    def _parse_problem(self):
        """解析题目文件，提取节点、边、golden值等信息"""
        self.all_nodes = set()
        self.initial_visible_nodes = set()
        self.edges = []  # [(src_node, src_port, dst_node, dst_port)]
        self.edges_with_type = []  # [(src_node, src_port, dst_node, dst_port, connection_type)]
        self.node_info = {}
        self.dependencies = defaultdict(set)  # {node_id: {required_nodes}}，包含所有类型的边
        self.data_dependencies = defaultdict(set)  # {node_id: {required_nodes}}，仅包含非ITEM/HIDDEN_ITEM数据依赖
        
        # 从nodes列表中提取节点信息
        nodes_data = self.problem.get('nodes', [])
        self.golden_inputs = {}   # {node_id: {param_name: value}} - 所有节点的golden输入
        self.golden_outputs = {}  # {node_id: {param_name: value}} - 所有节点的golden输出
        for node_data in nodes_data:
            node_id = node_data.get('id')
            if node_id:
                self.all_nodes.add(node_id)
                self.node_info[node_id] = node_data
                
                # 提取该节点的 golden 输入值（从 nodes[].inputs[].value）
                golden_input_dict = {}
                for input_port in node_data.get('inputs', []):
                    if 'value' in input_port:
                        param_name = input_port.get('name')
                        param_value = input_port.get('value')
                        golden_input_dict[param_name] = param_value
                
                if golden_input_dict:
                    self.golden_inputs[node_id] = golden_input_dict
                
                # 提取该节点的 golden 输出值（从 nodes[].outputs[].value）
                golden_output_dict = {}
                for output_port in node_data.get('outputs', []):
                    if 'value' in output_port:
                        param_name = output_port.get('name')
                        param_value = output_port.get('value')
                        golden_output_dict[param_name] = param_value
                
                if golden_output_dict:
                    self.golden_outputs[node_id] = golden_output_dict
        
        # 解析边
        edges_data = self.problem.get('edges', [])
        for edge in edges_data:
            src_node = edge.get('source_id', edge.get('src_node'))
            src_port = edge.get('source_port', edge.get('src_port'))
            dst_node = edge.get('target_id', edge.get('dst_node'))
            dst_port = edge.get('target_port', edge.get('dst_port'))
            connection_type = edge.get('connection_type', 'Unknown')
            
            self.edges.append((src_node, src_port, dst_node, dst_port))
            self.edges_with_type.append((src_node, src_port, dst_node, dst_port, connection_type))
            self.dependencies[dst_node].add(src_node)
            if connection_type not in ['Item', 'Hidden_Item', 'ITEM', 'HIDDEN_ITEM']:
                self.data_dependencies[dst_node].add(src_node)
            
            # 添加目标节点（可能不在节点列表中）# 不会的，一定在遍历nodes_data的时候就已经添加进all_nodes了
            # if dst_node not in self.all_nodes:
            #     self.all_nodes.add(dst_node)
        
        # 计算初始可见节点: 没有 ITEM/HIDDEN_ITEM 入边的节点初始可见
        # 这与评测框架 server.py 的 _apply_progressive_reveal_at_init() 逻辑一致
        nodes_with_item_edges = set()
        for src_node, src_port, dst_node, dst_port, conn_type in self.edges_with_type:
            if conn_type in ['Item', 'Hidden_Item', 'ITEM', 'HIDDEN_ITEM']:
                nodes_with_item_edges.add(dst_node) # 这是初始不可见的节点
        
        self.initial_visible_nodes = self.all_nodes - nodes_with_item_edges
        
        # 计算隐藏节点
        self.hidden_nodes = nodes_with_item_edges
        
        # 计算完成胜利节点所需的最少执行节点数（包含数据边和ITEM/HIDDEN_ITEM掉落边）
        self.required_node_count = self._compute_required_node_count()
    
    def _compute_required_node_count(self) -> int:
        """计算完成胜利节点所需的最少执行节点数（win节点及其全部上游依赖祖先）"""
        win_node_id = self.problem.get('metadata', {}).get('win_node_id')
        if not win_node_id:
            return 0
        
        required_nodes = set()
        stack = [win_node_id]
        
        while stack:
            node = stack.pop()
            if node in required_nodes:
                continue
            
            required_nodes.add(node)
            for parent in self.dependencies.get(node, set()):
                if parent not in required_nodes:
                    stack.append(parent)
        
        return len(required_nodes)
    
    def _parse_messages(self):
        """解析评测消息上下文，提取模型行为"""
        self.tool_calls = []  # 所有工具调用记录
        self.attempted_nodes = set()  # 尝试过的节点
        self.successfully_executed_nodes = set()  # 成功执行的节点
        self.node_attempts = defaultdict(list)  # {node_id: [attempt_record]}
        self.node_outputs = defaultdict(list)  # {node_id: [output_values_dict]}
        
        # 从messages中提取工具调用
        messages = self.result.get('messages', [])
        
        for i, msg in enumerate(messages):
            if msg.get('role') == 'assistant' and 'tool_calls' in msg:
                for tool_call in msg['tool_calls']:#每个工具调用都会被遍历，这一层不区分调用什么工具
                    function_name = tool_call['function']['name']
                    arguments = json.loads(tool_call['function']['arguments'])
                    print(f'========='*4)
                    print(f'function_name: {function_name},\n arguments: {arguments}')
                    tool_call_id = tool_call['id']
                    
                    # 查找对应的反馈
                    feedback = None
                    output_values = None
                    for j in range(i+1, len(messages)):
                        if messages[j].get('role') == 'tool' and messages[j].get('tool_call_id') == tool_call_id:
                            try:
                                feedback = messages[j].get('content') # feedback就是完整的反馈，可以说是反馈的完整文本，不管执行成功还是失败 
                            except:
                                print(f'从第{j}条消息中获取反馈失败!!!!!!')
                            # 根据不同的操作类型解析输出
                            # 1. 节点工具调用（function_name即node_id）:
                            #    格式: "Tool xxx invoked\nParameters: {...}\nOutput: {...}"
                            #       或 "Tool xxx execution successful\nParameters: {...}\nOutput: {...}"
                            if function_name not in ['investigate', 'use_item', 'submit_answer']:
                                if 'Output:' in feedback:
                                    try:
                                        output_start = feedback.find('Output:') + len('Output:')
                                        output_str = feedback[output_start:].strip()
                                        # 使用 raw_decode 避免 JSON 后的附加文本（如 "✓ All parameters are correct!..."）导致解析失败
                                        output_values, _ = json.JSONDecoder().raw_decode(output_str)
                                    except:
                                        # pass
                                        print(f"node_id型工具调用Output获取失败，从第{j}条消息中获取输出（Output）失败!!!!!!")
                            # 2. use_item 成功: "Item used successfully.\n...Content: {...}"
                            elif function_name == 'use_item' and 'Content:' in feedback:
                                try:
                                    content_start = feedback.find('Content:') + len('Content:')
                                    content_str = feedback[content_start:].strip()
                                    output_values = json.loads(content_str)
                                except:
                                    pass
                            
                            # 3. investigate 对 Item 节点成功返回内容时:
                            #    chat_completions_agent 格式: "Item content: {content}"
                            #    responses_agent 格式:        "**Content**: {content}\n"
                            #    两种格式中 content 是字典的字符串表示（如 {'key': 'val'}）或 JSON
                            elif function_name == 'investigate':
                                content_str = None
                                # 匹配 chat_completions_agent 格式
                                if 'Item content:' in feedback:
                                    try:
                                        idx = feedback.find('Item content:') + len('Item content:')
                                        raw = feedback[idx:].strip()
                                        # 去掉可能追加的 "Background clue:..." 后缀
                                        if '\n' in raw:
                                            raw = raw[:raw.find('\n')].strip() 
                                        content_str = raw
                                    except:
                                        pass
                                # 匹配 responses_agent 格式
                                elif '**Content**:' in feedback:
                                    try:
                                        idx = feedback.find('**Content**:') + len('**Content**:')
                                        raw = feedback[idx:].strip()
                                        if '\n' in raw:
                                            raw = raw[:raw.find('\n')].strip()
                                        content_str = raw
                                    except:
                                        pass
                                
                                if content_str:
                                    # 尝试 JSON 解析；若 content 是 Python dict 字符串则用 ast.literal_eval
                                    try:
                                        output_values = json.loads(content_str)
                                    except (json.JSONDecodeError, ValueError):
                                        try:
                                            import ast
                                            output_values = ast.literal_eval(content_str)
                                        except Exception:
                                            pass
                            
                            break
                    
                    # 确定node_id
                    if function_name in ['investigate', 'use_item']:
                        # 这些操作使用显式的 node_id 参数
                        node_id = arguments.get('node_id', '')
                    elif function_name == 'submit_answer':
                        # submit_answer 不对应任何节点，node_id 置空，不纳入节点统计
                        node_id = ''
                    else:
                        # 普通节点工具调用：function_name 即为 node_id
                        node_id = function_name
                    
                    # 定义 success：不同操作类型使用不同的判断方式
                    if function_name == 'submit_answer':
                        # submit_answer 成功 = feedback 中包含胜利祝贺语
                        # server 返回: {"ok": True, "is_win": True, "victory_message": "🎉 Congratulations..."}
                        # agent 会把 victory_message 或 error 写入 feedback
                        success = bool(feedback and '🎉' in feedback)
                    
                    elif function_name == 'investigate':
                        # investigate 成功 = server 返回 ok:True（节点已揭示且可调查）
                        # agent 将 ok:False 的情况格式化为 "Error: ..." 写入 feedback
                        success = bool(feedback and not feedback.startswith('Error:'))
                    
                    elif function_name == 'use_item':
                        # use_item 的 arguments 中含 node_id 字段，golden_inputs 里不含，需剔除后再比较
                        args_for_check = {k: v for k, v in arguments.items() if k != 'node_id'}
                        success = self._check_arguments_match_golden(node_id, args_for_check) if node_id else False
                    
                    else:
                        # 普通节点工具调用：参数与 golden 完全匹配则成功
                        success = self._check_arguments_match_golden(node_id, arguments) if node_id else False
                    
                    record = {
                        'step': len(self.tool_calls) + 1,
                        'function': function_name,
                        'node_id': node_id,
                        'arguments': arguments,
                        'feedback': feedback,
                        'success': success,
                        'output_values': output_values
                    }
                    
                    self.tool_calls.append(record)
                    
                    if node_id:
                        self.attempted_nodes.add(node_id)
                        self.node_attempts[node_id].append(record)
                        
                        if success:
                            self.successfully_executed_nodes.add(node_id)
                            # 保存输出值
                            if output_values:
                                self.node_outputs[node_id].append(output_values)
    
    def _check_arguments_match_golden(self, node_id: str, arguments: dict) -> bool:
        """
        检查调用参数是否与 golden 参数完全匹配。

        对于输入满足交换律的对称工具（如 XOR、GCD、乘法），如果精确匹配失败，
        还会尝试将对称端口的值互换后再做匹配，以避免对正确调用的误判。
        
        Args:
            node_id: 节点ID
            arguments: 实际调用的参数字典
            
        Returns:
            bool: 参数是否匹配（含对称工具的交换律宽容匹配）
        """
        if node_id not in self.golden_inputs:
            # 如果没有 golden 参数记录，无法判断，返回 False
            return False
        
        golden_params = self.golden_inputs[node_id]
        
        # 检查参数数量是否一致
        if len(arguments) != len(golden_params):
            return False
        
        # ---- 内部辅助：对一组 (arguments, golden) 做逐参数精确匹配 ----
        def _params_match(args: dict, golden: dict) -> bool:
            for pname, gval in golden.items():
                if pname not in args:
                    return False
                aval = args[pname]
                if aval != gval and str(aval) != str(gval):
                    return False
            return True
        
        # 1. 先做精确匹配
        if _params_match(arguments, golden_params):
            return True
        
        # 2. 对称工具：尝试将对称端口互换后再匹配
        node_data = self.node_info.get(node_id, {})
        template_id = node_data.get('template_id', '')
        symmetric_pairs = SYMMETRIC_TOOL_TEMPLATES.get(template_id, [])
        
        for port_a, port_b in symmetric_pairs:
            # 只有当两个对称端口都存在于 arguments 中时才尝试互换
            if port_a in arguments and port_b in arguments:
                swapped = dict(arguments)
                swapped[port_a], swapped[port_b] = arguments[port_b], arguments[port_a]
                if _params_match(swapped, golden_params):
                    return True
        
        return False
    
    def compute_all_metrics(self) -> Dict:
        """计算所有指标"""
        metrics = {
            'case_id': self.case_id,
            'graph_reasoning': self._compute_graph_reasoning_metrics(),
            'parameter_reasoning': self._compute_parameter_reasoning_metrics(),
            'error_recovery': self._compute_error_recovery_metrics(),
            'efficiency': self._compute_efficiency_metrics(),
            'source_priority': self._compute_source_priority_metrics(),
            'background_clue_utilization': self._compute_background_clue_utilization_metrics()
        }
        
        return metrics
    
    def _compute_graph_reasoning_metrics(self) -> Dict:
        """计算依赖图理解能力指标"""
        # 1.1 节点发现率：模型尝试过的隐藏节点占所有隐藏节点的比例
        discovered_hidden = self.attempted_nodes & self.hidden_nodes
        node_discovery_rate = len(discovered_hidden) / len(self.hidden_nodes) if self.hidden_nodes else None
        
        return {
            'node_discovery_rate': round(node_discovery_rate, 3) if node_discovery_rate is not None else None,
        }
    
    def _compute_parameter_reasoning_metrics(self) -> Dict:
        """计算参数推理能力指标"""
        # 2.2 参数收敛步数：成功解决的节点首次成功的尝试步数平均值
        convergence_steps = []
        
        for node_id in self.successfully_executed_nodes:
            attempts = self.node_attempts.get(node_id, [])
            first_success_step = None
            for idx, attempt in enumerate(attempts, start=1):
                if attempt['success']:
                    first_success_step = idx
                    break
            if first_success_step is not None:
                convergence_steps.append(first_success_step)
        
        avg_convergence = statistics.mean(convergence_steps) if convergence_steps else None
        
        return {
            'avg_convergence_steps': round(avg_convergence, 2) if avg_convergence is not None else None,
        }    
    def _compute_error_recovery_metrics(self) -> Dict:
        """计算错误类型分布"""
        # 4.2 错误类型分布
        # 细化分类：
        #   missing_dependency     : 前置依赖节点未执行（当前代码暂无来源，保留字段）
        #   wrong_parameter_value  : 参数值错误（传了错误的值）
        #   missing_required_param : 缺少必要参数
        #   wrong_parameter_name   : 参数名错误
        #   wrong_node_type        : 节点类型识别错误（对不需要参数的 Item 调用了 use_item）
        #   repeated_solved_node   : 重复调用已成功解决的节点
        #   wrong_parameter_type   : 参数类型错误（传了类型不符的值）
        #   node_not_visible       : 节点未解锁/不可见
        #   node_not_exist         : 调用了不存在的节点（"Node not found"）
        #   wrong_call_format      : 工具调用格式错误（如未传 node_id）
        #   other                  : 其他未分类错误
        # 注意：排除 wrong_parameter_value 类别，因为该类错误过于宽泛，
        # 几乎所有参数不匹配都会被归入此类，无法提供有效的区分度
        error_types = {
            'missing_dependency': 0,
            'missing_required_param': 0,
            'wrong_parameter_name': 0,
            'wrong_node_type': 0,
            'repeated_solved_node': 0,
            'wrong_parameter_type': 0,
            'node_not_visible': 0,
            'node_not_exist': 0,
            'wrong_call_format': 0,
            'other': 0
        }
        
        for call in self.tool_calls:
            if call['success']:
                continue
            
            # 只统计节点执行类操作的失败；investigate 和 submit_answer 不产生错误类型
            function_name = call.get('function', '')
            if function_name in ['investigate', 'submit_answer']:
                continue
            
            feedback = call.get('feedback', '')
            error_type_classified = 'other'
            
            # 第一层：顶层反馈文本关键字匹配
            if 'not visible yet' in feedback:
                # "Node is not visible yet." / "Tool is not visible yet." / "Item is not visible yet."
                error_type_classified = 'node_not_visible'
            elif 'missing node_id' in feedback.lower():
                # "Error: Missing node_id" → 调用时未传 node_id，属于工具调用格式错误
                error_type_classified = 'wrong_call_format'
            elif 'node not found' in feedback.lower() or 'does not exist' in feedback:
                # "Error: {\"detail\":\"Node not found\"}" → 调用了不存在的节点
                error_type_classified = 'node_not_exist'
            elif 'does not require parameters' in feedback:
                # "This item does not require parameters. Please use investigate..."
                # use_item 时对不需要参数的 Item 传了参数 → 节点类型识别错误
                error_type_classified = 'wrong_node_type'
            elif 'already been successfully unlocked' in feedback or \
                    ('already' in feedback.lower() and 'unlocked' in feedback.lower()):
                # "This item has already been successfully unlocked by you."
                error_type_classified = 'repeated_solved_node'
            else:
                # 第二层：以 "Error:" 开头的直接错误反馈
                if feedback.startswith('Error:'):
                    if 'missing required parameters' in feedback.lower() or \
                            'missing required parameter' in feedback.lower():
                        # "Error: Missing required parameters xxx" / "Error: Error: Missing required parameters xxx"
                        error_type_classified = 'missing_required_param'
                    elif 'parameter names are correct, but the parameter values are incorrect' in feedback.lower():
                        # "Error: Parameter names are correct, but the parameter values are incorrect."
                        error_type_classified = 'wrong_parameter_value'
                    elif 'parameter names do not match' in feedback.lower():
                        # "Error: Parameter names do not match. Expected: ... you provided: ..."
                        # 区分：provided=[] 是缺参数，provided 非空才是参数名错误
                        if 'you provided: []' in feedback:
                            error_type_classified = 'missing_required_param'
                        else:
                            error_type_classified = 'wrong_parameter_name'
                    elif 'hint:' in feedback.lower() and 'provided some parameters' in feedback.lower():
                        # "Error: Hint: You provided some parameters (...), but may also need: ..."
                        error_type_classified = 'missing_required_param'
                    elif 'hint:' in feedback.lower() and ('incorrect' in feedback.lower() or 'may be incorrect' in feedback.lower()):
                        # "Error: Hint: The value of parameter(s) xxx may be incorrect. Correct parameters: yyy."
                        error_type_classified = 'wrong_parameter_value'
                    elif 'must be a string type' in feedback.lower() or \
                            ('parameter' in feedback.lower() and 'type' in feedback.lower() and 'must be' in feedback.lower()):
                        # "Error: Parameter 'xxx' must be a string type" (type_error from simulator)
                        error_type_classified = 'wrong_parameter_type'
                    elif 'hint:' in feedback.lower():
                        # 其余 "Error: Hint: ..." → 参数值错误
                        error_type_classified = 'wrong_parameter_value'
                    elif 'parameter' in feedback.lower():
                        # 其余含 parameter 的 Error → 参数值错误
                        error_type_classified = 'wrong_parameter_value'
                else:
                    # 第三层：工具被正常调用但参数不是 golden
                    # 格式（新）: "Tool xxx invoked\nParameters: {...}\nOutput: {...}"
                    # 格式（旧）: "Tool xxx execution successful\nParameters: {...}\nOutput: {...}"
                    # 注意：use_item 成功（"Item used successfully"）时 success=True，不会进入此处
                    if 'invoked' in feedback or 'execution successful' in feedback or 'execution Successful' in feedback:
                        classified = False
                        try:
                            if 'Output:' in feedback:
                                output_start = feedback.find('Output:') + len('Output:')
                                output_str = feedback[output_start:].strip()
                                output_data, _ = json.JSONDecoder().raw_decode(output_str)
                                if 'error' in output_data:
                                    error_msg = output_data['error']
                                    if 'Incorrect parameters' in error_msg:
                                        # "Incorrect parameters: src, dst. Correct parameters: file_id"
                                        # 参数名传对了但值不对（或完全多余）
                                        error_type_classified = 'wrong_parameter_value'
                                    elif 'Missing required' in error_msg or 'missing required' in error_msg:
                                        error_type_classified = 'missing_required_param'
                                    elif 'You provided some parameters' in error_msg:
                                        error_type_classified = 'missing_required_param'
                                    elif 'must be a string type' in error_msg.lower() or \
                                            ('type' in error_msg.lower() and 'must be' in error_msg.lower()):
                                        error_type_classified = 'wrong_parameter_type'
                                    else:
                                        error_type_classified = 'wrong_parameter_value'
                                    classified = True
                        except:
                            pass
                        if not classified:
                            # Output 正常但输出值不是 golden → 参数值错误
                            error_type_classified = 'wrong_parameter_value'
            
            # 跳过 wrong_parameter_value 类别（已从统计中排除）
            if error_type_classified == 'wrong_parameter_value':
                continue
            error_types[error_type_classified] += 1
        
        return {
            'error_distribution': error_types,
        }
    
    def _compute_efficiency_metrics(self) -> Dict:
        """计算效率指标"""
        # 5.2 探索vs利用比率：首次尝试新节点的调用占所有节点执行类调用的比例
        # 只统计节点执行类操作（排除 investigate / submit_answer）
        node_execution_calls = []
        for call in self.tool_calls:
            function_name = call['function']
            if function_name not in ['investigate', 'submit_answer']:
                node_execution_calls.append(call)
        
        actual_node_steps = len(node_execution_calls)
        
        explored_nodes_set = set()
        exploration_attempts = 0
        for call in node_execution_calls:
            node_id = call['node_id']
            if node_id and node_id not in explored_nodes_set:
                explored_nodes_set.add(node_id)
                exploration_attempts += 1
        
        exploration_ratio = exploration_attempts / actual_node_steps if actual_node_steps > 0 else None
        
        return {
            'exploration_ratio': round(exploration_ratio, 3) if exploration_ratio is not None else None,
        }
    
    def _compute_source_priority_metrics(self) -> Dict:
        """计算源头节点相关指标"""
        # 识别源头节点: 初始可见节点中没有数据流依赖的节点
        data_dependencies = defaultdict(set)
        for src_node, src_port, dst_node, dst_port, conn_type in self.edges_with_type:
            if conn_type not in ['Item', 'Hidden_Item', 'ITEM', 'HIDDEN_ITEM']:
                data_dependencies[dst_node].add(src_node)
        
        # 源头节点 = 初始可见节点中没有数据流依赖的节点
        source_nodes = set()
        for node in self.initial_visible_nodes:
            if len(data_dependencies.get(node, set())) == 0:
                source_nodes.add(node)
        
        # 6.6 源头节点平均尝试次数
        # 统计被正确解决的源头节点及其尝试次数
        # 注意：排除 investigate 记录，因为 investigate 只是查看节点信息，不是真正的"参数尝试"
        # investigate 的 success 含义是"节点可查看"，与"参数匹配golden"语义不同
        correctly_solved_sources = set()
        source_attempt_counts = {}  # {node_id: attempt_count}

        for source_node in source_nodes:
            if source_node not in self.node_attempts:
                continue

            # 过滤掉 investigate 记录，只保留真正的执行尝试（直接调用 / use_item）
            exec_attempts = [a for a in self.node_attempts[source_node]
                             if a['function'] != 'investigate']
            if not exec_attempts:
                continue

            source_attempt_counts[source_node] = len(exec_attempts)

            # 检查是否有成功的尝试(success=True表示使用了正确的golden参数)
            for attempt in exec_attempts:
                if attempt['success']:
                    correctly_solved_sources.add(source_node)
                    break

        # 计算平均尝试次数
        if correctly_solved_sources:
            total_attempts_for_solved = sum(source_attempt_counts.get(node, 0) for node in correctly_solved_sources)
            avg_attempts_for_solved_sources = total_attempts_for_solved / len(correctly_solved_sources)
        else:
            avg_attempts_for_solved_sources = None
        
        # 6.7 依赖未就绪调用次数
        # 定义：调用节点时,其数据流前置依赖还没有被成功调用过的次数
        # 规则：
        # 1. 源头节点本身不算
        # 2. 如果前置依赖是源头节点,需要检查是否已经成功解决(不仅仅是被调用)
        # 3. 如果前置依赖是非源头节点,只需检查是否被调用过(不要求成功)
        # 注意：使用 data_dependencies（仅非 ITEM/HIDDEN_ITEM 边）而非 dependencies（所有边），
        # 因为 ITEM/HIDDEN_ITEM 边是掉落触发关系，模型只需 investigate 触发掉落链即可，
        # 不需要"用正确参数解决"掉落源节点。
        unready_dependency_calls = 0
        total_non_source_calls = 0

        # 追踪哪些节点已经被调用过
        attempted_nodes_so_far = set()
        # 追踪哪些源头节点已经成功解决
        solved_sources_so_far = set()

        for call in self.tool_calls:
            node_id = call['node_id']
            function_name = call['function']

            # 跳过非节点执行操作；use_item 也是对节点的有效操作，不应跳过
            if function_name in ['investigate', 'submit_answer']:
                continue

            # 只统计非源头节点
            if node_id in self.all_nodes and node_id not in source_nodes:
                total_non_source_calls += 1

                # 检查该节点的数据流前置依赖（排除 ITEM/HIDDEN_ITEM 掉落边）
                required_nodes = data_dependencies.get(node_id, set())

                has_unready_dependency = False
                for required_node in required_nodes:
                    # 检查前置依赖是否就绪
                    if required_node in source_nodes:
                        # 前置依赖是源头节点,需要检查是否已经成功解决
                        if required_node not in solved_sources_so_far:
                            has_unready_dependency = True
                            break
                    else:
                        # 前置依赖是非源头节点,只需检查是否被调用过
                        if required_node not in attempted_nodes_so_far:
                            has_unready_dependency = True
                            break

                if has_unready_dependency:
                    unready_dependency_calls += 1

            # 更新已尝试的节点集合
            if node_id and node_id in self.all_nodes:
                attempted_nodes_so_far.add(node_id)

                # 如果是源头节点且参数正确,更新已解决源头节点集合
                arguments = call.get('arguments', {})
                if node_id in source_nodes and self._check_arguments_match_golden(node_id, arguments):
                    solved_sources_so_far.add(node_id)

        unready_dependency_rate = unready_dependency_calls / total_non_source_calls if total_non_source_calls > 0 else None
        
        return {
            'avg_attempts_for_solved_sources': round(avg_attempts_for_solved_sources, 2) if avg_attempts_for_solved_sources is not None else None,
            'unready_dependency_rate': round(unready_dependency_rate, 3) if unready_dependency_rate is not None else None,
        }
    
    def _compute_background_clue_utilization_metrics(self) -> Dict:
        """
        计算 Background Clue 利用率指标
        
        Background Clue 告诉模型节点之间的依赖关系(边)
        该指标衡量模型在调用节点时，是否按照 Background Clue 的提示使用了上游节点的输出
        
        规则:
        1. 只统计有非掉落入边的节点(排除 ITEM 和 HIDDEN_ITEM 类型的边)
        2. 对于这些节点的每次调用，检查调用参数中是否包含所有上游节点的输出
        3. 不要求匹配 golden 值，只要参数值是上游节点的某个输出即可
        4. 不要求参数用在特定端口，只要有对应数量的上游输出在参数中即可
        
        Returns:
            {
                'clue_adherence_rate': 遵守 Background Clue 的比率,
                'clue_violation_rate': 不遵守的比率,
                'details': {
                    'total_calls_with_data_dependencies': 有数据依赖的节点调用总数,
                    'adhering_calls': 遵守的调用数,
                    'violating_calls': 违反的调用数,
                    'nodes_with_data_deps': 有数据依赖的节点列表
                }
            }
        """
        # 1. 构建非掉落入边的依赖关系: {dst_node: {src_node1, src_node2, ...}}
        data_dependencies = defaultdict(set)
        for src_node, src_port, dst_node, dst_port, conn_type in self.edges_with_type:
            # 排除掉落边
            if conn_type not in ['Item', 'Hidden_Item', 'ITEM', 'HIDDEN_ITEM']:
                data_dependencies[dst_node].add(src_node)
        
        # 2. 遍历所有工具调用，检查是否遵守 Background Clue
        total_calls = 0
        adhering_calls = 0
        violating_calls = 0
        
        # 构建一个字典来追踪到当前步骤为止，每个节点的所有输出值
        # {node_id: [all_output_values]}
        accumulated_outputs = defaultdict(list)
        
        for call in self.tool_calls:
            node_id = call['node_id']
            function_name = call['function']
            arguments = call['arguments']
            output_values = call.get('output_values')
            
            # 跳过非节点执行的调用；use_item 也是对节点的有效操作，不应跳过
            if function_name in ['investigate', 'submit_answer']:
                continue
            
            # 检查该节点是否有非掉落入边
            if node_id not in data_dependencies:
                # 该节点没有数据依赖，不计入统计
                # 但如果成功执行，更新其输出
                if output_values:
                    accumulated_outputs[node_id].append(output_values)
                continue
            
            # 该节点有数据依赖
            total_calls += 1
            required_upstream_nodes = data_dependencies[node_id]
            
            # 检查调用参数中是否包含所有上游节点的输出
            # 策略: 对于每个上游节点，检查其任意输出值是否出现在当前调用的参数中
            matched_upstream_nodes = set()
            
            for upstream_node in required_upstream_nodes:
                # 获取该上游节点到目前为止的所有输出
                upstream_outputs = accumulated_outputs.get(upstream_node, [])
                
                if not upstream_outputs:
                    # 上游节点还没有输出，无法匹配
                    continue
                
                # 将当前调用的参数转换为字符串，便于检查
                args_str = json.dumps(arguments, ensure_ascii=False)
                
                # 检查上游节点的任何输出值是否出现在参数中
                found = False
                for output_dict in upstream_outputs:
                    # output_dict 是一个字典，如 {"stdout": "12.0\n", "hex": "abc"}
                    # 检查每个输出值
                    for port_name, value in output_dict.items():
                        # 将值转换为字符串形式
                        value_str = str(value) if not isinstance(value, str) else value
                        
                        # 检查这个值是否出现在参数中
                        # 多种匹配方式: 直接匹配、JSON转义匹配
                        if (value_str in args_str or 
                            json.dumps(value, ensure_ascii=False) in args_str):
                            found = True
                            break
                    
                    if found:
                        break
                
                if found:
                    matched_upstream_nodes.add(upstream_node)
            
            # 判断是否遵守了 Background Clue
            # 要求: 所有上游节点的输出都要出现在参数中
            if matched_upstream_nodes == required_upstream_nodes:
                adhering_calls += 1
            else:
                violating_calls += 1
            
            # 更新当前节点的输出(如果有)
            if output_values:
                accumulated_outputs[node_id].append(output_values)
        
        # 计算比率
        clue_adherence_rate = adhering_calls / total_calls if total_calls > 0 else None
        clue_violation_rate = violating_calls / total_calls if total_calls > 0 else None
        
        return {
            'clue_adherence_rate': round(clue_adherence_rate, 3) if clue_adherence_rate is not None else None,
            'clue_violation_rate': round(clue_violation_rate, 3) if clue_violation_rate is not None else None,
        }


def compute_metrics_for_case(problem_file: str, result_file: str) -> Dict:
    """
    为单个案例计算所有指标
    
    Args:
        problem_file: 题目文件路径
        result_file: 评测结果文件路径
    
    Returns:
        包含所有指标的字典
    """
    computer = MetricsComputer(problem_file, result_file)
    return computer.compute_all_metrics()


def _collect_numeric_leaves(d: dict, prefix: str, result: dict):
    """
    递归收集嵌套指标字典中所有叶子数值（int/float），
    以 "section.key" 形式存入 result。
    """
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            _collect_numeric_leaves(v, full_key, result)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            result[full_key] = v


def _build_summary(all_metrics: list) -> dict:
    """
    计算所有案例各指标的平均值，构造汇总字典。
    返回与单条 metrics 结构一致的嵌套字典，外加顶层
    'case_id' = '__summary__' 以及 'case_count'。
    """
    if not all_metrics:
        return {}

    # 第一步：收集所有 key→[values] 映射
    key_values: Dict[str, list] = defaultdict(list)
    for m in all_metrics:
        leaf = {}
        # 跳过顶层的 case_id 字段
        for section_key, section_val in m.items():
            if section_key == 'case_id':
                continue
            if isinstance(section_val, dict):
                _collect_numeric_leaves(section_val, section_key, leaf)
            elif isinstance(section_val, (int, float)) and not isinstance(section_val, bool):
                leaf[section_key] = section_val
        for k, v in leaf.items():
            if v is not None:
                key_values[k].append(v)

    # 第二步：按 key 计算平均值，并重新组装成嵌套结构
    averages_flat = {}
    for k, vals in key_values.items():
        averages_flat[k] = round(sum(vals) / len(vals), 4) if vals else None

    # 将扁平 key 还原为嵌套字典
    summary_nested: dict = {'case_id': '__summary__', 'case_count': len(all_metrics)}
    for flat_key, avg_val in averages_flat.items():
        parts = flat_key.split('.')
        node = summary_nested
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = avg_val

    return summary_nested


def batch_compute_metrics(problem_dir: str, result_dir: str, output_file: str):
    """
    批量计算所有案例的指标，并在末尾附加所有案例的指标平均值汇总。
    
    Args:
        problem_dir: 题目文件目录（可以是包含 narrative/ 子目录的父目录，或直接是 narrative/ 目录）
        result_dir: 评测结果目录
        output_file: 输出文件路径
    """
    # 自动探测：如果传入的是父目录且存在 narrative/ 子目录，则自动切换进去
    narrative_subdir = os.path.join(problem_dir, 'narrative')
    if os.path.isdir(narrative_subdir):
        print(f"Auto-detected narrative subdir: {narrative_subdir}")
        problem_dir = narrative_subdir

    all_metrics = []
    skipped_no_problem = 0
    skipped_error = 0

    # 遍历result_dir下的所有结果文件
    for filename in sorted(os.listdir(result_dir)):
        if not filename.endswith('_result.json'):
            continue

        result_file = os.path.join(result_dir, filename)

        # 找到对应的题目文件
        # 兼容两种结果文件格式：
        # 1. skeleton_xxx_result.json -> skeleton_xxx_narrative.json
        # 2. skeleton_xxx_narrative_result.json -> skeleton_xxx_narrative.json
        if filename.endswith('_narrative_result.json'):
            problem_filename = filename.replace('_narrative_result.json', '_narrative.json')
        else:
            problem_filename = filename.replace('_result.json', '_narrative.json')
        problem_file = os.path.join(problem_dir, problem_filename)

        if not os.path.exists(problem_file):
            print(f"Warning: Problem file not found for {filename}")
            skipped_no_problem += 1
            continue

        print(f"Computing metrics for {filename}...")

        try:
            metrics = compute_metrics_for_case(problem_file, result_file)
            all_metrics.append(metrics)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            skipped_error += 1

    # 构造汇总条目（放在列表末尾）
    output_data = list(all_metrics)
    if all_metrics:
        summary = _build_summary(all_metrics)
        output_data.append(summary)

    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nMetrics saved to {output_file}")
    print(f"Cases analyzed        : {len(all_metrics)}")
    print(f"Skipped (no problem)  : {skipped_no_problem}")
    print(f"Skipped (error)       : {skipped_error}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Single case: python compute_fine_grained_metrics.py <problem_file> <result_file>")
        print("  Batch: python compute_fine_grained_metrics.py <problem_dir> <result_dir> <output_file>")
        sys.exit(1)
    
    if len(sys.argv) == 3:
        # 单个案例
        problem_file = sys.argv[1]
        result_file = sys.argv[2]
        
        metrics = compute_metrics_for_case(problem_file, result_file)
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    
    elif len(sys.argv) == 4:
        # 批量处理
        problem_dir = sys.argv[1]
        result_dir = sys.argv[2]
        output_file = sys.argv[3]
        
        batch_compute_metrics(problem_dir, result_dir, output_file)
