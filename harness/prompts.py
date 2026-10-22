"""Model-facing prompt text built only from model_visible and the action list."""

from __future__ import annotations

import json
from typing import Any


def model_prompt(cfg: dict) -> str:
    visible = cfg.get("model_visible") or {}
    title = str(visible.get("title") or cfg.get("id") or "未命名作品")
    intro = str(visible.get("intro") or "只能根据当前能看到的信息行动。")
    actions = cfg.get("actions_enabled") or []
    lines = [
        f"你是玩家。你正在玩解谜作品「{title}」。",
        "目标是只根据屏幕上能看到的信息，把这个作品推进到结局。",
        intro,
        "",
        "你写下的整段回复都会保留，之后每一步都会再看到。可以把这一局的进程、思路和假设写在回复里。",
        f"最近 {int((cfg.get('history') or {}).get('full_obs_k') or 4)} 步会附上较完整的画面和你做过的动作。更早的步骤保留当时的整段回复，以及动作和结果。",
        "",
        "每一步只输出一个 JSON 对象，用 op 表示动作。可以在 JSON 前写下思考，程序只执行最后一个 JSON。",
        "可用动作：" + json.dumps(actions, ensure_ascii=False),
        "示例：" + "  ".join(_examples(cfg)),
        "",
        "只使用上面列出的动作。按键不能是组合键。预算见每步观察里的 steps_left 与 seconds_left。",
        "只根据屏幕上能看到的信息推理。",
    ]
    if "note" in actions:
        lines.append(
            '你有一本笔记。可以把这一局的进程、思路和假设写进去。用 {"op":"note","text":"..."} 替换整篇内容。写下来的内容以后每一步都会给你看。'
        )
    if "call" in actions:
        lines.append(
            '查看或使用场景里的东西用 {"op":"call","name":"investigate","object":{"node_id":"..."}}。name 还可以是 tool 或 use_item。tool 的 object 里加 arguments。'
        )
    if cfg.get("grid"):
        lines.append("这是棋盘游戏。用方向键移动，方向键名是 ArrowUp、ArrowDown、ArrowLeft、ArrowRight。")
    if "submit_answer" in actions:
        lines.append('需要提交答案时用 {"op":"submit_answer","text":"..."}。你会看到「正确」或「不正确」。')
    if "submit_conclusion" in actions:
        lines.append('需要提交结论时用 {"op":"submit_conclusion","object":{...}}。你会看到「已记录」。')
    return "\n".join(lines)


def _examples(cfg: dict) -> list[str]:
    category = cfg.get("category")
    mode = cfg.get("obs_mode") or "B"
    shared = [
        '{"op":"key","key":"Enter"}',
        '{"op":"scroll","dir":"down"}',
        '{"op":"wait","ms":1000}',
        '{"op":"back"}',
        '{"op":"dialog","accept":true}',
        '{"op":"give_up"}',
    ]
    if cfg.get("grid"):
        examples = [
            '{"op":"key","key":"ArrowUp"}',
            '{"op":"key","key":"ArrowLeft"}',
            '{"op":"give_up"}',
        ]
    elif "call" in (cfg.get("actions_enabled") or []):
        examples = [
            '{"op":"call","name":"investigate","object":{"node_id":"..."}}',
            '{"op":"call","name":"tool","object":{"node_id":"...","arguments":{}}}',
            '{"op":"give_up"}',
        ]
    elif category in {"text_adventure", "static"}:
        examples = ['{"op":"type","text":"look","enter":true}', '{"op":"give_up"}']
    elif mode == "A":
        examples = [
            '{"op":"click","n":0}',
            '{"op":"type","n":1,"text":"测试","enter":true}',
            '{"op":"drag","x1":10,"y1":10,"x2":40,"y2":40}',
            *shared,
        ]
    elif mode == "C":
        examples = [
            '{"op":"click","x":100,"y":200}',
            '{"op":"type","text":"测试","enter":true}',
            '{"op":"drag","x1":10,"y1":10,"x2":40,"y2":40}',
            *shared,
        ]
    else:
        examples = [
            '{"op":"click","n":0}',
            '{"op":"click","x":100,"y":200}',
            '{"op":"type","n":1,"text":"测试","enter":true}',
            '{"op":"drag","x1":10,"y1":10,"x2":40,"y2":40}',
            *shared,
        ]
    if "note" in (cfg.get("actions_enabled") or []):
        examples.append('{"op":"note","text":"..."}')
    return examples


def history_message(turn: dict[str, Any], *, full: bool, with_image: bool, include_notebook: bool = False) -> dict[str, Any]:
    obs = turn.get("obs") or {}
    if full:
        payload = {
            "url": obs.get("url"),
            "tabs": obs.get("tabs"),
            "visible_text": obs.get("visible_text"),
            "elements": obs.get("elements"),
            "dialogs": obs.get("dialogs"),
            "pending_dialog": obs.get("pending_dialog"),
            "last_result": obs.get("last_result"),
            "budget": obs.get("budget"),
        }
        if "turn" in obs:
            payload["turn"] = obs.get("turn")
        if turn.get("action"):
            payload["action"] = turn.get("action")
            payload["result"] = turn.get("result")
        if include_notebook and "notebook" in obs:
            payload["notebook"] = obs.get("notebook") or ""
    else:
        payload = {
            "url": obs.get("url") or turn.get("url"),
            "title": turn.get("title") or "",
            "action": turn.get("action"),
            "result": turn.get("result"),
        }
    content: list[dict[str, Any]] = [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]
    screenshot = obs.get("screenshot")
    if full and with_image and screenshot:
        content.append({"type": "image_path", "path": screenshot})
    return {"role": "user", "content": content}


def assistant_message(turn: dict[str, Any]) -> dict[str, Any] | None:
    reply = turn.get("reply")
    if isinstance(reply, str) and reply.strip():
        content = reply
    else:
        action = turn.get("action")
        if not action:
            return None
        content = json.dumps(action, ensure_ascii=False)
    message: dict[str, Any] = {"role": "assistant", "content": content}
    reasoning = turn.get("reasoning")
    if isinstance(reasoning, str) and reasoning:
        message["reasoning_content"] = reasoning
    return message
