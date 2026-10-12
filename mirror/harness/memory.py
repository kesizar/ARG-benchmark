"""Short investigation index plus lookup into saved screenshots."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

HOST = "127.0.0.1:8766"
MARKER = re.compile(r"step\s*I\s*\d+\s*/\s*\d+|①\s*[：:]\s*\d+\s*/\s*\d+|②\s*[：:]\s*\d+\s*/\s*\d+")
NOTE_LIMIT = 2000


def page_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc != HOST:
        return ""
    path = parsed.path or "/"
    if parsed.fragment:
        return f"{path}#{parsed.fragment}"
    return path


def screen_key(observation: dict[str, Any]) -> str:
    url = page_url(str(observation.get("url") or ""))
    text = str(observation.get("text") or "")
    markers = MARKER.findall(text)
    if not markers:
        return url
    return url + "|" + ",".join(markers)


def is_button(control: dict[str, Any]) -> bool:
    tag = str(control.get("tag") or "")
    kind = str(control.get("type") or "")
    return tag == "button" or (tag == "input" and kind in {"button", "submit"})


def button_label(control: dict[str, Any]) -> str:
    return str(control.get("text") or "").strip()[:40]


class InvestigationMemory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.approach = ""
        self.theory = ""
        self.pages: list[dict[str, Any]] = []
        self.submissions: list[dict[str, Any]] = []
        self.seen_links: dict[str, dict[str, str]] = {}
        self.inputs: dict[str, dict[str, Any]] = {}
        self.used_inputs: set[str] = set()
        self.buttons: dict[str, dict[str, Any]] = {}
        self.last_key = ""
        self.last_url = ""
        self.last_shot = ""
        self.previous_shot = ""
        self.last_typed: dict[str, Any] | None = None
        self.pending: dict[str, Any] | None = None

    def see(self, observation: dict[str, Any], step: int) -> None:
        key = screen_key(observation)
        if self.pending is not None:
            self.submissions.append(
                {
                    "id": f"s{len(self.submissions) + 1}",
                    "url": self.pending["url"],
                    "text": self.pending["text"],
                    "advanced": key != self.pending["before"],
                    "step": self.pending["step"],
                    "screenshot": self.pending["screenshot"],
                }
            )
            self.pending = None
        self.previous_shot = self.last_shot
        self.last_key = key
        self.last_url = page_url(str(observation.get("url") or ""))
        self.last_shot = str(observation.get("screenshot") or "")
        self._touch_page(observation, step)
        self._collect(observation)
        self._write()

    def record_action(
        self,
        action: dict[str, Any],
        step: int,
        observation: dict[str, Any] | None = None,
        applied: bool = True,
    ) -> None:
        approach = str(action.get("approach") or "").strip()
        if approach:
            self.approach = approach[:NOTE_LIMIT]
        theory = str(action.get("theory") or "").strip()
        if theory:
            self.theory = theory[:NOTE_LIMIT]
        if not applied:
            self._write()
            return
        tool = action.get("tool")
        if tool == "type":
            typed = {
                "url": self.last_url,
                "text": str(action.get("text") or "")[:80],
                "before": self.last_key,
                "step": step,
                "screenshot": self.last_shot,
            }
            self.used_inputs.add(self.last_url)
            if action.get("submit"):
                self.pending = typed
                self.last_typed = None
            else:
                self.last_typed = typed
        elif tool == "click":
            self._mark_button(action, observation)
            if self.last_typed and self.last_typed["url"] == self.last_url:
                self.pending = self.last_typed
                self.last_typed = None
        elif tool != "recall":
            self.last_typed = None
        self._write()

    def view(self) -> dict[str, Any]:
        visited_urls = {item["url"] for item in self.pages}
        unopened = [
            {"id": item["from"], "text": item["text"], "url": url}
            for url, item in self.seen_links.items()
            if url not in visited_urls
        ]
        inputs = [
            {"on": item["on"], "label": item["label"], "used": item["url"] in self.used_inputs}
            for item in self.inputs.values()
        ]
        buttons = sorted(self.buttons.values(), key=lambda item: (bool(item["used"]), item["on"], item["label"]))
        empty = not self.approach and not self.theory
        return {
            "visited": [{"id": item["id"], "url": item["url"], "title": item["title"]} for item in self.pages],
            "unopened": unopened[:24],
            "inputs": inputs[:16],
            "buttons": [
                {"on": item["on"], "label": item["label"], "used": item["used"]}
                for item in buttons[:24]
            ],
            "submissions": [
                {"id": item["id"], "url": item["url"], "text": item["text"], "advanced": item["advanced"]}
                for item in self.submissions[-16:]
            ],
            "approach": self.approach or ("还没有判断。" if empty else ""),
            "theory": self.theory or ("还没有判断。" if empty else ""),
        }

    def lookup(self, record_id: str) -> dict[str, str]:
        record_id = record_id.strip()
        for item in self.pages:
            if item["id"] == record_id:
                return {
                    "id": record_id,
                    "summary": f"{item['id']} {item['title']} {item['url']}",
                    "screenshot": item["screenshot"],
                }
        for item in self.submissions:
            if item["id"] == record_id:
                moved = "画面有前进" if item["advanced"] else "画面没有前进"
                return {
                    "id": record_id,
                    "summary": f"{item['id']} 在 {item['url']} 提交「{item['text']}」，{moved}",
                    "screenshot": item["screenshot"],
                }
        return {"id": record_id, "summary": "笔记里没有这个编号", "screenshot": ""}

    def _touch_page(self, observation: dict[str, Any], step: int) -> None:
        url = self.last_url
        if not url or any(item["url"] == url for item in self.pages):
            return
        title = str(observation.get("title") or "").strip()[:40]
        self.pages.append(
            {
                "id": f"p{len(self.pages) + 1}",
                "url": url,
                "title": title,
                "step": step,
                "screenshot": self.last_shot,
            }
        )

    def _collect(self, observation: dict[str, Any]) -> None:
        base = str(observation.get("url") or "")
        page_id = next((item["id"] for item in self.pages if item["url"] == self.last_url), "")
        for control in observation.get("controls") or []:
            if not isinstance(control, dict):
                continue
            tag = str(control.get("tag") or "")
            kind = str(control.get("type") or "")
            label = str(control.get("text") or "").strip()[:40]
            if tag == "a":
                target = page_url(urljoin(base, str(control.get("href") or "")))
                if target and target != self.last_url and target not in self.seen_links:
                    self.seen_links[target] = {"from": page_id, "text": label or target}
            if tag in {"input", "textarea"} and kind not in {"hidden", "button", "submit", "checkbox", "radio"}:
                key = f"{self.last_url}|{label}"
                self.inputs[key] = {"on": page_id, "url": self.last_url, "label": label or tag}
            if is_button(control):
                text = button_label(control)
                if not text:
                    continue
                key = f"{self.last_url}|{text}"
                if key not in self.buttons:
                    self.buttons[key] = {"on": page_id, "url": self.last_url, "label": text, "used": False}

    def _mark_button(self, action: dict[str, Any], observation: dict[str, Any] | None) -> None:
        if not observation:
            return
        control_id = str(action.get("control_id") or "")
        for control in observation.get("controls") or []:
            if not isinstance(control, dict) or str(control.get("id") or "") != control_id:
                continue
            if not is_button(control):
                return
            text = button_label(control)
            if not text:
                return
            key = f"{self.last_url}|{text}"
            if key in self.buttons:
                self.buttons[key]["used"] = True
            return

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "approach": self.approach,
                    "theory": self.theory,
                    "pages": self.pages,
                    "submissions": self.submissions,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
