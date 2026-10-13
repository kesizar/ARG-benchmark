"""Host allow-list, shortcut blocks, and guide-site blocks."""

from __future__ import annotations

import fnmatch
import re
from urllib.parse import parse_qs, urlparse

GUIDE_HOSTS = [
    "*.bilibili.com",
    "www.youtube.com",
    "zhuanlan.zhihu.com",
    "www.reddit.com",
    "walkthrough*",
    "*walkthrough*",
    "*spoiler*",
    "*solution*",
    "*guide*",
]


def _host(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or "").lower()


def _netloc(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_loose_scheme(url: str) -> bool:
    lowered = url.lower()
    return lowered.startswith(("data:", "blob:", "about:"))


def host_allowed(url: str, allow_hosts: list[str]) -> bool:
    if is_loose_scheme(url):
        return True
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = _host(url)
    netloc = _netloc(url)
    for rule in allow_hosts:
        token = rule.strip().lower()
        if not token:
            continue
        if token.startswith("*."):
            base = token[2:]
            if host == base or host.endswith("." + base):
                return True
            continue
        if token in {host, netloc}:
            return True
    return False


def shortcut_hit(url: str, rules: list[dict] | None) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for rule in rules or []:
        kind = rule.get("type")
        if kind == "url_param" and rule.get("name") in query:
            return str(rule.get("label") or rule.get("name"))
        if kind == "url_regex" and rule.get("pattern") and re.search(str(rule["pattern"]), url):
            return str(rule.get("label") or rule["pattern"])
    return None


def guide_hit(url: str, patterns: list[str] | None) -> str | None:
    host = _host(url)
    netloc = _netloc(url)
    haystacks = [host, netloc, url.lower()]
    for pattern in patterns or []:
        token = pattern.strip().lower()
        if not token:
            continue
        for hay in haystacks:
            if fnmatch.fnmatch(hay, token):
                return pattern
    return None


def block_reason(url: str, cfg: dict) -> tuple[str, str] | None:
    """Return (why, rule) when the request must be aborted."""
    if is_loose_scheme(url):
        return None
    shortcut = shortcut_hit(url, cfg.get("shortcut_block"))
    if shortcut:
        return ("shortcut", shortcut)
    guide = guide_hit(url, cfg.get("guide_block_hosts"))
    if guide:
        return ("guide", guide)
    if not host_allowed(url, cfg.get("allow_hosts") or []):
        return ("host", _netloc(url) or url)
    return None


def goto_permitted(url: str, cfg: dict) -> bool:
    if not cfg.get("allow_model_goto"):
        return False
    scope = cfg.get("goto_scope") or "none"
    if scope == "none":
        return False
    if block_reason(url, cfg):
        return False
    if scope == "allow_hosts":
        return host_allowed(url, cfg.get("allow_hosts") or [])
    if scope == "same_host":
        entry = cfg.get("entry_url") or ""
        return _netloc(url) == _netloc(entry) and host_allowed(url, cfg.get("allow_hosts") or [])
    return False
