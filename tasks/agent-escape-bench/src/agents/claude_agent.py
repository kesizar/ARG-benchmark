"""
Anthropic Claude API Implementation
Supports Claude's native tool use (function calling) with extended thinking
"""
import os
import json
import time
import logging
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base_agent import BaseModelAgent

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from language_config import get_prompts

# Get prompts based on current language setting
_prompts = get_prompts()
AGENT_FUNCTION_CALLING_HINT = _prompts.AGENT_FUNCTION_CALLING_HINT

logger = logging.getLogger(__name__)


class ClaudeAgent(BaseModelAgent):
    """
    Anthropic Claude API Implementation

    Supports:
    1. Native tool use (function calling) - Claude's built-in tool calling
    2. Extended thinking (optional) - for deeper reasoning
    """

    def __init__(self,
                 model: str = "claude-opus-4-6",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 8192,
                 max_history_messages: int = 100,
                 max_retries: int = 3,
                 enable_thinking: bool = False,
                 thinking_budget: int = 10000,
                 default_headers: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        Initialize Claude Agent

        Args:
            model: Model name (e.g., "claude-opus-4-6", "claude-sonnet-4-6")
            api_key: Anthropic API key, or from ANTHROPIC_API_KEY env var
            base_url: API base URL (optional, for proxy/custom endpoints)
            temperature: Sampling temperature (ignored when thinking is enabled)
            max_tokens: Maximum output tokens
            max_history_messages: Maximum history messages to keep
            max_retries: Maximum retry attempts
            enable_thinking: Whether to enable extended thinking
            thinking_budget: Token budget for thinking (only used when enable_thinking=True)
            default_headers: Custom HTTP headers
            **kwargs: Other parameters
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

        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

        # Initialize Anthropic client
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API Key not provided. "
                "Please set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )

        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if default_headers:
            client_kwargs["default_headers"] = default_headers

        self.client = anthropic.Anthropic(**client_kwargs)

        # Conversation history (Claude format: list of {"role": "user"/"assistant", "content": ...})
        self.messages = []
        self.system_prompt = None

        # Tool definitions
        self.tools = []

        # Multi-tool calling state
        self.pending_tool_uses = []  # Store pending tool use blocks
        self.tool_use_results = []  # Store tool use results

        logger.info(
            f"Initialized ClaudeAgent - model: {model}, "
            f"thinking: {enable_thinking}, max_tokens: {max_tokens}"
        )

    def initialize(self, initial_data: Dict[str, Any]):
        """Initialize agent and receive initial environment information"""
        self.start_time = datetime.now()
        self.narrative = initial_data.get("narrative", "")
        self.available_entities = initial_data.get("available_entities", [])
        self.available_information = initial_data.get("available_information", [])
        self.win_node_id = initial_data.get("win_node_id", "")

        # Build system prompt
        self.system_prompt = self._build_system_prompt() + AGENT_FUNCTION_CALLING_HINT

        # Build initial environment description
        initial_message = self._build_initial_message()

        # Initialize conversation history (Claude uses separate system param, not in messages)
        self.messages = [
            {"role": "user", "content": initial_message}
        ]

        # Build tool definitions
        self.tools = self._build_tools_schema()

        logger.info(f"Agent initialized - entities: {len(self.available_entities)}, tools: {len(self.available_tools)}")

    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Build tool definitions for Claude's native tool use"""
        tools = []

        # Create tool definitions for each investigated tool node
        for tool in self.available_tools:
            node_id = tool.get('id')
            description = tool.get('description', f"Tool node {node_id}")

            # Build input schema
            properties = {}
            required = []

            # Check if it's a terminal-type tool
            template_id = tool.get('_template_id', '')
            is_terminal = (
                template_id.startswith('terminal') or
                'terminal' in template_id.lower() or
                node_id.startswith('terminal')
            )

            if tool.get('inputs'):
                for inp in tool['inputs']:
                    param_type = self._convert_type_to_json_schema(inp['type'])
                    param_description = inp.get('description', '')

                    properties[inp['name']] = {
                        "type": param_type,
                        "description": param_description
                    }

                    # Check if optional
                    is_optional = is_terminal or (
                        'optional' in param_description.lower() or
                        '(optional)' in param_description.lower() or
                        'optional:' in param_description.lower() or
                        'default' in param_description.lower() or
                        '(default' in param_description.lower()
                    )

                    if not is_optional:
                        required.append(inp['name'])

            tool_def = {
                "name": node_id,
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            tools.append(tool_def)

        # Add investigate tool
        tools.append({
            "name": "investigate",
            "description": "Investigate an item or information, may discover hidden content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "ID of the item or information to investigate"
                    }
                },
                "required": ["node_id"]
            }
        })

        # Add use_item tool
        tools.append({
            "name": "use_item",
            "description": "For items that require parameters to unlock (such as containers, safes), provide necessary parameters to use them. Can only be used for Item type nodes.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "string",
                        "description": "Item node ID to use (must be Item type)"
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Parameters to provide to the item, parameter names and values must match required_inputs returned by investigate"
                    }
                },
                "required": ["node_id", "arguments"]
            }
        })

        # Add submit_answer tool
        tools.append({
            "name": "submit_answer",
            "description": "[ULTIMATE GOAL] Submit the victory string to complete the task and escape the room. When you believe you have obtained the victory string, call this function to submit it. If correct, the system will return '🎉 Congratulations on successfully escaping the room! Your answer is correct: [your answer]'. Only by successfully calling this function is the task truly completed.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "The complete victory string informed by the system (could be a description, code, numbers, or any form of text)"
                    }
                },
                "required": ["answer"]
            }
        })

        logger.debug(f"Built tools schema with {len(tools)} tools: {[t['name'] for t in tools]}")
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
        """Trim conversation history to keep within maximum length limit"""
        if len(self.messages) <= self.max_history_messages:
            return

        logger.debug(f"Trimming history: {len(self.messages)} messages > {self.max_history_messages} limit")

        # Preserve initial user message
        preserved_messages = [self.messages[0]]

        # Trim remaining messages
        remaining_messages = self.messages[1:]
        max_remaining = self.max_history_messages - 1

        if len(remaining_messages) > max_remaining:
            trimmed = remaining_messages[-max_remaining:]

            # Ensure conversation starts with user message (Claude requirement)
            # If first message is assistant, we need to find the previous user message
            if trimmed and trimmed[0].get("role") == "assistant":
                # Check if assistant message contains tool_use that needs tool_result
                # Just remove leading assistant messages that break the flow
                while trimmed and trimmed[0].get("role") == "assistant":
                    trimmed.pop(0)

            # Ensure we don't start with a tool_result without preceding assistant+tool_use
            if trimmed and trimmed[0].get("role") == "user":
                content = trimmed[0].get("content", "")
                if isinstance(content, list):
                    # Check if it contains tool_result blocks
                    has_tool_result = any(
                        isinstance(block, dict) and block.get("type") == "tool_result"
                        for block in content
                    )
                    if has_tool_result:
                        trimmed.pop(0)

            self.messages = preserved_messages + trimmed

        logger.debug(f"Trimmed history to {len(self.messages)} messages")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((anthropic.APIError, anthropic.APIConnectionError)),
        reraise=True
    )
    def _call_api(self) -> Any:
        """API call with retry mechanism"""
        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": self.messages,
        }

        if self.tools:
            params["tools"] = self.tools
            params["tool_choice"] = {"type": "auto"}

        # Handle thinking mode
        if self.enable_thinking:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget
            }
            # Temperature must be 1 when thinking is enabled
        else:
            params["temperature"] = self.temperature

        return self.client.messages.create(**params)

    def step(self) -> Optional[Dict[str, Any]]:
        """Execute one reasoning step, return the action to execute"""
        try:
            # Trim history
            self._trim_history()

            logger.debug(f"Calling API - model: {self.model}, messages: {len(self.messages)}")
            if self.tools:
                tool_names = [t['name'] for t in self.tools]
                logger.info(f"Available tools for this API call: {tool_names}")

            start_time = time.time()

            # Call API
            response = self._call_api()

            elapsed = time.time() - start_time
            self.api_calls += 1

            # Update token statistics
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                cost = self._estimate_cost(input_tokens, output_tokens)
                self.total_cost += cost

                logger.info(
                    f"API call #{self.api_calls} - elapsed: {elapsed:.2f}s, "
                    f"tokens: {input_tokens}/{output_tokens}, cost: ${cost:.4f}"
                )

            # Process response content blocks
            tool_use_blocks = []
            text_content = ""

            for block in response.content:
                if block.type == "tool_use":
                    tool_use_blocks.append(block)
                elif block.type == "text":
                    text_content += block.text
                elif block.type == "thinking":
                    # Log thinking content for debugging
                    logger.debug(f"Thinking: {block.thinking[:200]}...")

            if tool_use_blocks:
                # Process tool use blocks
                actions = self._handle_tool_uses(tool_use_blocks)

                # Save assistant message to history (full content blocks)
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Store pending tool uses
                self.pending_tool_uses = tool_use_blocks
                self.tool_use_results = []

                logger.info(f"Parsed {len(actions)} actions")
                return {
                    "action": "parallel_tool_calls",
                    "tool_calls": actions,
                    "count": len(actions)
                }
            else:
                # No tool use - model chose to respond with text only
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                logger.warning("No tool calls - model chose to wait")
                return {
                    "action": "wait",
                    "reasoning": text_content or "Model did not call any tools"
                }

        except Exception as e:
            logger.error(f"Agent step error: {e}", exc_info=True)

            # Handle broken conversation state
            if self.messages and self.messages[-1].get("role") == "user":
                # Check if last user message contains tool_result without preceding assistant
                pass

            return {
                "action": "wait",
                "reasoning": f"Error: {str(e)}"
            }

    def _handle_tool_uses(self, tool_use_blocks: List) -> List[Dict[str, Any]]:
        """
        Process Claude tool use blocks

        Args:
            tool_use_blocks: List of tool_use content blocks from Claude response

        Returns:
            List of action dicts compatible with the evaluator
        """
        actions = []

        for block in tool_use_blocks:
            tool_name = block.name
            arguments = block.input
            tool_use_id = block.id

            logger.debug(f"Tool use: {tool_name}, args: {arguments}, id: {tool_use_id}")

            # Handle investigate
            if tool_name == "investigate":
                actions.append({
                    "action": "investigate",
                    "node_id": arguments.get("node_id"),
                    "reasoning": f"Investigate {arguments.get('node_id')}",
                    "tool_call_id": tool_use_id
                })
                continue

            # Handle use_item
            if tool_name == "use_item":
                actions.append({
                    "action": "use_item",
                    "node_id": arguments.get("node_id"),
                    "arguments": arguments.get("arguments", {}),
                    "reasoning": f"Use item {arguments.get('node_id')} (params: {arguments.get('arguments', {})})",
                    "tool_call_id": tool_use_id
                })
                continue

            # Handle submit_answer
            if tool_name == "submit_answer":
                actions.append({
                    "action": "submit_answer",
                    "answer": arguments.get("answer"),
                    "reasoning": f"Submit answer: {arguments.get('answer')}",
                    "tool_call_id": tool_use_id
                })
                continue

            # Handle regular tool calls: tool_name is the node_id
            matching_tool = self._find_tool_by_node_id(tool_name)

            if matching_tool:
                actions.append({
                    "action": "tool_call",
                    "node_id": tool_name,
                    "arguments": arguments,
                    "reasoning": f"Call node {tool_name}",
                    "tool_call_id": tool_use_id
                })
            else:
                logger.warning(f"Unknown node or not investigated: {tool_name}")
                actions.append({
                    "action": "error",
                    "reasoning": f"Unknown node or not investigated: {tool_name}",
                    "tool_call_id": tool_use_id,
                    "error": f"Node '{tool_name}' not found or not investigated yet"
                })

        return actions

    def _find_tool_by_node_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Find tool by node_id"""
        for tool in self.available_tools:
            if tool.get('id') == node_id:
                return tool
        return None

    def receive_feedback(self, result: Dict[str, Any], tool_call_id: Optional[str] = None):
        """
        Receive feedback from the environment

        Args:
            result: Execution result
            tool_call_id: Tool use ID (for parallel tool calls)
        """
        if tool_call_id:
            self.tool_use_results.append({
                "tool_call_id": tool_call_id,
                "result": result
            })

            # If not all results collected yet, return
            if len(self.tool_use_results) < len(self.pending_tool_uses):
                logger.debug(
                    f"Collected {len(self.tool_use_results)}/{len(self.pending_tool_uses)} tool use results"
                )
                return

            # All results collected, process them
            logger.info(f"All {len(self.tool_use_results)} tool use results collected, processing feedback")
            self._process_parallel_feedback()

            # Clear state
            self.pending_tool_uses = []
            self.tool_use_results = []
            return

        # Single action feedback (non-parallel)
        # For Claude, we need to add a user message with the feedback
        feedback_msg = self._build_feedback_message(result)
        self.messages.append({"role": "user", "content": feedback_msg})
        logger.debug(f"Feedback: {feedback_msg[:200]}...")

    def _process_parallel_feedback(self):
        """
        Process parallel tool use feedback.
        Claude requires tool_result blocks in a user message following the assistant's tool_use.
        """
        # Build tool_result content blocks
        tool_results_content = []

        for result_data in self.tool_use_results:
            tool_call_id = result_data["tool_call_id"]
            result = result_data["result"]

            # Build the tool result content
            content = self._build_tool_result_content(result)

            tool_results_content.append({
                "type": "tool_result",
                "tool_use_id": tool_call_id,
                "content": content,
                "is_error": not result.get("ok", False)
            })

            # Update internal state
            self._update_state_from_result(result)

        # Add as a single user message with all tool_result blocks
        self.messages.append({
            "role": "user",
            "content": tool_results_content
        })

        logger.info(f"Added {len(tool_results_content)} tool_result blocks to conversation history")

    def _build_tool_result_content(self, result: Dict[str, Any]) -> str:
        """Build content string for a tool_result block"""
        if not result.get("ok"):
            return f"Error: {result.get('error', 'Unknown error')}"

        content = ""

        # Tool investigate result
        if result.get("entity_type") == "Tool":
            details = result.get("details", {})
            content += f"Tool investigation successful: {details.get('id')}\n"
            content += f"Description: {details.get('description', 'N/A')}\n"

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

        # Item investigate result
        elif result.get("entity_type") == "Item":
            if result.get("message"):
                content = f"✓ {result['message']}"
            elif result.get("required_inputs"):
                content = "Item investigation successful\n"
                content += "⚠️ This item requires parameters to unlock.\n"
                content += "Required parameters (use with use_item):\n"
                for inp in result["required_inputs"]:
                    content += f"  - {inp['name']} ({inp['type']}): {inp.get('description', 'N/A')}\n"
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"
            elif "content" in result:
                content = f"Item content: {result.get('content')}"
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"
            else:
                content = "Item investigation successful: This item is a trigger with no readable content"
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"

        # Tool call result
        elif "output_values" in result:
            content = f"Output: {json.dumps(result['output_values'], ensure_ascii=False)}"

            if result.get("parameter_feedback"):
                feedback = result["parameter_feedback"]
                content += f"\n\n{feedback['message']}"

        # use_item result
        elif result.get("message"):
            content = result.get("message")
            if result.get("message") != "This item has already been successfully unlocked by you.":
                if result.get('narrative'):
                    content += f"\nBackground clue: {result.get('narrative')}"
                if result.get('content'):
                    content += f"\nContent: {json.dumps(result.get('content'), ensure_ascii=False)}"

        # Newly revealed entities
        if result.get("newly_revealed"):
            newly_revealed = result['newly_revealed']
            if newly_revealed:
                content += f"\n\nDiscovered {len(newly_revealed)} new entities:\n"
                for entity in newly_revealed:
                    content += f"- {entity.get('type')}: {entity['id']}\n"
                    if entity.get('description'):
                        content += f"  Description: {entity['description']}\n"
                    if entity.get('hint'):
                        content += f"  Hint: {entity['hint']}\n"

        # Investigate hints
        if result.get("investigate_hints"):
            hints = result['investigate_hints']
            if hints:
                content += f"\n\n💡 Exploration hints:\n"
                for hint in hints:
                    tool_id = hint.get('tool_id')
                    hint_text = hint.get('hint', '')
                    content += f"- Tool {tool_id}: {hint_text}\n"

        # Victory
        if result.get("is_win"):
            content += f"\n🎉 {result.get('victory_message', 'Congratulations on escaping!')}"
        elif result.get("is_win") == False and result.get("error"):
            content += f"\n❌ {result.get('error')}"

        return content

    def _build_feedback_message(self, result: Dict[str, Any]) -> str:
        """Build feedback message for single (non-parallel) action results"""
        # This is used when there's no tool_call_id (legacy single-action mode)
        return self._build_tool_result_content(result)

    def _update_state_from_result(self, result: Dict[str, Any]):
        """Update agent internal state from result"""
        if not result.get("ok"):
            return

        # Tool investigate - add to available_tools
        if result.get("entity_type") == "Tool":
            details = result.get("details", {})
            tool_id = details.get('id')
            if details and tool_id and tool_id not in [t.get('id') for t in self.available_tools]:
                self.available_tools.append(details)
                self.investigated_entities.add(tool_id)
                logger.info(f"Tool investigated and added: {tool_id}")

                # Rebuild tools schema
                self.tools = self._build_tools_schema()
                logger.debug(f"Rebuilt tools schema with {len(self.tools)} tools")

        # Newly revealed entities
        if result.get("newly_revealed"):
            newly_revealed = result['newly_revealed']
            for entity in newly_revealed:
                if entity['id'] not in [e['id'] for e in self.available_entities]:
                    self.available_entities.append(entity)
                    logger.info(f"New entity revealed: {entity['id']}, type: {entity.get('type')}")

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate API call cost (USD) for Claude models"""
        model_lower = self.model.lower()

        if "opus" in model_lower:
            # Claude Opus pricing: $15/MTok input, $75/MTok output
            input_cost = input_tokens * 15.0 / 1_000_000
            output_cost = output_tokens * 75.0 / 1_000_000
        elif "sonnet" in model_lower:
            # Claude Sonnet pricing: $3/MTok input, $15/MTok output
            input_cost = input_tokens * 3.0 / 1_000_000
            output_cost = output_tokens * 15.0 / 1_000_000
        elif "haiku" in model_lower:
            # Claude Haiku pricing: $0.25/MTok input, $1.25/MTok output
            input_cost = input_tokens * 0.25 / 1_000_000
            output_cost = output_tokens * 1.25 / 1_000_000
        else:
            # Default to Sonnet pricing
            input_cost = input_tokens * 3.0 / 1_000_000
            output_cost = output_tokens * 15.0 / 1_000_000

        return input_cost + output_cost

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics with Claude-specific info"""
        stats = super().get_statistics()
        stats["model_provider"] = "anthropic"
        stats["thinking_enabled"] = self.enable_thinking
        if self.enable_thinking:
            stats["thinking_budget"] = self.thinking_budget
        return stats
