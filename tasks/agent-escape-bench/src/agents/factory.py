"""
模型 Agent 工厂
根据配置创建不同类型的 Agent 实例
"""
import logging
from typing import Dict, Any, Optional
from .base_agent import BaseModelAgent
from .chat_completions_agent import ChatCompletionsAgent
from .responses_agent import ResponsesAgent
from .deepseek_chat_agent import DeepSeekChatAgent
from .deepseek_reasoner_agent import DeepSeekReasonerAgent
from .gemini_agent import GeminiAgent
from .doubao_agent import DoubaoAgent
from .qwen_agent import QwenAgent
from .minimax_agent import MinimaxAgent
from .claude_agent import ClaudeAgent
from .claude_third_party_agent import ClaudeThirdPartyAgent

logger = logging.getLogger(__name__)


# 支持的 Agent 类型
AGENT_TYPES = {
    "chat_completions": ChatCompletionsAgent,
    "responses": ResponsesAgent,
    "deepseek_chat": DeepSeekChatAgent,
    "deepseek_reasoner": DeepSeekReasonerAgent,
    "gemini": GeminiAgent,
    "doubao": DoubaoAgent,
    "qwen": QwenAgent,
    "minimax": MinimaxAgent,
    "claude": ClaudeAgent,
    "claude_third_party": ClaudeThirdPartyAgent,
    # 未来可以添加其他模型提供商
    # "anthropic": AnthropicAgent,
    # "custom": CustomAgent,
}


def create_agent(
    agent_type: str = "chat_completions",
    model: str = "gpt-4",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    max_history_messages: int = 20,
    max_retries: int = 3,
    **kwargs
) -> BaseModelAgent:
    """
    创建模型 Agent 实例
    
    Args:
        agent_type: Agent 类型，可选值:
            - "chat_completions": OpenAI Chat Completions API
            - "responses": OpenAI Responses API
            - "deepseek_chat": DeepSeek Chat API (非推理模式)
            - "deepseek_reasoner": DeepSeek Reasoner API (推理模式)
            - "gemini": Google Gemini 3 API
            - "doubao": 字节跳动豆包 API
            - "qwen": 阿里云通义千问 API
            - "minimax": MiniMax M2 系列 API
            - "claude": Anthropic Claude 官方 API (原生 tool use)
            - "claude_third_party": Claude 第三方 API (OpenAI 兼容格式，支持 thinking)
            - 未来可添加: "anthropic", 等
        model: 模型名称
        api_key: API key
        base_url: API base URL（可选）
        temperature: 采样温度（注意：DeepSeek Reasoner 模式下无效）
        max_tokens: 最大 token 数
        max_history_messages: 最大历史消息数
        max_retries: 最大重试次数
        **kwargs: 其他模型特定参数，例如:
            - use_function_calling: bool (for ChatCompletionsAgent, DeepSeekChatAgent, DeepSeekReasonerAgent, QwenAgent)
            - store: bool (for ResponsesAgent)
            - enable_thinking: bool (for DeepSeekReasonerAgent, DoubaoAgent, QwenAgent)
            - thinking_level: str (for GeminiAgent, "minimal"/"low"/"medium"/"high")
            - reasoning_effort: str (for DoubaoAgent, "minimal"/"low"/"medium"/"high")
            - reasoning_split: bool (for MinimaxAgent, True=reasoning_details字段/False=<think>标签)
            - enable_thinking: bool (for ClaudeAgent, 开启 extended thinking)
            - thinking_budget: int (for ClaudeAgent, thinking token 预算)
            - default_headers: Dict[str, str] (自定义HTTP请求头，如 {"uid": "xxx"}，YuJu平台必需)
    
    Returns:
        BaseModelAgent 实例
    
    Raises:
        ValueError: 如果 agent_type 不支持
    
    Examples:
        >>> # 创建 Chat Completions Agent（带 Function Calling）
        >>> agent = create_agent(
        ...     agent_type="chat_completions",
        ...     model="gpt-4",
        ...     use_function_calling=True
        ... )
        
        >>> # 创建 Chat Completions Agent（纯 JSON 模式）
        >>> agent = create_agent(
        ...     agent_type="chat_completions",
        ...     model="gpt-4",
        ...     use_function_calling=False
        ... )
        
        >>> # 创建 Responses Agent
        >>> agent = create_agent(
        ...     agent_type="responses",
        ...     model="gpt-4.1",
        ...     store=True
        ... )
        
        >>> # 创建 DeepSeek Chat Agent（非推理模式）
        >>> agent = create_agent(
        ...     agent_type="deepseek_chat",
        ...     model="deepseek-chat",
        ...     api_key="your-deepseek-api-key",
        ...     use_function_calling=True
        ... )
        
        >>> # 创建 DeepSeek Reasoner Agent（推理模式）
        >>> agent = create_agent(
        ...     agent_type="deepseek_reasoner",
        ...     model="deepseek-reasoner",
        ...     api_key="your-deepseek-api-key",
        ...     max_tokens=8000,
        ...     enable_thinking=True
        ... )
        
        >>> # 创建 Gemini Agent
        >>> agent = create_agent(
        ...     agent_type="gemini",
        ...     model="gemini-3-flash-preview",
        ...     api_key="your-gemini-api-key",
        ...     thinking_level="medium"
        ... )
        
        >>> # 创建 Doubao Agent
        >>> agent = create_agent(
        ...     agent_type="doubao",
        ...     model="doubao-pro-32k",
        ...     api_key="your-doubao-api-key",
        ...     enable_thinking=True,
        ...     reasoning_effort="medium"
        ... )
        
        >>> # 创建 Qwen Agent (DashScope)
        >>> agent = create_agent(
        ...     agent_type="qwen",
        ...     model="qwen-plus",
        ...     api_key="your-dashscope-api-key",
        ...     base_url=""
        ... )
        
        >>> # 创建 Qwen Agent (YuJu平台)
        >>> agent = create_agent(
        ...     agent_type="qwen",
        ...     model="qwen3-32b",
        ...     api_key="your-yuju-api-key",
        ...     base_url="",
        ...     enable_thinking=True,
        ...     default_headers={"uid": "your-uid"}
        ... )
        
        >>> # 创建 MiniMax Agent (官方)
        >>> agent = create_agent(
        ...     agent_type="minimax",
        ...     model="MiniMax-M2.5",
        ...     api_key="your-minimax-api-key",
        ...     base_url="",
        ...     reasoning_split=True
        ... )
        
        >>> # 创建 MiniMax Agent (YuJu平台)
        >>> agent = create_agent(
        ...     agent_type="minimax",
        ...     model="minimax-m2",
        ...     api_key="your-yuju-api-key",
        ...     base_url="",
        ...     reasoning_split=True,
        ...     default_headers={"uid": "your-uid"}
        ... )
        
        >>> # 创建带自定义Headers的Agent（如语聚平台）
        >>> agent = create_agent(
        ...     agent_type="chat_completions",
        ...     model="gpt-4",
        ...     base_url="",
        ...     default_headers={"uid": ""}
        ... )
    """
    agent_type = agent_type.lower()
    
    if agent_type not in AGENT_TYPES:
        available = ", ".join(AGENT_TYPES.keys())
        raise ValueError(
            f"Unsupported agent type: '{agent_type}'. "
            f"Available types: {available}"
        )
    
    # 特殊处理：Gemini 需要根据 base_url 选择不同的实现
    if agent_type == "gemini":
        # 如果 base_url 包含 toiotech.com，使用 YuJu 平台的实现
        if base_url and "toiotech.com" in base_url:
            from .gemini_agent import GeminiYuJuAgent
            agent_class = GeminiYuJuAgent
            logger.info(f"Creating agent - type: gemini (YuJu platform), model: {model}")
        else:
            # 否则使用 Google 官方 API
            agent_class = AGENT_TYPES[agent_type]
            logger.info(f"Creating agent - type: gemini (Google official), model: {model}")
    else:
        agent_class = AGENT_TYPES[agent_type] # agent_class为ChatCompletionsAgent 或者 ResponsesAgent
        logger.info(f"Creating agent - type: {agent_type}, model: {model}")
    
    try:
        agent = agent_class(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history_messages=max_history_messages,
            max_retries=max_retries,
            **kwargs
        )
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise


def list_agent_types() -> Dict[str, str]:
    """
    列出所有支持的 Agent 类型及其描述
    
    Returns:
        {agent_type: description} 字典
    """
    return {
        "chat_completions": "OpenAI Chat Completions API (supports Function Calling)",
        "responses": "OpenAI Responses API (latest, recommended for new projects)",
        "deepseek_chat": "DeepSeek Chat API (non-thinking mode, compatible with OpenAI)",
        "deepseek_reasoner": "DeepSeek Reasoner API (thinking mode with reasoning chain)",
        "gemini": "Google Gemini 3 API (supports function calling and thinking)",
        "doubao": "ByteDance Doubao API (thinking mode with reasoning_effort control)",
        "qwen": "Alibaba Qwen API (DashScope or YuJu platform, OpenAI compatible)",
        "minimax": "MiniMax M2 API (Interleaved Thinking, reasoning_split control)",
        "claude": "Anthropic Claude official API (native tool use, optional extended thinking)",
        "claude_third_party": "Claude via third-party provider (OpenAI-compatible, with thinking support)",
        # 未来添加其他类型的描述
    }


def get_recommended_agent_type(model: str) -> str:
    """
    根据模型名称推荐 Agent 类型
    
    Args:
        model: 模型名称
    
    Returns:
        推荐的 agent_type
    """
    model_lower = model.lower()

    # Claude 模型
    if "claude" in model_lower or "opus" in model_lower or "sonnet" in model_lower or "haiku" in model_lower:
        return "claude"
    
    # MiniMax 模型
    if "minimax" in model_lower or "m2" in model_lower:
        return "minimax"
    
    # Gemini 模型
    if "gemini" in model_lower:
        return "gemini"
    
    # Doubao 模型
    if "doubao" in model_lower:
        return "doubao"
    
    # Qwen 模型
    if "qwen" in model_lower:
        return "qwen"
    
    # DeepSeek Reasoner 模型
    if "deepseek-reasoner" in model_lower or "deepseek_reasoner" in model_lower:
        return "deepseek_reasoner"
    
    # DeepSeek Chat 模型
    if "deepseek-chat" in model_lower or "deepseek_chat" in model_lower or "deepseek" in model_lower:
        return "deepseek_chat"
    
    # GPT-5 和 gpt-4.1 推荐使用 Responses API
    if "gpt-5" in model_lower or "gpt-4.1" in model_lower:
        return "responses"
    
    # 其他 OpenAI 模型使用 Chat Completions
    if "gpt" in model_lower:
        return "chat_completions"
    
    # 默认使用 Chat Completions
    return "chat_completions"