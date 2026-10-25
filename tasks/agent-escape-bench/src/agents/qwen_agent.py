"""
阿里云通义千问（Qwen）API 实现
基于 chat_completions_agent.py，针对 Qwen 系列模型的适配

支持两种部署方式：
1. 阿里云 DashScope 官方 API
2. 语聚（YuJu）平台 API

主要特性：
- 与 OpenAI Chat Completions API 高度兼容
- 支持 Function Calling
- 支持 enable_thinking 参数（YuJu 平台）
"""
import os
import logging
from typing import Dict, Any, Optional

from .chat_completions_agent import ChatCompletionsAgent

logger = logging.getLogger(__name__)


class QwenAgent(ChatCompletionsAgent):
    """
    阿里云通义千问（Qwen）API 实现
    
    适用于 Qwen 系列模型：
    - Qwen3-8B / 14B / 32B
    - Qwen-Plus
    - Qwen-Max
    - Qwen-Turbo
    
    支持部署平台：
    - 阿里云 DashScope（官方）
    - 语聚（YuJu）平台
    """
    
    def __init__(self, 
                 model: str = "qwen-plus",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 8192,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 use_function_calling: bool = True,
                 enable_thinking: bool = False,  # 仅 YuJu 平台支持
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        初始化 Qwen Agent
        
        Args:
            model: 模型名称（如 qwen-plus, qwen3-8b, qwen3-14b, qwen3-32b）
            api_key: API Key
            base_url: API 端点
                - DashScope 官方: "https://dashscope.aliyuncs.com/compatible-mode/v1"
                - YuJu 平台: ""
            temperature: 采样温度，默认 0.7
            max_tokens: 最大回答长度
            max_history_messages: 最大历史消息数
            max_retries: 最大重试次数
            use_function_calling: 是否使用 Function Calling
            enable_thinking: 是否启用思考模式（仅 YuJu 平台支持，DashScope 忽略）
            default_headers: 自定义HTTP请求头（YuJu 平台需要 uid）
        
        注意：
            - Qwen API 与 OpenAI 高度兼容
            - DashScope 使用 DASHSCOPE_API_KEY 环境变量
            - YuJu 平台支持 enable_thinking 参数
            - YuJu 平台需要在 default_headers 中传入 uid
        """
        # 自动检测平台和设置默认值
        if base_url is None:
            # 默认使用 DashScope 官方 API
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        # 检测是否为 YuJu 平台
        self.is_yuju_platform = "toiotech.com" in base_url if base_url else False
        
        # 尝试从环境变量获取 API Key
        if api_key is None:
            if self.is_yuju_platform:
                # YuJu 平台优先使用 YUJU_API_KEY
                api_key = os.environ.get("YUJU_API_KEY") or os.environ.get("OPENAI_API_KEY")
            else:
                # DashScope 平台使用 DASHSCOPE_API_KEY
                api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY")
        
        if not api_key:
            platform_name = "YuJu" if self.is_yuju_platform else "DashScope"
            env_var = "YUJU_API_KEY" if self.is_yuju_platform else "DASHSCOPE_API_KEY"
            raise ValueError(
                f"Qwen API Key not provided for {platform_name} platform. "
                f"Please set {env_var} environment variable or pass api_key parameter."
            )
        
        self.enable_thinking = enable_thinking
        
        # YuJu 平台的特殊限制：非流式时不能开启 thinking
        if self.is_yuju_platform and self.enable_thinking:
            logger.warning(
                "YuJu platform: enable_thinking=True requires stream=True. "
                "Current implementation uses non-streaming API, so thinking may not work as expected."
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
        
        platform_name = "YuJu" if self.is_yuju_platform else "DashScope"
        logger.info(
            f"Initialized QwenAgent - model: {model}, platform: {platform_name}, "
            f"base_url: {base_url}, enable_thinking: {enable_thinking}"
        )
    
    def _call_api(self, messages, tools=None):
        """
        调用 Qwen API
        
        重写父类方法以添加 enable_thinking 参数（YuJu 平台）
        """
        # 构建请求参数
        api_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # YuJu 平台：添加 enable_thinking 参数
        if self.is_yuju_platform and self.enable_thinking:
            api_params["enable_thinking"] = True
        
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
        估算成本（基于 Qwen 定价）
        
        DashScope 定价（参考）:
        - Qwen-Plus: ¥0.004 / ¥0.012 per 1K tokens (约 $0.0006 / $0.0017)
        - Qwen-Max: ¥0.04 / ¥0.12 per 1K tokens (约 $0.006 / $0.017)
        - Qwen-Turbo: ¥0.0008 / ¥0.002 per 1K tokens (约 $0.0001 / $0.0003)
        
        YuJu 平台定价可能不同，这里使用相同估算
        """
        model_lower = self.model.lower()
        
        # Qwen-Max 系列
        if "max" in model_lower:
            input_cost = (input_tokens / 1_000) * 0.006
            output_cost = (output_tokens / 1_000) * 0.017
        # Qwen-Plus 系列
        elif "plus" in model_lower:
            input_cost = (input_tokens / 1_000) * 0.0006
            output_cost = (output_tokens / 1_000) * 0.0017
        # Qwen-Turbo 或小模型
        elif "turbo" in model_lower or any(size in model_lower for size in ["8b", "14b"]):
            input_cost = (input_tokens / 1_000) * 0.0001
            output_cost = (output_tokens / 1_000) * 0.0003
        # Qwen3-32B 或其他中等模型
        elif "32b" in model_lower:
            input_cost = (input_tokens / 1_000) * 0.0003
            output_cost = (output_tokens / 1_000) * 0.0008
        else:
            # 默认使用 Plus 的定价
            input_cost = (input_tokens / 1_000) * 0.0006
            output_cost = (output_tokens / 1_000) * 0.0017
        
        return input_cost + output_cost