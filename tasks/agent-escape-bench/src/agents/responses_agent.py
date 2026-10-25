"""
OpenAI Responses API 实现
使用最新的 Responses API 和原生 Function Calling
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime

from .base_agent import BaseModelAgent

logger = logging.getLogger(__name__)


class ResponsesAgent(BaseModelAgent):
    """
    OpenAI Responses API 实现
    
    使用新的 Responses API，支持：
    - 原生 Function Calling
    - 更简洁的 API 结构
    - 更好的性能和缓存
    """
    
    def __init__(self, 
                 model: str = "gpt-4.1",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1500,
                 max_history_messages: int = 20,
                 max_retries: int = 3,
                 store: bool = False,  # 是否存储响应（用于状态管理）
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        初始化 Responses Agent
        
        Args:
            store: 是否存储响应以便状态管理
            default_headers: 自定义HTTP请求头（如 {"uid": "xxx"}）
            其他参数见 BaseModelAgent
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history_messages=max_history_messages,
            max_retries=max_retries,
            **kwargs
        )
        
        self.store = store
        
        # 初始化 OpenAI 客户端
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not provided and not found in environment")
        
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if default_headers:
            client_kwargs["default_headers"] = default_headers
        
        self.client = OpenAI(**client_kwargs)
        
        # 上下文（input items）
        self.context = []
        self.instructions = None
        
        # Function calling 相关
        self.tools = None
        
        # 响应 ID 链（用于 previous_response_id）
        self.last_response_id = None
        
        # 多工具调用状态
        self.pending_tool_calls = []  # 存储待处理的工具调用
        self.tool_call_results = []  # 存储工具调用结果
        
        logger.info(f"Initialized ResponsesAgent - model: {model}, store: {store}")
    
    def initialize(self, initial_data: Dict[str, Any]):
        """初始化 agent，接收初始环境信息"""
        self.start_time = datetime.now()
        self.narrative = initial_data.get("narrative", "")
        self.available_entities = initial_data.get("available_entities", [])
        self.available_information = initial_data.get("available_information", [])
        self.win_node_id = initial_data.get("win_node_id", "")  # 胜利节点 ID
        
        # 构造 instructions（system-level guidance）
        self.instructions = self._build_system_prompt()
        
        # 构造初始 input
        initial_message = self._build_initial_message()
        self.context = [
            {"role": "user", "content": initial_message}
        ]
        
        # 构建工具定义（初始为空，只有 investigate）
        self.tools = self._build_tools_schema()
        
        logger.info(f"Agent initialized - entities: {len(self.available_entities)}, tools: {len(self.available_tools)}")
    
    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """构建 Responses API 的工具定义（扁平结构）"""
        tools = []
        
        # 为每个已 investigate 的工具节点创建函数定义
        for tool in self.available_tools:
            # id 字段存储的是 node_id（节点唯一标识）
            node_id = tool.get('id')
            
            # 使用工具的描述（如果有的话）
            description = tool.get('description', f"Tool node {node_id}")
            
            tool_def = {
                "type": "function",
                "name": node_id,  # 使用 node_id 作为函数名，唯一标识这个节点
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            }
            
            # 检查是否为 terminal 类工具（terminal 的所有输入参数都是可选的）
            template_id = tool.get('_template_id', '')
            is_terminal = (
                template_id.startswith('terminal') or 
                'terminal' in template_id.lower() or
                node_id.startswith('terminal')  # 也检查 node_id 作为后备
            )
            
            # 添加输入参数，区分必需和可选参数
            if tool.get('inputs'):
                for inp in tool['inputs']:
                    param_type = self._convert_type_to_json_schema(inp['type'])
                    param_description = inp.get('description', '')
                    
                    tool_def["parameters"]["properties"][inp['name']] = {
                        "type": param_type,
                        "description": param_description
                    }
                    
                    # 检查是否为可选参数
                    # 1. terminal 类工具的所有输入参数都是可选的
                    # 2. 描述中包含 "optional"、"default" 等关键字的参数
                    is_optional = is_terminal or (
                        'optional' in param_description.lower() or
                        '(optional)' in param_description.lower() or
                        'optional:' in param_description.lower() or
                        'default' in param_description.lower() or
                        '(default' in param_description.lower()
                    )
                    
                    if not is_optional:
                        tool_def["parameters"]["required"].append(inp['name'])
            
            tools.append(tool_def)
        
        # 添加 investigate 函数
        tools.append({
            "type": "function",
            "name": "investigate",
            "description": "Investigate an item or information, may discover hidden content",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "ID of the item or information to investigate"
                    }
                },
                "required": ["node_id"],
                "additionalProperties": False
            }
        })
        
        # 添加 use_item 函数
        tools.append({
            "type": "function",
            "name": "use_item",
            "description": "For items that require parameters to unlock (such as containers, safes), provide necessary parameters to use them. Can only be used for Item type nodes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Item node ID to use (must be Item type)"
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Parameters to provide to the item, parameter names and values must match required_inputs returned by investigate",
                        "additionalProperties": True
                    }
                },
                "required": ["node_id", "arguments"],
                "additionalProperties": False
            }
        })
        
        # 添加 submit_answer 函数
        tools.append({
            "type": "function",
            "name": "submit_answer",
            "description": "[ULTIMATE GOAL] Submit the victory string to complete the task and escape the room. When you believe you have obtained the victory string, call this function to submit it. If correct, the system will return '🎉 Congratulations on successfully escaping the room! Your answer is correct: [your answer]'. Only by successfully calling this function is the task truly completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The complete victory string informed by the system (could be a description, code, numbers, or any form of text)"
                    }
                },
                "required": ["answer"],
                "additionalProperties": False
            }
        })
        
        return tools
    
    def _convert_type_to_json_schema(self, type_str: str) -> str:
        """将类型字符串转换为 JSON Schema 类型"""
        type_mapping = {
            "String": "string",
            "Integer": "integer",
            "Float": "number",
            "Boolean": "boolean",
            "Hex_String": "string",
            "Binary_String": "string",
            "Path": "string",
            "Code": "string",
            "Markdown": "string",
            "JSON": "string",
            "CSV": "string"
        }
        return type_mapping.get(type_str, "string")
    
    def _trim_context(self):
        """修剪上下文，保持在最大长度限制内"""
        if len(self.context) > self.max_history_messages:
            self.context = self.context[-self.max_history_messages:]
            logger.debug(f"Trimmed context to {len(self.context)} items")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def _call_api(self, input_items: List, tools: List) -> Any:
        """带重试机制的 API 调用"""
        params = {
            "model": self.model,
            "instructions": self.instructions,
            "input": input_items,
            "tools": tools,
            "store": self.store
        }
        
        # 如果有 previous_response_id，可以使用它来链接响应
        # if self.last_response_id and self.store:
        #     params["previous_response_id"] = self.last_response_id
        
        return self.client.responses.create(**params)
    
    def step(self) -> Optional[Dict[str, Any]]:
        """执行一步推理，返回要执行的动作"""
        try:
            # 修剪上下文
            self._trim_context()
            
            logger.debug(f"Calling Responses API - model: {self.model}, context items: {len(self.context)}")
            start_time = time.time()
            
            # 调用 API
            response = self._call_api(self.context, self.tools)
            
            elapsed = time.time() - start_time
            self.api_calls += 1
            
            # 保存响应 ID
            if hasattr(response, 'id'):
                self.last_response_id = response.id
            
            # 更新 token 统计（如果可用）
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.input_tokens or 0
                output_tokens = response.usage.output_tokens or 0
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                cost = self._estimate_cost(input_tokens, output_tokens)
                self.total_cost += cost
                
                logger.info(f"API call #{self.api_calls} - elapsed: {elapsed:.2f}s, tokens: {input_tokens}/{output_tokens}, cost: ${cost:.4f}")
            
            # 处理 output items - 支持多个工具调用
            actions, function_calls = self._handle_output(response.output)
            
            # 将 output 添加到 context 中（用于下次调用）
            self.context.extend(response.output)
            
            # 如果有多个工具调用，返回并行调用格式
            if len(actions) > 1:
                # 存储待处理的工具调用
                self.pending_tool_calls = function_calls
                self.tool_call_results = []
                
                logger.info(f"Parsed {len(actions)} actions")
                return {
                    "action": "parallel_tool_calls",
                    "tool_calls": actions,
                    "count": len(actions)
                }
            elif len(actions) == 1:
                # 单个工具调用
                logger.info(f"Parsed action: {actions[0].get('action', 'unknown')}")
                return actions[0]
            else:
                # 没有工具调用
                logger.warning("No function call found in output")
                return {
                    "action": "wait",
                    "reasoning": "No function call in response"
                }
            
        except Exception as e:
            logger.error(f"Agent step error: {e}", exc_info=True)
            return {
                "action": "wait",
                "reasoning": f"Error: {str(e)}"
            }
    
    def _handle_output(self, output_items: List) -> tuple[List[Dict[str, Any]], List]:
        """
        处理 Responses API 的 output items，支持多个工具调用
        
        Args:
            output_items: Responses API 返回的 output items
            
        Returns:
            tuple: (actions列表, function_call items列表)
        """
        actions = []
        function_calls = []
        
        # 查找所有 function_call items
        for item in output_items:
            if hasattr(item, 'type') and item.type == "function_call":
                function_name = item.name
                arguments = json.loads(item.arguments)
                call_id = item.call_id
                
                logger.debug(f"Function call: {function_name}, args: {arguments}, call_id: {call_id}")
                
                function_calls.append(item)
                
                # 解析函数名
                if function_name == "investigate":
                    actions.append({
                        "action": "investigate",
                        "node_id": arguments.get("node_id"),
                        "reasoning": f"Investigate {arguments.get('node_id')}",
                        "tool_call_id": call_id
                    })
                elif function_name == "use_item":
                    actions.append({
                        "action": "use_item",
                        "node_id": arguments.get("node_id"),
                        "arguments": arguments.get("arguments", {}),
                        "reasoning": f"Use item {arguments.get('node_id')} (params: {arguments.get('arguments', {})})",
                        "tool_call_id": call_id
                    })
                elif function_name == "submit_answer":
                    actions.append({
                        "action": "submit_answer",
                        "answer": arguments.get("answer"),
                        "reasoning": f"Submit answer: {arguments.get('answer')}",
                        "tool_call_id": call_id
                    })
                else:
                    # function_name 就是 node_id
                    # 验证该节点是否在 available_tools 中（已被 investigate）
                    matching_tool = self._find_tool_by_node_id(function_name)
                    
                    if matching_tool:
                        actions.append({
                            "action": "tool_call",
                            "node_id": function_name,  # function_name 就是 node_id
                            "arguments": arguments,
                            "reasoning": f"Call node {function_name}",
                            "tool_call_id": call_id
                        })
                    else:
                        logger.warning(f"Unknown node or not investigated: {function_name}")
                        actions.append({
                            "action": "error",
                            "reasoning": f"Unknown node or not investigated: {function_name}",
                            "tool_call_id": call_id,
                            "error": f"Node '{function_name}' not found or not investigated yet"
                        })
        
        return actions, function_calls
    
    def _find_tool_by_node_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 node_id 查找工具节点
        
        Args:
            node_id: 节点的唯一标识符
            
        Returns:
            Optional[Dict[str, Any]]: 找到的工具信息，未找到则返回 None
        """
        for tool in self.available_tools:
            if tool.get('id') == node_id:
                return tool
        return None
    
    def receive_feedback(self, result: Dict[str, Any], tool_call_id: Optional[str] = None):
        """
        接收环境的反馈
        
        Args:
            result: 执行结果
            tool_call_id: 工具调用的 ID（用于并行工具调用）
        """
        # 如果有 tool_call_id，说明是并行工具调用的一部分
        if tool_call_id:
            self.tool_call_results.append({
                "tool_call_id": tool_call_id,
                "result": result
            })
            
            # 如果还没收集完所有结果，直接返回
            if len(self.tool_call_results) < len(self.pending_tool_calls):
                logger.debug(f"Collected {len(self.tool_call_results)}/{len(self.pending_tool_calls)} tool call results")
                return
            
            # 所有结果都收集完毕，批量处理
            logger.info(f"All {len(self.tool_call_results)} tool call results collected, processing feedback")
            self._process_parallel_feedback()
            
            # 清空状态
            self.pending_tool_calls = []
            self.tool_call_results = []
            return
        
        # 单个动作的反馈处理（原有逻辑）
        feedback_content = "## Execution Result\n\n"
        
        if result.get("ok"):
            # 特殊处理：submit_answer 失败的情况（ok=True, is_win=False）
            if result.get("is_win") == False and result.get("error"):
                feedback_content += "❌ Answer submission failed\n\n"
                feedback_content += f"**Error**: {result.get('error')}\n"
            else:
                feedback_content += "✅ Operation successful\n\n"
            
            # 处理 Tool investigate 的结果
            if result.get("entity_type") == "Tool":
                feedback_content += "**Tool Investigation Result**\n\n"
                details = result.get("details", {})
                
                # 添加工具的详细信息到 available_tools
                # 使用 node_id 作为唯一标识符
                tool_id = details.get('id')
                if details and tool_id and tool_id not in [t.get('id') for t in self.available_tools]:
                    self.available_tools.append(details)
                    self.investigated_entities.add(tool_id)
                    logger.info(f"Tool investigated and added: {tool_id}")
                    
                    # 重新构建 tools schema（现在包含这个工具）
                    self.tools = self._build_tools_schema()
                    logger.debug(f"Rebuilt tools schema with {len(self.tools)} tools")
            
            # 显示工具详细信息（使用 node_id）
                feedback_content += f"Tool: `{tool_id}`\n"
                # if details.get('name'):
                #     feedback_content += f"Name: {details.get('name')}\n"
                if details.get('description'):
                    feedback_content += f"Function: {details.get('description')}\n"
                
                # 显示 narrative（如果存在）- 提供故事背景和线索
                if details.get('narrative'):
                    feedback_content += f"\n**Background Clue**: {details.get('narrative')}\n"
                
                if details.get('inputs'):
                    feedback_content += "**Input Parameters**:\n"
                    for inp in details['inputs']:
                        line = f"  - `{inp['name']}` ({inp['type']}): {inp.get('description', 'N/A')}"
                        if inp.get('upstream_from'):
                            line += f" [upstream: {inp['upstream_from']}]"
                        elif 'init_value' in inp:
                            line += f" [value: {inp['init_value']}]"
                        feedback_content += line + "\n"
                
                if details.get('outputs'):
                    feedback_content += "**Output Parameters**:\n"
                    for out in details['outputs']:
                        feedback_content += f"  - `{out['name']}` ({out['type']}): {out.get('description', 'N/A')}\n"
                
                feedback_content += "\nYou can now call this tool!\n"
            
            # 处理 Item investigate 的结果
            elif result.get("entity_type") == "Item":
                feedback_content += "**Item Investigation Result**\n\n"
                
                # 【新增】检查是否已经被成功解锁
                if result.get("message"):
                    # 已经被成功解锁,只显示消息,不显示 narrative
                    feedback_content += f"✓ {result['message']}\n"
                # 检查是否有 required_inputs (需要使用 use_item 的情况)
                elif result.get("required_inputs"):
                    feedback_content += "**⚠️ This item requires parameters to unlock**\n\n"
                    feedback_content += "**Required Parameters** (use with `use_item`):\n"
                    for inp in result["required_inputs"]:
                        feedback_content += f"  - `{inp['name']}` ({inp['type']}): {inp.get('description', 'N/A')}\n"
                    feedback_content += "\n"
                    
                    # 添加 hint（如果存在）
                    # if result.get('hint'):
                    #     feedback_content += f"**💡 Hint**: {result['hint']}\n\n"
                    
                    # 显示 narrative（如果存在）- 只在未解锁时显示
                    if result.get('narrative'):
                        feedback_content += f"\n**Background Clue**: {result.get('narrative')}\n"
                else:
                    # 已经解锁或没有 required_inputs
                    content = result.get("content")
                    if content:
                        feedback_content += f"**Content**: {content}\n"
                    
                    # 显示 narrative（如果存在）- 只在未解锁时显示
                    if result.get('narrative'):
                        feedback_content += f"\n**Background Clue**: {result.get('narrative')}\n"
            
            # 处理 Tool 调用的结果
            elif "output_values" in result:
                feedback_content += "**Tool Call Result**\n\n"
                feedback_content += f"**Output Values**: {json.dumps(result['output_values'], ensure_ascii=False)}\n"
                
                # 【新增】处理源头节点的参数验证反馈
                if result.get("parameter_feedback"):
                    feedback_content += f"\n{result['parameter_feedback']['message']}\n"
                
                # 如果工具调用完全正确（输出与预期匹配），添加正向反馈
                if result.get("tool_call_correct"):
                    feedback_content += "\n✓ **This tool call result is correct**\n"
            
            # 处理 use_item 的结果
            elif result.get("message") and not result.get("entity_type"):
                feedback_content += f"**Use Item Result**\n\n"
                feedback_content += f"{result.get('message')}\n"
                
                # 只有在成功解锁(不是"已经解锁")时才显示 narrative 和 content
                if result.get("message") != "This item has already been successfully unlocked by you.":
                    # Add narrative (if exists)
                    if result.get('narrative'):
                        feedback_content += f"\n**Background Clue**: {result.get('narrative')}\n"
                    
                    # Add content (item content)
                    if result.get('content'):
                        feedback_content += f"\n**Content**: {json.dumps(result.get('content'), ensure_ascii=False)}\n"
            
            # 处理新揭示的实体
            if result.get("newly_revealed"):
                newly_revealed = result['newly_revealed']
                if newly_revealed:
                    feedback_content += "\n**Newly Discovered Entities**:\n"
                    for entity in newly_revealed:
                        # 添加到 available_entities
                        if entity['id'] not in [e['id'] for e in self.available_entities]:
                            self.available_entities.append(entity)
                            logger.info(f"New entity revealed: {entity['id']}, type: {entity.get('type')}")
                        
                        # 显示基本信息
                        feedback_content += f"\n- **{entity.get('type')}**: `{entity['id']}`\n"
                        # if entity.get('name'):
                        #     feedback_content += f"  Name: {entity['name']}\n"
                        if entity.get('description'):
                            feedback_content += f"  Description: {entity['description']}\n"
                        if entity.get('hint'):
                            feedback_content += f"  Hint: {entity['hint']}\n"
            
            # 处理 investigate 提示（HIDDEN_ITEM 掉落提示）
            if result.get("investigate_hints"):
                hints = result['investigate_hints']
                if hints:
                    feedback_content += "\n**💡 Exploration Hints**:\n"
                    for hint in hints:
                        tool_id = hint.get('tool_id')
                        tool_name = hint.get('tool_name', tool_id)
                        hint_text = hint.get('hint', '')
                        feedback_content += f"- Tool `{tool_name}`: {hint_text}\n"
            
            # 处理胜利条件
            if result.get("is_win"):
                feedback_content += f"\n🎉 {result.get('victory_message', 'Congratulations on escaping!')}\n"
            # 处理胜利尝试失败（调用了胜利节点但输出值不正确）
            elif result.get("win_attempt_feedback"):
                feedback_content += f"\n⚠️ {result.get('win_attempt_feedback')}\n"
        else:
            feedback_content += f"❌ Operation failed\n\n"
            feedback_content += f"**Error**: {result.get('error', 'Unknown error')}\n"
        
        # 添加到 context（作为 user message）
        self.context.append({
            "role": "user",
            "content": feedback_content
        })
        
        logger.debug(f"Feedback: {feedback_content[:200]}...")
    
    def _process_parallel_feedback(self):
        """
        处理并行工具调用的反馈
        根据 Responses API 规范，需要为每个 function_call 添加对应的 function_call_output
        """
        # 按照 Responses API 的格式，需要为每个 function_call 返回一个 function_call_output
        for result_data in self.tool_call_results:
            tool_call_id = result_data["tool_call_id"]
            result = result_data["result"]
            
            # 构建工具调用结果
            output_content = self._build_tool_output_content(result)
            
            # 添加 function_call_output 到 context
            self.context.append({
                "type": "function_call_output",
                "call_id": tool_call_id,
                "output": output_content
            })
            
            # 更新内部状态（处理新揭示的实体、工具等）
            self._update_state_from_result(result)
        
        logger.info(f"Added {len(self.tool_call_results)} function_call_output items to context")
    
    def _build_tool_output_content(self, result: Dict[str, Any]) -> str:
        """
        构建工具调用结果的输出内容
        
        Args:
            result: 工具调用的结果
            
        Returns:
            str: 格式化的结果消息
        """
        if not result.get("ok"):
            return json.dumps({"error": result.get('error', 'Unknown error')}, ensure_ascii=False)
        
        output = {}
        
        # 处理 Tool investigate 的结果
        if result.get("entity_type") == "Tool":
            details = result.get("details", {})
            output["type"] = "tool_investigation"
            output["tool_name"] = details.get('id')
            output["description"] = details.get('description', 'N/A')
            
            # 添加 narrative（如果存在）
            if details.get('narrative'):
                output["narrative"] = details.get('narrative')
            
            if details.get('inputs'):
                output["inputs"] = [
                    {
                        "name": inp['name'],
                        "type": inp['type'],
                        "description": inp.get('description', 'N/A'),
                        **({"upstream_from": inp["upstream_from"]} if inp.get("upstream_from") else {}),
                        **({"init_value": inp["init_value"]} if "init_value" in inp else {})
                    }
                    for inp in details['inputs']
                ]
            
            if details.get('outputs'):
                output["outputs"] = [
                    {
                        "name": out['name'],
                        "type": out['type'],
                        "description": out.get('description', 'N/A')
                    }
                    for out in details['outputs']
                ]
        
        # 处理 Item investigate 的结果
        elif result.get("entity_type") == "Item":
            output["type"] = "item_investigation"
            
            # 【三态处理】与 chat_completions_agent 保持一致
            # 状态1：已经被成功解锁（有 message 字段）
            if result.get("message"):
                output["status"] = "already_unlocked"
                output["message"] = result.get("message")
            # 状态2：需要参数才能解锁（有 required_inputs 字段）
            elif result.get("required_inputs"):
                output["status"] = "requires_unlock"
                output["required_inputs"] = [
                    {
                        "name": inp['name'],
                        "type": inp['type'],
                        "description": inp.get('description', 'N/A')
                    }
                    for inp in result["required_inputs"]
                ]
                # 添加 narrative（如果存在）- 只在未解锁时显示
                if result.get('narrative'):
                    output["narrative"] = result.get('narrative')
            # 状态3：普通 Item（有 content 字段或无内容）
            else:
                output["status"] = "accessible"
                if result.get('content') is not None:
                    output["content"] = result.get('content')
                # 添加 narrative（如果存在）
                if result.get('narrative'):
                    output["narrative"] = result.get('narrative')
        
        # 处理 Tool 调用的结果
        elif "output_values" in result:
            output["type"] = "tool_execution"
            output["output_values"] = result['output_values']
            
            # 【新增】处理源头节点的参数验证反馈
            if result.get("parameter_feedback"):
                output["parameter_feedback"] = result["parameter_feedback"]
            
            # 如果工具调用完全正确（输出与预期匹配），添加正向反馈
            if result.get("tool_call_correct"):
                output["tool_call_correct"] = True
        
        # 处理新揭示的实体
        if result.get("newly_revealed"):
            newly_revealed = result['newly_revealed']
            if newly_revealed:
                output["newly_revealed"] = [
                    {
                        "type": entity.get('type'),
                        "id": entity['id']
                    }
                    for entity in newly_revealed
                ]
        
        # 处理 investigate 提示（HIDDEN_ITEM 掉落提示）
        if result.get("investigate_hints"):
            hints = result['investigate_hints']
            if hints:
                output["investigate_hints"] = [
                    {
                        "tool_id": hint.get('tool_id'),
                        "tool_name": hint.get('tool_name'),
                        "hint": hint.get('hint')
                    }
                    for hint in hints
                ]
        
        # 处理胜利条件
        if result.get("is_win"):
            output["victory"] = True
            output["victory_message"] = result.get('victory_message', 'Congratulations on escaping!')
        # 处理 submit_answer 失败（is_win=False 且有 error）
        elif result.get("is_win") == False and result.get("error"):
            output["submit_failed"] = True
            output["error"] = result.get('error')
        # 处理胜利尝试失败（调用了胜利节点但输出值不正确）
        elif result.get("win_attempt_feedback"):
            output["win_attempt_feedback"] = result.get('win_attempt_feedback')
        
        return json.dumps(output, ensure_ascii=False)
    
    def _update_state_from_result(self, result: Dict[str, Any]):
        """
        从结果中更新 agent 的内部状态
        
        Args:
            result: 工具调用的结果
        """
        if not result.get("ok"):
            return
        
        # 处理 Tool investigate 的结果 - 添加到 available_tools
        if result.get("entity_type") == "Tool":
            details = result.get("details", {})
            # 使用 node_id 作为唯一标识符
            tool_id = details.get('id')
            if details and tool_id and tool_id not in [t.get('id') for t in self.available_tools]:
                self.available_tools.append(details)
                self.investigated_entities.add(tool_id)
                logger.info(f"Tool investigated and added: {tool_id}")
                
                # 重新构建 tools schema
                self.tools = self._build_tools_schema()
                logger.debug(f"Rebuilt tools schema with {len(self.tools)} tools")
        
        # 处理新揭示的实体
        if result.get("newly_revealed"):
            newly_revealed = result['newly_revealed']
            for entity in newly_revealed:
                if entity['id'] not in [e['id'] for e in self.available_entities]:
                    self.available_entities.append(entity)
                    logger.info(f"New entity revealed: {entity['id']}, type: {entity.get('type')}")