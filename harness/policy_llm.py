"""One model call per step. A bad JSON reply is not sent back to the API."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from harness.actions import parse_model_action
from harness.prompts import assistant_message, history_message, model_prompt


class LLMPolicy:
    def __init__(self, cfg: dict, run_dir: Path) -> None:
        self.cfg = cfg
        self.run_dir = run_dir
        self.system = model_prompt(cfg)
        self.history: list[dict] = []
        self.provider = (os.environ.get("LLM_PROVIDER") or "openai").strip().lower()
        self.temperature = float(os.environ.get("LLM_TEMPERATURE") or 0)
        self.max_tokens = int(os.environ.get("LLM_MAX_OUTPUT_TOKENS") or 1024)
        self.last_usage = {"prompt": 0, "completion": 0}
        self.last_raw = ""

    def note_result(self, obs: dict, action: dict, result: str) -> None:
        self.history.append({"obs": obs, "action": action, "result": result, "url": obs.get("url"), "title": ""})

    def act(self, obs: dict) -> dict:
        messages = self._messages(obs)
        raw, usage = self._complete(messages)
        self.last_raw = raw[:32768]
        self.last_usage = usage
        return parse_model_action(raw)

    def _messages(self, obs: dict) -> list[dict]:
        full_k = int((self.cfg.get("history") or {}).get("full_obs_k") or 4)
        shot_k = int((self.cfg.get("history") or {}).get("screenshot_k") or 2)
        prior = self.history
        messages = [{"role": "system", "content": self.system}]
        if len(prior) > full_k:
            for turn in prior[:-full_k]:
                _append_turn(messages, turn, full=False, with_image=False)
        window = prior[-full_k:]
        image_from = max(0, len(window) - shot_k)
        for index, turn in enumerate(window):
            _append_turn(messages, turn, full=True, with_image=index >= image_from)
        messages.append(history_message({"obs": obs}, full=True, with_image=True, include_notebook=True))
        return messages

    def _complete(self, messages: list[dict]) -> tuple[str, dict]:
        if self.provider == "anthropic":
            return self._anthropic(messages)
        return self._openai(messages)

    def _openai(self, messages: list[dict]) -> tuple[str, dict]:
        import httpx

        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("AGENT_API_KEY") or ""
        base = (os.environ.get("OPENAI_BASE_URL") or os.environ.get("AGENT_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        model = os.environ.get("OPENAI_MODEL") or os.environ.get("AGENT_MODEL") or "gpt-4.1"
        if not key:
            raise RuntimeError("缺少 OPENAI_API_KEY。没有密钥时请使用 --policy script。")
        payload = {
            "model": model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [_openai_message(item) for item in messages],
        }
        response = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        text = body["choices"][0]["message"]["content"] or ""
        usage = body.get("usage") or {}
        return text, {
            "prompt": int(usage.get("prompt_tokens") or 0),
            "completion": int(usage.get("completion_tokens") or 0),
        }

    def _anthropic(self, messages: list[dict]) -> tuple[str, dict]:
        import httpx

        key = os.environ.get("ANTHROPIC_API_KEY") or ""
        model = os.environ.get("ANTHROPIC_MODEL") or os.environ.get("OPENAI_MODEL") or "claude-sonnet-4-5"
        if not key:
            raise RuntimeError("缺少 ANTHROPIC_API_KEY。没有密钥时请使用 --policy script。")
        system, converted = to_anthropic_messages(messages)
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system,
                "messages": converted,
            },
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        text = "".join(part.get("text") or "" for part in body.get("content") or [] if part.get("type") == "text")
        usage = body.get("usage") or {}
        return text, {
            "prompt": int(usage.get("input_tokens") or 0),
            "completion": int(usage.get("output_tokens") or 0),
        }


def _append_turn(messages: list[dict], turn: dict, *, full: bool, with_image: bool) -> None:
    messages.append(history_message(turn, full=full, with_image=with_image))
    reply = assistant_message(turn)
    if reply:
        messages.append(reply)


def to_anthropic_messages(messages: list[dict]) -> tuple[str, list[dict]]:
    system = ""
    converted = []
    for item in messages:
        if item["role"] == "system":
            system = item["content"] if isinstance(item["content"], str) else ""
            continue
        role = "assistant" if item["role"] == "assistant" else "user"
        converted.append({"role": role, "content": _anthropic_content(item["content"])})
    return system, converted


def _openai_message(message: dict) -> dict:
    content = message.get("content")
    if isinstance(content, str):
        return {"role": message["role"], "content": content}
    parts = []
    for part in content:
        if part.get("type") == "text":
            parts.append({"type": "text", "text": part.get("text") or ""})
        elif part.get("type") == "image_path":
            encoded = _data_url(part.get("path") or "")
            if encoded:
                parts.append({"type": "image_url", "image_url": {"url": encoded}})
    return {"role": message["role"], "content": parts or ""}


def _anthropic_content(content) -> list[dict] | str:
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        if part.get("type") == "text":
            parts.append({"type": "text", "text": part.get("text") or ""})
        elif part.get("type") == "image_path":
            raw = _bytes(part.get("path") or "")
            if raw:
                parts.append(
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(raw).decode("ascii")},
                    }
                )
    return parts


def _data_url(path: str) -> str:
    raw = _bytes(path)
    if not raw:
        return ""
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def _bytes(path: str) -> bytes:
    file_path = Path(path)
    if not file_path.is_file():
        return b""
    return file_path.read_bytes()
