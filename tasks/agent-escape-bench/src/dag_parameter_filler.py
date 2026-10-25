#!/usr/bin/env python3
"""
Step 2: DAG Parameter Filler
This module fills in the specific values for DAG nodes using LLM API.
It reads the DAG skeleton JSON and uses LLM to generate appropriate parameter values.
"""

import json
import os
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from openai import OpenAI
from language_config import get_prompts

# Get all prompts from the configured language module
_prompts = get_prompts()
# Import all prompts as module-level variables
for attr_name in dir(_prompts):
    if not attr_name.startswith('_'):
        globals()[attr_name] = getattr(_prompts, attr_name)

class LLMClientFactory:
    """Factory for creating LLM API clients based on configuration."""

    @staticmethod
    def create_client(client_type: str = "auto", **kwargs):
        """
        Create an LLM client based on the specified type.

        Args:
            client_type: Type of client - "meituan", "yuju", "deepseek", or "auto"
            **kwargs: Additional arguments for the client

        Returns:
            An LLM client instance
        """
        if client_type == "meituan":
            return MeituanLLMClient(**kwargs)
        elif client_type == "yuju":
            return YuJuLLMClient(**kwargs)
        elif client_type == "deepseek":
            return DeepSeekLLMClient(**kwargs)
        elif client_type == "auto":
            # Auto-detect based on available credentials
            if "authorization" in kwargs:
                return MeituanLLMClient(**kwargs)
            elif "api_key" in kwargs:
                # Default to DeepSeek if api_key is provided
                return DeepSeekLLMClient(**kwargs)
            else:
                # Default to DeepSeek
                return DeepSeekLLMClient(**kwargs)
        else:
            raise ValueError(f"Unknown client type: {client_type}")


class BaseLLMClient:
    """Base class for LLM API clients."""

    def __init__(self, model: Optional[str] = None, **kwargs):
        """Initialize the LLM client."""
        self.model = model or self.default_model
        self.kwargs = kwargs

    @property
    def default_model(self) -> str:
        """Return the default model for this client."""
        raise NotImplementedError

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Send a chat request to the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            The LLM response text
        """
        raise NotImplementedError


class MeituanLLMClient(BaseLLMClient):
    """Client for Meituan internal API."""

    @property
    def default_model(self) -> str:
        return "gpt-4o-eva"

    def __init__(self, authorization: str = "", model: Optional[str] = None, **kwargs):
        """
        Initialize Meituan LLM client.

        Args:
            authorization: Authorization string for Meituan API
            model: Model name (default: gpt-4o-eva)
            **kwargs: Additional arguments
        """
        super().__init__(model, **kwargs)
        self.authorization = authorization
        self.api_endpoint = "" # 已删除**

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat request to Meituan API."""
        try:
            import requests
        except ImportError:
            raise ImportError("requests library is required. Install it with: pip install requests")

        headers = {
            "Authorization": self.authorization,
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages
        }

        response = requests.post(self.api_endpoint, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

class YuJuLLMClient(BaseLLMClient):
    """Client for YuJu platform API, using OpenAI SDK."""

    @property
    def default_model(self) -> str:
        # 和命令行默认一致
        return "gemini-3-pro-preview"

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        api_endpoint: str = "", # 已删除**
        uid: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize YuJu LLM client.

        Args:
            api_key: YuJu 平台的 API Key（必填）
            model: 模型名称（默认 gpt-5.2-pro）
            api_endpoint: YuJu 的 base_url（默认 ） # 已删除**
            uid: 加密后的 user id，如果不传则用环境变量 YUJU_UID
            **kwargs: 其他参数（忽略）
        """
        super().__init__(model, **kwargs)

        if not api_key:
            raise ValueError("YuJu api_key is required")

        self.api_endpoint = api_endpoint
        self.uid = uid or os.environ.get("YUJU_UID") or "" # 已删除**

        # 关键：用 OpenAI SDK，并把 uid 放进默认 headers
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.api_endpoint,
            default_headers={
                "uid": self.uid,
            },
        )

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat request to YuJu API via OpenAI SDK."""
        # 如果语聚完全兼容 /v1/chat/completions 接口：
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            # 可以视情况加个超时，避免长时间卡住
            # timeout=120,
        )
        return resp.choices[0].message.content


class DeepSeekLLMClient(BaseLLMClient):
    """Client for DeepSeek API (OpenAI compatible)."""

    @property
    def default_model(self) -> str:
        return "deepseek-chat"

    def __init__(self, api_key: str = "", model: Optional[str] = None,
                 api_endpoint: str = "https://api.deepseek.com", **kwargs):
        """
        Initialize DeepSeek LLM client.

        Args:
            api_key: API key for DeepSeek
            model: Model name (default: deepseek-chat)
            api_endpoint: Custom API endpoint (default: https://api.deepseek.com)
            **kwargs: Additional arguments
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.api_endpoint = api_endpoint

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat request to DeepSeek API."""
        try:
            import requests
        except ImportError:
            raise ImportError("requests library is required. Install it with: pip install requests")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages
        }

        response = requests.post(
            f"{self.api_endpoint}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]


class DAGParameterFiller:
    """Fills in parameter values for DAG nodes using LLM."""

    def __init__(self, llm_client: BaseLLMClient):
        """
        Initialize the parameter filler.

        Args:
            llm_client: An LLM client instance
        """
        self.llm_client = llm_client

    def load_skeleton(self, skeleton_path: str) -> Dict[str, Any]:
        """
        Load a DAG skeleton from JSON file.

        Args:
            skeleton_path: Path to the skeleton JSON file

        Returns:
            The skeleton dictionary
        """
        with open(skeleton_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_system_prompt(self) -> str:
        """Generate the system prompt for the LLM."""
        return """You are an expert "DAG Source Initialization Value Generator". You are proficient in generating format-correct, semantically reasonable, and executable initialization data for various tool nodes (cryptography, mathematical calculations, string processing, file operations, etc.). You strictly follow the given type constraints and output format requirements, outputting only strict JSON without any other text or explanation."""

    # def generate_user_prompt(self, skeleton: Dict[str, Any]) -> str:
    #     """
    #     Generate the user prompt with the DAG skeleton.

    #     Args:
    #         skeleton: The DAG skeleton dictionary

    #     Returns:
    #         The user prompt string
    #     """
    #     prompt = "Please fill in the missing parameter values for the following DAG:\n\n"
    #     prompt += json.dumps(skeleton, indent=2, ensure_ascii=False)
    #     prompt += "\n\nGenerate appropriate values for all unconnected input ports."
    #     return prompt
    def generate_user_prompt(self, skeleton: Dict[str, Any]) -> str:
        """
        Generate the user prompt with the DAG skeleton.

        Args:
            skeleton: The DAG skeleton dictionary

        Returns:
            The user prompt string
        """
        DAG_JSON = skeleton
        BY_NODE_JSON = skeleton["metadata"]["source_init"]["by_node"]
        prompt = fill_source_prompt2.format(DAG_JSON=DAG_JSON, BY_NODE_JSON=BY_NODE_JSON)
        return prompt

    def fill_parameters(self, skeleton_path: str) -> Dict[str, Any]:
        """
        Fill in parameter values for a DAG skeleton.

        Args:
            skeleton_path: Path to the skeleton JSON file

        Returns:
            Dictionary with filled parameters
        """
        # Load the skeleton
        skeleton = self.load_skeleton(skeleton_path)
        print(f"要填充的骨架是：\n{skeleton}")

        # Generate prompts
        system_prompt = self.generate_system_prompt()
        user_prompt = self.generate_user_prompt(skeleton)
        print("system prompt 和 user prompt创建完成！✅")

        # Call LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        print(f"Calling LLM to fill parameters for {skeleton_path}...")
        print(f"messages内容为：\n{messages}\n")
        response = self.llm_client.chat(messages)
        print("API 调用完成！✅")
        # Parse the response
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parameters = json.loads(json_match.group())
            else:
                parameters = json.loads(response)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse LLM response as JSON")
            print(f"Response: {response}")
            parameters = {}

        return parameters

    def save_filled_parameters(self, parameters: Dict[str, Any], output_path: str) -> None:
        """
        Save filled parameters to a JSON file.

        Args:
            parameters: The filled parameters dictionary
            output_path: Path to save the parameters
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parameters, f, indent=2, ensure_ascii=False)
        print(f"Saved filled parameters to {output_path}")


def main():
    """Main entry point for the parameter filler."""
    parser = argparse.ArgumentParser(description="Fill DAG parameters using LLM.")
    parser.add_argument(
    "--skeleton",
    required=False,
    default="./dag_2026_sources/skeleton_8d2a10cf.json",
    help="Path to the DAG skeleton JSON file")
    parser.add_argument("--output", "-o", help="Output path for filled parameters", default="./dag_2026_init/skeleton_8d2a10cf_source_init2.json")
    parser.add_argument("--client-type", default="yuju",
                       choices=["meituan", "yuju", "deepseek", "auto"],
                       help="Type of LLM client to use")
    parser.add_argument("--model", help="Model name to use", default="gemini-3-pro-preview")
    # parser.add_argument("--model", help="Model name to use", default="gemini-2.5-pro")
    parser.add_argument("--authorization", help="Authorization string (for Meituan)")
    parser.add_argument("--api-key", help="API key (for YuJu or DeepSeek)", default="") # 已删除**
    parser.add_argument("--api-endpoint", help="Custom API endpoint (for DeepSeek)")

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        skeleton_name = os.path.splitext(os.path.basename(args.skeleton))[0]
        output_path = f"parameters/{skeleton_name}_parameters.json"

    # Create LLM client
    client_kwargs = {}
    if args.model:
        client_kwargs["model"] = args.model
    if args.authorization:
        client_kwargs["authorization"] = args.authorization
    if args.api_key:
        client_kwargs["api_key"] = args.api_key
    if args.api_endpoint:
        client_kwargs["api_endpoint"] = args.api_endpoint

    llm_client = LLMClientFactory.create_client(args.client_type, **client_kwargs)

    # Fill parameters
    filler = DAGParameterFiller(llm_client)
    parameters = filler.fill_parameters(args.skeleton)

    # Save parameters
    filler.save_filled_parameters(parameters, output_path)

    print(f"Parameter filling completed!")


if __name__ == "__main__":
    main()