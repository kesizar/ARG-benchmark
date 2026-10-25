"""
字节跳动豆包（Doubao）API 实现
基于 chat_completions_agent.py，针对豆包模型的适配

主要差异：
1. API 端点：https://ark.cn-beijing.volces.com/api/v3/chat/completions
2. 支持 thinking 模式（通过 thinking 和 reasoning_effort 参数）
3. 其他功能与 OpenAI Chat Completions API 高度兼容
"""
import os
import logging
from typing import Dict, Any, Optional

from .chat_completions_agent import ChatCompletionsAgent

logger = logging.getLogger(__name__)


class DoubaoAgent(ChatCompletionsAgent):
    """
    字节跳动豆包（Doubao）API 实现
    
    适用于豆包系列模型，支持：
    - Function Calling
    - Thinking 模式（深度思考）
    - reasoning_effort 控制思考深度
    """
    
    def __init__(self, 
                 model: str = "doubao-pro-32k",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 1.0,  # 豆包默认为 1.0
                 max_tokens: int = 4096,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 use_function_calling: bool = True,
                 enable_thinking: bool = False,  # 是否启用思考模式
                 reasoning_effort: str = "medium",  # minimal, low, medium, high
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        初始化 Doubao Agent
        
        Args:
            model: 模型 ID 或 Endpoint ID
            api_key: 豆包 API Key
            base_url: API 端点，默认 "https://ark.cn-beijing.volces.com/api/v3"
            temperature: 采样温度，默认 1.0
            max_tokens: 最大回答长度
            max_history_messages: 最大历史消息数
            max_retries: 最大重试次数
            use_function_calling: 是否使用 Function Calling
            enable_thinking: 是否启用深度思考模式
            reasoning_effort: 思考深度 - "minimal"（关闭）, "low", "medium", "high"
            default_headers: 自定义HTTP请求头
        
        注意：
            - 豆包 API 与 OpenAI 高度兼容
            - 支持 thinking 模式进行深度推理
            - reasoning_effort="minimal" 可关闭思考，提升速度
        """
        # 设置默认的 base_url
        if base_url is None:
            base_url = "https://ark.cn-beijing.volces.com/api/v3"
        
        # 尝试从环境变量获取 API Key
        if api_key is None:
            api_key = os.environ.get("DOUBAO_API_KEY") or os.environ.get("ARK_API_KEY")
            if not api_key:
                # 降级到 OPENAI_API_KEY（兼容性）
                api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Doubao API Key not provided. "
                "Please set DOUBAO_API_KEY or ARK_API_KEY environment variable or pass api_key parameter."
            )
        
        self.enable_thinking = enable_thinking
        self.reasoning_effort = reasoning_effort
        
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
            f"Initialized DoubaoAgent - model: {model}, "
            f"base_url: {base_url}, enable_thinking: {enable_thinking}, "
            f"reasoning_effort: {reasoning_effort}"
        )
    
    def _call_api(self, messages, tools=None):
        """
        调用豆包 API
        
        重写父类方法以添加 thinking 和 reasoning_effort 参数
        """
        # 构建请求参数
        api_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # 检测是否为官方豆包 API（ark.cn-beijing.volces.com）
        base_url_str = str(self.client.base_url) if self.client.base_url else ""
        is_official_api = "volces.com" in base_url_str
        
        # 只有在官方 API 时才添加 thinking 配置
        # 某些代理服务（如 toiotech.com）可能不支持这些参数
        if is_official_api:
            if self.enable_thinking:
                api_params["thinking"] = {"type": "enabled"}
                
                # 添加 reasoning_effort
                if self.reasoning_effort:
                    api_params["reasoning_effort"] = self.reasoning_effort
            else:
                api_params["thinking"] = {"type": "disabled"}
        else:
            # 非官方 API，记录警告
            if self.enable_thinking:
                logger.warning(
                    f"enable_thinking=True but base_url ({base_url_str}) "
                    "is not official Doubao API (ark.cn-beijing.volces.com). "
                    "Thinking parameters will be ignored."
                )
        
        # 添加 tools（如果使用 Function Calling）
        if tools:
            api_params["tools"] = tools
            if self.tool_choice:
                api_params["tool_choice"] = self.tool_choice
        
        # 调用 API
        response = self.client.chat.completions.create(**api_params)
        
        return response
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        估算成本（基于豆包定价）
        
        注意：豆包定价因模型而异，这里使用估算值
        大致范围：
        - Pro 系列：约 $1-2 / $3-6 per 1M tokens
        - Lite 系列：约 $0.3-0.5 / $1-2 per 1M tokens
        """
        model_lower = self.model.lower()
        
        if "lite" in model_lower or "32k" in model_lower:
            # Lite 系列或较小模型
            input_cost = (input_tokens / 1_000_000) * 0.3
            output_cost = (output_tokens / 1_000_000) * 1.0
        elif "pro" in model_lower or "128k" in model_lower:
            # Pro 系列或大模型
            input_cost = (input_tokens / 1_000_000) * 1.5
            output_cost = (output_tokens / 1_000_000) * 4.0
        else:
            # 默认使用中等定价
            input_cost = (input_tokens / 1_000_000) * 0.8
            output_cost = (output_tokens / 1_000_000) * 2.0
        
        return input_cost + output_cost