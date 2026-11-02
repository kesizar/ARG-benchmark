"""One model call per step. A bad JSON reply is not sent back to the API."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from harness.actions import parse_model_action
from harness.prompts import assistant_message, history_message, model_prompt


class ModelRefusal(Exception):
    """The model returned an explicit refusal in an otherwise valid response."""


class LLMPolicy:
    def __init__(self, cfg: dict, run_dir: Path) -> None:
        self.cfg = cfg
        self.run_dir = run_dir
        self.system = model_prompt(cfg)
        self.history: list[dict] = []
        self.provider = (os.environ.get("LLM_PROVIDER") or "openai").strip().lower()
        self.model_name = ((os.environ.get("ANTHROPIC_MODEL") or os.environ.get("OPENAI_MODEL") or "claude-sonnet-4-5")
                           if self.provider == "anthropic" else
                           (os.environ.get("OPENAI_MODEL") or os.environ.get("AGENT_MODEL") or "gpt-4.1"))
        self.endpoint = ("https://api.anthropic.com/v1/messages" if self.provider == "anthropic" else
                         (os.environ.get("OPENAI_BASE_URL") or os.environ.get("AGENT_BASE_URL") or "https://api.openai.com/v1").rstrip("/") + "/chat/completions")
        self.official = cfg.get("_run_kind") == "official"
        self.trust_env = (os.environ.get("AGENT_HTTP_TRUST_ENV") or "true").strip().lower() not in {"0", "false", "no"}
        self.temperature = None if self.official else float(os.environ.get("LLM_TEMPERATURE") or 0)
        self.max_tokens = int(os.environ.get("LLM_MAX_OUTPUT_TOKENS") or (32768 if self.official else 1024))
        self.last_usage = {"prompt": 0, "completion": 0}
        self.last_raw = ""
        self.last_reasoning = ""
        self.last_response_model = ""
        self.last_image_mode = ""
        self.image_fallbacks = 0
        self.clock = None
        self.last_finish_reason = None
        self.last_request_id = None
        self.last_refusal = None
        self.preserve_reasoning = (os.environ.get("PRESERVE_REASONING") or "").strip().lower() in {"1", "true", "yes"}
        self.enable_thinking = self.preserve_reasoning or (os.environ.get("ENABLE_THINKING") or "").strip().lower() in {"1", "true", "yes"}
        self.reasoning_effort = (os.environ.get("LLM_REASONING_EFFORT") or "").strip().lower()
        if self.official and not self.reasoning_effort and (
            (self.provider == "openai" and self.model_name.startswith("gpt-6")) or self.provider == "anthropic"
        ):
            self.reasoning_effort = "medium"
        self.anthropic_adaptive = self.official and self.provider == "anthropic"

    def profile(self) -> dict:
        parts = urlsplit(self.endpoint)
        endpoint = urlunsplit((parts.scheme, parts.hostname or "", parts.path, "", ""))
        if parts.port:
            endpoint = urlunsplit((parts.scheme, f"{parts.hostname}:{parts.port}", parts.path, "", ""))
        return {"provider": self.provider, "model": self.model_name, "endpoint": endpoint,
                "temperature": self.temperature, "max_tokens": self.max_tokens,
                "enable_thinking": self.enable_thinking, "preserve_reasoning": self.preserve_reasoning,
                "reasoning_effort": self.reasoning_effort, "anthropic_adaptive": self.anthropic_adaptive,
                "http_trust_env": self.trust_env,
                "request_total_timeout_seconds": 900 if self.official else None,
                "request_deadline_mode": "subprocess_total" if self.official else "httpx_phase",
                "obs_mode": self.cfg.get("obs_mode"), "history": self.cfg.get("history") or {},
                "require_images": bool(self.cfg.get("require_images"))}

    def profile_sha256(self) -> str:
        data = json.dumps(self.profile(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def note_result(self, obs: dict, action: dict, result: str, reply: str = "", reasoning: str = "") -> None:
        self.history.append({
            "obs": obs,
            "action": action,
            "result": result,
            "reply": reply,
            "reasoning": reasoning if self.preserve_reasoning else "",
            "url": obs.get("url"),
            "title": "",
        })

    def act(self, obs: dict) -> dict:
        import httpx

        if self.cfg.get("require_images"):
            screenshot = obs.get("screenshot")
            if not screenshot or not Path(screenshot).is_file() or Path(screenshot).stat().st_size == 0:
                raise RuntimeError("当前截图缺失或为空，不能回退为纯文本")

        for mode in ("all", "current", "none"):
            try:
                raw, usage = self._complete(self._messages(obs, images=mode))
                self.last_image_mode = mode
                break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 400:
                    detail = (exc.response.text or "").replace("\n", " ")[:300]
                    print(f"接口返回 400：{detail}", flush=True)
                if exc.response.status_code != 400 or mode == "none" or self.cfg.get("require_images"):
                    raise
                self.image_fallbacks += 1
                print("当前截图仍被拒绝，改为只发文字" if mode == "current" else "截图请求被拒绝，减少图片后重试", flush=True)
        self.last_raw = raw[:32768]
        self.last_usage = usage
        if self.last_finish_reason in {"content_filter", "safety"}:
            raise RuntimeError("服务安全系统拦截输出，需人工审查")
        if self.last_refusal or self.last_finish_reason == "refusal":
            raise ModelRefusal(str(self.last_refusal or "模型拒绝"))
        if self.last_finish_reason in {"length", "max_tokens", "model_context_window_exceeded"}:
            raise ValueError("模型输出因长度限制被截断")
        return parse_model_action(raw)

    def _messages(self, obs: dict, images: str = "all") -> list[dict]:
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
            _append_turn(messages, turn, full=True, with_image=images == "all" and index >= image_from)
        messages.append(history_message({"obs": obs}, full=True, with_image=images != "none", include_notebook=True))
        return messages

    def _complete(self, messages: list[dict]) -> tuple[str, dict]:
        if self.provider == "anthropic":
            return self._anthropic(messages)
        return self._openai(messages)

    def _openai(self, messages: list[dict]) -> tuple[str, dict]:
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("AGENT_API_KEY") or ""
        base = (os.environ.get("OPENAI_BASE_URL") or os.environ.get("AGENT_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        model = self.model_name
        if not key:
            raise RuntimeError("缺少 OPENAI_API_KEY。没有密钥时请使用 --policy script。")
        payload = {
            "model": model,
            "messages": [_openai_message(item) for item in messages],
        }
        payload["max_completion_tokens" if self.official and self.provider == "openai" and model.startswith("gpt-6") else "max_tokens"] = self.max_tokens
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.enable_thinking:
            payload["enable_thinking"] = True
        if self.preserve_reasoning:
            payload["preserve_thinking"] = True
        response = _post_with_retry(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=900 if self.official else 120,
            attempts=3 if self.official else 8,
            clock=self.clock,
            log_path=self.run_dir / "model_requests.jsonl",
            trust_env=self.trust_env,
        )
        response.raise_for_status()
        body = response.json()
        self.last_request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
        self.last_finish_reason = (body.get("choices") or [{}])[0].get("finish_reason")
        self.last_response_model = str(body.get("model") or "")
        message = body["choices"][0]["message"] or {}
        self.last_refusal = message.get("refusal")
        text = message.get("content") or ""
        self.last_reasoning = str(message.get("reasoning_content") or "")[:32768] if self.preserve_reasoning else ""
        usage = body.get("usage") or {}
        return text, {
            "prompt": int(usage.get("prompt_tokens") or 0),
            "completion": int(usage.get("completion_tokens") or 0),
        }

    def _anthropic(self, messages: list[dict]) -> tuple[str, dict]:
        import httpx

        key = os.environ.get("ANTHROPIC_API_KEY") or ""
        model = self.model_name
        if not key:
            raise RuntimeError("缺少 ANTHROPIC_API_KEY。没有密钥时请使用 --policy script。")
        system, converted = to_anthropic_messages(messages)
        payload = {
            "model": model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": converted,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.anthropic_adaptive:
            payload["thinking"] = {"type": "adaptive"}
            if self.reasoning_effort:
                payload["output_config"] = {"effort": self.reasoning_effort}
        response = _post_with_retry(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=900 if self.official else 120,
            attempts=3 if self.official else 1,
            clock=self.clock,
            log_path=self.run_dir / "model_requests.jsonl",
            trust_env=self.trust_env,
        )
        response.raise_for_status()
        body = response.json()
        self.last_request_id = response.headers.get("request-id") or response.headers.get("x-request-id")
        self.last_response_model = str(body.get("model") or "")
        self.last_finish_reason = body.get("stop_reason")
        self.last_refusal = None
        text = "".join(part.get("text") or "" for part in body.get("content") or [] if part.get("type") == "text")
        usage = body.get("usage") or {}
        return text, {
            "prompt": int(usage.get("input_tokens") or 0),
            "completion": int(usage.get("output_tokens") or 0),
        }


def _post_with_retry(url: str, **kwargs):
    """Retry a model call when the TLS connection drops before the request is sent."""
    import time

    import httpx

    timeout = kwargs.pop("timeout", 120)
    attempts = kwargs.pop("attempts", 8)
    clock = kwargs.pop("clock", None)
    log_path = kwargs.pop("log_path", None)
    trust_env = kwargs.pop("trust_env", True)
    last_error: Exception | None = None
    for attempt in range(attempts):
        current_timeout = clock.timeout(timeout) if clock else timeout
        client_timeout = httpx.Timeout(current_timeout, connect=min(20, current_timeout))
        attempt_started = time.monotonic()
        try:
            _request_log(log_path, {"attempt": attempt + 1, "event": "started"})
            if clock:
                response = _post_with_deadline(url, current_timeout, trust_env, kwargs)
            else:
                with httpx.Client(timeout=client_timeout, trust_env=trust_env) as client:
                    response = client.post(url, **kwargs)
            if response.status_code not in {429, 500, 502, 503, 504}:
                _request_log(log_path, {"attempt": attempt + 1, "status": response.status_code,
                                        "request_id": response.headers.get("x-request-id") or response.headers.get("request-id"),
                                        "elapsed": time.monotonic() - attempt_started})
                return response
            last_error = httpx.HTTPStatusError(
                f"模型接口返回 {response.status_code}",
                request=response.request,
                response=response,
            )
        except httpx.TransportError as exc:
            last_error = exc
        elapsed = time.monotonic() - attempt_started
        if clock:
            clock.add_infrastructure_delay(elapsed)
        _request_log(log_path, {"attempt": attempt + 1, "status": getattr(getattr(last_error, "response", None), "status_code", None),
                                "request_id": (last_error.response.headers.get("x-request-id") or last_error.response.headers.get("request-id")) if isinstance(last_error, httpx.HTTPStatusError) else None,
                                "error_type": type(last_error).__name__, "elapsed": elapsed})
        if clock:
            clock.check()
        if attempt == attempts - 1:
            break
        delay = (5, 15)[min(attempt, 1)] if attempts == 3 else min(20, 5 * (attempt + 1))
        if isinstance(last_error, httpx.HTTPStatusError):
            try:
                delay = max(delay, float(last_error.response.headers.get("Retry-After", "0")))
            except ValueError:
                try:
                    deadline = parsedate_to_datetime(last_error.response.headers["Retry-After"])
                    delay = max(delay, (deadline - datetime.now(timezone.utc)).total_seconds())
                except (KeyError, TypeError, ValueError, OverflowError):
                    pass
        print(f"模型请求中断，{delay}s 后重试", flush=True)
        if clock:
            clock.check()
            delay = min(delay, max(0, 2 * clock.limit - clock.wall))
        sleep_started = time.monotonic()
        time.sleep(delay)
        if clock:
            clock.add_infrastructure_delay(time.monotonic() - sleep_started)
    assert last_error is not None
    raise last_error


def _post_with_deadline(url: str, timeout: float, trust_env: bool, kwargs: dict):
    """Enforce a total request deadline with a killable subprocess.

    Credentials travel over stdin, not command arguments or on-disk files.
    A timed-out remote request may still have been processed or billed.
    """
    import base64
    import subprocess
    import sys
    import httpx

    request = httpx.Request('POST', url)
    data = json.dumps({'url': url, 'timeout': timeout, 'trust_env': trust_env, 'kwargs': kwargs})
    try:
        result = subprocess.run([sys.executable, '-m', 'harness.http_deadline_worker'], input=data,
                                text=True, capture_output=True, timeout=timeout,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=False)
    except subprocess.TimeoutExpired:
        raise httpx.ReadTimeout('模型请求超过总时限', request=request) from None
    if result.returncode:
        raise RuntimeError('模型请求工作进程异常退出')
    try:
        payload = json.loads(result.stdout)
        if 'transport_error' in payload:
            error_type = getattr(httpx, payload['transport_error'], httpx.TransportError)
            if not isinstance(error_type, type) or not issubclass(error_type, httpx.TransportError):
                error_type = httpx.TransportError
            raise error_type('模型请求传输失败', request=request)
        return httpx.Response(payload['status'], headers=payload['headers'],
                              content=base64.b64decode(payload['body'], validate=True), request=request)
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('模型请求工作进程响应无效') from exc


def _request_log(path: Path | None, event: dict) -> None:
    if path is not None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


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
        payload = {"role": message["role"], "content": content}
    else:
        parts = []
        for part in content:
            if part.get("type") == "text":
                parts.append({"type": "text", "text": part.get("text") or ""})
            elif part.get("type") == "image_path":
                encoded = _data_url(part.get("path") or "")
                if encoded:
                    parts.append({"type": "image_url", "image_url": {"url": encoded}})
        payload = {"role": message["role"], "content": parts or ""}
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning:
        payload["reasoning_content"] = reasoning
    return payload


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
