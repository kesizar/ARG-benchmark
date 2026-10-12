"""Download only files referenced by the Involuntary Appetite exhibition pages."""

from __future__ import annotations

import re
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent / "involuntary-appetite"
LIVE = "https://d1rbt3w1v12ruj.cloudfront.net/game-users/contemporary/live/"
STEP2 = "https://lineargame.top/games/step2/"
HOST = "https://contemporary.minis.yoroll.ai/"
SEEDS = [LIVE + "index.html"]
ALLOW_PREFIXES = (LIVE, STEP2, HOST)
SKIP_PARTS = ("lg-game-analytics.js", "googletagmanager.com", "google-analytics.com")
TEXT_EXT = {".html", ".css", ".js", ".svg", ".json", ".txt"}
ASSET_EXT = r"png|jpg|jpeg|gif|webp|svg|mp3|mp4|pdf|css|js|ico|woff2?|ttf"
ATTR_RE = re.compile(r"""(?:src|href)\s*=\s*['"]([^'"]+)['"]""", re.I)
URL_FN_RE = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""", re.I)
ABS_RE = re.compile(r"""https://[^\s'"()<>]+""", re.I)
REL_ASSET_RE = re.compile(
    rf"""['"]([^'"]+\.(?:{ASSET_EXT}))['"]""",
    re.I,
)


def allowed(url: str) -> bool:
    clean, _ = urldefrag(url)
    if any(part in clean for part in SKIP_PARTS):
        return False
    return clean.startswith(ALLOW_PREFIXES)


def local_path(url: str) -> Path:
    clean, _ = urldefrag(url)
    parsed = urlparse(clean)
    path = parsed.path
    if clean.startswith(LIVE) or clean.startswith(HOST):
        name = path.rstrip("/").split("/")[-1] or "index.html"
        return ROOT / "live" / name
    prefix = "/games/step2/"
    if prefix not in path:
        raise ValueError(url)
    rel = path.split(prefix, 1)[1]
    return ROOT / "step2" / rel


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "ARG-benchmark-local-mirror"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def references(url: str, body: bytes) -> list[str]:
    if local_path(url).suffix.lower() not in TEXT_EXT and not url.endswith((".html", ".css", ".js")):
        return []
    text = body.decode("utf-8", errors="replace")
    found: list[str] = []
    base = LIVE if (url.startswith(LIVE) or url.startswith(HOST)) else url
    base_tag = re.search(r"""<base\s+href=['"]([^'"]+)['"]""", text, re.I)
    if base_tag:
        base = base_tag.group(1)
    for match in list(ATTR_RE.finditer(text)) + list(URL_FN_RE.finditer(text)):
        raw = match.group(1).strip()
        if not raw or raw.startswith(("data:", "mailto:", "javascript:", "#")):
            continue
        found.append(urljoin(base, raw))
    for match in ABS_RE.finditer(text):
        found.append(match.group(0).rstrip(".,;"))
    step2_base = STEP2 if STEP2 in text or url.startswith(STEP2) else None
    if step2_base:
        for match in REL_ASSET_RE.finditer(text):
            raw = match.group(1)
            if raw.startswith(("http://", "https://", "data:")):
                continue
            found.append(urljoin(STEP2, raw))
    return found


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    queue = deque(SEEDS)
    seen: set[str] = set()
    saved: list[tuple[str, int]] = []
    while queue:
        url, _ = urldefrag(queue.popleft())
        if url in seen or not allowed(url):
            continue
        seen.add(url)
        try:
            body = fetch(url)
        except Exception as exc:  # noqa: BLE001 — report and continue
            print(f"FAIL {url} {exc}")
            continue
        path = local_path(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        saved.append((str(path.relative_to(ROOT)), len(body)))
        print(f"OK {len(body):8d} {path.relative_to(ROOT)}")
        for ref in references(url, body):
            ref, _ = urldefrag(ref)
            if ref not in seen and allowed(ref):
                queue.append(ref)
    print(f"TOTAL {len(saved)} files, {sum(size for _, size in saved)} bytes")


if __name__ == "__main__":
    main()
