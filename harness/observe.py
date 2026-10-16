"""Build the three observation modes. Judge state never enters this payload."""

from __future__ import annotations

import hashlib
from typing import Any

TEXT_JS = r"""
({limit, scope}) => {
  const skip = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE"]);
  const viewW = window.innerWidth;
  const viewH = window.innerHeight;
  const clipRe = /rect\(\s*0(?:px)?[\s,]+0(?:px)?[\s,]+0(?:px)?[\s,]+0(?:px)?\s*\)/i;
  function ancestorHidden(el) {
    let node = el;
    while (node && node.nodeType === 1) {
      if (skip.has(node.tagName) || node.hidden) return true;
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden") return true;
      if (Number.parseFloat(style.opacity) === 0) return true;
      const left = Number.parseFloat(style.left);
      if ((style.position === "absolute" || style.position === "fixed") && Number.isFinite(left) && left <= -9999) return true;
      if (clipRe.test(style.clip || "")) return true;
      const overflow = style.overflow + style.overflowX + style.overflowY;
      if (overflow.includes("hidden")) {
        const rect = node.getBoundingClientRect();
        if (rect.width <= 2 && rect.height <= 2) return true;
      }
      node = node.parentElement;
    }
    return false;
  }
  function tiny(el) {
    const font = Number.parseFloat(getComputedStyle(el).fontSize);
    return Number.isFinite(font) && font < 4;
  }
  function inView(el) {
    const rect = el.getBoundingClientRect();
    return rect.bottom > 0 && rect.right > 0 && rect.top < viewH && rect.left < viewW;
  }
  const parts = [];
  const root = document.body || document.documentElement;
  if (!root) return "";
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const parent = node.parentElement;
    if (!parent || ancestorHidden(parent) || tiny(parent)) continue;
    if (scope === "viewport" && !inView(parent)) continue;
    const text = node.textContent.replace(/\s+/g, " ").trim();
    if (!text) continue;
    parts.push(text);
    if (parts.join("\n").length >= limit) break;
  }
  return parts.join("\n").slice(0, limit);
}
"""

ELEMENTS_JS = r"""
() => {
  const skip = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE"]);
  const viewW = window.innerWidth;
  const viewH = window.innerHeight;
  const clipRe = /rect\(\s*0(?:px)?[\s,]+0(?:px)?[\s,]+0(?:px)?[\s,]+0(?:px)?\s*\)/i;
  function ancestorHidden(el) {
    let node = el;
    while (node && node.nodeType === 1) {
      if (skip.has(node.tagName) || node.hidden) return true;
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden") return true;
      if (Number.parseFloat(style.opacity) === 0) return true;
      const left = Number.parseFloat(style.left);
      if ((style.position === "absolute" || style.position === "fixed") && Number.isFinite(left) && left <= -9999) return true;
      if (clipRe.test(style.clip || "")) return true;
      const overflow = style.overflow + style.overflowX + style.overflowY;
      if (overflow.includes("hidden")) {
        const rect = node.getBoundingClientRect();
        if (rect.width <= 2 && rect.height <= 2) return true;
      }
      node = node.parentElement;
    }
    return false;
  }
  const selector = [
    "a", "button", "input", "textarea", "select", "summary",
    "canvas", "label", "[contenteditable='true']", "[onclick]",
    "[role='button']", "[role='link']", "[role='tab']", "[role='checkbox']",
    "[role='radio']", "[role='switch']", "[role='menuitem']",
    "div", "span", "li", "img", "td"
  ].join(",");
  const roles = new Set(["button", "link", "tab", "checkbox", "radio", "switch", "menuitem"]);
  function clickable(node) {
    if (node.matches("a, button, input, textarea, select, summary, canvas, label, [contenteditable='true'], [onclick]")) return true;
    const role = (node.getAttribute("role") || "").toLowerCase();
    if (roles.has(role)) return true;
    const tag = node.tagName;
    if (!["DIV", "SPAN", "LI", "IMG", "TD"].includes(tag)) return false;
    if (node.hasAttribute("onclick")) return true;
    if (getComputedStyle(node).cursor !== "pointer") return false;
    const rect = node.getBoundingClientRect();
    if (rect.width > viewW * 0.7 && rect.height > viewH * 0.7) return false;
    return true;
  }
  const nodes = [];
  for (const node of document.querySelectorAll(selector)) {
    if (!clickable(node) || ancestorHidden(node)) continue;
    nodes.push(node);
  }
  const chosen = nodes.filter((node) => !nodes.some((other) => other !== node && node.contains(other)));
  const out = [];
  let n = 0;
  for (const node of chosen) {
    const rect = node.getBoundingClientRect();
    if (rect.width < 2 || rect.height < 2) continue;
    if (rect.bottom <= 0 || rect.top >= viewH || rect.right <= 0 || rect.left >= viewW) continue;
    const x = Math.round(rect.left + rect.width / 2);
    const y = Math.round(rect.top + rect.height / 2);
    const top = document.elementFromPoint(x, y);
    if (!top || (top !== node && !node.contains(top) && !top.contains(node))) continue;
    const label = (node.innerText || "").replace(/\s+/g, " ").trim().slice(0, 80);
    const role = (node.getAttribute("role") || "").toLowerCase();
    const kind = roles.has(role) ? role : node.tagName.toLowerCase();
    out.push({n, kind, label, x, y});
    n += 1;
    if (n >= 80) break;
  }
  return out;
}
"""


def public_elements(elements: list[dict]) -> list[dict]:
    cleaned = []
    for item in elements:
        cleaned.append(
            {
                "n": int(item["n"]),
                "kind": str(item.get("kind") or ""),
                "label": str(item.get("label") or ""),
                "x": int(item["x"]),
                "y": int(item["y"]),
            }
        )
    return cleaned


def model_view(raw: dict[str, Any], cfg: dict) -> dict[str, Any]:
    """Drop fields the current obs_mode must not give the model."""
    obs: dict[str, Any] = {
        "tabs": raw.get("tabs") or [],
        "dialogs": raw.get("dialogs") or [],
        "pending_dialog": raw.get("pending_dialog"),
        "last_result": raw.get("last_result") or "",
        "budget": raw.get("budget") or {},
    }
    if cfg.get("show_url", True):
        obs["url"] = raw.get("url") or ""
    if cfg.get("obs_text"):
        obs["visible_text"] = str(raw.get("visible_text") or "")[: int(cfg.get("text_limit") or 6000)]
    if cfg.get("obs_elements"):
        obs["elements"] = public_elements(raw.get("elements") or [])
    if cfg.get("obs_screenshot") and raw.get("screenshot"):
        obs["screenshot"] = raw["screenshot"]
    if raw.get("turn") is not None:
        obs["turn"] = int(raw["turn"])
    book = cfg.get("notebook") or {}
    if book.get("enabled", False):
        obs["notebook"] = str(raw.get("notebook") or "")
    return obs


def obs_summary(model_obs: dict[str, Any], screenshot_name: str) -> dict[str, Any]:
    text = str(model_obs.get("visible_text") or "")
    return {
        "screenshot": screenshot_name,
        "tabs": model_obs.get("tabs") or [],
        "n_elements": len(model_obs.get("elements") or []),
        "text_sha1": hashlib.sha1(text.encode("utf-8")).hexdigest(),
        "text_head": text[:200],
        "dialogs": model_obs.get("dialogs") or [],
        "pending_dialog": model_obs.get("pending_dialog"),
    }
