"""
DeepSeek Chat API 实现（非推理模式）
基于 chat_completions_agent.py，针对 DeepSeek-Chat 模型的适配

主要差异：
1. base_url 默认为 "https://api.deepseek.com"
2. API 格式与 OpenAI 兼容，使用相同的 Function Calling 机制
3. 工具调用格式完全相同
"""
import os
import logging
from typing import Dict, Any, Optional

from .chat_completions_agent import ChatCompletionsAgent

logger = logging.getLogger(__name__)


class DeepSeekChatAgent(ChatCompletionsAgent):
    """
    DeepSeek Chat API 实现（非推理模式）
    
    适用于 deepseek-chat 模型
    API 格式与 OpenAI 完全兼容，继承 ChatCompletionsAgent 的所有功能
    """
    
    def __init__(self, 
                 model: str = "deepseek-chat",
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
        初始化 DeepSeek Chat Agent
        
        Args:
            model: 模型名称，默认 "deepseek-chat"
            api_key: DeepSeek API Key，如未提供则从 DEEPSEEK_API_KEY 环境变量获取
            base_url: API 基础 URL，默认 "https://api.deepseek.com"
            其他参数见 ChatCompletionsAgent
        """
        # 设置默认的 base_url
        if base_url is None:
            base_url = "https://api.deepseek.com"
        
        # 尝试从环境变量获取 API Key
        if api_key is None:
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                # 如果没有 DEEPSEEK_API_KEY，尝试使用 OPENAI_API_KEY（兼容性）
                api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "DeepSeek API Key not provided. "
                "Please set DEEPSEEK_API_KEY environment variable or pass api_key parameter."
            )
        
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
        
        logger.info(f"Initialized DeepSeekChatAgent - model: {model}, base_url: {base_url}")