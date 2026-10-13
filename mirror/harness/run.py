"""Play the local exhibition in a browser.

评测入口在仓库根的 scripts/run_one.py。本文件保留原来的调查循环。

Self-check, no model:

    python mirror/harness/run.py --selfcheck

One model session, until the model stops:

    python mirror/harness/run.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from harness.agent import choose_action, load_env  # noqa: E402
from harness.browser import HOME, GameBrowser  # noqa: E402
from harness.memory import InvestigationMemory  # noqa: E402


def selfcheck(browser: GameBrowser) -> None:
    browser.goto(HOME + "/live/breadcrumb-home.html")
    before = browser.observe()
    if not before["tiles"]:
        raise SystemExit("面包屑拼图没有出现")
    browser.drag("t0", "move", 70, 35)
    browser.drag("t0", "zoom", 0, -80)
    after = browser.observe()
    tile = after["tiles"][0]
    if abs(tile["x"]) < 20 or abs(tile["y"]) < 10:
        raise SystemExit(f"平移没有生效: {tile}")
    if tile["scale"] <= 1.05:
        raise SystemExit(f"缩放没有生效: {tile}")
    browser.goto(HOME + "/live/breadcrumbs.html")
    page = browser.observe()
    field = next((item for item in page["controls"] if item["tag"] == "input"), None)
    if field is None:
        raise SystemExit("车站输入框没有出现")
    browser.type_text(field["id"], "测试车站", submit=False)
    value = browser.page.locator(f'[data-harness-id="{field["id"]}"]').input_value()
    if value != "测试车站":
        raise SystemExit(f"输入没有写入: {value}")
    print("selfcheck ok")
    print(json.dumps({"moved": tile, "typed": field["id"]}, ensure_ascii=False))


def play(browser: GameBrowser, url: str, steps: int | None) -> None:
    browser.goto(url)
    history: list[dict] = []
    memory = InvestigationMemory(browser.runs / "memory.json")
    pending_recall: dict[str, str] | None = None
    index = 0
    report = browser.runs / "trace.json"
    try:
        while steps is None or index < steps:
            observation = browser.observe()
            memory.see(observation, browser.step)
            if memory.previous_shot:
                observation["previous_screenshot"] = memory.previous_shot
            if pending_recall:
                observation["recall"] = pending_recall
                pending_recall = None
            observation["notebook"] = memory.view()
            recent_pages = [item["url"].split("#")[0] for item in history[-4:]]
            if len(recent_pages) == 4 and len(set(recent_pages)) <= 2:
                observation["stuck"] = "最近四步只在这两个页面之间来回。不要再点返回或同一条新闻，改点一个还没打开过的链接，或打开页面上的对话。"
            action = choose_action(observation, history)
            if action.get("tool") == "recall":
                pending_recall = memory.lookup(str(action.get("id") or ""))
                result = pending_recall["summary"]
                applied = True
            else:
                result = browser.act(action)
                applied = not str(result).startswith("无法执行")
            memory.record_action(action, browser.step, observation, applied=applied)
            history.append({"step": index + 1, "action": action, "result": result, "url": observation["url"]})
            print(json.dumps(history[-1], ensure_ascii=False), flush=True)
            report.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
            if action.get("tool") == "done":
                break
            index += 1
    finally:
        report.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        print(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="在本机浏览器里玩非自愿摄入")
    parser.add_argument("--url", default=HOME + "/live/index.html")
    parser.add_argument("--steps", type=int, default=None, help="可选步数上限。不填则直到模型自己结束")
    parser.add_argument("--show", action="store_true", help="打开可见浏览器")
    parser.add_argument("--selfcheck", action="store_true", help="只检查点击、输入和面包屑拖动")
    args = parser.parse_args()
    repo = ROOT.parent
    load_env(repo)
    runs = ROOT / "harness" / "runs" / ("selfcheck" if args.selfcheck else "play")
    browser = GameBrowser(runs, headless=not args.show)
    print("正在打开浏览器", flush=True)
    browser.start()
    print("浏览器已打开", flush=True)
    try:
        if args.selfcheck:
            selfcheck(browser)
        else:
            play(browser, args.url, args.steps)
    finally:
        browser.close()


if __name__ == "__main__":
    main()
