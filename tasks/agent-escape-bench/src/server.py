import json
import os
import time
import logging
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from models import GraphScenario, Node, InterfaceType
# from generator import ScenarioGenerator
from simulator import ToolSimulator
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgentEscapeBench Universal Server",
    version="1.0.0",
    description="Industrial-grade evaluation server for escape room AI agents"
)

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory State
SCENARIOS: Dict[str, GraphScenario] = {}
SIMULATORS: Dict[str, ToolSimulator] = {} # case_id -> ToolSimulator
RAW_NODES_DATA: Dict[str, Dict[str, Any]] = {} # case_id -> node_id -> raw node data (for template_id)
FILE_METADATA: Dict[str, Dict[str, Any]] = {} # case_id -> metadata (for initial_values access)

# Performance monitoring
STATS: Dict[str, Any] = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "tool_calls": defaultdict(int),
    "investigates": defaultdict(int),
    "use_items": defaultdict(int),
    "case_loads": 0,
    "start_time": datetime.now()
}

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    STATS["total_requests"] += 1
    
    try:
        response = await call_next(request)
        STATS["successful_requests"] += 1
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        return response
    except Exception as e:
        STATS["failed_requests"] += 1
        logger.error(f"{request.method} {request.url.path} - Error: {str(e)}")
        raise

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else "An error occurred"
        }
    )

# Health check endpoint
@app.get("/health")
def health_check():
    """健康检查端点"""
    uptime = (datetime.now() - STATS["start_time"]).total_seconds()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "loaded_cases": len(SCENARIOS),
        "stats": {
            "total_requests": STATS["total_requests"],
            "successful_requests": STATS["successful_requests"],
            "failed_requests": STATS["failed_requests"],
            "success_rate": STATS["successful_requests"] / max(STATS["total_requests"], 1)
        }
    }

# Statistics endpoint
@app.get("/stats")
def get_stats():
    """获取详细统计信息"""
    return {
        "stats": STATS,
        "loaded_cases": list(SCENARIOS.keys()),
        "uptime": str(datetime.now() - STATS["start_time"])
    }

def _apply_progressive_reveal_at_init(scenario: GraphScenario):
    """
    在初始化时应用渐进式暴露机制（基于ITEM/HIDDEN_ITEM边）
    
    新逻辑：
    - 如果一个节点没有 ITEM/HIDDEN_ITEM 类型的入边，它就是初始可见的
    - 如果一个节点有 ITEM/HIDDEN_ITEM 类型的入边，它初始不可见，需要等待上游触发
    
    Args:
        scenario: 场景对象
    """  
    # 收集所有有 ITEM/HIDDEN_ITEM 入边的节点
    nodes_with_item_edges = set()
    for edge in scenario.edges:
        if edge.connection_type in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]:
            nodes_with_item_edges.add(edge.target_id)
    
    logger.info(f"Nodes with ITEM/HIDDEN_ITEM incoming edges: {nodes_with_item_edges}")
    
    # 设置初始可见性：没有 ITEM/HIDDEN_ITEM 入边的节点初始可见
    initially_visible_count = 0
    for node_id, node in scenario.nodes.items():
        if node_id not in nodes_with_item_edges:
            node.is_revealed = True
            initially_visible_count += 1
            logger.info(f"Initial visible (no ITEM/HIDDEN_ITEM edges): {node_id} ({node.type})")
        else:
            node.is_revealed = False
            logger.debug(f"Initial hidden (has ITEM/HIDDEN_ITEM edges): {node_id} ({node.type})")
    
    logger.info(f"Progressive reveal initialized: {initially_visible_count}/{len(scenario.nodes)} nodes initially visible")


def _check_inputs_match_golden(arguments: Dict[str, Any], golden_inputs: Dict[str, Any]) -> bool:
    """
    检查实际输入参数是否与 golden inputs 完全匹配
    
    Args:
        arguments: 实际调用时传入的参数
        golden_inputs: 期望的正确参数值（来自 JSON 的 inputs[].value）
    
    Returns:
        True 表示所有 golden inputs 都存在且值匹配
    """
    if not golden_inputs:
        return True  # 如果没有 golden inputs，认为匹配
    
    for key, expected_value in golden_inputs.items():
        actual_value = arguments.get(key)
        # 转换为字符串比较，避免类型问题（如 int vs str）
        if str(actual_value) != str(expected_value):
            logger.debug(f"Input mismatch for '{key}': expected '{expected_value}', got '{actual_value}'")
            return False
    
    return True


def _get_parameter_validation_feedback(arguments: Dict[str, Any], golden_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    对源头节点的参数进行详细验证，返回验证反馈
    
    注意：不返回期望值（expected），避免泄漏答案
    
    Args:
        arguments: 实际调用时传入的参数
        golden_inputs: 期望的正确参数值（来自 JSON 的 inputs[].value）
    
    Returns:
        包含验证结果的字典：
        - all_correct: bool - 所有参数是否正确
        - correct_params: List[str] - 正确的参数名列表
        - incorrect_params: List[str] - 错误的参数名列表（不包含期望值）
    """
    if not golden_inputs:
        return {
            "all_correct": True,
            "correct_params": [],
            "incorrect_params": []
        }
    
    correct_params = []
    incorrect_params = []
    
    for key, actual_value in arguments.items():
        # 只对用户实际提交的参数给反馈，未提交的参数不评价
        if key not in golden_inputs:
            continue  # 该参数不在 golden 中，跳过（如 _golden_inputs 等内部参数）
        expected_value = golden_inputs[key]
        # 转换为字符串比较，避免类型问题（如 int vs str）
        if str(actual_value) == str(expected_value):
            correct_params.append(key)
        else:
            # 只记录参数名，不包含期望值，避免泄漏答案
            incorrect_params.append(key)
    
    # all_correct：用户提交的所有参数都正确，且覆盖了全部 golden 参数
    all_provided_correct = len(incorrect_params) == 0
    all_golden_covered = all(k in arguments for k in golden_inputs)
    return {
        "all_correct": all_provided_correct and all_golden_covered,
        "correct_params": correct_params,
        "incorrect_params": incorrect_params
    }


def _is_source_node(node_id: str, scenario: GraphScenario) -> bool:
    """
    判断节点是否是源头节点（完全没有任何入边的节点）
    
    源头节点定义：
    - 没有任何类型的入边（包括 DATA、ITEM、HIDDEN_ITEM）
    - 即没有任何上游节点
    
    Args:
        node_id: 节点ID
        scenario: 场景对象
    
    Returns:
        True 表示是源头节点
    """
    for edge in scenario.edges:
        if edge.target_id == node_id:
            # 只要有任何入边，就不是源头节点
            return False
    
    return True


def _check_and_reveal_ready_nodes(scenario: GraphScenario, recent_outputs: Dict[str, Any], source_node_id: str) -> List[Dict[str, Any]]:
    """
    检查并释放参数齐全的隐藏节点（渐进式暴露机制）
    
    核心逻辑：
    1. 维护"可见值集合"：包含所有被测模型当前可以看到的值
       - init_inputs 的值（初始可见）
       - 工具执行后的实际输出值（运行时获得）
       - 可见 Item 的输出值
    2. 检查隐藏节点：该节点的所有 golden_input 值是否都在可见值集合中
    3. 如果是，则释放该节点
    
    Args:
        scenario: 场景对象
        recent_outputs: 最近执行的工具的输出
        source_node_id: 刚执行的工具节点ID
        
    Returns:
        新释放的节点列表
    """
    newly_revealed = []
    
    # 构建"可见值集合"（Set of visible values）
    # 存储格式：set of values (转为字符串)
    visible_values = set()
    
    # 1. 添加有意义的 init_inputs 值到可见值集合
    # Item 的 init_inputs 不应该加入，因为它们在密室中完全用不到
    for node_id, node in scenario.nodes.items():
        # 跳过源头 Item 节点（没有入边的 Item）
        if node.type == "Item":
            has_incoming_edge = any(edge.target_id == node_id for edge in scenario.edges)
            if not has_incoming_edge:
                # 这是源头 Item，跳过其 init_inputs
                continue
        
        # 添加其他节点的 init_inputs
        for port_name, init_value in node.init_input_values.items():
            if init_value:
                visible_values.add(str(init_value))
    
    # 2. 添加已执行工具的所有历史输出值
    for node_id, node in scenario.nodes.items():
        if node.type == "Tool" and node.if_success and node.actual_outputs_history:
            # 遍历所有历史执行记录
            for output_dict in node.actual_outputs_history:
                for output_port_name, output_value in output_dict.items():
                    if output_value:
                        visible_values.add(str(output_value))
    
    # 3. 添加已被 investigate 的 Item 的 golden 输出值
    # 注意：Item 可见不等于其输出值可见，需要 investigate 后才能获得
    # 这里我们使用 actual_outputs_history 来标记 Item 是否已被 investigate
    for node_id, node in scenario.nodes.items():
        if node.type == "Item" and node.is_revealed and node.actual_outputs_history:
            # Item 通常只会被 investigate 一次，但为了一致性也使用历史列表
            for output_dict in node.actual_outputs_history:
                for port_name, port_value in output_dict.items():
                    if port_value:
                        visible_values.add(str(port_value))
    
    # 遍历所有隐藏的节点，检查其 golden_input 是否都在可见值集合中
    for node_id, node in scenario.nodes.items():
        # 跳过已可见的节点
        if node.is_revealed:
            continue
        
        # 只检查工具节点（物品节点由 ITEM 输出触发）
        if node.type != "Tool":
            continue
        
        # 检查该节点的所有 golden_input 值是否都在可见值集合中
        all_inputs_ready = True
        missing_values = []
        
        for input_port_name, golden_input_value in node.golden_input_values.items():
            # 检查这个 golden 值是否在可见值集合中
            if str(golden_input_value) not in visible_values:
                all_inputs_ready = False
                missing_values.append(f"{input_port_name}={golden_input_value}")
        
        # 如果所有 golden_input 值都在可见值集合中，释放该节点
        if all_inputs_ready and len(node.golden_input_values) > 0:
            logger.info(f"All golden inputs ready for {node_id}: {list(node.golden_input_values.values())}")
        
        # 如果所有输入都齐全，释放该节点
        if all_inputs_ready:
            node.is_revealed = True
            
            # 构建节点信息返回给模型
            node_info = {
                "id": node.id,
                "type": node.type,
                "can_investigate": True,
                "hint": "This tool's input parameters are now complete, you can use investigate to view detailed information"
            }
            
            # if node.name:
            #     node_info["name"] = node.name
            if node.description:
                node_info["description"] = node.description
            
            newly_revealed.append(node_info)
            logger.info(f"Progressive reveal: {node_id} is now ready (all inputs satisfied)")
    
    return newly_revealed


def _initialize_node_values(scenario: GraphScenario, raw_nodes_data: Dict[str, Any], metadata: Dict[str, Any]):
    """
    Initialize node state and load values from port value fields.
    应用渐进式暴露机制：初始时只显示参数齐全的节点（源头节点）
    
    重要区分：
    1. input_values: 只加载 metadata.initial_values 中的 init_inputs（真正的初始值）
    2. output_values: 加载 nodes[].outputs[].value（golden 输出，用于验证）
    """
    # 第一步：加载所有节点的值，并将所有节点初始设为隐藏
    initial_values = metadata.get('initial_values', {})
    
    for node_id, node in scenario.nodes.items():
        # 忽略 initial_visible 字段，初始全部隐藏
        # 由渐进式暴露机制根据参数齐全情况决定是否显示
        node.is_revealed = False
        
        if node.type == "Tool":
            node.if_success = False
            node.actual_outputs_history = []  # 清空历史输出
        elif node.type == "Item":
            node.if_success = False
            node.actual_outputs_history = []  # 清空历史输出
        
        # 从 JSON 加载值
        if node_id in raw_nodes_data:
            node_data = raw_nodes_data[node_id] # node_data是json文件中nodes中的字典
            
            # 【重要】只加载 metadata.initial_values 中的初始输入值
            if node_id in initial_values:
                init_data = initial_values[node_id]
                # 加载初始输入值（用于渐进式暴露判断）
                for port_name, port_value in init_data.get('init_inputs', {}).items():
                    node.init_input_values[port_name] = port_value
            
            # 【评测用】加载 golden 输入值（用于验证模型传入的参数是否正确）
            for input_port_data in node_data.get('inputs', []):
                if 'value' in input_port_data:
                    node.golden_input_values[input_port_data['name']] = input_port_data['value']
            
            # 【评测用】加载 golden 输出值（用于验证工具调用是否正确，以及 Item 节点的 content）
            for output_port_data in node_data.get('outputs', []):
                if 'value' in output_port_data:
                    node.golden_output_values[output_port_data['name']] = output_port_data['value']
            
            # For Items, set content from golden_output_values
            if node.type == "Item" and node.golden_output_values:
                # Item 的 content 是其第一个 golden 输出值
                node.content = list(node.golden_output_values.values())[0]
    
    # 第二步：应用渐进式暴露机制
    # 检查所有节点，根据参数齐全情况释放源头节点（工具 + Item）
    _apply_progressive_reveal_at_init(scenario)

def _build_node_info(node: Node, raw_nodes_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    构建节点信息（工具或物品）
    
    Args:
        node: 节点对象
        raw_nodes_data: 原始节点数据（用于获取 template_id 等）
    
    Returns:
        节点信息字典
    """
    if node.type == "Tool":
        # 过滤掉输入端口中的 ITEM/HIDDEN_ITEM 类型（trigger 端口）
        # 这些端口仅用于控制掉落机制，不应暴露给 Agent
        # 但保留输出端口（如 Terminal 的物品分发器需要让 Agent 看到）
        tool_info = {
            "id": node.id,
            # "name": node.name,
            "description": node.description,
            "type": "Tool",
            "inputs": [{"name": p.name, "type": p.type, "description": p.description} 
                      for p in node.inputs if p.type not in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]],
            "outputs": [{"name": p.name, "type": p.type, "description": p.description} 
                       for p in node.outputs]
        }
        
        # 添加 template_id（工具的标准名称）
        if node.id in raw_nodes_data:
            node_data = raw_nodes_data[node.id]
            template_id = node_data.get('template_id')
            if template_id:
                tool_info['template_id'] = template_id
        
        return tool_info
    
    elif node.type == "Item":
        return {
            "id": node.id,
            # "name": node.name,
            "description": node.description,
            "type": "Item"
        }
    
    else:
        return {
            "id": node.id,
            # "name": node.name,
            "type": node.type
        }

def _get_initial_observation(scenario: GraphScenario, raw_nodes_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate initial observation for the agent (what they see when entering the room).
    
    策略：
    - Tools: 只显示名称和描述，不显示接口定义。需要 investigate 才能获得详细接口信息。
    - Items: 只显示存在，不显示内容。需要 investigate 才能获得内容值。
    - init_inputs: 作为"可用信息"告诉模型，这些是可以用作工具参数的初始值。
    - init_outputs: 不告诉模型（这些是答案，需要模型通过调用工具获得）。
    """
    available_entities = []  # 统一的实体列表（Tools 和 Items）
    available_information = []  # 可用的初始信息（来自 init_inputs）

    # 从 metadata.initial_values 提取 init_inputs 作为可用信息
    # 只提供值本身，不透露这些值对应哪个节点的哪个参数，让模型自己推理
    # 注意：跳过源头 Item（没有入边的 Item）的 init_inputs，因为它们在密室中完全用不到
    initial_values = metadata.get('initial_values', {})
    # initial_values字段的格式
    # "initial_values": {
    #   "terminal_1": {
    #     "init_inputs": {},
    #     "init_outputs": {
    #       "text_output": "System initialization complete.",
    #       "hex_output": "48656c6c6f20576f726c64",
    #       "item_dispenser": "掉落了一张纸条，上面写着“请勿随意触摸终端”"
    #     }
    #   }
    # }
    for node_id, init_data in initial_values.items():
        # 获取节点信息，判断是否为源头 Item
        node = scenario.nodes.get(node_id)
        if node and node.type == "Item":
            # 检查是否为源头 Item（没有入边）
            has_incoming_edge = any(edge.target_id == node_id for edge in scenario.edges)
            if not has_incoming_edge:
                # 这是源头 Item，检查是否有 init_inputs
                init_inputs = init_data.get('init_inputs', {})
                if init_inputs:
                    # 有 init_inputs，需要暴露这些参数
                    for param_name, param_value in init_inputs.items():
                        available_information.append({
                            "value": param_value
                        })
                # 处理完后跳过后续的通用逻辑
                continue
        
        init_inputs = init_data.get('init_inputs', {})
        if init_inputs:
            # 为每个 init_input 值创建一个信息条目（不包含 source_node 和 parameter 信息）
            for param_name, param_value in init_inputs.items():
                available_information.append({
                    "value": param_value
                })

    for node in scenario.nodes.values():
        if node.is_revealed:
            # Tools: 只显示基本信息，提示可以 investigate 查看详细接口
            if node.type == "Tool":
                tool_info = {
                    "id": node.id, # 这里只有id而没有template_id
                    "type": "Tool",
                    "can_investigate": True,  # 可以被 investigate
                    "hint": "You can use investigate to view the tool's detailed interface information for calling"
                }
                # 只在 name 非空时添加
                # if node.name:
                #     tool_info["name"] = node.name
                # 只在 description 非空时添加
                if node.description:
                    tool_info["description"] = node.description
                
                available_entities.append(tool_info)
            
            # Items: 只显示基本信息，提示可以 investigate 查看内容
            elif node.type == "Item":
                item_info = {
                    "id": node.id, # 这里只有id而没有template_id
                    "type": "Item",
                    "can_investigate": True,  # 可以被 investigate
                    "hint": "You can use investigate to view the item's content"
                }
                # 只在 name 非空时添加
                # if node.name:
                #     item_info["name"] = node.name
                # 只在 description 非空时添加
                if node.description:
                    item_info["description"] = node.description
                
                available_entities.append(item_info)

    return {
        "narrative": scenario.intro_narrative,
        "available_entities": available_entities,  # 使用统一的实体列表
        "available_information": available_information,  # 可用的初始信息（只包含 init_inputs）
        "win_node_id": scenario.win_node_id  # 胜利节点ID，让模型知道需要关注哪个节点
    }

@app.post("/env/reset")
def reset_case(case_id: str = None, case_file_path: str = None, session_id: str = None):
    """Loads a specific case from file and resets it.
    
    Args:
        case_id: Optional case ID for resetting an existing case
        case_file_path: Path to case file for loading a new case
        session_id: Optional session ID to ensure isolation between concurrent evaluations
    """
    logger.info(f"Reset request - case_id: {case_id}, case_file_path: {case_file_path}, session_id: {session_id}")
    STATS["case_loads"] += 1

    if case_file_path:
        if not os.path.exists(case_file_path):
            logger.error(f"Case file not found: {case_file_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {case_file_path}")
        try:
            with open(case_file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                
                # 转换格式：从 DAG executor 生成的格式转换为 GraphScenario 格式
                # 1. 提取 metadata
                metadata = file_data.get('metadata', {})
                
                # 2. 生成 case_id, title, intro_narrative
                # 【修复】为每个评测会话生成唯一的 case_id，防止并发评测时状态污染
                base_name = os.path.basename(case_file_path).replace('.json', '').replace('_full', '').replace('_full2', '')
                
                if session_id:
                    # 如果提供了 session_id，使用它来确保唯一性
                    case_id = f"{base_name}_{session_id}"
                else:
                    # 否则使用时间戳和随机数确保唯一性
                    unique_suffix = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                    case_id = f"{base_name}_{unique_suffix}"
                
                file_data['case_id'] = case_id
                logger.info(f"Generated unique case_id: {case_id} (base: {base_name}, session: {session_id})")
                
                if 'title' not in file_data:
                    file_data['title'] = f"Escape Room: {file_data['case_id']}"
                
                if 'intro_narrative' not in file_data: # 目前的json文件中已经有了intro_narrative字段，不会使用下面一行的内容，而是使用每个评测问题的json文件中的对应字段
                    file_data['intro_narrative'] = 'You are trapped in a locked room. There may be tools and items in the environment - explore them and find a way to escape. You need to find a victory string to escape. When you obtain the victory string and submit it correctly, the system will clearly indicate: "🎉 Congratulations on successfully escaping the room! Your answer is correct: [your answer]".'
                
                # 3. 转换 nodes 列表为字典（DAG executor 生成的文件中 nodes 是列表格式）
                nodes_dict = {}
                for node_data in file_data['nodes']:
                    nodes_dict[node_data['id']] = node_data # 这里的id是template_id之后可能添加一个后缀
                file_data['nodes'] = nodes_dict # 把列表转成一个字典
                
                # 4. 添加缺失的字段
                if 'difficulty' not in file_data:
                    file_data['difficulty'] = metadata.get('total_nodes', 5)
                
                if 'win_node_id' not in file_data:
                    file_data['win_node_id'] = metadata.get('win_node_id', '')
                
                scenario = GraphScenario(**file_data)
                
                # Extract raw nodes data for template_id access
                # nodes 已经在上面转换为字典格式
                raw_nodes_data = file_data.get('nodes', {})
                RAW_NODES_DATA[scenario.case_id] = raw_nodes_data
                
                # Store metadata for initial values access
                FILE_METADATA[scenario.case_id] = metadata
                
                logger.info(f"Successfully parsed case file: {scenario.case_id}, nodes: {len(scenario.nodes)}, edges: {len(scenario.edges)}")
        except Exception as e:
            logger.error(f"Failed to load case file: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to load case file: {str(e)}")

        # Initialize node state and load values
        _initialize_node_values(scenario, raw_nodes_data, metadata) 

        SCENARIOS[scenario.case_id] = scenario
        simulator = ToolSimulator()
        SIMULATORS[scenario.case_id] = simulator

        logger.info(f"Case {scenario.case_id} initialized successfully - tools: {len([n for n in scenario.nodes.values() if n.type == 'Tool'])}, items: {len([n for n in scenario.nodes.values() if n.type == 'Item'])}")

        # 生成初始观察信息（进入密室后看到的环境）
        initial_observation = _get_initial_observation(scenario, raw_nodes_data, metadata)
        '''
        initial_observation的格式：
        {
            "narrative": scenario.intro_narrative,
            "available_entities": available_entities  # 使用统一的实体列表
            "available_information": available_information  # 可用的初始信息（只包含 init_inputs）
        }
        '''
        
        return {
            "ok": True,
            "message": f"Case loaded from {case_file_path}",
            "case_id": scenario.case_id,
            **initial_observation  # 直接展开初始观察信息
        }

    # 如果没有提供 case_file_path，但提供了 case_id，则尝试从内存重置
    if case_id and case_id in SCENARIOS:
        scenario = SCENARIOS[case_id]
        raw_nodes_data = RAW_NODES_DATA.get(case_id, {})
        metadata = FILE_METADATA.get(case_id, {})

        # Reset dynamic fields and re-apply progressive reveal
        # 重新初始化节点状态（包括渐进式暴露）
        _initialize_node_values(scenario, raw_nodes_data, metadata)

        logger.info(f"Case {case_id} reset - tools: {len([n for n in scenario.nodes.values() if n.type == 'Tool'])}, items: {len([n for n in scenario.nodes.values() if n.type == 'Item'])}")
        
        # 生成初始观察信息
        initial_observation = _get_initial_observation(scenario, raw_nodes_data, metadata)
        
        return {
            "ok": True,
            "message": f"Case {case_id} reset.",
            "case_id": case_id,
            **initial_observation  # 直接展开初始观察信息
        }
    
    # 如果既没有 case_file_path，也没有在内存中找到，返回错误
    raise HTTPException(
        status_code=400, 
        detail="Must provide case_file_path to load a new case, or use case_id to reset an existing case."
    )

class InvestigateRequest(BaseModel):
    node_id: str

@app.post("/env/{case_id}/investigate")
def investigate(case_id: str, req: InvestigateRequest):
    """
    Investigates a Tool or Item to reveal detailed information.
    
    - For Tools: Returns detailed interface information (inputs/outputs) needed to call the tool
    - For Items: Returns content value and triggers hidden item drops
    """
    logger.info(f"Investigate request - case_id: {case_id}, node_id: {req.node_id}")
    STATS["investigates"][case_id] += 1
    
    if case_id not in SCENARIOS:
        logger.error(f"Case not found: {case_id}")
        raise HTTPException(status_code=404, detail="Case not found")

    scenario = SCENARIOS[case_id]
    if req.node_id not in scenario.nodes:
        logger.error(f"Node not found: {req.node_id} in case {case_id}")
        raise HTTPException(status_code=404, detail="Node not found")

    node = scenario.nodes[req.node_id]

    if not node.is_revealed:
        logger.warning(f"Attempt to investigate hidden node: {req.node_id}")
        return {"ok": False, "error": "Node is not visible yet."}

    raw_nodes_data = RAW_NODES_DATA.get(case_id, {})
    newly_revealed = []
    
    # 处理 Tool 的 investigate
    if node.type == "Tool":
        logger.info(f"Investigating tool: {req.node_id}")
        
        # 返回工具的详细接口信息
        # id 字段使用 node.id（节点唯一标识），agent 用这个字段识别和调用具体的节点
        # template_id 是工具类型标识符，Agent 内部用于判断工具特性（如 terminal 类工具参数可选）
        # 注意：只过滤输入端口中的 ITEM/HIDDEN_ITEM 类型（trigger 端口），这些端口仅用于控制掉落，不应暴露给 Agent
        # 但保留输出端口（如 Terminal 的物品分发器需要让 Agent 看到）
        # 【端口上游依赖提示 & 初始值直接给出】
        # 针对参数语义模糊（全为数字类型）的工具，在 investigate 返回信息中标注
        # 哪个输入端口来自哪个上游节点（upstream_from）。
        # 对于所有工具：若该节点不是纯源头节点（有任意数据流入边），
        # 且某个端口没有上游入边（值来自初始可见参数），则直接给出该端口的 golden input 值。
        AMBIGUOUS_TOOLS = {
            "num_base_convert", "calc_modexp", "calc_modexp_int",
            "calc_inv_mod", "calc_inv_mod_int", "crypto_rsa_decrypt_hex", "geo_haversine"
        }
        # Terminal 类工具自带参数对错反馈机制，玩家/模型可自行试错，
        # 无需在 investigate 时直接暴露 init_value
        SELF_FEEDBACK_TOOLS = {
            "terminal_1", "terminal_2",
            "Logic Terminal", "Math Terminal", "Encryption Terminal", "Sequence Terminal"
        }
        _template_id_for_hint = raw_nodes_data.get(node.id, {}).get("template_id", "")
        # 构建数据流入边映射（对所有工具）：{target_port -> (source_node_id, source_port)}
        _upstream_map = {}
        for _edge in scenario.edges:
            if (_edge.target_id == node.id
                    and _edge.connection_type not in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]
                    and _edge.target_port is not None):
                _upstream_map[_edge.target_port] = (_edge.source_id, _edge.source_port)
        # 判断该节点是否有任意数据流入边（即不是纯源头节点）
        _has_any_upstream = len(_upstream_map) > 0
        # 判断该节点是否有任意入边（包括 ITEM/HIDDEN_ITEM 掉落边）
        # 有任意入边（含掉落边）但无数据流入边的节点，其输入来自初始可见参数，应直接给出
        _has_any_edge = any(_edge.target_id == node.id for _edge in scenario.edges)
        # 构建 inputs 列表
        _inputs_list = []
        for p in node.inputs:
            if p.type in [InterfaceType.ITEM, InterfaceType.HIDDEN_ITEM]:
                continue
            port_dict = {"name": p.name, "type": p.type, "description": p.description}
            if p.name in _upstream_map:
                # 该端口有上游数据流依赖，且属于语义模糊工具 → 标注来源
                if _template_id_for_hint in AMBIGUOUS_TOOLS:
                    src_node_id, src_port = _upstream_map[p.name]
                    port_dict["upstream_from"] = f"{src_node_id}.{src_port}" if src_port else src_node_id
            elif _has_any_edge and _template_id_for_hint not in SELF_FEEDBACK_TOOLS:
                # 该节点有任意入边，但此端口没有数据流入边 → 值来自初始可见参数，直接给出
                # 排除自带反馈机制的 terminal 类工具（它们通过执行结果反馈对错，无需提前暴露参数值）
                golden_val = node.golden_input_values.get(p.name)
                if golden_val is not None:
                    port_dict["init_value"] = golden_val
            _inputs_list.append(port_dict)

        tool_details = {
            "id": node.id,  # 节点 ID，用于唯一标识和调用这个具体节点
            "type": "Tool",
            "inputs": _inputs_list,
            "outputs": [{"name": p.name, "type": p.type, "description": p.description} 
                       for p in node.outputs]
        }
        
        # 添加 template_id 用于 Agent 内部判断工具类型（不会展示给被测模型）
        if node.id in raw_nodes_data:
            template_id = raw_nodes_data[node.id].get('template_id')
            if template_id:
                tool_details["_template_id"] = template_id  # 使用下划线前缀标记为内部字段
        
        # 只在 name 非空时添加
        # if node.name:
        #     tool_details["name"] = node.name
        # 只在 description 非空时添加
        if node.description:
            tool_details["description"] = node.description
        
        # 添加 narrative 字段（如果存在）
        if node.id in raw_nodes_data:
            narrative = raw_nodes_data[node.id].get('narrative')
            if narrative:
                tool_details['narrative'] = narrative
        
        # 不再返回 init_values，避免泄漏答案
        # investigate 只应该返回工具的接口定义，不应该暴露初始值
        
        # 【新增】检查该 Tool 是否有待触发的 HIDDEN_ITEM 掉落
        # 如果该工具已按照 golden_input 正确执行，且有 HIDDEN_ITEM 输出边，则触发掉落
        if node.has_hidden_item_ready:
            logger.info(f"Tool has HIDDEN_ITEM ready - triggering passive drop for: {req.node_id}")
            
            # 遍历该工具的所有 HIDDEN_ITEM 输出边
            for edge in scenario.edges:
                if edge.source_id == node.id and edge.connection_type == InterfaceType.HIDDEN_ITEM:
                    target_node = scenario.nodes[edge.target_id]
                    
                    if not target_node.is_revealed:
                        target_node.is_revealed = True
                        # 构建基本节点信息（不包含详细内容）
                        node_info = {
                            "id": target_node.id,
                            "type": target_node.type,
                            "can_investigate": True,
                            "hint": "Use investigate to view detailed information" if target_node.type == "Tool" else "Use investigate to view item content"
                        }
                        # 只在 name 非空时添加
                        # if target_node.name:
                        #     node_info["name"] = target_node.name
                        # 只在 description 非空时添加
                        if target_node.description:
                            node_info["description"] = target_node.description
                        
                        newly_revealed.append(node_info)
                        logger.info(f"HIDDEN_ITEM drop triggered: {target_node.id} (from {req.node_id} investigate)")
            
            # 重置标志，已经触发过了，避免重复
            node.has_hidden_item_ready = False
        
        logger.info(f"Tool investigation successful - node: {req.node_id}, revealed: {len(newly_revealed)}")
        
        # 构建返回结果
        result = {
            "ok": True,
            "entity_type": "Tool",
            "details": tool_details
        }
        
        # 如果有新掉落的节点，添加到响应中
        if newly_revealed:
            result["newly_revealed"] = newly_revealed
        
        return result
    
    # 处理 Item 的 investigate
    elif node.type == "Item":
        logger.info(f"Investigating item: {req.node_id}")
        
        # 【第一步】检查该 Item 是否有需要参数的输入端口
        # 如果有，且尚未通过 use_item 验证，则不返回内容，只返回参数要求
        required_inputs = []
        if node.id in raw_nodes_data:
            raw_node = raw_nodes_data[node.id]
            inputs_info = raw_node.get('inputs', [])
            required_inputs = [
                {
                    "name": inp.get("name"),
                    "type": inp.get("type"),
                    "description": inp.get("description", "")
                }
                for inp in inputs_info
                if inp.get("type") not in ["Item", "Hidden_Item"]
            ]
        
        # 如果有 required_inputs 且尚未通过 use_item 验证（if_success == False）
        # 则不返回内容，只返回参数要求提示
        if required_inputs and not node.if_success:
            logger.info(f"Item has required inputs and not yet unlocked: {req.node_id}")
            result = {
                "ok": True,
                "entity_type": "Item",
                "required_inputs": required_inputs
            }
            
            # 添加 narrative
            if node.id in raw_nodes_data:
                raw_node = raw_nodes_data[node.id]
                narrative = raw_node.get('narrative')
                if narrative:
                    result['narrative'] = narrative
            
            param_names = ', '.join([inp['name'] for inp in required_inputs])
            result["hint"] = f"This item requires parameters to unlock. Use the use_item operation with the following exact parameter names (do not change or translate): {param_names}"
            
            return result
        
        # 【新增】如果有 required_inputs 且已经通过 use_item 验证（if_success == True）
        # 则返回提示：该节点已经被成功解决
        if required_inputs and node.if_success:
            logger.info(f"Item has required inputs and already unlocked: {req.node_id}")
            result = {
                "ok": True,
                "entity_type": "Item",
                "message": "This item has already been successfully unlocked by you."
            }
            return result
        
        # 【第二步】该 Item 没有 required_inputs 或已通过验证，返回内容
        # 1. 返回 Item 的 golden_output_values（即 Item 的内容）
        # 注意：某些 Item 仅用于触发 HIDDEN_ITEM 掉落，没有实际内容
        has_actual_content = bool(node.golden_output_values) or node.content is not None
        content = node.golden_output_values if node.golden_output_values else node.content
        
        # 【关键】将 golden_output_values 追加到 actual_outputs_history，标记该 Item 已被 investigate
        # 这样在渐进式暴露时，这些值才会被加入可见值集合
        # 即使是空字典（仅触发 HIDDEN_ITEM 的 Item），也要记录，以便渐进式暴露逻辑知道该 Item 已被调查
        if node.golden_output_values is not None:
            node.actual_outputs_history.append(dict(node.golden_output_values))
        
        # 2. Trigger Hidden Item Drops (Passive Drop)
        for edge in scenario.edges:
            if edge.source_id == node.id and edge.connection_type == InterfaceType.HIDDEN_ITEM:
                target_node = scenario.nodes[edge.target_id]
                if not target_node.is_revealed:
                    target_node.is_revealed = True
                    # 构建基本节点信息（不包含详细内容）
                    node_info = {
                        "id": target_node.id,
                        "type": target_node.type,
                        "can_investigate": True,
                        "hint": "Use investigate to view detailed information" if target_node.type == "Tool" else "Use investigate to view item content"
                    }
                    # 只在 name 非空时添加
                    # if target_node.name:
                    #     node_info["name"] = target_node.name
                    # 只在 description 非空时添加
                    if target_node.description:
                        node_info["description"] = target_node.description
                    
                    newly_revealed.append(node_info)
                    logger.info(f"HIDDEN_ITEM drop triggered: {target_node.id} (from {req.node_id} investigate)")

        logger.info(f"Item investigation successful - node: {req.node_id}, has_content: {has_actual_content}, revealed: {len(newly_revealed)}")
        
        # 【渐进式暴露】旧机制（基于 golden_input）已禁用
        # 现在完全由 ITEM/HIDDEN_ITEM 边触发控制节点可见性
        # 上面的 HIDDEN_ITEM 掉落逻辑已经处理了节点释放
        # progressive_revealed = _check_and_reveal_ready_nodes(scenario, node.golden_output_values or {}, node.id)
        # if progressive_revealed:
        #     # 合并到 newly_revealed 中
        #     if newly_revealed:
        #         newly_revealed.extend(progressive_revealed)
        #     else:
        #         newly_revealed = progressive_revealed
        #     logger.info(f"Progressive reveal after Item investigate: {len(progressive_revealed)} nodes now ready")
        
        # 构建返回结果
        result = {
            "ok": True,
            "entity_type": "Item"
        }
        
        # 只在有实际内容时才添加 content 字段
        # 对于仅触发 HIDDEN_ITEM 掉落的 Item，不返回 content 字段，避免返回 None 或空字典让模型困惑
        if has_actual_content:
            result["content"] = content
        
        # 添加 narrative
        if node.id in raw_nodes_data:
            raw_node = raw_nodes_data[node.id]
            narrative = raw_node.get('narrative')
            if narrative:
                result['narrative'] = narrative
        
        if newly_revealed:
            result["newly_revealed"] = newly_revealed
        
        # 不再主动提示胜利字符串，让模型自己判断
        # 模型通过 investigate 获得内容后，需要自己识别这是否是胜利字符串
        
        return result
    
    else:
        logger.warning(f"Attempt to investigate unknown node type: {req.node_id} (type: {node.type})")
        return {"ok": False, "error": f"Cannot investigate node type: {node.type}"}

class ToolCallRequest(BaseModel):
    node_id: str  # 使用 node_id 精确指定要调用的节点
    arguments: Dict[str, Any]

@app.post("/env/{case_id}/tool_call")
def tool_call(case_id: str, req: ToolCallRequest):
    """Executes a tool and triggers item drops."""
    logger.info(f"Tool call request - case_id: {case_id}, node_id: {req.node_id}, args: {list(req.arguments.keys())}")
    STATS["tool_calls"][case_id] += 1
    
    if case_id not in SCENARIOS:
        logger.error(f"Case not found: {case_id}")
        raise HTTPException(status_code=404, detail="Case not found")

    scenario = SCENARIOS[case_id]
    raw_nodes_data = RAW_NODES_DATA.get(case_id, {})
    
    # 通过 node_id 精确查找节点
    node_id = req.node_id
    if node_id not in scenario.nodes:
        logger.error(f"Node not found: {node_id} in case {case_id}")
        raise HTTPException(status_code=404, detail="Node not found")
    
    tool_node = scenario.nodes[node_id]
    
    if not tool_node:
        logger.error(f"Tool not found: {node_id} in case {case_id}")
        raise HTTPException(status_code=404, detail="Tool not found")

    if not tool_node.is_revealed:
        logger.warning(f"Attempt to call hidden tool: {node_id}")
        return {"ok": False, "error": "Tool is not visible yet."}

    if tool_node.type != "Tool":
        logger.warning(f"Attempt to call non-tool node: {node_id} (type: {tool_node.type})")
        return {"ok": False, "error": "Only tools can be called."}

    # 1. Execute Tool (Real Execution via Simulator)
    simulator = SIMULATORS[case_id]
    
    # Get tool name from template_id if available, otherwise use node name
    tool_name = tool_node.name
    if case_id in RAW_NODES_DATA and node_id in RAW_NODES_DATA[case_id]:
        template_id = RAW_NODES_DATA[case_id][node_id].get('template_id')
        if template_id:
            tool_name = template_id
    
    # 文件处理工具和 Terminal 需要验证输入并返回预先计算的输出
    # 传递节点的实际输入输出值（从 DAG 执行后填充的数据）
    tool_arguments = dict(req.arguments)  # Make a copy
    
    # 传递节点的 golden values（从 JSON 的 inputs[].value 和 outputs[].value 加载）
    # 用于在评测阶段验证被测模型传入的参数是否正确
    if tool_node.golden_input_values:
        tool_arguments['_golden_inputs'] = tool_node.golden_input_values
    if tool_node.golden_output_values:
        tool_arguments['_golden_outputs'] = tool_node.golden_output_values
    
    logger.debug(f"Executing tool {tool_name} (node: {tool_node.name}) with args {tool_arguments}")

    try:
        output_values = simulator.execute(tool_name, tool_arguments)
        logger.info(f"Tool invoked - {tool_name}: {list(output_values.keys())}")
    except Exception as e:
        logger.error(f"Tool execution failed - {tool_name}: {str(e)}", exc_info=True)
        return {"ok": False, "error": f"Tool execution failed: {str(e)}"}

    # 检查验证结果（精细化错误反馈）
    validation = output_values.pop("_validation", {"valid": True})
    
    if not validation["valid"]:
        # 根据错误类型构造友好的错误消息
        error_type = validation.get("error_type")
        
        if error_type == "missing_required":
            missing = validation.get("missing_params", [])
            error_msg = f"Error: Missing required parameters {', '.join(missing)}"
        
        elif error_type == "type_error":
            param = validation.get("param_name")
            message = validation.get("message", "Parameter type error")
            error_msg = f"Error: {message}"
        
        elif error_type == "incomplete_optional":
            provided = validation.get("provided_params", [])
            missing = validation.get("missing_params", [])
            error_msg = (
                f"Hint: You provided some parameters ({', '.join(provided)}), "
                f"but may also need: {', '.join(missing)}.\n"
                f"Trying to provide these parameters together might yield better results."
            )
        
        elif error_type == "value_mismatch":
            param = validation.get("param_name")
            hint = validation.get("hint", "Parameter value may be incorrect")
            error_msg = f"Hint: {hint}.\nPlease check if this parameter value meets the requirements."
        
        else:
            error_msg = validation.get("hint") or validation.get("message", "Parameter validation failed")
        
        logger.info(f"Tool validation failed - {tool_name}: {error_type}")
        return {
            "ok": False,
            "error": error_msg,
            "error_type": error_type
        }
    
    # Simulate success
    tool_node.if_success = True
    
    # 【关键】将本次执行的输出值追加到历史列表（用于渐进式暴露判断）
    # 每次调用都会记录，不会覆盖之前的执行结果
    tool_node.actual_outputs_history.append(dict(output_values))

    # 2. 检查是否应该触发掉落（只有输入参数正确时才掉落）
    # 验证输入参数是否与 golden_input_values 匹配
    inputs_match_golden = _check_inputs_match_golden(req.arguments, tool_node.golden_input_values)
    
    newly_revealed = []
    investigate_hints = []  # 提示模型哪些节点可以 investigate 来发现隐藏内容
    
    if inputs_match_golden:
        logger.info(f"✓ Tool inputs match golden - node: {node_id}, triggering drops")
        
        # 检查该工具是否有 ITEM 或 HIDDEN_ITEM 输出边
        for edge in scenario.edges:
            if edge.source_id == tool_node.id:
                target_node = scenario.nodes[edge.target_id]
                
                # ITEM 边：立即掉落（主动掉落）
                if edge.connection_type == InterfaceType.ITEM:
                    if not target_node.is_revealed:
                        target_node.is_revealed = True
                        # 构建基本节点信息（不包含详细内容）
                        node_info = {
                            "id": target_node.id,
                            "type": target_node.type,
                            "can_investigate": True,
                            "hint": "Use investigate to view detailed information" if target_node.type == "Tool" else "Use investigate to view item content"
                        }
                        # 只在 name 非空时添加
                        # if target_node.name:
                        #     node_info["name"] = target_node.name
                        # 只在 description 非空时添加
                        if target_node.description:
                            node_info["description"] = target_node.description
                        
                        newly_revealed.append(node_info)
                        logger.info(f"ITEM drop triggered: {target_node.id} (from {node_id})")
                
                # HIDDEN_ITEM 边：不立即掉落，标记并提示（被动掉落）
                elif edge.connection_type == InterfaceType.HIDDEN_ITEM:
                    # 标记该工具有待触发的 HIDDEN_ITEM 掉落
                    tool_node.has_hidden_item_ready = True
                    
                    # 提示模型可以 investigate 这个工具来发现隐藏内容
                    hint_info = {
                        "tool_id": tool_node.id,
                        "hint": f"Tool '{tool_node.id}' seems to hide something, try investigating it to discover more information"
                    }
                    # if tool_node.name:
                    #     hint_info["tool_name"] = tool_node.name
                    
                    investigate_hints.append(hint_info)
                    logger.info(f"HIDDEN_ITEM ready: {tool_node.id} -> {target_node.id} (will drop on investigate)")
    else:
        logger.info(f"✗ Tool inputs do NOT match golden - node: {node_id}, no drops triggered")

    response = {
        "ok": True,
        "message": "Tool invoked",
        "output_values": output_values  # Return raw outputs to Agent
    }
    
    # 【新增】对源头节点进行参数验证反馈
    # 源头节点：没有数据流入边的节点，这些节点的参数需要模型自己推理
    # 验证模型使用的参数是否正确，并提供明确的反馈
    if _is_source_node(node_id, scenario) and tool_node.golden_input_values:
        validation_feedback = _get_parameter_validation_feedback(req.arguments, tool_node.golden_input_values)
        
        if validation_feedback["all_correct"]:
            # 用户提交了全部 golden 参数且全部正确
            response["parameter_feedback"] = {
                "status": "correct",
                "message": f"✓ All parameters are correct! This tool has been successfully solved. You can now proceed to explore downstream nodes that depend on this tool's output."
            }
            logger.info(f"✓ Source node parameters all correct - node: {node_id}")
        elif validation_feedback["incorrect_params"]:
            # 有提交了但值错误的参数，只对这些参数给出反馈
            incorrect_list = []
            for param_name in validation_feedback["incorrect_params"]:
                incorrect_list.append(f"  - Parameter '{param_name}' is incorrect")
            
            correct_info = ""
            if validation_feedback["correct_params"]:
                correct_info = f"\n✓ Correct parameters: {', '.join(validation_feedback['correct_params'])}"
            
            response["parameter_feedback"] = {
                "status": "incorrect",
                "message": (
                    f"⚠️ Some parameters are incorrect:\n" +
                    "\n".join(incorrect_list) +
                    correct_info +
                    f"\n\nHint: This is a source node. You need to reason about the correct parameter values from the available parameters. Please try using different parameter values."
                ),
                "incorrect_params": validation_feedback["incorrect_params"],
                "correct_params": validation_feedback["correct_params"]
            }
            logger.info(f"✗ Source node parameters incorrect - node: {node_id}, incorrect: {validation_feedback['incorrect_params']}")
        # else: 部分提交且全部正确 → 不给任何 parameter_feedback，避免对未提交的参数发表意见
    
    # 检查工具调用是否完全正确（输出与 golden outputs 匹配）
    # 用于给模型正向反馈，让它知道这个工具已经正确调用过，避免重复调用
    # 注意：只有当输出完全匹配时才标记为 correct，不会在错误时提供具体错误信息
    # if tool_node.golden_output_values and output_values:
    #     is_correct = True
    #     for port_name, expected_value in tool_node.golden_output_values.items():
    #         actual_value = output_values.get(port_name)
    #         if str(actual_value) != str(expected_value):
    #             is_correct = False
    #             break
        
    #     if is_correct:
    #         response["tool_call_correct"] = True
    #         logger.info(f"✓ Tool called with correct result - node: {node_id}")
    
    # 只在有新内容掉落时才返回 newly_revealed
    if newly_revealed:
        response["newly_revealed"] = newly_revealed
    
    # 添加 investigate 提示（对于有待触发 HIDDEN_ITEM 掉落的工具）
    if investigate_hints:
        response["investigate_hints"] = investigate_hints
    
    # 3. 渐进式暴露机制 - 现在完全由 ITEM/HIDDEN_ITEM 边控制
    # 旧机制（基于 golden_input 检查）已被禁用
    # 新机制中，节点的可见性只由 ITEM/HIDDEN_ITEM 边触发决定
    # 上面的 ITEM/HIDDEN_ITEM 掉落逻辑已经处理了节点释放
    # progressive_revealed = _check_and_reveal_ready_nodes(scenario, output_values, tool_node.id)
    # if progressive_revealed:
    #     # 合并到 newly_revealed 中
    #     if newly_revealed:
    #         newly_revealed.extend(progressive_revealed)
    #     else:
    #         newly_revealed = progressive_revealed
    #     response["newly_revealed"] = newly_revealed
    #     logger.info(f"Progressive reveal: {len(progressive_revealed)} nodes now ready")
    
    # Check if this is the win node
    if node_id == scenario.win_node_id:
        # 验证输出值是否等于预期的胜利值
        # 从节点的 golden_output_values 中获取预期值（在 _initialize_node_values 时从 JSON 加载）
        expected_outputs = tool_node.golden_output_values
        
        # 检查实际输出是否与预期输出匹配
        is_correct = False
        victory_string = None
        mismatch_info = []
        
        if expected_outputs and output_values:
            # 检查每个预期输出端口的值是否匹配
            is_correct = True
            for port_name, expected_value in expected_outputs.items():
                actual_value = output_values.get(port_name)
                if actual_value != expected_value:
                    is_correct = False
                    mismatch_info.append(f"Port '{port_name}': expected '{expected_value}', actual '{actual_value}'")
                    logger.warning(f"Win node output mismatch - port: {port_name}, expected: {expected_value}, actual: {actual_value}")
            
            # 如果所有输出都匹配，使用第一个输出作为胜利字符串
            if is_correct and output_values:
                victory_string = list(output_values.values())[0]
        else:
            logger.warning(f"Win node called but missing output values - expected: {expected_outputs}, actual: {output_values}")
        
        # 不再主动提示胜利字符串，让模型自己判断
        # 模型调用工具获得输出后，需要自己识别这是否是胜利字符串并提交
        if is_correct:
            logger.info(f"🎯 Win node called with correct output - case: {case_id}, node: {node_id}, victory: {victory_string}")
        else:
            logger.info(f"❌ Win node called with incorrect output - case: {case_id}, node: {node_id}")
    
    return response

class UseItemRequest(BaseModel):
    node_id: str = Field(..., description="The ID of the Item node to use (must be Item type)")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Input arguments to provide to the item")

@app.post("/env/{case_id}/use_item")
def use_item(case_id: str, req: UseItemRequest):
    """
    Use an Item node by providing input arguments.
    
    This is specifically for Item nodes that require parameters to be "unlocked" or "activated",
    such as containers that need a password/fingerprint.
    
    - Validates that the node is of type Item
    - Checks if provided arguments match the item's golden_input_values
    - If match: triggers ITEM-type edge drops and returns the item's content
    - If not match: returns error message
    """
    logger.info(f"Use item request - case_id: {case_id}, node_id: {req.node_id}, args: {req.arguments}")
    STATS["use_items"][case_id] += 1
    
    if case_id not in SCENARIOS:
        logger.error(f"Case not found: {case_id}")
        raise HTTPException(status_code=404, detail="Case not found")
    
    scenario = SCENARIOS[case_id]
    if req.node_id not in scenario.nodes:
        logger.error(f"Node not found: {req.node_id} in case {case_id}")
        raise HTTPException(status_code=404, detail="Node not found")
    
    item_node = scenario.nodes[req.node_id]
    
    if not item_node.is_revealed:
        logger.warning(f"Attempt to use hidden item: {req.node_id}")
        return {"ok": False, "error": "Item is not visible yet."}
    
    if item_node.type != "Item":
        logger.warning(f"Attempt to use non-item node: {req.node_id} (type: {item_node.type})")
        return {"ok": False, "error": "Only Item nodes can be used with use_item. Tools should be called with tool_call."}
    
    # 【新增】检查该 Item 是否已经被成功解锁
    # 如果已经被正确使用过，直接返回成功提示
    if item_node.if_success:
        logger.info(f"Item already unlocked, returning success message: {req.node_id}")
        return {
            "ok": True,
            "message": "This item has already been successfully unlocked by you."
        }
    
    # 检查该 Item 是否真的需要通过 use_item 提供参数
    # 只有当 Item 有非 Item/Hidden_Item 类型的输入时，才应该使用 use_item
    raw_nodes_data = RAW_NODES_DATA.get(case_id, {})
    if req.node_id in raw_nodes_data:
        raw_node = raw_nodes_data[req.node_id]
        inputs_info = raw_node.get('inputs', [])
        non_hidden_inputs = [
            inp for inp in inputs_info
            if inp.get("type") not in ["Item", "Hidden_Item"]
        ]
        
        if not non_hidden_inputs:
            # 该 Item 不需要参数，应该只使用 investigate
            logger.warning(f"Attempt to use_item on a node that doesn't require parameters: {req.node_id}")
            return {
                "ok": False,
                "error": "This item does not require parameters. Please use investigate to examine the item directly."
            }
    
    # 验证输入参数是否与 golden_input_values 匹配
    inputs_match_golden = _check_inputs_match_golden(req.arguments, item_node.golden_input_values)
    
    if not inputs_match_golden:
        logger.info(f"✗ Item inputs do NOT match golden - node: {req.node_id}")
        # 提供更详细的错误信息，帮助 Agent 理解问题
        # 只显示非 Item/Hidden_Item 类型的参数（Hidden_Item 由系统自动处理）
        expected_params = []
        if req.node_id in raw_nodes_data:
            raw_node = raw_nodes_data[req.node_id]
            inputs_info = raw_node.get('inputs', [])
            expected_params = [
                inp.get("name") for inp in inputs_info
                if inp.get("type") not in ["Item", "Hidden_Item"]
            ]
        
        provided_params = list(req.arguments.keys()) if req.arguments else []
        
        # 检查参数名是否匹配
        if set(expected_params) == set(provided_params):
            # 参数名正确但值不匹配 - 不泄漏正确的值
            error_msg = f"Parameter names are correct, but the parameter values are incorrect. Please try using different parameter values."
        else:
            error_msg = f"Parameter names do not match. Expected parameter names: {expected_params}, you provided: {provided_params}."
        
        return {
            "ok": False,
            "error": error_msg
        }
    
    logger.info(f"✓ Item inputs match golden - node: {req.node_id}, activating item")
    
    # 标记该 Item 已被正确使用
    item_node.if_success = True
    
    # 将 golden_output_values 追加到 actual_outputs_history
    if item_node.golden_output_values:
        item_node.actual_outputs_history.append(dict(item_node.golden_output_values))
    
    # 触发 ITEM 类型边的掉落
    newly_revealed = []
    for edge in scenario.edges:
        if edge.source_id == item_node.id and edge.connection_type == InterfaceType.ITEM:
            target_node = scenario.nodes[edge.target_id]
            
            if not target_node.is_revealed:
                target_node.is_revealed = True
                # 构建基本节点信息（不包含详细内容）
                node_info = {
                    "id": target_node.id,
                    "type": target_node.type,
                    "can_investigate": True,
                    "hint": "Use investigate to view detailed information" if target_node.type == "Tool" else "Use investigate to view item content"
                }
                # 只在 name 非空时添加
                # if target_node.name:
                #     node_info["name"] = target_node.name
                # 只在 description 非空时添加
                if target_node.description:
                    node_info["description"] = target_node.description
                
                newly_revealed.append(node_info)
                logger.info(f"ITEM drop triggered: {target_node.id} (from use_item on {req.node_id})")
    
    # 检查是否为 Win Node
    win_node_id = scenario.win_node_id
    is_win_node = (req.node_id == win_node_id)
    
    # 构建返回结果
    result = {
        "ok": True,
        "message": "Item used successfully.",
        "content": item_node.golden_output_values if item_node.golden_output_values else None
    }
    
    # 获取 narrative（如果存在）
    raw_nodes_data = RAW_NODES_DATA.get(case_id, {})
    if req.node_id in raw_nodes_data:
        narrative = raw_nodes_data[req.node_id].get('narrative')
        if narrative:
            result['narrative'] = narrative
    
    if newly_revealed:
        result["newly_revealed"] = newly_revealed
    
    # 不再主动提示胜利字符串，让模型自己判断
    # 如果是 Win Node，只记录日志
    if is_win_node:
        logger.info(f"Win node (Item) unlocked via use_item - case: {case_id}, node: {req.node_id}")
    
    return result


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., description="The victory string to submit")

@app.post("/env/{case_id}/submit_answer")
def submit_answer(case_id: str, req: SubmitAnswerRequest):
    """
    提交答案接口
    被测模型在获得胜利字符串提示后，需要调用此接口提交答案
    """
    logger.info(f"Submit answer request - case_id: {case_id}, answer: {req.answer}")
    
    if case_id not in SCENARIOS:
        logger.error(f"Case not found: {case_id}")
        raise HTTPException(status_code=404, detail="Case not found")
    
    scenario = SCENARIOS[case_id]
    
    # 获取 win_node 的 golden_output_values
    if not scenario.win_node_id:
        logger.error(f"No win node defined for case: {case_id}")
        return {
            "ok": False,
            "error": "This case has no victory node defined"
        }
    
    win_node = scenario.nodes.get(scenario.win_node_id)
    if not win_node:
        logger.error(f"Win node not found: {scenario.win_node_id}")
        return {
            "ok": False,
            "error": "Victory node does not exist"
        }
    
    # 获取正确的胜利字符串（取第一个 golden_output_value）
    if win_node.golden_output_values:
        correct_answer = list(win_node.golden_output_values.values())[0]
    else:
        logger.error(f"Win node has no golden_output_values: {scenario.win_node_id}")
        return {
            "ok": False,
            "error": "Victory node has no correct answer"
        }
    
    # 验证提交的答案
    if req.answer == correct_answer:
        logger.info(f"🎉 CORRECT ANSWER SUBMITTED - case: {case_id}, answer: {req.answer}")
        return {
            "ok": True,
            "is_win": True,
            "victory_message": f"🎉 Congratulations on successfully escaping the room! Your answer is correct: {req.answer}"
        }
    else:
        logger.info(f"❌ INCORRECT ANSWER SUBMITTED - case: {case_id}, submitted: {req.answer}, correct: {correct_answer}")
        return {
            "ok": True,
            "is_win": False,
            "error": f"The submitted answer is incorrect. You submitted: {req.answer}"
        }

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)