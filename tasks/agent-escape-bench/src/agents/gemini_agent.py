"""
Google Gemini 3 API 实现
支持 Function Calling 和 Thinking 模式

支持两种模式：
1. Google 官方 API：使用 Google GenAI SDK
2. YuJu 平台 API：使用 OpenAI SDK（兼容模式）

主要差异：
1. Google 官方：使用 Google GenAI SDK，消息格式为 contents (role + parts)
2. YuJu 平台：使用 OpenAI SDK，消息格式为标准 messages，支持 thinking 参数
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List

from .base_agent import BaseModelAgent
from .chat_completions_agent import ChatCompletionsAgent

logger = logging.getLogger(__name__)


class GeminiYuJuAgent(ChatCompletionsAgent):
    """
    YuJu 平台的 Gemini API 实现（OpenAI 兼容模式）
    
    使用标准 OpenAI Chat Completions API 格式
    """
    
    def __init__(self,
                 model: str = "gemini-3-flash-preview",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 8192,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 use_function_calling: bool = True,
                 thinking_level: str = "medium",  # minimal, low, medium, high
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        初始化 YuJu Gemini Agent
        
        Args:
            model: 模型名称
            api_key: API Key
            base_url: API 端点
            thinking_level: 推理级别，对应 thinking 参数
        """
        if base_url is None:
            base_url = ""
        
        self.thinking_level = thinking_level
        self.enable_thinking = thinking_level != "minimal"
        
        # 调用父类初始化
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history_messages=max_history_messages,
            max_retries=max_retries,
            use_function_calling=use_function_calling,
            default_headers=default_headers,
            **kwargs
        )
        
        logger.info(
            f"Initialized GeminiYuJuAgent - model: {model}, "
            f"base_url: {base_url}, thinking_level: {thinking_level}"
        )
    
    def _call_api(self, messages, tools=None):
        """
        调用 YuJu Gemini API
        
        重写父类方法以添加 thinking 参数（如果支持）
        """
        # 构建请求参数
        api_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # YuJu 平台的 Gemini 可能不支持 thinking 参数
        # 暂时禁用，避免 API 调用挂起

        # if self.enable_thinking:
        #     api_params["extra_body"] = {"thinking": {"type": "enabled"}}
        
        if self.enable_thinking:
            logger.warning(
                "thinking_level is set but YuJu Gemini API may not support thinking parameter. "
                "Ignoring thinking configuration."
            )
        
        # 添加 tools（如果使用 Function Calling）
        if tools:
            api_params["tools"] = tools
            if self.tool_choice:
                api_params["tool_choice"] = self.tool_choice
        
        # 调用 API
        response = self.client.chat.completions.create(**api_params)
        
        return response


class GeminiAgent(BaseModelAgent):
    """
    Google Gemini 3 API 实现
    
    支持：
    - Gemini 3.1 Pro Preview
    - Gemini 3 Flash Preview
    - Function Calling
    - Thinking 模式（thinking_level: minimal, low, medium, high）
    """
    
    def __init__(self, 
                 model: str = "gemini-3-flash-preview",
                 api_key: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 8192,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 thinking_level: str = "medium",  # minimal, low, medium, high
                 **kwargs):
        """
        初始化 Gemini Agent
        
        Args:
            model: 模型名称，如 "gemini-3-flash-preview" 或 "gemini-3.1-pro-preview"
            api_key: Google API Key
            temperature: 采样温度
            max_tokens: 最大 token 数
            max_history_messages: 最大历史消息数
            max_retries: 最大重试次数
            thinking_level: 推理级别 - "minimal", "low", "medium", "high"
        
        注意：
            - Gemini API 与 OpenAI API 完全不同
            - 需要安装：pip install google-genai
        """
        # Gemini 不需要 base_url、uid 等参数，从 kwargs 中移除
        kwargs.pop('base_url', None)
        kwargs.pop('uid', None)
        kwargs.pop('default_headers', None)
        kwargs.pop('use_function_calling', None)  # Gemini 总是使用 function calling
        
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=None,  # Gemini 不需要 base_url
            temperature=temperature,
            max_tokens=max_tokens,
            max_history_messages=max_history_messages,
            max_retries=max_retries,
            **kwargs
        )
        
        self.thinking_level = thinking_level
        
        # 获取 API Key
        api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API Key not provided. "
                "Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable or pass api_key parameter."
            )
        
        # 初始化 Google GenAI 客户端
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            
            # 配置 API Key
            os.environ["GOOGLE_API_KEY"] = api_key
            self.client = genai.Client(api_key=api_key)
            
        except ImportError:
            raise ImportError(
                "Google GenAI SDK not installed. "
                "Please install it with: pip install google-genai"
            )
        
        # 对话历史（Gemini 格式）
        self.contents = []  # List of Content objects
        self.system_instruction = None
        
        # Function calling 相关
        self.tools = None  # Gemini Tool object
        self.function_declarations = []
        
        # 多工具调用状态
        self.pending_function_calls = []
        self.function_call_results = []
        
        logger.info(
            f"Initialized GeminiAgent - model: {model}, "
            f"thinking_level: {thinking_level}"
        )
    
    def initialize(self, initial_data: Dict[str, Any]):
        """初始化 agent，接收初始环境信息"""
        # 构建 system instruction
        system_parts = []
        
        # 添加案例背景
        if initial_data.get("narrative"):
            system_parts.append(f"## Task Background\n\n{initial_data['narrative']}")
        
        # 添加可用实体
        if initial_data.get("available_entities"):
            entities_text = "\n".join([
                f"- {e.get('id')} (Type: {e.get('type', 'unknown')})"
                for e in initial_data["available_entities"]
            ])
            system_parts.append(f"## Available Entities\n\n{entities_text}")
        
        # 构建完整的 system instruction
        system_instruction = "\n\n".join(system_parts)
        self.system_instruction = system_instruction
        
        # 保存实体信息
        self.available_entities = initial_data.get("available_entities", [])
        self.available_information = initial_data.get("available_information", [])
        self.win_node_id = initial_data.get("win_node_id", "")
        self.available_tools = []
        self.investigated_entities = set()
        
        # 初始化工具集（包含 investigate、use_item、submit_answer）
        self._rebuild_gemini_tools()
        
        logger.info(f"Agent initialized with {len(self.available_entities)} entities")
    
    def register_tools(self, tools_schema: List[Dict[str, Any]]):
        """
        注册工具（从 OpenAI 格式转换为 Gemini 格式）
        
        Args:
            tools_schema: OpenAI 格式的工具定义
        """
        # 转换 OpenAI 格式到 Gemini 格式
        function_declarations = []
        
        for tool in tools_schema:
            if tool.get("type") == "function":
                func = tool["function"]
                
                # 转换参数格式
                gemini_func = {
                    "name": func["name"],
                    "description": func["description"],
                    "parameters": func["parameters"]
                }
                
                function_declarations.append(gemini_func)
        
        self.function_declarations = function_declarations
        
        # 创建 Gemini Tool object
        if function_declarations:
            self.tools = self.types.Tool(function_declarations=function_declarations)
        
        logger.info(f"Registered {len(function_declarations)} tools")
    
    def step(self) -> Optional[Dict[str, Any]]:
        """执行一步推理，返回要执行的动作"""
        try:
            # 构建配置
            config_params = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
            
            # 添加 thinking config
            if self.thinking_level:
                config_params["thinking_config"] = self.types.ThinkingConfig(
                    thinking_level=self.thinking_level
                )
            
            # 添加 tools
            if self.tools:
                config_params["tools"] = [self.tools]
            
            config = self.types.GenerateContentConfig(**config_params)
            
            # 调用 API
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.contents,
                config=config,
                system_instruction=self.system_instruction
            )
            
            self.api_calls += 1
            
            # 更新 token 统计
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                cost = self._estimate_cost(input_tokens, output_tokens)
                self.total_cost += cost
                
                logger.info(f"API call #{self.api_calls} - tokens: {input_tokens}/{output_tokens}, cost: ${cost:.4f}")
            
            # 获取第一个候选响应
            if not response.candidates:
                logger.warning("No candidates in response")
                return {"action": "wait", "reasoning": "No response from model"}
            
            candidate = response.candidates[0]
            content = candidate.content
            
            # 检查是否有 function call
            function_calls = []
            text_response = ""
            
            for part in content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append(part.function_call)
                elif hasattr(part, 'text') and part.text:
                    text_response += part.text
            
            if function_calls:
                # 处理 function calls
                actions = self._handle_function_calls(function_calls)
                
                # 保存到历史
                self.contents.append(content)
                
                # 存储待处理的 function calls
                self.pending_function_calls = function_calls
                self.function_call_results = []
                
                logger.info(f"Parsed {len(actions)} function calls")
                
                return {
                    "action": "parallel_tool_calls",
                    "tool_calls": actions,
                    "count": len(actions)
                }
            else:
                # 没有 function call，处理文本响应
                self.contents.append(content)
                
                logger.warning("No function calls - model chose to wait or respond with text")
                return {
                    "action": "wait",
                    "reasoning": text_response or "Model did not call any tools"
                }
        
        except Exception as e:
            logger.error(f"Agent step error: {e}", exc_info=True)
            
            return {
                "action": "wait",
                "reasoning": f"Error: {str(e)}"
            }
    
    def _handle_function_calls(self, function_calls: List) -> List[Dict[str, Any]]:
        """
        处理 Gemini Function Calls
        
        Args:
            function_calls: Gemini FunctionCall objects
            
        Returns:
            标准化的 actions 列表
        """
        actions = []
        
        for fc in function_calls:
            function_name = fc.name
            arguments = dict(fc.args)  # 转换为普通 dict
            
            logger.debug(f"Function call: {function_name}, args: {arguments}")
            
            # 处理特殊动作
            if function_name == "investigate":
                actions.append({
                    "action": "investigate",
                    "node_id": arguments.get("node_id"),
                    "reasoning": f"Investigate {arguments.get('node_id')}",
                    "function_call": fc  # 保存原始对象
                })
            elif function_name == "use_item":
                actions.append({
                    "action": "use_item",
                    "node_id": arguments.get("node_id"),
                    "arguments": arguments.get("arguments", {}),
                    "reasoning": f"Use item {arguments.get('node_id')}",
                    "function_call": fc
                })
            elif function_name == "submit_answer":
                actions.append({
                    "action": "submit_answer",
                    "answer": arguments.get("answer"),
                    "reasoning": "Submit final answer",
                    "function_call": fc
                })
            else:
                # 工具调用
                actions.append({
                    "action": "tool_call",
                    "tool_name": function_name,
                    "node_id": arguments.get("node_id") or function_name,
                    "arguments": {k: v for k, v in arguments.items() if k != "node_id"},
                    "reasoning": f"Execute tool {function_name}",
                    "function_call": fc
                })
        
        return actions
    
    def receive_feedback(self, result: Dict[str, Any], tool_call_id: Optional[str] = None):
        """
        接收环境的反馈
        
        Args:
            result: 执行结果
            tool_call_id: 在 Gemini 中，我们使用 function_call 对象本身
        """
        # 收集结果
        self.function_call_results.append(result)
        
        # 检查是否所有结果都收集完毕
        if len(self.function_call_results) < len(self.pending_function_calls):
            logger.debug(f"Collected {len(self.function_call_results)}/{len(self.pending_function_calls)} results")
            return
        
        # 所有结果都收集完毕，构建 function response
        logger.info(f"All {len(self.function_call_results)} results collected, processing feedback")
        
        # 为每个 function call 构建 response
        function_response_parts = []
        
        for fc, result in zip(self.pending_function_calls, self.function_call_results):
            # 构建响应内容
            response_content = self._build_function_response_content(result, fc)
            
            # 创建 function response part
            function_response_part = self.types.Part.from_function_response(
                name=fc.name,
                response={"result": response_content}
            )
            
            function_response_parts.append(function_response_part)
            
            # 更新内部状态（处理新揭示的实体、工具等）
            self._update_state_from_result(result)
        
        # 添加到历史
        feedback_content = self.types.Content(
            role="user",
            parts=function_response_parts
        )
        self.contents.append(feedback_content)
        
        # 清空状态
        self.pending_function_calls = []
        self.function_call_results = []
        
        logger.debug("Feedback processed and added to conversation history")
    
    def _update_state_from_result(self, result: Dict[str, Any]):
        """
        从结果中更新 agent 的内部状态（与 chat_completions_agent 保持一致）
        
        Args:
            result: 工具调用的结果
        """
        if not result.get("ok"):
            return
        
        # 处理 Tool investigate 的结果 - 添加到 available_tools
        if result.get("entity_type") == "Tool":
            details = result.get("details", {})
            tool_id = details.get('id')
            if details and tool_id and tool_id not in [t.get('id') for t in self.available_tools]:
                self.available_tools.append(details)
                self.investigated_entities.add(tool_id)
                logger.info(f"Tool investigated and added: {tool_id}")
                
                # 重新构建 tools schema（Gemini 格式）
                self._rebuild_gemini_tools()
                logger.debug(f"Rebuilt Gemini tools with {len(self.function_declarations)} declarations")
        
        # 处理新揭示的实体
        if result.get("newly_revealed"):
            newly_revealed = result['newly_revealed']
            for entity in newly_revealed:
                if entity['id'] not in [e['id'] for e in self.available_entities]:
                    self.available_entities.append(entity)
                    logger.info(f"New entity revealed: {entity['id']}, type: {entity.get('type')}")
    
    def _rebuild_gemini_tools(self):
        """重新构建 Gemini Tool schema（investigate 工具调查后调用）"""
        function_declarations = []
        
        # 为每个已 investigate 的工具节点创建 function declaration
        for tool in self.available_tools:
            node_id = tool.get('id')
            description = tool.get('description', f"Tool node {node_id}")
            
            # 检查是否为 terminal 类工具（terminal 的所有输入参数都是可选的）
            template_id = tool.get('_template_id', '')
            is_terminal = (
                template_id.startswith('terminal') or
                'terminal' in template_id.lower() or
                node_id.startswith('terminal')
            )
            
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            if tool.get('inputs'):
                for inp in tool['inputs']:
                    param_description = inp.get('description', '')
                    parameters["properties"][inp['name']] = {
                        "type": "string",  # Gemini 统一用 string 简化处理
                        "description": param_description
                    }
                    
                    is_optional = is_terminal or (
                        'optional' in param_description.lower() or
                        '(optional)' in param_description.lower() or
                        'optional:' in param_description.lower() or
                        'default' in param_description.lower() or
                        '(default' in param_description.lower()
                    )
                    
                    if not is_optional:
                        parameters["required"].append(inp['name'])
            
            function_declarations.append({
                "name": node_id,
                "description": description,
                "parameters": parameters
            })
        
        # 加上固定工具
        function_declarations.extend([
            {
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
                    "required": ["node_id"]
                }
            },
            {
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
                            "description": "Parameters to provide to the item"
                        }
                    },
                    "required": ["node_id", "arguments"]
                }
            },
            {
                "name": "submit_answer",
                "description": "[ULTIMATE GOAL] Submit the victory string to complete the task and escape the room.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "The complete victory string informed by the system"
                        }
                    },
                    "required": ["answer"]
                }
            }
        ])
        
        self.function_declarations = function_declarations
        if function_declarations:
            self.tools = self.types.Tool(function_declarations=function_declarations)
    
    def _build_function_response_content(self, result: Dict[str, Any], function_call) -> str:
        """
        构建 function response 内容
        
        Args:
            result: 工具执行结果
            function_call: Gemini FunctionCall object
            
        Returns:
            格式化的响应文本
        """
        content_parts = []
        
        if result.get("ok"):
            content_parts.append("✅ Operation successful")
            
            # 根据不同的操作类型构建响应
            if result.get("entity_type") == "Tool":
                # 工具调查结果
                details = result.get("details", {})
                content_parts.append(f"\n**Tool**: {details.get('id')}")
                content_parts.append(f"**Description**: {details.get('description', 'N/A')}")
                
                # 显示 narrative（如果存在）- 提供故事背景和线索
                if details.get('narrative'):
                    content_parts.append(f"\n**Background Clue**: {details.get('narrative')}")
                
                if details.get("inputs"):
                    content_parts.append("**Input Parameters**:")
                    for inp in details.get("inputs", []):
                        line = f"  - {inp['name']} ({inp['type']}): {inp.get('description', 'N/A')}"
                        if inp.get("upstream_from"):
                            line += f" [upstream: {inp['upstream_from']}]"
                        elif "init_value" in inp:
                            line += f" [value: {inp['init_value']}]"
                        content_parts.append(line)
                
                if details.get("outputs"):
                    content_parts.append("**Output Parameters**:")
                    for out in details.get("outputs", []):
                        content_parts.append(f"  - {out['name']} ({out['type']}): {out.get('description', 'N/A')}")
                
                content_parts.append("\nYou can now call this tool!")
            
            elif result.get("entity_type") == "Container":
                # 容器调查结果
                content_parts.append(f"\n**Container**: {result.get('details', {}).get('id')}")
                if result.get("locked"):
                    content_parts.append("**Status**: 🔒 Locked")
                    if result.get("required_inputs"):
                        inputs_text = ", ".join([
                            f"{inp['name']} ({inp['type']})"
                            for inp in result.get("required_inputs", [])
                        ])
                        content_parts.append(f"**Required Parameters**: {inputs_text}")
                else:
                    content_parts.append("**Status**: 🔓 Unlocked")
            
            elif result.get("entity_type") == "Item":
                # 物品调查结果
                
                # 【新增】检查是否已经被成功解锁
                if result.get("message"):
                    # 已经被成功解锁,只显示消息,不显示 narrative
                    content_parts.append(f"✓ {result['message']}")
                # 检查是否有 required_inputs (需要使用 use_item 的情况)
                elif result.get("required_inputs"):
                    content_parts.append("\n⚠️ **This item requires parameters to unlock**")
                    inputs_text = ", ".join([
                        f"{inp['name']} ({inp['type']})"
                        for inp in result.get("required_inputs", [])
                    ])
                    content_parts.append(f"**Required Parameters** (use with use_item): {inputs_text}")
                    
                    # 添加 hint（如果存在）
                    if result.get('hint'):
                        content_parts.append(f"\n💡 Hint: {result['hint']}")
                    
                    # 添加 narrative（如果存在）- 只在未解锁时显示
                    if result.get('narrative'):
                        content_parts.append(f"\n**Background Clue**: {result['narrative']}")
                else:
                    # 普通 Item（有 content 字段或无内容）
                    if "content" in result:
                        content_parts.append(f"\n**Item Content**: {result.get('content')}")
                    else:
                        content_parts.append("This item appears to be a trigger with no readable content.")
                    # 添加 narrative（如果存在）
                    if result.get('narrative'):
                        content_parts.append(f"\n**Background Clue**: {result['narrative']}")
            
            # 工具执行结果
            if result.get("output_values"):
                content_parts.append(f"\n**Output**: {json.dumps(result['output_values'], ensure_ascii=False)}")
            
            # 【新增】处理源头节点的参数验证反馈
            if result.get("parameter_feedback"):
                feedback = result["parameter_feedback"]
                content_parts.append(f"\n\n{feedback['message']}")
            
            # use_item 成功结果
            if result.get("message") and not result.get("entity_type"):
                content_parts.append(result.get("message"))
                # 只有在成功解锁(不是"已经解锁")时才显示 narrative 和 content
                if result.get("message") != "This item has already been successfully unlocked by you.":
                    if result.get('narrative'):
                        content_parts.append(f"\n**Background Clue**: {result['narrative']}")
                    if result.get('content'):
                        content_parts.append(f"\n**Content**: {json.dumps(result['content'], ensure_ascii=False)}")
            
            # 新发现的实体
            if result.get("newly_revealed"):
                newly_revealed = result["newly_revealed"]
                if newly_revealed:
                    content_parts.append("\n**Newly Discovered Entities**:")
                    for entity in newly_revealed:
                        entity_line = f"- **{entity.get('type')}**: `{entity['id']}`"
                        content_parts.append(entity_line)
                        if entity.get('description'):
                            content_parts.append(f"  Description: {entity['description']}")
                        if entity.get('hint'):
                            content_parts.append(f"  Hint: {entity['hint']}")
            
            # investigate 提示（HIDDEN_ITEM 掉落提示）
            if result.get("investigate_hints"):
                hints = result['investigate_hints']
                if hints:
                    content_parts.append("\n💡 **Exploration Hints**:")
                    for hint in hints:
                        tool_id = hint.get('tool_id')
                        hint_text = hint.get('hint', '')
                        content_parts.append(f"- Tool `{tool_id}`: {hint_text}")
            
            # 胜利消息
            if result.get("is_win"):
                content_parts.append(f"\n\n🎉 {result.get('victory_message', 'Congratulations on your victory!')}")
            # submit_answer 失败（is_win=False 且有 error）
            elif result.get("is_win") == False and result.get("error"):
                content_parts.append(f"\n❌ {result.get('error')}")
        
        else:
            # 操作失败
            content_parts.append("❌ Operation failed")
            if result.get("error"):
                content_parts.append(f"\n**Error**: {result['error']}")
        
        return "\n".join(content_parts)
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        估算成本（基于 Gemini 定价）
        
        Gemini 3 Flash: $0.50 / $3 per 1M tokens
        Gemini 3.1 Pro: $2 / $12 per 1M tokens (< 200k), $4 / $18 (> 200k)
        """
        model_lower = self.model.lower()
        
        if "flash" in model_lower:
            # Gemini 3 Flash
            input_cost = (input_tokens / 1_000_000) * 0.50
            output_cost = (output_tokens / 1_000_000) * 3.0
        elif "pro" in model_lower:
            # Gemini 3.1 Pro (简化为小于 200k 的情况)
            input_cost = (input_tokens / 1_000_000) * 2.0
            output_cost = (output_tokens / 1_000_000) * 12.0
        else:
            # 默认使用 Flash 定价
            input_cost = (input_tokens / 1_000_000) * 0.50
            output_cost = (output_tokens / 1_000_000) * 3.0
        
        return input_cost + output_cost
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "api_calls": self.api_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": self.total_cost,
            "model": self.model,
            "thinking_level": self.thinking_level
        }