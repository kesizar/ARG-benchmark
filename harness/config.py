"""Load a task config and apply the observation-mode table."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import urlparse

from harness.network import host_allowed

log = logging.getLogger("harness")

OBS_TABLE = {
    "A": {"obs_screenshot": False, "obs_text": True, "obs_elements": True},
    "B": {"obs_screenshot": True, "obs_text": True, "obs_elements": True},
    "C": {"obs_screenshot": True, "obs_text": False, "obs_elements": False},
}

DEFAULT_ACTIONS = [
    "click",
    "dblclick",
    "type",
    "key",
    "scroll",
    "drag",
    "back",
    "switch_tab",
    "close_tab",
    "wait",
    "dialog",
    "give_up",
    "note",
]


def repo_root_from(start: Path | None = None) -> Path:
    cursor = (start or Path.cwd()).resolve()
    for candidate in [cursor, *cursor.parents]:
        if (candidate / "configs").is_dir() and (candidate / "harness").is_dir():
            return candidate
    return cursor


def apply_obs_mode(cfg: dict) -> dict:
    mode = str(cfg.get("obs_mode") or "B")
    if mode not in OBS_TABLE:
        raise ValueError(f"obs_mode 只能是 A、B 或 C，收到 {mode}")
    cfg["obs_mode"] = mode
    for key, forced in OBS_TABLE[mode].items():
        if key in cfg and bool(cfg[key]) != forced:
            log.warning("obs_mode %s 覆盖了 %s=%s", mode, key, cfg[key])
        cfg[key] = forced
    return cfg


def apply_defaults(cfg: dict) -> dict:
    cfg.setdefault("computer_use", False)
    cfg.setdefault("allow_model_goto", False)
    cfg.setdefault("goto_scope", "none")
    cfg.setdefault("show_url", True)
    cfg.setdefault("text_scope", "page")
    cfg.setdefault("text_limit", 6000)
    cfg.setdefault("settle_ms", 1200)
    cfg.setdefault("shortcut_block", [])
    cfg.setdefault("guide_block_hosts", [])
    cfg.setdefault("allow_hosts", [])
    cfg.setdefault("notes_for_report", [])
    cfg.setdefault("actions_enabled", list(DEFAULT_ACTIONS))
    if not isinstance(cfg.get("notebook"), dict):
        cfg["notebook"] = {}
    cfg["notebook"].setdefault("enabled", False)
    cfg["notebook"].setdefault("max_chars", 4000)
    actions = [str(item) for item in cfg.get("actions_enabled") or []]
    if cfg["notebook"]["enabled"]:
        if "note" not in actions:
            actions.append("note")
    else:
        actions = [item for item in actions if item != "note"]
    cfg["actions_enabled"] = actions
    cfg.setdefault("viewport", {"width": 1366, "height": 900})
    cfg.setdefault("locale", "zh-CN")
    cfg.setdefault("timezone", "Asia/Shanghai")
    cfg.setdefault("seed", 20261012)
    cfg.setdefault("limits", {})
    limits = cfg["limits"]
    limits.setdefault("max_steps", 80)
    limits.setdefault("max_seconds", 1800)
    limits.setdefault("max_answer_submits", 20)
    cfg.setdefault("history", {})
    history = cfg["history"]
    history.setdefault("full_obs_k", 4)
    history.setdefault("screenshot_k", 2)
    window = int(history["full_obs_k"])
    if window < 3 or window > 5:
        raise ValueError("history.full_obs_k 必须在 3 到 5 之间")
    if cfg.get("category") == "arg" and cfg.get("arg_layer") not in {"L1", "L2", "L3"}:
        raise ValueError("ARG 任务必须标明 arg_layer 为 L1、L2 或 L3")
    if cfg.get("category") != "arg" and cfg.get("arg_layer") not in {None, "null"}:
        if "arg_layer" in cfg and cfg["arg_layer"] is not None:
            raise ValueError("非 ARG 任务的 arg_layer 必须为 null")
    return cfg


def load_config(path: Path, obs_mode: str | None = None) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    if obs_mode:
        cfg["obs_mode"] = obs_mode
    apply_defaults(cfg)
    apply_obs_mode(cfg)
    return cfg


def load_exclude(root: Path) -> list[str]:
    path = root / "exclude" / "sites.txt"
    if not path.is_file():
        return ["ae27ff"]
    tokens = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            tokens.append(line.lower())
    if "ae27ff" not in tokens:
        tokens.append("ae27ff")
    return tokens


def exclusion_hit(cfg: dict, tokens: list[str]) -> str | None:
    blob = " ".join(
        [
            str(cfg.get("id") or ""),
            str(cfg.get("entry_url") or ""),
            " ".join(cfg.get("allow_hosts") or []),
        ]
    ).lower()
    for token in tokens:
        if token and token in blob:
            return token
    return None


def entry_allowed(cfg: dict) -> bool:
    entry = cfg.get("entry_url")
    if not entry:
        return True
    if urlparse(entry).scheme not in {"http", "https"}:
        return False
    return host_allowed(entry, cfg.get("allow_hosts") or [])
