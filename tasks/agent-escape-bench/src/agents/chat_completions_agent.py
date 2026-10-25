"""
OpenAI Chat Completions API Implementation
Supports both Function Calling and plain JSON text modes
"""
import os
import json
import time
import logging
import sys
from typing import Dict, Any, Optional, List
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime

from .base_agent import BaseModelAgent

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_config import get_prompts

# Get prompts based on current language setting
_prompts = get_prompts()
AGENT_JSON_RESPONSE_FORMAT = _prompts.AGENT_JSON_RESPONSE_FORMAT
AGENT_FUNCTION_CALLING_HINT = _prompts.AGENT_FUNCTION_CALLING_HINT

logger = logging.getLogger(__name__)


class ChatCompletionsAgent(BaseModelAgent):
    """
    OpenAI Chat Completions API Implementation
    
    Supports two modes:
    1. Function Calling mode (recommended) - uses OpenAI's tools parameter
    2. JSON mode - plain text prompts with manual JSON parsing
    """
    
    def __init__(self, 
                 model: str = "gpt-4",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1500,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 use_function_calling: bool = True,
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        Initialize Chat Completions Agent
        
        Args:
            use_function_calling: Whether to use Function Calling (default True)
            default_headers: Custom HTTP headers (e.g., {"uid": "xxx"})
            Other parameters see BaseModelAgent
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
        
        self.use_function_calling = use_function_calling
        
        # Initialize OpenAI client
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not provided and not found in environment")
        
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if default_headers:
            client_kwargs["default_headers"] = default_headers
        
        self.client = OpenAI(**client_kwargs)
        
        # Conversation history
        self.messages = []
        self.system_prompt = None
        
        # Function calling related
        self.tools = None
        self.tool_choice = "auto"  # Options: "auto", "required", "none", or specific tool
        
        # Multi-tool calling state
        self.pending_tool_calls = []  # Store pending tool calls
        self.tool_call_results = []  # Store tool call results
        
        logger.info(f"Initialized ChatCompletionsAgent - model: {model}, function_calling: {use_function_calling}, max_history_messages: {self.max_history_messages}")
    
    def initialize(self, initial_data: Dict[str, Any]):
        """Initialize agent and receive initial environment information"""
        # initial_data format:
        #     {
        #         "ok": True,
        #         "message": f"Case loaded from {case_file_path}",
        #         "case_id": scenario.case_id,
        #         "narrative": scenario.intro_narrative,
        #         "available_entities": available_entities,  # Use unified entity list
        #         "available_information": available_information,  # Available initial information
        #         "win_node_id": scenario.win_node_id  # Victory node ID
        #     }
        self.start_time = datetime.now()
        self.narrative = initial_data.get("narrative", "")
        self.available_entities = initial_data.get("available_entities", [])
        self.available_information = initial_data.get("available_information", [])
        self.win_node_id = initial_data.get("win_node_id", "")  # Store victory node ID
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt_for_mode()
        
        # Build initial environment description
        initial_message = self._build_initial_message()  # Defined in BaseModelAgent
        
        # Initialize conversation history (including system message)
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": initial_message}
        ]
        
        # If using Function Calling, build tool definitions (initially empty, only investigate)
        if self.use_function_calling:
            self.tools = self._build_tools_schema()
        
        logger.info(f"Agent initialized - entities: {len(self.available_entities)}, tools: {len(self.available_tools)}")
    
    def _build_system_prompt_for_mode(self) -> str:
        """Build system prompt based on mode"""
        base_prompt = self._build_system_prompt()
        
        if self.use_function_calling:
            # Function Calling mode
            return base_prompt + AGENT_FUNCTION_CALLING_HINT
        else:
            # JSON mode
            return base_prompt + AGENT_JSON_RESPONSE_FORMAT
    
    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Build tool definitions for OpenAI Function Calling"""
        tools = []
        
        # Create function definitions for each investigated tool node
        for tool in self.available_tools:
            # id field stores the node_id (unique node identifier)
            node_id = tool.get('id')
            
            # Use tool description (if available)
            description = tool.get('description', f"Tool node {node_id}")
            
            function_def = {
                "type": "function",
                "function": {
                    "name": node_id,  # Use node_id as function name to uniquely identify this node
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Check if it's a terminal-type tool (all input parameters of terminal are optional)
            template_id = tool.get('_template_id', '')
            is_terminal = (
                template_id.startswith('terminal') or 
                'terminal' in template_id.lower() or
                node_id.startswith('terminal')  # Also check node_id as fallback
            )
            
            # Add input parameters, distinguishing required and optional parameters
            if tool.get('inputs'):
                for inp in tool['inputs']:
                    param_type = self._convert_type_to_json_schema(inp['type'])
                    param_description = inp.get('description', '')
                    
                    function_def["function"]["parameters"]["properties"][inp['name']] = {
                        "type": param_type,
                        "description": param_description
                    }
                    
                    # Check if it's an optional parameter
                    # 1. All input parameters of terminal-type tools are optional
                    # 2. Parameters with "optional", "default", etc. keywords in description
                    is_optional = is_terminal or (
                        'optional' in param_description.lower() or
                        '(optional)' in param_description.lower() or
                        'optional:' in param_description.lower() or
                        'default' in param_description.lower() or
                        '(default' in param_description.lower()
                    )
                    
                    if not is_optional:
                        function_def["function"]["parameters"]["required"].append(inp['name'])
            
            tools.append(function_def)
        
        # Add investigate function
        tools.append({
            "type": "function",
            "function": {
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
            }
        })
        
        # Add use_item function
        tools.append({
            "type": "function",
            "function": {
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
                    "required": ["node_id", "arguments"]
                }
            }
        })
        
        # Add submit_answer function
        tools.append({
            "type": "function",
            "function": {
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
                    "required": ["answer"]
                }
            }
        })
        
        logger.debug(f"Built tools schema with {len(tools)} tools: {[t['function']['name'] for t in tools]}")
        
        return tools
    
    def _convert_type_to_json_schema(self, type_str: str) -> str:
        """Convert type string to JSON Schema type"""
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
    
    def _trim_history(self):
        """Trim conversation history to keep within maximum length limit while ensuring message sequence integrity"""
        if len(self.messages) <= self.max_history_messages:
            return
        
        logger.debug(f"Trimming history: {len(self.messages)} messages > {self.max_history_messages} limit")
        
        # Preserve initial system message and first user message
        preserved_messages = []
        start_idx = 0
        
        # Preserve system message
        if self.messages and self.messages[0].get("role") == "system":
            preserved_messages.append(self.messages[0])
            start_idx = 1
        
        # Preserve initial user message (immediately after system message)
        if len(self.messages) > start_idx and self.messages[start_idx].get("role") == "user":
            preserved_messages.append(self.messages[start_idx])
            start_idx += 1
        
        # Trim remaining messages
        remaining_messages = self.messages[start_idx:]
        max_remaining = self.max_history_messages - len(preserved_messages)
        
        if len(remaining_messages) > max_remaining:
            # Simple truncation
            trimmed = remaining_messages[-max_remaining:]
            
            # Check first message: if it's a tool message, need to find corresponding assistant (tool_calls)
            if trimmed and trimmed[0].get("role") == "tool":
                # Search backward for assistant message (with tool_calls)
                original_idx = len(remaining_messages) - max_remaining
                while original_idx > 0:
                    original_idx -= 1
                    prev_msg = remaining_messages[original_idx]
                    if prev_msg.get("role") == "assistant" and prev_msg.get("tool_calls"):
                        # Found it, truncate from here
                        trimmed = remaining_messages[original_idx:]
                        break
                    # If encounter other assistant message (without tool_calls), sequence is broken
                    if prev_msg.get("role") == "assistant":
                        # Remove leading isolated tool messages
                        while trimmed and trimmed[0].get("role") == "tool":
                            trimmed.pop(0)
                        break
            
            # Reassemble message list (preserve leading key messages)
            self.messages = preserved_messages + trimmed
            
            logger.debug(f"Trimmed history to {len(self.messages)} messages (kept system + initial user messages)")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    def _call_api(self, messages: List[Dict[str, str]], tools: Optional[List] = None) -> Any:
        """API call with retry mechanism"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = self.tool_choice
        # Definition: tool_choice controls how the model uses these tools (calling strategy).
        # Purpose: Tell the model "how you should decide whether to call tools".
        # Options:
        # "auto" (default): Model automatically decides whether to call tools, can call 0, 1, or multiple tools
        # "required": Force model to call at least one tool
        # "none": Prohibit model from calling any tools (even if tools list is not empty)
        # Specify specific tool: Force model to call a specific tool
        
        return self.client.chat.completions.create(**params)
    
    def step(self) -> Optional[Dict[str, Any]]:
        """Execute one reasoning step, return the action to execute"""
        try:
            # Trim history
            self._trim_history()
            
            # self.messages already contains system message, use directly
            logger.debug(f"Calling API - model: {self.model}, messages: {len(self.messages)}, function_calling: {self.use_function_calling}")
            if self.use_function_calling and self.tools:
                tool_names = [t['function']['name'] for t in self.tools]
                logger.info(f"Available tools for this API call: {tool_names}")
            start_time = time.time()
            
            # Call API
            response = self._call_api(self.messages, self.tools if self.use_function_calling else None)
            
            elapsed = time.time() - start_time
            self.api_calls += 1
            
            # Update token statistics
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                cost = self._estimate_cost(input_tokens, output_tokens)
                self.total_cost += cost
                
                logger.info(f"API call #{self.api_calls} - elapsed: {elapsed:.2f}s, tokens: {input_tokens}/{output_tokens}, cost: ${cost:.4f}")
            
            message = response.choices[0].message # API call response, equivalent to action taken by tested model
            
            # Process response
            if self.use_function_calling and message.tool_calls:
                # Function Calling mode - process all tool calls
                actions = self._handle_tool_calls(message) # action is a list recording all tool calls from this API response, could be one or multiple
                # Save assistant message to history (including all tool_calls)
                self.messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls]
                })
                
                # Store pending tool calls
                self.pending_tool_calls = message.tool_calls
                self.tool_call_results = []
                
                logger.info(f"Parsed {len(actions)} actions")
                return {
                    "action": "parallel_tool_calls",
                    "tool_calls": actions,
                    "count": len(actions)
                }
            else:
                # JSON mode or no tool calls
                assistant_content = message.content or ""
                self.messages.append({"role": "assistant", "content": assistant_content})
                
                # If in Function Calling mode but no tool calls, model chose not to execute operations
                if self.use_function_calling:
                    logger.warning("Function calling mode but no tool calls - model chose to wait")
                    return {
                        "action": "wait",
                        "reasoning": assistant_content or "Model did not call any tools"
                    }
                
                # JSON mode: parse JSON response
                # Note: JSON mode returns single action (tool_call, investigate or wait)
                # This differs from Function Calling mode, which returns parallel_tool_calls
                action = self._parse_action(assistant_content)
                logger.info(f"Parsed action: {action.get('action', 'unknown')}")
                return action
            
        except Exception as e:
            print("8"*100)
            logger.error(f"Agent step error: {e}", exc_info=True)
            
            # If there are pending tool messages but no assistant response, need to add an assistant message
            # Otherwise next API call will violate "tool messages must come after tool_calls" rule
            if self.messages and self.messages[-1].get("role") == "tool":
                # Add an assistant message to "respond" to these tool messages
                self.messages.append({
                    "role": "assistant",
                    "content": f"Encountered error: {str(e)}, need to rethink strategy."
                })
                logger.debug("Added assistant message after tool messages due to API error")
            
            return {
                "action": "wait",
                "reasoning": f"Error: {str(e)}"
            }
    
    def _handle_tool_calls(self, message) -> List[Dict[str, Any]]:
        """
        Process Function Calling response, supports multiple tool calls
        
        Args:
            message: Message object returned by OpenAI API, contains tool_calls
            
        Returns:
            List[Dict[str, Any]]: List containing multiple actions, each with action, node_id, arguments, reasoning, tool_call_id
        """
        actions = []
        
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            tool_call_id = tool_call.id
            
            logger.debug(f"Function call: {function_name}, args: {arguments}, id: {tool_call_id}")
            
            # 处理 investigate 特殊动作
            if function_name == "investigate":
                actions.append({
                    "action": "investigate",
                    "node_id": arguments.get("node_id"),
                    "reasoning": f"Investigate {arguments.get('node_id')}",
                    "tool_call_id": tool_call_id
                })
                continue
            
            # 处理 use_item 特殊动作
            if function_name == "use_item":
                actions.append({
                    "action": "use_item",
                    "node_id": arguments.get("node_id"),
                    "arguments": arguments.get("arguments", {}),
                    "reasoning": f"Use item {arguments.get('node_id')} (params: {arguments.get('arguments', {})})",
                    "tool_call_id": tool_call_id
                })
                continue
            
            # 处理 submit_answer 特殊动作
            if function_name == "submit_answer":
                actions.append({
                    "action": "submit_answer",
                    "answer": arguments.get("answer"),
                    "reasoning": f"Submit answer: {arguments.get('answer')}",
                    "tool_call_id": tool_call_id
                })
                continue
            
            # 处理工具调用：function_name 就是 node_id
            # 验证该节点是否在 available_tools 中（已被 investigate）
            matching_tool = self._find_tool_by_node_id(function_name)
            
            if matching_tool:
                actions.append({
                    "action": "tool_call",
                    "node_id": function_name,  # function_name 就是 node_id
                    "arguments": arguments,
                    "reasoning": f"Call node {function_name}",
                    "tool_call_id": tool_call_id
                })
            else:
                # 未找到匹配的节点（可能是未 investigate 的节点或不存在的节点）
                logger.warning(f"Unknown node or not investigated: {function_name}")
                actions.append({
                    "action": "error",
                    "reasoning": f"Unknown node or not investigated: {function_name}",
                    "tool_call_id": tool_call_id,
                    "error": f"Node '{function_name}' not found or not investigated yet"
                })
        
        return actions
    
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
    
    def _parse_action(self, response: str) -> Dict[str, Any]:
        """解析模型响应（JSON 模式）"""
        try:
            # 尝试提取 JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = response[start:end]
                else:
                    json_str = response.strip()
            
            action = json.loads(json_str)
            
            if "action" not in action:
                raise ValueError("Missing 'action' field")
            
            return action
            
        except Exception as e:
            logger.warning(f"Failed to parse action: {e}")
            logger.debug(f"Response was: {response[:200]}...")
            return {
                "action": "wait",
                "reasoning": f"Failed to parse response: {str(e)}"
            }
    
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
        feedback_msg = "## Execution Result\n\n"
        
        if result.get("ok"):
            # 特殊处理：submit_answer 失败的情况（ok=True, is_win=False）
            if result.get("is_win") == False and result.get("error"):
                feedback_msg += "❌ Answer submission failed\n\n"
                feedback_msg += f"**Error**: {result.get('error')}\n"
            else:
                feedback_msg += "✅ Operation successful\n\n"
            
            # 处理 wait 动作的特殊反馈
            if result.get("message") and not result.get("entity_type") and "output_values" not in result:
                feedback_msg += f"{result['message']}\n"
                if result.get("reasoning"):
                    feedback_msg += f"\nYour reasoning: {result['reasoning']}\n"
            
            # 处理 Tool investigate 的结果
            elif result.get("entity_type") == "Tool":
                feedback_msg += "**Tool Investigation Result**\n\n"
                details = result.get("details", {})
                
                # 添加工具的详细信息到 available_tools
                # id 字段存储的是 node_id（节点唯一标识）
                tool_id = details.get('id')
                if details and tool_id and tool_id not in [t.get('id') for t in self.available_tools]:
                    self.available_tools.append(details)
                    self.investigated_entities.add(tool_id)
                    logger.info(f"Tool investigated and added: {tool_id}")
                    
                    # 重新构建 tools schema（现在包含这个工具）
                    if self.use_function_calling:
                        self.tools = self._build_tools_schema()
                        logger.debug(f"Rebuilt tools schema with {len(self.tools)} tools")
                
                # 显示工具详细信息
                feedback_msg += f"Tool: `{details.get('id')}`\n"
                # if details.get('name'):
                #     feedback_msg += f"Name: {details.get('name')}\n"
                if details.get('description'):
                    feedback_msg += f"Function: {details.get('description')}\n"
                
                # 显示 narrative（如果存在）- 提供故事背景和线索
                if details.get('narrative'):
                    feedback_msg += f"\n**Background Clue**: {details.get('narrative')}\n"
                
                if details.get('inputs'):
                    feedback_msg += "**Input Parameters**:\n"
                    for inp in details['inputs']:
                        feedback_msg += f"  - `{inp['name']}` ({inp['type']}): {inp.get('description', 'N/A')}\n"
                
                if details.get('outputs'):
                    feedback_msg += "**Output Parameters**:\n"
                    for out in details['outputs']:
                        feedback_msg += f"  - `{out['name']}` ({out['type']}): {out.get('description', 'N/A')}\n"
                
                feedback_msg += "\nYou can now call this tool!\n"
            
            # 处理 Item investigate 的结果
            elif result.get("entity_type") == "Item":
                feedback_msg += "**Item Investigation Result**\n\n"
                
                # 【新增】检查是否已经被成功解锁
                if result.get("message"):
                    # 已经被成功解锁,只显示消息,不显示 narrative
                    feedback_msg += f"✓ {result['message']}\n"
                # 检查是否有 required_inputs (需要使用 use_item 的情况)
                elif result.get("required_inputs"):
                    feedback_msg += "**⚠️ This item requires parameters to unlock**\n\n"
                    feedback_msg += "**Required Parameters** (use with `use_item`):\n"
                    for inp in result["required_inputs"]:
                        feedback_msg += f"  - `{inp['name']}` ({inp['type']}): {inp.get('description', 'N/A')}\n"
                    feedback_msg += "\n"
                    
                    # 添加 hint（如果存在）
                    # if result.get('hint'):
                    #     feedback_msg += f"**💡 Hint**: {result['hint']}\n\n"
                    
                    # 显示 narrative（如果存在）- 只在未解锁时显示
                    if result.get('narrative'):
                        feedback_msg += f"\n**Background Clue**: {result.get('narrative')}\n"
                else:
                    # 某些 Item 仅用于触发掉落，没有实际内容
                    if "content" in result:
                        content = result.get("content")
                        feedback_msg += f"**Content**: {content}\n"
                    else:
                        feedback_msg += "This item appears to be a trigger with no readable content.\n"
                    
                    # 显示 narrative（如果存在）- 只在未解锁时显示
                    if result.get('narrative'):
                        feedback_msg += f"\n**Background Clue**: {result.get('narrative')}\n"
            
            # 处理 Tool 调用的结果
            elif "output_values" in result:
                feedback_msg += "**Tool Call Result**\n\n"
                feedback_msg += f"**Output Values**: {json.dumps(result['output_values'], ensure_ascii=False)}\n"
                
                # 【新增】处理源头节点的参数验证反馈
                if result.get("parameter_feedback"):
                    feedback_msg += f"\n{result['parameter_feedback']['message']}\n"
                
                # 如果工具调用完全正确（输出与预期匹配），添加正向反馈
                # if result.get("tool_call_correct"):
                #     feedback_msg += "\n✓ **This tool call result is correct**\n"
            
            # 处理新揭示的实体
            if result.get("newly_revealed"):
                newly_revealed = result['newly_revealed']
                if newly_revealed:
                    feedback_msg += "\n**Newly Discovered Entities**:\n"
                    for entity in newly_revealed:
                        # 添加到 available_entities
                        if entity['id'] not in [e['id'] for e in self.available_entities]:
                            self.available_entities.append(entity)
                            logger.info(f"New entity revealed: {entity['id']}, type: {entity.get('type')}")
                        
                        # 显示基本信息
                        feedback_msg += f"\n- **{entity.get('type')}**: `{entity['id']}`\n"
                        # if entity.get('name'):
                        #     feedback_msg += f"  Name: {entity['name']}\n"
                        if entity.get('description'):
                            feedback_msg += f"  Description: {entity['description']}\n"
                        if entity.get('hint'):
                            feedback_msg += f"  Hint: {entity['hint']}\n"
            
            # 处理 investigate 提示（HIDDEN_ITEM 掉落提示）
            if result.get("investigate_hints"):
                hints = result['investigate_hints']
                if hints:
                    feedback_msg += "\n**💡 Exploration Hints**:\n"
                    for hint in hints:
                        tool_id = hint.get('tool_id')
                        # tool_name = hint.get('tool_name', tool_id)
                        hint_text = hint.get('hint', '')
                        feedback_msg += f"- Tool `{tool_id}`: {hint_text}\n"
            
            # 处理胜利条件
            if result.get("is_win"):
                feedback_msg += f"\n🎉 {result.get('victory_message', 'Congratulations on escaping!')}\n"
        else:
            feedback_msg += f"❌ Operation failed\n\n"
            feedback_msg += f"**Error**: {result.get('error', 'Unknown error')}\n"
        
        self.messages.append({"role": "user", "content": feedback_msg})
        logger.debug(f"Feedback: {feedback_msg[:200]}...")
    
    def _process_parallel_feedback(self):
        """
        处理并行工具调用的反馈
        根据 OpenAI Function Calling 规范,需要为每个 tool_call 添加对应的 tool 消息
        """
        # 按照 OpenAI 的格式，需要为每个 tool_call 返回一个 tool 消息
        for result_data in self.tool_call_results:
            tool_call_id = result_data["tool_call_id"]
            result = result_data["result"] # 这个result是receive_feedback的参数result
            
            # 找到对应的 tool_call 信息（用于获取工具名称和参数）
            tool_call_info = None
            for tc in self.pending_tool_calls:
                if tc.id == tool_call_id:
                    tool_call_info = tc
                    break
            
            # 构建工具调用结果消息
            tool_message_content = self._build_tool_message_content(result, tool_call_info)
            
            # 添加 tool 消息到历史
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": tool_message_content
            })
            
            # 更新内部状态（处理新揭示的实体、工具等）
            self._update_state_from_result(result)
        
        logger.info(f"Added {len(self.tool_call_results)} tool messages to conversation history")
    
    def _build_tool_message_content(self, result: Dict[str, Any], tool_call_info=None) -> str:
        """
        构建工具调用结果的消息内容
        
        Args:
            result: 工具调用的结果
            tool_call_info: 工具调用的信息（包含函数名称和参数），可选
            
        Returns:
            str: 格式化的结果消息
        """
        content = ""
        
        if not result.get("ok"):
            return f"Error: {result.get('error', 'Unknown error')}"
        
        # 处理 Tool investigate 的结果
        if result.get("entity_type") == "Tool":
            details = result.get("details", {})
            content += f"Tool investigation successful: {details.get('id')}\n"
            content += f"Description: {details.get('description', 'N/A')}\n"
            
            # 添加 narrative（如果存在）
            if details.get('narrative'):
                content += f"Background clue: {details.get('narrative')}\n"
            
            if details.get('inputs'):
                content += "Input parameters:\n"
                for inp in details['inputs']:
                    line = f"  - {inp['name']} ({inp['type']}): {inp.get('description', 'N/A')}"
                    if inp.get('upstream_from'):
                        line += f" [upstream: {inp['upstream_from']}]"
                    elif 'init_value' in inp:
                        line += f" [value: {inp['init_value']}]"
                    content += line + "\n"
            
            if details.get('outputs'):
                content += "Output parameters:\n"
                for out in details['outputs']:
                    content += f"  - {out['name']} ({out['type']}): {out.get('description', 'N/A')}\n"
        
        # 处理 Item investigate 的结果
        elif result.get("entity_type") == "Item":
            # 【新增】检查是否已经被成功解锁
            if result.get("message"):
                # 已经被成功解锁,只显示消息,不显示 narrative
                content = f"✓ {result['message']}"
            # 检查是否有 required_inputs (需要使用 use_item 的情况)
            elif result.get("required_inputs"):
                content = "Item investigation successful\n"
                content += "⚠️ This item requires parameters to unlock.\n"
                content += "Required parameters (use with use_item):\n"
                for inp in result["required_inputs"]:
                    content += f"  - {inp['name']} ({inp['type']}): {inp.get('description', 'N/A')}\n"
                
                # 添加 hint（如果存在）
                # if result.get('hint'):
                #     content += f"\n💡 Hint: {result['hint']}\n"
                
                # 添加 narrative（如果存在）- 只在未解锁时显示
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"
            # 某些 Item 仅用于触发掉落，没有实际内容
            elif "content" in result:
                content = f"Item content: {result.get('content')}"
                # 添加 narrative（如果存在）
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"
            else:
                content = "Item investigation successful: This item is a trigger with no readable content"
                # 添加 narrative（如果存在）
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"
        
        # 处理 Tool 调用的结果
        elif "output_values" in result:
            # 如果有 tool_call_info，添加 node_id 和参数信息以提高可读性
            if tool_call_info:
                node_id = tool_call_info.function.name  # function.name 就是 node_id
                
                try:
                    args = json.loads(tool_call_info.function.arguments)
                    content = f"Tool {node_id} invoked\nParameters: {json.dumps(args, ensure_ascii=False)}\nOutput: {json.dumps(result['output_values'], ensure_ascii=False)}"
                except:
                    content = f"Tool {node_id} invoked\nOutput: {json.dumps(result['output_values'], ensure_ascii=False)}"
            else:
                content = f"Tool invoked\nOutput: {json.dumps(result['output_values'], ensure_ascii=False)}"
            
            # 【新增】处理源头节点的参数验证反馈
            if result.get("parameter_feedback"):
                feedback = result["parameter_feedback"]
                content += f"\n\n{feedback['message']}"
            
            # 如果工具调用完全正确（输出与预期匹配），添加正向反馈
            # if result.get("tool_call_correct"):
            #     content += "\n✓ This tool call result is correct"
        
        # 处理 use_item 的结果
        elif result.get("message"):
            content = result.get("message")
            # 只有在成功解锁(不是"已经解锁")时才显示 narrative 和 content
            if result.get("message") != "This item has already been successfully unlocked by you.":
                # Add narrative (if exists)
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"
                # Add content (item content)
                if result.get('content'):
                    content += f"\nContent: {json.dumps(result.get('content'), ensure_ascii=False)}"
        
        # 处理新揭示的实体
        if result.get("newly_revealed"):
            newly_revealed = result['newly_revealed']
            if newly_revealed:
                content += f"\n\nDiscovered {len(newly_revealed)} new entities:\n"
                for entity in newly_revealed:
                    content += f"- {entity.get('type')}: {entity['id']}"
                    # if entity.get('name'):
                    #     content += f" ({entity['name']})"
                    content += "\n"
                    if entity.get('description'):
                        content += f"  Description: {entity['description']}\n"
                    if entity.get('hint'):
                        content += f"  Hint: {entity['hint']}\n"
        
        # 处理 investigate 提示（HIDDEN_ITEM 掉落提示）
        if result.get("investigate_hints"):
            hints = result['investigate_hints']
            if hints:
                content += f"\n\n💡 Exploration hints:\n"
                for hint in hints:
                    tool_id = hint.get('tool_id')
                    # tool_name = hint.get('tool_name', tool_id)
                    hint_text = hint.get('hint', '')
                    content += f"- Tool {tool_id}: {hint_text}\n"
        
        # 处理胜利条件
        if result.get("is_win"):
            content += f"\n🎉 {result.get('victory_message', 'Congratulations on escaping!')}"
        # 处理提交答案失败（is_win=False 且有 error）
        elif result.get("is_win") == False and result.get("error"):
            content += f"\n❌ {result.get('error')}"
        
        return content
    
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
            # id 字段存储的是 node_id（节点唯一标识）
            tool_id = details.get('id')
            if details and tool_id and tool_id not in [t.get('id') for t in self.available_tools]:
                self.available_tools.append(details)
                self.investigated_entities.add(tool_id)
                logger.info(f"Tool investigated and added: {tool_id}")
                
                # 重新构建 tools schema
                if self.use_function_calling:
                    self.tools = self._build_tools_schema()
                    logger.debug(f"Rebuilt tools schema with {len(self.tools)} tools")
        
        # 处理新揭示的实体
        if result.get("newly_revealed"):
            newly_revealed = result['newly_revealed']
            for entity in newly_revealed:
                if entity['id'] not in [e['id'] for e in self.available_entities]:
                    self.available_entities.append(entity)
                    logger.info(f"New entity revealed: {entity['id']}, type: {entity.get('type')}")