"""
模型 Agent 模块
支持多种 API 调用方式和模型提供商
"""
from .base_agent import BaseModelAgent
from .chat_completions_agent import ChatCompletionsAgent
from .responses_agent import ResponsesAgent
from .deepseek_chat_agent import DeepSeekChatAgent
from .deepseek_reasoner_agent import DeepSeekReasonerAgent
from .gemini_agent import GeminiAgent, GeminiYuJuAgent
from .doubao_agent import DoubaoAgent
from .qwen_agent import QwenAgent
from .minimax_agent import MinimaxAgent
from .claude_agent import ClaudeAgent
from .claude_third_party_agent import ClaudeThirdPartyAgent
from .factory import create_agent, list_agent_types, get_recommended_agent_type

__all__ = [
    'BaseModelAgent',
    'ChatCompletionsAgent',
    'ResponsesAgent',
    'DeepSeekChatAgent',
    'DeepSeekReasonerAgent',
    'GeminiAgent',
    'GeminiYuJuAgent',
    'DoubaoAgent',
    'QwenAgent',
    'MinimaxAgent',
    'ClaudeAgent',
    'ClaudeThirdPartyAgent',
    'create_agent',
    'list_agent_types',
    'get_recommended_agent_type'
]