"""Copy the netdisk folder, the metro PDF, and a local museum collection page."""

from __future__ import annotations

import html
import re
import shutil
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "involuntary-appetite"
BAIDU = Path(r"D:\BaiduNetdiskDownload") / "非自愿摄入"
LIST_HTML = Path(__file__).resolve().parent / "_kanazawa.html"
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url: str) -> bytes:
    import subprocess
    last_error = "unknown"
    for attempt in range(4):
        result = subprocess.run(
            ["curl.exe", "-sL", "-A", "Mozilla/5.0", "--fail", url],
            capture_output=True,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
        last_error = result.stderr.decode("utf-8", errors="replace") or str(result.returncode)
        time.sleep(1 + attempt)
    raise RuntimeError(f"{url} {last_error}")


def ext_for(body: bytes) -> str:
    if body.startswith(b"\xff\xd8"):
        return ".jpg"
    if body.startswith(b"\x89PNG"):
        return ".png"
    if body.startswith(b"GIF8"):
        return ".gif"
    if body.startswith(b"RIFF"):
        return ".webp"
    return ".img"


def absolute(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return "https://www.kanazawa21.jp" + url


def main() -> None:
    netdisk = ROOT / "step2" / "netdisk"
    if not netdisk.exists():
        shutil.copytree(BAIDU, netdisk)
    print(f"netdisk files {sum(1 for p in netdisk.rglob('*') if p.is_file())}")

    list_text = LIST_HTML.read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(
        r'href="\./data_list\.php\?g=30&d=(\d+)[^"]*"[\s\S]*?<img src="([^"]+)"[\s\S]*?'
        r'class="panel__name">(.*?)</h3><h3 class="panel__artist">(.*?)</h3>'
        r'<p class="panel__copyright">(.*?)</p>',
        list_text,
    )
    image_dir = ROOT / "step2" / "kanazawa"
    image_dir.mkdir(parents=True, exist_ok=True)
    cards = []
    for work_id, image_url, name, artist, copyright_html in blocks:
        name = html.unescape(re.sub(r"<[^>]+>", "", name)).strip()
        artist = html.unescape(re.sub(r"<[^>]+>", "", artist)).strip()
        copyright_text = html.unescape(re.sub(r"<br\s*/?>", " ", copyright_html))
        copyright_text = re.sub(r"<[^>]+>", "", copyright_text).strip()
        detail = fetch(f"https://www.kanazawa21.jp/data_list.php?g=30&d={work_id}&lng=cn")
        detail_text = detail.decode("utf-8", errors="replace")
        lead_match = re.search(r'<p class="lead">(.*?)</p>', detail_text, re.S)
        lead = html.unescape(re.sub(r"<[^>]+>", "", lead_match.group(1))).strip() if lead_match else ""
        main_match = re.search(r'hero__full__img"><img src="([^"]+)"', detail_text)
        list_body = fetch(absolute(image_url))
        list_name = f"d{work_id}-list{ext_for(list_body)}"
        (image_dir / list_name).write_bytes(list_body)
        main_name = ""
        if main_match:
            main_body = fetch(absolute(main_match.group(1)))
            main_name = f"d{work_id}-main{ext_for(main_body)}"
            (image_dir / main_name).write_bytes(main_body)
        cards.append({
            "id": work_id,
            "name": name,
            "artist": artist,
            "copyright": copyright_text,
            "lead": lead,
            "list": list_name,
            "main": main_name,
        })
        print(f"work {work_id} {name} list={len(list_body)} main={main_name}")
        time.sleep(0.4)

    write_pages(cards)


def write_pages(cards: list[dict]) -> None:
    live = ROOT / "live"
    items = []
    for card in cards:
        items.append(
            "<article>"
            f'<a href="kanazawa-d{card["id"]}.html">'
            f'<img src="/step2/kanazawa/{card["list"]}" alt="{html.escape(card["name"])}">'
            f"<h2>{html.escape(card['name'])}</h2>"
            f"<p>{html.escape(card['artist'])}</p>"
            "</a></article>"
        )
    collection = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>恒久展示作品 | 金泽21世纪美术馆</title>
<style>
body {{ margin: 24px; font-family: "Microsoft YaHei", sans-serif; background: #f4f4f4; color: #222; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
article {{ background: #fff; }}
img {{ width: 100%; height: 180px; object-fit: cover; background: #ddd; }}
a {{ color: inherit; text-decoration: none; }}
h2, p {{ margin: 8px 12px; }}
</style>
</head>
<body>
<p><a href="index.html">返回展览</a></p>
<h1>恒久展示作品</h1>
<p>金泽21世纪美术馆。此页是该名单的本地副本，只供本机游戏使用。</p>
<div class="grid">
{"".join(items)}
</div>
<p>Copyright © 2024 21st Century Museum of Contemporary Art, Kanazawa.</p>
</body>
</html>
"""
    (live / "kanazawa-collection.html").write_text(collection, encoding="utf-8")
    for card in cards:
        image = f'<img src="/step2/kanazawa/{card["main"]}" alt="{html.escape(card["name"])}">' if card["main"] else ""
        page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{html.escape(card["name"])}</title>
<style>
body {{ margin: 24px auto; max-width: 880px; font-family: "Microsoft YaHei", sans-serif; color: #222; }}
img {{ width: 100%; height: auto; background: #ddd; }}
</style>
</head>
<body>
<p><a href="kanazawa-collection.html">返回恒久展示作品</a></p>
{image}
<h1>{html.escape(card["name"])}</h1>
<h2>{html.escape(card["artist"])}</h2>
<p>{html.escape(card["lead"])}</p>
<p>{html.escape(card["copyright"])}</p>
<p>Copyright © 2024 21st Century Museum of Contemporary Art, Kanazawa.</p>
</body>
</html>
"""
        (live / f"kanazawa-d{card['id']}.html").write_text(page, encoding="utf-8")
    print(f"pages {len(cards) + 1}")


if __name__ == "__main__":
    main()
