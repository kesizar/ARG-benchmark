"""
Claude Third-Party API Implementation (OpenAI-compatible format)
第三方供应商提供的 Claude API，使用 OpenAI 兼容格式，额外支持 thinking 参数
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List

from openai import OpenAI
from .chat_completions_agent import ChatCompletionsAgent

logger = logging.getLogger(__name__)


class ClaudeThirdPartyAgent(ChatCompletionsAgent):
    """
    Claude Third-Party API Agent

    通过第三方供应商调用 Claude，API 格式与 OpenAI 兼容：
    - tools 使用 OpenAI function calling 格式
    - 响应格式为 choices[0].message.tool_calls
    - 额外支持 thinking 参数（extended thinking）
    - 响应中包含 reasoning_content 字段
    """

    def __init__(self,
                 model: str = "claude-opus-4-6",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 8192,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 use_function_calling: bool = True,
                 enable_thinking: bool = False,
                 thinking_budget: int = 10000,
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        Initialize Claude Third-Party Agent

        Args:
            model: Model name (e.g., "claude-opus-4-6", "claude-sonnet-4-6")
            api_key: API key for the third-party provider
            base_url: Third-party API base URL (required)
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            enable_thinking: Whether to enable extended thinking
            thinking_budget: Token budget for thinking
            Other parameters see ChatCompletionsAgent
        """
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

        # Use ANTHROPIC_API_KEY as fallback env var
        if api_key is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "API Key not provided. "
                "Please set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )

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
            f"Initialized ClaudeThirdPartyAgent - model: {model}, "
            f"base_url: {base_url}, thinking: {enable_thinking}"
        )

    def _call_api(self, messages: List[Dict[str, str]], tools: Optional[List] = None) -> Any:
        """
        Override API call to inject thinking parameter.
        第三方 API 支持额外的 thinking 和 stream 参数。
        """
        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = self.tool_choice

        # Add thinking parameter if enabled
        if self.enable_thinking:
            params["extra_body"] = {
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                }
            }

        return self.client.chat.completions.create(**params)

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Claude models"""
        model_lower = self.model.lower()

        if "opus" in model_lower:
            input_cost = input_tokens * 15.0 / 1_000_000
            output_cost = output_tokens * 75.0 / 1_000_000
        elif "sonnet" in model_lower:
            input_cost = input_tokens * 3.0 / 1_000_000
            output_cost = output_tokens * 15.0 / 1_000_000
        elif "haiku" in model_lower:
            input_cost = input_tokens * 0.25 / 1_000_000
            output_cost = output_tokens * 1.25 / 1_000_000
        else:
            input_cost = input_tokens * 3.0 / 1_000_000
            output_cost = output_tokens * 15.0 / 1_000_000

        return input_cost + output_cost
