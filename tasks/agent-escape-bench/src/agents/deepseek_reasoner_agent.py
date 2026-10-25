"""
DeepSeek Reasoner API 实现（推理模式）
基于 chat_completions_agent.py，针对 DeepSeek-Reasoner 模型的特殊适配

主要差异：
1. 支持 reasoning_content 字段（思维链）
2. Tool calls 时需要传回 reasoning_content
3. 新一轮对话时需要清除历史的 reasoning_content
4. 不支持 temperature、top_p、presence_penalty、frequency_penalty 参数
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI

from .chat_completions_agent import ChatCompletionsAgent

logger = logging.getLogger(__name__)


class DeepSeekReasonerAgent(ChatCompletionsAgent):
    """
    DeepSeek Reasoner API 实现（推理模式）
    
    适用于 deepseek-reasoner 模型，支持思维链推理
    """
    
    def __init__(self, 
                 model: str = "deepseek-reasoner",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 max_tokens: int = 8000,  # Reasoner 模式通常需要更多 tokens
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 use_function_calling: bool = True,
                 default_headers: Optional[Dict[str, str]] = None,
                 enable_thinking: bool = True,  # 是否启用思维模式
                 **kwargs):
        """
        初始化 DeepSeek Reasoner Agent
        
        Args:
            model: 模型名称，默认 "deepseek-reasoner"
            api_key: DeepSeek API Key
            base_url: API 基础 URL，默认 "https://api.deepseek.com"
            enable_thinking: 是否启用思维模式（默认 True）
                - 如果使用 deepseek-reasoner 模型，会自动启用
                - 如果使用 deepseek-chat + thinking 参数，通过此选项控制
            其他参数见 ChatCompletionsAgent
        
        注意：
            - temperature 和 top_p 参数在 Reasoner 模式下不生效
            - 推荐 max_tokens 设置为较大值（如 8000-32000）
        """
        # 设置默认的 base_url
        if base_url is None:
            base_url = "https://api.deepseek.com"
        
        # 尝试从环境变量获取 API Key
        if api_key is None:
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "DeepSeek API Key not provided. "
                "Please set DEEPSEEK_API_KEY environment variable or pass api_key parameter."
            )
        
        self.enable_thinking = enable_thinking
        
        # Reasoner 模式不支持 temperature 和 top_p
        # 从 kwargs 中移除这些参数，避免重复传递
        kwargs.pop('temperature', None)
        kwargs.pop('top_p', None)
        
        # 调用父类时设置为默认值，但实际 API 调用时会忽略
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.0,  # Reasoner 模式下无效
            max_tokens=max_tokens,
            max_history_messages=max_history_messages,
            max_retries=max_retries,
            use_function_calling=use_function_calling,
            default_headers=default_headers,
            **kwargs
        )
        
        logger.info(
            f"Initialized DeepSeekReasonerAgent - model: {model}, "
            f"base_url: {base_url}, enable_thinking: {enable_thinking}"
        )
    
    def _clear_reasoning_content(self, messages: List[Dict]) -> List[Dict]:
        """
        清除消息历史中的 reasoning_content
        
        在新一轮对话开始时调用，以节省网络带宽
        
        Args:
            messages: 消息列表
            
        Returns:
            清除 reasoning_content 后的消息列表
        """
        for message in messages:
            if isinstance(message, dict) and 'reasoning_content' in message:
                # 移除 reasoning_content 但保留其他字段
                message.pop('reasoning_content', None)
        return messages
    
    def step(self) -> Dict[str, Any]:
        """
        执行一步推理
        
        重写父类方法，以支持 reasoning_content 的处理
        """
        try:
            # 如果是新一轮对话的开始，清除历史的 reasoning_content
            # 判断标准：最后一条消息是 user 消息且倒数第二条是 assistant 消息
            if (len(self.messages) >= 2 and 
                self.messages[-1].get("role") == "user" and 
                self.messages[-2].get("role") == "assistant"):
                # 保留最新的 user 消息，清除之前所有的 reasoning_content
                last_user_msg = self.messages[-1]
                self.messages = self._clear_reasoning_content(self.messages[:-1])
                self.messages.append(last_user_msg)
                logger.debug("Cleared reasoning_content from previous turns")
            
            # 构建 API 请求参数
            api_params = {
                "model": self.model,
                "messages": self.messages,
                "max_tokens": self.max_tokens,
            }
            
            # 注意：不添加 temperature 和 top_p，因为 Reasoner 模式下会忽略它们
            
            # 添加 tools（如果使用 Function Calling）
            if self.use_function_calling and self.tools:
                api_params["tools"] = self.tools
                if self.tool_choice:
                    api_params["tool_choice"] = self.tool_choice
            
            # 如果使用 deepseek-chat 模型且启用 thinking，需要通过 extra_body 传递
            extra_body = {}
            if self.model == "deepseek-chat" and self.enable_thinking:
                extra_body["thinking"] = {"type": "enabled"}
            
            if extra_body:
                api_params["extra_body"] = extra_body
            
            # 调用 API
            response = self.client.chat.completions.create(**api_params)
            
            message = response.choices[0].message
            
            # 处理响应
            if self.use_function_calling and message.tool_calls:
                # Function Calling 模式 - 处理所有工具调用
                actions = self._handle_tool_calls(message)
                
                # 保存助手消息到历史（包含 reasoning_content 和 tool_calls）
                assistant_message = {
                    "role": "assistant",
                    "content": message.content or "",
                }
                
                # 添加 reasoning_content（如果存在）
                if hasattr(message, 'reasoning_content') and message.reasoning_content:
                    assistant_message["reasoning_content"] = message.reasoning_content
                
                # 添加 tool_calls
                if message.tool_calls:
                    assistant_message["tool_calls"] = [tc.model_dump() for tc in message.tool_calls]
                
                self.messages.append(assistant_message)
                
                # 存储待处理的工具调用
                self.pending_tool_calls = message.tool_calls
                self.tool_call_results = []
                
                logger.info(f"Parsed {len(actions)} actions")
                if hasattr(message, 'reasoning_content') and message.reasoning_content:
                    logger.debug(f"Reasoning: {message.reasoning_content[:200]}...")
                
                return {
                    "action": "parallel_tool_calls",
                    "tool_calls": actions,
                    "count": len(actions)
                }
            else:
                # JSON 模式或无工具调用
                assistant_content = message.content or ""
                
                assistant_message = {
                    "role": "assistant",
                    "content": assistant_content
                }
                
                # 添加 reasoning_content（如果存在）
                if hasattr(message, 'reasoning_content') and message.reasoning_content:
                    assistant_message["reasoning_content"] = message.reasoning_content
                    logger.debug(f"Reasoning: {message.reasoning_content[:200]}...")
                
                self.messages.append(assistant_message)
                
                # 如果是 Function Calling 模式但没有工具调用，说明模型选择不执行操作
                if self.use_function_calling:
                    logger.warning("Function calling mode but no tool calls - model chose to wait")
                    return {
                        "action": "wait",
                        "reasoning": assistant_content or "Model did not call any tools"
                    }
                
                # JSON 模式：解析 JSON 响应
                action = self._parse_action(assistant_content)
                logger.info(f"Parsed action: {action.get('action', 'unknown')}")
                return action
            
        except Exception as e:
            logger.error(f"Agent step error: {e}", exc_info=True)
            
            # 如果有待处理的tool messages但没有assistant响应，需要添加一个assistant message
            if self.messages and self.messages[-1].get("role") == "tool":
                self.messages.append({
                    "role": "assistant",
                    "content": f"Encountered error: {str(e)}, need to rethink strategy."
                })
                logger.debug("Added assistant message after tool messages due to API error")
            
            return {
                "action": "wait",
                "reasoning": f"Error: {str(e)}"
            }
    
    def _build_tool_message_content(self, result: Dict[str, Any], tool_call_info=None) -> str:
        """
        构建工具调用结果的消息内容
        
        继承父类方法，Reasoner 模式下格式相同
        """
        return super()._build_tool_message_content(result, tool_call_info)
    
    def get_reasoning_history(self) -> List[Dict[str, str]]:
        """
        获取推理历史
        
        Returns:
            包含推理内容的消息列表
            格式: [{"role": "assistant", "reasoning": "...", "content": "..."}]
        """
        reasoning_history = []
        for message in self.messages:
            if message.get("role") == "assistant" and message.get("reasoning_content"):
                reasoning_history.append({
                    "role": "assistant",
                    "reasoning": message["reasoning_content"],
                    "content": message.get("content", "")
                })
        return reasoning_history