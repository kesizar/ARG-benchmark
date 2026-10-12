"""Ask a model for one browser action. The page observation is the only source."""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SYSTEM = """你在本机浏览器里玩一个已经打开的展览解谜网页。
把这局里能推进的调查做下去，找出隐藏的真相。
只能根据当前观察、上一张截图和所附回看行动。不要访问站外网站，不要猜测观察里没有的控件。
需要填写或判断的内容，要根据页面文字、图片和其他可见线索推理后再行动。
如果一处已经推不下去，就离开这一处，改查还没看过的页面、链接或对话。不要为此结束。

每一步只输出一个 JSON 对象，不要输出 Markdown。

动作：
{"tool":"click","control_id":"c1"}
{"tool":"type","control_id":"c2","text":"要输入的文字","submit":false}
{"tool":"drag","tile_id":"t0","mode":"move","dx":40,"dy":-20}
{"tool":"drag","tile_id":"t0","mode":"zoom","dx":0,"dy":-80}
{"tool":"drag","tile_id":"t0","mode":"rotate","dx":60,"dy":0}
{"tool":"scroll","dy":400}
{"tool":"back"}
{"tool":"goto","url":"/live/index.html"}
{"tool":"recall","id":"p1"}
{"tool":"done","note":"为什么整局无法再推进"}

每次观察都附有调查笔记。索引记录去过的页面、还没打开的链接、还可以填写的输入、见过但未使用的按钮，以及每次提交后画面有没有前进。编号可以回看。
判断由你重写，没写就保留上一次：
- "approach":"眼下卡在哪一题、正在验证哪条线、下一步打算查什么"
- "theory":"对人物、矛盾和真相的猜想，包括还没证实的假设"

规则：
- control_id 和 tile_id 必须来自当前观察。
- recall 的 id 必须来自调查笔记。
- 面包屑拼图：move 按住图片平移；zoom 按住缩放钮再拖，dy 为负会放大；rotate 按住旋转钮再拖。
- 输入后如果要提交，把 submit 设为 true。
- done 会立刻结束整局调查，后面不能再行动。只有整局确实无法再推进时才用。放弃眼前这一题时，去打开还没看过的内容，不要用 done。
"""


def load_env(repo: Path) -> None:
    for path in (repo / ".env",):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def credentials() -> tuple[str, str, str]:
    key = os.environ.get("AGENT_API_KEY") or os.environ.get("JUDGE_API_KEY") or ""
    base = os.environ.get("AGENT_BASE_URL") or os.environ.get("JUDGE_BASE_URL") or ""
    model = os.environ.get("AGENT_MODEL") or os.environ.get("JUDGE_MODEL") or ""
    if not key or not base or not model:
        raise RuntimeError("缺少 AGENT_API_KEY、AGENT_BASE_URL、AGENT_MODEL。可放在仓库根目录的 .env。")
    return key, base, model


PARSE = """你只负责把玩家的回复整理成一个浏览器动作。不要改它的意图，不要补充它没写的操作。
只输出一个 JSON 对象，不要 Markdown。

tool 只能是 click、type、drag、scroll、back、goto、recall、done。
{"tool":"click","control_id":"c1"}
{"tool":"type","control_id":"c2","text":"要输入的文字","submit":false}
{"tool":"drag","tile_id":"t0","mode":"move","dx":40,"dy":-20}
{"tool":"scroll","dy":400}
{"tool":"back"}
{"tool":"goto","url":"/live/index.html"}
{"tool":"recall","id":"p1"}
{"tool":"done","note":"为什么整局无法再推进"}

如果动作被包在 tool、action 或其他字段里，展开成上面这一层。mode 只能是 move、zoom、rotate。
玩家原文里有 approach 或 theory 时原样保留，没有就不要添加，也不要改写成 journal。
"""


def _action_from_text(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError("解析模型没有返回 JSON")
    data, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(data, dict):
        raise ValueError("解析结果必须是对象")
    tool = str(data.get("tool") or "")
    allowed = {"click", "type", "drag", "scroll", "back", "goto", "recall", "done"}
    if tool not in allowed:
        raise ValueError(f"未知动作 {tool}")
    action: dict[str, Any] = {"tool": tool}
    if tool == "click":
        action["control_id"] = str(data.get("control_id") or "")
    elif tool == "type":
        action["control_id"] = str(data.get("control_id") or "")
        action["text"] = str(data.get("text") or "")
        action["submit"] = bool(data.get("submit"))
    elif tool == "drag":
        action["tile_id"] = str(data.get("tile_id") or "")
        action["mode"] = str(data.get("mode") or "move")
        action["dx"] = float(data.get("dx") or 0)
        action["dy"] = float(data.get("dy") or 0)
    elif tool == "scroll":
        action["dy"] = float(data.get("dy") or 400)
    elif tool == "goto":
        action["url"] = str(data.get("url") or "/live/index.html")
    elif tool == "recall":
        action["id"] = str(data.get("id") or "")
    elif tool == "done":
        action["note"] = str(data.get("note") or "")
    approach = str(data.get("approach") or "").strip()
    if approach:
        action["approach"] = approach[:2000]
    theory = str(data.get("theory") or "").strip()
    if theory:
        action["theory"] = theory[:2000]
    return action


def parse_action(raw: str) -> dict[str, Any]:
    last_error = ""
    prompt = raw
    for _ in range(2):
        parsed = _complete(PARSE, prompt, parse=True)
        try:
            return _action_from_text(parsed)
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            prompt = f"上一次整理失败：{last_error}\n请只输出一个规定格式的 JSON。\n玩家原文：\n{raw}"
    raise ValueError(last_error or "无法解析动作")


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content") or ""
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(str(part.get("text") or ""))
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(content)


def _image_part(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}}


def _user_content(
    observation: dict[str, Any],
    history: list[dict[str, Any]],
    images: str = "all",
) -> str | list[dict[str, Any]]:
    recall = observation.get("recall") if isinstance(observation.get("recall"), dict) else None
    hidden = {"screenshot", "previous_screenshot", "recall"}
    visible = {key: value for key, value in observation.items() if key not in hidden}
    if recall:
        visible["recall"] = {"id": recall.get("id") or "", "summary": recall.get("summary") or ""}
    text = json.dumps({"observation": visible, "history": history[-8:]}, ensure_ascii=False)
    if images == "none":
        return text
    parts: list[dict[str, Any]] = []
    if images == "all":
        previous = _image_part(Path(str(observation.get("previous_screenshot") or "")))
        if previous:
            parts.append({"type": "text", "text": "上一张："})
            parts.append(previous)
    current = _image_part(Path(str(observation.get("screenshot") or "")))
    if current:
        parts.append({"type": "text", "text": "当前："})
        parts.append(current)
    if images == "all" and recall:
        remembered = _image_part(Path(str(recall.get("screenshot") or "")))
        if remembered:
            parts.append({"type": "text", "text": f"回看 {recall.get('id') or ''}："})
            parts.append(remembered)
    if not parts:
        return text
    parts.append({"type": "text", "text": text})
    return parts


def _endpoint(parse: bool) -> tuple[str, str, str]:
    if parse:
        key = os.environ.get("AGENT_PARSE_API_KEY") or ""
        base = os.environ.get("AGENT_PARSE_BASE_URL") or ""
        model = os.environ.get("AGENT_PARSE_MODEL") or ""
        if key and base and model:
            return key, base, model
    return credentials()


def _answer_from_chunk(chunk: dict[str, Any]) -> str:
    error = chunk.get("error")
    if error:
        raise RuntimeError(f"模型请求失败: {str(error)[:300]}")
    choices = chunk.get("choices") or []
    if not choices:
        return ""
    delta = choices[0].get("delta") or {}
    piece = delta.get("content")
    return str(piece) if piece else ""


def _read_completion(response, streamed: bool) -> str:
    if not streamed:
        body = json.loads(response.read().decode("utf-8"))
        return _message_text((body.get("choices") or [{}])[0].get("message") or {})
    answer: list[str] = []
    leftover: list[str] = []
    saw_event = False
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        if not line.startswith("data:"):
            leftover.append(line)
            continue
        saw_event = True
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(chunk, dict):
            answer.append(_answer_from_chunk(chunk))
    if saw_event:
        text = "".join(answer).strip()
        if not text:
            raise ConnectionError("流式响应没有正文")
        return text
    body = json.loads("".join(leftover))
    return _message_text((body.get("choices") or [{}])[0].get("message") or {})


def _complete(
    system: str,
    content: str | list[dict[str, Any]],
    model: str | None = None,
    parse: bool = False,
    stream: bool = False,
) -> str:
    key, base, default_model = _endpoint(parse)
    payload: dict[str, Any] = {
        "model": model or default_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
    }
    if stream:
        payload["stream"] = True
    if "maas.aliyuncs.com" in base:
        payload["temperature"] = 0
        if "kimi" not in str(payload["model"]):
            payload["enable_thinking"] = False
    elif "moonshot." in base:
        payload["reasoning_effort"] = "low"
    elif not ("dashscope.aliyuncs.com" in base and "kimi" in str(payload["model"])):
        payload["temperature"] = 0
    request = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "ARG-benchmark/1.0",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=None) as response:
                return _read_completion(response, stream)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"模型请求失败 HTTP {exc.code}: {detail}") from exc
        except (TimeoutError, urllib.error.URLError, ConnectionError) as exc:
            last_error = exc
            if attempt < 2:
                print(f"连接中断，5 秒后重试（{attempt + 1}/3）", flush=True)
                time.sleep(5)
    raise RuntimeError(f"模型连接中断: {last_error}") from last_error


def choose_action(observation: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        raw = _complete(SYSTEM, _user_content(observation, history, images="all"), stream=True)
    except RuntimeError as exc:
        if "HTTP 400" not in str(exc):
            raise
        try:
            raw = _complete(SYSTEM, _user_content(observation, history, images="current"), stream=True)
        except RuntimeError as nested:
            if "HTTP 400" not in str(nested):
                raise
            raw = _complete(SYSTEM, _user_content(observation, history, images="none"), stream=True)
    return parse_action(raw)
