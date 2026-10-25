"""
MiniMax M2 系列模型 API 实现
基于 chat_completions_agent.py，针对 MiniMax 系列模型的适配

支持两种部署方式：
1. MiniMax 官方 API（推荐使用 Anthropic SDK）
2. 语聚（YuJu）平台 API（使用 OpenAI SDK）

主要特性：
- 与 OpenAI Chat Completions API 兼容
- 支持 Function Calling
- 支持 Interleaved Thinking（交错思维链）
- 支持 reasoning_split 参数控制推理内容输出格式
"""
import os
import logging
from typing import Dict, Any, Optional

from .chat_completions_agent import ChatCompletionsAgent

logger = logging.getLogger(__name__)


class MinimaxAgent(ChatCompletionsAgent):
    """
    MiniMax M2 系列模型 API 实现
    
    适用于 MiniMax 系列模型：
    - MiniMax-M2.5（推荐）
    - MiniMax-M2.5-highspeed
    - MiniMax-M2.1
    - MiniMax-M2.1-highspeed
    - MiniMax-M2
    
    支持部署平台：
    - MiniMax 官方 API
    - 语聚（YuJu）平台
    """
    
    def __init__(self, 
                 model: str = "minimax-m2",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 1.0,  # MiniMax 默认 temperature 为 1.0
                 max_tokens: int = 4096,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 use_function_calling: bool = True,
                 reasoning_split: bool = True,  # 是否分离推理内容到 reasoning_details
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        初始化 MiniMax Agent
        
        Args:
            model: 模型名称（如 minimax-m2, MiniMax-M2.5）
            api_key: API Key
            base_url: API 端点
                - MiniMax 官方: "https://api.minimaxi.com/v1"
                - YuJu 平台: ""
            temperature: 采样温度，默认 1.0（MiniMax 推荐值）
            max_tokens: 最大回答长度
            max_history_messages: 最大历史消息数
            max_retries: 最大重试次数
            use_function_calling: 是否使用 Function Calling
            reasoning_split: 是否分离推理内容（True: reasoning_details字段，False: <think>标签）
            default_headers: 自定义HTTP请求头（YuJu 平台需要 uid）
        
        注意：
            - MiniMax 支持 Interleaved Thinking（交错思维链）
            - reasoning_split=True 时，推理内容在 reasoning_details 字段
            - reasoning_split=False 时，推理内容嵌入在 content 的 <think> 标签中
            - 必须完整回传 response_message（包括 reasoning_details）以保持思维链连续性
            - YuJu 平台需要在 default_headers 中传入 uid
        """
        # 自动检测平台和设置默认值
        if base_url is None:
            # 默认使用 MiniMax 官方 API
            base_url = "https://api.minimaxi.com/v1"
        
        # 检测是否为 YuJu 平台
        self.is_yuju_platform = "toiotech.com" in base_url if base_url else False
        
        # 尝试从环境变量获取 API Key
        if api_key is None:
            if self.is_yuju_platform:
                # YuJu 平台优先使用 YUJU_API_KEY
                api_key = os.environ.get("YUJU_API_KEY") or os.environ.get("OPENAI_API_KEY")
            else:
                # MiniMax 官方平台使用 MINIMAX_API_KEY
                api_key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            platform_name = "YuJu" if self.is_yuju_platform else "MiniMax Official"
            env_var = "YUJU_API_KEY" if self.is_yuju_platform else "MINIMAX_API_KEY"
            raise ValueError(
                f"MiniMax API Key not provided for {platform_name} platform. "
                f"Please set {env_var} environment variable or pass api_key parameter."
            )
        
        self.reasoning_split = reasoning_split
        
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
        
        platform_name = "YuJu" if self.is_yuju_platform else "MiniMax Official"
        logger.info(
            f"Initialized MinimaxAgent - model: {model}, platform: {platform_name}, "
            f"base_url: {base_url}, reasoning_split: {reasoning_split}"
        )
    
    def _call_api(self, messages, tools=None):
        """
        调用 MiniMax API
        
        重写父类方法以添加 reasoning_split 参数
        """
        # 构建请求参数
        api_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # 添加 reasoning_split 参数到 extra_body
        # 这个参数控制推理内容的输出格式：
        # - True: 推理内容在 reasoning_details 字段（推荐，便于解析）
        # - False: 推理内容嵌入在 content 的 <think> 标签中（原生格式）
        extra_body = {"reasoning_split": self.reasoning_split}
        api_params["extra_body"] = extra_body
        
        # 添加 tools（如果使用 Function Calling）
        if tools:
            api_params["tools"] = tools
            if self.tool_choice:
                api_params["tool_choice"] = self.tool_choice
        
        # 调用 API
        response = self.client.chat.completions.create(**api_params)
        
        return response
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """
        解析 MiniMax API 响应
        
        重写父类方法以处理 reasoning_details 字段
        """
        # 调用父类方法获取基础解析结果
        result = super()._parse_response(response)
        
        # 处理推理内容（reasoning_details）
        message = response.choices[0].message
        
        if self.reasoning_split:
            # reasoning_split=True: 推理内容在 reasoning_details 字段
            reasoning_details = getattr(message, 'reasoning_details', None)
            if reasoning_details:
                # 提取推理文本
                reasoning_texts = []
                for detail in reasoning_details:
                    if isinstance(detail, dict) and 'text' in detail:
                        reasoning_texts.append(detail['text'])
                
                if reasoning_texts:
                    result['reasoning_content'] = '\n'.join(reasoning_texts)
                    logger.debug(f"Extracted reasoning content from reasoning_details: {len(reasoning_texts)} blocks")
        else:
            # reasoning_split=False: 推理内容在 content 的 <think> 标签中
            content = result.get('content', '')
            if content and '<think>' in content and '</think>' in content:
                # 提取 <think> 标签中的内容
                import re
                think_pattern = r'<think>(.*?)</think>'
                think_matches = re.findall(think_pattern, content, re.DOTALL)
                if think_matches:
                    result['reasoning_content'] = '\n'.join(think_matches)
                    # 移除 <think> 标签，保留纯文本内容
                    result['content'] = re.sub(think_pattern, '', content, flags=re.DOTALL).strip()
                    logger.debug(f"Extracted reasoning content from <think> tags: {len(think_matches)} blocks")
        
        return result
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        估算成本（基于 MiniMax 定价）
        
        MiniMax M2.5 定价（参考官网）:
        - MiniMax-M2.5: 约 $0.001 / $0.003 per 1K tokens（估算）
        - MiniMax-M2.5-highspeed: 约 $0.0015 / $0.0045 per 1K tokens（估算）
        - MiniMax-M2: 约 $0.0008 / $0.002 per 1K tokens（估算）
        
        YuJu 平台定价可能不同，这里使用相同估算
        
        注意：官网未提供详细定价，以下为估算值
        """
        model_lower = self.model.lower()
        
        # M2.5-highspeed 系列（更快但略贵）
        if "highspeed" in model_lower or "high-speed" in model_lower:
            input_cost = (input_tokens / 1_000) * 0.0015
            output_cost = (output_tokens / 1_000) * 0.0045
        # M2.5 系列
        elif "m2.5" in model_lower or "m25" in model_lower:
            input_cost = (input_tokens / 1_000) * 0.001
            output_cost = (output_tokens / 1_000) * 0.003
        # M2.1 系列
        elif "m2.1" in model_lower or "m21" in model_lower:
            input_cost = (input_tokens / 1_000) * 0.0009
            output_cost = (output_tokens / 1_000) * 0.0027
        # M2 基础版本
        elif "m2" in model_lower:
            input_cost = (input_tokens / 1_000) * 0.0008
            output_cost = (output_tokens / 1_000) * 0.002
        else:
            # 默认使用 M2.5 的定价
            input_cost = (input_tokens / 1_000) * 0.001
            output_cost = (output_tokens / 1_000) * 0.003
        
        return input_cost + output_cost