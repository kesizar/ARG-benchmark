"""Validate one action object. Only the last JSON object in a model reply is used."""

from __future__ import annotations

import json
import re
from typing import Any

from harness.network import goto_permitted

ALLOWED_KEYS = {
    "Enter",
    "Escape",
    "Tab",
    "Backspace",
    "Delete",
    "Space",
    "ArrowUp",
    "ArrowDown",
    "ArrowLeft",
    "ArrowRight",
    "PageUp",
    "PageDown",
    "Home",
    "End",
}

FORMAT_ERROR = "动作格式错误"


def last_json_object(text: str) -> dict[str, Any]:
    raw = text or ""
    decoder = json.JSONDecoder()
    found: dict[str, Any] | None = None
    index = 0
    while True:
        start = raw.find("{", index)
        if start < 0:
            break
        try:
            value, end = decoder.raw_decode(raw[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(value, dict):
            found = value
        index = start + max(end, 1)
    if found is None:
        raise ValueError(FORMAT_ERROR)
    return found


def from_legacy(action: dict[str, Any]) -> dict[str, Any]:
    """Map the old mirror/harness tool names onto op. recall is not a model action."""
    tool = str(action.get("tool") or "")
    if tool == "click":
        return {"op": "click", "n": _control_index(action.get("control_id"))}
    if tool == "type":
        mapped: dict[str, Any] = {
            "op": "type",
            "n": _control_index(action.get("control_id")),
            "text": action.get("text") or "",
            "enter": bool(action.get("submit")),
        }
        return mapped
    if tool == "drag":
        if "x1" in action:
            return {
                "op": "drag",
                "x1": action.get("x1"),
                "y1": action.get("y1"),
                "x2": action.get("x2"),
                "y2": action.get("y2"),
            }
        return {"op": "drag"}
    if tool == "scroll":
        mapped = {"op": "scroll"}
        if "dir" in action:
            mapped["dir"] = action["dir"]
        if "dy" in action:
            mapped["dy"] = action["dy"]
        if "dx" in action:
            mapped["dx"] = action["dx"]
        return mapped
    if tool == "back":
        return {"op": "back"}
    if tool == "goto":
        return {"op": "goto", "url": action.get("url") or ""}
    if tool == "done":
        return {"op": "give_up"}
    if tool == "recall":
        return {"op": "recall"}
    return {"op": tool}


def _control_index(control_id: Any) -> int:
    match = re.fullmatch(r"c(\d+)", str(control_id or ""))
    if not match:
        return -1
    return int(match.group(1)) - 1


def parse_model_action(text: str) -> dict[str, Any]:
    data = last_json_object(text)
    if "op" not in data and "tool" in data:
        return from_legacy(data)
    return data


def key_allowed(key: str) -> bool:
    if key in ALLOWED_KEYS:
        return True
    return len(key) == 1 and key in "abcdefghijklmnopqrstuvwxyz0123456789"


def normalize(action: dict[str, Any], cfg: dict) -> tuple[dict[str, Any] | None, str | None]:
    """Return (action, None) or (None, short Chinese result)."""
    if "op" not in action and "tool" in action:
        action = from_legacy(action)
    op = action.get("op")
    if not isinstance(op, str) or not op:
        return None, FORMAT_ERROR
    enabled = set(cfg.get("actions_enabled") or [])
    if op not in enabled:
        return None, "动作未启用"
    try:
        cleaned = _clean(op, action, cfg)
    except PermissionError:
        return None, "已拒绝打开该地址"
    except (ValueError, KeyError, TypeError):
        return None, FORMAT_ERROR
    return cleaned, None


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(FORMAT_ERROR)
    return float(value)


def _clean(op: str, action: dict[str, Any], cfg: dict) -> dict[str, Any]:
    mode = cfg.get("obs_mode")
    if op in {"click", "dblclick", "hover", "long_press"}:
        return _pointer(op, action, mode)
    if op == "drag":
        return {
            "op": "drag",
            "x1": _number(action["x1"]),
            "y1": _number(action["y1"]),
            "x2": _number(action["x2"]),
            "y2": _number(action["y2"]),
        }
    if op == "type":
        text = str(action.get("text") or "")
        if len(text) > 200:
            raise ValueError(FORMAT_ERROR)
        cleaned: dict[str, Any] = {"op": "type", "text": text, "clear": bool(action.get("clear")), "enter": bool(action.get("enter"))}
        if "n" in action and action["n"] is not None:
            cleaned["n"] = int(action["n"])
        elif mode == "A" and cfg.get("category") not in {"text_adventure", "static"}:
            raise ValueError(FORMAT_ERROR)
        return cleaned
    if op == "key":
        key = str(action.get("key") or "")
        if any(token in key for token in ("+", "Control", "Alt", "Meta", "Shift", "Ctrl")):
            raise ValueError(FORMAT_ERROR)
        if not key_allowed(key):
            raise ValueError(FORMAT_ERROR)
        return {"op": "key", "key": key}
    if op == "scroll":
        cleaned = {"op": "scroll"}
        if action.get("dir"):
            if action["dir"] not in {"up", "down", "left", "right"}:
                raise ValueError(FORMAT_ERROR)
            cleaned["dir"] = action["dir"]
        if "dx" in action or "dy" in action:
            cleaned["dx"] = _number(action.get("dx") or 0)
            cleaned["dy"] = _number(action.get("dy") or 0)
        if "dir" not in cleaned and "dx" not in cleaned:
            raise ValueError(FORMAT_ERROR)
        if "x" in action and "y" in action:
            cleaned["x"] = _number(action["x"])
            cleaned["y"] = _number(action["y"])
        return cleaned
    if op == "wait":
        ms = int(action.get("ms") or 0)
        if ms < 0 or ms > 10000:
            raise ValueError(FORMAT_ERROR)
        return {"op": "wait", "ms": ms}
    if op == "dialog":
        cleaned = {"op": "dialog", "accept": bool(action.get("accept", True))}
        if "text" in action:
            cleaned["text"] = str(action.get("text") or "")[:200]
        return cleaned
    if op in {"back", "give_up"}:
        return {"op": op}
    if op in {"switch_tab", "close_tab"}:
        return {"op": op, "i": int(action["i"])}
    if op == "goto":
        url = str(action.get("url") or "")
        if not goto_permitted(url, cfg):
            raise PermissionError(url)
        return {"op": "goto", "url": url}
    if op == "submit_answer":
        return {"op": "submit_answer", "text": str(action.get("text") or "")}
    if op == "submit_conclusion":
        payload = action.get("object", action.get("conclusion"))
        if not isinstance(payload, dict):
            raise ValueError(FORMAT_ERROR)
        return {"op": "submit_conclusion", "object": payload}
    raise ValueError(FORMAT_ERROR)


def _pointer(op: str, action: dict[str, Any], mode: str | None) -> dict[str, Any]:
    has_n = "n" in action and action["n"] is not None
    has_xy = "x" in action and "y" in action
    if mode == "C":
        if not has_xy or has_n:
            raise ValueError(FORMAT_ERROR)
        cleaned: dict[str, Any] = {"op": op, "x": _number(action["x"]), "y": _number(action["y"])}
    elif mode == "A":
        if not has_n:
            raise ValueError(FORMAT_ERROR)
        cleaned = {"op": op, "n": int(action["n"])}
    elif has_n:
        cleaned = {"op": op, "n": int(action["n"])}
    elif has_xy:
        cleaned = {"op": op, "x": _number(action["x"]), "y": _number(action["y"])}
    else:
        raise ValueError(FORMAT_ERROR)
    if op == "long_press":
        ms = int(action.get("ms") or 0)
        if ms < 0 or ms > 3000:
            raise ValueError(FORMAT_ERROR)
        cleaned["ms"] = ms
    return cleaned
