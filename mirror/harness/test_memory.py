"""Investigation notebook behavior. No live model or browser."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.agent import _action_from_text, _user_content
from harness.memory import InvestigationMemory


def observation(
    url: str,
    *,
    title: str = "",
    text: str = "",
    screenshot: str = "",
    controls: list[dict] | None = None,
) -> dict:
    return {
        "url": url,
        "title": title,
        "text": text,
        "screenshot": screenshot,
        "controls": controls or [],
    }


class MemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "memory.json"
        self.memory = InvestigationMemory(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_approach_and_theory_update_independently(self) -> None:
        self.memory.see(observation("http://127.0.0.1:8766/live/index.html", title="首页"), 1)
        self.memory.record_action({"tool": "click", "control_id": "c1", "approach": "先打开导览"}, 1)
        view = self.memory.view()
        self.assertEqual(view["approach"], "先打开导览")
        self.assertEqual(view["theory"], "")
        self.memory.record_action({"tool": "click", "control_id": "c2", "theory": "第六人是网站作者"}, 2)
        view = self.memory.view()
        self.assertEqual(view["approach"], "先打开导览")
        self.assertEqual(view["theory"], "第六人是网站作者")
        self.memory.record_action({"tool": "click", "control_id": "c3"}, 3)
        view = self.memory.view()
        self.assertEqual(view["approach"], "先打开导览")
        self.assertEqual(view["theory"], "第六人是网站作者")

    def test_empty_notes_show_placeholder(self) -> None:
        view = self.memory.view()
        self.assertEqual(view["approach"], "还没有判断。")
        self.assertEqual(view["theory"], "还没有判断。")

    def test_notes_truncated_to_2000(self) -> None:
        self.memory.record_action({"tool": "done", "approach": "甲" * 2100, "theory": "乙" * 2100}, 1)
        self.assertEqual(len(self.memory.approach), 2000)
        self.assertEqual(len(self.memory.theory), 2000)

    def test_previous_shot_is_empty_on_first_page(self) -> None:
        first = Path(self.tmp.name) / "step-001.png"
        first.write_bytes(b"one")
        self.memory.see(observation("http://127.0.0.1:8766/live/index.html", screenshot=str(first)), 1)
        self.assertEqual(self.memory.previous_shot, "")
        self.assertEqual(self.memory.last_shot, str(first))

    def test_previous_shot_holds_last_page(self) -> None:
        first = Path(self.tmp.name) / "step-001.png"
        second = Path(self.tmp.name) / "step-002.png"
        first.write_bytes(b"one")
        second.write_bytes(b"two")
        self.memory.see(observation("http://127.0.0.1:8766/live/index.html", screenshot=str(first)), 1)
        self.memory.see(observation("http://127.0.0.1:8766/live/news.html", screenshot=str(second)), 2)
        self.assertEqual(self.memory.previous_shot, str(first))
        self.assertEqual(self.memory.last_shot, str(second))

    def test_seen_buttons_unused_first_and_click_marks_used(self) -> None:
        page = observation(
            "http://127.0.0.1:8766/live/index.html",
            title="首页",
            controls=[
                {"id": "c1", "tag": "a", "text": "NEWS", "href": "/live/news.html", "type": ""},
                {"id": "c2", "tag": "button", "text": "打开噗咚导览机器人", "href": "", "type": ""},
                {"id": "c3", "tag": "button", "text": "下一题", "href": "", "type": ""},
                {"id": "c4", "tag": "button", "text": "", "href": "", "type": ""},
                {"id": "c5", "tag": "input", "text": "提交", "href": "", "type": "submit"},
            ],
        )
        self.memory.see(page, 1)
        labels = [item["label"] for item in self.memory.view()["buttons"]]
        self.assertEqual(labels, ["下一题", "打开噗咚导览机器人", "提交"])
        self.assertTrue(all(not item["used"] for item in self.memory.view()["buttons"]))
        self.memory.record_action({"tool": "click", "control_id": "c2"}, 1, page)
        buttons = {item["label"]: item["used"] for item in self.memory.view()["buttons"]}
        self.assertTrue(buttons["打开噗咚导览机器人"])
        self.assertFalse(buttons["下一题"])
        self.assertEqual(self.memory.view()["buttons"][0]["label"], "下一题")

    def test_hidden_keyword_link_stays_out_until_visible(self) -> None:
        self.memory.see(
            observation(
                "http://127.0.0.1:8766/live/index.html",
                title="首页",
                controls=[{"id": "c1", "tag": "button", "text": "打开噗咚导览机器人", "href": "", "type": ""}],
            ),
            1,
        )
        self.assertEqual(self.memory.view()["unopened"], [])
        self.memory.see(
            observation(
                "http://127.0.0.1:8766/live/index.html",
                title="首页",
                controls=[
                    {
                        "id": "c1",
                        "tag": "a",
                        "text": "会议记录",
                        "href": "/live/record.html?keyword=无害穿刺",
                        "type": "",
                    }
                ],
            ),
            2,
        )
        urls = [item["url"] for item in self.memory.view()["unopened"]]
        self.assertEqual(urls, ["/live/record.html"])

    def test_recall_returns_summary_and_screenshot(self) -> None:
        shot = Path(self.tmp.name) / "step-001.png"
        shot.write_bytes(b"page")
        self.memory.see(
            observation("http://127.0.0.1:8766/live/index.html", title="首页", screenshot=str(shot), text="整页正文"),
            1,
        )
        found = self.memory.lookup("p1")
        self.assertEqual(found["id"], "p1")
        self.assertEqual(found["screenshot"], str(shot))
        self.assertIn("首页", found["summary"])
        self.assertNotIn("整页正文", found["summary"])
        missing = self.memory.lookup("p9")
        self.assertEqual(missing["summary"], "笔记里没有这个编号")
        self.assertEqual(missing["screenshot"], "")

    def test_rejected_action_keeps_notes_without_marking_input(self) -> None:
        page = observation(
            "http://127.0.0.1:8766/live/index.html",
            title="首页",
            controls=[{"id": "c1", "tag": "a", "text": "ABOUT", "href": "#about", "type": ""}],
        )
        self.memory.see(page, 1)
        self.memory.record_action(
            {"tool": "type", "control_id": "c1", "text": "浅野慧", "submit": True, "theory": "会议里有浅野慧"},
            1,
            page,
            applied=False,
        )
        self.assertEqual(self.memory.theory, "会议里有浅野慧")
        self.assertEqual(self.memory.submissions, [])
        self.assertEqual(self.memory.used_inputs, set())

    def test_recall_submission_keeps_one_line(self) -> None:
        first = Path(self.tmp.name) / "step-001.png"
        first.write_bytes(b"before")
        self.memory.see(observation("http://127.0.0.1:8766/live/form.html", screenshot=str(first)), 1)
        self.memory.record_action({"tool": "type", "control_id": "c1", "text": "池袋", "submit": True}, 1)
        self.memory.see(observation("http://127.0.0.1:8766/live/form.html", text="画面变了", screenshot=str(first)), 2)
        found = self.memory.lookup("s1")
        self.assertIn("池袋", found["summary"])
        self.assertIn("画面没有前进", found["summary"])
        self.assertEqual(found["screenshot"], str(first))


class BrowserActTests(unittest.TestCase):
    def test_type_on_link_returns_to_model(self) -> None:
        from playwright.sync_api import sync_playwright

        from harness.browser import GameBrowser

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            try:
                page.set_content('<a data-harness-id="c1" href="#about">ABOUT</a><input data-harness-id="c2">')
                game = GameBrowser(Path("."))
                game.page = page
                refused = game.act({"tool": "type", "control_id": "c1", "text": "浅野慧", "submit": True})
                self.assertTrue(refused.startswith("无法执行"))
                typed = game.act({"tool": "type", "control_id": "c2", "text": "池袋", "submit": False})
                self.assertEqual(typed, "已输入")
                self.assertEqual(page.locator('[data-harness-id="c2"]').input_value(), "池袋")
            finally:
                browser.close()


class AgentParseTests(unittest.TestCase):
    def test_action_keeps_approach_and_theory(self) -> None:
        action = _action_from_text(
            '{"tool":"click","control_id":"c1","approach":"打开导览","theory":"噗咚会给线索"}'
        )
        self.assertEqual(action["approach"], "打开导览")
        self.assertEqual(action["theory"], "噗咚会给线索")
        self.assertNotIn("journal", action)

    def test_action_omits_missing_notes(self) -> None:
        action = _action_from_text('{"tool":"back"}')
        self.assertNotIn("approach", action)
        self.assertNotIn("theory", action)

    def test_user_content_image_order(self) -> None:
        folder = Path(tempfile.mkdtemp())
        previous = folder / "prev.png"
        current = folder / "now.png"
        recalled = folder / "old.png"
        previous.write_bytes(b"prev")
        current.write_bytes(b"now")
        recalled.write_bytes(b"old")
        payload = {
            "url": "http://127.0.0.1:8766/live/index.html",
            "screenshot": str(current),
            "previous_screenshot": str(previous),
            "recall": {"id": "p1", "summary": "p1 首页", "screenshot": str(recalled)},
        }
        parts = _user_content(payload, [], images="all")
        labels = [part.get("text") for part in parts if part.get("type") == "text"]
        self.assertEqual(labels[:3], ["上一张：", "当前：", "回看 p1："])
        current_only = _user_content(payload, [], images="current")
        current_labels = [part.get("text") for part in current_only if part.get("type") == "text"]
        self.assertEqual(current_labels[0], "当前：")
        self.assertTrue(all("上一张" not in str(item) and "回看" not in str(item) for item in current_labels[:-1]))
        none = _user_content(payload, [], images="none")
        self.assertIsInstance(none, str)
        body = json.loads(none)
        self.assertNotIn("screenshot", body["observation"])
        self.assertNotIn("previous_screenshot", body["observation"])


if __name__ == "__main__":
    unittest.main()
