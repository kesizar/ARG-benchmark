"""
Abstract base class - defines the unified interface for all model Agents
Supports extension of various API calling methods
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import sys
import os

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_config import get_prompts

# Get prompts based on current language setting
_prompts = get_prompts()
AGENT_SYSTEM_PROMPT = _prompts.AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class BaseModelAgent(ABC):
    """
    Model Agent abstract base class
    
    All concrete model implementations should inherit from this class and implement abstract methods.
    This supports OpenAI Chat Completions, Responses API, and APIs from other model providers.
    """
    
    def __init__(self, 
                 model: str,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 8092,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 **kwargs):
        """
        Initialize base parameters
        
        Args:
            model: Model name
            api_key: API key
            base_url: API base URL (optional)
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens
            max_history_messages: Maximum number of history messages to keep
            max_retries: Maximum retry attempts on API call failure
            **kwargs: Other model-specific parameters
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_history_messages = max_history_messages
        self.max_retries = max_retries
        self.extra_params = kwargs
        
        # Statistics
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0
        self.start_time = None
        
        # Environment state
        self.narrative = ""
        self.available_entities = []  # Unified entity list (Tools and Items)
        self.available_tools = []  # Investigated tools (with detailed interface info)
        self.investigated_entities = set()  # IDs of investigated entities
        self.win_node_id = ""  # Victory node ID
        
        logger.info(f"Initialized {self.__class__.__name__} - model: {model}")
    
    @abstractmethod
    def initialize(self, initial_data: Dict[str, Any]):
        """
        Initialize agent, receiving initial environment information
        
        Args:
            initial_data: Data returned from evaluator's load_case
                - narrative: Escape room story background
                - available_entities: Available entity list (Tools and Items)
                - available_information: Available information list
        """
        # initial_data format:
        #     {
        #         "ok": True,
        #         "message": f"Case loaded from {case_file_path}",
        #         "case_id": scenario.case_id,
        #         "narrative": scenario.intro_narrative,
        #         "available_entities": available_entities  # Use unified entity list
        #     }
        
        pass
    
    @abstractmethod
    def step(self) -> Optional[Dict[str, Any]]:
        """
        Execute one reasoning step, return the action to execute
        
        Returns:
            Action dict: {
                "action": "tool_call" | "investigate" | "wait",
                "node_id": "ID of tool or item",
                "arguments": {"param_name": "param_value", ...},  # Only needed for tool_call
                "reasoning": "Reasoning process"
            }
        """
        pass
    
    @abstractmethod
    def receive_feedback(self, result: Dict[str, Any]):
        """
        Receive feedback from the environment
        
        Args:
            result: Result of tool call or investigation
                - ok: Whether operation succeeded
                - output_values: Tool output values (if any)
                - content: Item content (if any)
                - newly_revealed: List of newly discovered items
                - investigate_hints: Investigation hints
                - is_win: Whether victory achieved
                - victory_message: Victory message
                - error: Error message (if failed)
        """
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics
        
        Returns:
            Dictionary containing API calls, token usage, cost and other statistics
        """
        elapsed_time = 0
        if self.start_time:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "api_calls": self.api_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": self.total_cost,
            "avg_tokens_per_call": (self.total_input_tokens + self.total_output_tokens) / max(self.api_calls, 1),
            "elapsed_time_seconds": elapsed_time
        }
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate API call cost (USD)
        Subclasses can override this method to provide more accurate cost estimation
        """
        # 简化的成本估算，实际成本取决于具体模型
        if "gpt-4" in self.model.lower():
            input_cost = input_tokens * 0.03 / 1000
            output_cost = output_tokens * 0.06 / 1000
        elif "gpt-3.5" in self.model.lower():
            input_cost = input_tokens * 0.0015 / 1000
            output_cost = output_tokens * 0.002 / 1000
        elif "gpt-5" in self.model.lower():
            # GPT-5 的假设价格
            input_cost = input_tokens * 0.05 / 1000
            output_cost = output_tokens * 0.10 / 1000
        else:
            # Default to gpt-3.5 pricing
            input_cost = input_tokens * 0.0015 / 1000
            output_cost = output_tokens * 0.002 / 1000
        return input_cost + output_cost
    
    def _build_system_prompt(self) -> str:
        """Build system prompt (can be overridden by subclasses)"""
        return AGENT_SYSTEM_PROMPT
    
    def _build_initial_message(self) -> str:
        """Build initial environment description (can be overridden by subclasses)"""
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
        
        msg = f"## Escape Room Environment\n\n{self.narrative}\n\n"
        
        # Add victory node information
        if hasattr(self, 'win_node_id') and self.win_node_id:
            msg += f"### 🎯 Victory Node\n\n"
            msg += f"**Victory Node ID**: `{self.win_node_id}`\n\n"
            msg += f"This is your ultimate target node. When you successfully call or investigate this node and obtain its output, you should determine if the output is the victory string and submit it using `submit_answer`.\n\n"
            msg += f"**Note**: The victory node usually has upstream dependencies. Don't try to call it from the beginning. Explore other nodes first to understand the dependency relationships.\n\n"
        
        # Available initial information (init_inputs values)
        if self.available_information:
            msg += f"### Available Parameters ({len(self.available_information)} items)\n\n"
            msg += "The following are available parameter values in the environment. You need to reason which tools' parameters they should be used for. Only by using the correct parameters can you escape the room:\n\n"
            
            for info in self.available_information:
                # info format:
                # {
                #     "value": param_value
                # }
                # Only show values, don't reveal correspondence
                msg += f"- `{info['value']}`\n"
        
        # Visible entities (Tools and Items)
        msg += f"### Entities in Environment ({len(self.available_entities)} items)\n\n"
        msg += "You can use the `investigate` operation on these entities to view detailed information.\n\n"
        
        for entity in self.available_entities:
            # entity format:
            #   tool_info = {
            #         "id": node.id,
            #         "name": node.name,  # Optional, only exists when not empty
            #         "description": node.description,  # Optional, only exists when not empty
            #         "type": "Tool",
            #         "can_investigate": True,
            #         "hint": "You can use investigate to view detailed interface information for calling"
            #     }  
            entity_type = entity.get('type', 'Unknown')
            msg += f"**ID**: `{entity['id']}`\n"  # This id corresponds to the id in the json file, not template_id
            msg += f"**Type**: {entity_type}\n"
            # if entity.get('name'):
            #     msg += f"**Name**: {entity['name']}\n"
            if entity.get('description'):
                msg += f"**Description**: {entity['description']}\n"
            if entity.get('hint'):
                msg += f"**Hint**: {entity['hint']}\n"
            msg += "\n"
        
        msg += "\nStart exploring! Remember:\n"
        msg += "- Use `investigate` on Tools to view detailed interface information before calling\n"
        msg += "- Use `investigate` on Items to view their contents\n"
        msg += "- Investigation may reveal new hidden entities or information\n"
        msg += "- Use the available parameters listed above as tool parameters\n"
        
        return msg