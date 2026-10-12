"""Download the remaining exhibition HTML pages and any newly referenced assets."""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent / "involuntary-appetite"
LIVE = "https://d1rbt3w1v12ruj.cloudfront.net/game-users/contemporary/live/"
STEP2 = "https://lineargame.top/games/step2/"
PAGES = [
    "kay.html",
    "breadcrumb-home.html",
    "breadcrumbs.html",
    "song-docs.html",
    "hidden-record.html",
    "yanagihara-docs.html",
    "superpukupon.html",
    "contemporary-onair.html",
    "survey-done-K7m2.html",
    "survey-done-9xP4.html",
    "record.html",
]
EXTRA = [STEP2 + "images/icon-exe.png"]
SKIP = ("${", "googletagmanager.com", "google-analytics.com", "lg-game-analytics.js")
ASSET_RE = re.compile(
    r"""https://(?:lineargame\.top/games/step2|d1rbt3w1v12ruj\.cloudfront\.net/game-users/contemporary/live)/[^\s'"()<>]+""",
    re.I,
)
ATTR_RE = re.compile(r"""(?:src|href)\s*=\s*['"]([^'"$]+)['"]""", re.I)


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "ARG-benchmark-local-mirror"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def dest(url: str) -> Path:
    clean, _ = urldefrag(url)
    if clean.startswith(STEP2):
        return ROOT / "step2" / clean[len(STEP2):]
    name = clean.rstrip("/").split("/")[-1]
    return ROOT / "live" / name


def main() -> None:
    queue = deque([LIVE + name for name in PAGES] + EXTRA)
    seen: set[str] = set()
    while queue:
        url, _ = urldefrag(queue.popleft().split("?", 1)[0])
        if url in seen or any(part in url for part in SKIP):
            continue
        if not (url.startswith(LIVE) or url.startswith(STEP2)):
            continue
        seen.add(url)
        path = dest(url)
        if path.exists() and path.stat().st_size > 0 and url in EXTRA:
            print(f"HAVE {path.relative_to(ROOT)}")
            continue
        try:
            body = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {url} {exc}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        print(f"OK {len(body):8d} {path.relative_to(ROOT)}", flush=True)
        if path.suffix.lower() not in {".html", ".css", ".js", ".svg"}:
            continue
        text = body.decode("utf-8", errors="replace")
        base = LIVE
        for match in ATTR_RE.finditer(text):
            raw = match.group(1).strip()
            if raw.startswith(("data:", "mailto:", "javascript:", "#", "http://", "https://")):
                if raw.startswith("http"):
                    queue.append(raw)
                continue
            queue.append(urljoin(base, raw))
        for match in ASSET_RE.finditer(text):
            queue.append(match.group(0).rstrip(".,;"))


if __name__ == "__main__":
    main()
