"""Write one config and judge per meta-data puzzle and Bellingcat challenge."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITEUP = Path(r"D:\HuaweiMoveData\Users\17669\Desktop\ARG-packs\bellingcat-writeup\challenge sets")


def answer_sha256(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    folded = "".join(normalized.split()).lower()
    return hashlib.sha256(folded.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def static_config(task_id: str, title: str, intro: str, prompt: str, note: str) -> dict:
    return {
        "id": task_id,
        "category": "static",
        "runtime_layer": "L1",
        "obs_mode": "A",
        "obs_modes_to_run": ["A"],
        "computer_use": False,
        "model_visible": {"title": title, "intro": intro},
        "entry_url": None,
        "local_serve": {"enabled": False},
        "allow_model_goto": False,
        "goto_scope": "none",
        "actions_enabled": ["submit_answer", "give_up"],
        "static": {"prompt": prompt},
        "limits": {"max_steps": 20, "max_seconds": 600, "max_answer_submits": 5},
        "history": {"full_obs_k": 4, "screenshot_k": 2},
        "judge_path": f"judge/{task_id}/judge.json",
        "policy_script": [{"op": "give_up"}],
        "isolation": {"container": False},
        "notes_for_report": [note],
    }


def answer_judge(hashes: list[str]) -> dict:
    return {
        "hooks": {},
        "checkpoints": [],
        "events": {},
        "ending": None,
        "answer_sha256": hashes,
        "answer_hash_file": None,
        "request_milestones": [],
        "submit_conclusion": {"enabled": False, "schema": None},
        "rubric_path": None,
    }


def build_meta() -> list[str]:
    source = json.loads((ROOT / "tasks/meta-data/src/src/metadata.json").read_text(encoding="utf-8"))
    paths = []
    for index, item in enumerate(source, start=1):
        task_id = f"meta-data-{index:03d}"
        feeders = [str(word) for word in item.get("feeders") or []]
        lines = []
        note = str(item.get("note") or "").strip()
        flavor = str(item.get("flavor") or "").strip()
        if note:
            lines.append(note)
        if flavor:
            lines.append(flavor)
        lines.append("喂入词：")
        lines.extend(feeders)
        lines.append("用 submit_answer 提交一个答案。")
        hunt = (item.get("source") or {}).get("hunt") or ""
        year = (item.get("source") or {}).get("year") or ""
        write_json(
            ROOT / f"configs/meta-data/{task_id}.json",
            static_config(
                task_id,
                f"meta-data {index:03d}",
                "这是一道元谜题。题面只有喂入词和原题留下的说明。用 submit_answer 提交答案。不要打开其他网站。",
                "\n".join(lines),
                f"来自 {hunt} {year}。答案只在裁判哈希里。完整数据文件不交给模型。",
            ),
        )
        hashes = [answer_sha256(str(answer)) for answer in item.get("answer") or []]
        write_json(ROOT / f"judge/{task_id}/judge.json", answer_judge(hashes))
        paths.append(f"configs/meta-data/{task_id}.json")
    write_json(ROOT / "configs/meta_data_set.json", {"tasks": paths})
    return paths


def section(text: str, heading: str, following: str) -> str:
    match = re.search(rf"^## {heading}\s*$([\s\S]*?)(?=^## |\Z)", text, flags=re.M)
    if not match:
        return ""
    body = match.group(1)
    if following:
        body = re.split(rf"^## {following}\s*$", body, maxsplit=1, flags=re.M)[0]
    return body.strip()


def slug(name: str) -> str:
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    token = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    return token or "challenge"


def build_bellingcat() -> list[str]:
    paths = ["configs/bellingcat-sample.json"]
    port = 8801
    for writeup in sorted(WRITEUP.glob("*/*/writeup.md")):
        if writeup.parent.name == "pet the cat":
            continue
        text = writeup.read_text(encoding="utf-8")
        challenge = section(text, "Challenge", "Investigation")
        answer = section(text, "Answer", "")
        if not challenge or not answer:
            print("skip", writeup)
            continue
        images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", challenge)
        question = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", challenge)
        question = re.sub(r"^>\s?", "", question, flags=re.M).strip()
        task_id = "bellingcat-" + slug(writeup.parent.name)
        mirror = ROOT / "tasks" / task_id / "mirror"
        if mirror.exists():
            shutil.rmtree(mirror)
        mirror.mkdir(parents=True)
        tags = []
        for name in images:
            src = writeup.parent / name
            if not src.is_file():
                continue
            target = mirror / Path(name).name
            shutil.copyfile(src, target)
            tags.append(f'<img src="{html.escape(target.name)}" alt="challenge">')
        page = (
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
            f"<title>{html.escape(writeup.parent.name)}</title></head><body>"
            f"<h1>{html.escape(writeup.parent.name)}</h1>"
            f"<pre>{html.escape(question)}</pre>"
            + "".join(tags)
            + "</body></html>"
        )
        (mirror / "index.html").write_text(page, encoding="utf-8")
        cfg = {
            "id": task_id,
            "category": "web_puzzle",
            "runtime_layer": "L1",
            "obs_mode": "B",
            "obs_modes_to_run": ["B"],
            "computer_use": False,
            "model_visible": {
                "title": writeup.parent.name,
                "intro": "根据屏幕上的图片和问题作答。用 submit_answer 提交答案。不要打开其他网站。",
            },
            "entry_url": f"http://127.0.0.1:{port}/",
            "local_serve": {
                "enabled": True,
                "command": ["python", "scripts/serve_static.py", "--root", f"tasks/{task_id}/mirror", "--port", str(port)],
                "cwd": ".",
                "ready_url": f"http://127.0.0.1:{port}/",
                "ready_timeout_s": 30,
                "port": port,
            },
            "viewport": {"width": 1366, "height": 900},
            "locale": "en-US",
            "timezone": "Europe/Belgrade",
            "seed": 20261018,
            "allow_hosts": [f"127.0.0.1:{port}"],
            "shortcut_block": [],
            "guide_block_hosts": ["*bellingcat.com*", "*walkthrough*", "*writeup*"],
            "allow_model_goto": False,
            "goto_scope": "none",
            "show_url": False,
            "text_scope": "page",
            "text_limit": 4000,
            "actions_enabled": ["click", "scroll", "wait", "submit_answer", "give_up"],
            "limits": {"max_steps": 30, "max_seconds": 900, "max_answer_submits": 5},
            "settle_ms": 400,
            "history": {"full_obs_k": 4, "screenshot_k": 2},
            "judge_path": f"judge/{task_id}/judge.json",
            "policy_script": [{"op": "wait"}, {"op": "give_up"}],
            "isolation": {"container": False},
            "notes_for_report": ["镜像只有题目图和题干。题解目录不在这个任务里。答案只在裁判哈希里。"],
        }
        write_json(ROOT / f"configs/bellingcat/{task_id}.json", cfg)
        lines = [line.strip() for line in answer.splitlines() if line.strip()]
        hashes = [answer_sha256(answer)]
        for line in lines:
            digest = answer_sha256(line)
            if digest not in hashes:
                hashes.append(digest)
        write_json(ROOT / f"judge/{task_id}/judge.json", answer_judge(hashes))
        paths.append(f"configs/bellingcat/{task_id}.json")
        port += 1
    write_json(ROOT / "configs/bellingcat_set.json", {"tasks": paths})
    return paths


def main() -> None:
    meta = build_meta()
    geo = build_bellingcat()
    print(f"meta {len(meta)} bellingcat {len(geo)}")


if __name__ == "__main__":
    main()
