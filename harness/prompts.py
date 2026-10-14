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
        f"你是玩家。作品：{title}",
        intro,
        "",
        "每一步只输出一个 JSON 对象，用 op 表示动作。可以在 JSON 前写很短的思考，程序只采用最后一个 JSON。",
        "可用动作：" + json.dumps(actions, ensure_ascii=False),
        "示例：" + "  ".join(_examples(cfg)),
        "",
        "只使用上面列出的动作。按键不能是组合键。预算见每步观察里的 steps_left 与 seconds_left。",
        "只根据屏幕上能看到的信息推理。",
    ]
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
    if category in {"text_adventure", "static"}:
        return ['{"op":"type","text":"look","enter":true}', '{"op":"give_up"}']
    if mode == "A":
        return [
            '{"op":"click","n":0}',
            '{"op":"type","n":1,"text":"测试","enter":true}',
            '{"op":"drag","x1":10,"y1":10,"x2":40,"y2":40}',
            *shared,
        ]
    if mode == "C":
        return [
            '{"op":"click","x":100,"y":200}',
            '{"op":"type","text":"测试","enter":true}',
            '{"op":"drag","x1":10,"y1":10,"x2":40,"y2":40}',
            *shared,
        ]
    return [
        '{"op":"click","n":0}',
        '{"op":"click","x":100,"y":200}',
        '{"op":"type","n":1,"text":"测试","enter":true}',
        '{"op":"drag","x1":10,"y1":10,"x2":40,"y2":40}',
        *shared,
    ]


def history_message(turn: dict[str, Any], *, full: bool, with_image: bool) -> dict[str, Any]:
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
    action = turn.get("action")
    if not action:
        return None
    return {"role": "assistant", "content": json.dumps(action, ensure_ascii=False)}
